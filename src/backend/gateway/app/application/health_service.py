import asyncio

from app.application.ports import InfrastructureHealthPort
from app.domain.models import ComponentStatus, HealthReport


class HealthService:
    """Caso de uso de verificación de salud del sistema (Arquitectura Hexagonal)."""

    def __init__(self, adapter: InfrastructureHealthPort):
        self._adapter = adapter

    async def get_system_health(self) -> HealthReport:
        # Sondeo concurrente con timeout
        results = await asyncio.gather(
            self._adapter.check_postgres(),
            self._adapter.check_redis(),
            self._adapter.check_rabbitmq(),
            return_exceptions=True
        )

        components = {}
        names = ["postgres", "redis", "rabbitmq"]

        all_healthy = True
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                components[name] = ComponentStatus(name=name, healthy=False, error=str(res))
                all_healthy = False
            elif isinstance(res, ComponentStatus):
                components[name] = res
                if not res.healthy:
                    all_healthy = False
            else:
                components[name] = ComponentStatus(name=name, healthy=False, error="Unknown result")
                all_healthy = False

        status_str = "healthy" if all_healthy else "unhealthy"
        return HealthReport(status=status_str, components=components)
