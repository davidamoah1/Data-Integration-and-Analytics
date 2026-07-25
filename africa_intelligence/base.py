"""Base structures for the Africa Intelligence Layer.

Defines:
  - CountryProfile: Full profile for a country (regions, currency, industries, structures)
  - RegionInfo, CurrencyInfo, IndustryInfo: Detailed metadata
  - EducationStructure, HealthcareStructure, AgricultureStructure: Domain templates
  - AfricaIntelligenceResult: Composite result for pipeline integration
  - AfricaIntelligenceRegistry: Registry for country profiles and analyzers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any


@dataclass
class RegionInfo:
    """Information about a region/state/province."""

    name: str
    code: str
    capital: str
    districts: list[str] = field(default_factory=list)
    population: int | None = None
    area_km2: float | None = None
    languages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "capital": self.capital,
            "districts": self.districts,
            "population": self.population,
            "area_km2": self.area_km2,
            "languages": self.languages,
        }


@dataclass
class CurrencyInfo:
    """Information about a country's currency."""

    code: str
    name: str
    symbol: str
    subunit: str
    subunit_symbol: str | None = None
    decimal_places: int = 2
    exchange_rate_to_usd: float | None = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "subunit": self.subunit,
            "subunit_symbol": self.subunit_symbol,
            "decimal_places": self.decimal_places,
            "exchange_rate_to_usd": self.exchange_rate_to_usd,
        }


@dataclass
class IndustryInfo:
    """Information about a local industry."""

    name: str
    sector: str
    description: str
    key_products: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    contribution_to_gdp: float | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "sector": self.sector,
            "description": self.description,
            "key_products": self.key_products,
            "regions": self.regions,
            "contribution_to_gdp": self.contribution_to_gdp,
        }


@dataclass
class EducationStructure:
    """Education system structure for a country."""

    levels: list[dict] = field(default_factory=list)
    grading_scales: dict[str, list[dict]] = field(default_factory=dict)
    academic_year: str = ""
    school_types: list[str] = field(default_factory=list)
    examination_bodies: list[str] = field(default_factory=list)
    notable_institutions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "levels": self.levels,
            "grading_scales": self.grading_scales,
            "academic_year": self.academic_year,
            "school_types": self.school_types,
            "examination_bodies": self.examination_bodies,
            "notable_institutions": self.notable_institutions,
        }


@dataclass
class HealthcareStructure:
    """Healthcare system structure for a country."""

    tiers: list[dict] = field(default_factory=list)
    insurance_schemes: list[dict] = field(default_factory=list)
    facility_types: list[str] = field(default_factory=list)
    major_diseases: list[str] = field(default_factory=list)
    regulatory_bodies: list[str] = field(default_factory=list)
    doctor_to_patient_ratio: str = ""

    def to_dict(self) -> dict:
        return {
            "tiers": self.tiers,
            "insurance_schemes": self.insurance_schemes,
            "facility_types": self.facility_types,
            "major_diseases": self.major_diseases,
            "regulatory_bodies": self.regulatory_bodies,
            "doctor_to_patient_ratio": self.doctor_to_patient_ratio,
        }


@dataclass
class AgricultureStructure:
    """Agriculture system structure for a country."""

    major_crops: list[dict] = field(default_factory=list)
    farming_systems: list[str] = field(default_factory=list)
    growing_seasons: list[dict] = field(default_factory=list)
    livestock: list[str] = field(default_factory=list)
    export_crops: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "major_crops": self.major_crops,
            "farming_systems": self.farming_systems,
            "growing_seasons": self.growing_seasons,
            "livestock": self.livestock,
            "export_crops": self.export_crops,
            "challenges": self.challenges,
        }


@dataclass
class CountryProfile:
    """Full profile for an African country."""

    name: str
    code: str  # ISO 3166-1 alpha-2
    dialing_code: str
    capital: str
    official_languages: list[str]
    currency: CurrencyInfo
    regions: list[RegionInfo]
    industries: list[IndustryInfo]
    education: EducationStructure
    healthcare: HealthcareStructure
    agriculture: AgricultureStructure
    national_holidays: list[dict] = field(default_factory=list)
    demographics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "dialing_code": self.dialing_code,
            "capital": self.capital,
            "official_languages": self.official_languages,
            "currency": self.currency.to_dict(),
            "regions": [r.to_dict() for r in self.regions],
            "industries": [i.to_dict() for i in self.industries],
            "education": self.education.to_dict(),
            "healthcare": self.healthcare.to_dict(),
            "agriculture": self.agriculture.to_dict(),
            "national_holidays": self.national_holidays,
            "demographics": self.demographics,
        }

    def get_region(self, name_or_code: str) -> RegionInfo | None:
        """Find a region by name or code (case-insensitive)."""
        query = name_or_code.lower().strip()
        for r in self.regions:
            if r.name.lower() == query or r.code.lower() == query:
                return r
        return None

    def get_industry(self, name: str) -> IndustryInfo | None:
        """Find an industry by name (case-insensitive)."""
        query = name.lower().strip()
        for i in self.industries:
            if i.name.lower() == query or i.sector.lower() == query:
                return i
        return None

    def get_all_region_names(self) -> list[str]:
        """Get all region names."""
        return [r.name for r in self.regions]

    def get_all_region_codes(self) -> list[str]:
        """Get all region codes."""
        return [r.code for r in self.regions]


