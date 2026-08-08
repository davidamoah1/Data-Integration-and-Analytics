"""Africa Column Recognizer.

Recognizes African data patterns in DataFrames:
  - Region names (Ghana: Greater Accra, Ashanti; Nigeria: Lagos, Kano; etc.)
  - Currency symbols and codes (₵, GHS, ₦, NGN, KSh, KES, R, ZAR)
  - Phone numbers with African dialing codes (+233, +234, +254, +27)
  - Education terms (SHS, JHS, BECE, WASSCE, KCSE, NHIF)
  - Healthcare terms (NHIS, CHPS, NHIF, clinic, hospital)
  - Agriculture terms (cocoa, cassava, yam, maize, tea, coffee)

Provides localized column mapping and insights.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from africa_intelligence.base import CountryProfile


class AfricaColumnRecognizer:
    """Recognizes African data patterns in a DataFrame."""

    # Patterns that indicate specific column types
    REGION_KEYWORDS = {"region", "province", "state", "district", "metro", "constituency"}
    CURRENCY_KEYWORDS = {
        "amount",
        "price",
        "cost",
        "revenue",
        "salary",
        "fee",
        "payment",
        "balance",
        "total",
        "sum",
    }
    PHONE_KEYWORDS = {"phone", "mobile", "tel", "telephone", "contact", "cell", "whatsapp"}
    EDUCATION_KEYWORDS = {
        "grade",
        "score",
        "mark",
        "gpa",
        "cgpa",
        "class",
        "result",
        "exam",
        "test",
        "assessment",
    }
    HEALTHCARE_KEYWORDS = {
        "diagnosis",
        "patient",
        "admission",
        "discharge",
        "ward",
        "treatment",
        "medication",
        "prescription",
    }
    AGRICULTURE_KEYWORDS = {
        "crop",
        "yield",
        "harvest",
        "farm",
        "acre",
        "hectare",
        "production",
        "planting",
        "irrigation",
    }

    def __init__(self, profile: CountryProfile):
        self.profile = profile
        self._region_names_lower = {r.name.lower(): r.name for r in profile.regions}
        self._region_codes_lower = {r.code.lower(): r.name for r in profile.regions}
        self._all_districts = {}
        for r in profile.regions:
            for d in r.districts:
                self._all_districts[d.lower()] = r.name

    def recognize(self, df: pd.DataFrame, column_mapping: dict | None = None) -> dict[str, Any]:
        """Recognize African data patterns in the DataFrame."""
        result: dict[str, Any] = {
            "localized_columns": {},
            "detected_regions": [],
            "detected_currency": None,
            "detected_industries": [],
            "region_mappings": [],
            "currency_mappings": [],
            "education_mappings": [],
            "healthcare_mappings": [],
            "agriculture_mappings": [],
            "insights": [],
        }

        for col in df.columns:
            col_lower = str(col).lower()
            col_values = df[col].dropna().astype(str).unique() if col in df.columns else []

            # Check for region data
            region_match = self._check_region_column(col_lower, col_values)
            if region_match:
                result["localized_columns"][col] = f"region_{self.profile.code.lower()}"
                result["region_mappings"].append({"column": col, "type": "region", **region_match})
                for r in region_match.get("matched_regions", []):
                    if r not in result["detected_regions"]:
                        result["detected_regions"].append(r)

            # Check for currency data
            currency_match = self._check_currency_column(col_lower, col_values)
            if currency_match:
                result["localized_columns"][col] = f"currency_{self.profile.currency.code.lower()}"
                result["detected_currency"] = self.profile.currency.code
                result["currency_mappings"].append(
                    {"column": col, "type": "currency", **currency_match}
                )

            # Check for phone numbers
            phone_match = self._check_phone_column(col_lower, col_values)
            if phone_match:
                result["localized_columns"][col] = f"phone_{self.profile.code.lower()}"
                result["insights"].append(
                    f"Column '{col}' contains {self.profile.name} phone numbers (dialing code +{self.profile.dialing_code})."
                )

            # Check for education data
            edu_match = self._check_education_column(col_lower, col_values)
            if edu_match:
                result["localized_columns"][col] = f"education_{self.profile.code.lower()}"
                result["education_mappings"].append(
                    {"column": col, "type": "education", **edu_match}
                )

            # Check for healthcare data
            health_match = self._check_healthcare_column(col_lower, col_values)
            if health_match:
                result["localized_columns"][col] = f"healthcare_{self.profile.code.lower()}"
                result["healthcare_mappings"].append(
                    {"column": col, "type": "healthcare", **health_match}
                )

            # Check for agriculture data
            agri_match = self._check_agriculture_column(col_lower, col_values)
            if agri_match:
                result["localized_columns"][col] = f"agriculture_{self.profile.code.lower()}"
                result["agriculture_mappings"].append(
                    {"column": col, "type": "agriculture", **agri_match}
                )

        # Detect industries from all text
        all_text_parts: list[str] = []
        for col in df.select_dtypes(include=["object"]).columns:
            for v in df[col].dropna().astype(str).unique():
                all_text_parts.append(str(v).lower())
        all_text = " ".join(all_text_parts)
        for industry in self.profile.industries:
            # Check industry name
            if industry.name.lower() in all_text:
                if industry.name not in result["detected_industries"]:
                    result["detected_industries"].append(industry.name)
                continue
            # Check key products
            for product in industry.key_products:
                if product.lower() in all_text:
                    if industry.name not in result["detected_industries"]:
                        result["detected_industries"].append(industry.name)
                    break

        # Generate insights
        if result["detected_regions"]:
            result["insights"].append(
                f"Data contains {len(result['detected_regions'])} {self.profile.name} regions: {', '.join(result['detected_regions'][:5])}."
            )
        if result["detected_currency"]:
            result["insights"].append(
                f"Currency detected: {self.profile.currency.name} ({self.profile.currency.code}, symbol: {self.profile.currency.symbol})."
            )
        if result["detected_industries"]:
            result["insights"].append(
                f"Industries detected: {', '.join(result['detected_industries'])}."
            )
        if result["education_mappings"]:
            result["insights"].append(
                f"Education data detected in {len(result['education_mappings'])} column(s). "
                f"Grading system: {self.profile.education.academic_year}."
            )
        if result["healthcare_mappings"]:
            result["insights"].append(
                f"Healthcare data detected in {len(result['healthcare_mappings'])} column(s). "
                f"Insurance: {self.profile.healthcare.insurance_schemes[0]['name'] if self.profile.healthcare.insurance_schemes else 'N/A'}."
            )
        if result["agriculture_mappings"]:
            result["insights"].append(
                f"Agriculture data detected in {len(result['agriculture_mappings'])} column(s). "
                f"Major crops: {', '.join([c['name'] for c in self.profile.agriculture.major_crops[:5]])}."
            )

        return result

    def _check_region_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains region names."""
        # Check column name
        if not any(kw in col_lower for kw in self.REGION_KEYWORDS):
            return None

        matched_regions = []
        for v in values:
            v_lower = str(v).lower().strip()
            if v_lower in self._region_names_lower:
                matched_regions.append(self._region_names_lower[v_lower])
            elif v_lower in self._region_codes_lower:
                matched_regions.append(self._region_codes_lower[v_lower])
            elif v_lower in self._all_districts:
                matched_regions.append(self._all_districts[v_lower])

        if matched_regions:
            return {"matched_regions": list(set(matched_regions))}
        return None

    def _check_currency_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains currency values."""
        # Check column name for currency keywords
        if not any(kw in col_lower for kw in self.CURRENCY_KEYWORDS):
            return None

        # Check if values contain currency symbols
        symbol = self.profile.currency.symbol
        code = self.profile.currency.code
        has_symbol = any(symbol in str(v) for v in values[:100])
        has_code = any(code in str(v).upper() for v in values[:100])

        if has_symbol or has_code:
            return {"currency_code": code, "symbol": symbol}
        return None

    def _check_phone_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains phone numbers with the country's dialing code."""
        if not any(kw in col_lower for kw in self.PHONE_KEYWORDS):
            return None

        dialing = "+" + self.profile.dialing_code
        has_dialing = any(dialing in str(v) for v in values[:100])
        # Also check without + (e.g., 233...)
        has_dialing_no_plus = any(
            str(v).strip().startswith(self.profile.dialing_code) for v in values[:100]
        )

        if has_dialing or has_dialing_no_plus:
            return {"dialing_code": dialing}
        return None

    def _check_education_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains education-related data."""
        # Check column name
        if any(kw in col_lower for kw in self.EDUCATION_KEYWORDS):
            # Check if values match grading scales
            grading_values = set()
            for scale in self.profile.education.grading_scales.values():
                for entry in scale:
                    grading_values.add(entry["grade"].lower())

            matched_grades = [
                str(v).strip() for v in values if str(v).strip().lower() in grading_values
            ]
            if matched_grades:
                return {"matched_grades": list(set(matched_grades))[:10]}
            return {"type": "score_column"}

        # Check for education-specific terms in values
        edu_terms = []
        for level in self.profile.education.levels:
            edu_terms.append(level["name"].lower())
        for body in self.profile.education.examination_bodies:
            edu_terms.extend(term.lower() for term in body.split())

        for v in values:
            v_lower = str(v).lower()
            if any(term in v_lower for term in edu_terms):
                return {
                    "matched_terms": [
                        v for v in values if any(t in str(v).lower() for t in edu_terms)
                    ][:5]
                }

        return None

    def _check_healthcare_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains healthcare-related data."""
        if any(kw in col_lower for kw in self.HEALTHCARE_KEYWORDS):
            # Check for disease names
            diseases = [d.lower() for d in self.profile.healthcare.major_diseases]
            matched_diseases = [
                str(v).strip() for v in values if str(v).strip().lower() in diseases
            ]
            if matched_diseases:
                return {"matched_diseases": list(set(matched_diseases))[:10]}
            return {"type": "healthcare_column"}

        # Check for facility types
        facilities = [f.lower() for f in self.profile.healthcare.facility_types]
        for v in values:
            v_lower = str(v).lower()
            if any(f in v_lower for f in facilities):
                return {
                    "matched_facilities": [
                        v for v in values if any(f in str(v).lower() for f in facilities)
                    ][:5]
                }

        return None

    def _check_agriculture_column(self, col_lower: str, values: list) -> dict | None:
        """Check if a column contains agriculture-related data."""
        if any(kw in col_lower for kw in self.AGRICULTURE_KEYWORDS):
            # Check for crop names
            crops = [c["name"].lower() for c in self.profile.agriculture.major_crops]
            matched_crops = [str(v).strip() for v in values if str(v).strip().lower() in crops]
            if matched_crops:
                return {"matched_crops": list(set(matched_crops))[:10]}
            return {"type": "agriculture_column"}

        # Check for crop names in values
        crops = [c["name"].lower() for c in self.profile.agriculture.major_crops]
        for v in values:
            v_lower = str(v).lower()
            if any(c in v_lower for c in crops):
                return {
                    "matched_crops": [v for v in values if any(c in str(v).lower() for c in crops)][
                        :5
                    ]
                }

        return None
