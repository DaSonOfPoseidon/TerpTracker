# Value conversion utilities for terpene and cannabinoid data.
# Centralizes the "parse float, convert percentage to fraction" pattern
# that was previously duplicated across multiple API clients and parsers.

from typing import Optional


def safe_float(value) -> Optional[float]:
    """
    Safely parse a value to a positive float, return None on failure.

    Handles common lab-data sentinel values: '', 'nan', 'none', 'null',
    'nd' (not detected), 'n/a', '<loq' (below limit of quantitation).
    """
    if value is None:
        return None
    try:
        s = str(value).strip()
        if not s or s.lower() in ('', 'nan', 'none', 'null', 'nd', 'n/a', '<loq'):
            return None
        result = float(s)
        if result > 0:
            return result
        return None
    except (ValueError, TypeError):
        return None


def safe_terpene_value(value) -> Optional[float]:
    """
    Parse a terpene/cannabinoid value and normalize to a fraction (0-1 scale).

    Many APIs and datasets return values as percentages (e.g., 24.45 = 24.45%).
    This function converts them to fractions (e.g., 0.2445).

    Rules:
        - If value > 1, divide by 100 (treat as percentage)
        - If 0 < value <= 1, keep as-is (already a fraction)
        - Returns None on parse failure or non-positive values
    """
    parsed = safe_float(value)
    if parsed is None:
        return None
    return parsed / 100 if parsed > 1 else parsed
