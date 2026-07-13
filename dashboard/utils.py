"""Utility functions for the dashboard.

Formatting helpers and HTML sanitization for safe rendering.
"""

import html


def fmt_currency(v: float) -> str:
    """Format a numeric value as a currency string.

    Args:
        v: Numeric value to format.

    Returns:
        Formatted string like '$1.2M', '$15.3K', or '$1,234.56'.
    """
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:,.2f}"


def fmt_number(v: float) -> str:
    """Format a numeric value with thousands separators.

    Args:
        v: Numeric value to format.

    Returns:
        Formatted string like '12.3K' or '1,234'.
    """
    if v >= 1_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:,}"


def sanitize_text(text: str) -> str:
    """HTML-escape user-provided text to prevent XSS.

    Args:
        text: Raw text that may contain HTML/JS.

    Returns:
        HTML-escaped string safe for rendering.
    """
    if text is None:
        return ""
    return html.escape(str(text))


MAX_UPLOAD_SIZE_MB = 50
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
