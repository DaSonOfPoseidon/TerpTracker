# Strain name normalization utilities.
# Single implementation used by both ProfileCacheService and StrainAnalyzer.

from app.core.constants import STRAIN_NAME_SUFFIXES


def normalize_strain_name(name: str, title_case: bool = False) -> str:
    """
    Normalize a strain name for consistent lookups and API matching.

    Args:
        name: Raw strain name
        title_case: If True, return in Title Case (for API matching).
                    If False, return lowercase (for database lookups).

    Examples:
        normalize_strain_name("Blue Dream")          -> "blue dream"
        normalize_strain_name("Blue Dream", True)     -> "Blue Dream"
        normalize_strain_name("OG Kush #18")          -> "og kush 18"
        normalize_strain_name("Girl Scout Cookies")   -> "girl scout cookies"
    """
    name = name.lower()

    # Remove common product type suffixes
    for suffix in STRAIN_NAME_SUFFIXES:
        name = name.replace(f' {suffix}', '').replace(f'{suffix} ', '')

    # Clean special characters but keep spaces
    name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)

    # Normalize whitespace
    name = ' '.join(name.split()).strip()

    if title_case:
        return name.title()
    return name
