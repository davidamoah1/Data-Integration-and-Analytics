"""Automatic Analysis Engine â€” column semantic role detection.

After a dataset is uploaded, this engine inspects every column using:
  - column name
  - data type
  - value patterns
  - cardinality
  - sample values
  - distribution
  - relationships

Columns are classified into semantic roles:
  DIMENSION, MEASURE, DATE_TIME, IDENTIFIER, CATEGORY, TEXT,
  GEOGRAPHY, BOOLEAN, CURRENCY, PERCENTAGE, UNKNOWN

The output is a machine-readable DatasetUnderstanding object that
downstream engines (chart selection, KPI, insights) consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# â”€â”€ Semantic roles â”€â”€


class SemanticRole:
    DIMENSION = "dimension"
    MEASURE = "measure"
    DATE_TIME = "date_time"
    IDENTIFIER = "identifier"
    CATEGORY = "category"
    TEXT = "text"
    GEOGRAPHY = "geography"
    BOOLEAN = "boolean"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    UNKNOWN = "unknown"


# â”€â”€ Name-based hints â”€â”€

_ID_KEYWORDS = {"id", "_id", "uuid", "guid", "ref", "code", "number", "no", "num", "seq"}
_DATE_KEYWORDS = {
    "date",
    "time",
    "timestamp",
    "datetime",
    "created",
    "updated",
    "modified",
    "period",
}
_GEO_KEYWORDS = {
    "country",
    "region",
    "city",
    "state",
    "district",
    "location",
    "address",
    "branch",
    "zone",
    "area",
    "lat",
    "lon",
    "latitude",
    "longitude",
}
_MEASURE_KEYWORDS = {
    "revenue",
    "sales",
    "amount",
    "total",
    "sum",
    "cost",
    "price",
    "value",
    "count",
    "quantity",
    "qty",
    "volume",
    "income",
    "expense",
    "profit",
    "loss",
    "billing",
    "payment",
    "balance",
    "score",
    "rate",
    "fee",
    "charge",
    "budget",
    "salary",
    "wage",
}
_CURRENCY_KEYWORDS = {
    "revenue",
    "sales",
    "amount",
    "cost",
    "price",
    "value",
    "income",
    "expense",
    "profit",
    "billing",
    "payment",
    "balance",
    "fee",
    "charge",
    "budget",
    "salary",
    "wage",
    "donation",
    "offering",
    "tithe",
    "fund",
}
_PERCENTAGE_KEYWORDS = {
    "rate",
    "pct",
    "percent",
    "percentage",
    "ratio",
    "share",
    "growth",
    "margin",
    "completion",
    "attendance",
}
_BOOLEAN_KEYWORDS = {
    "is_",
    "has_",
    "active",
    "enabled",
    "approved",
    "verified",
    "confirmed",
    "completed",
    "paid",
    "valid",
    "flag",
    "status",
}
_CATEGORY_KEYWORDS = {
    "category",
    "type",
    "class",
    "group",
    "tier",
    "level",
    "grade",
    "rank",
    "stage",
    "phase",
    "mode",
    "channel",
    "method",
    "status",
    "label",
    "tag",
    "segment",
    "department",
    "product",
    "service",
    "program",
    "course",
    "diagnosis",
    "plan",
    "ministry",
    "project",
    "event",
    "gender",
    "branch",
}


@dataclass
class ColumnUnderstanding:
    """Semantic understanding of a single column."""

    name: str
    dtype: str
    semantic_role: str = SemanticRole.UNKNOWN
    cardinality: int = 0
    unique_percentage: float = 0.0
    missing_percentage: float = 0.0
    is_numeric: bool = False
    is_datetime: bool = False
    is_categorical: bool = False
    sample_values: list[Any] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    detected_patterns: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "semantic_role": self.semantic_role,
            "cardinality": self.cardinality,
            "unique_percentage": round(self.unique_percentage, 2),
            "missing_percentage": round(self.missing_percentage, 2),
            "is_numeric": self.is_numeric,
            "is_datetime": self.is_datetime,
            "is_categorical": self.is_categorical,
            "sample_values": [str(v) for v in self.sample_values[:5]],
            "stats": self.stats,
            "detected_patterns": self.detected_patterns,
            "confidence": round(self.confidence, 2),
            "notes": self.notes,
        }


@dataclass
class DatasetUnderstanding:
    """Machine-readable dataset understanding object.

    This is the central metadata object that downstream engines consume
    to make intelligent decisions about charts, KPIs, insights, etc.
    """

    dataset_name: str = ""
    dataset_type: str = ""
    domain: str = ""
    industry: str = "unknown"
    row_count: int = 0
    column_count: int = 0
    quality_score: float = 0.0

    columns: list[ColumnUnderstanding] = field(default_factory=list)

    # Grouped by semantic role
    measures: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    time_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    identifier_columns: list[str] = field(default_factory=list)
    geographic_columns: list[str] = field(default_factory=list)
    boolean_columns: list[str] = field(default_factory=list)
    currency_columns: list[str] = field(default_factory=list)
    percentage_columns: list[str] = field(default_factory=list)
    text_columns: list[str] = field(default_factory=list)

    # Relationships
    correlations: list[dict[str, Any]] = field(default_factory=list)
    possible_dependent: list[str] = field(default_factory=list)
    possible_independent: list[str] = field(default_factory=list)

    # Recommended analyses
    recommended_analyses: list[str] = field(default_factory=list)

    # Data quality warnings
    quality_warnings: list[str] = field(default_factory=list)

    # Dataset hash for versioning
    dataset_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "dataset_type": self.dataset_type,
            "domain": self.domain,
            "industry": self.industry,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "quality_score": round(self.quality_score, 1),
            "columns": [c.to_dict() for c in self.columns],
            "measures": self.measures,
            "dimensions": self.dimensions,
            "time_columns": self.time_columns,
            "categorical_columns": self.categorical_columns,
            "identifier_columns": self.identifier_columns,
            "geographic_columns": self.geographic_columns,
            "boolean_columns": self.boolean_columns,
            "currency_columns": self.currency_columns,
            "percentage_columns": self.percentage_columns,
            "text_columns": self.text_columns,
            "correlations": self.correlations,
            "possible_dependent": self.possible_dependent,
            "possible_independent": self.possible_independent,
            "recommended_analyses": self.recommended_analyses,
            "quality_warnings": self.quality_warnings,
            "dataset_hash": self.dataset_hash,
        }


class AutomaticAnalysisEngine:
    """Analyzes a dataset and produces a DatasetUnderstanding object.

    Uses multiple signals (name, dtype, values, cardinality, distribution)
    to infer semantic meaning.  Does NOT rely solely on column names.
    """

    @classmethod
    def analyze(
        cls,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        industry: str = "unknown",
        quality_score: float = 0.0,
        dataset_hash: str = "",
    ) -> DatasetUnderstanding:
        """Analyze a DataFrame and return a DatasetUnderstanding.

        Args:
            df: The dataset DataFrame.
            dataset_name: Name of the dataset.
            industry: Detected industry (if known from prior semantic analysis).
            quality_score: Data quality score (0-100).
            dataset_hash: Hash of dataset content for versioning.

        Returns:
            DatasetUnderstanding object.
        """
        understanding = DatasetUnderstanding(
            dataset_name=dataset_name,
            industry=industry,
            row_count=len(df),
            column_count=len(df.columns),
            quality_score=quality_score,
            dataset_hash=dataset_hash,
        )

        # Analyze each column
        for col_name in df.columns:
            col_understanding = cls._analyze_column(df, col_name)
            understanding.columns.append(col_understanding)

            # Group by semantic role
            role = col_understanding.semantic_role
            if role == SemanticRole.MEASURE or role == SemanticRole.CURRENCY:
                understanding.measures.append(col_name)
            elif role == SemanticRole.DIMENSION or role == SemanticRole.CATEGORY:
                understanding.dimensions.append(col_name)
            elif role == SemanticRole.DATE_TIME:
                understanding.time_columns.append(col_name)
            elif role == SemanticRole.IDENTIFIER:
                understanding.identifier_columns.append(col_name)
            elif role == SemanticRole.GEOGRAPHY:
                understanding.geographic_columns.append(col_name)
                understanding.dimensions.append(col_name)
            elif role == SemanticRole.BOOLEAN:
                understanding.boolean_columns.append(col_name)
                understanding.dimensions.append(col_name)
            elif role == SemanticRole.PERCENTAGE:
                understanding.percentage_columns.append(col_name)
                understanding.measures.append(col_name)
            elif role == SemanticRole.TEXT:
                understanding.text_columns.append(col_name)

            # Track categorical columns
            if col_understanding.is_categorical:
                understanding.categorical_columns.append(col_name)

        # Detect correlations between numeric columns
        understanding.correlations = cls._detect_correlations(df, understanding.measures)

        # Infer possible dependent/independent variables
        understanding.possible_dependent, understanding.possible_independent = (
            cls._infer_variable_roles(df, understanding)
        )

        # Recommend analyses
        understanding.recommended_analyses = cls._recommend_analyses(understanding)

        # Detect quality warnings
        understanding.quality_warnings = cls._detect_quality_warnings(df, understanding)

        # Infer dataset type and domain
        understanding.dataset_type = cls._infer_dataset_type(understanding)
        understanding.domain = industry if industry != "unknown" else understanding.dataset_type

        return understanding

    # â”€â”€ Column analysis â”€â”€

    @classmethod
    def _analyze_column(cls, df: pd.DataFrame, col_name: str) -> ColumnUnderstanding:
        """Analyze a single column and determine its semantic role."""
        series = df[col_name]
        non_null = series.dropna()
        n = len(series)
        n_non_null = len(non_null)

        col = ColumnUnderstanding(
            name=col_name,
            dtype=str(series.dtype),
            cardinality=int(series.nunique()),
            unique_percentage=float(series.nunique() / max(n, 1) * 100),
            missing_percentage=float(series.isna().sum() / max(n, 1) * 100),
            is_numeric=pd.api.types.is_numeric_dtype(series),
            is_datetime=pd.api.types.is_datetime64_any_dtype(series),
            is_categorical=series.dtype == "object" or series.dtype.name == "category",
            sample_values=non_null.head(5).tolist(),
        )

        if n_non_null == 0:
            col.semantic_role = SemanticRole.UNKNOWN
            col.notes = "Column is entirely empty"
            col.confidence = 1.0
            return col

        # â”€â”€ Step 1: Check data type â”€â”€
        if col.is_datetime:
            col.semantic_role = SemanticRole.DATE_TIME
            col.confidence = 0.95
            col.stats = cls._datetime_stats(non_null)
            col.detected_patterns.append("datetime_dtype")
            return col

        # â”€â”€ Step 2: Check for boolean (before numeric, since bool is numeric dtype) â”€â”€
        if n_non_null > 0:
            unique_vals = set(non_null.dropna().unique())
            bool_vals = {
                True,
                False,
                "true",
                "false",
                "True",
                "False",
                "yes",
                "no",
                "Yes",
                "No",
                "Y",
                "N",
                "0",
                "1",
            }
            if unique_vals.issubset(bool_vals) and len(unique_vals) <= 3 and len(unique_vals) >= 2:
                col.semantic_role = SemanticRole.BOOLEAN
                col.confidence = 0.9
                col.detected_patterns.append("boolean_values")
                col.stats = cls._categorical_stats(non_null)
                return col

        # â”€â”€ Step 3: Check for date-like strings â”€â”€
        if col.is_categorical:
            date_parsed = cls._try_parse_dates(non_null.head(20))
            if date_parsed is not None:
                col.semantic_role = SemanticRole.DATE_TIME
                col.confidence = 0.85
                col.detected_patterns.append("date_string")
                col.stats = {
                    "min_date": str(date_parsed.min()),
                    "max_date": str(date_parsed.max()),
                    "span_days": (date_parsed.max() - date_parsed.min()).days,
                }
                return col

        # â”€â”€ Step 4: Numeric columns â”€â”€
        if col.is_numeric:
            col.stats = cls._numeric_stats(non_null)

            # Check for identifier (sequential integers, high uniqueness)
            if col.unique_percentage > 90:
                diffs = non_null.sort_values().diff().dropna()
                if len(diffs) > 0 and (diffs == 1).mean() > 0.8:
                    col.semantic_role = SemanticRole.IDENTIFIER
                    col.confidence = 0.85
                    col.detected_patterns.append("sequential_integer")
                    return col

            # Check for percentage (0-100 or 0-1 range)
            mn, mx = col.stats.get("min", 0), col.stats.get("max", 0)
            if mn is not None and mx is not None:
                if mn >= 0 and mx <= 1.0 and col.stats.get("mean", 0) < 1:
                    col_name_lower = col_name.lower()
                    if any(kw in col_name_lower for kw in _PERCENTAGE_KEYWORDS):
                        col.semantic_role = SemanticRole.PERCENTAGE
                        col.confidence = 0.8
                        col.detected_patterns.append("range_0_1")
                        return col
                if mn >= 0 and mx <= 100 and col.stats.get("mean", 0) < 100:
                    col_name_lower = col_name.lower()
                    if any(kw in col_name_lower for kw in _PERCENTAGE_KEYWORDS):
                        col.semantic_role = SemanticRole.PERCENTAGE
                        col.confidence = 0.75
                        col.detected_patterns.append("range_0_100")
                        return col

            # Check for currency (positive, decimals, reasonable range, name hint)
            col_name_lower = col_name.lower()
            if any(kw in col_name_lower for kw in _CURRENCY_KEYWORDS):
                if mn is not None and mx is not None and mn >= 0 and mx > 100:
                    col.semantic_role = SemanticRole.CURRENCY
                    col.confidence = 0.8
                    col.detected_patterns.append("currency_name_hint")
                    return col

            # Default numeric â†’ measure
            col.semantic_role = SemanticRole.MEASURE
            col.confidence = 0.7
            col.detected_patterns.append("numeric_measure")
            return col

        # â”€â”€ Step 5: Categorical / text columns â”€â”€
        if col.is_categorical:
            col_name_lower = col_name.lower()

            # Check for geography
            if any(kw in col_name_lower for kw in _GEO_KEYWORDS):
                col.semantic_role = SemanticRole.GEOGRAPHY
                col.confidence = 0.8
                col.detected_patterns.append("geo_name_hint")
                col.stats = cls._categorical_stats(non_null)
                return col

            # Check for identifier (high cardinality, unique-like)
            if col.unique_percentage > 90:
                col.semantic_role = SemanticRole.IDENTIFIER
                col.confidence = 0.75
                col.detected_patterns.append("high_cardinality_id")
                col.stats = cls._categorical_stats(non_null)
                return col

            # Check for ID by name
            if any(kw in col_name_lower for kw in _ID_KEYWORDS):
                col.semantic_role = SemanticRole.IDENTIFIER
                col.confidence = 0.7
                col.detected_patterns.append("id_name_hint")
                col.stats = cls._categorical_stats(non_null)
                return col

            # Low cardinality â†’ category/dimension
            if col.unique_percentage < 50 or col.cardinality <= 30:
                col.semantic_role = SemanticRole.CATEGORY
                col.confidence = 0.75
                col.detected_patterns.append("low_cardinality_category")
                col.stats = cls._categorical_stats(non_null)
                return col

            # High cardinality text â†’ text
            col.semantic_role = SemanticRole.TEXT
            col.confidence = 0.6
            col.detected_patterns.append("high_cardinality_text")
            col.stats = cls._categorical_stats(non_null)
            return col

        # Fallback
        col.semantic_role = SemanticRole.UNKNOWN
        col.confidence = 0.3
        return col

    # â”€â”€ Helpers â”€â”€

    @staticmethod
    def _datetime_stats(series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a datetime series."""
        vals = series.dropna()
        if len(vals) == 0:
            return {}
        mn = vals.min()
        mx = vals.max()
        return {
            "min_date": str(mn),
            "max_date": str(mx),
            "span_days": (mx - mn).days if hasattr(mx, "days") else (mx - mn).days,
            "unique_count": int(vals.nunique()),
        }

    @staticmethod
    def _numeric_stats(series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a numeric series."""
        vals = series.dropna()
        if len(vals) == 0:
            return {}
        # Convert to float to handle bool, int, and other numeric dtypes
        try:
            vals = vals.astype(float)
        except (TypeError, ValueError):
            return {"min": str(vals.min()), "max": str(vals.max())}
        result: dict[str, Any] = {
            "min": float(vals.min()),
            "max": float(vals.max()),
            "mean": float(vals.mean()),
            "median": float(vals.median()),
            "std": float(vals.std()) if len(vals) > 1 else 0.0,
            "q1": float(vals.quantile(0.25)),
            "q3": float(vals.quantile(0.75)),
        }
        result["iqr"] = result["q3"] - result["q1"]
        result["outlier_count"] = int(
            (
                (vals < result["q1"] - 1.5 * result["iqr"])
                | (vals > result["q3"] + 1.5 * result["iqr"])
            ).sum()
        )
        return result

    @staticmethod
    def _categorical_stats(series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a categorical series."""
        vals = series.dropna()
        if len(vals) == 0:
            return {}
        vc = vals.value_counts().head(10)
        return {
            "unique_count": int(vals.nunique()),
            "top_values": {str(k): int(v) for k, v in vc.items()},
            "top_value": str(vc.index[0]) if len(vc) > 0 else "",
            "top_value_count": int(vc.iloc[0]) if len(vc) > 0 else 0,
            "top_value_pct": round(float(vc.iloc[0] / len(vals) * 100), 1) if len(vals) > 0 else 0,
        }

    @staticmethod
    def _try_parse_dates(series: pd.Series) -> pd.Series | None:
        """Try to parse a series as dates. Return parsed series or None."""
        try:
            parsed = pd.to_datetime(series, errors="coerce")
            if parsed.notna().mean() > 0.8:
                return parsed.dropna()
        except Exception:
            pass
        return None

    @staticmethod
    def _detect_correlations(df: pd.DataFrame, measures: list[str]) -> list[dict[str, Any]]:
        """Detect correlations between numeric measure columns."""
        if len(measures) < 2:
            return []

        correlations = []
        numeric_measures = [m for m in measures if pd.api.types.is_numeric_dtype(df[m])]
        if len(numeric_measures) < 2:
            return []

        corr_matrix = df[numeric_measures].corr(method="pearson")

        for i, col1 in enumerate(numeric_measures):
            for j, col2 in enumerate(numeric_measures):
                if i >= j:
                    continue
                val = corr_matrix.loc[col1, col2]
                if pd.isna(val):
                    continue
                abs_val = abs(val)
                strength = "weak" if abs_val < 0.3 else "moderate" if abs_val < 0.7 else "strong"
                direction = "positive" if val > 0 else "negative"
                correlations.append(
                    {
                        "column_1": col1,
                        "column_2": col2,
                        "correlation": round(float(val), 3),
                        "strength": strength,
                        "direction": direction,
                    }
                )

        correlations.sort(key=lambda c: abs(c["correlation"]), reverse=True)
        return correlations[:15]

    @staticmethod
    def _infer_variable_roles(
        df: pd.DataFrame, understanding: DatasetUnderstanding
    ) -> tuple[list[str], list[str]]:
        """Infer possible dependent and independent variables."""
        dependent = []
        independent = []

        # Measures with "revenue", "sales", "amount" in name â†’ likely dependent
        for m in understanding.measures:
            m_lower = m.lower()
            if any(
                kw in m_lower
                for kw in (
                    "revenue",
                    "sales",
                    "amount",
                    "total",
                    "income",
                    "profit",
                    "billing",
                    "payment",
                )
            ):
                dependent.append(m)

        # If no obvious dependent, use the first measure
        if not dependent and understanding.measures:
            dependent = [understanding.measures[0]]

        # Dimensions, time columns â†’ independent
        independent = understanding.dimensions + understanding.time_columns
        # Also measures that aren't dependent are independent
        for m in understanding.measures:
            if m not in dependent:
                independent.append(m)

        return dependent, list(dict.fromkeys(independent))  # dedupe preserving order

    @staticmethod
    def _recommend_analyses(understanding: DatasetUnderstanding) -> list[str]:
        """Recommend statistical analyses based on data structure."""
        recommendations = []

        # Time series â†’ trend analysis
        if understanding.time_columns and understanding.measures:
            recommendations.append("trend_analysis")
            recommendations.append("time_series_decomposition")

        # Two numeric variables â†’ correlation
        if len(understanding.measures) >= 2:
            recommendations.append("correlation_analysis")

        # Multiple numeric variables â†’ correlation matrix
        if len(understanding.measures) >= 3:
            recommendations.append("correlation_matrix")
            recommendations.append("regression_analysis")

        # Categorical + numeric â†’ group comparison
        if understanding.dimensions and understanding.measures:
            recommendations.append("group_comparison")
            # t-test if 2 groups, ANOVA if more
            for dim in understanding.dimensions[:3]:
                if dim in understanding.categorical_columns:
                    n_unique = 0
                    for c in understanding.columns:
                        if c.name == dim:
                            n_unique = c.cardinality
                            break
                    if n_unique == 2:
                        recommendations.append("t_test")
                    elif n_unique > 2:
                        recommendations.append("anova")

        # Distribution analysis
        if understanding.measures:
            recommendations.append("distribution_analysis")
            recommendations.append("outlier_detection")

        # Geographic analysis
        if understanding.geographic_columns and understanding.measures:
            recommendations.append("geographic_analysis")

        # Dedupe
        return list(dict.fromkeys(recommendations))

    @staticmethod
    def _detect_quality_warnings(
        df: pd.DataFrame, understanding: DatasetUnderstanding
    ) -> list[str]:
        """Detect data quality warnings that affect chart selection."""
        warnings = []

        for col in understanding.columns:
            if col.missing_percentage > 80:
                warnings.append(
                    f"Column '{col.name}' has {col.missing_percentage:.0f}% missing values â€” excluded from automatic charts"
                )
            elif col.missing_percentage > 50:
                warnings.append(
                    f"Column '{col.name}' has {col.missing_percentage:.0f}% missing values â€” use with caution"
                )

            if col.is_numeric and col.stats.get("outlier_count", 0) > 0:
                outlier_pct = col.stats["outlier_count"] / max(understanding.row_count, 1) * 100
                if outlier_pct > 10:
                    warnings.append(
                        f"Column '{col.name}' has {outlier_pct:.0f}% outliers â€” may affect visualizations"
                    )

        # Check for duplicate rows
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            dup_pct = dup_count / max(len(df), 1) * 100
            if dup_pct > 10:
                warnings.append(
                    f"Dataset has {dup_count} duplicate rows ({dup_pct:.0f}%) â€” consider deduplication"
                )

        return warnings

    @staticmethod
    def _infer_dataset_type(understanding: DatasetUnderstanding) -> str:
        """Infer the dataset type from column roles."""
        has_time = bool(understanding.time_columns)
        has_geo = bool(understanding.geographic_columns)
        has_measures = bool(understanding.measures)
        has_categories = bool(understanding.dimensions)

        if has_time and has_measures and has_categories:
            return "time_series_categorical"
        elif has_time and has_measures:
            return "time_series"
        elif has_geo and has_measures:
            return "geographic"
        elif has_measures and has_categories:
            return "cross_sectional"
        elif has_measures and len(understanding.measures) >= 2:
            return "multivariate"
        elif has_categories and not has_measures:
            return "categorical"
        else:
            return "generic"
