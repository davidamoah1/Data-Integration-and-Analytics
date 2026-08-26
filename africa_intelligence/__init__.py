"""Africa Intelligence Layer.

Provides Ghana/Africa-specific understanding for the platform:
  - Country profiles (regions, currency, industries, structures)
  - Column recognizer for African data patterns
  - Currency converter for African currencies
  - Industry mapper for local sectors
  - Education, healthcare, agriculture templates

Countries supported:
  - Ghana (primary)
  - Nigeria, Kenya, South Africa (expansion)
  - Africa-wide datasets
"""

from __future__ import annotations

from africa_intelligence.base import (
    AfricaIntelligenceRegistry,
    AfricaIntelligenceResult,
    AgricultureStructure,
    CountryProfile,
    CurrencyInfo,
    EducationStructure,
    HealthcareStructure,
    IndustryInfo,
    RegionInfo,
)
from africa_intelligence.currency import AfricaCurrencyConverter
from africa_intelligence.ghana import GHANA_PROFILE
from africa_intelligence.industry_mapper import AfricaIndustryMapper
from africa_intelligence.kenya import KENYA_PROFILE
from africa_intelligence.nigeria import NIGERIA_PROFILE
from africa_intelligence.recognizer import AfricaColumnRecognizer
from africa_intelligence.south_africa import SOUTH_AFRICA_PROFILE

__all__ = [
    "CountryProfile",
    "RegionInfo",
    "CurrencyInfo",
    "IndustryInfo",
    "EducationStructure",
    "HealthcareStructure",
    "AgricultureStructure",
    "AfricaIntelligenceResult",
    "AfricaIntelligenceRegistry",
    "GHANA_PROFILE",
    "NIGERIA_PROFILE",
    "KENYA_PROFILE",
    "SOUTH_AFRICA_PROFILE",
    "AfricaColumnRecognizer",
    "AfricaCurrencyConverter",
    "AfricaIndustryMapper",
]
