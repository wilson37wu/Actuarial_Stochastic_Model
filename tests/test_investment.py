import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

import pandas as pd
import numpy as np
from investment import InvestmentAssumptions, InvestmentPortfolio, PortfolioType

def test_investment_system():
    # Initialize assumptions
    assumptions = InvestmentAssumptions()
    
    # Test portfolio creation
    initial_balance = 1000000  # $1M initial investment
    portfolio = InvestmentPortfolio(
        portfolio_type=PortfolioType.BALANCED,
        initial_balance=initial_balance,
        assumptions=assumptions
    )
    
    print("\n=== Initial Portfolio State ===")
    print(f"Portfolio Type: {portfolio.portfolio_type}")
    print(f"Initial Balance: ${portfolio.balance:,.2f}")
    print("\nInitial Holdings:")
    for asset, holding in portfolio.holdings.items():
        weight = holding['amount'] / portfolio.balance
        print(f"{asset}: ${holding['amount']:,.2f} ({weight:.1%})")
    
    # Test portfolio metrics
    print("\n=== Portfolio Metrics ===")
    exp_return = portfolio.calculate_expected_return()
    volatility = portfolio.calculate_volatility()
    sharpe = portfolio.calculate_sharpe_ratio()
    var_95 = portfolio.calculate_var(0.95)
    
    print(f"Expected Return: {exp_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"95% VaR: ${var_95:,.2f}")
    
    # Test rebalancing
    print("\n=== Testing Rebalancing ===")
    # Simulate market movement
    market_returns = {
        'government_bonds': -0.02,
        'corporate_bonds': 0.03,
        'public_equity': 0.15
    }
    
    # Update portfolio with market returns
    portfolio.update_performance(pd.Timestamp.now(), market_returns)
    
    print("\nHoldings After Market Movement:")
    for asset, holding in portfolio.holdings.items():
        weight = holding['amount'] / portfolio.balance
        print(f"{asset}: ${holding['amount']:,.2f} ({weight:.1%})")
    
    # Perform rebalancing
    did_rebalance = portfolio.rebalance()
    
    print("\nHoldings After Rebalancing:")
    print(f"Rebalancing performed: {did_rebalance}")
    for asset, holding in portfolio.holdings.items():
        weight = holding['amount'] / portfolio.balance
        print(f"{asset}: ${holding['amount']:,.2f} ({weight:.1%})")
    
    if portfolio.rebalancing_history:
        last_rebalance = portfolio.rebalancing_history[-1]
        print("\nRebalancing Details:")
        print(f"Total Trading Cost: ${last_rebalance['total_cost']:,.2f}")
        print("\nTrades:")
        for asset, trade in last_rebalance['trades'].items():
            print(f"{asset}: ${trade['amount']:,.2f} (Cost: ${trade['cost']:,.2f})")

if __name__ == '__main__':
    test_investment_system()
