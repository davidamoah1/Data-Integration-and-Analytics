"""Base connector abstract class and connector registry.

Every connector implements a standardised interface:
  - metadata
  - test_connection
  - extract_data
  - validate_config
"""

from __future__ import annotations

import abc
import logging
from typing import Any, ClassVar

import pandas as pd

logger = logging.getLogger("etl_project.connectors")


class BaseConnector(abc.ABC):
    """Abstract base class for all connectors."""

    # Metadata — overridden by subclasses
    type_code: ClassVar[str] = ""
    display_name: ClassVar[str] = ""
    category: ClassVar[str] = ""
    description: ClassVar[str] = ""
    icon: ClassVar[str] = ""
    is_africa_first: ClassVar[bool] = False
    region: ClassVar[str] = "global"

    # JSON schemas for configuration and auth (optional)
    config_schema: ClassVar[dict[str, Any] | None] = None
    auth_schema: ClassVar[dict[str, Any] | None] = None

    def __init__(self, configuration: dict[str, Any] | None = None, auth_config: dict[str, Any] | None = None):
        self.configuration = configuration or {}
        self.auth_config = auth_config or {}

    @abc.abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Test the connection. Return {success, message, details}."""
        ...

    @abc.abstractmethod
    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        """Extract data from the source. Return a DataFrame."""
        ...

    def validate_config(self) -> list[str]:
        """Validate the configuration. Return list of error messages (empty = valid)."""
        return []

    def get_metadata(self) -> dict[str, Any]:
        """Return connector metadata."""
        return {
            "type_code": self.type_code,
            "display_name": self.display_name,
            "category": self.category,
            "description": self.description,
            "icon": self.icon,
            "is_africa_first": self.is_africa_first,
            "region": self.region,
            "config_schema": self.config_schema,
            "auth_schema": self.auth_schema,
        }


class ConnectorRegistry:
    """Registry for connector types."""

    _registry: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_class: type[BaseConnector]) -> type[BaseConnector]:
        """Register a connector class. Can be used as a decorator."""
        code = connector_class.type_code
        if not code:
            raise ValueError(f"Connector {connector_class.__name__} has no type_code")
        cls._registry[code] = connector_class
        logger.info(f"Registered connector: {code}")
        return connector_class

    @classmethod
    def get(cls, type_code: str) -> type[BaseConnector] | None:
        return cls._registry.get(type_code)

    @classmethod
    def create(cls, type_code: str, configuration: dict | None = None, auth_config: dict | None = None) -> BaseConnector | None:
        connector_class = cls._registry.get(type_code)
        if not connector_class:
            return None
        return connector_class(configuration=configuration, auth_config=auth_config)

    @classmethod
    def list_types(cls) -> list[dict[str, Any]]:
        return [
            {
                "type_code": c.type_code,
                "display_name": c.display_name,
                "category": c.category,
                "description": c.description,
                "icon": c.icon,
                "is_africa_first": c.is_africa_first,
                "region": c.region,
                "config_schema": c.config_schema,
                "auth_schema": c.auth_schema,
            }
            for c in cls._registry.values()
        ]

    @classmethod
    def list_by_category(cls, category: str) -> list[dict[str, Any]]:
        return [t for t in cls.list_types() if t["category"] == category]
