"""South Africa Country Profile."""

from __future__ import annotations

from africa_intelligence.base import (
    AgricultureStructure, CountryProfile, CurrencyInfo,
    EducationStructure, HealthcareStructure, IndustryInfo, RegionInfo,
)

SOUTH_AFRICA_PROFILE = CountryProfile(
    name="South Africa", code="ZA", dialing_code="27", capital="Pretoria",
    official_languages=["English", "Afrikaans", "Zulu", "Xhosa", "Sotho", "Tswana", "Tsonga", "Swati", "Venda", "Ndebele"],
    currency=CurrencyInfo(
        code="ZAR", name="South African Rand", symbol="R",
        subunit="Cent", subunit_symbol="c", decimal_places=2,
        exchange_rate_to_usd=0.053,
    ),
    regions=[
        RegionInfo(name="Gauteng", code="GP", capital="Johannesburg", population=15810388, area_km2=18178, languages=["English", "Zulu", "Afrikaans"]),
        RegionInfo(name="KwaZulu-Natal", code="KZN", capital="Pietermaritzburg", population=11538325, area_km2=94361, languages=["Zulu", "English"]),
        RegionInfo(name="Western Cape", code="WC", capital="Cape Town", population=7113149, area_km2=129462, languages=["Afrikaans", "English", "Xhosa"]),
        RegionInfo(name="Eastern Cape", code="EC", capital="Bhisho", population=6712276, area_km2=168966, languages=["Xhosa", "English"]),
        RegionInfo(name="Limpopo", code="LP", capital="Polokwane", population=5926724, area_km2=125754, languages=["Sotho", "Tsonga", "English"]),
        RegionInfo(name="Mpumalanga", code="MP", capital="Mbombela", population=4743584, area_km2=76495, languages=["Swati", "Zulu", "English"]),
        RegionInfo(name="North West", code="NW", capital="Mahikeng", population=4108802, area_km2=104882, languages=["Tswana", "English"]),
        RegionInfo(name="Free State", code="FS", capital="Bloemfontein", population=2928903, area_km2=129825, languages=["Sotho", "Afrikaans"]),
        RegionInfo(name="Northern Cape", code="NC", capital="Kimberley", population=1303575, area_km2=372889, languages=["Afrikaans", "English", "Tswana"]),
    ],
    industries=[
        IndustryInfo(name="Mining", sector="Mining", description="World's largest producer of platinum, chromium, manganese.",
            key_products=["platinum", "gold", "diamonds", "coal", "iron ore", "chromium"], regions=["Gauteng", "North West", "Limpopo", "Mpumalanga"], contribution_to_gdp=8.0),
        IndustryInfo(name="Financial Services", sector="Services", description="Most advanced banking sector in Africa.",
            key_products=["banking", "insurance", "investment", "fintech"], regions=["Gauteng", "Western Cape"], contribution_to_gdp=20.0),
        IndustryInfo(name="Manufacturing", sector="Manufacturing", description="Diversified industrial base.",
            key_products=["automotive", "chemicals", "steel", "food processing"], regions=["Gauteng", "KwaZulu-Natal", "Western Cape"], contribution_to_gdp=13.0),
        IndustryInfo(name="Tourism", sector="Services", description="Major tourist destination.",
            key_products=["Cape Town", "Kruger National Park", "Winelands", "Garden Route"], regions=["Western Cape", "Mpumalanga", "KwaZulu-Natal"], contribution_to_gdp=3.0),
        IndustryInfo(name="Agriculture", sector="Agriculture", description="Diverse agricultural sector.",
            key_products=["wine", "maize", "citrus", "sugar", "wool", "beef"], regions=["Western Cape", "Free State", "KwaZulu-Natal"], contribution_to_gdp=2.5),
    ],
    education=EducationStructure(
        levels=[
            {"name": "Foundation Phase", "duration": "3 years (Grades R-2)", "ages": "5-7"},
            {"name": "Intermediate Phase", "duration": "4 years (Grades 3-6)", "ages": "8-11"},
            {"name": "Senior Phase", "duration": "3 years (Grades 7-9)", "ages": "12-14"},
            {"name": "FET Phase (Further Education and Training)", "duration": "3 years (Grades 10-12)", "ages": "15-17"},
            {"name": "Higher Education (University)", "duration": "3-4 years", "ages": "18+"},
            {"name": "TVET Colleges", "duration": "1-3 years", "ages": "16+"},
        ],
        grading_scales={
            "FET": [
                {"grade": "7", "score": "80-100", "interpretation": "Outstanding Achievement"},
                {"grade": "6", "score": "70-79", "interpretation": "Meritorious Achievement"},
                {"grade": "5", "score": "60-69", "interpretation": "Substantial Achievement"},
                {"grade": "4", "score": "50-59", "interpretation": "Adequate Achievement"},
                {"grade": "3", "score": "40-49", "interpretation": "Moderate Achievement"},
                {"grade": "2", "score": "30-39", "interpretation": "Elementary Achievement"},
                {"grade": "1", "score": "0-29", "interpretation": "Not Achieved"},
            ],
        },
        academic_year="January to December (4 terms)",
        school_types=["Public", "Private", "Model C", "Independent"],
        examination_bodies=["Department of Basic Education (DBE)", "UMALUSI", "SAQA"],
        notable_institutions=[
            "University of Cape Town (UCT)",
            "University of the Witwatersrand (Wits)",
            "Stellenbosch University (SU)",
            "University of Pretoria (UP)",
            "University of KwaZulu-Natal (UKZN)",
        ],
    ),
    healthcare=HealthcareStructure(
        tiers=[
            {"name": "Primary Healthcare Clinic", "level": "Primary", "description": "Community-level care"},
            {"name": "District Hospital", "level": "Secondary", "description": "District-level referral"},
            {"name": "Regional Hospital", "level": "Secondary", "description": "Regional referral"},
            {"name": "Tertiary/Academic Hospital", "level": "Tertiary", "description": "Highest-level care"},
        ],
        insurance_schemes=[
            {"name": "Public Health System", "type": "Public", "coverage": "Nationwide (free at point of care)"},
            {"name": "Medical Aid Schemes", "type": "Private", "coverage": "Private insurance"},
            {"name": "NHI (National Health Insurance)", "type": "Public", "coverage": "In development"},
        ],
        facility_types=["Clinic", "Community Health Centre", "District Hospital", "Regional Hospital", "Tertiary Hospital", "Private Hospital"],
        major_diseases=["HIV/AIDS", "Tuberculosis", "Diabetes", "Hypertension", "Cervical Cancer"],
        regulatory_bodies=["Department of Health (DoH)", "Health Professions Council of South Africa (HPCSA)", "SAHPRA"],
        doctor_to_patient_ratio="1:3,000 (approximate)",
    ),
    agriculture=AgricultureStructure(
        major_crops=[
            {"name": "Maize", "season": "October-April", "regions": ["Free State", "Mpumalanga", "North West"], "export": False},
            {"name": "Wine Grapes", "season": "January-April (harvest)", "regions": ["Western Cape"], "export": True},
            {"name": "Citrus", "season": "April-September", "regions": ["Eastern Cape", "Limpopo", "Western Cape"], "export": True},
            {"name": "Sugar Cane", "season": "Year-round", "regions": ["KwaZulu-Natal", "Mpumalanga"], "export": False},
            {"name": "Wheat", "season": "May-November", "regions": ["Western Cape", "Free State"], "export": False},
        ],
        farming_systems=["Commercial farming", "Smallholder farming", "Communal farming", "Irrigation farming"],
        growing_seasons=[
            {"name": "Summer (Rainy)", "period": "October-April", "rainfall": "Summer rains"},
            {"name": "Winter (Rainy in WC)", "period": "May-August", "rainfall": "Winter rains (Western Cape only)"},
            {"name": "Dry Season", "period": "May-September", "rainfall": "Dry (except Western Cape)"},
        ],
        livestock=["Cattle", "Sheep", "Goats", "Poultry", "Pigs", "Ostrich"],
        export_crops=["Wine", "Citrus", "Table grapes", "Apples", "Pears", "Wool", "Maize"],
        challenges=["Drought", "Land reform", "Water scarcity", "Climate change"],
    ),
    national_holidays=[
        {"name": "New Year's Day", "date": "January 1"},
        {"name": "Human Rights Day", "date": "March 21"},
        {"name": "Freedom Day", "date": "April 27"},
        {"name": "Workers' Day", "date": "May 1"},
        {"name": "Youth Day", "date": "June 16"},
        {"name": "National Women's Day", "date": "August 9"},
        {"name": "Heritage Day", "date": "September 24"},
        {"name": "Day of Reconciliation", "date": "December 16"},
        {"name": "Christmas Day", "date": "December 25"},
        {"name": "Day of Goodwill", "date": "December 26"},
        {"name": "Good Friday", "date": "Variable"},
        {"name": "Easter Monday", "date": "Variable"},
    ],
    demographics={
        "population": 60000000, "life_expectancy": 65.0, "literacy_rate": 95.0,
        "urban_population_pct": 68.0,
        "major_ethnic_groups": ["Zulu", "Xhosa", "Sotho", "Tswana", "Afrikaner", "Indian", "Coloured"],
        "major_religions": ["Christianity", "Islam", "Hinduism", "Traditional"],
    },
)
