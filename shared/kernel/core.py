from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from shared.contracts.events import DomainEvent, EventBus
from shared.contracts.plugins import PluginLifecycleRegistry, PluginManifest
from shared.contracts.registry import PLATFORM_CONTRACTS, ContractRegistry

CommandHandler = Callable[[dict[str, Any]], Any]
QueryHandler = Callable[[dict[str, Any]], Any]


class CommandBus:
    def __init__(self):
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, command_name: str, handler: CommandHandler) -> None:
        if command_name in self._handlers:
            raise ValueError(f"command already registered: {command_name}")
        self._handlers[command_name] = handler

    def dispatch(self, command_name: str, payload: dict[str, Any] | None = None) -> Any:
        try:
            return self._handlers[command_name](payload or {})
        except KeyError as exc:
            raise KeyError(f"unknown command: {command_name}") from exc


class QueryBus:
    def __init__(self):
        self._handlers: dict[str, QueryHandler] = {}

    def register(self, query_name: str, handler: QueryHandler) -> None:
        if query_name in self._handlers:
            raise ValueError(f"query already registered: {query_name}")
        self._handlers[query_name] = handler

    def execute(self, query_name: str, parameters: dict[str, Any] | None = None) -> Any:
        try:
            return self._handlers[query_name](parameters or {})
        except KeyError as exc:
            raise KeyError(f"unknown query: {query_name}") from exc


class ScopedRegistry:
    def __init__(self):
        self._values: dict[tuple[int | None, str], Any] = {}

    def set(self, key: str, value: Any, organization_id: int | None = None) -> None:
        self._values[(organization_id, key)] = value

    def get(self, key: str, organization_id: int | None = None, default: Any = None) -> Any:
        return self._values.get((organization_id, key), self._values.get((None, key), default))

    def list(self, organization_id: int | None = None) -> dict[str, Any]:
        return {
            key: value for (scope, key), value in self._values.items() if scope == organization_id
        }


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, set[str]] = {}

    def register(self, component_id: str, capabilities: list[str]) -> None:
        self._capabilities[component_id] = set(capabilities)

    def supports(self, component_id: str, capability: str) -> bool:
        return capability in self._capabilities.get(component_id, set())

    def find(self, capability: str) -> list[str]:
        return sorted(
            component_id
            for component_id, values in self._capabilities.items()
            if capability in values
        )


class HealthRegistry:
    def __init__(self):
        self._checks: dict[str, Callable[[], bool]] = {}

    def register(self, component_id: str, check: Callable[[], bool]) -> None:
        self._checks[component_id] = check

    def status(self) -> dict[str, bool]:
        return {component_id: bool(check()) for component_id, check in self._checks.items()}


@dataclass
class MarketplaceItem:
    manifest: PluginManifest
    author: str
    license_name: str = "proprietary"
    support_url: str | None = None
    health: str = "unknown"


@dataclass
class PlatformKernel:
    version: str = "3.0.0"
    contracts: ContractRegistry = field(default_factory=lambda: PLATFORM_CONTRACTS)
    events: EventBus = field(default_factory=EventBus)
    commands: CommandBus = field(default_factory=CommandBus)
    queries: QueryBus = field(default_factory=QueryBus)
    plugins: PluginLifecycleRegistry = field(default_factory=PluginLifecycleRegistry)
    extensions: ScopedRegistry = field(default_factory=ScopedRegistry)
    configuration: ScopedRegistry = field(default_factory=ScopedRegistry)
    feature_flags: ScopedRegistry = field(default_factory=ScopedRegistry)
    versions: ScopedRegistry = field(default_factory=ScopedRegistry)
    permissions: ScopedRegistry = field(default_factory=ScopedRegistry)
    audit: ScopedRegistry = field(default_factory=ScopedRegistry)
    capabilities: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    health: HealthRegistry = field(default_factory=HealthRegistry)
    marketplace: dict[str, MarketplaceItem] = field(default_factory=dict)

    def start(self) -> None:
        self.events.publish(
            DomainEvent(
                event_type="kernel.started", resource_type="kernel", resource_id=self.version
            )
        )

    def register_extension(
        self, manifest: PluginManifest, author: str, license_name: str = "proprietary"
    ) -> None:
        self.plugins.install(manifest)
        self.marketplace[manifest.id] = MarketplaceItem(manifest, author, license_name)
        self.capabilities.register(manifest.id, manifest.capabilities)
        self.versions.set(manifest.id, manifest.version)
        self.permissions.set(manifest.id, manifest.permissions)
        self.events.publish(
            DomainEvent(
                event_type="plugin.installed", resource_type="plugin", resource_id=manifest.id
            )
        )

    def set_feature(self, feature: str, enabled: bool, organization_id: int | None = None) -> None:
        self.feature_flags.set(feature, enabled, organization_id)

    def feature_enabled(self, feature: str, organization_id: int | None = None) -> bool:
        return bool(self.feature_flags.get(feature, organization_id, False))