@dataclass
class AfricaIntelligenceResult:
    """Composite result from Africa intelligence analysis."""

    detected_country: str | None = None
    detected_regions: list[str] = field(default_factory=list)
    detected_currency: str | None = None
    detected_industries: list[str] = field(default_factory=list)
    localized_columns: dict[str, str] = field(default_factory=dict)
    country_profile: dict | None = None
    region_mappings: list[dict] = field(default_factory=list)
    currency_mappings: list[dict] = field(default_factory=list)
    education_mappings: list[dict] = field(default_factory=list)
    healthcare_mappings: list[dict] = field(default_factory=list)
    agriculture_mappings: list[dict] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "detected_country": self.detected_country,
            "detected_regions": self.detected_regions,
            "detected_currency": self.detected_currency,
            "detected_industries": self.detected_industries,
            "localized_columns": self.localized_columns,
            "country_profile": self.country_profile,
            "region_mappings": self.region_mappings,
            "currency_mappings": self.currency_mappings,
            "education_mappings": self.education_mappings,
            "healthcare_mappings": self.healthcare_mappings,
            "agriculture_mappings": self.agriculture_mappings,
            "insights": self.insights,
            "summary": self.summary,
        }


class AfricaIntelligenceRegistry:
    """Registry for country profiles and Africa-specific analyzers."""

    _countries: dict[str, CountryProfile] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        if not cls._initialized:
            from africa_intelligence.ghana import GHANA_PROFILE
            from africa_intelligence.nigeria import NIGERIA_PROFILE
            from africa_intelligence.kenya import KENYA_PROFILE
            from africa_intelligence.south_africa import SOUTH_AFRICA_PROFILE

            cls._countries = {
                "GH": GHANA_PROFILE,
                "NG": NIGERIA_PROFILE,
                "KE": KENYA_PROFILE,
                "ZA": SOUTH_AFRICA_PROFILE,
            }
            cls._initialized = True

    @classmethod
    def get_country(cls, code: str) -> CountryProfile | None:
        """Get a country profile by ISO code."""
        cls._ensure_initialized()
        return cls._countries.get(code.upper())

    @classmethod
    def get_all_countries(cls) -> dict[str, CountryProfile]:
        """Get all registered country profiles."""
        cls._ensure_initialized()
        return cls._countries

    @classmethod
    def registered_country_codes(cls) -> list[str]:
        """Get all registered country codes."""
        cls._ensure_initialized()
        return list(cls._countries.keys())

    @classmethod
    def detect_country(cls, df, column_mapping: dict | None = None) -> str | None:
        """Detect which country the data likely belongs to.

        Checks for:
          - Region names matching a country's regions
          - Currency symbols/codes
          - Phone number patterns (dialing codes)
          - Local industry terms
        """
        cls._ensure_initialized()
        import pandas as pd

        scores: dict[str, int] = {code: 0 for code in cls._countries}

        # Collect all string values from object columns
        string_values: list[str] = []
        for col in df.select_dtypes(include=["object"]).columns:
            unique_vals = df[col].dropna().astype(str).unique()
            string_values.extend([v.lower().strip() for v in unique_vals])

        all_text = " ".join(string_values)

        for code, profile in cls._countries.items():
            # Check region names
            for region in profile.regions:
                if region.name.lower() in all_text:
                    scores[code] += 3
                # Only match region codes that are at least 3 chars to avoid false positives
                if len(region.code) >= 3 and region.code.lower() in all_text:
                    scores[code] += 2

            # Check currency (exact code match, not substring)
            if profile.currency.code.lower() in all_text.split():
                scores[code] += 5
            if profile.currency.symbol in all_text:
                scores[code] += 3

            # Check dialing code
            dialing = "+" + profile.dialing_code
            if dialing in all_text:
                scores[code] += 4

            # Check industry terms
            for industry in profile.industries:
                for product in industry.key_products:
                    if product.lower() in all_text:
                        scores[code] += 1

            # Check capital
            if profile.capital.lower() in all_text:
                scores[code] += 2

        # Return the country with highest score (if any score > 0)
        best_code = max(scores, key=scores.get)
        if scores[best_code] > 0:
            return best_code
        return None

    @classmethod
    def analyze(cls, df, column_mapping: dict | None = None) -> AfricaIntelligenceResult:
        """Run full Africa intelligence analysis on a DataFrame."""
        from africa_intelligence.recognizer import AfricaColumnRecognizer

        cls._ensure_initialized()
        result = AfricaIntelligenceResult()

        # Step 1: Detect country
        country_code = cls.detect_country(df, column_mapping)
        if country_code:
            result.detected_country = country_code
            profile = cls._countries[country_code]
            result.country_profile = profile.to_dict()

            # Step 2: Recognize African data patterns
            recognizer = AfricaColumnRecognizer(profile)
            recognized = recognizer.recognize(df, column_mapping)
            result.localized_columns = recognized["localized_columns"]
            result.detected_regions = recognized["detected_regions"]
            result.detected_currency = recognized["detected_currency"]
            result.detected_industries = recognized["detected_industries"]
            result.region_mappings = recognized["region_mappings"]
            result.currency_mappings = recognized["currency_mappings"]
            result.education_mappings = recognized["education_mappings"]
            result.healthcare_mappings = recognized["healthcare_mappings"]
            result.agriculture_mappings = recognized["agriculture_mappings"]
            result.insights = recognized["insights"]

            # Step 3: Generate summary
            parts = [f"Detected country: {profile.name} ({country_code})"]
            if result.detected_regions:
                parts.append(f"Regions found: {', '.join(result.detected_regions[:5])}")
            if result.detected_currency:
                parts.append(f"Currency: {result.detected_currency}")
            if result.detected_industries:
                parts.append(f"Industries: {', '.join(result.detected_industries[:5])}")
            if result.localized_columns:
                parts.append(f"Localized columns: {len(result.localized_columns)}")
            if result.insights:
                parts.append(f"Insights: {len(result.insights)}")
            result.summary = ". ".join(parts) + "."
        else:
            result.summary = "No African country detected in the data."

        return result
