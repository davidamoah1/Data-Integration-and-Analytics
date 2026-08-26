"""Tests for Africa Intelligence Layer.

Tests cover:
  - Country profiles (Ghana, Nigeria, Kenya, South Africa)
  - Region lookup, currency info, industry mapping
  - Education, healthcare, agriculture structures
  - Column recognizer for African data patterns
  - Currency converter
  - Industry mapper
  - Registry: country detection, full analysis
  - Pipeline integration
"""

from __future__ import annotations

import pandas as pd
import pytest

from africa_intelligence import (
    GHANA_PROFILE,
    KENYA_PROFILE,
    NIGERIA_PROFILE,
    SOUTH_AFRICA_PROFILE,
    AfricaColumnRecognizer,
    AfricaCurrencyConverter,
    AfricaIndustryMapper,
    AfricaIntelligenceRegistry,
)

# â”€â”€ Ghana Profile Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestGhanaProfile:
    def test_basic_info(self):
        assert GHANA_PROFILE.name == "Ghana"
        assert GHANA_PROFILE.code == "GH"
        assert GHANA_PROFILE.dialing_code == "233"
        assert GHANA_PROFILE.capital == "Accra"
        assert "English" in GHANA_PROFILE.official_languages

    def test_has_16_regions(self):
        assert len(GHANA_PROFILE.regions) == 16

    def test_currency(self):
        assert GHANA_PROFILE.currency.code == "GHS"
        assert GHANA_PROFILE.currency.name == "Ghana Cedi"
        assert GHANA_PROFILE.currency.symbol == "â‚µ"
        assert GHANA_PROFILE.currency.subunit == "Pesewa"

    def test_get_region_by_name(self):
        region = GHANA_PROFILE.get_region("Greater Accra")
        assert region is not None
        assert region.capital == "Accra"

    def test_get_region_by_code(self):
        region = GHANA_PROFILE.get_region("AS")
        assert region is not None
        assert region.name == "Ashanti"

    def test_get_region_case_insensitive(self):
        region = GHANA_PROFILE.get_region("ashanti")
        assert region is not None
        assert region.name == "Ashanti"

    def test_get_region_not_found(self):
        assert GHANA_PROFILE.get_region("Nonexistent") is None

    def test_get_all_region_names(self):
        names = GHANA_PROFILE.get_all_region_names()
        assert "Greater Accra" in names
        assert "Ashanti" in names
        assert len(names) == 16

    def test_get_all_region_codes(self):
        codes = GHANA_PROFILE.get_all_region_codes()
        assert "GA" in codes
        assert "AS" in codes

    def test_industries(self):
        industry_names = [i.name for i in GHANA_PROFILE.industries]
        assert "Cocoa" in industry_names
        assert "Gold Mining" in industry_names
        assert "Oil and Gas" in industry_names

    def test_get_industry(self):
        industry = GHANA_PROFILE.get_industry("Cocoa")
        assert industry is not None
        assert industry.sector == "Agriculture"
        assert "cocoa beans" in industry.key_products

    def test_education_structure(self):
        levels = GHANA_PROFILE.education.levels
        assert len(levels) > 0
        level_names = [l["name"] for l in levels]
        assert "Senior High School (SHS)" in level_names

    def test_education_grading(self):
        shs_grades = GHANA_PROFILE.education.grading_scales.get("SHS", [])
        assert len(shs_grades) > 0
        grade_names = [g["grade"] for g in shs_grades]
        assert "A1" in grade_names
        assert "F9" in grade_names

    def test_education_examination_bodies(self):
        bodies = GHANA_PROFILE.education.examination_bodies
        assert any("WAEC" in b for b in bodies)

    def test_healthcare_structure(self):
        assert len(GHANA_PROFILE.healthcare.tiers) > 0
        assert len(GHANA_PROFILE.healthcare.insurance_schemes) > 0
        assert "Malaria" in GHANA_PROFILE.healthcare.major_diseases

    def test_healthcare_nhis(self):
        scheme_names = [s["name"] for s in GHANA_PROFILE.healthcare.insurance_schemes]
        assert any("NHIS" in n for n in scheme_names)

    def test_healthcare_chps(self):
        tier_names = [t["name"] for t in GHANA_PROFILE.healthcare.tiers]
        assert any("CHPS" in n for n in tier_names)

    def test_agriculture_structure(self):
        crops = GHANA_PROFILE.agriculture.major_crops
        assert len(crops) > 0
        crop_names = [c["name"] for c in crops]
        assert "Cocoa" in crop_names
        assert "Maize" in crop_names
        assert "Cassava" in crop_names

    def test_agriculture_export_crops(self):
        assert "Cocoa" in GHANA_PROFILE.agriculture.export_crops

    def test_agriculture_growing_seasons(self):
        seasons = GHANA_PROFILE.agriculture.growing_seasons
        assert len(seasons) >= 2

    def test_national_holidays(self):
        holidays = GHANA_PROFILE.national_holidays
        names = [h["name"] for h in holidays]
        assert "Independence Day" in names
        assert any("March 6" in h["date"] for h in holidays)

    def test_demographics(self):
        assert GHANA_PROFILE.demographics["population"] > 0
        assert "Akan" in GHANA_PROFILE.demographics["major_ethnic_groups"]

    def test_to_dict(self):
        d = GHANA_PROFILE.to_dict()
        assert d["name"] == "Ghana"
        assert d["code"] == "GH"
        assert "currency" in d
        assert "regions" in d
        assert "education" in d
        assert "healthcare" in d
        assert "agriculture" in d


