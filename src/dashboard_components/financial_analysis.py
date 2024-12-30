"""
Financial model analysis dashboard component.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from datetime import date, timedelta

from financial_models import (
    ModelParameters,
    HullWhiteModel,
    JarrowTurnbullModel,
    MertonCreditModel,
    HestonModel,
    MertonJumpDiffusionModel,
    ALMEngine
)

def plot_rate_scenarios(scenarios: Dict[str, np.ndarray], title: str = "Interest Rate Scenarios"):
    """Plot interest rate scenarios."""
    fig = go.Figure()
    
    # Plot individual scenarios
    num_scenarios = scenarios['interest_rates'].shape[0]
    for i in range(min(10, num_scenarios)):
        fig.add_trace(go.Scatter(
            y=scenarios['interest_rates'][i],
            mode='lines',
            name=f'Scenario {i+1}',
            opacity=0.3
        ))
    
    # Plot mean
    mean_rates = scenarios['interest_rates'].mean(axis=0)
    fig.add_trace(go.Scatter(
        y=mean_rates,
        mode='lines',
        name='Mean',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time Step",
        yaxis_title="Interest Rate",
        showlegend=True
    )
    
    return fig

def plot_credit_analysis(scenarios: Dict[str, np.ndarray]):
    """Plot credit spread analysis."""
    fig = make_subplots(rows=2, cols=1,
                       subplot_titles=("Credit Spread Scenarios",
                                     "Credit Spread Distribution"))
    
    # Plot scenarios
    num_scenarios = scenarios['credit_spreads'].shape[0]
    for i in range(min(10, num_scenarios)):
        fig.add_trace(
            go.Scatter(
                y=scenarios['credit_spreads'][i],
                mode='lines',
                name=f'Scenario {i+1}',
                opacity=0.3
            ),
            row=1, col=1
        )
    
    # Plot mean
    mean_spreads = scenarios['credit_spreads'].mean(axis=0)
    fig.add_trace(
        go.Scatter(
            y=mean_spreads,
            mode='lines',
            name='Mean',
            line=dict(color='red', width=2)
        ),
        row=1, col=1
    )
    
    # Plot distribution at final time step
    final_spreads = scenarios['credit_spreads'][:, -1]
    fig.add_trace(
        go.Histogram(
            x=final_spreads,
            name='Final Distribution'
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=800, showlegend=True)
    return fig

def plot_equity_analysis(scenarios: Dict[str, np.ndarray]):
    """Plot equity price analysis."""
    fig = make_subplots(rows=2, cols=2,
                       subplot_titles=("Heston Price Paths",
                                     "Jump Diffusion Price Paths",
                                     "Variance Paths",
                                     "Return Distribution"))
    
    # Plot Heston prices
    num_scenarios = scenarios['equity_prices_heston'].shape[0]
    for i in range(min(5, num_scenarios)):
        fig.add_trace(
            go.Scatter(
                y=scenarios['equity_prices_heston'][i],
                mode='lines',
                name=f'Heston {i+1}',
                opacity=0.3
            ),
            row=1, col=1
        )
    
    # Plot Jump Diffusion prices
    for i in range(min(5, num_scenarios)):
        fig.add_trace(
            go.Scatter(
                y=scenarios['equity_prices_jump'][i],
                mode='lines',
                name=f'Jump {i+1}',
                opacity=0.3
            ),
            row=1, col=2
        )
    
    # Plot variance paths
    for i in range(min(5, num_scenarios)):
        fig.add_trace(
            go.Scatter(
                y=scenarios['equity_variances'][i],
                mode='lines',
                name=f'Variance {i+1}',
                opacity=0.3
            ),
            row=2, col=1
        )
    
    # Calculate and plot return distribution
    returns_heston = np.diff(np.log(scenarios['equity_prices_heston']), axis=1)
    returns_jump = np.diff(np.log(scenarios['equity_prices_jump']), axis=1)
    
    fig.add_trace(
        go.Histogram(
            x=returns_heston.flatten(),
            name='Heston Returns',
            opacity=0.7,
            nbinsx=50
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Histogram(
            x=returns_jump.flatten(),
            name='Jump Returns',
            opacity=0.7,
            nbinsx=50
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=1000, showlegend=True)
    return fig

def render_financial_analysis():
    """Render financial model analysis section."""
    st.header("Financial Model Analysis")
    
    # Model parameters in sidebar
    st.sidebar.subheader("Model Parameters")
    
    # Interest rate parameters
    st.sidebar.markdown("### Interest Rate Parameters")
    mean_reversion = st.sidebar.slider(
        "Mean Reversion Speed",
        min_value=0.01,
        max_value=0.5,
        value=0.15,
        step=0.01
    )
    rate_vol = st.sidebar.slider(
        "Rate Volatility",
        min_value=0.001,
        max_value=0.05,
        value=0.012,
        step=0.001
    )
    
    # Equity parameters
    st.sidebar.markdown("### Equity Parameters")
    equity_vol = st.sidebar.slider(
        "Equity Volatility",
        min_value=0.1,
        max_value=0.5,
        value=0.15,
        step=0.01
    )
    jump_intensity = st.sidebar.slider(
        "Jump Intensity",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1
    )
    
    # Simulation parameters
    st.sidebar.markdown("### Simulation Parameters")
    num_scenarios = st.sidebar.number_input(
        "Number of Scenarios",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100
    )
    projection_years = st.sidebar.number_input(
        "Projection Years",
        min_value=1,
        max_value=30,
        value=5,
        step=1
    )
    
    # Initialize models with parameters
    params = ModelParameters(
        mean_reversion_speed=mean_reversion,
        rate_volatility=rate_vol,
        equity_volatility=equity_vol,
        jump_intensity=jump_intensity
    )
    
    alm_engine = ALMEngine(params)
    
    # Generate scenarios
    if st.button("Generate Scenarios"):
        with st.spinner("Generating scenarios..."):
            scenarios = alm_engine.simulate_multiple_scenarios(
                num_scenarios=num_scenarios,
                T=float(projection_years),
                dt=1.0/12
            )
            
            # Store scenarios in session state
            st.session_state.scenarios = scenarios
            st.success(f"Generated {num_scenarios} scenarios")
    
    # Display analysis if scenarios exist
    if 'scenarios' in st.session_state:
        scenarios = st.session_state.scenarios
        
        # Interest rate analysis
        st.subheader("Interest Rate Analysis")
        rate_plot = plot_rate_scenarios(scenarios)
        st.plotly_chart(rate_plot)
        
        # Credit analysis
        st.subheader("Credit Analysis")
        credit_plot = plot_credit_analysis(scenarios)
        st.plotly_chart(credit_plot)
        
        # Equity analysis
        st.subheader("Equity Analysis")
        equity_plot = plot_equity_analysis(scenarios)
        st.plotly_chart(equity_plot)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Avg Interest Rate",
                f"{scenarios['interest_rates'].mean():.2%}"
            )
            
        with col2:
            st.metric(
                "Avg Credit Spread",
                f"{scenarios['credit_spreads'].mean():.2%}"
            )
            
        with col3:
            equity_return = np.diff(np.log(scenarios['equity_prices_heston'])).mean() * 12
            st.metric(
                "Annualized Equity Return",
                f"{equity_return:.2%}"
            )
