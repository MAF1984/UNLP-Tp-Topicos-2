## ADR 001: Arquitectura base de microservicios

**Estado:** Aceptado (rev. 2) · **Fecha:** 15/11/2026 · **Etapa:** I (se refina en II y III)

**Drivers:** el enunciado exige microservicios con límites de servicio, comunicación sync/async, manejo de fallos parciales, consistencia eventual y despliegue independiente; carga asimétrica (picos de compra frente a tráfico bajo de administración y gestión de eventos); necesidad de aislar el ciclo de vida de los componentes críticos.

**Contexto:** el sistema atiende tres perfiles (administradores, event owners y clientes). La venta genera picos impredecibles de alta concurrencia; la administración y el diseño de eventos tienen poco tráfico pero requieren disponibilidad. Hay que poder desplegar y escalar los componentes de forma independiente sin afectar los flujos críticos.

**Alternativas consideradas:**

- *Monolito tradicional*: descartado. Un pico de compra degrada los portales de administración y de event owners, y todo escala junto.
- *Monolito modular*: descartado como arquitectura de despliegue. También escala horizontalmente, pero como una sola unidad: no permite escalar ni desplegar de forma aislada el camino de compra y pagos, y el enunciado pide microservicios. Se adopta como estructura interna de cada servicio (módulos con límites claros).
- *Microservicios muy granulares (uno por entidad)*: descartado; trasladarían transacciones distribuidas al camino crítico de compra.

**Decisión:**

1. Pocos servicios, con límites por dominio y por transacción:

| Servicio | Responsabilidad | Etapa |
|---|---|---|
| Identity | Usuarios, roles, emisión de tokens (ADR 010) | I |
| Catalog | Eventos, organizadores, participantes, venues, publicación | I |
| Ticketing | Inventario numerado y por zona, holds, órdenes, tickets y devoluciones. Un único límite transaccional para el camino crítico (ADR 002, 011) | I |
| Payments | Integración con la pasarela, webhooks, reembolsos (ADR 009) | I |
| Waiting Room | Cola virtual y admisión (ADR 003) | III |
| Search / Recommendation | Búsqueda e índices, recomendaciones (ADR 006, 007) | II–III |

Se agrega un API Gateway (autenticación, rate limiting, ruteo, bitácora). No se crea un servicio de reportes: la v1 lo mencionaba sin que exista un requisito; si hiciera falta, se resuelve con una réplica de lectura o una proyección.

2. **Base de datos por servicio** (PostgreSQL): esquemas lógicos separados y credenciales propias, sin acceso cruzado. En el TP pueden compartir instancia física. La integración entre servicios es solo por API o por eventos.
3. **Comunicación:**
   - Sincrónica: REST/JSON con contrato OpenAPI *contract-first* (alineado con OpenSpec). gRPC queda como opción interna si una medición lo justifica.
   - Asincrónica: RabbitMQ (quorum queues, exchanges por tópico, DLQ) con eventos de dominio versionados (p. ej. `ticketing.order.paid.v1`) publicados mediante Outbox (ADR 009). Se elige por simplicidad operativa y soporte nativo de reintentos y DLQ; Kafka se reevaluaría si se necesitara replay masivo.
   - Regla: el camino de compra (Gateway → Ticketing) hace como máximo una llamada síncrona entre servicios (Ticketing → Payments); el resto viaja por eventos.
4. **Consistencia:** sagas con consistencia eventual (ADR 009). Como el broker entrega *at-least-once*, todos los consumidores son idempotentes (ADR 002).
5. **Fallos parciales:** timeouts explícitos en toda llamada (supuesto: 2 s en lecturas, 5 s hacia la pasarela); reintentos con backoff exponencial y jitter solo sobre operaciones idempotentes; circuit breaker; bulkheads (pools de conexiones e hilos separados por dependencia); DLQ con alerta. Degradación explícita: sin Search/Recommendation, el catálogo y la compra siguen; sin Payments no se aceptan compras nuevas pero el catálogo sigue (*fail closed* en la venta).
6. **Despliegue:** un contenedor Docker por servicio, pipeline CI/CD por servicio (build, tests de unidad, tests de contrato, imagen versionada) y Docker Compose como orquestador del TP. Los manifiestos se mantienen compatibles con Kubernetes como evolución, no como requisito. Las migraciones de BD son retrocompatibles (expand/contract) para permitir despliegues independientes.

**Implicancias:**

- Positivas: escalado y despliegue independiente de los cuellos de botella; aislamiento de fallos parciales; transaccionalidad fuerte dentro de Ticketing.
- Negativas / riesgos: mayor complejidad operativa (CI/CD, observabilidad, broker); consistencia eventual entre servicios; riesgo de sobre-fragmentación (mitigado con pocos servicios y límites transaccionales); mayor costo de pruebas de integración (mitigado con tests de contrato).

**Criterio de verificación:** (1) con Search/Recommendation detenido, catálogo y compra siguen operando; (2) se despliega una nueva versión de Catalog sin reiniciar Ticketing; (3) ningún servicio accede a la BD de otro (verificado por permisos y en CI); (4) con Payments detenido, Ticketing responde con un error controlado y no deja holds colgados (expiran).