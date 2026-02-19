# Effects engine: pure-function analysis of terpene/cannabinoid profiles
# to generate detailed experience predictions.

from typing import Dict, List, Optional
from app.models.schemas import Totals

# Terpene effect profiles — body_weight is 0 (cerebral) to 1 (body)
TERPENE_EFFECTS = {
    "myrcene": {
        "body_weight": 0.85,
        "primary_effects": ["Relaxing", "Sedating", "Muscle relaxant", "Pain relief"],
        "best_for": ["Nighttime", "Sleep", "Pain relief", "Relaxation"],
        "avoid_for": ["Daytime productivity", "Social events"],
        "negatives": ["Drowsiness", "Couch-lock at high levels"],
        "onset_modifier": 0.0,  # baseline
        "duration_modifier": 0.1,  # slightly extends
    },
    "limonene": {
        "body_weight": 0.2,
        "primary_effects": ["Uplifting", "Mood enhancement", "Stress relief", "Anti-anxiety"],
        "best_for": ["Daytime", "Social events", "Creative work", "Mood boost"],
        "avoid_for": ["Bedtime (may be too stimulating)"],
        "negatives": ["Heartburn in sensitive individuals"],
        "onset_modifier": -0.05,  # slightly faster
        "duration_modifier": -0.05,
    },
    "caryophyllene": {
        "body_weight": 0.6,
        "primary_effects": ["Anti-inflammatory", "Pain relief", "Stress reduction", "Calming"],
        "best_for": ["Pain management", "Stress relief", "Evening wind-down"],
        "avoid_for": [],
        "negatives": ["Dry mouth"],
        "onset_modifier": 0.0,
        "duration_modifier": 0.05,
    },
    "alpha_pinene": {
        "body_weight": 0.15,
        "primary_effects": ["Alertness", "Focus", "Memory retention", "Bronchodilator"],
        "best_for": ["Daytime", "Studying", "Hiking", "Creative focus"],
        "avoid_for": ["Sleep"],
        "negatives": ["May increase anxiety in sensitive users"],
        "onset_modifier": -0.05,
        "duration_modifier": -0.1,
    },
    "beta_pinene": {
        "body_weight": 0.15,
        "primary_effects": ["Alertness", "Focus", "Memory retention"],
        "best_for": ["Daytime", "Studying", "Focus work"],
        "avoid_for": ["Sleep"],
        "negatives": [],
        "onset_modifier": -0.05,
        "duration_modifier": -0.1,
    },
    "terpinolene": {
        "body_weight": 0.3,
        "primary_effects": ["Uplifting", "Creative", "Energizing", "Antioxidant"],
        "best_for": ["Daytime", "Creative work", "Social events", "Exercise"],
        "avoid_for": ["Anxiety-prone individuals", "Sleep"],
        "negatives": ["Overstimulation if sensitive"],
        "onset_modifier": -0.1,
        "duration_modifier": -0.15,
    },
    "humulene": {
        "body_weight": 0.5,
        "primary_effects": ["Anti-inflammatory", "Appetite suppressant", "Pain relief"],
        "best_for": ["Weight management", "Pain relief", "Evening"],
        "avoid_for": [],
        "negatives": [],
        "onset_modifier": 0.0,
        "duration_modifier": 0.0,
    },
    "linalool": {
        "body_weight": 0.75,
        "primary_effects": ["Calming", "Sedative", "Anti-anxiety", "Anti-convulsant"],
        "best_for": ["Nighttime", "Anxiety relief", "Sleep", "Relaxation"],
        "avoid_for": ["Needing to stay alert"],
        "negatives": ["Drowsiness"],
        "onset_modifier": 0.05,
        "duration_modifier": 0.1,
    },
    "ocimene": {
        "body_weight": 0.25,
        "primary_effects": ["Uplifting", "Anti-inflammatory", "Antifungal"],
        "best_for": ["Daytime", "Light activity"],
        "avoid_for": [],
        "negatives": [],
        "onset_modifier": 0.0,
        "duration_modifier": -0.05,
    },
}

# Interaction rules: ratio-based terpene synergies
INTERACTION_RULES = [
    {
        "condition": lambda t: t.get("limonene", 0) > 0.15 and t.get("myrcene", 0) > 0.20,
        "description": "Limonene tempers myrcene's heavy sedation, creating a more balanced relaxation with uplifted mood",
    },
    {
        "condition": lambda t: t.get("myrcene", 0) > 0.25 and t.get("caryophyllene", 0) > 0.15,
        "description": "Myrcene and caryophyllene synergize for deep body relaxation and potent pain relief",
    },
    {
        "condition": lambda t: t.get("alpha_pinene", 0) + t.get("beta_pinene", 0) > 0.15 and t.get("myrcene", 0) > 0.20,
        "description": "Pinene may counteract some of myrcene's memory-clouding effects while preserving relaxation",
    },
    {
        "condition": lambda t: t.get("linalool", 0) > 0.05 and t.get("myrcene", 0) > 0.20,
        "description": "Linalool and myrcene together amplify sedative effects — strong candidate for sleep aid",
    },
    {
        "condition": lambda t: t.get("limonene", 0) > 0.15 and t.get("caryophyllene", 0) > 0.15,
        "description": "Limonene and caryophyllene together create a spicy-citrus stress relief combo",
    },
    {
        "condition": lambda t: t.get("terpinolene", 0) > 0.15 and t.get("ocimene", 0) > 0.05,
        "description": "Terpinolene and ocimene create a distinctly uplifting, energetic experience characteristic of classic sativas",
    },
    {
        "condition": lambda t: t.get("caryophyllene", 0) > 0.15 and t.get("humulene", 0) > 0.05,
        "description": "Caryophyllene and humulene (both found in hops) work together for enhanced anti-inflammatory effects",
    },
]


