"""
Cash flow analysis dashboard component with vectorized operations support.

This module provides visualization and analysis components for the cash flow model,
optimized for handling large datasets using pandas operations. It supports:

- Interactive cash flow projections visualization
- Risk metrics analysis
- Scenario comparison
- Asset-liability matching analysis

All visualizations are created using plotly for interactive exploration.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
from datetime import date
from src.cash_flow_model import CashFlow

def plot_cash_flows(
    cash_flows: List[CashFlow], 
    num_scenarios_to_show: int = 10,
    title: str = "Cash Flow Projections"
) -> go.Figure:
    """
    Plot cash flow projections using vectorized operations.
    
    Args:
        cash_flows (List[CashFlow]): List of cash flows to plot
        num_scenarios_to_show (int): Number of scenarios to display
        title (str): Title for the plot
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Convert cash flows to DataFrame using vectorized operations
    df = pd.DataFrame([
        {
            'date': cf.date,
            'amount': cf.amount,
            'scenario_id': cf.scenario_id,
            'flow_type': cf.flow_type
        }
        for cf in cash_flows
    ])
    
    # Pivot and aggregate using pandas operations
    pivot_df = df.pivot_table(
        index=['date', 'scenario_id'],
        columns='flow_type',
        values='amount',
        aggfunc='sum'
    ).fillna(0)
    
    # Create figure
    fig = go.Figure()
    
    # Plot each scenario
    for scenario in range(min(num_scenarios_to_show, pivot_df.index.get_level_values('scenario_id').nunique())):
        scenario_data = pivot_df.xs(scenario, level='scenario_id')
        fig.add_trace(go.Scatter(
            x=scenario_data.index,
            y=scenario_data.sum(axis=1),
            name=f'Scenario {scenario}',
            mode='lines',
            opacity=0.6
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Amount",
        showlegend=True
    )
    
    return fig

def plot_risk_metrics(metrics: Dict[str, float]) -> go.Figure:
    """
    Plot risk metrics visualization using plotly.
    
    Args:
        metrics (Dict[str, float]): Dictionary of risk metrics
        
    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        text=[f"{v:,.2f}" for v in metrics.values()],
        textposition='auto',
    ))
    
    # Update layout
    fig.update_layout(
        title="Risk Metrics",
        xaxis_title="Metric",
        yaxis_title="Value",
        showlegend=False
    )
    
    return fig

def render_cash_flow_analysis(
    cash_flow_model,
    economic_scenarios: List,
    policy_data: Optional[pd.DataFrame] = None
) -> None:
    """
    Render cash flow analysis section in the dashboard.
    
    Args:
        cash_flow_model: Instance of DynamicCashFlowModel
        economic_scenarios (List): List of economic scenarios
        policy_data (Optional[pd.DataFrame]): Optional policy data for analysis
    """
    st.header("Cash Flow Analysis")
    
    # Project cash flows if policy data is provided
    if policy_data is not None:
        liability_flows = cash_flow_model.project_liability_flows(
            economic_scenarios, policy_data)
        asset_flows = cash_flow_model.project_asset_flows(
            economic_scenarios, liability_flows)
        
        # Plot projections
        st.subheader("Cash Flow Projections")
        fig = plot_cash_flows(liability_flows + asset_flows)
        st.plotly_chart(fig)
        
        # Calculate and plot risk metrics
        metrics = cash_flow_model.calculate_risk_metrics(
            liability_flows, asset_flows)
        st.subheader("Risk Metrics")
        fig = plot_risk_metrics(metrics)
        st.plotly_chart(fig)
    else:
        st.warning("Please provide policy data to view cash flow analysis.")

def render_asset_liability_cash_flow_analysis(cash_flow_model, asset_model):
    st.header("Asset-Liability Cash Flow Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        bond_alloc = st.slider("Bond Allocation (%)", 0, 100, 55)
        equity_alloc = 100 - bond_alloc
        st.metric("Equity Allocation", f"{equity_alloc}%")
    with col2:
        strategy = st.selectbox("Reinvestment Strategy", ["Proportional", "Priority Order", "Market Timing"])
    
    # Get projections
    liability_cf = cash_flow_model.get_undiscounted_liability_cf()
    asset_cf = asset_model.project_asset_cf(bond_alloc/100, equity_alloc/100, strategy)
    net_cf = asset_cf - liability_cf
    
    # Plot with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=liability_cf.index, y=liability_cf, name='Liability CF', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=asset_cf.index, y=asset_cf, name='Asset CF', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=net_cf.index, y=net_cf, name='Net CF', line=dict(color='green')))
    fig.update_layout(title='10-Year Cash Flow Projection', xaxis_title='Year', yaxis_title='Cash Flow ($M)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    if st.checkbox("Show Data Table"):
        df = pd.DataFrame({'Liability': liability_cf, 'Asset': asset_cf, 'Net': net_cf})
        st.dataframe(df.style.format("${:.2f}"))
    
    # Export
    if st.button("Export to CSV"):
        df.to_csv('cash_flow_projections.csv')
        st.success("Exported to cash_flow_projections.csv")

def render_cash_flow_analysis(cash_flow_model, economic_scenarios):
    """Render cash flow analysis section."""
    st.header("Cash Flow Analysis")
    
    # Sidebar controls
    st.sidebar.subheader("Analysis Parameters")
    num_scenarios = st.sidebar.slider(
        "Number of scenarios to display",
        min_value=1,
        max_value=50,
        value=10
    )
    confidence_level = st.sidebar.slider(
        "Confidence Level for Risk Metrics",
        min_value=0.8,
        max_value=0.99,
        value=0.95,
        step=0.01
    )
    
    # Project cash flows
    with st.spinner("Projecting cash flows..."):
        liability_flows = cash_flow_model.project_liability_flows(
            economic_scenarios,
            pd.DataFrame()  # Add policy data here
        )
        asset_flows = cash_flow_model.project_asset_flows(
            economic_scenarios,
            liability_flows
        )
    
    # Plot cash flows
    st.subheader("Liability Cash Flows")
    liability_plot = plot_cash_flows(
        liability_flows,
        num_scenarios_to_show=num_scenarios,
        title="Liability Cash Flow Projections"
    )
    st.plotly_chart(liability_plot)
    
    st.subheader("Asset Cash Flows")
    asset_plot = plot_cash_flows(
        asset_flows,
        num_scenarios_to_show=num_scenarios,
        title="Asset Cash Flow Projections"
    )
    st.plotly_chart(asset_plot)
    
    # Calculate and display risk metrics
    st.subheader("Risk Metrics")
    metrics = cash_flow_model.calculate_risk_metrics(
        liability_flows,
        asset_flows,
        confidence_level
    )
    metrics_plot = plot_risk_metrics(metrics)
    st.plotly_chart(metrics_plot)
    
    # Download options
    if st.button("Download Results"):
        # Convert cash flows to DataFrame
        df = pd.DataFrame([
            {
                'date': cf.date,
                'amount': cf.amount,
                'type': cf.flow_type,
                'scenario': cf.scenario_id
            }
            for cf in liability_flows + asset_flows
        ])
        
        # Create Excel writer
        output = pd.ExcelWriter('cash_flow_results.xlsx', engine='xlsxwriter')
        
        # Write cash flows
        df.to_excel(output, sheet_name='Cash Flows', index=False)
        
        # Write metrics
        pd.DataFrame([
            {'Metric': k, 'Value': v}
            for k, v in metrics.items()
        ]).to_excel(output, sheet_name='Risk Metrics', index=False)
        
        output.save()
        st.success("Results downloaded to cash_flow_results.xlsx")
