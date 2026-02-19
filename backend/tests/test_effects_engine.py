# Tests for app/services/effects_engine.py

import pytest
from app.services.effects_engine import generate_effects_profile
from app.models.schemas import Totals


class TestGenerateEffectsProfile:

    def test_myrcene_dominant_body_focused(self):
        terpenes = {"myrcene": 0.6, "limonene": 0.2, "caryophyllene": 0.2}
        result = generate_effects_profile(terpenes, Totals(thc=20.0), "BLUE")
        assert result["body_mind_balance"] < 0.4  # body-leaning
        assert result["daytime_score"] < 0.5  # nighttime-leaning
        assert "body" in result["overall_character"].lower()

    def test_limonene_dominant_uplifting(self):
        terpenes = {"limonene": 0.6, "caryophyllene": 0.2, "myrcene": 0.2}
        result = generate_effects_profile(terpenes, Totals(thc=18.0), "YELLOW")
        assert result["body_mind_balance"] > 0.4  # mind-leaning
        assert result["daytime_score"] > 0.3

    def test_balanced_profile(self):
        terpenes = {"myrcene": 0.33, "limonene": 0.33, "caryophyllene": 0.34}
        result = generate_effects_profile(terpenes, Totals(thc=18.0), "RED")
        assert 0.3 < result["body_mind_balance"] < 0.7

    def test_terpinolene_daytime(self):
        terpenes = {"terpinolene": 0.5, "myrcene": 0.3, "ocimene": 0.2}
        result = generate_effects_profile(terpenes, Totals(thc=20.0), "ORANGE")
        assert result["daytime_score"] > 0.4
        assert result["body_mind_balance"] > 0.4  # cerebral

    def test_interaction_rules_myrcene_caryophyllene(self):
        terpenes = {"myrcene": 0.5, "caryophyllene": 0.3, "limonene": 0.2}
        result = generate_effects_profile(terpenes, Totals(), None)
        assert len(result["terpene_interactions"]) > 0
        assert any("myrcene" in i.lower() or "caryophyllene" in i.lower() for i in result["terpene_interactions"])

    def test_cbd_buffering(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.5}
        result_no_cbd = generate_effects_profile(terpenes, Totals(thc=25.0), "BLUE")
        result_cbd = generate_effects_profile(terpenes, Totals(thc=25.0, cbd=10.0), "BLUE")
        # CBD should buffer intensity
        assert result_cbd["intensity_estimate"] != "Very High" or result_no_cbd["intensity_estimate"] == "Very High"

    def test_high_thc_warning(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.5}
        result = generate_effects_profile(terpenes, Totals(thc=30.0), "BLUE")
        assert any("thc" in neg.lower() or "dose" in neg.lower() for neg in result["potential_negatives"])

    def test_empty_profile(self):
        result = generate_effects_profile({}, Totals(), None)
        assert result == {}

    def test_intensity_tiers(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.5}
        assert generate_effects_profile(terpenes, Totals(thc=30.0))["intensity_estimate"] == "Very High"
        assert generate_effects_profile(terpenes, Totals(thc=24.0))["intensity_estimate"] == "High"
        assert generate_effects_profile(terpenes, Totals(thc=18.0))["intensity_estimate"] == "Moderate-High"
        assert generate_effects_profile(terpenes, Totals(thc=12.0))["intensity_estimate"] == "Moderate"
        assert generate_effects_profile(terpenes, Totals(thc=5.0))["intensity_estimate"] == "Low-Moderate"

    def test_best_contexts_populated(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.3, "caryophyllene": 0.2}
        result = generate_effects_profile(terpenes, Totals(), None)
        assert len(result["best_contexts"]) > 0

    def test_experience_summary_present(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.3, "caryophyllene": 0.2}
        result = generate_effects_profile(terpenes, Totals(thc=20.0), "BLUE")
        assert len(result["experience_summary"]) > 20  # non-trivial summary

    def test_timeline_fields_present(self):
        terpenes = {"myrcene": 0.5, "limonene": 0.5}
        result = generate_effects_profile(terpenes, Totals(thc=20.0), "BLUE")
        assert "min" in result["onset"]
        assert "min" in result["peak"]
        assert "min" in result["duration"]
