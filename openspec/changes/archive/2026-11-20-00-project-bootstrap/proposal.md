# Proposal: 00-project-bootstrap

## Why

Para iniciar el desarrollo del Trabajo Final de Tópicos de Ingeniería de Software II sin incurrir en deuda cognitiva ni caos arquitectónico, es indispensable establecer primero las bases de gobierno, infraestructura y verificación continua antes de escribir lógica de negocio. Este cambio introduce la "Iteración Cero", proveyendo el entorno reproducible de desarrollo local basado exclusivamente en Docker, la configuración inicial de persistencia políglota con aislamiento de esquemas según DDD, la gobernanza de contribución con políticas de IA y el primer endpoint de sondaje operativo del API Gateway.

## What Changes

- **Gobernanza y Guía de Contribución ([CONTRIBUTE.md](file:///c:/Users/MAF/repos/UNLP-Tp-Topicos-2/CONTRIBUTE.md))**:
  - Incorporación explícita de política de ramas protegidas (`main` y `Development`), prohibición de push directo y flujo `E{Etapa}-feature/<nombre>`.
  - Estándar de mensajes mediante **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
  - **Política de uso de IA y mitigación de Bus Factor**: revisión humana obligatoria del diff antes de cada PR para asegurar la comprensión total del código generado.
  - **Sistema de Carriles (Lanes)**: *Lane Docs* (modificaciones de documentación y ADRs sin requerir Issue previo) vs. *Lane Code/Feat/Fix* (requiere Issue previo, PR formal, CI verde y 2 aprobaciones).
- **Infraestructura Unificada ([docker-compose.yml](file:///c:/Users/MAF/repos/UNLP-Tp-Topicos-2/docker-compose.yml))**:
  - Contenedor **PostgreSQL 16** con script de inicialización (`init-schemas.sql`) que aprovisiona automáticamente los 5 esquemas lógicos aislados (`identity`, `catalog`, `ticketing`, `payments`, `reco`) y la extensión `pg_trgm` (ADR 001, ADR 003, ADR 006).
  - Contenedor **Redis 7 (Alpine)** para soporte de caché look-aside, locks informativos y sala de espera (ADR 003, ADR 004).
  - Contenedor **RabbitMQ 3 (Management)** con exchanges y colas base para eventos de dominio asíncronos bajo patrón Outbox/Inbox (ADR 001, ADR 009).
  - Servicio **API Gateway Base (FastAPI / Python 3.12)** estructurado con Arquitectura Hexagonal, middleware de observabilidad base (inyección de Correlation ID / W3C `traceparent` y timer) y endpoint `/health`.
- **Integración Continua (.github/workflows/ci.yml)**:
  - Pipeline de GitHub Actions ejecutando tests de unidad/integración con `pytest` y linters dentro del entorno Docker/Python 3.12.

## Capabilities

### New Capabilities
- `gateway-health`: Capacidad del API Gateway para exponer sondas de disponibilidad y salud operativa (`GET /health`), verificando el estado del propio gateway y la conectividad hacia los servicios de soporte (PostgreSQL, Redis, RabbitMQ).

### Modified Capabilities
*(Ninguna - primer cambio del proyecto)*

## Impact

- **Código y APIs**: Estructura inicial del proyecto en `src/backend/gateway/` respetando Arquitectura Hexagonal (puertos, adaptadores y aplicación).
- **Infraestructura**: Creación de `docker-compose.yml`, scripts de inicialización de base de datos y archivos `.env.example`.
- **Dependencias**: Definición de `requirements.txt` base para Python 3.12 (FastAPI, Uvicorn, SQLModel/SQLAlchemy, asyncpg, redis, aio-pika, pydantic v2, pytest, pytest-asyncio).
- **ADRs Vinculados**: Respeta y sienta las bases de [ADR 001](file:///c:/Users/MAF/repos/UNLP-Tp-Topicos-2/docs/adr/001-Arquitectura%20base%20de%20microservicios.md), [ADR 005](file:///c:/Users/MAF/repos/UNLP-Tp-Topicos-2/docs/adr/005-Observabilidad,%20bit%C3%A1cora%20de%20solicitudes%20HTTP%20y%20auditor%C3%ADa.md) y [ADR 012](file:///c:/Users/MAF/repos/UNLP-Tp-Topicos-2/docs/adr/012-Requisitos%20no%20funcionales%20cuantificados.md).
