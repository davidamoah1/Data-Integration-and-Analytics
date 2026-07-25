"""Natural Language Query Engine.

Parses user questions into structured analytical queries. Understands
intent types like:
  - why_change: "Why did sales drop?", "Why did revenue increase?"
  - top_n: "Top 5 products by sales", "Best performing regions"
  - summary: "Give me a summary", "Overview of the data"
  - trend: "What's the trend in billing?", "Sales over time"
  - comparison: "Compare regions", "Compare departments"
  - breakdown: "Break down sales by category"
  - anomaly: "Any anomalies?", "What's unusual?"
  - correlation: "Correlation between sales and profit"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class QueryIntent(Enum):
    WHY_CHANGE = "why_change"
    TOP_N = "top_n"
    SUMMARY = "summary"
    TREND = "trend"
    COMPARISON = "comparison"
    BREAKDOWN = "breakdown"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    DESCRIBE = "describe"
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    """A parsed natural language query."""

    intent: QueryIntent
    raw_text: str
    metric: str | None = None
    dimension: str | None = None
    direction: str | None = None  # "increase", "decrease", "change"
    top_n: int = 5
    filters: dict[str, str] = field(default_factory=dict)
    entities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "raw_text": self.raw_text,
            "metric": self.metric,
            "dimension": self.dimension,
            "direction": self.direction,
            "top_n": self.top_n,
            "filters": self.filters,
            "entities": self.entities,
        }


class QueryEngine:
    """Parses natural language questions into structured queries."""

    # Metric synonyms — maps natural language to entity keys
    METRIC_SYNONYMS: dict[str, list[str]] = {
        "revenue": ["sales", "revenue", "income", "turnover", "billing", "amount", "earnings"],
        "profit": ["profit", "margin", "earnings", "net"],
        "cost": ["cost", "expense", "spending", "expenditure"],
        "quantity": ["quantity", "volume", "count", "units", "orders"],
        "patients": ["patients", "admissions", "visits", "cases"],
        "students": ["students", "enrollment", "enrollees"],
        "donations": ["donations", "funding", "contributions", "giving"],
        "production": ["production", "output", "throughput", "yield"],
        "transactions": ["transactions", "transfers", "payments"],
    }

    # Dimension synonyms
    DIMENSION_SYNONYMS: dict[str, list[str]] = {
        "product": ["product", "item", "sku"],
        "category": ["category", "type", "class", "segment"],
        "region": ["region", "area", "zone", "location", "geography"],
        "department": ["department", "dept", "ward", "unit", "division"],
        "customer": ["customer", "client", "patient", "student", "donor", "beneficiary"],
        "date": ["date", "time", "period", "month", "year", "quarter"],
        "gender": ["gender", "sex"],
        "doctor": ["doctor", "physician", "provider"],
        "teacher": ["teacher", "instructor", "educator"],
        "crop": ["crop", "produce", "harvest"],
        "farm": ["farm", "field", "parcel"],
        "program": ["program", "initiative", "project"],
        "machine": ["machine", "equipment", "device"],
        "branch": ["branch", "office", "store"],
    }

    # Direction keywords
    INCREASE_KEYWORDS = ["increase", "increased", "rise", "rose", "grew", "growth", "up", "higher", "gain", "gained"]
    DECREASE_KEYWORDS = ["decrease", "decreased", "drop", "dropped", "decline", "declined", "fall", "fell", "down", "lower", "loss", "lost", "reduce", "reduced", "shrink", "shrank"]
    CHANGE_KEYWORDS = ["change", "changed", "shift", "shifted", "fluctuate", "fluctuated", "vary", "varied"]

    # Intent patterns
    WHY_PATTERNS = [
        r"^why\s+(did|do|does|is|are)\b",
        r"^what\s+(caused|causes)\b",
        r"^reason\s+for\b",
        r"^explain\s+(why|the\s+(drop|decline|increase|change))\b",
    ]
    TOP_N_PATTERNS = [
        r"(top|best|worst|bottom|highest|lowest|leading|performing)\s+(\d+)?\s*",
        r"(\d+)\s+(top|best|worst|leading)\b",
        r"rank\s+(by|top)\b",
        r"which\s+.*\s+(has|have)\s+(the\s+)?(highest|lowest|most|least|largest|smallest)\b",
    ]
    SUMMARY_PATTERNS = [
        r"^(summary|summarize|overview|sum up|recap|brief|snapshot)\b",
        r"^give\s+me\s+(a\s+)?summary\b",
        r"^what.*happening\b",
        r"^tell\s+me\s+about\b",
        r"^describe\s+(the\s+)?(data|dataset)\b",
    ]
    TREND_PATTERNS = [
        r"(trend|over\s+time|time\s+series|trajectory|pattern)",
        r"(monthly|weekly|daily|yearly|quarterly)\s+(trend|pattern|breakdown)",
        r"how.*changed\s+over\s+time",
    ]
    COMPARISON_PATTERNS = [
        r"(compare|comparison|versus|vs\.?|against|difference\s+between)",
        r"which\s+.*\s+(is|are)\s+(better|worse|higher|lower)\b",
    ]
    BREAKDOWN_PATTERNS = [
        r"(break\s*down|breakdown|split\s+by|group\s+by|distribute?d?\s+by|by\s+category|by\s+region|by\s+department)",
        r"(distribution|segmentation|composition)\s+(of|by)\b",
    ]
    ANOMALY_PATTERNS = [
        r"(anomal|unusual|outlier|abnormal|irregular|strange|weird|odd|spike|dip)",
        r"what.*wrong\b",
        r"anything\s+(strange|unusual|odd)\b",
    ]
    CORRELATION_PATTERNS = [
        r"(correlat|relationship\s+between|association\s+between|link\s+between|connect)",
        r"how\s+.*\s+relate\b",
        r"does\s+.*\s+(affect|impact|influence)\b",
    ]
    DESCRIBE_PATTERNS = [
        r"^(describe|what\s+is|tell\s+me\s+about|explain)\b",
        r"^(what\s+are|what\s+does)\b",
    ]

    @classmethod
    def parse(cls, text: str, col_mapping: dict[str, str] | None = None) -> ParsedQuery:
        """Parse a natural language question into a structured query.

        Args:
            text: The user's natural language question.
            col_mapping: Mapping of column names to entity keys (optional,
                         used to resolve metric/dimension references).

        Returns:
            ParsedQuery with intent, metric, dimension, and other parameters.
        """
        text_lower = text.lower().strip()
        col_mapping = col_mapping or {}

        # Determine intent
        intent = cls._detect_intent(text_lower)

        # Extract metric
        metric = cls._extract_metric(text_lower, col_mapping)

        # Extract dimension
        dimension = cls._extract_dimension(text_lower, col_mapping)

        # Extract direction
        direction = cls._extract_direction(text_lower)

        # Extract top_n
        top_n = cls._extract_top_n(text_lower)

        # Extract entities mentioned
        entities = cls._extract_entities(text_lower, col_mapping)

        return ParsedQuery(
            intent=intent,
            raw_text=text,
            metric=metric,
            dimension=dimension,
            direction=direction,
            top_n=top_n,
            entities=entities,
        )

    @classmethod
    def _detect_intent(cls, text: str) -> QueryIntent:
        # Check in priority order
        for pattern in cls.WHY_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.WHY_CHANGE

        for pattern in cls.ANOMALY_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.ANOMALY

        for pattern in cls.CORRELATION_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.CORRELATION

        for pattern in cls.TOP_N_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.TOP_N

        for pattern in cls.COMPARISON_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.COMPARISON

        for pattern in cls.BREAKDOWN_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.BREAKDOWN

        for pattern in cls.TREND_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.TREND

        for pattern in cls.SUMMARY_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.SUMMARY

        for pattern in cls.DESCRIBE_PATTERNS:
            if re.search(pattern, text):
                return QueryIntent.DESCRIBE

        return QueryIntent.UNKNOWN

    @classmethod
    def _extract_metric(cls, text: str, col_mapping: dict) -> str | None:
        # Check col_mapping entities first
        entity_values = set(col_mapping.values())
        for entity_key, synonyms in cls.METRIC_SYNONYMS.items():
            if entity_key in entity_values:
                for syn in synonyms:
                    if syn in text:
                        return entity_key
            else:
                for syn in synonyms:
                    if syn in text:
                        return entity_key
        return None

    @classmethod
    def _extract_dimension(cls, text: str, col_mapping: dict) -> str | None:
        entity_values = set(col_mapping.values())
        for entity_key, synonyms in cls.DIMENSION_SYNONYMS.items():
            if entity_key in entity_values:
                for syn in synonyms:
                    if syn in text:
                        return entity_key
            else:
                for syn in synonyms:
                    if syn in text:
                        return entity_key
        return None

    @classmethod
    def _extract_direction(cls, text: str) -> str | None:
        for kw in cls.INCREASE_KEYWORDS:
            if kw in text:
                return "increase"
        for kw in cls.DECREASE_KEYWORDS:
            if kw in text:
                return "decrease"
        for kw in cls.CHANGE_KEYWORDS:
            if kw in text:
                return "change"
        return None

    @classmethod
    def _extract_top_n(cls, text: str) -> int:
        # "top 5", "best 10", "top10"
        match = re.search(r"(?:top|best|worst|bottom|highest|lowest|leading)\s*(\d+)", text)
        if match:
            n = int(match.group(1))
            return max(1, min(n, 50))
        # "5 top"
        match = re.search(r"(\d+)\s*(?:top|best|worst|leading)", text)
        if match:
            n = int(match.group(1))
            return max(1, min(n, 50))
        return 5  # default

    @classmethod
    def _extract_entities(cls, text: str, col_mapping: dict) -> list[str]:
        entities = []
        all_synonyms: dict[str, str] = {}
        for entity_key, synonyms in {**cls.METRIC_SYNONYMS, **cls.DIMENSION_SYNONYMS}.items():
            for syn in synonyms:
                all_synonyms[syn] = entity_key

        for syn, entity_key in all_synonyms.items():
            if syn in text and entity_key not in entities:
                entities.append(entity_key)
        return entities
