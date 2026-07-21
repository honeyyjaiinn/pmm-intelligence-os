from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class Signal:
    source: str
    source_type: str
    text: str
    created_at: str | None = None
    rating: float | None = None
    url: str | None = None
    external_id: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Connector(ABC):
    @abstractmethod
    def fetch(self, **kwargs: Any) -> list[Signal]:
        raise NotImplementedError
