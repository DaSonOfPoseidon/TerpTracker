# Shared test fixtures for TerpTracker backend tests

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.schemas import Totals, Evidence, DataAvailability, AnalyzeUrlResponse


@pytest.fixture
def sample_terpene_profile():
    return {
        "myrcene": 0.35,
        "limonene": 0.25,
        "caryophyllene": 0.15,
        "alpha_pinene": 0.08,
        "beta_pinene": 0.05,
        "humulene": 0.05,
        "linalool": 0.04,
        "terpinolene": 0.02,
        "ocimene": 0.01,
    }


@pytest.fixture
def sample_totals():
    return Totals(
        total_terpenes=0.021,
        thc=0.18,
        thca=0.22,
        cbd=0.001,
        cbda=0.002,
        cbn=0.001,
        cbg=0.005,
    )


@pytest.fixture
def sample_analysis_result(sample_terpene_profile, sample_totals):
    return AnalyzeUrlResponse(
        sources=["page", "database"],
        terpenes=sample_terpene_profile,
        totals=sample_totals,
        category="BLUE",
        traditional_label="Classic Indica",
        summary="Blue Dream's composition puts it in the BLUE category — expect myrcene-forward with an earthy, relaxing profile featuring myrcene and limonene. In traditional terms, this aligns with a classic indica experience.",
        strain_guess="Blue Dream",
        evidence=Evidence(detection_method="page_scrape", url="https://example.com/strain"),
        data_available=DataAvailability(
            has_terpenes=True,
            has_cannabinoids=True,
            has_coa=False,
            terpene_count=9,
            cannabinoid_count=5,
        ),
        cannabinoid_insights=["THC-dominant, minimal CBD", "High potency"],
    )


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.limit.return_value.all.return_value = []
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_cache_service():
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.check_rate_limit = AsyncMock(return_value=(True, 29))
    return cache
