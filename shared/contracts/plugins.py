from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from shared.contracts.models import LifecycleState

SUPPORTED_PLUGIN_TYPES = frozenset(
    {
        "industry_pack",
        "ai_agent",
        "report",
        "widget",
        "connector",
        "workflow",
        "kpi",
        "semantic_library",
        "validation_rule",
    }
)


class PluginManifest(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    name: str = Field(min_length=3)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    plugin_type: str
    description: str = Field(min_length=10)
    entrypoint: str
    platform_version: str = "2.x"
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)

    @field_validator("plugin_type")
    @classmethod
    def supported_type(cls, value: str) -> str:
        if value not in SUPPORTED_PLUGIN_TYPES:
            raise ValueError(f"unsupported plugin type: {value}")
        return value


class PluginLifecycleRegistry:
    def __init__(self):
        self._plugins: dict[str, tuple[PluginManifest, LifecycleState]] = {}

    def install(self, manifest: PluginManifest) -> None:
        current = self._plugins.get(manifest.id)
        if current and current[0].version == manifest.version:
            raise ValueError(
                f"plugin {manifest.id} version {manifest.version} is already installed"
            )
        self._plugins[manifest.id] = (manifest, LifecycleState.ACTIVE)

    def upgrade(self, manifest: PluginManifest) -> None:
        if manifest.id not in self._plugins:
            raise KeyError(f"plugin {manifest.id} is not installed")
        self._plugins[manifest.id] = (manifest, LifecycleState.ACTIVE)

    def disable(self, plugin_id: str) -> None:
        manifest, _ = self._plugins[plugin_id]
        self._plugins[plugin_id] = (manifest, LifecycleState.DISABLED)

    def remove(self, plugin_id: str) -> None:
        self._plugins.pop(plugin_id)

    def get(self, plugin_id: str) -> tuple[PluginManifest, LifecycleState]:
        return self._plugins[plugin_id]

    def list(self, plugin_type: str | None = None) -> list[dict]:
        return [
            {"manifest": manifest.model_dump(), "lifecycle": lifecycle.value}
            for manifest, lifecycle in self._plugins.values()
            if plugin_type is None or manifest.plugin_type == plugin_type
        ]


class IndustryPackDiscovery:
    REQUIRED_DIRECTORIES = frozenset(
        {
            "metadata",
            "semantic",
            "business_glossary",
            "knowledge",
            "kpis",
            "dashboards",
            "reports",
            "widgets",
            "rules",
            "ai",
            "sample_data",
            "validation",
            "documentation",
        }
    )

    @classmethod
    def discover(cls, root: str | Path) -> list[tuple[Path, PluginManifest]]:
        root_path = Path(root)
        discovered = []
        for manifest_path in root_path.rglob("manifest.yaml"):
            pack_path = manifest_path.parent
            missing = cls.REQUIRED_DIRECTORIES.difference(
                child.name for child in pack_path.iterdir() if child.is_dir()
            )
            if missing:
                continue
            discovered.append((pack_path, cls._load_manifest(manifest_path)))
        return discovered

    @staticmethod
    def _load_manifest(path: Path) -> PluginManifest:
        with path.open(encoding="utf-8") as manifest_file:
            content = manifest_file.read()
        try:
            import yaml
        except ImportError:
            payload = {
                key.strip(): value.strip().strip("\"'")
                for line in content.splitlines()
                if ":" in line and not line.lstrip().startswith("#")
                for key, value in [line.split(":", 1)]
            }
        else:
            payload = yaml.safe_load(content)
        return PluginManifest.model_validate(payload)
