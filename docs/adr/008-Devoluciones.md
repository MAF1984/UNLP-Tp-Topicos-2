## ADR 008: Devoluciones

**Estado:** Propuesto · **Fecha:** 15/11/2026 · **Etapa:** III

**Drivers:** el enunciado exige que los clientes soliciten devoluciones y que los administradores las aprueben o rechacen, liberando el asiento o la zona correspondiente; la operación involucra dinero, tickets e inventario en dos servicios y debe tolerar fallos de la pasarela.

**Contexto:** la v1 no cubría este desafío funcional. Un reembolso cruza Ticketing (estado del ticket e inventario) y Payments (dinero), por lo que requiere una Saga (ADR 009).

**Alternativas consideradas:**

- *Reembolso automático sin aprobación*: descartado como regla general (el enunciado exige aprobación), salvo en cancelación del evento y pago tardío.
- *Transacción distribuida entre Ticketing y Payments*: descartada; las pasarelas no participan en 2PC.
- *Liberar el asiento al solicitar la devolución*: descartado; permitiría revender un ticket todavía válido. El inventario se libera solo cuando el reembolso se completa.

**Decisión:**

1. **Estados del refund:** `REQUESTED` → `APPROVED` → `REFUND_IN_PROGRESS` → `COMPLETED`; `REQUESTED` → `REJECTED`; `REFUND_IN_PROGRESS` → `REFUND_PENDING` (falla de la pasarela, con reintentos) → `COMPLETED` o `FAILED_MANUAL_REVIEW`. Mientras está `REQUESTED`, el ticket sigue válido y el asiento `SOLD`.
2. **Política (supuestos configurables por evento):** se puede solicitar hasta 48 h antes del inicio; no se puede solicitar si el ticket fue usado; un solo refund activo por ticket; el monto reembolsable y el tratamiento de los cargos de servicio se definen por evento (a confirmar con el cliente).
3. **Saga orquestada por Ticketing:**

   1. El cliente envía `POST /refunds` con `Idempotency-Key` (ADR 002); queda `REQUESTED` y se audita.
   2. El administrador aprueba o rechaza con un motivo (`POST /refunds/{id}/approve` o `/reject`); queda auditado y el cliente es notificado.
   3. Al aprobar, el ticket pasa a `REFUND_IN_PROGRESS` (no válido para ingreso) y se emite `payments.refund.requested.v1` vía Outbox.
   4. Payments ejecuta el reembolso en la pasarela usando `refund_id` como clave de idempotencia y responde con `payments.refund.completed.v1` o `failed.v1`.
   5. Al completarse, en una sola transacción: ticket `REFUNDED`, `seat_allocation` pasa a `RELEASED` (o `zone_inventory.available` suma `qty`), refund `COMPLETED` y se emite `ticketing.ticket.refunded.v1` (invalida caché y actualiza la búsqueda).
   6. Ante fallas se reintenta con backoff; agotados los intentos, el refund queda en `REFUND_PENDING` o `FAILED_MANUAL_REVIEW` con alerta, y el inventario permanece ocupado hasta resolverlo.

4. **Cancelación de un evento por el owner o el administrador:** genera devoluciones automáticas, sin aprobación, para todos los tickets vendidos. Es un proceso en lote idempotente por ticket, con tasa limitada para no saturar la pasarela; el evento queda `CANCELLED` y se bloquea la venta.
5. **Concurrencia:** el ticket tiene control de versión para resolver una devolución simultánea con un ingreso o una transferencia; un índice único parcial garantiza un único refund activo por ticket.
6. **Conciliación:** los reembolsos se concilian a diario contra el reporte de la pasarela (ADR 009).

**Implicancias:**

- Positivas: el dinero y el inventario nunca quedan inconsistentes sin que haya una alerta; el flujo es auditable de punta a punta.
- Negativas / riesgos: estados intermedios visibles al cliente; carga operativa de revisión manual en fallas persistentes; la devolución masiva por cancelación requiere control de tasa.

**Criterio de verificación:** (1) solicitar dos veces la devolución del mismo ticket produce un solo refund; (2) un refund aprobado llega una única vez a la pasarela aunque el mensaje se reintente; (3) el asiento solo queda comprable después de `COMPLETED`; (4) con la pasarela caída, el refund queda en `REFUND_PENDING`, reintenta y no libera el inventario; (5) rechazar una solicitud deja el ticket válido; (6) cancelar un evento con 1.000 tickets genera 1.000 reembolsos sin duplicados; (7) cada aprobación y rechazo tiene su registro de auditoría.