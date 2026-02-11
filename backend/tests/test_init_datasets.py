"""
Tests for dataset initialization and parsers.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.data.init_datasets import (
    safe_float,
    is_dataset_initialized,
    mark_dataset_initialized,
    parse_phytochem_csv,
    parse_cannlytics_state_csv,
    parse_openthc_varieties,
    MARKERS,
    LEGACY_MARKER,
    DATASETS_DIR,
)
from app.services.classifier import classify_terpene_profile, normalize_terpene_profile


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# safe_float tests
# ---------------------------------------------------------------------------

class TestSafeFloat:

    def test_valid_float(self):
        assert safe_float("1.23") == 1.23

    def test_valid_int_string(self):
        assert safe_float("5") == 5.0

    def test_small_positive(self):
        assert safe_float("0.001") == 0.001

    def test_zero_returns_none(self):
        assert safe_float("0") is None
        assert safe_float("0.0") is None

    def test_negative_returns_none(self):
        assert safe_float("-1.5") is None

    def test_empty_string_returns_none(self):
        assert safe_float("") is None

    def test_none_returns_none(self):
        assert safe_float(None) is None

    def test_nan_returns_none(self):
        assert safe_float("nan") is None
        assert safe_float("NaN") is None

    def test_na_returns_none(self):
        assert safe_float("N/A") is None
        assert safe_float("n/a") is None

    def test_nd_returns_none(self):
        assert safe_float("ND") is None
        assert safe_float("nd") is None

    def test_loq_returns_none(self):
        assert safe_float("<LOQ") is None
        assert safe_float("<loq") is None

    def test_none_value_returns_none(self):
        assert safe_float("none") is None
        assert safe_float("None") is None

    def test_null_returns_none(self):
        assert safe_float("null") is None

    def test_garbage_returns_none(self):
        assert safe_float("abc") is None
        assert safe_float("--") is None

    def test_whitespace_stripped(self):
        assert safe_float("  1.5  ") == 1.5

    def test_numeric_input(self):
        assert safe_float(3.14) == 3.14
        assert safe_float(42) == 42.0


# ---------------------------------------------------------------------------
# Per-dataset marker tests
# ---------------------------------------------------------------------------

class TestDatasetMarkers:

    def test_is_dataset_initialized_false_when_no_marker(self, tmp_path):
        with patch.dict('app.data.init_datasets.MARKERS', {'test_ds': tmp_path / ".init_test"}):
            assert is_dataset_initialized('test_ds') is False

    def test_is_dataset_initialized_true_when_marker_exists(self, tmp_path):
        marker = tmp_path / ".init_test"
        marker.touch()
        with patch.dict('app.data.init_datasets.MARKERS', {'test_ds': marker}):
            assert is_dataset_initialized('test_ds') is True

    def test_mark_dataset_initialized_creates_file(self, tmp_path):
        marker = tmp_path / ".init_test"
        with patch.dict('app.data.init_datasets.MARKERS', {'test_ds': marker}):
            with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
                mark_dataset_initialized('test_ds')
        assert marker.exists()

    def test_legacy_marker_counts_for_terpene_parser(self, tmp_path):
        legacy = tmp_path / ".initialized"
        legacy.touch()
        with patch('app.data.init_datasets.LEGACY_MARKER', legacy):
            assert is_dataset_initialized('terpene_parser') is True

    def test_unknown_key_returns_false(self):
        assert is_dataset_initialized('nonexistent_dataset') is False

    def test_independent_markers(self, tmp_path):
        """Each dataset marker is independent."""
        marker_a = tmp_path / ".init_a"
        marker_b = tmp_path / ".init_b"
        marker_a.touch()
        with patch.dict('app.data.init_datasets.MARKERS', {'a': marker_a, 'b': marker_b}):
            assert is_dataset_initialized('a') is True
            assert is_dataset_initialized('b') is False


# ---------------------------------------------------------------------------
# Phytochemical Diversity parser tests
# ---------------------------------------------------------------------------

class TestParsePhytochemCsv:

    def test_parse_returns_correct_strain_count(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        # Should have 3 unique strains: blue-dream (3 samples), og-kush (1), sour-diesel (1)
        # Row 6 has has_terps=0, row 7 has no strain_slug
        names = [s['name'] for s in result]
        assert "Blue Dream" in names
        assert "Og Kush" in names
        assert "Sour Diesel" in names
        assert len(result) == 3

    def test_parse_aggregates_by_mean(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        blue_dream = next(s for s in result if s['name'] == 'Blue Dream')

        # Blue Dream has 3 samples for myrcene: 0.55, 0.60, 0.50 -> mean = 0.55
        assert abs(blue_dream['terpenes']['myrcene'] - 0.55) < 0.001

        # limonene: 0.35, 0.40, 0.30 -> mean = 0.35
        assert abs(blue_dream['terpenes']['limonene'] - 0.35) < 0.001

    def test_parse_includes_sample_count(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        blue_dream = next(s for s in result if s['name'] == 'Blue Dream')
        assert blue_dream['sample_count'] == 3

        og_kush = next(s for s in result if s['name'] == 'Og Kush')
        assert og_kush['sample_count'] == 1

    def test_parse_skips_no_terp_rows(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        names = [s['name'] for s in result]
        assert "No Terps Strain" not in names

    def test_parse_skips_empty_slug(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        # Row 7 has empty strain_slug
        assert len(result) == 3

    def test_parse_extracts_cannabinoids(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        og_kush = next(s for s in result if s['name'] == 'Og Kush')
        # tot_thc=26.0, should be stored as fraction: 0.26
        assert og_kush['totals'].thc is not None
        assert og_kush['totals'].thc == pytest.approx(0.26, abs=0.01)

    def test_parse_maps_terpene_columns_correctly(self):
        result = parse_phytochem_csv(FIXTURES_DIR / "phytochem_sample.csv")
        og_kush = next(s for s in result if s['name'] == 'Og Kush')
        # a_pinene -> alpha_pinene
        assert 'alpha_pinene' in og_kush['terpenes']
        # b_pinene -> beta_pinene
        assert 'beta_pinene' in og_kush['terpenes']
        # tot_ocimene -> ocimene
        assert 'ocimene' in og_kush['terpenes']


# ---------------------------------------------------------------------------
# Cannlytics parser tests
# ---------------------------------------------------------------------------

class TestParseCannlyticsStateCsv:

    def test_parse_returns_correct_strain_count(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        # GSC (2 samples), Wedding Cake (1), Jack Herer (1)
        # Row 4 has no strain_name, Row 5 (Gelato) has no terpene data
        names = [s['name'] for s in result]
        assert "Girl Scout Cookies" in names
        assert "Wedding Cake" in names
        assert "Jack Herer" in names
        assert len(result) == 3

    def test_parse_skips_empty_strain_name(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        names = [s['name'] for s in result]
        # Row 4 has empty strain name
        assert "" not in names

    def test_parse_skips_no_terpene_data(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        names = [s['name'] for s in result]
        # Gelato row has no terpene columns
        assert "Gelato" not in names

    def test_parse_aggregates_gsc(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        gsc = next(s for s in result if s['name'] == 'Girl Scout Cookies')

        # beta_myrcene: 0.45, 0.50 -> mean = 0.475
        assert abs(gsc['terpenes']['myrcene'] - 0.475) < 0.001
        assert gsc['sample_count'] == 2

    def test_parse_extracts_cannabinoids(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        wedding = next(s for s in result if s['name'] == 'Wedding Cake')
        # total_thc=28.0 -> fraction 0.28
        assert wedding['totals'].thc is not None
        assert wedding['totals'].thc == pytest.approx(0.28, abs=0.01)

    def test_parse_detects_terpinolene_dominant(self):
        result = parse_cannlytics_state_csv(FIXTURES_DIR / "cannlytics_sample.csv", "Test State")
        jack = next(s for s in result if s['name'] == 'Jack Herer')
        # Jack Herer has terpinolene=0.55, should be highest
        assert jack['terpenes']['terpinolene'] == 0.55
        assert jack['terpenes']['terpinolene'] > jack['terpenes'].get('myrcene', 0)


# ---------------------------------------------------------------------------
# OpenTHC parser tests
# ---------------------------------------------------------------------------

class TestParseOpenthcVarieties:

    def test_parse_returns_stub_map(self, tmp_path):
        # Copy fixture to tmp_path so the output file goes there
        import shutil
        fixture = FIXTURES_DIR / "openthc_sample.json"

        with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
            result = parse_openthc_varieties(fixture)

        assert isinstance(result, dict)
        assert result['bluedream'] == 'Blue Dream'
        assert result['girlscoutcookies'] == 'Girl Scout Cookies'
        assert result['ogkush'] == 'OG Kush'

    def test_parse_skips_empty_name(self, tmp_path):
        with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
            result = parse_openthc_varieties(FIXTURES_DIR / "openthc_sample.json")

        # Entry with empty name should be skipped
        assert 'emptystrain' not in result

    def test_parse_skips_empty_stub(self, tmp_path):
        with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
            result = parse_openthc_varieties(FIXTURES_DIR / "openthc_sample.json")

        # Purple Haze has empty stub, should be skipped
        assert '' not in result

    def test_parse_saves_alias_map_file(self, tmp_path):
        with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
            parse_openthc_varieties(FIXTURES_DIR / "openthc_sample.json")

        alias_file = tmp_path / "strain_alias_map.json"
        assert alias_file.exists()

        with open(alias_file) as f:
            saved = json.load(f)
        assert saved['bluedream'] == 'Blue Dream'

    def test_parse_count(self, tmp_path):
        with patch('app.data.init_datasets.DATASETS_DIR', tmp_path):
            result = parse_openthc_varieties(FIXTURES_DIR / "openthc_sample.json")

        # 7 entries, minus 1 empty name, minus 1 empty stub = 5
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Classifier with small absolute-weight percentages
# ---------------------------------------------------------------------------

class TestClassifierWithAbsoluteWeights:
    """Test that the classifier handles small absolute weight values correctly.

    Phytochemical diversity data uses absolute percentages (e.g., 0.55% myrcene)
    rather than relative proportions. The classifier's normalize_terpene_profile()
    should handle this by normalizing to relative proportions.
    """

    def test_small_values_normalize_correctly(self):
        # Typical phytochem values: myrcene=0.55%, limonene=0.35%, caryophyllene=0.25%
        profile = {'myrcene': 0.55, 'limonene': 0.35, 'caryophyllene': 0.25}
        normalized = normalize_terpene_profile(profile)
        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.001

    def test_classify_small_myrcene_dominant(self):
        # Myrcene is highest -> should classify as BLUE
        profile = {
            'myrcene': 0.55, 'limonene': 0.35, 'caryophyllene': 0.25,
            'alpha_pinene': 0.12, 'beta_pinene': 0.08, 'humulene': 0.15,
            'linalool': 0.12, 'terpinolene': 0.03, 'ocimene': 0.02,
        }
        category = classify_terpene_profile(profile)
        assert category == "BLUE"

    def test_classify_small_terpinolene_dominant(self):
        # Terpinolene is highest -> should classify as ORANGE
        profile = {
            'terpinolene': 0.55, 'myrcene': 0.20, 'ocimene': 0.15,
            'limonene': 0.10, 'caryophyllene': 0.08,
        }
        category = classify_terpene_profile(profile)
        assert category == "ORANGE"

    def test_classify_small_limonene_dominant(self):
        # Limonene is highest -> should classify as YELLOW
        profile = {
            'limonene': 0.50, 'myrcene': 0.20, 'caryophyllene': 0.15,
            'linalool': 0.10, 'alpha_pinene': 0.05,
        }
        category = classify_terpene_profile(profile)
        assert category == "YELLOW"


# ---------------------------------------------------------------------------
# import_strains_to_db tests (mocked database)
# ---------------------------------------------------------------------------

class TestImportStrainsToDb:

    @patch('app.data.init_datasets.SessionLocal')
    def test_import_returns_counts(self, mock_session_cls):
        from app.data.init_datasets import import_strains_to_db

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        # No existing profiles
        mock_db.query.return_value.filter.return_value.first.return_value = None

        strains = [
            {
                'name': 'Test Strain',
                'terpenes': {'myrcene': 0.5, 'limonene': 0.3},
                'totals': MagicMock(model_dump=lambda: {'thc': 0.2}),
            }
        ]
        imported, skipped = import_strains_to_db(
            strains, source='test', original_dataset='test_ds'
        )
        assert imported == 1
        assert skipped == 0

    @patch('app.data.init_datasets.SessionLocal')
    def test_import_skips_existing(self, mock_session_cls):
        from app.data.init_datasets import import_strains_to_db

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        # Simulate existing profile
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        strains = [
            {
                'name': 'Existing Strain',
                'terpenes': {'myrcene': 0.5},
                'totals': MagicMock(model_dump=lambda: {}),
            }
        ]
        imported, skipped = import_strains_to_db(strains, source='test', original_dataset='test_ds')
        assert imported == 0
        assert skipped == 1

    @patch('app.data.init_datasets.SessionLocal')
    def test_import_skips_empty_name(self, mock_session_cls):
        from app.data.init_datasets import import_strains_to_db

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        strains = [
            {
                'name': '!!!',  # normalizes to empty
                'terpenes': {'myrcene': 0.5},
                'totals': MagicMock(model_dump=lambda: {}),
            }
        ]
        imported, skipped = import_strains_to_db(strains, source='test', original_dataset='test_ds')
        assert imported == 0
        assert skipped == 1

    @patch('app.data.init_datasets.SessionLocal')
    def test_import_stores_sample_count_in_provenance(self, mock_session_cls):
        from app.data.init_datasets import import_strains_to_db

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        strains = [
            {
                'name': 'Multi Sample',
                'terpenes': {'myrcene': 0.5},
                'totals': MagicMock(model_dump=lambda: {}),
                'sample_count': 15,
            }
        ]
        import_strains_to_db(strains, source='test', original_dataset='test_ds')

        # Check that db.add was called and the profile has sample_count in provenance
        added_profile = mock_db.add.call_args[0][0]
        assert added_profile.provenance['sample_count'] == 15
        assert added_profile.provenance['original_dataset'] == 'test_ds'
