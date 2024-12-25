import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import date, timedelta
from src.public_equity import Equity, EquityModel
from src.asset_model import AssetModel

def create_sample_scenarios(start_date: date, periods: int = 60) -> pd.DataFrame:
    """Create sample economic scenarios for testing."""
    dates = pd.date_range(start=start_date, periods=periods, freq='M')
    np.random.seed(42)  # For reproducibility
    
    # Generate correlated market returns and risk-free rates
    correlation = 0.3
    cov_matrix = np.array([[0.04, correlation * 0.04 * 0.01],
                          [correlation * 0.04 * 0.01, 0.01]])
    
    returns = np.random.multivariate_normal(
        mean=[0.08/12, 0.03/12],  # Monthly mean returns
        cov=cov_matrix/12,        # Monthly covariance
        size=periods
    )
    
    scenarios = pd.DataFrame({
        'equity_return': returns[:, 0],
        'risk_free_rate': returns[:, 1]
    }, index=dates)
    
    return scenarios

def create_sample_portfolio() -> list[Equity]:
    """Create a sample equity portfolio."""
    today = date.today()
    
    return [
        Equity(
            id="AAPL",
            quantity=100,
            initial_price=150.0,
            dividend_yield=0.006,
            beta=1.2,
            sector="Technology",
            purchase_date=today
        ),
        Equity(
            id="JPM",
            quantity=50,
            initial_price=140.0,
            dividend_yield=0.028,
            beta=1.1,
            sector="Financial",
            purchase_date=today
        ),
        Equity(
            id="JNJ",
            quantity=75,
            initial_price=160.0,
            dividend_yield=0.025,
            beta=0.8,
            sector="Healthcare",
            purchase_date=today
        )
    ]

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
        }
    }
    
    # Create models
    asset_model = AssetModel(config)
    
    # Create sample data
    start_date = date.today()
    scenarios = create_sample_scenarios(start_date)
    portfolio = create_sample_portfolio()
    
    # Set economic scenarios
    asset_model.set_economic_scenarios(scenarios)
    
    # Project equity portfolio
    projections = asset_model.project_equity(portfolio, scenario_idx=0)
    
    # Calculate and display some analytics
    print("\nPortfolio Projections Summary:")
    print("-" * 50)
    
    # Summary by equity position
    summary = projections.groupby('instrument_id').agg({
        'market_value': ['first', 'last', 'mean', 'std'],
        'dividend_amount': 'sum',
        'total_return': 'last'
    })
    
    print("\nPosition-level metrics:")
    print(summary)
    
    # Portfolio-level metrics
    print("\nPortfolio-level metrics:")
    portfolio_value = projections.groupby('date')['market_value'].sum()
    portfolio_dividends = projections.groupby('date')['dividend_amount'].sum()
    
    print(f"Initial Portfolio Value: ${portfolio_value.iloc[0]:,.2f}")
    print(f"Final Portfolio Value: ${portfolio_value.iloc[-1]:,.2f}")
    print(f"Total Dividends Received: ${portfolio_dividends.sum():,.2f}")
    print(f"Portfolio Volatility (Monthly): {portfolio_value.pct_change().std()*100:.2f}%")
    
    # Calculate correlation between positions
    position_returns = projections.pivot(
        index='date',
        columns='instrument_id',
        values='total_return'
    )
    
    print("\nPosition Correlations:")
    print(position_returns.corr())

if __name__ == "__main__":
    main()
