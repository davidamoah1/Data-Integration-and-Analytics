"""Africa Currency Converter.

Converts between African currencies and USD.
Supports GHS, NGN, KES, ZAR with exchange rates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of a currency conversion."""

    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float

    def to_dict(self) -> dict:
        return {
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "amount": self.amount,
            "converted_amount": round(self.converted_amount, 2),
            "rate": round(self.rate, 6),
        }


class AfricaCurrencyConverter:
    """Convert between African currencies using USD as intermediary."""

    # Exchange rates to USD (1 unit = X USD)
    RATES_TO_USD: dict[str, float] = {
        "GHS": 0.075,
        "NGN": 0.00067,
        "KES": 0.0077,
        "ZAR": 0.053,
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
    }

    # Currency symbols
    SYMBOLS: dict[str, str] = {
        "GHS": "₵",
        "NGN": "₦",
        "KES": "KSh",
        "ZAR": "R",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    # Currency names
    NAMES: dict[str, str] = {
        "GHS": "Ghana Cedi",
        "NGN": "Nigerian Naira",
        "KES": "Kenyan Shilling",
        "ZAR": "South African Rand",
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
    }

    @classmethod
    def convert(cls, amount: float, from_currency: str, to_currency: str) -> ConversionResult:
        """Convert an amount from one currency to another.

        Uses USD as an intermediary for cross-rate calculation.
        """
        from_cur = from_currency.upper()
        to_cur = to_currency.upper()

        if from_cur not in cls.RATES_TO_USD:
            raise ValueError(f"Unsupported currency: {from_currency}")
        if to_cur not in cls.RATES_TO_USD:
            raise ValueError(f"Unsupported currency: {to_currency}")

        # Convert to USD first, then to target
        usd_amount = amount * cls.RATES_TO_USD[from_cur]
        converted = usd_amount / cls.RATES_TO_USD[to_cur]
        rate = cls.RATES_TO_USD[from_cur] / cls.RATES_TO_USD[to_cur]

        return ConversionResult(
            from_currency=from_cur,
            to_currency=to_cur,
            amount=amount,
            converted_amount=converted,
            rate=rate,
        )

    @classmethod
    def get_symbol(cls, currency_code: str) -> str:
        """Get the symbol for a currency code."""
        return cls.SYMBOLS.get(currency_code.upper(), currency_code)

    @classmethod
    def get_name(cls, currency_code: str) -> str:
        """Get the name for a currency code."""
        return cls.NAMES.get(currency_code.upper(), currency_code)

    @classmethod
    def supported_currencies(cls) -> list[dict]:
        """Get all supported currencies."""
        return [
            {"code": code, "name": cls.NAMES.get(code, code), "symbol": cls.SYMBOLS.get(code, ""),
             "rate_to_usd": rate}
            for code, rate in cls.RATES_TO_USD.items()
        ]

    @classmethod
    def detect_currency_in_text(cls, text: str) -> str | None:
        """Detect currency code or symbol in a text string."""
        text_upper = text.upper()
        for code in cls.RATES_TO_USD:
            if code in text_upper:
                return code
        for code, symbol in cls.SYMBOLS.items():
            if symbol in text:
                return code
        return None

    @classmethod
    def normalize_amount(cls, value: str, currency_code: str | None = None) -> float:
        """Parse a currency string and return a float.

        Handles formats like:
          - "₵1,500.00"
          - "GHS 1500"
          - "1,500.00"
          - "KSh 25,000"
        """
        if currency_code is None:
            currency_code = cls.detect_currency_in_text(value)

        # Remove currency symbols and codes
        cleaned = value
        if currency_code:
            cleaned = cleaned.replace(cls.SYMBOLS.get(currency_code, ""), "")
            cleaned = cleaned.replace(currency_code, "")
        # Remove common currency indicators
        for sym in ["$", "€", "£", "₵", "₦", "R", "KSh"]:
            cleaned = cleaned.replace(sym, "")
        # Remove commas and spaces
        cleaned = cleaned.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
