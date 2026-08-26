"""Africa Industry Mapper.

Maps local African industry terms to standard industry classifications.
Provides sector mapping for Ghana, Nigeria, Kenya, and South Africa.
"""

from __future__ import annotations


class AfricaIndustryMapper:
    """Maps local industry terms to standard sectors."""

    # Local term â†’ standard sector mapping (Africa-wide)
    LOCAL_TO_SECTOR: dict[str, str] = {
        # Agriculture
        "cocoa": "Agriculture - Cocoa",
        "cassava": "Agriculture - Food Crops",
        "yam": "Agriculture - Food Crops",
        "maize": "Agriculture - Food Crops",
        "rice": "Agriculture - Food Crops",
        "millet": "Agriculture - Food Crops",
        "sorghum": "Agriculture - Food Crops",
        "plantain": "Agriculture - Food Crops",
        "palm oil": "Agriculture - Oil Palm",
        "oil palm": "Agriculture - Oil Palm",
        "cashew": "Agriculture - Cashew",
        "shea": "Agriculture - Shea",
        "shea nuts": "Agriculture - Shea",
        "shea butter": "Agriculture - Shea",
        "tea": "Agriculture - Tea",
        "coffee": "Agriculture - Coffee",
        "flowers": "Agriculture - Horticulture",
        "horticulture": "Agriculture - Horticulture",
        "groundnut": "Agriculture - Groundnut",
        "groundnuts": "Agriculture - Groundnut",
        "citrus": "Agriculture - Citrus",
        "wine": "Agriculture - Viticulture",
        "wine grapes": "Agriculture - Viticulture",
        "sugar cane": "Agriculture - Sugar",
        "wheat": "Agriculture - Cereals",
        "cotton": "Agriculture - Cotton",
        "rubber": "Agriculture - Rubber",
        "timber": "Forestry - Timber",
        "lumber": "Forestry - Timber",
        "fishing": "Agriculture - Fishing",
        "tilapia": "Agriculture - Fishing",
        "tuna": "Agriculture - Fishing",
        # Mining
        "gold": "Mining - Gold",
        "gold mining": "Mining - Gold",
        "diamond": "Mining - Diamonds",
        "diamonds": "Mining - Diamonds",
        "platinum": "Mining - Platinum",
        "chromium": "Mining - Chromium",
        "manganese": "Mining - Manganese",
        "coal": "Mining - Coal",
        "iron ore": "Mining - Iron Ore",
        "bauxite": "Mining - Bauxite",
        # Energy
        "crude oil": "Energy - Oil & Gas",
        "oil": "Energy - Oil & Gas",
        "natural gas": "Energy - Oil & Gas",
        "lng": "Energy - Oil & Gas",
        "petroleum": "Energy - Oil & Gas",
        "lpg": "Energy - Oil & Gas",
        # Manufacturing
        "textiles": "Manufacturing - Textiles",
        "kente": "Manufacturing - Textiles",
        "adinkra": "Manufacturing - Textiles",
        "batik": "Manufacturing - Textiles",
        "garments": "Manufacturing - Garments",
        "cement": "Manufacturing - Cement",
        "food processing": "Manufacturing - Food Processing",
        "beverages": "Manufacturing - Beverages",
        "automotive": "Manufacturing - Automotive",
        "steel": "Manufacturing - Steel",
        "chemicals": "Manufacturing - Chemicals",
        # Services
        "tourism": "Services - Tourism",
        "safari": "Services - Tourism",
        "banking": "Services - Financial Services",
        "insurance": "Services - Financial Services",
        "fintech": "Services - Financial Services",
        "mobile money": "Services - Financial Services",
        "m-pesa": "Services - Financial Services",
        "telecommunications": "Services - Telecommunications",
        "telecom": "Services - Telecommunications",
        "film": "Entertainment - Film",
        "nollywood": "Entertainment - Film",
        "music": "Entertainment - Music",
        # Healthcare
        "nhis": "Healthcare - Insurance",
        "nhif": "Healthcare - Insurance",
        "chps": "Healthcare - Primary Care",
        "hospital": "Healthcare - Hospital",
        "clinic": "Healthcare - Clinic",
        "pharmacy": "Healthcare - Pharmacy",
        # Education
        "school": "Education - School",
        "university": "Education - University",
        "shs": "Education - Secondary",
        "jhs": "Education - Junior High",
        "basic school": "Education - Basic",
        "polytechnic": "Education - Tertiary",
        "wassce": "Education - Examination",
        "bece": "Education - Examination",
        "kcse": "Education - Examination",
        "kcpe": "Education - Examination",
    }

    # Country-specific industry highlights
    COUNTRY_HIGHLIGHTS: dict[str, list[str]] = {
        "GH": [
            "Cocoa",
            "Gold Mining",
            "Oil and Gas",
            "Timber",
            "Textiles and Garments",
            "Tourism",
            "Fishing",
        ],
        "NG": [
            "Oil and Gas",
            "Agriculture",
            "Telecommunications",
            "Nollywood (Film)",
            "Banking and Finance",
        ],
        "KE": [
            "Agriculture (Tea, Coffee, Horticulture)",
            "Tourism (Safari)",
            "Financial Services (M-Pesa)",
            "Manufacturing",
        ],
        "ZA": [
            "Mining (Platinum, Gold, Diamonds)",
            "Financial Services",
            "Manufacturing (Automotive)",
            "Tourism",
            "Agriculture (Wine, Citrus)",
        ],
    }

    @classmethod
    def map_to_sector(cls, term: str) -> str | None:
        """Map a local term to a standard sector.

        Args:
            term: A local industry term (e.g., "cocoa", "kente", "nhis").

        Returns:
            Standard sector name, or None if no match.
        """
        return cls.LOCAL_TO_SECTOR.get(term.lower().strip())

    @classmethod
    def map_column_values(cls, values: list[str]) -> dict[str, str]:
        """Map a list of values to their sectors.

        Returns:
            Dict mapping each value to its sector (only matched values).
        """
        result = {}
        for v in values:
            sector = cls.map_to_sector(str(v))
            if sector:
                result[str(v)] = sector
        return result

    @classmethod
    def get_country_highlights(cls, country_code: str) -> list[str]:
        """Get key industries for a country."""
        return cls.COUNTRY_HIGHLIGHTS.get(country_code.upper(), [])

    @classmethod
    def get_all_sectors(cls) -> list[str]:
        """Get all unique sectors."""
        return sorted(set(cls.LOCAL_TO_SECTOR.values()))

    @classmethod
    def get_terms_for_sector(cls, sector: str) -> list[str]:
        """Get all local terms that map to a given sector."""
        return sorted([term for term, sec in cls.LOCAL_TO_SECTOR.items() if sec == sector])

    @classmethod
    def detect_industries_in_text(cls, text: str) -> list[str]:
        """Detect industry terms in a text string."""
        text_lower = text.lower()
        detected = set()
        for term, sector in cls.LOCAL_TO_SECTOR.items():
            if term in text_lower:
                detected.add(sector)
        return sorted(detected)
