# Tests for search/autocomplete functionality in profile_cache.py

import pytest
from unittest.mock import patch, MagicMock
from app.services.profile_cache import ProfileCacheService


@pytest.fixture
def cache_service():
    return ProfileCacheService()


@pytest.fixture
def mock_db_profiles():
    profiles = [
        MagicMock(strain_normalized="blue dream", category="BLUE"),
        MagicMock(strain_normalized="blue cheese", category="PURPLE"),
        MagicMock(strain_normalized="blueberry", category="BLUE"),
        MagicMock(strain_normalized="og kush", category="YELLOW"),
        MagicMock(strain_normalized="bubba kush", category="BLUE"),
    ]
    return profiles


class TestAutocompleteStrains:

    def test_short_query_returns_empty(self, cache_service):
        assert cache_service.autocomplete_strains("b") == []

    @patch("app.services.profile_cache.SessionLocal")
    def test_prefix_matching(self, mock_session_cls, cache_service, mock_db_profiles):
        session = MagicMock()
        mock_session_cls.return_value = session
        # Filter to profiles starting with "blue"
        blue_profiles = [p for p in mock_db_profiles if p.strain_normalized.startswith("blue")]
        session.query.return_value.filter.return_value.limit.return_value.all.return_value = blue_profiles

        results = cache_service.autocomplete_strains("blue")
        assert len(results) == 3
        assert all(r["name"].startswith("blue") for r in results)
        assert all("category" in r for r in results)

    @patch("app.services.profile_cache.SessionLocal")
    def test_no_matches(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        results = cache_service.autocomplete_strains("zzz")
        assert results == []


class TestSearchStrains:

    def test_empty_query(self, cache_service):
        assert cache_service.search_strains("") == []

    @patch("app.services.profile_cache.SessionLocal")
    def test_prefix_matches_first(self, mock_session_cls, cache_service, mock_db_profiles):
        session = MagicMock()
        mock_session_cls.return_value = session
        blue_profiles = [p for p in mock_db_profiles if p.strain_normalized.startswith("blue")]
        session.query.return_value.filter.return_value.limit.return_value.all.return_value = blue_profiles
        session.query.return_value.all.return_value = mock_db_profiles

        results = cache_service.search_strains("blue")
        prefix_results = [r for r in results if r["match_type"] == "prefix"]
        assert len(prefix_results) >= 1
        assert all(r["match_score"] == 1.0 for r in prefix_results)

    @patch("app.services.profile_cache.SessionLocal")
    def test_fuzzy_matches_included(self, mock_session_cls, cache_service, mock_db_profiles):
        session = MagicMock()
        mock_session_cls.return_value = session
        # No prefix matches for "bleu"
        session.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        session.query.return_value.all.return_value = mock_db_profiles

        results = cache_service.search_strains("bleu dream")
        # Should find "blue dream" via fuzzy matching
        fuzzy = [r for r in results if r["match_type"] == "fuzzy"]
        assert len(fuzzy) > 0
        assert any(r["name"] == "blue dream" for r in fuzzy)
