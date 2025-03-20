import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import date, timedelta
from src.public_equity import Equity, EquityModel
from src.fixed_income import Bond, FixedIncomeModel
from src.asset_model import AssetModel

def create_sample_scenarios(start_date: date, periods: int = 1200) -> pd.DataFrame:
    """Create sample economic scenarios for testing.
    
    This function generates a DataFrame of simulated monthly economic scenarios containing:
    - Equity returns: Monthly returns with 8% annual mean return and 20% annual volatility
    - Risk-free rates: Monthly rates with 3% annual mean and 10% annual volatility
    
    The two series have a correlation of 0.3.
    
    Args:
        start_date: The start date for the scenario projections
        periods: Number of monthly periods to generate (default 1200 = 100 years)
        
    Returns:
        DataFrame with columns 'equity_return' and 'risk_free_rate' indexed by date
    """
    dates = pd.date_range(start=start_date, periods=periods, freq='M')
    np.random.seed(42)  # For reproducibility
    
    # Generate correlated market returns and risk-free rates
    correlation = 0.3
    cov_matrix = np.array([[0.04, correlation * 0.04 * 0.01],  # 0.04 = (20% volatility)^2 
                          [correlation * 0.04 * 0.01, 0.01]])   # 0.01 = (10% volatility)^2
    
    returns = np.random.multivariate_normal(
        mean=[0.08/12, 0.03/12],  # Monthly mean returns (8% and 3% annual)
        cov=cov_matrix/12,        # Monthly covariance (divide annual by 12)
        size=periods
    )
    
    scenarios = pd.DataFrame({
        'equity_return': returns[:, 0],
        'risk_free_rate': returns[:, 1]
    }, index=dates)
    
    return scenarios
def create_sample_portfolio() -> tuple[list[Bond], list[Equity]]:
    """Create a sample mixed portfolio of bonds and equities."""
    today = date.today()
    
    # Create sample bonds
    bonds = [
        Bond(
            id="GOVT_10Y",
            par_value=1000000.0,
            coupon_rate=0.035,
            maturity_date=today + timedelta(days=3650),  # 10-year bond
            payment_frequency=2,  # Semi-annual
            credit_rating="AAA",
            issue_date=today,
            purchase_price=1000000.0
        ),
        Bond(
            id="CORP_5Y",
            par_value=500000.0,
            coupon_rate=0.045,
            maturity_date=today + timedelta(days=1825),  # 5-year bond
            payment_frequency=2,  # Semi-annual
            credit_rating="AA",
            issue_date=today,
            purchase_price=500000.0
        )
    ]
    
    # Create sample equities
    equities = [
        Equity(
            id="AAPL",
            quantity=1000,
            initial_price=150.0,
            dividend_yield=0.006,
            beta=1.2,
            sector="Technology",
            purchase_date=today
        ),
        Equity(
            id="JPM",
            quantity=500,
            initial_price=140.0,
            dividend_yield=0.028,
            beta=1.1,
            sector="Financial",
            purchase_date=today
        ),
        Equity(
            id="JNJ",
            quantity=750,
            initial_price=160.0,
            dividend_yield=0.025,
            beta=0.8,
            sector="Healthcare",
            purchase_date=today
        )
    ]
    
    return bonds, equities

def main():
    # Initialize configuration
    config = {
        'equity': {
            'market_volatility': 0.15,
            'sector_correlations': {
                'Technology': {'Technology': 1.0, 'Financial': 0.6, 'Healthcare': 0.4},
                'Financial': {'Technology': 0.6, 'Financial': 1.0, 'Healthcare': 0.5},
                'Healthcare': {'Technology': 0.4, 'Financial': 0.5, 'Healthcare': 1.0}
            }
        },
        'fixed_income': {
            'credit_spread': {
                'AAA': 0.001,
                'AA': 0.002,
                'A': 0.003
            }
        }
    }
    
    # Create models
    asset_model = AssetModel(config)
    
    # Create sample data
    valuation_date = date.today()
    scenarios = create_sample_scenarios(valuation_date)
    bonds, equities = create_sample_portfolio()
    
    # Set economic scenarios
    asset_model.set_economic_scenarios(scenarios)
    
    # Project portfolio with different parameters
    print("\nProjecting portfolio...")
    
    # Monthly projection for 5 years
    monthly_results = asset_model.project_portfolio(
        bonds=bonds,
        equities=equities,
        valuation_date=valuation_date,
        scenario_idx=0,
        projection_years=5,
        frequency='monthly',
        output_path='portfolio_projection_monthly.xlsx'
    )
    
    # Annual projection for 30 years
    annual_results = asset_model.project_portfolio(
        bonds=bonds,
        equities=equities,
        valuation_date=valuation_date,
        scenario_idx=0,
        projection_years=30,
        frequency='annual',
        output_path='portfolio_projection_annual.xlsx'
    )
    
    # Print summary statistics
    print("\nMonthly Projection Summary (5 years):")
    print("-" * 50)
    monthly_summary = monthly_results['portfolio_cf'].groupby('asset_type').agg({
        'market_value': ['mean', 'std'],
        'total_return': 'mean'
    })
    print(monthly_summary)
    
    print("\nAnnual Projection Summary (30 years):")
    print("-" * 50)
    annual_summary = annual_results['portfolio_cf'].groupby('asset_type').agg({
        'market_value': ['mean', 'std'],
        'total_return': 'mean'
    })
    print(annual_summary)
    
    print("\nResults have been exported to:")
    print("1. portfolio_projection_monthly.xlsx (5-year monthly projection)")
    print("2. portfolio_projection_annual.xlsx (30-year annual projection)")

if __name__ == "__main__":
    main()