def generate_effects_profile(
    terpenes: Dict[str, float],
    totals: Optional[Totals] = None,
    category: Optional[str] = None,
) -> dict:
    """
    Generate a detailed effects profile from terpene and cannabinoid data.
    Pure function — no side effects or external calls.

    Args:
        terpenes: Normalized terpene profile (fractions summing to ~1.0)
        totals: Cannabinoid totals (percentage scale)
        category: SDP category for additional context

    Returns:
        Dict with all effects analysis fields
    """
    if not terpenes:
        return {}

    totals = totals or Totals()

    # Normalize terpenes to fractions if needed
    total_terp = sum(terpenes.values())
    if total_terp > 0:
        norm_terps = {k: v / total_terp for k, v in terpenes.items()}
    else:
        return {}

    # Calculate body/mind balance (0 = pure body, 1 = pure mind)
    body_mind_balance = _calc_body_mind_balance(norm_terps)

    # Calculate daytime suitability (0 = nighttime, 1 = daytime)
    daytime_score = _calc_daytime_score(norm_terps, body_mind_balance)

    # Determine onset, peak, and duration
    onset, peak, duration = _calc_timeline(norm_terps, totals)

    # Intensity estimate based on THC + terpene content
    intensity_estimate = _calc_intensity(totals)

    # Collect best contexts and potential negatives
    best_contexts = _collect_best_contexts(norm_terps)
    potential_negatives = _collect_negatives(norm_terps, totals)

    # Find terpene interactions
    terpene_interactions = _find_interactions(norm_terps)

    # Generate overall character description
    overall_character = _describe_character(norm_terps, category, body_mind_balance, daytime_score)

    # Generate narrative experience summary
    experience_summary = _generate_experience_summary(
        norm_terps, totals, category, body_mind_balance, daytime_score, intensity_estimate
    )

    return {
        "overall_character": overall_character,
        "onset": onset,
        "peak": peak,
        "duration": duration,
        "best_contexts": best_contexts,
        "potential_negatives": potential_negatives,
        "terpene_interactions": terpene_interactions,
        "experience_summary": experience_summary,
        "intensity_estimate": intensity_estimate,
        "daytime_score": round(daytime_score, 2),
        "body_mind_balance": round(body_mind_balance, 2),
    }


def _calc_body_mind_balance(terps: Dict[str, float]) -> float:
    # Weighted average of body_weight (inverted: 0=body, 1=mind)
    total_weight = 0.0
    total_value = 0.0
    for name, fraction in terps.items():
        effect = TERPENE_EFFECTS.get(name)
        if effect and fraction > 0:
            mind_weight = 1.0 - effect["body_weight"]
            total_value += mind_weight * fraction
            total_weight += fraction
    if total_weight > 0:
        return total_value / total_weight
    return 0.5  # default balanced


def _calc_daytime_score(terps: Dict[str, float], body_mind: float) -> float:
    # Daytime terpenes boost score, nighttime terpenes lower it
    daytime_terps = {"terpinolene", "alpha_pinene", "beta_pinene", "limonene", "ocimene"}
    nighttime_terps = {"myrcene", "linalool"}

    daytime_frac = sum(terps.get(t, 0) for t in daytime_terps)
    nighttime_frac = sum(terps.get(t, 0) for t in nighttime_terps)

    # Base from body_mind, adjusted by terpene fractions
    score = body_mind * 0.6 + daytime_frac * 0.8 - nighttime_frac * 0.4
    return max(0.0, min(1.0, score))


def _calc_timeline(terps: Dict[str, float], totals: Totals) -> tuple:
    # Base timeline in minutes
    base_onset = 10
    base_peak = 30
    base_duration = 120

    onset_mod = 0.0
    duration_mod = 0.0
    for name, fraction in terps.items():
        effect = TERPENE_EFFECTS.get(name)
        if effect and fraction > 0.05:
            onset_mod += effect["onset_modifier"] * fraction * 10
            duration_mod += effect["duration_modifier"] * fraction * 10

    # THC potency extends duration
    thc_total = (getattr(totals, 'thc', 0) or 0) + (getattr(totals, 'thca', 0) or 0) * 0.877
    if thc_total > 25:
        duration_mod += 30
    elif thc_total > 20:
        duration_mod += 15

    # CBD can moderate onset
    cbd_total = (getattr(totals, 'cbd', 0) or 0) + (getattr(totals, 'cbda', 0) or 0) * 0.877
    if cbd_total > 5:
        onset_mod += 5  # slightly slower onset

    onset = f"{max(5, int(base_onset + onset_mod))}-{max(10, int(base_onset + onset_mod + 10))} min"
    peak = f"{max(15, int(base_peak + onset_mod))}-{max(30, int(base_peak + onset_mod + 20))} min"
    duration = f"{max(60, int(base_duration + duration_mod))}-{max(90, int(base_duration + duration_mod + 60))} min"

    return onset, peak, duration


