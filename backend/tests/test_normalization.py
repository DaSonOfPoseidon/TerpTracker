# Tests for app/utils/normalization.py

from app.utils.normalization import normalize_strain_name


class TestNormalizeStrainName:

    def test_basic_lowercase(self):
        assert normalize_strain_name("Blue Dream") == "blue dream"

    def test_title_case(self):
        assert normalize_strain_name("blue dream", title_case=True) == "Blue Dream"

    def test_removes_flower_suffix(self):
        result = normalize_strain_name("OG Kush flower")
        assert "flower" not in result
        assert result == "og kush"

    def test_removes_strain_suffix(self):
        result = normalize_strain_name("Girl Scout Cookies strain")
        assert "strain" not in result

    def test_removes_indica_suffix(self):
        result = normalize_strain_name("Northern Lights indica")
        assert "indica" not in result

    def test_special_characters_replaced(self):
        # Hash/number signs become spaces, then get collapsed
        result = normalize_strain_name("OG Kush #18")
        assert result == "og kush 18"

    def test_whitespace_normalization(self):
        result = normalize_strain_name("  Blue   Dream  ")
        assert result == "blue dream"

    def test_empty_string(self):
        result = normalize_strain_name("")
        assert result == ""

    def test_already_clean(self):
        result = normalize_strain_name("gelato")
        assert result == "gelato"
