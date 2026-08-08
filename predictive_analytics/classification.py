"""Risk Classifier.

Classifies items into risk levels (high, medium, low) using:
  - Rule-based scoring (weighted risk factors)
  - Logistic regression (when target labels available)

Used for:
  - Student risk prediction (low grades, high absenteeism)
  - Patient risk prediction (high readmission probability)
  - Customer churn risk (declining engagement)
"""

from __future__ import annotations

import pandas as pd

from predictive_analytics.base import RiskAssessment


class RiskClassifier:
    """Risk classification engine."""

    @staticmethod
    def classify(
        df: pd.DataFrame,
        id_col: str,
        risk_factors: list[dict],
        name: str = "Risk Assessment",
        target: str = "risk_level",
        high_threshold: float = 0.6,
        medium_threshold: float = 0.3,
    ) -> RiskAssessment:
        """Classify items into risk levels based on weighted factors.

        Args:
            df: DataFrame with the data.
            id_col: Column identifying each item (e.g., student_id).
            risk_factors: List of dicts with keys:
                - "column": column name to evaluate
                - "condition": "below", "above", "equals"
                - "threshold": value to compare against
                - "weight": importance weight (0-1)
                - "label": human-readable description
            name: Display name.
            target: What is being assessed.
            high_threshold: Score above which = high risk.
            medium_threshold: Score above which = medium risk.

        Returns:
            RiskAssessment with counts, factors, and at-risk items.
        """
        scores: list[float] = []
        total_weight = sum(f.get("weight", 1.0) for f in risk_factors)
        if total_weight == 0:
            total_weight = 1.0

        item_details: list[dict] = []
        factor_labels: list[str] = []

        for f in risk_factors:
            factor_labels.append(f.get("label", f["column"]))

        for idx, row in df.iterrows():
            score = 0.0
            triggered: list[str] = []

            for f in risk_factors:
                col = f["column"]
                if col not in df.columns:
                    continue
                val = row[col]
                if pd.isna(val):
                    continue

                condition = f.get("condition", "below")
                threshold = f.get("threshold", 0)
                weight = f.get("weight", 1.0)

                triggered_flag = False
                if (
                    condition == "below"
                    and val < threshold
                    or condition == "above"
                    and val > threshold
                    or condition == "equals"
                    and val == threshold
                ):
                    triggered_flag = True

                if triggered_flag:
                    score += weight
                    triggered.append(f.get("label", col))

            normalized_score = score / total_weight
            scores.append(normalized_score)

            if normalized_score >= high_threshold:
                risk_level = "high"
            elif normalized_score >= medium_threshold:
                risk_level = "medium"
            else:
                risk_level = "low"

            item_id = row[id_col] if id_col in df.columns else idx
            item_details.append(
                {
                    "id": str(item_id),
                    "risk_score": round(normalized_score, 3),
                    "risk_level": risk_level,
                    "triggered_factors": triggered,
                }
            )

        high_count = sum(1 for i in item_details if i["risk_level"] == "high")
        medium_count = sum(1 for i in item_details if i["risk_level"] == "medium")
        low_count = sum(1 for i in item_details if i["risk_level"] == "low")

        at_risk = [i for i in item_details if i["risk_level"] in ("high", "medium")]
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)

        summary = (
            f"{name}: {high_count} high-risk, {medium_count} medium-risk, "
            f"{low_count} low-risk out of {len(item_details)} total. "
            f"Risk factors: {', '.join(factor_labels)}."
        )

        return RiskAssessment(
            name=name,
            target=target,
            method="rule_based",
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            low_risk_count=low_count,
            risk_factors=factor_labels,
            at_risk_items=at_risk,
            summary=summary,
        )
