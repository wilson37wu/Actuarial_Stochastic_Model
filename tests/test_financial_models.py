"""
Tests for financial models.
"""
import pytest
import numpy as np
from src.financial_models import (
    ModelParameters,
    HullWhiteModel,
    JarrowTurnbullModel,
    MertonCreditModel,
    HestonModel,
    MertonJumpDiffusionModel,
    ALMEngine
)

@pytest.fixture
def model_params():
    """Create test model parameters."""
    return ModelParameters()

@pytest.fixture
def alm_engine(model_params):
    """Create test ALM engine."""
    return ALMEngine(model_params)

def test_hull_white_model():
    """Test Hull-White interest rate model."""
    model = HullWhiteModel(a=0.1, sigma=0.02)
    rates = model.simulate(r0=0.03, theta=0.04, T=1.0, dt=0.1)
    
    assert len(rates) == 10
    assert rates[0] == 0.03
    assert all(isinstance(r, float) for r in rates)

def test_jarrow_turnbull_model():
    """Test Jarrow-Turnbull credit model."""
    model = JarrowTurnbullModel(intensity=0.02)
    price = model.price(face_value=100.0, T=1.0, r=0.03)
    
    assert isinstance(price, float)
    assert 0 < price < 100.0
    
    survival_prob = model.survival_probability(T=1.0)
    assert 0 < survival_prob < 1.0

def test_merton_credit_model():
    """Test Merton structural credit model."""
    model = MertonCreditModel(
        asset_value=100.0,
        asset_volatility=0.2,
        debt=80.0,
        r=0.03
    )
    
    spread = model.credit_spread(T=1.0)
    assert isinstance(spread, float)
    assert spread > 0
    
    default_prob = model.default_probability(T=1.0)
    assert 0 < default_prob < 1.0

def test_heston_model():
    """Test Heston stochastic volatility model."""
    model = HestonModel(
        S0=100.0,
        v0=0.04,
        kappa=2.0,
        theta=0.04,
        xi=0.3,
        rho=-0.7
    )
    
    prices, variances = model.simulate(T=1.0, dt=0.1)
    
    assert len(prices) == len(variances) == 10
    assert prices[0] == 100.0
    assert variances[0] == 0.04
    assert all(v >= 0 for v in variances)
    assert all(p > 0 for p in prices)

def test_merton_jump_diffusion():
    """Test Merton jump-diffusion model."""
    model = MertonJumpDiffusionModel(
        S0=100.0,
        sigma=0.15,
        r=0.03,
        jump_intensity=0.1,
        jump_mean=-0.2,
        jump_std=0.2
    )
    
    prices = model.simulate(T=1.0, dt=0.1)
    
    assert len(prices) == 10
    assert prices[0] == 100.0
    assert all(p > 0 for p in prices)

def test_alm_engine(alm_engine):
    """Test ALM engine scenario generation."""
    # Test single scenario
    scenario = alm_engine.simulate_scenario(T=1.0, dt=0.1)
    
    assert isinstance(scenario, dict)
    assert all(key in scenario for key in [
        'interest_rates',
        'credit_spreads',
        'equity_prices_heston',
        'equity_prices_jump',
        'equity_variances'
    ])
    assert all(len(arr) == 10 for arr in scenario.values())
    
    # Test multiple scenarios
    scenarios = alm_engine.simulate_multiple_scenarios(
        num_scenarios=5,
        T=1.0,
        dt=0.1
    )
    
    assert isinstance(scenarios, dict)
    assert all(arr.shape == (5, 10) for arr in scenarios.values())

def test_model_parameters():
    """Test model parameters dataclass."""
    params = ModelParameters()
    
    assert params.mean_reversion_speed > 0
    assert params.rate_volatility > 0
    assert params.initial_rate >= 0
    assert params.equity_volatility > 0
    assert params.jump_intensity >= 0
