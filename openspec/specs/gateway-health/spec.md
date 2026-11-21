# gateway-health Specification

## Purpose
Provee un mecanismo estandarizado de monitoreo y sondaje de salud operativa (health check) a través del API Gateway, verificando la disponibilidad del gateway y la conectividad con la infraestructura de soporte (PostgreSQL, Redis y RabbitMQ).

## Requirements

### Requirement: Endpoint de salud operativa del Gateway
El API Gateway SHALL exponer un endpoint HTTP `GET /health` público que reporte el estado operativo del servicio y verifique la conectividad hacia PostgreSQL, Redis y RabbitMQ.

#### Scenario: Todos los componentes operativos
- **WHEN** un cliente o sistema de orquestación realiza una petición `GET /health` y todos los servicios de soporte (PostgreSQL, Redis, RabbitMQ) responden satisfactoriamente
- **THEN** el sistema responde con código HTTP 200 (OK), header `Content-Type: application/json` y cuerpo con `status: "healthy"` y el desglose de cada servicio en `healthy`

#### Scenario: Fallo o degradación en componente de soporte
- **WHEN** un cliente o sistema de orquestación realiza una petición `GET /health` y al menos un servicio de soporte no responde o supera el timeout de sondeo (2 segundos)
- **THEN** el sistema responde con código HTTP 503 (Service Unavailable), cuerpo con `status: "degraded"` o `"unhealthy"` y el detalle de cuál componente falló

### Requirement: Trazabilidad HTTP en health check
Toda petición al endpoint de salud SHALL incorporar trazabilidad distribuida mediante inyección de identificadores de correlación y registro de duración en milisegundos.

#### Scenario: Petición sin Correlation-ID previo
- **WHEN** llega una petición `GET /health` sin encabezados de trazabilidad
- **THEN** el middleware genera un nuevo identificador de correlación (UUID v4 o W3C `traceparent`), lo inyecta en el contexto y lo retorna en el header `X-Request-ID` de la respuesta

#### Scenario: Petición con Correlation-ID existente
- **WHEN** llega una petición `GET /health` con el encabezado `X-Request-ID` provisto por el cliente
- **THEN** el middleware propaga dicho identificador de correlación y lo incluye en la respuesta y en la bitácora interna
