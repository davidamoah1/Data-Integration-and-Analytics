"""AI Plugin System â€” extensible architecture for custom AI capabilities.

Plugins can be:
- Custom providers (new LLM backends)
- Custom assistants (new AI personalities)
- Custom engines (new AI capabilities)
- Custom tools (utilities used by assistants)

Plugins are registered in the database and loaded dynamically.
"""

import importlib
from typing import Any

from sqlalchemy.orm import Session as DbSession

from ai.models import AIPlugin
from ai.providers.base import BaseProvider
from ai.providers.manager import register_provider_class


class PluginRegistry:
    """Registry for AI plugins."""

    def __init__(self, db: DbSession):
        self.db = db
        self._loaded: dict[str, Any] = {}

    def register_plugin(
        self,
        name: str,
        display_name: str,
        plugin_type: str,
        module_path: str,
        description: str = "",
        config_schema: dict | None = None,
        is_system: bool = False,
    ) -> dict:
        """Register a new plugin in the database."""
        plugin = AIPlugin(
            name=name,
            display_name=display_name,
            description=description,
            plugin_type=plugin_type,
            module_path=module_path,
            config_schema=config_schema,
            is_active=False,
            is_system=is_system,
        )
        self.db.add(plugin)
        self.db.commit()
        self.db.refresh(plugin)
        return {
            "id": plugin.id,
            "name": plugin.name,
            "display_name": plugin.display_name,
            "plugin_type": plugin.plugin_type,
            "is_active": plugin.is_active,
        }

    def activate_plugin(self, plugin_id: int) -> bool:
        """Activate a plugin by loading its module."""
        plugin = self.db.query(AIPlugin).filter(AIPlugin.id == plugin_id).first()
        if not plugin:
            return False

        try:
            module = importlib.import_module(plugin.module_path)
            self._loaded[plugin.name] = module

            # Auto-register based on plugin type
            if plugin.plugin_type == "provider":
                # Look for a provider class in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseProvider)
                        and attr != BaseProvider
                    ):
                        register_provider_class(plugin.name, attr)

            plugin.is_active = True
            self.db.commit()
            return True
        except Exception:
            return False

    def deactivate_plugin(self, plugin_id: int) -> bool:
        """Deactivate a plugin."""
        plugin = self.db.query(AIPlugin).filter(AIPlugin.id == plugin_id).first()
        if not plugin:
            return False
        plugin.is_active = False
        self._loaded.pop(plugin.name, None)
        self.db.commit()
        return True

    def list_plugins(self, plugin_type: str | None = None) -> list[dict]:
        """List all registered plugins."""
        query = self.db.query(AIPlugin)
        if plugin_type:
            query = query.filter(AIPlugin.plugin_type == plugin_type)
        plugins = query.order_by(AIPlugin.created_at.desc()).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "plugin_type": p.plugin_type,
                "is_active": p.is_active,
                "is_system": p.is_system,
            }
            for p in plugins
        ]

    def get_plugin(self, name: str) -> Any | None:
        """Get a loaded plugin module by name."""
        return self._loaded.get(name)


# --- Built-in System Plugins ------------------------------------------------


def register_system_plugins(db: DbSession):
    """Register built-in system plugins."""
    registry = PluginRegistry(db)

    # Check if already registered
    existing = db.query(AIPlugin).filter(AIPlugin.is_system.is_(True)).count()
    if existing > 0:
        return

    system_plugins = [
        {
            "name": "openai_provider",
            "display_name": "OpenAI Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.openai_provider",
            "description": "Built-in OpenAI GPT provider",
        },
        {
            "name": "gemini_provider",
            "display_name": "Google Gemini Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.gemini_provider",
            "description": "Built-in Google Gemini provider",
        },
        {
            "name": "deepseek_provider",
            "display_name": "DeepSeek Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.deepseek_provider",
            "description": "Built-in DeepSeek provider",
        },
        {
            "name": "glm_provider",
            "display_name": "GLM Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.glm_provider",
            "description": "Built-in GLM (Zhipu) provider",
        },
        {
            "name": "claude_provider",
            "display_name": "Claude Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.claude_provider",
            "description": "Built-in Anthropic Claude provider",
        },
        {
            "name": "local_llm_provider",
            "display_name": "Local LLM Provider",
            "plugin_type": "provider",
            "module_path": "ai.providers.local_provider",
            "description": "Built-in local LLM provider (Ollama, LM Studio, vLLM)",
        },
    ]

    for p in system_plugins:
        registry.register_plugin(
            name=p["name"],
            display_name=p["display_name"],
            plugin_type=p["plugin_type"],
            module_path=p["module_path"],
            description=p["description"],
            is_system=True,
        )
