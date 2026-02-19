# Tests for classifier.py:generate_cannabinoid_insights()

from app.services.classifier import generate_cannabinoid_insights
from app.models.schemas import Totals


class TestCannabinoidInsights:

    def test_thc_dominant_high_ratio(self):
        totals = Totals(thc=25.0, cbd=0.5)
        insights = generate_cannabinoid_insights(totals)
        assert any("THC-dominant" in i for i in insights)

    def test_high_thc_ratio(self):
        totals = Totals(thc=20.0, cbd=2.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("High THC" in i or "THC" in i for i in insights)

    def test_balanced_ratio(self):
        totals = Totals(thc=10.0, cbd=10.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("Balanced" in i for i in insights)

    def test_cbd_rich(self):
        totals = Totals(thc=1.0, cbd=15.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("CBD-rich" in i for i in insights)

    def test_very_high_potency(self):
        # Code compares thc_total > 25 (percentage scale, not fraction)
        totals = Totals(thc=28.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("Very high potency" in i for i in insights)

    def test_high_potency(self):
        totals = Totals(thc=22.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("High potency" in i for i in insights)

    def test_moderate_potency(self):
        totals = Totals(thc=12.0)
        insights = generate_cannabinoid_insights(totals)
        assert any("Moderate potency" in i for i in insights)

    def test_thca_decarb_factor(self):
        # THCA * 0.877 should contribute to effective THC
        totals = Totals(thca=30.0)  # effective = 30.0 * 0.877 = 26.3
        insights = generate_cannabinoid_insights(totals)
        assert any("potency" in i.lower() for i in insights)

    def test_elevated_cbn(self):
        totals = Totals(thc=15.0, cbn=0.01)
        insights = generate_cannabinoid_insights(totals)
        assert any("CBN" in i for i in insights)

    def test_notable_cbg(self):
        totals = Totals(thc=15.0, cbg=0.02)
        insights = generate_cannabinoid_insights(totals)
        assert any("CBG" in i for i in insights)

    def test_empty_totals(self):
        totals = Totals()
        insights = generate_cannabinoid_insights(totals)
        assert insights == []
