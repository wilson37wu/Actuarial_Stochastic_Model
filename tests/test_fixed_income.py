import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.fixed_income import Bond, FixedIncomeModel

@pytest.fixture
def sample_bond():
    return Bond(
        id="BOND001",
        par_value=1000000.0,
        coupon_rate=0.05,  # 5% annual coupon
        maturity_date=date.today() + timedelta(days=365*5),  # 5-year bond
        payment_frequency=2,  # Semi-annual payments
        credit_rating="AA",
        issue_date=date.today(),
        purchase_price=1000000.0
    )

@pytest.fixture
def fixed_income_model():
    config = {
        'credit_transition_matrix': None,  # Using default matrix
        'recovery_rates': None  # Using default rates
    }
    return FixedIncomeModel(config)

@pytest.fixture
def scenario_rates():
    dates = pd.date_range(start=date.today(), periods=60, freq='M')
    rates = pd.DataFrame({
        'risk_free_rate': np.linspace(0.02, 0.04, 60),
        'credit_spread': np.linspace(0.001, 0.002, 60)
    }, index=dates)
    return rates

def test_bond_cashflow_projection(sample_bond, fixed_income_model, scenario_rates):
    # Project cash flows
    projection_dates = scenario_rates.index.date.tolist()
    cashflows = fixed_income_model.project_cashflows(
        sample_bond,
        projection_dates,
        scenario_rates
    )
    
    # Basic validation checks
    assert not cashflows.empty, "Cashflow projection should not be empty"
    assert all(cf >= 0 for cf in cashflows['coupon']), "Coupon payments should be non-negative"
    assert all(cf >= 0 for cf in cashflows['principal']), "Principal payments should be non-negative"
    
    # Check number of coupon payments
    expected_payments = sample_bond.payment_frequency * 5  # 5 years * 2 payments per year
    actual_payments = len(cashflows[cashflows['coupon'] > 0])
    assert actual_payments == expected_payments, f"Expected {expected_payments} payments, got {actual_payments}"

def test_duration_calculation(sample_bond, fixed_income_model):
    yield_rate = 0.05  # 5% yield
    duration = fixed_income_model.calculate_duration(sample_bond, yield_rate)
    
    # For a 5-year bond with 5% coupon and 5% yield, duration should be around 4.5 years
    assert 4.0 <= duration <= 5.0, f"Duration {duration} outside expected range"

def test_convexity_calculation(sample_bond, fixed_income_model):
    yield_rate = 0.05  # 5% yield
    convexity = fixed_income_model.calculate_convexity(sample_bond, yield_rate)
    
    # Convexity should be positive
    assert convexity > 0, "Convexity should be positive"
    
def test_credit_risk_impact(sample_bond, fixed_income_model, scenario_rates):
    # Project cash flows for different credit ratings
    sample_bond.credit_rating = "AAA"
    cf_aaa = fixed_income_model.project_cashflows(
        sample_bond,
        scenario_rates.index.date.tolist(),
        scenario_rates
    )
    
    sample_bond.credit_rating = "B"
    cf_b = fixed_income_model.project_cashflows(
        sample_bond,
        scenario_rates.index.date.tolist(),
        scenario_rates
    )
    
    # Lower rated bond should have lower cash flows due to higher credit risk
    assert cf_aaa['coupon'].sum() > cf_b['coupon'].sum(), \
        "AAA-rated bond should have higher cash flows than B-rated bond"
