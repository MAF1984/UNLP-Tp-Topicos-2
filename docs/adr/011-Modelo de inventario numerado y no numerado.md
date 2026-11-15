## ADR 011: Modelo de inventario numerado y no numerado

**Estado:** Propuesto · **Fecha:** 15/11/2026 · **Etapa:** I

**Drivers:** el enunciado exige dos modalidades de ticket (con asiento específico y por zona) con reglas de negocio distintas; el mecanismo de unicidad del ADR 002 depende de este modelo.

**Contexto:** un mismo evento puede combinar ambas modalidades (por ejemplo, una platea numerada y un campo general). La v1 dejaba esta distinción implícita.

**Alternativas consideradas:**

- *Modelar todo como asientos* (la zona como N asientos “virtuales”): descartado; crea decenas de miles de filas por evento sin un asiento real que mostrar.
- *Modelar todo como contadores*: imposible para las ubicaciones numeradas.
- *Dos estructuras dentro de Ticketing detrás de una interfaz común*: elegida.

**Decisión:**

1. **Entidades en Ticketing:** `inventory_section` (tipo `NUMBERED` o `GENERAL`, nivel de precio), `seat` (solo `NUMBERED`: sección, fila, número y coordenadas para el mapa) y `zone_inventory` (solo `GENERAL`: capacidad y disponibilidad). Los asientos se generan al publicar a partir del layout del venue y no cambian una vez abiertas las ventas.
2. **Reglas por modalidad:**

| Aspecto | Numerada | No numerada (zona) |
|---|---|---|
| Unidad de venta | Un asiento específico | Una cantidad dentro de una zona |
| Selección del cliente | Elige asientos en el mapa (máx. 6 por orden, supuesto) | Elige zona y cantidad (máx. 8 por orden, supuesto) |
| Mecanismo de unicidad | Índice único parcial (ADR 002) | Decremento atómico condicional (ADR 002) |
| Hold | Fila `seat_allocation` en `HELD` | Fila `zone_hold` más decremento |
| Ticket emitido | Uno por asiento, con ubicación | Uno por entrada, sin asiento fijo |
| Devolución | Libera el asiento específico | Restituye la cantidad a la zona |
| Visualización | Mapa de asientos (caché de 2–5 s) | Estado agregado: Disponible, Pocas o Agotado |

Se aplican límites por orden y por usuario y evento (configurables) como medida anti-reventa.

3. **Máquinas de estado** (las únicas transiciones permitidas, verificadas con tests de tabla de transición):
   - Asignación (`seat_allocation` y `zone_hold`): `HELD` → `SOLD`; `HELD` → `EXPIRED`; `HELD` → `RELEASED` (cancelación voluntaria); `SOLD` → `RELEASED` (devolución completada, ADR 008). Solo `HELD` y `SOLD` ocupan inventario; “disponible” significa que no hay una asignación activa.
   - Orden: `PENDING_PAYMENT` → `PAID`, `FAILED`, `EXPIRED` o `FAILED_LATE_PAYMENT`.
   - Ticket: `ISSUED` → `USED` o `REFUND_IN_PROGRESS` → `REFUNDED`.
4. **Interfaz común:** Ticketing expone `reserve`, `confirm` y `release`, y resuelve la modalidad mediante una estrategia por tipo de sección. La UI y las demás capas no conocen la diferencia.
5. **Capacidad:** el owner puede cambiar la capacidad de una zona durante la venta, pero nunca por debajo de lo retenido y vendido. Invariante: `capacity = available + held + sold`.

**Implicancias:**

- Positivas: reglas explícitas por modalidad; cada una usa el mecanismo de concurrencia que le corresponde; el modelo es verificable con invariantes.
- Negativas / riesgos: dos caminos de código que mantener; el layout inmutable tras abrir ventas exige un proceso administrativo para cambios; la asignación de “mejores asientos contiguos” queda fuera de alcance.

**Criterio de verificación:** (1) un evento con una sección numerada y una zona general vende ambas en paralelo, cada una con sus reglas; (2) pedir más de 6 asientos en una orden devuelve 422 `LIMIT_EXCEEDED`; (3) cualquier transición de estado fuera de la tabla falla; (4) devolver un ticket de zona aumenta `available` exactamente en `qty`; (5) tras un stress test, `capacity = available + held + sold` se cumple en todas las zonas y no existen dos asignaciones activas para el mismo asiento.