# â”€â”€ Nigeria Profile Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestNigeriaProfile:
    def test_basic_info(self):
        assert NIGERIA_PROFILE.name == "Nigeria"
        assert NIGERIA_PROFILE.code == "NG"
        assert NIGERIA_PROFILE.dialing_code == "234"
        assert NIGERIA_PROFILE.capital == "Abuja"

    def test_currency(self):
        assert NIGERIA_PROFILE.currency.code == "NGN"
        assert NIGERIA_PROFILE.currency.symbol == "â‚¦"

    def test_has_36_states_plus_fct(self):
        assert len(NIGERIA_PROFILE.regions) == 37  # 36 states + FCT

    def test_lagos_region(self):
        lagos = NIGERIA_PROFILE.get_region("Lagos")
        assert lagos is not None
        assert lagos.capital == "Ikeja"

    def test_industries(self):
        names = [i.name for i in NIGERIA_PROFILE.industries]
        assert "Oil and Gas" in names
        assert "Agriculture" in names

    def test_education(self):
        assert len(NIGERIA_PROFILE.education.levels) > 0
        assert any("WAEC" in b for b in NIGERIA_PROFILE.education.examination_bodies)


# â”€â”€ Kenya Profile Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestKenyaProfile:
    def test_basic_info(self):
        assert KENYA_PROFILE.name == "Kenya"
        assert KENYA_PROFILE.code == "KE"
        assert KENYA_PROFILE.dialing_code == "254"
        assert KENYA_PROFILE.capital == "Nairobi"

    def test_currency(self):
        assert KENYA_PROFILE.currency.code == "KES"
        assert KENYA_PROFILE.currency.symbol == "KSh"

    def test_official_languages(self):
        assert "Swahili" in KENYA_PROFILE.official_languages
        assert "English" in KENYA_PROFILE.official_languages

    def test_industries(self):
        names = [i.name for i in KENYA_PROFILE.industries]
        assert "Tourism" in names
        assert "Agriculture" in names

    def test_education_grading(self):
        secondary = KENYA_PROFILE.education.grading_scales.get("Secondary", [])
        assert len(secondary) > 0
        grades = [g["grade"] for g in secondary]
        assert "A" in grades


