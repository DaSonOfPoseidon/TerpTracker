# Tests for app/api/routes.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.models.schemas import AnalyzeUrlResponse, Evidence, DataAvailability, Totals


# Patch cache_service and rate limiter before importing app
@pytest.fixture(autouse=True)
def _patch_infra():
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    mock_cache.check_rate_limit = AsyncMock(return_value=(True, 29))
    mock_cache.connect = AsyncMock()
    mock_cache.disconnect = AsyncMock()

    with patch("app.services.cache.cache_service", mock_cache), \
         patch("app.core.middleware.cache_service", mock_cache), \
         patch("app.api.routes.cache_service", mock_cache):
        from app.main import app
        yield app, mock_cache


@pytest.fixture
def client(_patch_infra):
    app, _ = _patch_infra
    return TestClient(app)


@pytest.fixture
def mock_cache(_patch_infra):
    _, cache = _patch_infra
    return cache


class TestVersionEndpoint:

    def test_get_version(self, client):
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "api" in data


class TestTerpeneEndpoints:

    def test_list_terpenes(self, client):
        resp = client.get("/api/terpenes")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 8
        keys = {t["key"] for t in data}
        assert "myrcene" in keys
        assert "limonene" in keys

    def test_get_terpene_info(self, client):
        resp = client.get("/api/terpenes/myrcene")
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == "myrcene"
        assert "effects" in data

    def test_get_unknown_terpene_404(self, client):
        resp = client.get("/api/terpenes/nonexistent")
        assert resp.status_code == 404


class TestAnalyzeUrlEndpoint:

    def _make_result(self):
        return AnalyzeUrlResponse(
            sources=["page"],
            terpenes={"myrcene": 0.5, "limonene": 0.3},
            totals=Totals(thc=0.20),
            category="BLUE",
            traditional_label="Classic Indica",
            summary="Test summary",
            strain_guess="Test Strain",
            evidence=Evidence(detection_method="page_scrape", url="https://example.com"),
            data_available=DataAvailability(has_terpenes=True, has_cannabinoids=True),
            cannabinoid_insights=["High potency"],
        )

    @patch("app.api.routes.StrainAnalyzer")
    def test_analyze_url_success(self, mock_analyzer_cls, client):
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_url = AsyncMock(return_value=self._make_result())
        mock_analyzer_cls.return_value = mock_analyzer

        resp = client.post("/api/analyze-url", json={"url": "https://example.com/strain"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "BLUE"
        assert data["strain_guess"] == "Test Strain"

    def test_analyze_url_cache_hit(self, client, mock_cache):
        mock_cache.get = AsyncMock(return_value={
            "sources": ["page"],
            "terpenes": {"myrcene": 0.5},
            "totals": {},
            "category": "BLUE",
            "traditional_label": "Classic Indica",
            "summary": "Cached",
            "strain_guess": "Cached Strain",
            "evidence": {"detection_method": "page_scrape"},
            "data_available": {"has_terpenes": True, "has_cannabinoids": False, "has_coa": False, "terpene_count": 1, "cannabinoid_count": 0},
            "cannabinoid_insights": [],
        })

        resp = client.post("/api/analyze-url", json={"url": "https://example.com/cached"})
        assert resp.status_code == 200
        assert resp.json()["strain_guess"] == "Cached Strain"

    @patch("app.api.routes.StrainAnalyzer")
    def test_analyze_url_value_error_404(self, mock_analyzer_cls, client):
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_url = AsyncMock(side_effect=ValueError("No data found"))
        mock_analyzer_cls.return_value = mock_analyzer

        resp = client.post("/api/analyze-url", json={"url": "https://example.com/empty"})
        assert resp.status_code == 404

    @patch("app.api.routes.StrainAnalyzer")
    def test_analyze_url_exception_500(self, mock_analyzer_cls, client):
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_url = AsyncMock(side_effect=RuntimeError("Unexpected"))
        mock_analyzer_cls.return_value = mock_analyzer

        resp = client.post("/api/analyze-url", json={"url": "https://example.com/error"})
        assert resp.status_code == 500

    def test_analyze_url_invalid_body(self, client):
        resp = client.post("/api/analyze-url", json={"url": "not-a-url"})
        assert resp.status_code == 422


class TestStrainSearchEndpoints:

    @patch("app.api.routes.profile_cache_service")
    def test_autocomplete(self, mock_cache, client):
        mock_cache.autocomplete_strains.return_value = [
            {"name": "blue dream", "category": "BLUE"},
            {"name": "blue cheese", "category": "PURPLE"},
        ]
        resp = client.get("/api/strains/autocomplete?q=blue")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "blue dream"

    def test_autocomplete_short_query(self, client):
        resp = client.get("/api/strains/autocomplete?q=b")
        assert resp.status_code == 422  # min_length=2

    @patch("app.api.routes.profile_cache_service")
    def test_search(self, mock_cache, client):
        mock_cache.search_strains.return_value = [
            {"name": "blue dream", "category": "BLUE", "match_score": 1.0, "match_type": "prefix"},
        ]
        resp = client.get("/api/strains/search?q=blue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "blue dream"

    @patch("app.api.routes.profile_cache_service")
    def test_analyze_strain_success(self, mock_cache, client):
        mock_cache.get_full_cached_result.return_value = {
            'strain_name': 'Blue Dream',
            'terpenes': {"myrcene": 0.5, "limonene": 0.3},
            'totals': Totals(thc=20.0),
            'category': 'BLUE',
            'source': 'database',
            'cached_at': '2025-01-01',
        }
        resp = client.post("/api/analyze-strain", json={"strain_name": "Blue Dream"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["strain_guess"] == "Blue Dream"
        assert data["category"] == "BLUE"
        assert "database" in data["sources"]

    @patch("app.api.routes.profile_cache_service")
    def test_analyze_strain_not_found(self, mock_cache, client):
        mock_cache.get_full_cached_result.return_value = None
        resp = client.post("/api/analyze-strain", json={"strain_name": "Nonexistent"})
        assert resp.status_code == 404

    @patch("app.api.routes.profile_cache_service")
    def test_analyze_strain_no_terpenes(self, mock_cache, client):
        mock_cache.get_full_cached_result.return_value = {
            'strain_name': 'Minimal Strain',
            'terpenes': {},
            'totals': Totals(thc=20.0),
            'category': None,
            'source': 'database',
            'cached_at': '2025-01-01',
        }
        resp = client.post("/api/analyze-strain", json={"strain_name": "Minimal Strain"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["strain_guess"] == "Minimal Strain"
