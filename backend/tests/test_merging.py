# Tests for app/utils/merging.py

from app.utils.merging import merge_terpene_data, merge_cannabinoid_data
from app.models.schemas import Totals


class TestMergeTerpeneData:

    def test_coa_highest_priority(self):
        coa = {"myrcene": 0.5}
        page = {"myrcene": 0.3}
        db = {"myrcene": 0.2}
        api = {"myrcene": 0.1}
        merged, sources = merge_terpene_data(coa, page, db, api)
        assert merged["myrcene"] == 0.5
        assert "coa" in sources

    def test_page_over_db_and_api(self):
        merged, sources = merge_terpene_data(
            {}, {"limonene": 0.4}, {"limonene": 0.2}, {"limonene": 0.1}
        )
        assert merged["limonene"] == 0.4
        assert "page" in sources

    def test_db_over_api(self):
        merged, sources = merge_terpene_data(
            {}, {}, {"caryophyllene": 0.3}, {"caryophyllene": 0.1}
        )
        assert merged["caryophyllene"] == 0.3
        assert "database" in sources

    def test_api_fallback(self):
        merged, sources = merge_terpene_data(
            {}, {}, {}, {"humulene": 0.15}
        )
        assert merged["humulene"] == 0.15
        assert "api" in sources

    def test_gap_filling(self):
        # COA has myrcene, page has limonene — both should be in merged
        coa = {"myrcene": 0.5}
        page = {"limonene": 0.3}
        merged, sources = merge_terpene_data(coa, page, {}, {})
        assert merged["myrcene"] == 0.5
        assert merged["limonene"] == 0.3
        assert "coa" in sources
        assert "page" in sources

    def test_zero_values_skipped(self):
        coa = {"myrcene": 0.0}
        page = {"myrcene": 0.3}
        merged, _ = merge_terpene_data(coa, page, {}, {})
        assert merged["myrcene"] == 0.3

    def test_none_values_skipped(self):
        coa = {"myrcene": None}
        page = {"myrcene": 0.3}
        merged, _ = merge_terpene_data(coa, page, {}, {})
        assert merged["myrcene"] == 0.3

    def test_all_empty(self):
        merged, sources = merge_terpene_data({}, {}, {}, {})
        assert merged == {}
        assert sources == []

    def test_multiple_terpenes_mixed_sources(self):
        coa = {"myrcene": 0.5}
        page = {"limonene": 0.4}
        db = {"caryophyllene": 0.3, "myrcene": 0.2}
        api = {"humulene": 0.1}
        merged, sources = merge_terpene_data(coa, page, db, api)
        assert merged["myrcene"] == 0.5  # from coa
        assert merged["limonene"] == 0.4  # from page
        assert merged["caryophyllene"] == 0.3  # from db
        assert merged["humulene"] == 0.1  # from api

    def test_none_source_dicts(self):
        # None dicts should be handled (treated as empty)
        merged, sources = merge_terpene_data(None, None, None, None)
        assert merged == {}

    def test_preserves_all_unique_keys(self):
        coa = {"myrcene": 0.5}
        page = {"limonene": 0.4}
        db = {"pinene": 0.3}
        api = {"ocimene": 0.2}
        merged, _ = merge_terpene_data(coa, page, db, api)
        assert len(merged) == 4


class TestMergeCannabinoidData:

    def test_coa_priority(self):
        coa = Totals(thc=0.25)
        page = Totals(thc=0.20)
        merged, sources = merge_cannabinoid_data(coa, page, Totals(), Totals())
        assert merged.thc == 0.25
        assert "coa" in sources

    def test_gap_filling_cannabinoids(self):
        coa = Totals(thc=0.25)
        page = Totals(cbd=0.05)
        merged, sources = merge_cannabinoid_data(coa, page, Totals(), Totals())
        assert merged.thc == 0.25
        assert merged.cbd == 0.05

    def test_zero_values_skipped(self):
        coa = Totals(thc=0.0)
        page = Totals(thc=0.20)
        merged, _ = merge_cannabinoid_data(coa, page, Totals(), Totals())
        assert merged.thc == 0.20

    def test_all_empty(self):
        merged, sources = merge_cannabinoid_data(Totals(), Totals(), Totals(), Totals())
        assert sources == []

    def test_api_fallback_cannabinoids(self):
        api = Totals(thca=0.22, cbg=0.01)
        merged, sources = merge_cannabinoid_data(Totals(), Totals(), Totals(), api)
        assert merged.thca == 0.22
        assert merged.cbg == 0.01
        assert "api" in sources