def _calc_intensity(totals: Totals) -> str:
    thc_total = (getattr(totals, 'thc', 0) or 0) + (getattr(totals, 'thca', 0) or 0) * 0.877
    cbd_total = (getattr(totals, 'cbd', 0) or 0) + (getattr(totals, 'cbda', 0) or 0) * 0.877

    # CBD buffers intensity
    if cbd_total > 5 and thc_total > 0:
        thc_total *= 0.8  # reduce effective intensity

    if thc_total > 28:
        return "Very High"
    elif thc_total > 22:
        return "High"
    elif thc_total > 15:
        return "Moderate-High"
    elif thc_total > 10:
        return "Moderate"
    elif thc_total > 0:
        return "Low-Moderate"
    else:
        return "Unknown"


def _collect_best_contexts(terps: Dict[str, float]) -> List[str]:
    contexts = {}  # context -> max weight
    for name, fraction in terps.items():
        effect = TERPENE_EFFECTS.get(name)
        if effect and fraction > 0.05:
            for ctx in effect["best_for"]:
                if ctx not in contexts or fraction > contexts[ctx]:
                    contexts[ctx] = fraction

    # Sort by weight, return top contexts
    sorted_contexts = sorted(contexts.items(), key=lambda x: x[1], reverse=True)
    return [ctx for ctx, _ in sorted_contexts[:6]]


def _collect_negatives(terps: Dict[str, float], totals: Totals) -> List[str]:
    negatives = set()
    for name, fraction in terps.items():
        effect = TERPENE_EFFECTS.get(name)
        if effect and fraction > 0.10:
            for neg in effect["negatives"]:
                negatives.add(neg)

    # THC-related warnings
    thc_total = (getattr(totals, 'thc', 0) or 0) + (getattr(totals, 'thca', 0) or 0) * 0.877
    if thc_total > 25:
        negatives.add("High THC may cause anxiety or paranoia in sensitive users")
    if thc_total > 30:
        negatives.add("Very high THC — start with a low dose")

    return list(negatives)


def _find_interactions(terps: Dict[str, float]) -> List[str]:
    interactions = []
    for rule in INTERACTION_RULES:
        if rule["condition"](terps):
            interactions.append(rule["description"])
    return interactions


def _describe_character(
    terps: Dict[str, float],
    category: Optional[str],
    body_mind: float,
    daytime: float,
) -> str:
    # Pick the primary character
    if body_mind < 0.3:
        character = "deeply body-focused"
    elif body_mind < 0.45:
        character = "body-leaning"
    elif body_mind < 0.55:
        character = "balanced body and mind"
    elif body_mind < 0.7:
        character = "mind-leaning"
    else:
        character = "cerebral and heady"

    if daytime > 0.7:
        timing = "best suited for daytime use"
    elif daytime > 0.4:
        timing = "versatile for any time of day"
    else:
        timing = "best suited for evening or nighttime"

    return f"A {character} experience, {timing}"


def _generate_experience_summary(
    terps: Dict[str, float],
    totals: Totals,
    category: Optional[str],
    body_mind: float,
    daytime: float,
    intensity: str,
) -> str:
    # Build a narrative summary
    sorted_terps = sorted(terps.items(), key=lambda x: x[1], reverse=True)
    top = sorted_terps[0] if sorted_terps else ("unknown", 0)
    top_name = top[0].replace("_", " ")

    parts = [f"Dominated by {top_name}"]

    if len(sorted_terps) >= 2:
        second_name = sorted_terps[1][0].replace("_", " ")
        parts[0] += f" with supporting {second_name}"

    if body_mind < 0.35:
        parts.append("expect a heavy, body-centered sensation that builds into deep physical relaxation")
    elif body_mind < 0.5:
        parts.append("expect a warm body buzz with gentle mental calm")
    elif body_mind > 0.65:
        parts.append("expect an uplifting, cerebral experience with creative energy")
    else:
        parts.append("expect a well-rounded experience balancing mind and body")

    thc_total = (getattr(totals, 'thc', 0) or 0) + (getattr(totals, 'thca', 0) or 0) * 0.877
    cbd_total = (getattr(totals, 'cbd', 0) or 0) + (getattr(totals, 'cbda', 0) or 0) * 0.877

    if cbd_total > 5 and thc_total > 0:
        parts.append("CBD presence may buffer intensity and reduce anxiety")
    elif thc_total > 25:
        parts.append("high THC suggests a potent experience — pace yourself")

    return ". ".join(parts) + "."
