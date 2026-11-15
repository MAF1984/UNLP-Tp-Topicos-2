## ADR 009: Pagos, Saga y Outbox

**Estado:** Propuesto · **Fecha:** 15/11/2026 · **Etapa:** I (pagos, Outbox, inbox) y III (reembolsos, conciliación)

**Drivers:** el enunciado pide manejo de fallos parciales y consistencia eventual; hay que integrar una pasarela externa de forma segura, sin que los datos de tarjeta toquen los servicios propios, y entregar eventos de forma confiable.

**Contexto:** el pago es una operación externa y no transaccional: puede fallar, demorar, llegar duplicada o confirmarse después de expirar el hold. Los servicios deben coordinarse sin transacciones distribuidas. No está definido si habrá pasarela real, sandbox o mock (ver “Puntos a confirmar”).

**Alternativas consideradas:**

- *Transacciones distribuidas (2PC / XA)*: descartadas; las pasarelas externas no las soportan y acoplan la disponibilidad.
- *Doble escritura (guardar en la BD y publicar el evento en pasos separados)*: descartada; puede perder o duplicar eventos si falla entre ambos pasos.
- *CDC (por ejemplo Debezium) para el outbox*: válido, pero pospuesto por complejidad; un relay por polling alcanza.
- *Datos de tarjeta pasando por el backend*: descartado por el alcance PCI DSS.

**Decisión:**

1. **Pasarela detrás de `PaymentGatewayPort`**, con dos adaptadores: un mock determinístico para tests y CI (simula aprobado, rechazado, timeout y confirmación tardía) y el sandbox de un proveedor real si la cátedra lo permite. Checkout alojado o tokenización: los datos de tarjeta van del navegador a la pasarela; el backend maneja solo tokens e identificadores de pago.
2. **Flujo de compra (Saga orquestada por Ticketing):**

   1. Ticketing crea el hold y la orden `PENDING_PAYMENT` (ADR 002).
   2. Ticketing llama a Payments (`POST /payments`, con una `Idempotency-Key` derivada de la orden y el intento); Payments crea el pago en la pasarela y devuelve el `payment_intent`.
   3. La pasarela confirma por webhook. Payments verifica la firma y la ventana temporal, rechaza replays, deduplica por el `event_id` del proveedor, responde 200 rápidamente y publica `payments.payment.succeeded.v1` o `failed.v1`.
   4. Ticketing consume el evento: si hay éxito, el hold pasa a `SOLD`, la orden a `PAID` y se emiten los tickets; si falla o expira, libera el hold y la orden queda `FAILED` o `EXPIRED`. El pago tardío se resuelve según el ADR 002.
   5. Compensación: si tras cobrar no se puede asignar el ticket, se dispara un reembolso automático.

3. **Outbox transaccional:** cada servicio escribe sus eventos en una tabla `outbox` en la misma transacción que el cambio de estado. Un relay (polling con `FOR UPDATE SKIP LOCKED`, supuesto: cada 1 s) los publica en RabbitMQ y los marca como enviados. Garantiza *at-least-once* sin pérdida. La tabla existe desde la Etapa I; el relay se conecta al broker cuando aparece el primer consumidor.
4. **Inbox y mensajes:** los consumidores deduplican por `message_id` (ADR 002). Todo evento incluye `message_id`, `type`, `version`, `occurred_at` y `trace_id`; el orden se garantiza por agregado mediante un número de versión, no de forma global.
5. **Reintentos y DLQ:** backoff exponencial con jitter y máximo de 5 intentos (supuesto); luego DLQ con alerta y una herramienta de reprocesamiento para administradores.
6. **Estado desconocido:** ante un timeout hacia la pasarela (5 s), el pago queda `UNKNOWN` y se resuelve consultando por clave de idempotencia; nunca se asume el fallo. Los pagos `PENDING` por más de unos minutos se consultan activamente por si se perdió el webhook.
7. **Conciliación diaria:** un job compara pagos y reembolsos locales con el reporte de la pasarela; las diferencias generan alerta y registro de auditoría.

**Implicancias:**

- Positivas: sin transacciones distribuidas; sin pérdida de eventos; alcance PCI reducido; fallas de la pasarela tratadas como un caso normal.
- Negativas / riesgos: latencia añadida por el relay; más piezas a operar (outbox, inbox, DLQ, conciliación); estados intermedios visibles al usuario (“pago en proceso”).

**Criterio de verificación:** (1) un webhook enviado 5 veces produce una sola transición de estado; (2) un webhook con firma inválida se rechaza sin efecto; (3) detener el servicio entre el commit y la publicación no pierde el evento; (4) el mock con timeout deja el pago en `UNKNOWN` y se resuelve por consulta, sin doble cobro; (5) un mensaje redeliverado 3 veces produce un solo efecto; (6) ninguna tabla ni log contiene PAN ni CVV.
