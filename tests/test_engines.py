"""Engine tests against independently verifiable financial math."""

import pytest

from finance_engines_mcp import engines


class TestCompoundGrowth:
    def test_textbook_monthly_compounding(self):
        # 10,000 at 12% APR compounded monthly for 1 year = 10,000 * 1.01^12
        result = engines.compound_growth(10_000, 12, 1)
        assert result["future_value"] == 11_268.25

    def test_zero_rate_is_simple_accumulation(self):
        result = engines.compound_growth(1_000, 0, 2, monthly_contribution=100)
        assert result["future_value"] == 1_000 + 100 * 24
        assert result["total_growth"] == 0.0

    def test_contributions_annuity_formula(self):
        # 500/mo at 6% for 10 years, no principal: FV = 500 * ((1.005^120 - 1)/0.005)
        result = engines.compound_growth(0, 6, 10, monthly_contribution=500)
        assert result["future_value"] == 81_939.67

    def test_rejects_negative_years(self):
        with pytest.raises(ValueError):
            engines.compound_growth(1000, 5, -1)


class TestLoanAmortization:
    def test_classic_30_year_mortgage(self):
        # 300,000 at 6% for 30 years -> 1,798.65/mo (standard reference value)
        result = engines.loan_amortization(300_000, 6, 30)
        assert result["monthly_payment"] == 1_798.65
        assert result["months"] == 360

    def test_first_payment_split(self):
        result = engines.loan_amortization(300_000, 6, 30)
        assert result["first_payment"]["interest"] == 1_500.00
        assert result["first_payment"]["principal"] == 298.65

    def test_schedule_reconciles(self):
        # total paid = principal + total interest, to the cent
        result = engines.loan_amortization(250_000, 5.5, 15)
        assert result["total_paid"] == pytest.approx(
            250_000 + result["total_interest"], abs=0.01
        )

    def test_zero_rate_loan(self):
        result = engines.loan_amortization(12_000, 0, 1)
        assert result["monthly_payment"] == 1_000.00
        assert result["total_interest"] == 0.0


class TestEffectiveAnnualRate:
    def test_monthly_compounding_of_12_pct(self):
        # (1 + 0.12/12)^12 - 1 = 12.6825%
        result = engines.effective_annual_rate(12, 12)
        assert result["effective_annual_pct"] == 12.6825

    def test_annual_compounding_is_identity(self):
        result = engines.effective_annual_rate(7, 1)
        assert result["effective_annual_pct"] == 7.0


class TestInflationAdjusted:
    def test_known_discounting(self):
        # 100,000 in 10 years at 3% inflation = 74,409.39 today
        result = engines.inflation_adjusted(100_000, 3, 10)
        assert result["todays_purchasing_power"] == 74_409.39

    def test_zero_years_unchanged(self):
        result = engines.inflation_adjusted(5_000, 3, 0)
        assert result["todays_purchasing_power"] == 5_000.00


class TestSavingsGoal:
    def test_already_met(self):
        result = engines.savings_goal_months(10_000, 12_000, 5, 100)
        assert result["months"] == 0

    def test_no_growth_exact_division(self):
        result = engines.savings_goal_months(1_200, 0, 0, 100)
        assert result["months"] == 12

    def test_growth_shortens_timeline(self):
        without = engines.savings_goal_months(50_000, 10_000, 0, 500)
        with_growth = engines.savings_goal_months(50_000, 10_000, 7, 500)
        assert with_growth["months"] < without["months"]

    def test_unreachable_goal_raises(self):
        with pytest.raises(ValueError):
            engines.savings_goal_months(1_000_000, 0, 0, 0)


class TestRetirementProjection:
    def test_composes_growth_and_inflation(self):
        result = engines.retirement_projection(40, 60, 100_000, 1_000, 7, 2.5)
        nominal = engines.compound_growth(100_000, 7, 20, 1_000)["future_value"]
        real = engines.inflation_adjusted(nominal, 2.5, 20)["todays_purchasing_power"]
        assert result["projected_nominal"] == nominal
        assert result["projected_todays_dollars"] == real

    def test_rejects_inverted_ages(self):
        with pytest.raises(ValueError):
            engines.retirement_projection(60, 40, 0, 0, 5)
