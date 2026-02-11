# Multi-source data merging utilities for terpene and cannabinoid data.
# Pure functions with no state — extracted from StrainAnalyzer.

from typing import Dict, List
from app.models.schemas import Totals


def merge_terpene_data(
    coa_terpenes: Dict[str, float],
    page_terpenes: Dict[str, float],
    db_terpenes: Dict[str, float],
    api_terpenes: Dict[str, float],
) -> tuple[Dict[str, float], List[str]]:
    """
    Merge terpene data from multiple sources with priority: COA > Page > Database > API.

    For each terpene compound, uses the highest priority source that has it.

    Returns:
        Tuple of (merged_terpenes, sources_used)
    """
    merged = {}
    sources_used = set()

    sources = [
        ('coa', coa_terpenes),
        ('page', page_terpenes),
        ('database', db_terpenes),
        ('api', api_terpenes),
    ]

    # Collect all unique terpene keys
    all_keys = set()
    for _, terp_data in sources:
        if terp_data:
            all_keys.update(terp_data.keys())

    # For each terpene, use highest priority source
    for key in all_keys:
        for source_name, terp_data in sources:
            if terp_data and key in terp_data and terp_data[key] is not None and terp_data[key] > 0:
                merged[key] = terp_data[key]
                sources_used.add(source_name)
                break

    return merged, list(sources_used)


def merge_cannabinoid_data(
    coa_totals: Totals,
    page_totals: Totals,
    db_totals: Totals,
    api_totals: Totals,
) -> tuple[Totals, List[str]]:
    """
    Merge cannabinoid data from multiple sources with priority: COA > Page > Database > API.

    For each cannabinoid field, uses the highest priority source that has it.

    Returns:
        Tuple of (merged_totals, sources_used)
    """
    merged = Totals()
    sources_used = set()

    sources = [
        ('coa', coa_totals),
        ('page', page_totals),
        ('database', db_totals),
        ('api', api_totals),
    ]

    cannabinoid_fields = [
        'total_terpenes', 'thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
        'cbn', 'cbg', 'cbgm', 'cbgv', 'cbc', 'cbcv', 'cbv', 'cbe', 'cbt', 'cbl',
    ]

    for field in cannabinoid_fields:
        for source_name, totals_obj in sources:
            if totals_obj:
                value = getattr(totals_obj, field, None)
                if value is not None and value > 0:
                    setattr(merged, field, value)
                    sources_used.add(source_name)
                    break

    return merged, list(sources_used)
