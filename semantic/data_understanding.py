"""Data Understanding Engine — value-based semantic signals.

Analyzes column VALUES (not just names) to detect industry signals.
Complements the column-name-based SemanticEngine with a second signal layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ValueSignal:
    column_name: str
    signal_type: str
    industry: str
    confidence: float
    evidence: str
    suggested_entity: str | None = None


@dataclass
class DataUnderstandingResult:
    signals: list[ValueSignal] = field(default_factory=list)
    industry_votes: dict[str, float] = field(default_factory=dict)
    column_hints: dict[str, dict] = field(default_factory=dict)
    statistical_patterns: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "signals": [
                {
                    "column": s.column_name,
                    "signal_type": s.signal_type,
                    "industry": s.industry,
                    "confidence": round(s.confidence, 2),
                    "evidence": s.evidence,
                    "suggested_entity": s.suggested_entity,
                }
                for s in self.signals
            ],
            "industry_votes": {k: round(v, 2) for k, v in self.industry_votes.items()},
            "column_hints": self.column_hints,
            "statistical_patterns": self.statistical_patterns,
        }


# ── Regex patterns for value-based detection ──

_DIAGNOSIS_RE = re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,4})?$")
_CPT_RE = re.compile(r"^\d{5}$")
_NPI_RE = re.compile(r"^[12]\d{9}$")
_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")
_ACCOUNT_RE = re.compile(r"^\d{8,17}$")
_SWIFT_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")
_GRADE_RE = re.compile(r"^[A-F][+-]?$")
_CLAIM_RE = re.compile(r"^(CLM|CL)-?\d{4,12}$", re.IGNORECASE)
_POLICY_RE = re.compile(r"^(POL|PL)-?\d{4,12}$", re.IGNORECASE)
_TITHE_RE = re.compile(r"^(TITHE|OFFR|GIFT)-?\d{3,10}$", re.IGNORECASE)
_SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")
_PHONE_RE = re.compile(r"^\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$")
_IMEI_RE = re.compile(r"^\d{15}$")
_SKU_RE = re.compile(r"^[A-Z0-9]{3,5}-[A-Z0-9]{3,8}$", re.IGNORECASE)
_BARCODE_RE = re.compile(r"^\d{12,13}$")
_PART_RE = re.compile(r"^(PN|PART)-?\d{3,10}$", re.IGNORECASE)
_FIELD_RE = re.compile(r"^(FLD|PLOT|FARM)-?\d{1,8}$", re.IGNORECASE)
_DONATION_RE = re.compile(r"^(DON|GRANT|FUND)-?\d{3,10}$", re.IGNORECASE)
_RESERVATION_RE = re.compile(r"^(RES|RNV|BOOK)-?\d{3,10}$", re.IGNORECASE)

_CURRENCY_CODES = {
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CNY",
    "AUD",
    "CAD",
    "CHF",
    "GHS",
    "NGN",
    "ZAR",
    "KES",
}


class DataUnderstandingEngine:
    """Analyzes column values to detect industry signals."""

    SIGNAL_WEIGHTS = {
        "diagnosis_code": 3.0,
        "cpt_code": 2.5,
        "npi_number": 3.0,
        "iban": 3.0,
        "account_number": 2.0,
        "swift_code": 3.0,
        "grade": 3.0,
        "gpa": 3.0,
        "claim_number": 3.0,
        "policy_number": 2.5,
        "tithe_reference": 3.0,
        "ssn": 1.5,
        "phone_number": 0.5,
        "imei": 3.0,
        "sku_code": 2.0,
        "barcode": 2.0,
        "part_number": 2.5,
        "field_code": 2.5,
        "donation_reference": 2.5,
        "reservation_code": 2.5,
        "currency_in_values": 0.5,
        "monetary_range": 0.3,
    }

    @classmethod
    def analyze(cls, df: pd.DataFrame, sample_size: int = 100) -> DataUnderstandingResult:
        signals: list[ValueSignal] = []
        industry_votes: dict[str, float] = {}
        column_hints: dict[str, dict] = {}
        statistical_patterns: dict[str, dict] = {}

        for col_name in df.columns:
            col_signals = cls._analyze_column(df, col_name, sample_size)
            for sig in col_signals:
                signals.append(sig)
                if sig.industry != "universal":
                    weight = cls.SIGNAL_WEIGHTS.get(sig.signal_type, 0.5)
                    vote = weight * sig.confidence
                    industry_votes[sig.industry] = industry_votes.get(sig.industry, 0.0) + vote
                if sig.suggested_entity:
                    column_hints.setdefault(col_name, {})["suggested_entity"] = sig.suggested_entity
                column_hints.setdefault(col_name, {})["signal_type"] = sig.signal_type

            stats = cls._analyze_statistics(df, col_name)
            if stats:
                statistical_patterns[col_name] = stats

        return DataUnderstandingResult(
            signals=signals,
            industry_votes=industry_votes,
            column_hints=column_hints,
            statistical_patterns=statistical_patterns,
        )

    @classmethod
    def _analyze_column(
        cls, df: pd.DataFrame, col_name: str, sample_size: int
    ) -> list[ValueSignal]:
        series = df[col_name]
        non_null = series.dropna()
        if len(non_null) == 0:
            return []
        sample = non_null.head(sample_size).astype(str)
        n = len(sample)
        if n == 0:
            return []

        signals: list[ValueSignal] = []
        col_lower = col_name.lower()

        # Run all detectors
        for detector in [
            cls._det_healthcare,
            cls._det_banking,
            cls._det_education,
            cls._det_insurance,
            cls._det_church,
            cls._det_government,
            cls._det_telecom,
            cls._det_retail,
            cls._det_manufacturing,
            cls._det_agriculture,
            cls._det_ngo,
            cls._det_hospitality,
            cls._det_universal,
        ]:
            signals.extend(detector(col_name, col_lower, sample, n, non_null))

        return signals

    # ── Healthcare ──
    @staticmethod
    def _det_healthcare(col, cl, s, n, nn):
        out = []
        m = s.str.match(_DIAGNOSIS_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "diagnosis_code",
                    "healthcare",
                    min(m / n, 1.0),
                    f"{m}/{n} values match ICD-10 diagnosis code pattern",
                    "diagnosis",
                )
            )
        m = s.str.match(_CPT_RE).sum()
        if m / n > 0.6:
            out.append(
                ValueSignal(
                    col,
                    "cpt_code",
                    "healthcare",
                    min(m / n, 1.0),
                    f"{m}/{n} values match CPT procedure code pattern",
                    "procedure",
                )
            )
        m = s.str.match(_NPI_RE).sum()
        if m / n > 0.7:
            out.append(
                ValueSignal(
                    col,
                    "npi_number",
                    "healthcare",
                    min(m / n, 1.0),
                    f"{m}/{n} values match NPI pattern",
                    "doctor",
                )
            )
        return out

    # ── Banking ──
    @staticmethod
    def _det_banking(col, cl, s, n, nn):
        out = []
        m = s.str.match(_IBAN_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "iban",
                    "banking",
                    min(m / n, 1.0),
                    f"{m}/{n} values match IBAN pattern",
                    "account",
                )
            )
        m = s.str.match(_SWIFT_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "swift_code",
                    "banking",
                    min(m / n, 1.0),
                    f"{m}/{n} values match SWIFT/BIC code pattern",
                    "bank",
                )
            )
        m = s.str.match(_ACCOUNT_RE).sum()
        if m / n > 0.7 and len(s.iloc[0]) >= 8:
            if not any(kw in cl for kw in ("patient", "student", "teacher", "grade", "diagnosis")):
                out.append(
                    ValueSignal(
                        col,
                        "account_number",
                        "banking",
                        min(m / n * 0.7, 1.0),
                        f"{m}/{n} values match bank account number (8–17 digits)",
                        "account",
                    )
                )
        return out

    # ── Education ──
    @staticmethod
    def _det_education(col, cl, s, n, nn):
        out = []
        m = s.str.match(_GRADE_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "grade",
                    "education",
                    min(m / n, 1.0),
                    f"{m}/{n} values are letter grades (A–F)",
                    "grade",
                )
            )
        if np.issubdtype(nn.dtype, np.number):
            vals = nn.dropna()
            if len(vals) > 0:
                mn, mx = float(vals.min()), float(vals.max())
                if mn >= 0 and mx <= 4.0:
                    if any(kw in cl for kw in ("gpa", "score", "grade", "cgpa", "point")):
                        out.append(
                            ValueSignal(
                                col,
                                "gpa",
                                "education",
                                0.85,
                                "Numeric 0.0–4.0 range with GPA-like column name",
                                "grade",
                            )
                        )
        return out

    # ── Insurance ──
    @staticmethod
    def _det_insurance(col, cl, s, n, nn):
        out = []
        m = s.str.match(_CLAIM_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "claim_number",
                    "insurance",
                    min(m / n, 1.0),
                    f"{m}/{n} values match claim number pattern",
                    "claim",
                )
            )
        m = s.str.match(_POLICY_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "policy_number",
                    "insurance",
                    min(m / n, 1.0),
                    f"{m}/{n} values match policy number pattern",
                    "policy",
                )
            )
        return out

    # ── Church ──
    @staticmethod
    def _det_church(col, cl, s, n, nn):
        out = []
        m = s.str.match(_TITHE_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "tithe_reference",
                    "church",
                    min(m / n, 1.0),
                    f"{m}/{n} values match tithe/offering reference pattern",
                    "tithe",
                )
            )
        return out

    # ── Government ──
    @staticmethod
    def _det_government(col, cl, s, n, nn):
        out = []
        m = s.str.match(_SSN_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "ssn",
                    "government",
                    min(m / n, 1.0),
                    f"{m}/{n} values match SSN pattern (XXX-XX-XXXX)",
                    "citizen",
                )
            )
        return out

    # ── Telecom ──
    @staticmethod
    def _det_telecom(col, cl, s, n, nn):
        out = []
        m = s.str.match(_IMEI_RE).sum()
        if m / n > 0.7:
            out.append(
                ValueSignal(
                    col,
                    "imei",
                    "telecom",
                    min(m / n, 1.0),
                    f"{m}/{n} values match IMEI pattern (15 digits)",
                    "device",
                )
            )
        m = s.str.match(_PHONE_RE).sum()
        if m / n > 0.6 and any(kw in cl for kw in ("phone", "mobile", "cell", "tel", "msisdn")):
            out.append(
                ValueSignal(
                    col,
                    "phone_number",
                    "telecom",
                    min(m / n * 0.5, 1.0),
                    f"{m}/{n} values match phone number pattern",
                    "subscriber",
                )
            )
        return out

    # ── Retail ──
    @staticmethod
    def _det_retail(col, cl, s, n, nn):
        out = []
        m = s.str.match(_SKU_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "sku_code",
                    "retail",
                    min(m / n, 1.0),
                    f"{m}/{n} values match SKU pattern (XXX-XXXX)",
                    "product",
                )
            )
        m = s.str.match(_BARCODE_RE).sum()
        if m / n > 0.6 and any(kw in cl for kw in ("upc", "ean", "barcode", "sku", "product")):
            out.append(
                ValueSignal(
                    col,
                    "barcode",
                    "retail",
                    min(m / n, 1.0),
                    f"{m}/{n} values match UPC/EAN barcode (12–13 digits)",
                    "product",
                )
            )
        return out

    # ── Manufacturing ──
    @staticmethod
    def _det_manufacturing(col, cl, s, n, nn):
        out = []
        m = s.str.match(_PART_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "part_number",
                    "manufacturing",
                    min(m / n, 1.0),
                    f"{m}/{n} values match part number pattern (PN-prefix)",
                    "machine",
                )
            )
        return out

    # ── Agriculture ──
    @staticmethod
    def _det_agriculture(col, cl, s, n, nn):
        out = []
        m = s.str.match(_FIELD_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "field_code",
                    "agriculture",
                    min(m / n, 1.0),
                    f"{m}/{n} values match field/plot code pattern",
                    "crop",
                )
            )
        return out

    # ── NGO ──
    @staticmethod
    def _det_ngo(col, cl, s, n, nn):
        out = []
        m = s.str.match(_DONATION_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "donation_reference",
                    "ngo",
                    min(m / n, 1.0),
                    f"{m}/{n} values match donation/grant reference pattern",
                    "donation",
                )
            )
        return out

    # ── Hospitality ──
    @staticmethod
    def _det_hospitality(col, cl, s, n, nn):
        out = []
        m = s.str.match(_RESERVATION_RE).sum()
        if m / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "reservation_code",
                    "hospitality",
                    min(m / n, 1.0),
                    f"{m}/{n} values match reservation code pattern",
                    "reservation",
                )
            )
        return out

    # ── Universal (currency, monetary) ──
    @staticmethod
    def _det_universal(col, cl, s, n, nn):
        out = []
        # Currency codes in string values
        upper_vals = s.str.upper()
        curr_matches = upper_vals.isin(_CURRENCY_CODES).sum()
        if curr_matches / n > 0.5:
            out.append(
                ValueSignal(
                    col,
                    "currency_in_values",
                    "universal",
                    min(curr_matches / n, 1.0),
                    f"{curr_matches}/{n} values are ISO currency codes",
                    "currency",
                )
            )
        return out

    # ── Statistical patterns ──
    @staticmethod
    def _analyze_statistics(df: pd.DataFrame, col_name: str) -> dict | None:
        series = df[col_name]
        non_null = series.dropna()
        if len(non_null) == 0:
            return None

        result: dict[str, Any] = {}

        if np.issubdtype(series.dtype, np.number):
            result["type"] = "numeric"
            result["min"] = float(non_null.min())
            result["max"] = float(non_null.max())
            result["mean"] = float(non_null.mean())
            result["median"] = float(non_null.median())
            result["std"] = float(non_null.std()) if len(non_null) > 1 else 0.0
            result["unique_pct"] = float(non_null.nunique() / max(len(non_null), 1) * 100)

            # Detect monetary pattern: positive, decimals, reasonable range
            if result["min"] >= 0 and result["max"] > 100:
                result["likely_monetary"] = True

            # Detect percentage: 0–100 or 0–1 range
            if (
                result["min"] >= 0
                and result["max"] <= 1.0
                or result["min"] >= 0
                and result["max"] <= 100
                and result["mean"] < 50
            ):
                result["likely_percentage"] = True

            # Detect ID column: sequential integers, high uniqueness
            if result["unique_pct"] > 90:
                diffs = non_null.diff().dropna()
                if len(diffs) > 0 and (diffs == 1).all():
                    result["likely_sequential_id"] = True

        elif series.dtype == "object":
            result["type"] = "categorical"
            result["unique_count"] = int(non_null.nunique())
            result["unique_pct"] = float(non_null.nunique() / max(len(non_null), 1) * 100)
            vc = non_null.value_counts().head(5)
            result["top_values"] = {str(k): int(v) for k, v in vc.items()}

            # Low cardinality → likely dimension/category
            if result["unique_pct"] < 5:
                result["likely_dimension"] = True
            elif result["unique_pct"] > 90:
                result["likely_identifier"] = True

        elif np.issubdtype(series.dtype, np.datetime64):
            result["type"] = "datetime"
            result["min_date"] = str(non_null.min())
            result["max_date"] = str(non_null.max())
            result["span_days"] = (non_null.max() - non_null.min()).days

        return result if result else None
