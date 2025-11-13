"""
Terpene classifier implementing SDP (Strain Data Project) categories.

Categories:
- BLUE: Myrcene-dominant
- YELLOW: Limonene-dominant; notable Caryophyllene + Linalool, appreciable Pinene
- PURPLE: Caryophyllene-dominant; notable Limonene, Humulene, Myrcene; low Pinene
- GREEN: Pinene-dominant; rare/diverse, notable α-Pinene, Myrcene, Caryophyllene
- ORANGE: Terpinolene-dominant; notable Myrcene + β-Ocimene
- RED: Myrcene + Limonene + Caryophyllene in roughly equal amounts; low Pinene/Humulene
"""

from typing import Dict, Tuple, List

# Category descriptions for summaries
CATEGORY_DESCRIPTIONS = {
    "BLUE": "myrcene-forward with an earthy, relaxing profile",
    "YELLOW": "limonene-forward with bright, citrus-leaning aroma and an upbeat profile",
    "PURPLE": "caryophyllene-forward with spicy, peppery notes and a balanced profile",
    "GREEN": "pinene-forward with sharp, pine-like aroma and an alert profile",
    "ORANGE": "terpinolene-forward with complex, floral, and citrus notes",
    "RED": "balanced myrcene-limonene-caryophyllene with a versatile, hybrid profile"
}

