## ADR 002: Prevención de doble venta (idempotencia y concurrencia)

**Estado:** Aceptado (rev. 2) · **Fecha:** 15/11/2026 · **Etapa:** I

**Drivers:** un mismo asiento o cupo de zona nunca puede venderse a dos clientes; los reintentos de red y los clics dobles no deben duplicar órdenes ni cobros; los picos de concurrencia no deben degradar la integridad.

**Contexto:** la unicidad de venta es el requisito crítico del negocio, tanto en ubicaciones numeradas como en zonas generales. Las dos modalidades tienen patrones de contención distintos (ADR 011): en las numeradas cada asiento es una fila distinta; en las zonas todos los compradores compiten por un mismo contador.

**Alternativas consideradas:**

- *Lock distribuido en Redis como garantía*: descartado. Un lock con TTL puede vencer mientras su dueño sigue operando (pausa de GC, latencia de red, failover de Redis con pérdida de escrituras), por lo que no ofrece exclusión mutua fuerte. Redis puede servir como optimización, nunca como garantía.
- *Lock pesimista en transacciones largas*: descartado, porque retiene filas durante todo el flujo de pago. En transacciones cortas (un hold dura milisegundos), `SELECT … FOR UPDATE SKIP LOCKED` es una opción válida y queda como alternativa si el índice único mostrara demasiados conflictos. La v1 lo descartaba en bloque.
- *Lock optimista por versión de fila para zonas*: descartado; todos los compradores compiten por la misma fila y se generan tormentas de conflictos y reintentos.
- *Cola secuencial de un solo hilo*: descartada por latencia inaceptable.

**Decisión:** la fuente de verdad de la unicidad es PostgreSQL. Las demás capas solo optimizan.

1. **Asientos numerados:** tabla `seat_allocation` con índice único parcial que hace físicamente imposible el duplicado:

```sql
CREATE UNIQUE INDEX uq_seat_active ON seat_allocation (event_id, seat_id)
  WHERE status IN ('HELD','SOLD');
```

Un hold es un INSERT con `held_until = now() + TTL`. Antes del INSERT, en la misma transacción, se expira cualquier hold vencido de ese asiento (`UPDATE … SET status = 'EXPIRED' WHERE status = 'HELD' AND held_until < now()`). Si el INSERT falla por violación de unicidad, se responde 409 `SEAT_UNAVAILABLE`. Este conflicto significa “ese asiento ya no está”, no “reintentá”: no se reintenta automáticamente y la UI ofrece elegir otro.

2. **Zonas no numeradas:** decremento atómico condicional y registro del hold en la misma transacción:

```sql
UPDATE zone_inventory SET available = available - :qty
 WHERE zone_id = :z AND available >= :qty;   -- 0 filas = sin cupo (409 ZONE_SOLD_OUT)
INSERT INTO zone_hold (hold_id, zone_id, qty, held_until, status) VALUES (...);
```

La contención sobre la fila contador se acota con la sala de espera (ADR 003). Si el stress test la revelara como cuello de botella, el contador se parte en N sub-contadores por zona.

3. **Locks optimistas** (columna `version`) sobre la orden y el hold, para detectar actualizaciones concurrentes (p. ej. confirmación de pago frente a expiración): 409 `STALE_VERSION`.
4. **Expiración:** un job periódico (supuesto: cada 30 s) pasa los HELD vencidos a EXPIRED y restituye el cupo de las zonas. La corrección no depende del job, porque la regla de disponibilidad evalúa `held_until`.
5. **TTL del hold (supuesto):** 10 minutos, configurable por evento. Al iniciar el pago se extiende una única vez +3 minutos.
6. **Pago tardío:** si el pago se confirma después de expirado el hold, se intenta readquirir el asiento o cupo en la misma transacción; si ya no está libre, se dispara reembolso automático (ADR 009) y la orden queda en `FAILED_LATE_PAYMENT`.
7. **Idempotencia en toda mutación de estado:** header `Idempotency-Key` (UUID v4 generado por la UI por intención del usuario y reutilizado en los reintentos). Tabla `idempotency_key (user_id, method, route, key, request_hash, status, response, created_at)` con unicidad sobre (user_id, method, route, key), en la BD del servicio:
   - misma clave y mismo hash: se devuelve la respuesta almacenada;
   - misma clave con body distinto: 422 `IDEMPOTENCY_KEY_REUSED`;
   - misma clave con request en curso: 409 `IDEMPOTENCY_IN_PROGRESS` con `Retry-After`;
   - retención de 24 h; la clave se propaga a la pasarela de pagos.
8. **Deduplicación en consumidores (inbox):** tabla `inbox (message_id, consumer)` con unicidad, registrada en la misma transacción que el efecto. Es necesaria porque el broker entrega *at-least-once*.
9. **Redis fuera del camino de corrección:** puede usarse para marcar eventos agotados (*fast-reject*), pero toda venta se confirma en PostgreSQL. Si Redis cae, la venta no se ve afectada. En la Etapa I no hace falta Redis.

**Implicancias:**

- Positivas: la garantía vive en la base de datos y resiste fallos de Redis, de la aplicación y de red; sin locks largos, el rendimiento se sostiene bajo concurrencia.
- Negativas / riesgos: la aplicación debe manejar con claridad las excepciones de concurrencia y devolver códigos de error estables para que la UI muestre un mensaje útil; hay contención en el contador de zonas; el job de expiración es un componente más a monitorear.

**Criterio de verificación:** (1) 100 hilos intentan retener el mismo asiento: exactamente 1 éxito y 99 `SEAT_UNAVAILABLE`; (2) una zona con capacidad 50 recibe 200 solicitudes de 1 entrada: exactamente 50 holds y `available = 0`; (3) la misma `Idempotency-Key` enviada 10 veces en paralelo produce 1 orden y 1 cobro; (4) pago confirmado tras expirar el hold, con el asiento ya vendido a otro: reembolso automático y 0 dobles ventas; (5) detener Redis durante la prueba no produce doble venta.
