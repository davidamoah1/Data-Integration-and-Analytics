"""Data source resolver — enforces strict separation between Production, Demo, and Test data.

Production data sources:
    - User-uploaded files (registered via DatasetLibrary)
    - Connected databases (registered via DatasetLibrary)
    - Never falls back to demo or test data

Demo data sources:
    - Curated demo datasets (opt-in, from demo_datasets/ directory)
    - Only used when explicitly requested or SEED_DEMO_DATA=true

Test data sources:
    - Test fixtures in tests/ directory
    - Only available when PYTEST_RUNNING env var is set
"""

from __future__ import annotations

import os

from dataset_library import DataTier, get_dataset_library


class DataSourceError(Exception):
    """Raised when a data source is not available or not allowed."""


class DataSourceResolver:
    """Resolves data sources with strict tier enforcement.

    Production mode: Only PRODUCTION tier datasets are accessible.
    Demo mode: PRODUCTION and approved DEMO datasets are accessible.
    Test mode: All tiers accessible (for testing only).
    """

    def __init__(self):
        self._library = get_dataset_library()
        self._is_test = os.getenv("PYTEST_RUNNING", "0") == "1"
        self._demo_enabled = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")

    @property
    def mode(self) -> str:
        if self._is_test:
            return "test"
        if self._demo_enabled:
            return "demo"
        return "production"

    def resolve(self, dataset_id: str) -> DataTier:
        """Resolve a dataset ID and verify it's allowed in the current mode.

        Returns the data tier of the resolved dataset.
        Raises DataSourceError if the dataset is not found or not allowed.
        """
        entry = self._library.get(dataset_id)
        if not entry:
            raise DataSourceError(f"Dataset '{dataset_id}' not found in library.")

        if self._is_test:
            # Test mode: all tiers allowed
            return entry.tier

        if entry.tier == DataTier.PRODUCTION:
            return entry.tier

        if entry.tier == DataTier.DEMO:
            if self._demo_enabled and entry.approved_for_demo:
                return entry.tier
            raise DataSourceError(
                f"Dataset '{dataset_id}' is a demo dataset. "
                "Demo data is not enabled in production. Set SEED_DEMO_DATA=true to allow demo datasets."
            )

        if entry.tier == DataTier.TEST:
            raise DataSourceError(
                f"Dataset '{dataset_id}' is a test dataset. "
                "Test datasets are not available outside of test environments."
            )

        raise DataSourceError(f"Dataset '{dataset_id}' has unknown tier: {entry.tier}")

    def get_available_datasets(self) -> list[dict]:
        """Get all datasets available in the current mode."""
        all_entries = self._library.list_all()
        available = []
        for entry in all_entries:
            try:
                self.resolve(entry.id)
                available.append(entry.to_dict())
            except DataSourceError:
                continue
        return available

    def is_demo_available(self) -> bool:
        """Check if demo datasets are available in the current mode."""
        return self._demo_enabled or self._is_test

    def assert_production_data(self, dataset_id: str) -> None:
        """Assert that a dataset is production-tier. Raises if not."""
        entry = self._library.get(dataset_id)
        if not entry:
            raise DataSourceError(f"Dataset '{dataset_id}' not found.")
        if entry.tier != DataTier.PRODUCTION:
            raise DataSourceError(
                f"Dataset '{dataset_id}' is not production-tier (tier={entry.tier.value}). "
                "Production operations require production-tier data."
            )


_resolver: DataSourceResolver | None = None


def get_data_source_resolver() -> DataSourceResolver:
    """Get the singleton DataSourceResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = DataSourceResolver()
    return _resolver
