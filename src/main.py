"""
Main entry point for the Actuarial Stochastic Model.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path

from economic_scenario import EconomicScenarioGenerator
from cash_flow_model import DynamicCashFlowModel
from dashboard_components.cash_flow_analysis import render_cash_flow_analysis
from dashboard_components.gcv_analysis import render_controls as render_gcv_controls
from dashboard_components.financial_analysis import render_financial_analysis

def load_sample_data():
    """Load sample data for demonstration."""
    # Sample mortality table
    ages = range(20, 100)
    mortality_rates = [0.001 * (1.05 ** (age - 20)) for age in ages]
    mortality_table = pd.Series(mortality_rates, index=ages)
    
    # Sample lapse rates
    lapse_rates = {
        year: 0.1 * (0.9 ** year) for year in range(20)
    }
    
    # Sample expense factors
    expense_factors = {
        'acquisition': 100,
        'maintenance': 50,
        'per_policy': 5
    }
    
    # Sample investment strategy
    investment_strategy = {
        'fixed_income': 0.7,
        'equity': 0.3
    }
    
    return mortality_table, lapse_rates, expense_factors, investment_strategy

def initialize_models():
    """Initialize economic scenario generator and cash flow model."""
    # Load sample data
    mortality_table, lapse_rates, expense_factors, investment_strategy = load_sample_data()
    
    # Initialize economic scenario generator
    esg = EconomicScenarioGenerator(
        initial_short_rate=0.03,
        initial_long_rate=0.04,
        mean_reversion_speed=0.15,
        volatility_short_rate=0.012,
        volatility_long_rate=0.008,
        equity_risk_premium=0.06,
        equity_volatility=0.15,
        inflation_mean=0.02,
        inflation_volatility=0.01
    )
    
    # Initialize cash flow model
    cfm = DynamicCashFlowModel(
        initial_assets=1_000_000,
        mortality_table=mortality_table,
        lapse_rates=lapse_rates,
        expense_factors=expense_factors,
        investment_strategy=investment_strategy
    )
    
    return esg, cfm

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Actuarial Stochastic Model",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Actuarial Stochastic Model")
    
    # Initialize session state
    if 'esg' not in st.session_state:
        st.session_state.esg, st.session_state.cfm = initialize_models()
    
    # Sidebar navigation
    analysis_type = st.sidebar.selectbox(
        "Select Analysis",
        ["Cash Flow Analysis", "Financial Model Analysis", "GCV Analysis"]
    )
    
    # Model parameters in sidebar
    st.sidebar.subheader("Scenario Parameters")
    num_scenarios = st.sidebar.number_input(
        "Number of Scenarios",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100
    )
    projection_years = st.sidebar.number_input(
        "Projection Years",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )
    time_steps = st.sidebar.number_input(
        "Time Steps per Year",
        min_value=1,
        max_value=12,
        value=12
    )
    
    # Generate scenarios if requested
    if st.sidebar.button("Generate Scenarios"):
        with st.spinner("Generating economic scenarios..."):
            scenarios = st.session_state.esg.generate_scenarios(
                num_scenarios=num_scenarios,
                projection_years=projection_years,
                time_steps_per_year=time_steps
            )
            st.session_state.scenarios = scenarios
            st.success(f"Generated {num_scenarios} scenarios")
    
    # Render selected analysis
    if analysis_type == "Cash Flow Analysis":
        if 'scenarios' in st.session_state:
            render_cash_flow_analysis(
                st.session_state.cfm,
                st.session_state.scenarios
            )
        else:
            st.warning("Please generate scenarios first")
    elif analysis_type == "Financial Model Analysis":
        render_financial_analysis()
    else:  # GCV Analysis
        render_gcv_controls()

if __name__ == "__main__":
    main()
