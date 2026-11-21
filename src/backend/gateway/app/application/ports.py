from abc import ABC, abstractmethod

from app.domain.models import ComponentStatus


class InfrastructureHealthPort(ABC):
    """Puerto de salida para sondear componentes de infraestructura."""

    @abstractmethod
    async def check_postgres(self) -> ComponentStatus:
        pass

    @abstractmethod
    async def check_redis(self) -> ComponentStatus:
        pass

    @abstractmethod
    async def check_rabbitmq(self) -> ComponentStatus:
        pass
