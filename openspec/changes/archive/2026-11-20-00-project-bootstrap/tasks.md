# Tasks: 00-project-bootstrap

## 1. Gobernanza y Flujo de Trabajo

- [x] 1.1 Actualizar `CONTRIBUTE.md` formalizando ramas protegidas (`main` y `Development`), Conventional Commits obligatorios, política de IA para mitigación de Bus Factor y el modelo de Lanes (Docs sin Issue vs Code/Feat con Issue previo). Verificar inspeccionando `CONTRIBUTE.md`.

## 2. Infraestructura y Persistencia Base (Docker)

- [x] 2.1 Crear el script de inicialización `docker/init-db/01-init-schemas.sql` creando los esquemas `identity`, `catalog`, `ticketing`, `payments` y `reco` junto con la extensión `pg_trgm`. Verificar que el archivo SQL contenga la sintaxis DDL correcta.
- [x] 2.2 Crear `docker-compose.yml` base y `.env.example` definiendo PostgreSQL 16, Redis 7 Alpine, RabbitMQ 3 Management y el servicio API Gateway. Verificar la validez de la configuración con `docker compose config`.

## 3. API Gateway y Health Check (TDD)

- [x] 3.1 Crear la estructura de carpetas de Arquitectura Hexagonal en `src/backend/gateway/` y definir dependencias en `src/backend/gateway/requirements.txt` (FastAPI, Pydantic v2, uvicorn, httpx, pytest, asyncpg, redis, aio-pika). Verificar la presencia de archivos y dependencias.
- [x] 3.2 Escribir pruebas automatizadas en rojo (`src/backend/tests/test_health.py`) validando escenarios EARS de `GET /health` (200 OK y 503 Service Unavailable) e inyección/propagación de `X-Request-ID`. Verificar que los tests fallen inicialmente (TDD en rojo).
- [x] 3.3 Implementar modelos de dominio, caso de uso (`HealthService`), adaptadores de infraestructura (Postgres, Redis, RabbitMQ), middleware de logging/trace y endpoint FastAPI para poner los tests en verde. Verificar con ejecución de `pytest`.

## 4. Integración Continua y Validación Final

- [x] 4.1 Actualizar el pipeline de CI en `.github/workflows/ci.yml` configurando Python 3.12, ejecución de linters y corrida de `pytest` dentro de Docker. Verificar sintaxis del workflow.
- [x] 4.2 Validar la integridad del cambio completo mediante `openspec validate 00-project-bootstrap`.

## Workflow follow-up

- Presentar la propuesta y especificaciones completas para revisión humana antes de aplicar (`apply`).
- Ejecutar el apply e implementar los componentes en el código.
- Archivar el cambio con `openspec archive 00-project-bootstrap`.
