"""Data governance engine.

Combines privacy detection, classification, lifecycle management, and ownership
to provide a single interface for governing datasets before they are published
to dashboards or shared with other users.
"""

from __future__ import annotations

from typing import Any

from governance.classification import (
    DataClassification,
    DatasetLifecycle,
    can_transition,
    max_classification_for_columns,
)
from governance.privacy import SensitivityCategory, detect_sensitive_columns


class GovernanceResult:
    """Outcome of a governance review on a dataset."""

    def __init__(
        self,
        classification: DataClassification,
        lifecycle: DatasetLifecycle,
        sensitive_columns: dict[str, list[str]],
        warnings: list[str],
        blocked_actions: list[str],
    ):
        self.classification = classification
        self.lifecycle = lifecycle
        self.sensitive_columns = sensitive_columns
        self.warnings = warnings
        self.blocked_actions = blocked_actions

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "lifecycle": self.lifecycle.value,
            "sensitive_columns": self.sensitive_columns,
            "warnings": self.warnings,
            "blocked_actions": self.blocked_actions,
        }


def classify_dataset(
    df: Any,
    lifecycle: DatasetLifecycle = DatasetLifecycle.UPLOADED,
) -> GovernanceResult:
    """Run a governance review on a DataFrame.

    Returns the recommended classification, sensitive-column findings, and any
    warnings that should be shown before publishing or exporting the dataset.
    """
    flagged = detect_sensitive_columns(df)

    warnings: list[str] = []
    blocked: list[str] = []

    if flagged:
        warnings.append(
            f"Detected potentially sensitive data in {len(flagged)} column(s): "
            f"{', '.join(flagged.keys())}."
        )

    # Determine overall classification from the most sensitive flagged category.
    column_classifications: list[DataClassification] = []
    for column, categories in flagged.items():
        category_set = {SensitivityCategory(c) for c in categories}
        if category_set & {
            SensitivityCategory.GOVERNMENT_ID,
            SensitivityCategory.FINANCIAL,
            SensitivityCategory.HEALTH,
        }:
            column_classifications.append(DataClassification.SENSITIVE)
        elif category_set & {
            SensitivityCategory.NAME,
            SensitivityCategory.EMAIL,
            SensitivityCategory.PHONE,
            SensitivityCategory.ADDRESS,
            SensitivityCategory.LOCATION,
        }:
            column_classifications.append(DataClassification.CONFIDENTIAL)
        else:
            column_classifications.append(DataClassification.INTERNAL)

    classification = max_classification_for_columns(column_classifications)

    if classification in (DataClassification.CONFIDENTIAL, DataClassification.SENSITIVE):
        warnings.append(
            f"Dataset classified as '{classification.value}'. Review before publishing or exporting."
        )

    if classification == DataClassification.SENSITIVE and lifecycle == DatasetLifecycle.PUBLISHED:
        blocked.append("publishing")
        warnings.append(
            "Sensitive datasets cannot be published without explicit organization-admin approval."
        )

    return GovernanceResult(
        classification=classification,
        lifecycle=lifecycle,
        sensitive_columns={k: [c.value for c in v] for k, v in flagged.items()},
        warnings=warnings,
        blocked_actions=blocked,
    )


__all__ = [
    "GovernanceResult",
    "classify_dataset",
    "can_transition",
    "DataClassification",
    "DatasetLifecycle",
    "SensitivityCategory",
    "detect_sensitive_columns",
    "max_classification_for_columns",
]
