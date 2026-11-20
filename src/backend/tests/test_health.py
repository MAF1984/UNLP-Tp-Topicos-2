import pytest
from httpx import ASGITransport, AsyncClient

# Importaremos app desde gateway.main una vez implementado
from main import app


@pytest.mark.asyncio
async def test_health_check_all_healthy(monkeypatch):
    """
    Scenario: Todos los componentes operativos
    GIVEN que PostgreSQL, Redis y RabbitMQ responden satisfactoriamente
    WHEN se invoca GET /health
    THEN el sistema retorna 200 OK con status healthy
    """
    # Mocking adapters to return healthy
    from app.application.ports import InfrastructureHealthPort
    from app.domain.models import ComponentStatus

    class HealthyMockAdapter(InfrastructureHealthPort):
        async def check_postgres(self) -> ComponentStatus:
            return ComponentStatus(name="postgres", healthy=True, latency_ms=1.2)

        async def check_redis(self) -> ComponentStatus:
            return ComponentStatus(name="redis", healthy=True, latency_ms=0.8)

        async def check_rabbitmq(self) -> ComponentStatus:
            return ComponentStatus(name="rabbitmq", healthy=True, latency_ms=1.5)

    from app.infrastructure.api.routes import health
    health.get_health_service = lambda: health.HealthService(adapter=HealthyMockAdapter())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["components"]["postgres"]["healthy"] is True
        assert data["components"]["redis"]["healthy"] is True
        assert data["components"]["rabbitmq"]["healthy"] is True
        assert "X-Request-ID" in response.headers

@pytest.mark.asyncio
async def test_health_check_component_failure(monkeypatch):
    """
    Scenario: Fallo o degradación en componente de soporte
    GIVEN que un servicio (p.ej. PostgreSQL) falla
    WHEN se invoca GET /health
    THEN el sistema retorna 503 Service Unavailable con status unhealthy
    """
    from app.application.ports import InfrastructureHealthPort
    from app.domain.models import ComponentStatus

    class DegradedMockAdapter(InfrastructureHealthPort):
        async def check_postgres(self) -> ComponentStatus:
            return ComponentStatus(name="postgres", healthy=False, error="Connection timeout", latency_ms=2000.0)

        async def check_redis(self) -> ComponentStatus:
            return ComponentStatus(name="redis", healthy=True, latency_ms=0.5)

        async def check_rabbitmq(self) -> ComponentStatus:
            return ComponentStatus(name="rabbitmq", healthy=True, latency_ms=1.1)

    from app.infrastructure.api.routes import health
    health.get_health_service = lambda: health.HealthService(adapter=DegradedMockAdapter())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["postgres"]["healthy"] is False
        assert "Connection timeout" in data["components"]["postgres"]["error"]

@pytest.mark.asyncio
async def test_request_id_propagation():
    """
    Scenario: Trazabilidad HTTP en health check
    GIVEN una petición con header X-Request-ID provisto
    WHEN se procesa por el middleware
    THEN el mismo X-Request-ID se propaga en la respuesta
    """
    transport = ASGITransport(app=app)
    custom_trace_id = "test-custom-trace-uuid-1234"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Request-ID": custom_trace_id})
        assert response.headers.get("X-Request-ID") == custom_trace_id
