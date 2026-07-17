"""Base connector interface for all data source connectors.

Every connector implements the same interface so new connectors can be
plugged in without modifying the core ETL engine.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseConnector(ABC):
    """Abstract base class for all data connectors.

    Subclasses must implement:
        - connect(): Open connection to the data source
        - extract(): Return a pandas DataFrame
        - get_schema(): Return column names and inferred types
        - close(): Release resources
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._connected = False

    @abstractmethod
    def connect(self):
        """Open connection to the data source."""
        self._connected = True

    @abstractmethod
    def extract(self, **kwargs) -> pd.DataFrame:
        """Extract data and return as a pandas DataFrame.

        Returns:
            pandas DataFrame containing the extracted data.
        """
        ...

    @abstractmethod
    def get_schema(self) -> list[dict]:
        """Return the schema (column names and inferred types).

        Returns:
            List of dicts: [{"name": str, "type": str, "nullable": bool}]
        """
        ...

    def validate_config(self, required: tuple[str, ...] = ()) -> None:
        missing = [key for key in required if not self.config.get(key)]
        if missing:
            raise ValueError(f"Missing required connector configuration: {', '.join(missing)}")

    def test_connection(self) -> dict:
        try:
            self.connect()
            return {"healthy": True, "connector": self.name, "message": "Connection successful"}
        except Exception as exc:
            return {"healthy": False, "connector": self.name, "message": str(exc)}
        finally:
            self.close()

    def discover_metadata(self) -> dict:
        schema = self.get_schema()
        return {"connector": self.name, "schema": schema, "tables": [], "columns": schema}

    def close(self):
        """Release any held resources."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def preview(self, rows: int = 10) -> pd.DataFrame:
        """Return a small preview of the data.

        Args:
            rows: Number of preview rows.

        Returns:
            DataFrame with at most `rows` rows.
        """
        df = self.extract()
        return df.head(rows)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
