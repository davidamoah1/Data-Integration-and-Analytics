"""Data classification levels and dataset lifecycle states.

These enums are used by the governance engine to classify datasets and control
transitions between lifecycle stages.
"""

from __future__ import annotations

from enum import Enum


class DataClassification(str, Enum):
    """Sensitivity classification for datasets, columns, and reports."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SENSITIVE = "sensitive"


class DatasetLifecycle(str, Enum):
    """Lifecycle stages for a governed dataset."""

    UPLOADED = "uploaded"
    VALIDATED = "validated"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Order matters for allowed transitions.
_LIFECYCLE_TRANSITIONS: dict[DatasetLifecycle, set[DatasetLifecycle]] = {
    DatasetLifecycle.UPLOADED: {
        DatasetLifecycle.VALIDATED,
        DatasetLifecycle.ARCHIVED,
    },
    DatasetLifecycle.VALIDATED: {
        DatasetLifecycle.APPROVED,
        DatasetLifecycle.ARCHIVED,
    },
    DatasetLifecycle.APPROVED: {
        DatasetLifecycle.PUBLISHED,
        DatasetLifecycle.ARCHIVED,
    },
    DatasetLifecycle.PUBLISHED: {
        DatasetLifecycle.APPROVED,
        DatasetLifecycle.ARCHIVED,
    },
    DatasetLifecycle.ARCHIVED: {
        DatasetLifecycle.UPLOADED,
    },
}


def can_transition(from_stage: DatasetLifecycle, to_stage: DatasetLifecycle) -> bool:
    """Return True if `to_stage` is a valid transition from `from_stage`."""
    return to_stage in _LIFECYCLE_TRANSITIONS.get(from_stage, set())


def required_classification_role(classification: DataClassification) -> str:
    """Return the minimum platform role typically required to view the data."""
    return {
        DataClassification.PUBLIC: "viewer",
        DataClassification.INTERNAL: "viewer",
        DataClassification.CONFIDENTIAL: "analyst",
        DataClassification.SENSITIVE: "organization_admin",
    }.get(classification, "viewer")


def max_classification_for_columns(
    columns: list[DataClassification],
) -> DataClassification:
    """Return the most restrictive classification in a list."""
    order = [
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
        DataClassification.CONFIDENTIAL,
        DataClassification.SENSITIVE,
    ]
    if not columns:
        return DataClassification.INTERNAL
    max_index = max(order.index(c) for c in columns)
    return order[max_index]
