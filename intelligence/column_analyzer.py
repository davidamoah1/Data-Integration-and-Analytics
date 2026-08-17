"""Column Semantic Analyzer.

Inspects each column in a DataFrame and classifies it into a semantic
role using multiple signals:
  - column name patterns
  - data type
  - cardinality / uniqueness ratio
  - sample value patterns
  - distribution shape
  - missing value ratio

Roles:
  MEASURE       — numeric metric (revenue, sales, count)
  DIMENSION     — categorical grouping (region, product, department)
  DATE_TIME     — temporal column (date, timestamp)
  IDENTIFIER    — unique ID (customer_id, transaction_id)
  CATEGORY      — low-cardinality categorical (status, gender, type)
  TEXT          — high-cardinality string (description, name)
  GEOGRAPHY     — location (country, city, region, lat/lon)
  BOOLEAN       — true/false column
  CURRENCY      — monetary values
  PERCENTAGE    — 0-100 or 0-1 ratio values
  UNKNOWN       — cannot classify
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class ColumnSemanticRole(str, Enum):
    MEASURE = "measure"
    DIMENSION = "dimension"
    DATE_TIME = "date_time"
    IDENTIFIER = "identifier"
    CATEGORY = "category"
    TEXT = "text"
    GEOGRAPHY = "geography"
    BOOLEAN = "boolean"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    UNKNOWN = "unknown"


# ─── Name-based heuristics ─────────────────────────────────────────────────

ID_PATTERNS = re.compile(
    r"\b(id|uuid|guid|ref|reference|serial|code|number|num|no|hash)\b",
    re.IGNORECASE,
)

MEASURE_PATTERNS = re.compile(
    r"\b(revenue|sales|amount|total|sum|count|quantity|qty|price|cost|profit|"
    r"margin|rate|score|value|income|expense|salary|wage|price|fee|charge|"
    r"balance|volume|weight|height|age|temperature|score|grade|gpa|cgpa)\b",
    re.IGNORECASE,
)

DATE_PATTERNS = re.compile(
    r"\b(date|time|timestamp|day|month|year|week|quarter|created|updated|"
    r"expiry|expires|deadline|dob|born|awarded|issued|graduation|start|end|"
    r"period|fiscal)\b",
    re.IGNORECASE,
)

GEO_PATTERNS = re.compile(
    r"\b(country|region|state|city|province|district|zone|area|location|"
    r"address|postal|zip|latitude|longitude|lat|lon|geo|continent|town|"
    r"village|county|municipality)\b",
    re.IGNORECASE,
)

CATEGORY_PATTERNS = re.compile(
    r"\b(type|category|class|group|segment|status|gender|sex|tier|level|"
    r"grade|rank|phase|stage|mode|channel|source|medium|priority|label|"
    r"department|faculty|programme|program|course|product|brand|"
    r"industry|sector|role|position|title)\b",
    re.IGNORECASE,
)

CURRENCY_PATTERNS = re.compile(
    r"\b(price|cost|revenue|sales|amount|total|sum|balance|fee|charge|"
    r"salary|wage|income|expense|profit|budget|payment|deposit|loan|"
    r"transaction|order_value|unit_price)\b",
    re.IGNORECASE,
)

PERCENTAGE_PATTERNS = re.compile(
    r"\b(percent|percentage|rate|ratio|proportion|share|pct|%\b)",
    re.IGNORECASE,
)

BOOLEAN_PATTERNS = re.compile(
    r"\b(is_|has_|active|enabled|disabled|verified|approved|rejected|"
    r"completed|paid|sent|received|valid|confirmed|flag|boolean)\b",
    re.IGNORECASE,
)

# Known geographic values for value-based detection
GEO_VALUES = {
    # Countries
    "ghana",
    "nigeria",
    "kenya",
    "south africa",
    "egypt",
    "morocco",
    "tunisia",
    "usa",
    "united states",
    "uk",
    "united kingdom",
    "canada",
    "australia",
    "india",
    "china",
    "japan",
    "germany",
    "france",
    "spain",
    "italy",
    "brazil",
    "mexico",
    "argentina",
    "russia",
    "south korea",
    "saudi arabia",
    # Ghana regions
    "greater accra",
    "ashanti",
    "western",
    "eastern",
    "central",
    "volta",
    "northern",
    "upper east",
    "upper west",
    "bono",
    "ahafo",
    "oti",
    # Nigerian states
    "lagos",
    "abuja",
    "kano",
    "rivers",
    "oyo",
    "kaduna",
    # Cities
    "accra",
    "kumasi",
    "takoradi",
    "tamale",
    "cape coast",
    "tema",
    "nairobi",
    "cairo",
}


@dataclass
class ColumnUnderstanding:
    """Semantic understanding of a single column."""

    name: str
    dtype: str
    role: ColumnSemanticRole
    confidence: float  # 0..1
    cardinality: int
    uniqueness_ratio: float  # 0..1
    missing_ratio: float  # 0..1
    sample_values: list
    numeric_stats: dict | None = None
    category_distribution: dict | None = None
    date_range: list | None = None
    detected_format: str | None = None
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "role": self.role.value,
            "confidence": round(self.confidence, 3),
            "cardinality": self.cardinality,
            "uniqueness_ratio": round(self.uniqueness_ratio, 3),
            "missing_ratio": round(self.missing_ratio, 3),
            "sample_values": [str(v) for v in self.sample_values[:10]],
            "numeric_stats": self.numeric_stats,
            "category_distribution": (
                {str(k): v for k, v in list(self.category_distribution.items())[:15]}
                if self.category_distribution
                else None
            ),
            "date_range": [str(d) for d in self.date_range] if self.date_range else None,
            "detected_format": self.detected_format,
            "reasoning": self.reasoning,
        }


@dataclass
class DatasetUnderstanding:
    """Complete semantic understanding of a dataset."""

    row_count: int
    column_count: int
    columns: list[ColumnUnderstanding] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    identifiers: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    geo_columns: list[str] = field(default_factory=list)
    boolean_columns: list[str] = field(default_factory=list)
    text_columns: list[str] = field(default_factory=list)
    quality_score: float = 0.0
    detected_domain: str = "unknown"
    recommended_analyses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [c.to_dict() for c in self.columns],
            "measures": self.measures,
            "dimensions": self.dimensions,
            "date_columns": self.date_columns,
            "identifiers": self.identifiers,
            "categories": self.categories,
            "geo_columns": self.geo_columns,
            "boolean_columns": self.boolean_columns,
            "text_columns": self.text_columns,
            "quality_score": round(self.quality_score, 2),
            "detected_domain": self.detected_domain,
            "recommended_analyses": self.recommended_analyses,
        }


class ColumnAnalyzer:
    """Analyzes DataFrame columns and infers semantic roles."""

    # Cardinality thresholds
    CATEGORY_MAX_CARDINALITY = 30  # above this, categorical → dimension/text
    IDENTIFIER_MIN_UNIQUENESS = 0.95  # 95%+ unique → identifier

    def analyze(self, df: pd.DataFrame) -> DatasetUnderstanding:
        """Analyze all columns in the DataFrame."""
        columns: list[ColumnUnderstanding] = []

        for col_name in df.columns:
            col = self._analyze_column(df, col_name)
            columns.append(col)

        understanding = DatasetUnderstanding(
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
        )

        # Group columns by role
        for c in columns:
            if c.role in (
                ColumnSemanticRole.MEASURE,
                ColumnSemanticRole.CURRENCY,
                ColumnSemanticRole.PERCENTAGE,
            ):
                understanding.measures.append(c.name)
            elif c.role == ColumnSemanticRole.DIMENSION:
                understanding.dimensions.append(c.name)
            elif c.role == ColumnSemanticRole.DATE_TIME:
                understanding.date_columns.append(c.name)
            elif c.role == ColumnSemanticRole.IDENTIFIER:
                understanding.identifiers.append(c.name)
            elif c.role == ColumnSemanticRole.CATEGORY:
                understanding.categories.append(c.name)
            elif c.role == ColumnSemanticRole.GEOGRAPHY:
                understanding.geo_columns.append(c.name)
            elif c.role == ColumnSemanticRole.BOOLEAN:
                understanding.boolean_columns.append(c.name)
            elif c.role == ColumnSemanticRole.TEXT:
                understanding.text_columns.append(c.name)

        # Compute quality score
        understanding.quality_score = self._compute_quality_score(df, columns)

        # Detect domain
        understanding.detected_domain = self._detect_domain(columns)

        # Recommend analyses
        understanding.recommended_analyses = self._recommend_analyses(understanding)

        return understanding

    def _analyze_column(self, df: pd.DataFrame, col_name: str) -> ColumnUnderstanding:
        series = df[col_name]
        dtype = str(series.dtype)
        non_null = series.dropna()
        cardinality = series.nunique()
        uniqueness_ratio = cardinality / len(series) if len(series) > 0 else 0
        missing_ratio = series.isna().sum() / len(series) if len(series) > 0 else 0
        sample_values = non_null.head(10).tolist()

        # Try to detect actual type
        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_datetime = pd.api.types.is_datetime64_any_dtype(series)
        is_bool = pd.api.types.is_bool_dtype(series)
        is_string = pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)

        # Try to parse string dates
        detected_date_format = None
        if is_string and not is_numeric:
            detected_date_format = self._detect_date_format(non_null.head(20))

        # Try to parse numeric strings
        if is_string and not is_numeric and not detected_date_format:
            numeric_parsed = self._try_parse_numeric(non_null.head(20))
            if numeric_parsed is not None:
                is_numeric = True

        # Build numeric stats
        numeric_stats = None
        if is_numeric:
            numeric_stats = {
                "min": float(non_null.min()) if len(non_null) > 0 else None,
                "max": float(non_null.max()) if len(non_null) > 0 else None,
                "mean": float(non_null.mean()) if len(non_null) > 0 else None,
                "median": float(non_null.median()) if len(non_null) > 0 else None,
                "std": float(non_null.std()) if len(non_null) > 0 else None,
            }

        # Build category distribution
        category_distribution = None
        if is_string or is_bool:
            if cardinality <= 50:
                vc = non_null.value_counts().head(15)
                category_distribution = {str(k): int(v) for k, v in vc.items()}

        # Build date range
        date_range = None
        if is_datetime or detected_date_format:
            try:
                if is_datetime:
                    date_range = [non_null.min(), non_null.max()]
                elif detected_date_format:
                    parsed = pd.to_datetime(non_null.head(100), errors="coerce").dropna()
                    if len(parsed) > 0:
                        date_range = [parsed.min(), parsed.max()]
            except Exception:
                pass

        # Determine role
        role, confidence, reasoning = self._classify_role(
            col_name=col_name,
            dtype=dtype,
            is_numeric=is_numeric,
            is_datetime=is_datetime,
            is_bool=is_bool,
            is_string=is_string,
            cardinality=cardinality,
            uniqueness_ratio=uniqueness_ratio,
            missing_ratio=missing_ratio,
            sample_values=sample_values,
            detected_date_format=detected_date_format,
            numeric_stats=numeric_stats,
            category_distribution=category_distribution,
            row_count=len(df),
        )

        return ColumnUnderstanding(
            name=col_name,
            dtype=dtype,
            role=role,
            confidence=confidence,
            cardinality=cardinality,
            uniqueness_ratio=uniqueness_ratio,
            missing_ratio=missing_ratio,
            sample_values=sample_values,
            numeric_stats=numeric_stats,
            category_distribution=category_distribution,
            date_range=[str(d) for d in date_range] if date_range else None,
            detected_format=detected_date_format,
            reasoning=reasoning,
        )

    def _classify_role(
        self,
        col_name: str,
        dtype: str,
        is_numeric: bool,
        is_datetime: bool,
        is_bool: bool,
        is_string: bool,
        cardinality: int,
        uniqueness_ratio: float,
        missing_ratio: float,
        sample_values: list,
        detected_date_format: str | None,
        numeric_stats: dict | None,
        category_distribution: dict | None,
        row_count: int,
    ) -> tuple[ColumnSemanticRole, float, str]:
        """Classify a column into a semantic role. Returns (role, confidence, reasoning)."""

        # 1. Boolean — highest priority, unambiguous
        if is_bool:
            return ColumnSemanticRole.BOOLEAN, 0.98, "Column has boolean dtype"

        # 2. Date/time
        if is_datetime:
            return ColumnSemanticRole.DATE_TIME, 0.95, "Column has datetime dtype"
        if detected_date_format:
            return (
                ColumnSemanticRole.DATE_TIME,
                0.85,
                f"Values match date format: {detected_date_format}",
            )

        # 3. Identifier — very high uniqueness + name matches ID patterns
        if uniqueness_ratio >= self.IDENTIFIER_MIN_UNIQUENESS and row_count > 5:
            if ID_PATTERNS.search(col_name):
                return (
                    ColumnSemanticRole.IDENTIFIER,
                    0.92,
                    f"Column is {uniqueness_ratio:.0%} unique and name matches ID pattern",
                )
            # Very high uniqueness without ID name → could be identifier or text
            if is_string and cardinality == row_count:
                return (
                    ColumnSemanticRole.IDENTIFIER,
                    0.70,
                    "100% unique values — likely an identifier",
                )

        # 4. Geography — name or value matches geo patterns
        if GEO_PATTERNS.search(col_name):
            if is_string and cardinality <= 200:
                return ColumnSemanticRole.GEOGRAPHY, 0.88, "Column name matches geographic pattern"
        if is_string and cardinality <= 100 and category_distribution:
            geo_matches = sum(1 for k in category_distribution if k.lower().strip() in GEO_VALUES)
            if geo_matches >= max(2, len(category_distribution) * 0.5):
                return (
                    ColumnSemanticRole.GEOGRAPHY,
                    0.82,
                    f"{geo_matches}/{len(category_distribution)} values match known geographic names",
                )

        # 5. Currency — numeric + name matches currency patterns
        if is_numeric and CURRENCY_PATTERNS.search(col_name):
            return ColumnSemanticRole.CURRENCY, 0.85, "Numeric column with currency-related name"

        # 6. Percentage — numeric + name matches percentage + values in 0-100 or 0-1
        if is_numeric and PERCENTAGE_PATTERNS.search(col_name):
            if numeric_stats and numeric_stats.get("min") is not None:
                mn, mx = numeric_stats["min"], numeric_stats["max"]
                if mn >= 0 and mx <= 100:
                    return (
                        ColumnSemanticRole.PERCENTAGE,
                        0.85,
                        "Numeric column with percentage name and values in 0-100 range",
                    )
                if mn >= 0 and mx <= 1:
                    return (
                        ColumnSemanticRole.PERCENTAGE,
                        0.80,
                        "Numeric column with percentage name and values in 0-1 range",
                    )

        # 7. Measure — numeric + name matches measure patterns
        if is_numeric and MEASURE_PATTERNS.search(col_name):
            return (
                ColumnSemanticRole.MEASURE,
                0.85,
                "Numeric column with measure/metric-related name",
            )

        # 8. Measure — numeric without ID pattern, not unique
        if is_numeric and uniqueness_ratio < self.IDENTIFIER_MIN_UNIQUENESS:
            if cardinality > 1:
                return (
                    ColumnSemanticRole.MEASURE,
                    0.72,
                    "Numeric column with multiple distinct values",
                )

        # 9. Category — low cardinality string + name matches category patterns
        if is_string and cardinality <= self.CATEGORY_MAX_CARDINALITY:
            if CATEGORY_PATTERNS.search(col_name):
                return (
                    ColumnSemanticRole.CATEGORY,
                    0.85,
                    f"Low-cardinality ({cardinality}) string with category-related name",
                )
            # Low cardinality without name match
            if cardinality <= 10:
                return (
                    ColumnSemanticRole.CATEGORY,
                    0.65,
                    f"Very low cardinality ({cardinality}) string — likely a category",
                )

        # 10. Dimension — medium cardinality string, not unique
        if is_string and cardinality > self.CATEGORY_MAX_CARDINALITY and uniqueness_ratio < 0.5:
            return (
                ColumnSemanticRole.DIMENSION,
                0.65,
                f"Medium-cardinality ({cardinality}) string — likely a dimension",
            )

        # 11. Text — high cardinality string
        if is_string and uniqueness_ratio > 0.5:
            if not ID_PATTERNS.search(col_name):
                return ColumnSemanticRole.TEXT, 0.60, "High-cardinality string — likely free text"

        # 12. Dimension — fallback for categorical strings
        if is_string and cardinality <= self.CATEGORY_MAX_CARDINALITY * 3:
            return (
                ColumnSemanticRole.DIMENSION,
                0.55,
                f"String column with {cardinality} distinct values",
            )

        # 13. Fallback
        if is_numeric:
            return ColumnSemanticRole.MEASURE, 0.50, "Numeric column (fallback)"
        if is_string:
            return ColumnSemanticRole.TEXT, 0.40, "String column (fallback)"

        return ColumnSemanticRole.UNKNOWN, 0.30, "Could not classify column"

    def _detect_date_format(self, samples: pd.Series) -> str | None:
        """Try to detect if string values are dates."""
        if len(samples) == 0:
            return None

        formats_to_try = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ]

        for fmt in formats_to_try:
            matches = 0
            for val in samples:
                try:
                    pd.to_datetime(str(val), format=fmt)
                    matches += 1
                except (ValueError, TypeError):
                    pass
            if matches >= len(samples) * 0.7:
                return fmt

        # Try pandas flexible parsing
        try:
            parsed = pd.to_datetime(samples, errors="coerce")
            if parsed.notna().sum() >= len(samples) * 0.7:
                return "auto-detected"
        except Exception:
            pass

        return None

    def _try_parse_numeric(self, samples: pd.Series) -> pd.Series | None:
        """Try to parse string values as numeric."""
        try:
            parsed = pd.to_numeric(samples, errors="coerce")
            if parsed.notna().sum() >= len(samples) * 0.8:
                return parsed
        except Exception:
            pass
        return None

    def _compute_quality_score(self, df: pd.DataFrame, columns: list[ColumnUnderstanding]) -> float:
        """Compute overall data quality score (0-100)."""
        if len(df) == 0:
            return 0.0

        # Completeness: 1 - average missing ratio
        avg_missing = sum(c.missing_ratio for c in columns) / len(columns) if columns else 1
        completeness = (1 - avg_missing) * 40

        # Uniqueness (low duplicates)
        dup_ratio = df.duplicated().sum() / len(df) if len(df) > 0 else 0
        uniqueness = (1 - dup_ratio) * 20

        # Role confidence
        avg_confidence = sum(c.confidence for c in columns) / len(columns) if columns else 0
        confidence_score = avg_confidence * 20

        # Validity (no negative quality signals)
        validity = 20

        return min(100, completeness + uniqueness + confidence_score + validity)

    def _detect_domain(self, columns: list[ColumnUnderstanding]) -> str:
        """Detect the likely business domain from column names and roles."""
        all_names = " ".join(c.name.lower() for c in columns)

        domain_signals = {
            "retail": ["sale", "product", "customer", "revenue", "order", "store", "inventory"],
            "education": [
                "student",
                "grade",
                "course",
                "school",
                "gpa",
                "score",
                "exam",
                "teacher",
            ],
            "healthcare": [
                "patient",
                "diagnosis",
                "doctor",
                "hospital",
                "medical",
                "clinic",
                "prescription",
            ],
            "finance": [
                "loan",
                "credit",
                "bank",
                "account",
                "transaction",
                "payment",
                "balance",
                "deposit",
            ],
            "manufacturing": [
                "production",
                "factory",
                "machine",
                "output",
                "defect",
                "quality",
                "assembly",
            ],
            "agriculture": ["crop", "farm", "harvest", "livestock", "irrigation", "soil", "yield"],
            "logistics": [
                "shipment",
                "delivery",
                "route",
                "vehicle",
                "freight",
                "warehouse",
                "transport",
            ],
            "government": [
                "citizen",
                "census",
                "district",
                "public",
                "office",
                "department",
                "ministry",
            ],
            "hr": [
                "employee",
                "salary",
                "department",
                "attendance",
                "leave",
                "performance",
                "hire",
            ],
        }

        best_domain = "unknown"
        best_score = 0

        for domain, keywords in domain_signals.items():
            score = sum(1 for kw in keywords if kw in all_names)
            if score > best_score:
                best_score = score
                best_domain = domain

        return best_domain if best_score >= 2 else "unknown"

    def _recommend_analyses(self, understanding: DatasetUnderstanding) -> list[str]:
        """Recommend statistical analyses based on data structure."""
        recommendations: list[str] = []

        if understanding.date_columns and understanding.measures:
            recommendations.append("time_series_trend")
            recommendations.append("time_series_decomposition")

        if len(understanding.measures) >= 2:
            recommendations.append("correlation_analysis")
            recommendations.append("correlation_heatmap")

        if understanding.dimensions and understanding.measures:
            recommendations.append("group_comparison")
            recommendations.append("anova" if len(understanding.categories) >= 3 else "t_test")

        if understanding.measures:
            recommendations.append("distribution_analysis")
            recommendations.append("outlier_detection")

        if understanding.date_columns and len(understanding.measures) >= 1:
            recommendations.append("forecasting")

        if understanding.geo_columns and understanding.measures:
            recommendations.append("geographic_analysis")

        return recommendations
