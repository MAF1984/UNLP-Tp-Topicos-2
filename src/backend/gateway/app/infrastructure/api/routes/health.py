from fastapi import APIRouter, Response, status

from app.application.health_service import HealthService
from app.infrastructure.adapters.infrastructure_checker import (
    SystemInfrastructureAdapter,
)

router = APIRouter(tags=["Health"])

# Función proveedora inyectable para testing
def get_health_service() -> HealthService:
    return HealthService(adapter=SystemInfrastructureAdapter())

@router.get("/health", summary="Sonda de disponibilidad y salud operativa")
async def health_check(response: Response):
    service = get_health_service()
    report = await service.get_system_health()

    if not report.is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": report.status,
        "timestamp": report.timestamp,
        "components": {
            name: {
                "name": comp.name,
                "healthy": comp.healthy,
                "latency_ms": comp.latency_ms,
                "error": comp.error
            }
            for name, comp in report.components.items()
        }
    }
