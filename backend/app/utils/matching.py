# Fuzzy strain name matching utilities.

from rapidfuzz import fuzz, process


def fuzzy_match_strain(query: str, candidates: list[str], threshold: float = 0.8) -> tuple[str, float]:
    """
    Fuzzy match a strain name against a list of candidates.

    Args:
        query: The strain name to match
        candidates: List of known strain names
        threshold: Minimum match score (0-1)

    Returns:
        Tuple of (best_match, score) or (query, 0.0) if no good match
    """
    if not candidates:
        return query, 0.0

    # Use RapidFuzz to find best match
    result = process.extractOne(
        query,
        candidates,
        scorer=fuzz.ratio
    )

    if result and result[1] >= threshold * 100:  # RapidFuzz returns 0-100
        return result[0], result[1] / 100
    else:
        return query, 0.0
