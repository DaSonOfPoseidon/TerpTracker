# Tests for app/services/analyzer.py

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.analyzer import StrainAnalyzer
from app.models.schemas import Totals, ScrapedData, StrainAPIData


@pytest.fixture
def analyzer():
    return StrainAnalyzer()


@pytest.fixture
def mock_scraped():
    return ScrapedData(
        strain_name="Blue Dream",
        terpenes={"myrcene": 0.35, "limonene": 0.25},
        totals=Totals(thc=20.0, thca=22.0),
        coa_links=[],
        html_hash="abc123",
    )


@pytest.fixture
def mock_scraped_minimal():
    return ScrapedData(
        strain_name="Unknown Strain",
        terpenes={},
        totals=Totals(),
        coa_links=[],
        html_hash="def456",
    )


def run_async(coro):
    return asyncio.run(coro)


class TestIsDataComplete:

    def test_complete_with_enough_terpenes_and_cannabinoids(self, analyzer):
        terpenes = {f"t{i}": 0.1 for i in range(6)}
        totals = Totals(thc=20.0)
        assert analyzer.is_data_complete(terpenes, totals) is True

    def test_incomplete_few_terpenes(self, analyzer):
        terpenes = {"myrcene": 0.5}
        totals = Totals(thc=20.0)
        assert analyzer.is_data_complete(terpenes, totals) is False

    def test_incomplete_no_cannabinoids(self, analyzer):
        terpenes = {f"t{i}": 0.1 for i in range(6)}
        totals = Totals()
        assert analyzer.is_data_complete(terpenes, totals) is False


class TestAnalyzeUrl:

    @patch("app.db.base.SessionLocal")
    @patch("app.services.analyzer.scrape_url")
    @patch("app.services.analyzer.profile_cache_service")
    def test_saves_profile_for_db_only_results(self, mock_cache, mock_scrape, mock_session_cls, analyzer, mock_scraped_minimal):
        # Page returns nothing, but DB has data
        mock_scrape.return_value = mock_scraped_minimal
        mock_cache.get_cached_profile_with_aliases.return_value = {
            'terpenes': {"myrcene": 0.4, "limonene": 0.3, "caryophyllene": 0.2, "pinene": 0.05, "humulene": 0.05},
            'totals': Totals(thc=20.0),
            'category': 'BLUE',
            'cached_at': '2025-01-01',
        }

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        result = run_async(analyzer.analyze_url("https://example.com"))

        assert result.category is not None
        # Profile should be saved since we have terpenes + category + strain_name
        mock_cache.save_profile.assert_called_once()

    @patch("app.db.base.SessionLocal")
    @patch("app.services.analyzer.scrape_url")
    @patch("app.services.analyzer.profile_cache_service")
    def test_uses_alias_resolution(self, mock_cache, mock_scrape, mock_session_cls, analyzer, mock_scraped):
        mock_scrape.return_value = mock_scraped
        mock_cache.get_cached_profile_with_aliases.return_value = None
        mock_session_cls.return_value = MagicMock()

        result = run_async(analyzer.analyze_url("https://example.com"))

        # Should use get_cached_profile_with_aliases, not get_cached_profile
        mock_cache.get_cached_profile_with_aliases.assert_called_once_with("Blue Dream")

    @patch("app.db.base.SessionLocal")
    @patch("app.services.analyzer.scrape_url")
    @patch("app.services.analyzer.profile_cache_service")
    def test_extraction_recorded(self, mock_cache, mock_scrape, mock_session_cls, analyzer, mock_scraped):
        mock_scrape.return_value = mock_scraped
        mock_cache.get_cached_profile_with_aliases.return_value = None

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        result = run_async(analyzer.analyze_url("https://example.com"))

        # Extraction should be recorded via SessionLocal
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch("app.db.base.SessionLocal")
    @patch("app.services.analyzer.scrape_url")
    @patch("app.services.analyzer.profile_cache_service")
    def test_extraction_failure_doesnt_break_flow(self, mock_cache, mock_scrape, mock_session_cls, analyzer, mock_scraped):
        mock_scrape.return_value = mock_scraped
        mock_cache.get_cached_profile_with_aliases.return_value = None

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB down")

        # Should not raise — extraction recording is fire-and-forget
        result = run_async(analyzer.analyze_url("https://example.com"))

        assert result is not None
        assert result.strain_guess == "Blue Dream"

    @patch("app.db.base.SessionLocal")
    @patch("app.services.analyzer.scrape_url")
    @patch("app.services.analyzer.profile_cache_service")
    def test_primary_source_priority(self, mock_cache, mock_scrape, mock_session_cls, analyzer, mock_scraped):
        mock_scrape.return_value = mock_scraped
        mock_cache.get_cached_profile_with_aliases.return_value = {
            'terpenes': {"caryophyllene": 0.3},
            'totals': Totals(cbg=0.01),
            'category': 'PURPLE',
            'cached_at': '2025-01-01',
        }
        mock_session_cls.return_value = MagicMock()

        result = run_async(analyzer.analyze_url("https://example.com"))

        # page source should be primary since page data was found
        call_args = mock_cache.save_profile.call_args
        assert call_args.kwargs.get('source') == 'page' or (call_args[1] and call_args[1].get('source') == 'page')
