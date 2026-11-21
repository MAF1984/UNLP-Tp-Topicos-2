import asyncio
import os
import time

from app.application.ports import InfrastructureHealthPort
from app.domain.models import ComponentStatus


class SystemInfrastructureAdapter(InfrastructureHealthPort):
    """Adaptador de infraestructura real para PostgreSQL, Redis y RabbitMQ."""

    def __init__(self):
        self.pg_host = os.getenv("POSTGRES_HOST", "localhost")
        self.pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.rabbit_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))

    async def _check_socket(self, host: str, port: int, name: str, timeout: float = 2.0) -> ComponentStatus:
        start = time.perf_counter()
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            latency = (time.perf_counter() - start) * 1000.0
            return ComponentStatus(name=name, healthy=True, latency_ms=round(latency, 2))
        except (TimeoutError, OSError) as e:
            latency = (time.perf_counter() - start) * 1000.0
            return ComponentStatus(name=name, healthy=False, latency_ms=round(latency, 2), error=str(e))

    async def check_postgres(self) -> ComponentStatus:
        return await self._check_socket(self.pg_host, self.pg_port, "postgres")

    async def check_redis(self) -> ComponentStatus:
        return await self._check_socket(self.redis_host, self.redis_port, "redis")

    async def check_rabbitmq(self) -> ComponentStatus:
        return await self._check_socket(self.rabbit_host, self.rabbit_port, "rabbitmq")
