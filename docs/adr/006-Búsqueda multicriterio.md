## ADR 006: Búsqueda multicriterio

**Estado:** Aceptado (rev. 2; dividido del ADR 006 de la v1) · **Fecha:** 15/11/2026 · **Etapa:** III (el modelo de datos se prepara en la Etapa I)

**Drivers:** el enunciado pide buscar eventos por tipo, organizador, participante y fecha, con ordenamiento por relevancia, y ubica la búsqueda avanzada en la Etapa III; no hay que retrasar el núcleo transaccional ni forzar migraciones masivas.

**Contexto:** la v1 agrupaba búsqueda y recomendaciones en la Etapa II, lo que contradice el enunciado (recomendación en la II, búsqueda avanzada en la III). Se separan: las recomendaciones pasan al ADR 007.

**Alternativas consideradas:**

- *SQL con `LIKE` / `ILIKE`*: descartado; sin scoring de relevancia, sin tolerancia a errores tipográficos y con índices ineficientes.
- *Motor dedicado (OpenSearch o Elasticsearch) desde el día 1*: descartado; riesgo para el lanzamiento del núcleo y costo operativo.
- *PostgreSQL Full-Text Search con `pg_trgm`* (alternativa intermedia que la v1 no consideraba): elegida como primera implementación. `tsvector` con pesos (título A, participantes B, organizador C, descripción D), `ts_rank` para relevancia, `pg_trgm` para typos, índices GIN y filtros por tipo, fecha y organizador. No suma infraestructura.
- *OpenSearch administrado*: queda como evolución si FTS no alcanza (volumen, facetas, latencia).

**Decisión:**

1. El servicio Search mantiene una proyección de lectura (`event_search`, con `tsvector` y campos filtrables) alimentada por eventos de dominio de Catalog (`catalog.event.published.v1`, `updated`, `cancelled`) y de Ticketing (`ticketing.order.paid.v1`, para señales de popularidad). Los consumidores son idempotentes (inbox).
2. La proyección puede reconstruirse por completo (*reindex*) desde Catalog, que es la fuente de verdad. Cada documento lleva una versión para descartar eventos viejos.
3. El acceso es mediante un puerto `SearchPort`: PostgreSQL FTS es el primer adaptador y OpenSearch sería el segundo, sin cambiar a los consumidores.
4. API: `GET /events/search?q=&type=&organizer=&participant=&from=&to=&sort=relevance|date&cursor=`, con paginación por cursor y resultados cacheados 30 s (ADR 004). Se configura el diccionario `spanish`.
5. **Etapa I:** el modelo de Catalog incluye desde el inicio organizador, participantes o artistas (N:M con rol), tipo de evento, categorías y tags, venue, fecha y hora de inicio y fin, y estado de publicación. Los eventos de dominio se escriben en la tabla `outbox` (ADR 009) aunque el relay al broker se conecte después.
6. La proyección es eventualmente consistente (lag objetivo < 5 s, supuesto). Lo que muestra la búsqueda es informativo; la compra siempre se confirma contra Ticketing.

**Implicancias:**

- Positivas: relevancia y filtros múltiples sin nueva infraestructura; el núcleo transaccional sale primero; una migración futura queda aislada detrás del puerto.
- Negativas / riesgos: FTS tiene límites (facetas, escala, análisis lingüístico); hay que mantener la proyección y el reindex; el lag de indexación es visible; el estado entre la fuente de verdad y la proyección puede divergir temporalmente.

**Criterio de verificación:** (1) buscar por participante, organizador, tipo y rango de fechas devuelve exactamente el conjunto esperado; (2) una consulta con typo (por ejemplo, “Festival de Jaz”) encuentra el evento; (3) una coincidencia en el título rankea por encima de una coincidencia en la descripción; (4) borrar la proyección y reindexar produce resultados idénticos; (5) procesar dos veces el mismo evento no duplica documentos; (6) un evento publicado aparece en la búsqueda en ≤ 5 s.
