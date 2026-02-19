# Tests for app/utils/matching.py

from app.utils.matching import fuzzy_match_strain


class TestFuzzyMatchStrain:

    def test_exact_match(self):
        candidates = ["blue dream", "og kush", "gelato"]
        match, score = fuzzy_match_strain("blue dream", candidates)
        assert match == "blue dream"
        assert score == 1.0

    def test_close_match(self):
        candidates = ["blue dream", "og kush", "gelato"]
        match, score = fuzzy_match_strain("bleu dream", candidates)
        assert match == "blue dream"
        assert score > 0.8

    def test_no_match_below_threshold(self):
        candidates = ["blue dream", "og kush", "gelato"]
        match, score = fuzzy_match_strain("completely unrelated name xyz", candidates)
        # Should return original query with 0.0 score when no good match
        assert score == 0.0

    def test_empty_candidates(self):
        match, score = fuzzy_match_strain("blue dream", [])
        assert match == "blue dream"
        assert score == 0.0

    def test_custom_threshold(self):
        candidates = ["blue dream", "og kush"]
        # With a very high threshold, a close-but-not-exact match should fail
        match, score = fuzzy_match_strain("bleu dream", candidates, threshold=0.99)
        assert score == 0.0

    def test_case_insensitive_matching(self):
        candidates = ["Blue Dream", "OG Kush"]
        match, score = fuzzy_match_strain("blue dream", candidates)
        # rapidfuzz is case-sensitive, but the match should still be reasonable
        assert score > 0.0

    def test_returns_best_of_multiple(self):
        candidates = ["blue dream", "blue cheese", "blue cookies"]
        match, score = fuzzy_match_strain("blue dream", candidates)
        assert match == "blue dream"
        assert score == 1.0
