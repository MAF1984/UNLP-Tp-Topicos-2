## ADR 005: Observabilidad, bitácora de solicitudes HTTP y auditoría

**Estado:** Aceptado (rev. 2) · **Fecha:** 15/11/2026 · **Etapa:** I

**Drivers:** el enunciado pide instrumentar cada solicitud HTTP (timer al recibirla, autenticación, registro de resultado y tiempo, respuesta); en un entorno distribuido, resolver incidentes y auditar acciones exige observabilidad estructurada.

**Contexto:** hay dos necesidades con requisitos distintos que la v1 mezclaba. La *observabilidad operativa* (logs, métricas, trazas) puede muestrearse y rotarse. La *auditoría de negocio* (quién aprobó una devolución, quién modificó o canceló un evento) debe ser durable, inmutable y completa.

**Alternativas consideradas:**

- *Logs en texto plano*: descartados; dificultan la ingestión y el análisis.
- *Instrumentación manual en cada controlador*: descartada; viola DRY y se olvida.
- *Registrar solo las respuestas exitosas*: descartado; se pierden los 401 y los 500, que son los más valiosos.
- *Obtener las métricas de latencia parseando logs*: descartado; los histogramas son más baratos y precisos.

**Decisión:**

1. **Middleware global** en cada servicio (paquete compartido por lenguaje; el Gateway también registra), con este orden:

   1. Iniciar el timer (reloj monotónico) antes de cualquier procesamiento, de modo que el tiempo medido incluya la autenticación.
   2. Extraer el header `traceparent` (W3C Trace Context) o generar uno nuevo, y propagarlo en llamadas salientes y eventos. Reemplaza al Correlation ID propio de la v1.
   3. Autenticar y autorizar (ADR 010), midiendo su duración por separado (`auth_ms`).
   4. Ejecutar el handler.
   5. En un hook de fin de respuesta (que corre también ante 401, 403, 500, timeouts y cortes del cliente), escribir el log estructurado y observar el histograma.

2. **Campos del log JSON:** timestamp, service, trace_id, span_id, method, route (plantilla, no el path crudo), status, duration_ms, auth_ms, outcome (`OK`, `CLIENT_ERROR`, `SERVER_ERROR`, `AUTH_FAILED`, `ABORTED`), user_id y rol (si hay sesión), hash de la `Idempotency-Key` y tamaños de request y response.
3. **Sanitización por lista blanca:** no se registran cuerpos por defecto; nunca se registran `Authorization`, `Cookie` ni tokens; contraseñas y números de tarjeta se enmascaran; los query strings se filtran. Un test automático falla si aparecen patrones sensibles en los logs.
4. **Salida asíncrona:** stdout en JSON hacia un agente (OpenTelemetry Collector o Fluent Bit); el hilo del request nunca espera I/O de logging.
5. **Métricas:** histograma `http_server_duration_seconds{service,route,method,status_class}` para p50, p95 y p99 y tasa de error por ruta; métricas de negocio (holds, ventas, expiraciones, conflictos 409) y de infraestructura (consumer lag, pool de conexiones). Se registra el 100 % de las solicitudes en logs; las trazas OpenTelemetry usan muestreo (supuesto: 10 %, con 100 % de errores).
6. **Datos de tarjeta:** no pasan por ningún servicio propio (tokenización de la pasarela, ADR 009), lo que reduce el alcance PCI.
7. **Auditoría de negocio como mecanismo separado:** tabla `audit_log` *append-only* en cada servicio (el rol de la aplicación solo tiene INSERT), escrita en la misma transacción que el cambio auditado. Campos: actor, rol, acción, recurso, estado anterior y posterior, motivo, trace_id, timestamp. Se auditan las aprobaciones y rechazos de devoluciones, la creación, edición y cancelación de eventos, los cambios de rol, las acciones administrativas y los reembolsos automáticos. Retención: logs operativos 30 días; auditoría 5 años (propuesta, a confirmar con el cliente).

**Implicancias:**

- Positivas: trazabilidad end-to-end, dashboards de rendimiento precisos y requisitos de retención diferenciados.
- Negativas / riesgos: mayor volumen de almacenamiento; overhead mínimo de CPU por request; riesgo de registrar PII si falla la sanitización; la auditoría agrega una escritura a la transacción de negocio.

**Criterio de verificación:** (1) toda respuesta, incluidas 401 y 500, genera exactamente una línea de log con `duration_ms` y `trace_id`; (2) una compra completa comparte el mismo `trace_id` en Gateway, Ticketing y Payments; (3) el test de sanitización no encuentra tokens, contraseñas ni PAN; (4) aprobar una devolución crea un registro de auditoría en la misma transacción y el rol de la aplicación no puede hacer UPDATE ni DELETE sobre `audit_log`; (5) el overhead del middleware es < 2 ms en p95 (supuesto).