# â”€â”€ South Africa Profile Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestSouthAfricaProfile:
    def test_basic_info(self):
        assert SOUTH_AFRICA_PROFILE.name == "South Africa"
        assert SOUTH_AFRICA_PROFILE.code == "ZA"
        assert SOUTH_AFRICA_PROFILE.dialing_code == "27"
        assert SOUTH_AFRICA_PROFILE.capital == "Pretoria"

    def test_currency(self):
        assert SOUTH_AFRICA_PROFILE.currency.code == "ZAR"
        assert SOUTH_AFRICA_PROFILE.currency.symbol == "R"

    def test_has_9_provinces(self):
        assert len(SOUTH_AFRICA_PROFILE.regions) == 9

    def test_official_languages(self):
        assert len(SOUTH_AFRICA_PROFILE.official_languages) >= 10
        assert "Zulu" in SOUTH_AFRICA_PROFILE.official_languages

    def test_industries(self):
        names = [i.name for i in SOUTH_AFRICA_PROFILE.industries]
        assert "Mining" in names
        assert "Financial Services" in names


# â”€â”€ Registry Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestAfricaIntelligenceRegistry:
    def test_registered_countries(self):
        codes = AfricaIntelligenceRegistry.registered_country_codes()
        assert "GH" in codes
        assert "NG" in codes
        assert "KE" in codes
        assert "ZA" in codes

    def test_get_country(self):
        ghana = AfricaIntelligenceRegistry.get_country("GH")
        assert ghana is not None
        assert ghana.name == "Ghana"

    def test_get_country_not_found(self):
        assert AfricaIntelligenceRegistry.get_country("XX") is None

    def test_get_all_countries(self):
        countries = AfricaIntelligenceRegistry.get_all_countries()
        assert len(countries) == 4

    def test_detect_ghana_data(self):
        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti", "Western"],
                "amount_ghs": ["â‚µ1000", "â‚µ2000", "â‚µ3000"],
            }
        )
        code = AfricaIntelligenceRegistry.detect_country(df)
        assert code == "GH"

    def test_detect_nigeria_data(self):
        df = pd.DataFrame(
            {
                "state": ["Lagos", "Kano", "Rivers"],
                "amount_ngn": ["â‚¦50000", "â‚¦100000", "â‚¦75000"],
            }
        )
        code = AfricaIntelligenceRegistry.detect_country(df)
        assert code == "NG"

    def test_detect_kenya_data(self):
        df = pd.DataFrame(
            {
                "county": ["Nairobi", "Mombasa", "Kisumu"],
                "amount_kes": ["KSh 5000", "KSh 3000", "KSh 2000"],
            }
        )
        code = AfricaIntelligenceRegistry.detect_country(df)
        assert code == "KE"

    def test_detect_south_africa_data(self):
        df = pd.DataFrame(
            {
                "province": ["Gauteng", "Western Cape", "KwaZulu-Natal"],
                "amount zar": ["R1500", "R2000", "R1000"],
            }
        )
        code = AfricaIntelligenceRegistry.detect_country(df)
        assert code == "ZA"

    def test_detect_no_match(self):
        df = pd.DataFrame({"col": ["abc", "def", "ghi"]})
        code = AfricaIntelligenceRegistry.detect_country(df)
        assert code is None

    def test_analyze_ghana(self):
        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti", "Western", "Central"],
                "revenue_ghs": ["â‚µ1000", "â‚µ2000", "â‚µ3000", "â‚µ1500"],
                "crop": ["cocoa", "maize", "cocoa", "cassava"],
            }
        )
        result = AfricaIntelligenceRegistry.analyze(df)
        assert result.detected_country == "GH"
        assert "Greater Accra" in result.detected_regions
        assert result.detected_currency == "GHS"
        assert "Cocoa" in result.detected_industries
        assert result.summary != ""

    def test_analyze_no_country(self):
        df = pd.DataFrame({"col": ["abc", "def"]})
        result = AfricaIntelligenceRegistry.analyze(df)
        assert result.detected_country is None
        assert "No African country" in result.summary

    def test_analyze_to_dict(self):
        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti"],
                "amount": ["â‚µ1000", "â‚µ2000"],
            }
        )
        result = AfricaIntelligenceRegistry.analyze(df)
        d = result.to_dict()
        assert "detected_country" in d
        assert "detected_regions" in d
        assert "insights" in d


