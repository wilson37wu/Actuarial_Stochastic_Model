import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from investment import InvestmentAssumptions, InvestmentPortfolio, PortfolioType

def main():
    st.set_page_config(page_title="Investment Portfolio Dashboard", layout="wide")
    
    st.title("Investment Portfolio Analysis Dashboard")
    
    # Initialize assumptions
    assumptions = InvestmentAssumptions()
    
    # Sidebar for portfolio configuration
    st.sidebar.header("Portfolio Configuration")
    
    portfolio_type = st.sidebar.selectbox(
        "Select Portfolio Type",
        options=[pt.value for pt in PortfolioType],
        format_func=lambda x: x.title()
    )
    
    initial_balance = st.sidebar.number_input(
        "Initial Investment ($)",
        min_value=1000.0,
        max_value=10000000.0,
        value=1000000.0,
        step=10000.0,
        format="%.2f"
    )
    
    # Create portfolio
    portfolio = InvestmentPortfolio(
        portfolio_type=PortfolioType(portfolio_type),
        initial_balance=initial_balance,
        assumptions=assumptions
    )
    
    # Display portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Expected Return",
            f"{portfolio.calculate_expected_return():.1%}"
        )
    
    with col2:
        st.metric(
            "Portfolio Volatility",
            f"{portfolio.calculate_volatility():.1%}"
        )
    
    with col3:
        st.metric(
            "Sharpe Ratio",
            f"{portfolio.calculate_sharpe_ratio():.2f}"
        )
    
    with col4:
        st.metric(
            "95% VaR",
            f"${portfolio.calculate_var(0.95):,.0f}"
        )
    
    # Display asset allocation
    st.header("Asset Allocation")
    
    allocation_data = []
    for asset, holding in portfolio.holdings.items():
        weight = holding['amount'] / portfolio.balance
        allocation_data.append({
            'Asset': asset.replace('_', ' ').title(),
            'Amount': holding['amount'],
            'Weight': weight
        })
    
    allocation_df = pd.DataFrame(allocation_data)
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            allocation_df.style.format({
                'Amount': '${:,.2f}',
                'Weight': '{:.1%}'
            }),
            use_container_width=True
        )
    
    with col2:
        st.bar_chart(
            allocation_df.set_index('Asset')['Weight'],
            use_container_width=True
        )
    
    # Market Assumptions
    st.header("Market Assumptions")
    
    market_data = []
    for asset in portfolio.holdings.keys():
        assumption = assumptions.get_market_assumption(asset)
        market_data.append({
            'Asset': asset.replace('_', ' ').title(),
            'Expected Return': assumption['return'],
            'Volatility': assumption['volatility']
        })
    
    market_df = pd.DataFrame(market_data)
    st.dataframe(
        market_df.style.format({
            'Expected Return': '{:.1%}',
            'Volatility': '{:.1%}'
        }),
        use_container_width=True
    )
    
    # Trading Costs
    st.header("Trading Costs")
    
    trading_data = []
    for asset in portfolio.holdings.keys():
        cost = assumptions.get_trading_cost(asset)
        trading_data.append({
            'Asset': asset.replace('_', ' ').title(),
            'Fixed Cost': cost.fixed_cost,
            'Variable Cost': cost.variable_cost,
            'Minimum Cost': cost.minimum_cost,
            'Maximum Cost': cost.maximum_cost
        })
    
    trading_df = pd.DataFrame(trading_data)
    st.dataframe(
        trading_df.style.format({
            'Fixed Cost': '{:.4%}',
            'Variable Cost': '{:.4%}',
            'Minimum Cost': '${:,.2f}',
            'Maximum Cost': '${:,.2f}'
        }),
        use_container_width=True
    )
    
    # Rebalancing Rules
    st.header("Rebalancing Rules")
    rule = assumptions.get_rebalancing_rule(portfolio_type)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Frequency", rule['rebalancing_frequency'].title())
    
    with col2:
        st.metric("Threshold Type", rule['threshold_type'].title())
    
    with col3:
        st.metric("Threshold Value", f"{rule['threshold_value']:.1%}")

if __name__ == "__main__":
    main()
