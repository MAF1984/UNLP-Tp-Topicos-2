from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ComponentStatus:
    name: str
    healthy: bool
    latency_ms: float = 0.0
    error: str | None = None

@dataclass(frozen=True)
class HealthReport:
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    components: dict[str, ComponentStatus] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"
