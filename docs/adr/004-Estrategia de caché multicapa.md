    ## ADR 004: Estrategia de caché multicapa

**Estado:** Aceptado (rev. 2) · **Fecha:** 15/11/2026 · **Etapa:** II (el cacheo HTTP de assets puede adelantarse a la Etapa I)

**Drivers:** el portal de clientes es fuertemente de lectura; el enunciado pide definir qué cachear, dónde (cliente, CDN, servicio, distribuido), política de invalidación y TTL según el tipo de dato.

**Contexto:** consultar repetidamente la base primaria por catálogo, imágenes y disponibilidad es ineficiente y costoso. El riesgo principal es mostrar como “disponible” un evento que acaba de agotarse.

**Alternativas consideradas:**

- *Todo en la base primaria*: descartado por latencia y límites de conexiones.
- *Solo caché de cliente*: insuficiente para usuarios nuevos. La v1 la descartaba por completo, pero `Cache-Control` y ETag son casi gratuitos y se incluyen como una capa más.
- *Una única caché distribuida*: descartada; convierte a Redis en punto único de falla de lectura.

**Decisión:** caché en cuatro capas: navegador (`Cache-Control`, ETag), CDN/edge, in-process por servicio y distribuida (Redis).

| Dato | Capa | TTL | Invalidación |
|---|---|---|---|
| Assets estáticos con hash en el nombre (CSS, JS) | Navegador + CDN | 1 año, `immutable` | Nuevo nombre de archivo en cada build |
| Imágenes de eventos | CDN + navegador | 24 h | Purga por surrogate key al editar el evento |
| Detalle de evento publicado | Redis (+ CDN opcional) | 60 s ± jitter | Eventos `event.updated`, `cancelled`, `published` |
| Listados y resultados de búsqueda | Redis | 30 s | Versión de namespace; TTL |
| Disponibilidad por zona (informativa) | Redis | 5 s | TTL; push opcional desde Ticketing |
| Mapa de asientos (informativo) | Redis | 2–5 s | TTL; push por SSE en eventos calientes |
| Datos de referencia (categorías, tipos, venues) | In-process | 5 min | TTL |
| Claves públicas JWKS | In-process | 10 min | TTL; refresco ante `kid` desconocido |
| Perfil, órdenes, tickets, pagos | Sin caché compartida | — | `Cache-Control: private, no-store` |

Reglas:

1. **El camino de compra nunca lee de caché.** Hold, orden y pago consultan siempre PostgreSQL (ADR 002). La disponibilidad cacheada es solo informativa y la UI tolera un 409 al intentar comprar.
2. **Redis de caché es una instancia distinta** de la del Waiting Room y de cualquier dato de estado: política `allkeys-lru` con `maxmemory`. Ningún dato cacheado es fuente de verdad. Si cae, las lecturas degradan a PostgreSQL con circuit breaker y límite de concurrencia, sin devolver errores.
3. **Invalidación explícita** por eventos de dominio (borran claves y purgan la CDN por surrogate key); el TTL actúa como red de seguridad. En listados se usa una clave con número de versión del namespace.
4. **Protección contra cache stampede:** request coalescing (*single-flight*), `stale-while-revalidate`, jitter de ±10–20 % en los TTL y precalentamiento de los eventos por abrir.
5. Nunca se cachea en capas compartidas contenido personalizado o sensible.

**Implicancias:**

- Positivas: reducción drástica de latencia y de carga sobre la base primaria; degradación controlada ante la caída de Redis.
- Negativas / riesgos: inconsistencia acotada por los TTL (el rango de 10–30 s de la v1 era excesivo para el mapa de asientos); más piezas operativas; posibles invalidaciones perdidas (mitigadas por el TTL).

**Criterio de verificación:** (1) con caché caliente, el p95 del detalle de evento es < 200 ms con un hit ratio ≥ 90 % (supuesto) en el stress test; (2) tras `event.updated`, el cambio es visible en ≤ 5 s; (3) con Redis detenido, el catálogo responde desde PostgreSQL sin errores 5xx; (4) 1.000 requests simultáneos sobre una clave expirada generan una sola consulta a la base; (5) los endpoints de compra devuelven `Cache-Control: no-store`.
