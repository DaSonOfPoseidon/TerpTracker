# Tests for app/services/profile_cache.py

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.profile_cache import ProfileCacheService
from app.models.schemas import Totals


@pytest.fixture
def cache_service():
    return ProfileCacheService()


@pytest.fixture
def mock_profile():
    profile = MagicMock()
    profile.strain_normalized = "blue dream"
    profile.terp_vector = {"myrcene": 0.35, "limonene": 0.25}
    profile.totals = {"thc": 0.20, "thca": 0.22}
    profile.category = "BLUE"
    profile.provenance = {"source": "page"}
    profile.created_at = datetime(2025, 1, 1, 12, 0, 0)
    return profile


class TestGetCachedProfile:

    @patch("app.services.profile_cache.SessionLocal")
    def test_found(self, mock_session_cls, cache_service, mock_profile):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = mock_profile

        result = cache_service.get_cached_profile("Blue Dream")
        assert result is not None
        assert result["terpenes"] == {"myrcene": 0.35, "limonene": 0.25}
        assert result["category"] == "BLUE"
        assert result["source"] == "database"
        session.close.assert_called_once()

    @patch("app.services.profile_cache.SessionLocal")
    def test_not_found(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = cache_service.get_cached_profile("Nonexistent Strain")
        assert result is None
        session.close.assert_called_once()


class TestSaveProfile:

    @patch("app.services.profile_cache.SessionLocal")
    def test_save_new(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = cache_service.save_profile(
            strain_name="New Strain",
            terpenes={"myrcene": 0.5},
            totals=Totals(thc=0.20),
            category="BLUE",
            source="page",
        )
        assert result is True
        session.add.assert_called_once()
        session.commit.assert_called_once()

    @patch("app.services.profile_cache.SessionLocal")
    def test_update_existing(self, mock_session_cls, cache_service, mock_profile):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = mock_profile

        result = cache_service.save_profile(
            strain_name="Blue Dream",
            terpenes={"myrcene": 0.6},
            totals=Totals(thc=0.25),
            category="BLUE",
            source="coa",
        )
        assert result is True
        assert mock_profile.terp_vector == {"myrcene": 0.6}
        session.commit.assert_called_once()

    @patch("app.services.profile_cache.SessionLocal")
    def test_exception_rollback(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None
        session.commit.side_effect = Exception("DB error")

        result = cache_service.save_profile(
            strain_name="Bad Strain",
            terpenes={"myrcene": 0.5},
            totals=Totals(),
            category="BLUE",
            source="page",
        )
        assert result is False
        session.rollback.assert_called_once()


class TestGetCachedProfileWithAliases:

    @patch("app.services.profile_cache.SessionLocal")
    def test_direct_match_returned(self, mock_session_cls, cache_service, mock_profile):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = mock_profile

        result = cache_service.get_cached_profile_with_aliases("Blue Dream")
        assert result is not None
        assert result["category"] == "BLUE"

    @patch("app.services.profile_cache.SessionLocal")
    def test_alias_fallback(self, mock_session_cls, cache_service, mock_profile):
        session = MagicMock()
        mock_session_cls.return_value = session
        # First call (direct) returns None, second call (alias) returns profile
        session.query.return_value.filter.return_value.first.side_effect = [None, mock_profile]

        with patch.object(cache_service, "resolve_strain_aliases", return_value=["blue dream alt"]):
            result = cache_service.get_cached_profile_with_aliases("Blue Dream Alt")
            assert result is not None

    @patch("app.services.profile_cache.SessionLocal")
    def test_no_match_no_alias(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(cache_service, "resolve_strain_aliases", return_value=[]):
            result = cache_service.get_cached_profile_with_aliases("Nonexistent")
            assert result is None


class TestGetAllCachedStrains:

    @patch("app.services.profile_cache.SessionLocal")
    def test_returns_names(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        mock_rows = [MagicMock(strain_normalized="blue dream"), MagicMock(strain_normalized="og kush")]
        session.query.return_value.limit.return_value.all.return_value = mock_rows

        result = cache_service.get_all_cached_strains(limit=10)
        assert result == ["blue dream", "og kush"]
        session.close.assert_called_once()

    @patch("app.services.profile_cache.SessionLocal")
    def test_empty_db(self, mock_session_cls, cache_service):
        session = MagicMock()
        mock_session_cls.return_value = session
        session.query.return_value.limit.return_value.all.return_value = []

        result = cache_service.get_all_cached_strains()
        assert result == []