def normalize_terpene_profile(terpenes: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize terpene percentages to sum to 1.0 for classification.
    Handles various naming conventions.
    """
    # Normalize keys to standard names
    key_mapping = {
        "beta_myrcene": "myrcene",
        "β-myrcene": "myrcene",
        "d_limonene": "limonene",
        "d-limonene": "limonene",
        "beta_caryophyllene": "caryophyllene",
        "β-caryophyllene": "caryophyllene",
        "alpha_pinene": "alpha_pinene",
        "α-pinene": "alpha_pinene",
        "beta_pinene": "beta_pinene",
        "β-pinene": "beta_pinene",
        "beta_ocimene": "ocimene",
        "β-ocimene": "ocimene",
    }

    normalized = {}
    for key, value in terpenes.items():
        std_key = key_mapping.get(key.lower(), key.lower())
        if value is not None and value > 0:
            normalized[std_key] = float(value)

    # Calculate total for normalization
    total = sum(normalized.values())
    if total > 0:
        return {k: v / total for k, v in normalized.items()}
    return normalized

def get_combined_pinene(terps: Dict[str, float]) -> float:
    """Get combined alpha + beta pinene percentage."""
    return terps.get("alpha_pinene", 0) + terps.get("beta_pinene", 0)

def get_top_terpene(terps: Dict[str, float]) -> Tuple[str, float]:
    """Get the dominant terpene and its percentage."""
    if not terps:
        return "", 0.0
    top = max(terps.items(), key=lambda x: x[1])
    return top[0], top[1]

def is_within_range(values: list, tolerance: float = 0.15) -> bool:
    """Check if all values are within tolerance of each other."""
    if not values:
        return False
    avg = sum(values) / len(values)
    return all(abs(v - avg) / avg <= tolerance for v in values)

def classify_terpene_profile(terpenes: Dict[str, float]) -> str:
    """
    Classify terpene profile into one of the 6 SDP categories.

    Args:
        terpenes: Dictionary of terpene names to percentages (0-100 or 0-1)

    Returns:
        Category string: BLUE, YELLOW, PURPLE, GREEN, ORANGE, or RED
    """
    # Normalize the profile
    terps = normalize_terpene_profile(terpenes)

    if not terps:
        return "BLUE"  # Default fallback

    # Get individual terpene values
    myrcene = terps.get("myrcene", 0)
    limonene = terps.get("limonene", 0)
    caryophyllene = terps.get("caryophyllene", 0)
    terpinolene = terps.get("terpinolene", 0)
    pinene_total = get_combined_pinene(terps)
    humulene = terps.get("humulene", 0)

    top_terp, top_value = get_top_terpene(terps)

    # Apply SDP classification heuristic

    # ORANGE: Terpinolene-dominant
    if terpinolene >= 0.35 or (top_terp == "terpinolene" and top_value - terpinolene >= 0.10):
        return "ORANGE"

    # GREEN: Pinene-dominant
    if pinene_total >= 0.35 or (top_terp in ["alpha_pinene", "beta_pinene"] and top_value >= 0.10):
        return "GREEN"

    # BLUE: Myrcene-dominant
    if myrcene >= 0.35 or (top_terp == "myrcene" and top_value - myrcene >= 0.10):
        return "BLUE"

    # PURPLE: Caryophyllene-dominant with low pinene
    if caryophyllene >= 0.30 and pinene_total <= 0.15:
        return "PURPLE"

    # YELLOW: Limonene-dominant
    if limonene >= 0.30:
        return "YELLOW"

    # RED: Balanced myrcene-limonene-caryophyllene
    if (myrcene >= 0.20 and limonene >= 0.20 and caryophyllene >= 0.20 and
        is_within_range([myrcene, limonene, caryophyllene]) and
        pinene_total <= 0.15 and humulene <= 0.15):
        return "RED"

    # Fallback: pick nearest by top terpene
    if top_terp == "myrcene":
        return "BLUE"
    elif top_terp == "limonene":
        return "YELLOW"
    elif top_terp == "caryophyllene":
        return "PURPLE"
    elif top_terp in ["alpha_pinene", "beta_pinene"]:
        return "GREEN"
    elif top_terp == "terpinolene":
        return "ORANGE"

    # Ultimate fallback
    return "BLUE"

def generate_summary(strain_name: str, category: str, terpenes: Dict[str, float]) -> str:
    """
    Generate a friendly one-liner summary for the strain.

    Args:
        strain_name: Name of the strain
        category: SDP category (BLUE, YELLOW, etc.)
        terpenes: Terpene profile

    Returns:
        One-line summary string
    """
    description = CATEGORY_DESCRIPTIONS.get(category, "a unique terpene profile")

    # Get top 3 terpenes for detail
    sorted_terps = sorted(terpenes.items(), key=lambda x: x[1], reverse=True)[:3]
    top_names = [name.replace("_", "-") for name, _ in sorted_terps]

    if len(top_names) >= 2:
        terp_detail = f" featuring {top_names[0]} and {top_names[1]}"
    else:
        terp_detail = ""

    return f"{strain_name}'s composition puts it in the {category} category — expect {description}{terp_detail}."

def generate_cannabinoid_insights(totals) -> List[str]:
    """
    Generate insights from cannabinoid ratios.

    Args:
        totals: Totals object with cannabinoid data

    Returns:
        List of insight strings
    """
    insights = []

    # Get effective THC and CBD (accounting for acid forms)
    thc_total = (totals.thc or 0) + (totals.thca or 0) * 0.877  # THCA decarboxylation factor
    cbd_total = (totals.cbd or 0) + (totals.cbda or 0) * 0.877  # CBDA decarboxylation factor

    # THC:CBD ratio insights
    if thc_total > 0 and cbd_total > 0:
        ratio = thc_total / cbd_total
        if ratio > 20:
            insights.append(f"THC-dominant ({ratio:.0f}:1 ratio)")
        elif ratio > 5:
            insights.append(f"High THC ({ratio:.0f}:1 ratio)")
        elif ratio > 2:
            insights.append(f"THC-leaning ({ratio:.1f}:1 ratio)")
        elif ratio > 0.5:
            insights.append(f"Balanced THC:CBD ({ratio:.1f}:1 ratio)")
        else:
            insights.append(f"CBD-rich (1:{1/ratio:.1f} ratio)")
    elif thc_total > 0:
        insights.append("THC-dominant, minimal CBD")
    elif cbd_total > 0:
        insights.append("CBD-dominant, minimal THC")

    # Potency insights
    if thc_total > 25:
        insights.append("Very high potency")
    elif thc_total > 20:
        insights.append("High potency")
    elif thc_total > 15:
        insights.append("Moderate-high potency")
    elif thc_total > 10:
        insights.append("Moderate potency")

    # Minor cannabinoid insights
    if totals.cbn and totals.cbn > 0.005:  # >0.5%
        insights.append("Elevated CBN may promote sleepiness")

    if totals.cbg and totals.cbg > 0.01:  # >1%
        insights.append("Notable CBG presence")

    if totals.thcv and totals.thcv > 0.005:  # >0.5%
        insights.append("Contains THCV")

    if totals.cbdv and totals.cbdv > 0.005:  # >0.5%
        insights.append("Contains CBDV")

    return insights
