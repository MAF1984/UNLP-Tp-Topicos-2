## ADR 007: Sistema de recomendaciones

**Estado:** Aceptado · **Fecha:** 15/11/2026 · **Etapa:** II

**Drivers:** el enunciado pide generar recomendaciones personalizadas según el historial y las preferencias del cliente, y la Etapa II las integra; el objetivo de negocio es aumentar la conversión sin afectar el flujo de compra.

**Contexto:** no está definido si se construye el motor o se integra uno existente (ver “Puntos a confirmar”). La decisión debe ser válida en ambos casos.

**Alternativas consideradas:**

- *Servicio gestionado de ML*: descartado para el TP por costo y complejidad; sigue siendo posible como adaptador.
- *Recomendador síncrono que consulta las bases transaccionales*: descartado; carga sobre Ticketing y acoplamiento.
- *Algoritmo simple por afinidad y co-compra*: elegido; alcanza para el TP y es explicable.

**Decisión:**

1. Servicio Recommendation asíncrono, con base propia, alimentado por eventos (`ticketing.order.paid.v1`, `catalog.event.published.v1`, `catalog.event.cancelled.v1`) con consumidores idempotentes. No lee las bases de otros servicios.
2. Puerto `RecommendationPort.recommend(userId, limit, context)`. Primer adaptador, un algoritmo propio con tres señales: afinidad por categoría, participante y organizador según el historial de compras (con decaimiento temporal); co-compra calculada en batch (supuesto: cada hora); y popularidad como fallback para usuarios nuevos. Se filtran eventos no publicados, pasados, agotados o ya comprados. Si la cátedra provee un sistema externo, se integra como segundo adaptador.
3. Degradación: timeout corto (supuesto: 300 ms) y fallback a los populares cacheados. El portal nunca falla por las recomendaciones.
4. Privacidad: solo se usan las compras y preferencias propias del usuario; los eventos transportan un id interno, no PII; el usuario puede ver, borrar su historial de preferencias y desactivar la personalización.
5. Los resultados se cachean por usuario en Redis con TTL de 10 min (ADR 004).

**Implicancias:**

- Positivas: desacoplado del camino de compra; reemplazable detrás del puerto; explicable.
- Negativas / riesgos: calidad limitada frente a un modelo de ML; cold start; las recomendaciones pueden quedar levemente desactualizadas.

**Criterio de verificación:** (1) un usuario con compras de un mismo tipo recibe mayoría de ese tipo; (2) un usuario sin historial recibe los populares; (3) con Recommendation detenido, la home sigue cargando; (4) procesar dos veces un mismo evento no altera los puntajes; (5) un usuario con la personalización desactivada recibe solo populares; (6) nunca se recomiendan eventos pasados, cancelados o ya comprados.
