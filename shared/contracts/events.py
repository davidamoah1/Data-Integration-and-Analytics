from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    organization_id: int | None = None
    actor_id: int | None = None
    resource_type: str
    resource_id: str | int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._subscribers[event.event_type]:
            handler(event)
