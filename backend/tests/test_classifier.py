"""
Tests for terpene classifier.
"""

import pytest
from app.services.classifier import (
    classify_terpene_profile,
    normalize_terpene_profile,
    generate_summary,
    get_traditional_label,
    TRADITIONAL_LABELS,
)

class TestNormalization:
    """Test terpene profile normalization."""

    def test_normalize_basic(self):
        """Test basic normalization to sum to 1.0"""
        profile = {"myrcene": 0.5, "limonene": 0.3, "caryophyllene": 0.2}
        normalized = normalize_terpene_profile(profile)

        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.001

    def test_normalize_alternative_names(self):
        """Test normalization handles alternative terpene names"""
        profile = {"beta_myrcene": 0.5, "d-limonene": 0.3, "β-caryophyllene": 0.2}
        normalized = normalize_terpene_profile(profile)

        assert "myrcene" in normalized
        assert "limonene" in normalized
        assert "caryophyllene" in normalized

    def test_normalize_filters_zeros(self):
        """Test that zero values are filtered out"""
        profile = {"myrcene": 0.5, "limonene": 0.0, "caryophyllene": 0.5}
        normalized = normalize_terpene_profile(profile)

        assert "limonene" not in normalized


class TestClassification:
    """Test SDP category classification."""

    def test_classify_blue_myrcene_dominant(self):
        """Test BLUE classification for myrcene-dominant profile"""
        profile = {"myrcene": 0.6, "limonene": 0.2, "caryophyllene": 0.2}
        category = classify_terpene_profile(profile)
        assert category == "BLUE"

    def test_classify_yellow_limonene_dominant(self):
        """Test YELLOW classification for limonene-dominant profile"""
        profile = {"limonene": 0.6, "myrcene": 0.2, "caryophyllene": 0.2}
        category = classify_terpene_profile(profile)
        assert category == "YELLOW"

    def test_classify_purple_caryophyllene_low_pinene(self):
        """Test PURPLE classification for caryophyllene-dominant with low pinene"""
        profile = {
            "caryophyllene": 0.5,
            "limonene": 0.3,
            "myrcene": 0.15,
            "alpha_pinene": 0.05
        }
        category = classify_terpene_profile(profile)
        assert category == "PURPLE"

    def test_classify_green_pinene_dominant(self):
        """Test GREEN classification for pinene-dominant profile"""
        profile = {
            "alpha_pinene": 0.3,
            "beta_pinene": 0.2,
            "myrcene": 0.3,
            "caryophyllene": 0.2
        }
        category = classify_terpene_profile(profile)
        assert category == "GREEN"

    def test_classify_orange_terpinolene_dominant(self):
        """Test ORANGE classification for terpinolene-dominant profile"""
        profile = {
            "terpinolene": 0.5,
            "myrcene": 0.3,
            "ocimene": 0.2
        }
        category = classify_terpene_profile(profile)
        assert category == "ORANGE"

    def test_classify_red_balanced(self):
        """Test RED classification for balanced myrcene-limonene-caryophyllene"""
        profile = {
            "myrcene": 0.33,
            "limonene": 0.33,
            "caryophyllene": 0.34,
            "pinene": 0.0
        }
        category = classify_terpene_profile(profile)
        assert category == "RED"

    def test_classify_empty_profile_fallback(self):
        """Test that empty profile returns BLUE as fallback"""
        profile = {}
        category = classify_terpene_profile(profile)
        assert category == "BLUE"


class TestSummaryGeneration:
    """Test summary text generation."""

    def test_generate_summary_includes_strain_name(self):
        """Test that summary includes the strain name"""
        summary = generate_summary(
            "Blue Dream",
            "BLUE",
            {"myrcene": 0.5, "limonene": 0.3, "caryophyllene": 0.2}
        )
        assert "Blue Dream" in summary

    def test_generate_summary_includes_category(self):
        """Test that summary includes the category"""
        summary = generate_summary(
            "Test Strain",
            "YELLOW",
            {"limonene": 0.6, "myrcene": 0.4}
        )
        assert "YELLOW" in summary

    def test_generate_summary_includes_top_terpenes(self):
        """Test that summary mentions top terpenes"""
        summary = generate_summary(
            "Test Strain",
            "BLUE",
            {"myrcene": 0.5, "limonene": 0.3, "caryophyllene": 0.2}
        )
        # Should mention at least some terpene names
        assert "myrcene" in summary.lower() or "limonene" in summary.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_values(self):
        """Test handling of very small terpene percentages"""
        profile = {
            "myrcene": 0.001,
            "limonene": 0.001,
            "caryophyllene": 0.001
        }
        category = classify_terpene_profile(profile)
        assert category in ["BLUE", "YELLOW", "PURPLE", "GREEN", "ORANGE", "RED"]

    def test_unnormalized_percentages(self):
        """Test that classifier handles percentages that don't sum to 1.0"""
        profile = {
            "myrcene": 1.5,  # 150%
            "limonene": 0.8,
            "caryophyllene": 0.5
        }
        category = classify_terpene_profile(profile)
        assert category in ["BLUE", "YELLOW", "PURPLE", "GREEN", "ORANGE", "RED"]


class TestTraditionalLabels:
    """Test SDP 'Beyond Indica & Sativa' traditional label mappings."""

    def test_traditional_labels_dict_has_all_categories(self):
        """All 6 SDP categories have a traditional label."""
        for cat in ["BLUE", "YELLOW", "PURPLE", "GREEN", "ORANGE", "RED"]:
            assert cat in TRADITIONAL_LABELS

    def test_traditional_labels_values(self):
        """Labels match SDP research findings."""
        assert TRADITIONAL_LABELS["ORANGE"] == "Sativa"
        assert TRADITIONAL_LABELS["YELLOW"] == "Modern Indica"
        assert TRADITIONAL_LABELS["PURPLE"] == "Modern Indica"
        assert TRADITIONAL_LABELS["GREEN"] == "Classic Indica"
        assert TRADITIONAL_LABELS["BLUE"] == "Classic Indica"
        assert TRADITIONAL_LABELS["RED"] == "Hybrid"

    def test_get_traditional_label_valid(self):
        """get_traditional_label returns correct label for known categories."""
        assert get_traditional_label("ORANGE") == "Sativa"
        assert get_traditional_label("RED") == "Hybrid"
        assert get_traditional_label("BLUE") == "Classic Indica"

    def test_get_traditional_label_unknown(self):
        """get_traditional_label falls back to 'Hybrid' for unknown categories."""
        assert get_traditional_label("UNKNOWN") == "Hybrid"
        assert get_traditional_label("") == "Hybrid"

    def test_summary_includes_traditional_label(self):
        """generate_summary mentions the traditional label."""
        summary = generate_summary(
            "Jack Herer",
            "ORANGE",
            {"terpinolene": 0.5, "myrcene": 0.3, "ocimene": 0.2}
        )
        assert "sativa" in summary.lower()

    def test_summary_traditional_label_for_each_category(self):
        """Each category's summary includes the appropriate traditional term."""
        test_cases = {
            "BLUE": ("myrcene", "classic indica"),
            "YELLOW": ("limonene", "modern indica"),
            "PURPLE": ("caryophyllene", "modern indica"),
            "GREEN": ("alpha_pinene", "classic indica"),
            "ORANGE": ("terpinolene", "sativa"),
            "RED": ("myrcene", "hybrid"),
        }
        for category, (terp, expected_label) in test_cases.items():
            summary = generate_summary(
                "Test Strain",
                category,
                {terp: 0.5, "limonene": 0.3}
            )
            assert expected_label in summary.lower(), f"{category} summary should contain '{expected_label}'"