# â”€â”€ Column Recognizer Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestAfricaColumnRecognizer:
    def test_recognize_regions(self):
        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti", "Western"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert "region" in result["localized_columns"]
        assert "Greater Accra" in result["detected_regions"]

    def test_recognize_currency(self):
        df = pd.DataFrame(
            {
                "revenue": ["â‚µ1000", "â‚µ2000", "â‚µ3000"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert result["detected_currency"] == "GHS"

    def test_recognize_phone(self):
        df = pd.DataFrame(
            {
                "phone": ["+233244567890", "+233205556666", "+233277778888"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert "phone" in result["localized_columns"]

    def test_recognize_education(self):
        df = pd.DataFrame(
            {
                "grade": ["A1", "B2", "C4", "F9"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert "grade" in result["localized_columns"]
        assert len(result["education_mappings"]) > 0

    def test_recognize_healthcare(self):
        df = pd.DataFrame(
            {
                "diagnosis": ["Malaria", "HIV/AIDS", "Tuberculosis"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert "diagnosis" in result["localized_columns"]

    def test_recognize_agriculture(self):
        df = pd.DataFrame(
            {
                "crop": ["cocoa", "maize", "cassava"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert "crop" in result["localized_columns"]
        assert len(result["agriculture_mappings"]) > 0

    def test_insights_generated(self):
        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti"],
                "revenue": ["â‚µ1000", "â‚µ2000"],
                "crop": ["cocoa", "maize"],
            }
        )
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert len(result["insights"]) > 0

    def test_no_match(self):
        df = pd.DataFrame({"random_col": ["abc", "def", "ghi"]})
        recognizer = AfricaColumnRecognizer(GHANA_PROFILE)
        result = recognizer.recognize(df)
        assert len(result["localized_columns"]) == 0
        assert len(result["detected_regions"]) == 0


# â”€â”€ Currency Converter Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestAfricaCurrencyConverter:
    def test_convert_ghs_to_usd(self):
        result = AfricaCurrencyConverter.convert(1000, "GHS", "USD")
        assert result.from_currency == "GHS"
        assert result.to_currency == "USD"
        assert result.converted_amount > 0

    def test_convert_ngn_to_ghs(self):
        result = AfricaCurrencyConverter.convert(10000, "NGN", "GHS")
        assert result.from_currency == "NGN"
        assert result.to_currency == "GHS"
        assert result.converted_amount > 0

    def test_convert_kes_to_zar(self):
        result = AfricaCurrencyConverter.convert(5000, "KES", "ZAR")
        assert result.from_currency == "KES"
        assert result.to_currency == "ZAR"

    def test_get_symbol(self):
        assert AfricaCurrencyConverter.get_symbol("GHS") == "â‚µ"
        assert AfricaCurrencyConverter.get_symbol("NGN") == "â‚¦"
        assert AfricaCurrencyConverter.get_symbol("KES") == "KSh"
        assert AfricaCurrencyConverter.get_symbol("ZAR") == "R"

    def test_get_name(self):
        assert "Cedi" in AfricaCurrencyConverter.get_name("GHS")
        assert "Naira" in AfricaCurrencyConverter.get_name("NGN")

    def test_supported_currencies(self):
        currencies = AfricaCurrencyConverter.supported_currencies()
        codes = [c["code"] for c in currencies]
        assert "GHS" in codes
        assert "NGN" in codes
        assert "KES" in codes
        assert "ZAR" in codes

    def test_detect_currency_in_text(self):
        assert AfricaCurrencyConverter.detect_currency_in_text("Amount: â‚µ1500") == "GHS"
        assert AfricaCurrencyConverter.detect_currency_in_text("NGN 50000") == "NGN"

    def test_normalize_amount(self):
        assert AfricaCurrencyConverter.normalize_amount("â‚µ1,500.00", "GHS") == 1500.0
        assert AfricaCurrencyConverter.normalize_amount("GHS 2000") == 2000.0
        assert AfricaCurrencyConverter.normalize_amount("1,000.50") == 1000.50

    def test_unsupported_currency_raises(self):
        with pytest.raises(ValueError):
            AfricaCurrencyConverter.convert(100, "XYZ", "USD")

    def test_conversion_result_to_dict(self):
        result = AfricaCurrencyConverter.convert(1000, "GHS", "USD")
        d = result.to_dict()
        assert "from_currency" in d
        assert "converted_amount" in d
        assert "rate" in d


# â”€â”€ Industry Mapper Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestAfricaIndustryMapper:
    def test_map_cocoa(self):
        assert AfricaIndustryMapper.map_to_sector("cocoa") == "Agriculture - Cocoa"

    def test_map_gold(self):
        assert AfricaIndustryMapper.map_to_sector("gold") == "Mining - Gold"

    def test_map_kente(self):
        assert AfricaIndustryMapper.map_to_sector("kente") == "Manufacturing - Textiles"

    def test_map_nhis(self):
        assert AfricaIndustryMapper.map_to_sector("nhis") == "Healthcare - Insurance"

    def test_map_no_match(self):
        assert AfricaIndustryMapper.map_to_sector("nonexistent") is None

    def test_map_column_values(self):
        result = AfricaIndustryMapper.map_column_values(["cocoa", "gold", "unknown"])
        assert result["cocoa"] == "Agriculture - Cocoa"
        assert result["gold"] == "Mining - Gold"
        assert "unknown" not in result

    def test_country_highlights_ghana(self):
        highlights = AfricaIndustryMapper.get_country_highlights("GH")
        assert "Cocoa" in highlights
        assert "Gold Mining" in highlights

    def test_country_highlights_nigeria(self):
        highlights = AfricaIndustryMapper.get_country_highlights("NG")
        assert "Oil and Gas" in highlights

    def test_get_all_sectors(self):
        sectors = AfricaIndustryMapper.get_all_sectors()
        assert len(sectors) > 0
        assert "Agriculture - Cocoa" in sectors

    def test_get_terms_for_sector(self):
        terms = AfricaIndustryMapper.get_terms_for_sector("Agriculture - Cocoa")
        assert "cocoa" in terms

    def test_detect_industries_in_text(self):
        detected = AfricaIndustryMapper.detect_industries_in_text(
            "We produce cocoa and gold in Ghana"
        )
        assert "Agriculture - Cocoa" in detected
        assert "Mining - Gold" in detected


# â”€â”€ Pipeline Integration Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestPipelineIntegration:
    def test_africa_intelligence_in_mapping_result(self):
        from semantic.mapping_engine import SemanticMappingEngine

        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti", "Western"],
                "revenue": [1000, 2000, 3000],
                "crop": ["cocoa", "maize", "cassava"],
            }
        )
        result = SemanticMappingEngine.analyze(df, "ghana_data.csv")
        assert result.africa_intelligence is not None

    def test_africa_intelligence_in_to_dict(self):
        from semantic.mapping_engine import SemanticMappingEngine

        df = pd.DataFrame(
            {
                "region": ["Greater Accra", "Ashanti"],
                "amount": [1000, 2000],
            }
        )
        result = SemanticMappingEngine.analyze(df, "ghana.csv")
        d = result.to_dict()
        assert "africa_intelligence" in d
        assert d["africa_intelligence"] is not None

    def test_nigeria_pipeline(self):
        from semantic.mapping_engine import SemanticMappingEngine

        df = pd.DataFrame(
            {
                "state": ["Lagos", "Kano", "Rivers"],
                "amount": [50000, 100000, 75000],
            }
        )
        result = SemanticMappingEngine.analyze(df, "nigeria.csv")
        assert result.africa_intelligence is not None
        assert result.africa_intelligence.detected_country == "NG"

    def test_no_african_data_pipeline(self):
        from semantic.mapping_engine import SemanticMappingEngine

        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        result = SemanticMappingEngine.analyze(df, "generic.csv")
        assert result.africa_intelligence is not None
        assert result.africa_intelligence.detected_country is None
