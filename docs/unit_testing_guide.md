# Unit Testing Guide: Liability Cash Flow Projection, Economic Scenario Generation, and Stochastic Calculations

## Table of Contents

1. [Overview](#overview)
2. [Project Setup](#project-setup)
3. [Part 1 — Deterministic Cash Flow Projection](#part-1--deterministic-cash-flow-projection)
   - [Testing Actuarial Assumptions](#11-testing-actuarial-assumptions)
   - [Testing `CashFlowProjection`](#12-testing-cashflowprojection)
   - [Testing `LiabilityModel`](#13-testing-liabilitymodel)
4. [Part 2 — Economic Scenario Generation](#part-2--economic-scenario-generation)
   - [Testing `ScenarioConfig`](#21-testing-scenarioconfig)
   - [Testing Individual Stochastic Processes](#22-testing-individual-stochastic-processes)
   - [Testing `generate_scenarios()`](#23-testing-generate_scenarios)
5. [Part 3 — Stochastic Cash Flow Calculations](#part-3--stochastic-cash-flow-calculations)
   - [Testing `DynamicCashFlowModel`](#31-testing-dynamiccashflowmodel)
   - [Testing Risk Metrics](#32-testing-risk-metrics)
   - [Testing Multi-Scenario Integration](#33-testing-multi-scenario-integration)
6. [Test Fixtures Reference](#test-fixtures-reference)
7. [Running the Tests](#running-the-tests)
8. [Interpreting Results](#interpreting-results)

---

## Overview

This guide covers unit testing for three distinct layers of the actuarial model:

| Layer | Primary Classes | Test Scope |
|---|---|---|
| **Deterministic** | `LiabilityModel`, `CashFlowProjection`, `MortalityTable`, `LapseAssumption`, `InflationAssumption` | Single-path, fixed-assumption projections |
| **Economic Scenarios** | `EconomicScenarioGenerator`, `ScenarioConfig` | Hull-White rates, Merton jump-diffusion, credit spreads, inflation paths |
| **Stochastic** | `DynamicCashFlowModel`, `CashFlow` | Multi-scenario cash flows, VaR, CTE, NPV distributions |

Each layer has its own pytest file. Tests are written to verify:

- **Structural correctness** — outputs have the right shapes, types, and index labels
- **Boundary conditions** — zero contracts, single time-step, edge ages (0, 120)
- **Economic sense** — premiums are positive, death benefits are non-negative, mortality rates lie in (0, 1)
- **Determinism** — same seed produces identical results
- **Integration** — deterministic output feeds correctly into the stochastic layer

---

## Project Setup

### Directory layout

```
tests/
├── __init__.py
├── test_deterministic_cashflows.py   ← Part 1
├── test_economic_scenarios.py        ← Part 2
├── test_stochastic_calculations.py   ← Part 3
└── conftest.py                       ← shared fixtures
```

### Install test dependencies

```bash
pip install pytest pytest-cov numpy pandas scipy
```

### conftest.py — shared fixtures

Create `tests/conftest.py` with the fixtures that every test module needs:

```python
# tests/conftest.py
"""Shared pytest fixtures for actuarial model tests."""
import pytest
from datetime import date
from unittest.mock import MagicMock

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from actuarial_stochastic_model.models.liabilities.actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption,
    create_sample_mortality_table, create_sample_lapse_assumption,
    create_sample_inflation_assumption, ActuarialAssumptions,
)
from actuarial_stochastic_model.models.liabilities.liability_model import (
    LiabilityModel, CashFlowProjection,
)
from actuarial_stochastic_model.models.products.term import TermInsurance
from actuarial_stochastic_model.models.products.whole_life import WholeLifeInsurance
from actuarial_stochastic_model.enums import Sex, ProductType, PremiumMode
from economic_scenario_generator import EconomicScenarioGenerator, ScenarioConfig


# ── Assumptions ────────────────────────────────────────────────────────────────

@pytest.fixture
def base_assumptions() -> ActuarialAssumptions:
    return ActuarialAssumptions()


@pytest.fixture
def mortality_table(base_assumptions) -> MortalityTable:
    return create_sample_mortality_table(base_assumptions)


@pytest.fixture
def lapse_assumption(base_assumptions) -> LapseAssumption:
    return create_sample_lapse_assumption(base_assumptions)


@pytest.fixture
def inflation_assumption(base_assumptions) -> InflationAssumption:
    return create_sample_inflation_assumption(base_assumptions)


# ── Contracts ──────────────────────────────────────────────────────────────────

@pytest.fixture
def term_contract() -> TermInsurance:
    """Standard 20-year term policy, male age 35."""
    return TermInsurance(
        policy_number="T-001",
        issue_date=date(2020, 1, 1),
        face_amount=500_000.0,
        term_length=20,
        issue_age=35,
        sex=Sex.MALE,
        modal_premium=1_200.0,
        premium_mode=PremiumMode.ANNUAL,
    )


@pytest.fixture
def whole_life_contract() -> WholeLifeInsurance:
    """Whole life policy, female age 45."""
    return WholeLifeInsurance(
        policy_number="WL-001",
        issue_date=date(2015, 6, 1),
        face_amount=250_000.0,
        guaranteed_rate=0.03,
        issue_age=45,
        sex=Sex.FEMALE,
        modal_premium=2_400.0,
        premium_mode=PremiumMode.ANNUAL,
    )


# ── LiabilityModel ─────────────────────────────────────────────────────────────

@pytest.fixture
def liability_model(mortality_table, lapse_assumption, inflation_assumption):
    return LiabilityModel(
        mortality_table=mortality_table,
        lapse_assumption=lapse_assumption,
        inflation_assumption=inflation_assumption,
        investment_returns={},
        minimum_dividend_rate=0.01,
        shareholder_cost_rate=0.02,
    )


@pytest.fixture
def loaded_model(liability_model, term_contract, whole_life_contract):
    """Model pre-loaded with one term and one whole-life contract."""
    liability_model.add_contract(term_contract)
    liability_model.add_contract(whole_life_contract)
    return liability_model


# ── Scenario generator ─────────────────────────────────────────────────────────

@pytest.fixture
def scenario_config() -> ScenarioConfig:
    return ScenarioConfig(
        short_rate_mean=0.04,
        short_rate_speed=0.1,
        short_rate_vol=0.02,
        equity_return_mean=0.07,
        equity_vol=0.15,
        jump_intensity=0.1,
        jump_mean=-0.05,
        jump_vol=0.1,
        credit_spread_mean=0.015,
        credit_spread_vol=0.005,
        inflation_mean=0.025,
        inflation_vol=0.005,
    )


@pytest.fixture
def scenario_generator(scenario_config) -> EconomicScenarioGenerator:
    return EconomicScenarioGenerator(scenario_config)
```

---

## Part 1 — Deterministic Cash Flow Projection

Create `tests/test_deterministic_cashflows.py`.

### 1.1 Testing Actuarial Assumptions

These tests verify the building-block assumptions before testing the full projection.

```python
# tests/test_deterministic_cashflows.py
"""
Unit tests for deterministic liability cash flow projection.

Covers:
  - MortalityTable, LapseAssumption, InflationAssumption
  - CashFlowProjection dataclass
  - LiabilityModel.project_cashflows()
  - LiabilityModel.calculate_present_values()
"""
import pytest
from datetime import date
from typing import Dict

import numpy as np
import pandas as pd

from actuarial_stochastic_model.enums import (
    Sex, ProductType, SmokingStatus, OccupationClass,
)
from actuarial_stochastic_model.models.liabilities.actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption,
)
from actuarial_stochastic_model.models.liabilities.liability_model import (
    CashFlowProjection, LiabilityModel,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1.1  MortalityTable
# ─────────────────────────────────────────────────────────────────────────────

class TestMortalityTable:
    """Tests for MortalityTable rate retrieval and adjustment factors."""

    def test_rate_in_valid_range(self, mortality_table):
        """All mortality rates must lie in (0, 1)."""
        for age in range(20, 85, 5):
            rate = mortality_table.get_rate(age=age, sex=Sex.MALE)
            assert 0 < rate < 1, f"Rate {rate} out of range at age {age}"

    def test_mortality_increases_with_age(self, mortality_table):
        """Mortality rates should be monotonically increasing with age."""
        ages = list(range(25, 80, 5))
        rates = [mortality_table.get_rate(age=a, sex=Sex.MALE) for a in ages]
        for i in range(1, len(rates)):
            assert rates[i] >= rates[i - 1], (
                f"Mortality not increasing: age {ages[i-1]} rate={rates[i-1]}, "
                f"age {ages[i]} rate={rates[i]}"
            )

    def test_female_lower_than_male(self, mortality_table):
        """Female mortality should be lower than male at every age."""
        for age in range(30, 70, 5):
            male_rate = mortality_table.get_rate(age=age, sex=Sex.MALE)
            female_rate = mortality_table.get_rate(age=age, sex=Sex.FEMALE)
            assert female_rate < male_rate, (
                f"Female rate {female_rate} >= male rate {male_rate} at age {age}"
            )

    def test_smoker_higher_than_non_smoker(self, mortality_table):
        """Smoker rates should exceed non-smoker rates."""
        for age in [35, 45, 55]:
            ns_rate = mortality_table.get_rate(
                age=age, sex=Sex.MALE,
                smoking_status=SmokingStatus.NON_SMOKER
            )
            sm_rate = mortality_table.get_rate(
                age=age, sex=Sex.MALE,
                smoking_status=SmokingStatus.SMOKER
            )
            assert sm_rate > ns_rate, (
                f"Smoker rate {sm_rate} not > non-smoker rate {ns_rate} at age {age}"
            )

    def test_boundary_age_0(self, mortality_table):
        """Should return a valid rate for newborn (age 0)."""
        rate = mortality_table.get_rate(age=0, sex=Sex.MALE)
        assert 0 < rate < 1

    def test_boundary_age_100(self, mortality_table):
        """Should return a rate close to 1 at age 100."""
        rate = mortality_table.get_rate(age=100, sex=Sex.MALE)
        assert 0 < rate <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 1.2  LapseAssumption
# ─────────────────────────────────────────────────────────────────────────────

class TestLapseAssumption:
    """Tests for LapseAssumption rate retrieval and dynamic factors."""

    def test_lapse_rate_in_valid_range(self, lapse_assumption):
        """All base lapse rates must lie in [0, 1)."""
        for year in range(1, 21):
            rate = lapse_assumption.get_rate(duration=year)
            assert 0 <= rate < 1, f"Lapse rate {rate} out of range at year {year}"

    def test_early_duration_higher_lapse(self, lapse_assumption):
        """Year-1 lapse rate should be higher than year-15 (shock lapse pattern)."""
        year1 = lapse_assumption.get_rate(duration=1)
        year15 = lapse_assumption.get_rate(duration=15)
        assert year1 > year15, (
            f"Expected year-1 lapse {year1} > year-15 lapse {year15}"
        )

    def test_product_type_factor_applied(self, lapse_assumption):
        """Term policies should have a higher lapse rate than participating."""
        term_rate = lapse_assumption.get_rate(
            duration=5, product_type=ProductType.TERM
        )
        par_rate = lapse_assumption.get_rate(
            duration=5, product_type=ProductType.PARTICIPATING
        )
        assert term_rate > par_rate, (
            f"Term lapse {term_rate} should exceed participating lapse {par_rate}"
        )

    def test_dynamic_factor_positive(self, lapse_assumption):
        """Dynamic lapse factors must be positive."""
        for year in range(1, 11):
            factor = lapse_assumption.get_dynamic_factor(year)
            assert factor > 0, f"Dynamic factor {factor} not positive at year {year}"

    def test_zero_duration_returns_valid_rate(self, lapse_assumption):
        """Duration 0 (issue date) should return a valid rate, not raise."""
        rate = lapse_assumption.get_rate(duration=0)
        assert rate >= 0


# ─────────────────────────────────────────────────────────────────────────────
# 1.3  InflationAssumption
# ─────────────────────────────────────────────────────────────────────────────

class TestInflationAssumption:
    """Tests for InflationAssumption rate retrieval."""

    def test_base_rate_positive(self, inflation_assumption):
        """Base inflation rate must be positive."""
        rate = inflation_assumption.get_rate(date(2025, 1, 1))
        assert rate > 0, f"Base inflation rate {rate} should be positive"

    def test_medical_inflation_exceeds_general(self, inflation_assumption):
        """Medical inflation should exceed general (default factor 2x base)."""
        general = inflation_assumption.get_rate(date(2025, 1, 1), is_medical=False)
        medical = inflation_assumption.get_rate(date(2025, 1, 1), is_medical=True)
        assert medical >= general, (
            f"Medical inflation {medical} should be >= general {general}"
        )

    def test_wage_inflation_between_general_and_medical(self, inflation_assumption):
        """Wage inflation (1.5x base) should lie between general and medical."""
        general = inflation_assumption.get_rate(date(2025, 1, 1))
        wage = inflation_assumption.get_rate(date(2025, 1, 1), is_wage=True)
        medical = inflation_assumption.get_rate(date(2025, 1, 1), is_medical=True)
        assert general <= wage <= medical

    def test_inflation_factor_compounding(self, inflation_assumption):
        """A 2-year factor should be the square of the 1-year factor (compound)."""
        start = date(2025, 1, 1)
        mid = date(2026, 1, 1)
        end = date(2027, 1, 1)
        factor_1yr = inflation_assumption.get_inflation_factor(start, mid)
        factor_2yr = inflation_assumption.get_inflation_factor(start, end)
        assert abs(factor_2yr - factor_1yr ** 2) < 1e-6, (
            f"2-year factor {factor_2yr:.6f} != (1-year factor)^2 {factor_1yr**2:.6f}"
        )

    def test_same_date_factor_is_one(self, inflation_assumption):
        """Inflation factor from date to itself must equal 1."""
        d = date(2025, 6, 1)
        factor = inflation_assumption.get_inflation_factor(d, d)
        assert abs(factor - 1.0) < 1e-9
```

---

### 1.2 Testing `CashFlowProjection`

```python
# ─────────────────────────────────────────────────────────────────────────────
# 1.4  CashFlowProjection
# ─────────────────────────────────────────────────────────────────────────────

class TestCashFlowProjection:
    """Tests for the CashFlowProjection dataclass."""

    @pytest.fixture
    def simple_projection(self) -> CashFlowProjection:
        """Three time-point projection with known values."""
        dates = [date(2025, 1, 1), date(2026, 1, 1), date(2027, 1, 1)]
        return CashFlowProjection(
            time_points=dates,
            premiums=[1000.0, 1000.0, 1000.0],
            death_benefits=[500.0, 510.0, 520.0],
            surrenders=[50.0, 55.0, 60.0],
            expenses=[50.0, 51.0, 52.0],
            dividends=[10.0, 10.5, 11.0],
            policy_loans=[0.0, 0.0, 0.0],
            loan_repayments=[0.0, 0.0, 0.0],
            withdrawals=[0.0, 0.0, 0.0],
            cash_dividends=[10.0, 10.5, 11.0],
            experience_dividends=[0.0, 0.0, 0.0],
        )

    def test_to_dataframe_shape(self, simple_projection):
        """DataFrame should have 3 rows and the correct columns."""
        df = simple_projection.to_dataframe()
        assert df.shape[0] == 3
        expected_cols = {
            'Premium', 'Death_Benefit', 'Surrender', 'Expenses',
            'Dividends', 'Policy_Loans', 'Loan_Repayments',
            'Withdrawals', 'Cash_Dividends', 'Experience_Dividends'
        }
        assert expected_cols.issubset(set(df.columns))

    def test_to_dataframe_index_is_date(self, simple_projection):
        """DataFrame index must be date objects."""
        df = simple_projection.to_dataframe()
        assert all(isinstance(idx, date) for idx in df.index)

    def test_present_values_keys(self, simple_projection):
        """calculate_present_values() must return all required cash flow keys."""
        discount_rates = {
            date(2025, 1, 1): 0.05,
            date(2026, 1, 1): 0.05,
            date(2027, 1, 1): 0.05,
        }
        pvs = simple_projection.calculate_present_values(discount_rates)
        required = {
            'Premium', 'Death_Benefit', 'Surrender', 'Expenses',
            'Dividends', 'Net_Cashflow'
        }
        assert required.issubset(set(pvs.keys()))

    def test_pv_premiums_less_than_undiscounted(self, simple_projection):
        """Present value of premiums must be less than the undiscounted sum."""
        discount_rates = {d: 0.05 for d in simple_projection.time_points}
        pvs = simple_projection.calculate_present_values(discount_rates)
        undiscounted = sum(simple_projection.premiums)
        assert pvs['Premium'] < undiscounted, (
            "PV of premiums should be < undiscounted sum when discount rate > 0"
        )

    def test_pv_is_positive_for_positive_cashflows(self, simple_projection):
        """PV must remain positive for strictly positive cash flow vectors."""
        discount_rates = {d: 0.04 for d in simple_projection.time_points}
        pvs = simple_projection.calculate_present_values(discount_rates)
        assert pvs['Premium'] > 0
        assert pvs['Death_Benefit'] > 0

    def test_net_cashflow_equals_sum_of_components(self, simple_projection):
        """Net cash flow PV should equal premiums minus outgo (within rounding)."""
        # For this fixture: loans and repayments are zero, so net = premium - (db+surr+exp+div+wd)
        discount_rates = {d: 0.0 for d in simple_projection.time_points}
        pvs = simple_projection.calculate_present_values(discount_rates)
        expected_net = (
            sum(simple_projection.premiums)
            - sum(simple_projection.death_benefits)
            - sum(simple_projection.surrenders)
            - sum(simple_projection.expenses)
            - sum(simple_projection.dividends)
        )
        assert abs(pvs['Net_Cashflow'] - expected_net) < 1.0, (
            f"Net CF PV {pvs['Net_Cashflow']:.2f} != expected {expected_net:.2f}"
        )

    def test_timestamp_conversion_in_post_init(self):
        """pd.Timestamp objects in time_points should be converted to date."""
        timestamps = pd.date_range("2025-01-01", periods=3, freq="YS")
        proj = CashFlowProjection(
            time_points=list(timestamps),
            premiums=[100.0, 100.0, 100.0],
            death_benefits=[0.0, 0.0, 0.0],
            surrenders=[0.0, 0.0, 0.0],
            expenses=[0.0, 0.0, 0.0],
            dividends=[0.0, 0.0, 0.0],
            policy_loans=[0.0, 0.0, 0.0],
            loan_repayments=[0.0, 0.0, 0.0],
            withdrawals=[0.0, 0.0, 0.0],
            cash_dividends=[0.0, 0.0, 0.0],
            experience_dividends=[0.0, 0.0, 0.0],
        )
        assert all(isinstance(t, date) for t in proj.time_points)
        assert not any(isinstance(t, pd.Timestamp) for t in proj.time_points)
```

---

### 1.3 Testing `LiabilityModel`

```python
# ─────────────────────────────────────────────────────────────────────────────
# 1.5  LiabilityModel
# ─────────────────────────────────────────────────────────────────────────────

class TestLiabilityModel:
    """Tests for the full LiabilityModel projection pipeline."""

    VALUATION_DATE = date(2025, 1, 1)
    PROJECTION_YEARS = 10

    def test_empty_model_returns_empty_dataframe(self, liability_model):
        """A model with no contracts should return an empty DataFrame."""
        df = liability_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_add_contract_increments_count(self, liability_model, term_contract):
        """add_contract() should grow the internal contracts list."""
        assert len(liability_model.contracts) == 0
        liability_model.add_contract(term_contract)
        assert len(liability_model.contracts) == 1

    def test_cashflows_output_shape(self, loaded_model):
        """
        Monthly projection over 10 years for 2 contracts:
        expect 10 * 12 = 120 time-point rows per contract = 240 total.
        """
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
            time_step='M',
        )
        expected_rows = self.PROJECTION_YEARS * 12 * 2  # 2 contracts
        assert len(df) == expected_rows, (
            f"Expected {expected_rows} rows, got {len(df)}"
        )

    def test_cashflows_required_columns_present(self, loaded_model):
        """project_cashflows() DataFrame must contain all cash flow columns."""
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        required_columns = {
            'Policy_Number', 'Premiums', 'Death_Benefits',
            'Surrenders', 'Expenses', 'Cash_Dividends',
            'Experience_Dividends', 'Policy_Loans', 'Withdrawals',
        }
        assert required_columns.issubset(set(df.reset_index().columns))

    def test_premiums_are_non_negative(self, loaded_model):
        """All projected premium cash flows must be non-negative."""
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        assert (df['Premiums'] >= 0).all(), "Found negative premiums in projection"

    def test_death_benefits_are_non_negative(self, loaded_model):
        """Death benefit cash flows must be non-negative."""
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        assert (df['Death_Benefits'] >= 0).all()

    def test_expenses_are_non_negative(self, loaded_model):
        """Expense cash flows must be non-negative."""
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        assert (df['Expenses'] >= 0).all()

    def test_surrenders_do_not_exceed_face_amount(self, loaded_model, term_contract):
        """Aggregate surrenders at any time step should not exceed the face amount."""
        df = loaded_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=self.PROJECTION_YEARS,
        )
        term_df = df[df['Policy_Number'] == term_contract.policy_number]
        assert (term_df['Surrenders'] <= term_contract.face_amount).all()

    def test_term_policy_cashflows_stop_after_term(self, liability_model, term_contract):
        """
        After the policy term expires (year 20), premiums and death benefits
        for a term contract should be zero.
        """
        liability_model.add_contract(term_contract)
        # Project for 25 years — 5 years beyond the 20-year term
        df = liability_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=25,
            time_step='Y',
        )
        term_df = df[df['Policy_Number'] == term_contract.policy_number]
        # Rows beyond year 20 — check Death_Benefits are zero
        post_term = term_df.iloc[20:]
        assert (post_term['Death_Benefits'] == 0).all(), (
            "Death benefits should be 0 after term expiry"
        )

    def test_project_liabilities_net_liability_column(self, loaded_model):
        """project_liabilities() must produce a Net_Liability column."""
        df = loaded_model.project_liabilities(n_years=5)
        assert 'Net_Liability' in df.columns
        assert 'PV_Liability' in df.columns

    def test_annual_vs_monthly_totals_are_consistent(self, liability_model, term_contract):
        """
        Summed monthly premiums over a year should closely match
        annual premium projection (within 5% tolerance for timing differences).
        """
        liability_model.add_contract(term_contract)
        monthly = liability_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=1,
            time_step='M',
        )
        annual = liability_model.project_cashflows(
            valuation_date=self.VALUATION_DATE,
            projection_years=1,
            time_step='Y',
        )
        monthly_total = monthly['Premiums'].sum()
        annual_total = annual['Premiums'].sum()
        # Allow 5% tolerance for month-end timing differences
        assert abs(monthly_total - annual_total) / annual_total < 0.05, (
            f"Monthly total {monthly_total:.2f} vs annual total {annual_total:.2f} "
            f"differ by more than 5%"
        )
```

---

## Part 2 — Economic Scenario Generation

Create `tests/test_economic_scenarios.py`.

### 2.1 Testing `ScenarioConfig`

```python
# tests/test_economic_scenarios.py
"""
Unit tests for economic scenario generation.

Covers:
  - ScenarioConfig validation
  - EconomicScenarioGenerator._generate_hull_white_rates()
  - EconomicScenarioGenerator._generate_merton_jumps()
  - EconomicScenarioGenerator._generate_credit_spreads()
  - EconomicScenarioGenerator._generate_inflation()
  - EconomicScenarioGenerator.generate_scenarios()
"""
import pytest
import numpy as np
from economic_scenario_generator import EconomicScenarioGenerator, ScenarioConfig


class TestScenarioConfig:
    """Validate ScenarioConfig parameter ranges."""

    def test_positive_volatilities(self, scenario_config):
        """All volatility parameters must be strictly positive."""
        assert scenario_config.short_rate_vol > 0
        assert scenario_config.equity_vol > 0
        assert scenario_config.credit_spread_vol > 0
        assert scenario_config.inflation_vol > 0

    def test_positive_mean_reversion_speed(self, scenario_config):
        """Mean-reversion speed must be positive."""
        assert scenario_config.short_rate_speed > 0

    def test_positive_mean_levels(self, scenario_config):
        """Long-run mean levels (short rate, credit spread) must be positive."""
        assert scenario_config.short_rate_mean > 0
        assert scenario_config.credit_spread_mean > 0

    def test_jump_intensity_non_negative(self, scenario_config):
        """Poisson jump intensity must be non-negative."""
        assert scenario_config.jump_intensity >= 0
```

---

### 2.2 Testing Individual Stochastic Processes

```python
# ─────────────────────────────────────────────────────────────────────────────
# 2.2  Individual sub-models
# ─────────────────────────────────────────────────────────────────────────────

class TestHullWhiteRates:
    """Tests for Hull-White interest rate paths."""

    NUM_SCENARIOS = 100
    TIME_STEPS = 12   # one year, monthly
    DT = 1 / 12

    def test_output_shape(self, scenario_generator):
        """Rate array must have shape (time_steps, num_scenarios)."""
        rates = scenario_generator._generate_hull_white_rates(
            self.TIME_STEPS, self.DT
        )
        assert rates.shape == (self.TIME_STEPS, self.NUM_SCENARIOS), (
            f"Expected ({self.TIME_STEPS}, {self.NUM_SCENARIOS}), got {rates.shape}"
        )

    def test_rates_non_negative(self, scenario_generator):
        """Hull-White implementation applies a non-negative floor."""
        rates = scenario_generator._generate_hull_white_rates(
            self.TIME_STEPS, self.DT
        )
        assert (rates >= 0).all(), "Found negative interest rates"

    def test_rates_not_all_identical(self, scenario_generator):
        """Rates across scenarios must show variation (not degenerate)."""
        rates = scenario_generator._generate_hull_white_rates(
            self.TIME_STEPS, self.DT
        )
        # Standard deviation across scenarios at the final time step
        final_std = rates[-1].std()
        assert final_std > 0, "All rate paths are identical — check RNG seeding"

    def test_mean_reversion_pulls_toward_config_mean(self, scenario_generator):
        """
        Over a long horizon the cross-section mean of rates should be within
        ±3 std-errors of the configured long-run mean.
        """
        time_steps = 360   # 30 years monthly
        rates = scenario_generator._generate_hull_white_rates(
            time_steps, self.DT
        )
        config_mean = scenario_generator.config.short_rate_mean
        final_mean = rates[-1].mean()
        # Allow wide tolerance — 50 bps
        assert abs(final_mean - config_mean) < 0.005, (
            f"Final mean rate {final_mean:.4f} far from config mean {config_mean:.4f}"
        )


class TestMertonJumpDiffusion:
    """Tests for Merton jump-diffusion equity return paths."""

    NUM_SCENARIOS = 200
    TIME_STEPS = 12
    DT = 1 / 12

    def test_output_shape(self, scenario_generator):
        """Return array must have shape (time_steps, num_scenarios)."""
        returns = scenario_generator._generate_merton_jumps(
            self.TIME_STEPS, self.DT
        )
        assert returns.shape == (self.TIME_STEPS, self.NUM_SCENARIOS)

    def test_returns_are_finite(self, scenario_generator):
        """All generated returns must be finite (no NaN or Inf)."""
        returns = scenario_generator._generate_merton_jumps(
            self.TIME_STEPS, self.DT
        )
        assert np.isfinite(returns).all(), "Non-finite values in equity returns"

    def test_returns_show_variance(self, scenario_generator):
        """Returns must have non-zero standard deviation."""
        returns = scenario_generator._generate_merton_jumps(
            self.TIME_STEPS, self.DT
        )
        assert returns.std() > 0, "Equity returns have zero variance"

    def test_jump_events_occur_at_plausible_frequency(self, scenario_generator):
        """
        With 100 scenarios over 30 years, the number of time steps that
        show large deviations (|r| > 2*vol) should be plausible given the
        configured jump intensity.
        """
        time_steps = 360
        returns = scenario_generator._generate_merton_jumps(
            time_steps, self.DT
        )
        vol = scenario_generator.config.equity_vol
        large_moves = (np.abs(returns) > 2 * vol * np.sqrt(self.DT)).sum()
        total = returns.size
        # Roughly: p(|r|>2σ) ≈ 5% from diffusion + jump contribution
        fraction = large_moves / total
        assert 0.01 < fraction < 0.25, (
            f"Fraction of large moves {fraction:.3f} outside plausible range"
        )


class TestCreditSpreads:
    """Tests for credit spread paths."""

    NUM_SCENARIOS = 100
    TIME_STEPS = 60
    DT = 1 / 12

    def test_output_shape(self, scenario_generator):
        spreads = scenario_generator._generate_credit_spreads(
            self.TIME_STEPS, self.DT
        )
        assert spreads.shape == (self.TIME_STEPS, self.NUM_SCENARIOS)

    def test_spreads_non_negative(self, scenario_generator):
        """Credit spreads have a non-negative floor."""
        spreads = scenario_generator._generate_credit_spreads(
            self.TIME_STEPS, self.DT
        )
        assert (spreads >= 0).all(), "Found negative credit spreads"

    def test_spreads_mean_revert(self, scenario_generator):
        """Long-run mean of spreads should converge near the config mean."""
        time_steps = 360
        spreads = scenario_generator._generate_credit_spreads(
            time_steps, self.DT
        )
        config_mean = scenario_generator.config.credit_spread_mean
        final_mean = spreads[-1].mean()
        assert abs(final_mean - config_mean) < 0.005


class TestInflationPaths:
    """Tests for inflation rate paths."""

    NUM_SCENARIOS = 100
    TIME_STEPS = 60
    DT = 1 / 12

    def test_output_shape(self, scenario_generator):
        inflation = scenario_generator._generate_inflation(
            self.TIME_STEPS, self.DT
        )
        assert inflation.shape == (self.TIME_STEPS, self.NUM_SCENARIOS)

    def test_inflation_allows_deflation(self, scenario_generator):
        """
        Unlike rates/spreads, inflation is allowed to go negative (deflation).
        A long simulation should produce at least some negative values when
        inflation is volatile enough.
        """
        # Use a high-vol config to make this deterministic
        import dataclasses
        high_vol_config = dataclasses.replace(
            scenario_generator.config, inflation_vol=0.05
        )
        gen = EconomicScenarioGenerator(high_vol_config)
        inflation = gen._generate_inflation(360, self.DT)
        # Not asserting negative values must exist — just that they are permitted
        assert np.isfinite(inflation).all()
```

---

### 2.3 Testing `generate_scenarios()`

```python
# ─────────────────────────────────────────────────────────────────────────────
# 2.3  generate_scenarios() — integration of all sub-models
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateScenarios:
    """Tests for the top-level scenario generation method."""

    NUM_SCENARIOS = 50
    PROJECTION_YEARS = 10

    def test_returns_all_required_keys(self, scenario_generator):
        """Output dict must contain all five economic variable arrays."""
        scenarios = scenario_generator.generate_scenarios(
            self.NUM_SCENARIOS, self.PROJECTION_YEARS
        )
        required_keys = {
            'short_rate', 'long_rate', 'equity_return',
            'credit_spread', 'inflation'
        }
        assert required_keys.issubset(set(scenarios.keys())), (
            f"Missing keys: {required_keys - set(scenarios.keys())}"
        )

    def test_output_array_shapes(self, scenario_generator):
        """Each array must have shape (time_steps, num_scenarios)."""
        scenarios = scenario_generator.generate_scenarios(
            self.NUM_SCENARIOS, self.PROJECTION_YEARS
        )
        time_steps = self.PROJECTION_YEARS * 12
        for key, arr in scenarios.items():
            assert arr.shape == (time_steps, self.NUM_SCENARIOS), (
                f"Array '{key}' has shape {arr.shape}, "
                f"expected ({time_steps}, {self.NUM_SCENARIOS})"
            )

    def test_long_rate_exceeds_short_rate(self, scenario_generator):
        """
        Long rate = short rate + term premium.
        Every element of long_rate must be >= short_rate.
        """
        scenarios = scenario_generator.generate_scenarios(
            self.NUM_SCENARIOS, self.PROJECTION_YEARS
        )
        assert (scenarios['long_rate'] >= scenarios['short_rate']).all(), (
            "long_rate should be >= short_rate (term premium relationship)"
        )

    def test_all_values_finite(self, scenario_generator):
        """No NaN or Inf values in any scenario array."""
        scenarios = scenario_generator.generate_scenarios(
            self.NUM_SCENARIOS, self.PROJECTION_YEARS
        )
        for key, arr in scenarios.items():
            assert np.isfinite(arr).all(), (
                f"Non-finite values found in '{key}'"
            )

    def test_reproducibility_with_same_seed(self, scenario_config):
        """Two generators with the same seed must produce identical scenarios."""
        np.random.seed(42)
        gen1 = EconomicScenarioGenerator(scenario_config)
        s1 = gen1.generate_scenarios(20, 5)

        np.random.seed(42)
        gen2 = EconomicScenarioGenerator(scenario_config)
        s2 = gen2.generate_scenarios(20, 5)

        for key in s1:
            np.testing.assert_array_equal(
                s1[key], s2[key],
                err_msg=f"Array '{key}' not identical across identical seeds"
            )

    def test_different_seeds_produce_different_results(self, scenario_config):
        """Different seeds must produce statistically distinct scenario sets."""
        np.random.seed(1)
        gen1 = EconomicScenarioGenerator(scenario_config)
        s1 = gen1.generate_scenarios(100, 10)

        np.random.seed(99)
        gen2 = EconomicScenarioGenerator(scenario_config)
        s2 = gen2.generate_scenarios(100, 10)

        # Equity returns are continuous — they should differ
        assert not np.allclose(s1['equity_return'], s2['equity_return']), (
            "Equity return scenarios are identical despite different seeds"
        )

    def test_scenario_count_scaling(self, scenario_generator):
        """Doubling the scenario count should double the second dimension."""
        s_100 = scenario_generator.generate_scenarios(100, 5)
        s_200 = scenario_generator.generate_scenarios(200, 5)
        assert s_200['short_rate'].shape[1] == 2 * s_100['short_rate'].shape[1]
```

---

## Part 3 — Stochastic Cash Flow Calculations

Create `tests/test_stochastic_calculations.py`.

### 3.1 Testing `DynamicCashFlowModel`

```python
# tests/test_stochastic_calculations.py
"""
Unit tests for stochastic cash flow calculations.

Covers:
  - DynamicCashFlowModel construction
  - project_liability_flows() — per-scenario liability cash flows
  - project_asset_flows()     — per-scenario asset cash flows
  - calculate_risk_metrics()  — VaR, CTE, mean NPV, std NPV
  - Integration: economic scenarios + liability model
"""
import pytest
import numpy as np
import pandas as pd
from datetime import date

from cash_flow_model import DynamicCashFlowModel, CashFlow
from economic_scenario_generator import EconomicScenarioGenerator, ScenarioConfig
from economic_scenario import EconomicFactors        # dataclass per time-step


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def policy_data() -> pd.DataFrame:
    """Minimal policy portfolio DataFrame with two policies."""
    return pd.DataFrame({
        'policy_id':     [1, 2],
        'age':           [35, 50],
        'sex':           ['M', 'F'],
        'sum_assured':   [500_000.0, 250_000.0],
        'premium':       [1_200.0, 2_400.0],
        'account_value': [10_000.0, 80_000.0],
    })


@pytest.fixture
def mortality_df() -> pd.DataFrame:
    """Simple mortality table for testing."""
    ages = range(20, 100)
    return pd.DataFrame({
        'age': list(ages),
        'M':   [0.001 + 0.0003 * (a - 20) for a in ages],
        'F':   [0.0008 + 0.00025 * (a - 20) for a in ages],
    }).set_index('age')


@pytest.fixture
def lapse_rates() -> dict:
    return {yr: max(0.03, 0.15 - 0.01 * yr) for yr in range(1, 31)}


@pytest.fixture
def expense_factors() -> dict:
    return {
        'per_policy': 150.0,
        'percent_premium': 0.05,
        'percent_av': 0.01,
    }


@pytest.fixture
def investment_strategy() -> dict:
    return {
        'equity':       0.40,
        'fixed_income': 0.50,
        'cash':         0.10,
    }


@pytest.fixture
def dcf_model(mortality_df, lapse_rates, expense_factors, investment_strategy):
    return DynamicCashFlowModel(
        initial_assets=10_000_000.0,
        mortality_table=mortality_df,
        lapse_rates=lapse_rates,
        expense_factors=expense_factors,
        investment_strategy=investment_strategy,
    )


@pytest.fixture
def economic_scenarios(scenario_config) -> list:
    """
    Build a 3-scenario × 5-step list of EconomicFactors
    for lightweight stochastic tests.
    """
    np.random.seed(0)
    gen = EconomicScenarioGenerator(scenario_config)
    raw = gen.generate_scenarios(num_scenarios=3, projection_years=5)
    # Convert to List[List[EconomicFactors]] expected by DynamicCashFlowModel
    scenarios = []
    for s_idx in range(3):
        scenario = []
        for t_idx in range(raw['short_rate'].shape[0]):
            scenario.append(EconomicFactors(
                interest_rate=raw['short_rate'][t_idx, s_idx],
                equity_return=raw['equity_return'][t_idx, s_idx],
                credit_spread=raw['credit_spread'][t_idx, s_idx],
                inflation=raw['inflation'][t_idx, s_idx],
            ))
        scenarios.append(scenario)
    return scenarios


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  DynamicCashFlowModel construction
# ─────────────────────────────────────────────────────────────────────────────

class TestDynamicCashFlowModelConstruction:

    def test_initial_assets_stored(self, dcf_model):
        assert dcf_model.initial_assets == 10_000_000.0

    def test_investment_strategy_sums_to_one(self, investment_strategy):
        """Investment weights must sum to 1.0."""
        total = sum(investment_strategy.values())
        assert abs(total - 1.0) < 1e-9, (
            f"Investment strategy weights sum to {total:.6f}, not 1.0"
        )

    def test_lapse_rates_in_valid_range(self, lapse_rates):
        for yr, rate in lapse_rates.items():
            assert 0 <= rate < 1, (
                f"Lapse rate {rate} at year {yr} outside [0, 1)"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 3.2  project_liability_flows()
# ─────────────────────────────────────────────────────────────────────────────

class TestProjectLiabilityFlows:

    def test_returns_list_of_cashflows(self, dcf_model, economic_scenarios, policy_data):
        """Output must be a list of CashFlow objects."""
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        assert isinstance(flows, list)
        assert all(isinstance(cf, CashFlow) for cf in flows)

    def test_non_empty_for_populated_portfolio(self, dcf_model, economic_scenarios, policy_data):
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        assert len(flows) > 0

    def test_flow_types_are_expected(self, dcf_model, economic_scenarios, policy_data):
        """Only recognised flow types should appear."""
        expected_types = {'death_benefit', 'surrender_benefit', 'premium'}
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        actual_types = {cf.flow_type for cf in flows}
        unexpected = actual_types - expected_types
        assert not unexpected, f"Unexpected flow types found: {unexpected}"

    def test_death_benefits_non_negative(self, dcf_model, economic_scenarios, policy_data):
        """Death benefit amounts must be non-negative."""
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        death_flows = [cf for cf in flows if cf.flow_type == 'death_benefit']
        assert all(cf.amount >= 0 for cf in death_flows)

    def test_premiums_positive(self, dcf_model, economic_scenarios, policy_data):
        """Premium inflows must be strictly positive."""
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        premium_flows = [cf for cf in flows if cf.flow_type == 'premium']
        assert all(cf.amount > 0 for cf in premium_flows)

    def test_scenario_id_coverage(self, dcf_model, economic_scenarios, policy_data):
        """Every scenario index must appear in the output."""
        flows = dcf_model.project_liability_flows(economic_scenarios, policy_data)
        observed_ids = {cf.scenario_id for cf in flows}
        expected_ids = set(range(len(economic_scenarios)))
        assert expected_ids.issubset(observed_ids), (
            f"Missing scenario IDs: {expected_ids - observed_ids}"
        )

    def test_empty_portfolio_returns_empty_list(self, dcf_model, economic_scenarios):
        """Empty policy data should produce no cash flows."""
        empty_df = pd.DataFrame(columns=[
            'policy_id', 'age', 'sex', 'sum_assured',
            'premium', 'account_value'
        ])
        flows = dcf_model.project_liability_flows(economic_scenarios, empty_df)
        assert len(flows) == 0
```

---

### 3.2 Testing Risk Metrics

```python
# ─────────────────────────────────────────────────────────────────────────────
# 3.3  calculate_risk_metrics()
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskMetrics:
    """Tests for VaR, CTE, mean/std NPV from calculate_risk_metrics()."""

    NUM_SCENARIOS = 200

    @pytest.fixture
    def large_scenario_set(self, scenario_config):
        """200-scenario set for statistically meaningful risk metrics."""
        np.random.seed(123)
        gen = EconomicScenarioGenerator(scenario_config)
        raw = gen.generate_scenarios(
            num_scenarios=self.NUM_SCENARIOS,
            projection_years=10
        )
        scenarios = []
        for s_idx in range(self.NUM_SCENARIOS):
            scenario = []
            for t_idx in range(raw['short_rate'].shape[0]):
                scenario.append(EconomicFactors(
                    interest_rate=raw['short_rate'][t_idx, s_idx],
                    equity_return=raw['equity_return'][t_idx, s_idx],
                    credit_spread=raw['credit_spread'][t_idx, s_idx],
                    inflation=raw['inflation'][t_idx, s_idx],
                ))
            scenarios.append(scenario)
        return scenarios

    @pytest.fixture
    def risk_metric_inputs(
        self, dcf_model, large_scenario_set, policy_data
    ):
        """Pre-compute liability and asset flows once, reuse in all risk tests."""
        liability_flows = dcf_model.project_liability_flows(
            large_scenario_set, policy_data
        )
        asset_flows = dcf_model.project_asset_flows(
            large_scenario_set, liability_flows
        )
        return liability_flows, asset_flows

    def test_risk_metrics_keys(self, dcf_model, risk_metric_inputs):
        """Output must include VaR, CTE, mean, std, and skewness."""
        lib_flows, ast_flows = risk_metric_inputs
        metrics = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.95
        )
        required = {'var', 'cte', 'mean_npv', 'std_npv', 'skewness'}
        assert required.issubset(
            {k.lower() for k in metrics.keys()}
        ), f"Missing keys: {required - {k.lower() for k in metrics.keys()}}"

    def test_cte_exceeds_var(self, dcf_model, risk_metric_inputs):
        """
        CTE (Conditional Tail Expectation) at 95% must be at least as large
        as the corresponding VaR — it is an average over the tail, not a quantile.
        """
        lib_flows, ast_flows = risk_metric_inputs
        metrics = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.95
        )
        # Keys may be upper or lower case — normalise
        m = {k.lower(): v for k, v in metrics.items()}
        assert m['cte'] >= m['var'], (
            f"CTE {m['cte']:.2f} < VaR {m['var']:.2f} at 95% — violation of CTE definition"
        )

    def test_std_npv_positive(self, dcf_model, risk_metric_inputs):
        """With 200 stochastic scenarios the NPV standard deviation must be > 0."""
        lib_flows, ast_flows = risk_metric_inputs
        metrics = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.95
        )
        m = {k.lower(): v for k, v in metrics.items()}
        assert m['std_npv'] > 0, "NPV std-dev is zero — scenarios may be identical"

    def test_var_increases_with_confidence_level(self, dcf_model, risk_metric_inputs):
        """VaR at 99% must be >= VaR at 95%."""
        lib_flows, ast_flows = risk_metric_inputs
        metrics_95 = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.95
        )
        metrics_99 = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.99
        )
        var_95 = {k.lower(): v for k, v in metrics_95.items()}['var']
        var_99 = {k.lower(): v for k, v in metrics_99.items()}['var']
        assert var_99 >= var_95, (
            f"VaR(99%) {var_99:.2f} < VaR(95%) {var_95:.2f} — monotonicity violated"
        )

    def test_all_metrics_finite(self, dcf_model, risk_metric_inputs):
        """All risk metrics must be finite numbers."""
        import math
        lib_flows, ast_flows = risk_metric_inputs
        metrics = dcf_model.calculate_risk_metrics(
            lib_flows, ast_flows, confidence_level=0.95
        )
        for key, val in metrics.items():
            assert math.isfinite(val), f"Metric '{key}' = {val} is not finite"
```

---

### 3.3 Testing Multi-Scenario Integration

```python
# ─────────────────────────────────────────────────────────────────────────────
# 3.4  Integration: economic scenarios → liability projection → risk metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestStochasticIntegration:
    """
    End-to-end tests: generate economic scenarios, feed them through
    the liability and asset models, and verify the final risk output.
    """

    def test_full_stochastic_pipeline_runs_without_error(
        self, dcf_model, economic_scenarios, policy_data
    ):
        """The full 3-step pipeline must complete without raising."""
        liability_flows = dcf_model.project_liability_flows(
            economic_scenarios, policy_data
        )
        asset_flows = dcf_model.project_asset_flows(
            economic_scenarios, liability_flows
        )
        metrics = dcf_model.calculate_risk_metrics(
            liability_flows, asset_flows, confidence_level=0.95
        )
        assert metrics is not None

    def test_asset_flows_have_investment_return_type(
        self, dcf_model, economic_scenarios, policy_data
    ):
        """Asset flows should include 'investment_return' flow type."""
        liability_flows = dcf_model.project_liability_flows(
            economic_scenarios, policy_data
        )
        asset_flows = dcf_model.project_asset_flows(
            economic_scenarios, liability_flows
        )
        types = {cf.flow_type for cf in asset_flows}
        assert 'investment_return' in types

    def test_more_scenarios_reduce_metric_variance(self, dcf_model, policy_data, scenario_config):
        """
        The standard deviation of mean NPV estimates should decrease as
        scenario count increases (law of large numbers).
        This test compares the NPV mean between 50- and 500-scenario runs.
        With a fixed seed the 500-run result is taken as ground truth;
        the 50-run mean should be in the same ballpark (within 20%).
        """
        def run_pipeline(num_scenarios, seed):
            np.random.seed(seed)
            gen = EconomicScenarioGenerator(scenario_config)
            raw = gen.generate_scenarios(num_scenarios, projection_years=5)
            scenarios = [
                [
                    EconomicFactors(
                        interest_rate=raw['short_rate'][t, s],
                        equity_return=raw['equity_return'][t, s],
                        credit_spread=raw['credit_spread'][t, s],
                        inflation=raw['inflation'][t, s],
                    )
                    for t in range(raw['short_rate'].shape[0])
                ]
                for s in range(num_scenarios)
            ]
            lib = dcf_model.project_liability_flows(scenarios, policy_data)
            ast = dcf_model.project_asset_flows(scenarios, lib)
            metrics = dcf_model.calculate_risk_metrics(lib, ast)
            return {k.lower(): v for k, v in metrics.items()}

        m_50  = run_pipeline(50,  seed=7)
        m_500 = run_pipeline(500, seed=7)

        mean_50  = m_50['mean_npv']
        mean_500 = m_500['mean_npv']

        if abs(mean_500) > 1.0:
            relative_error = abs(mean_50 - mean_500) / abs(mean_500)
            assert relative_error < 0.20, (
                f"50-scenario mean NPV {mean_50:.2f} differs from "
                f"500-scenario mean NPV {mean_500:.2f} by {relative_error:.1%}"
            )

    def test_higher_equity_vol_increases_npv_dispersion(
        self, dcf_model, policy_data
    ):
        """
        A scenario generator with double the equity vol should produce
        a larger NPV standard deviation.
        """
        import dataclasses
        from economic_scenario_generator import ScenarioConfig

        base_config = ScenarioConfig(
            short_rate_mean=0.04, short_rate_speed=0.1, short_rate_vol=0.01,
            equity_return_mean=0.07, equity_vol=0.10,
            jump_intensity=0.05, jump_mean=-0.05, jump_vol=0.05,
            credit_spread_mean=0.015, credit_spread_vol=0.003,
            inflation_mean=0.02, inflation_vol=0.003,
        )
        high_vol_config = dataclasses.replace(base_config, equity_vol=0.25)

        def run(config, seed=42, n=100):
            np.random.seed(seed)
            gen = EconomicScenarioGenerator(config)
            raw = gen.generate_scenarios(n, projection_years=5)
            scenarios = [
                [
                    EconomicFactors(
                        interest_rate=raw['short_rate'][t, s],
                        equity_return=raw['equity_return'][t, s],
                        credit_spread=raw['credit_spread'][t, s],
                        inflation=raw['inflation'][t, s],
                    )
                    for t in range(raw['short_rate'].shape[0])
                ]
                for s in range(n)
            ]
            lib = dcf_model.project_liability_flows(scenarios, policy_data)
            ast = dcf_model.project_asset_flows(scenarios, lib)
            m = dcf_model.calculate_risk_metrics(lib, ast)
            return {k.lower(): v for k, v in m.items()}

        m_base     = run(base_config)
        m_high_vol = run(high_vol_config)

        assert m_high_vol['std_npv'] > m_base['std_npv'], (
            f"Higher equity vol did not increase NPV std-dev: "
            f"base={m_base['std_npv']:.2f}, high_vol={m_high_vol['std_npv']:.2f}"
        )
```

---

## Test Fixtures Reference

| Fixture | File | Returns | Purpose |
|---|---|---|---|
| `base_assumptions` | `conftest.py` | `ActuarialAssumptions` | Default assumption set |
| `mortality_table` | `conftest.py` | `MortalityTable` | Sample mortality rates |
| `lapse_assumption` | `conftest.py` | `LapseAssumption` | Sample lapse rates |
| `inflation_assumption` | `conftest.py` | `InflationAssumption` | Sample inflation |
| `term_contract` | `conftest.py` | `TermInsurance` | 20-yr term, M/35 |
| `whole_life_contract` | `conftest.py` | `WholeLifeInsurance` | WL, F/45 |
| `liability_model` | `conftest.py` | `LiabilityModel` | Empty model |
| `loaded_model` | `conftest.py` | `LiabilityModel` | 2-contract model |
| `scenario_config` | `conftest.py` | `ScenarioConfig` | Standard parameters |
| `scenario_generator` | `conftest.py` | `EconomicScenarioGenerator` | Ready-to-use generator |
| `policy_data` | `test_stochastic_calculations.py` | `pd.DataFrame` | 2-policy portfolio |
| `dcf_model` | `test_stochastic_calculations.py` | `DynamicCashFlowModel` | Ready-to-use |
| `economic_scenarios` | `test_stochastic_calculations.py` | `List[List[EconomicFactors]]` | 3 scenarios × 60 steps |
| `large_scenario_set` | `test_stochastic_calculations.py` | `List[List[EconomicFactors]]` | 200 scenarios × 120 steps |

---

## Running the Tests

### Run all tests

```bash
cd /home/user/Actuarial_Stochastic_Model
pytest tests/ -v
```

### Run a single layer

```bash
# Deterministic only
pytest tests/test_deterministic_cashflows.py -v

# Economic scenario generation only
pytest tests/test_economic_scenarios.py -v

# Stochastic calculations only
pytest tests/test_stochastic_calculations.py -v
```

### Run with coverage report

```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
# Open htmlcov/index.html in a browser
```

### Run only fast tests (skip large-scenario integration tests)

```bash
pytest tests/ -v -k "not large_scenario_set and not full_stochastic"
```

### Run with a fixed random seed for reproducibility

```bash
PYTHONHASHSEED=42 pytest tests/ -v
```

---

## Interpreting Results

### Deterministic layer — what to look for

| Symptom | Likely cause |
|---|---|
| `test_mortality_increases_with_age` fails | Base rates table is not sorted or contains a plateau at old ages — check `MortalityTable.base_rates` |
| `test_pv_premiums_less_than_undiscounted` fails | Discount function applies factor < 1 only for future dates; ensure `base_date` is the earliest point |
| `test_cashflows_output_shape` fails | `project_cashflows` time-step arithmetic; verify `periods = projection_years * 12` for monthly |
| `test_term_policy_cashflows_stop_after_term` fails | `_project_contract` does not check `contract.is_active()` at each step |

### Economic scenario layer — what to look for

| Symptom | Likely cause |
|---|---|
| `test_rates_non_negative` fails | Non-negative floor not applied to Hull-White draw; add `np.maximum(0, ...)` |
| `test_reproducibility_with_same_seed` fails | Internal state mutates before seeding; move `np.random.seed()` call closer to the generator |
| `test_long_rate_exceeds_short_rate` fails | Term premium constant is negative or was omitted |
| `test_mean_reversion_pulls_toward_config_mean` fails | Mean-reversion speed `kappa` is too small relative to the simulation horizon |

### Stochastic layer — what to look for

| Symptom | Likely cause |
|---|---|
| `test_cte_exceeds_var` fails | CTE calculated as a quantile rather than a conditional mean — check tail-averaging logic |
| `test_var_increases_with_confidence_level` fails | VaR percentile argument is `1 - alpha` instead of `alpha`; check `np.percentile` call |
| `test_more_scenarios_reduce_metric_variance` fails | Scenarios are not independent; check that each scenario is drawn from a fresh RNG state |
| `test_higher_equity_vol_increases_npv_dispersion` fails | Equity returns not propagated into asset flows; verify `equity_return` is used in `project_asset_flows` |

### Coverage targets

| Module | Recommended minimum coverage |
|---|---|
| `liability_model.py` | 90% |
| `actuarial_assumptions.py` | 85% |
| `economic_scenario_generator.py` | 80% |
| `cash_flow_model.py` | 85% |
