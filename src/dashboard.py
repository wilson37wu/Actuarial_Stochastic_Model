"""
Interactive dashboard for actuarial model analysis.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date, timedelta
from narrative_generator import NarrativeGenerator

# Basic styling
def apply_dashboard_theme():
    """Apply custom styling to the dashboard."""
    st.markdown(
        """
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stButton>button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

class ModelDashboard:
    """Interactive dashboard for model analysis."""
    
    def __init__(self):
        """Initialize dashboard components."""
        self.narrative_generator = NarrativeGenerator()
        
    def run(self):
        """Run the dashboard."""
        # Configure page layout
        st.set_page_config(
            page_title="Actuarial Model Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply dashboard theme
        apply_dashboard_theme()
        
        # Header
        st.title("Actuarial Model Analysis Dashboard")
        st.markdown("---")
        
        # Sidebar
        with st.sidebar:
            st.title("Model Parameters")
            
            # Analysis type selector
            analysis_type = st.selectbox(
                "Select Analysis Type",
                ["Portfolio Analysis", "GCV Analysis", "Dividend Analysis", 
                 "Stress Testing", "Sensitivity Analysis"]
            )
        
        # Main content
        if analysis_type == "Portfolio Analysis":
            self._render_portfolio_analysis()
        elif analysis_type == "GCV Analysis":
            self._render_gcv_analysis()
        elif analysis_type == "Dividend Analysis":
            self._render_dividend_analysis()
        elif analysis_type == "Stress Testing":
            self._render_stress_testing()
        else:
            self._render_sensitivity_analysis()
            
        # Footer
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                "<p style='text-align: center; color: #666666;'>"
                "Built with Streamlit</p>",
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                "<p style='text-align: center; color: #666666;'>"
                "2025 Actuarial Model Analysis Dashboard. All rights reserved.</p>",
                unsafe_allow_html=True
            )
    
    def _render_portfolio_analysis(self):
        """Render portfolio analysis section."""
        st.header("Portfolio Analysis")
        
        # Sample portfolio data
        data = {
            'Asset': ['Bonds', 'Stocks', 'Real Estate', 'Cash'],
            'Allocation': [40, 35, 20, 5],
            'Return': [5.2, 8.7, 6.5, 2.1],
            'Risk': [3.5, 15.2, 12.8, 0.5]
        }
        df = pd.DataFrame(data)
        
        # Display portfolio metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Portfolio allocation pie chart
            fig = go.Figure(data=[go.Pie(
                labels=df['Asset'],
                values=df['Allocation'],
                hole=.3
            )])
            fig.update_layout(title='Portfolio Allocation')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk-return scatter plot
            fig = go.Figure(data=[go.Scatter(
                x=df['Risk'],
                y=df['Return'],
                mode='markers+text',
                text=df['Asset'],
                textposition="top center"
            )])
            fig.update_layout(
                title='Risk-Return Profile',
                xaxis_title='Risk (%)',
                yaxis_title='Return (%)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Portfolio metrics
        st.subheader("Portfolio Metrics")
        metrics = st.columns(4)
        metrics[0].metric("Expected Return", "6.8%", "0.5%")
        metrics[1].metric("Portfolio Risk", "8.2%", "-0.3%")
        metrics[2].metric("Sharpe Ratio", "0.83", "0.05")
        metrics[3].metric("Yield", "4.2%", "0.2%")
        
        portfolio_data = {
            'allocation': {
                'Equities': 60.0,
                'Fixed Income': 30.0,
                'Cash': 10.0
            },
            'returns': {
                'Equities': 8.5,
                'Fixed Income': 4.2,
                'Cash': 1.5
            },
            'risks': {
                'Market Risk': 12.5,
                'Credit Risk': 8.0,
                'Liquidity Risk': 5.0
            }
        }
        
        # Generate and display narrative
        narrative = self.narrative_generator.generate_portfolio_narrative(portfolio_data)
        st.markdown(narrative)
    
    def _render_gcv_analysis(self):
        """Render GCV analysis section."""
        st.header("GCV Analysis")
        
        # Parameters
        col1, col2 = st.columns(2)
        with col1:
            premium = st.number_input("Annual Premium", 1000, 10000, 5000)
            term = st.number_input("Policy Term (Years)", 5, 30, 20)
        with col2:
            interest_rate = st.slider("Interest Rate (%)", 1.0, 5.0, 3.0, 0.1)
            surrender_charge = st.slider("Surrender Charge (%)", 0.0, 5.0, 2.0, 0.1)
        
        # Generate sample GCV values
        years = list(range(term + 1))
        gcv_values = [
            premium * year * (1 + interest_rate/100) * (1 - surrender_charge/100)
            for year in years
        ]
        
        # Plot GCV pattern
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=gcv_values,
            mode='lines+markers',
            name='GCV'
        ))
        fig.update_layout(
            title='Guaranteed Cash Value Pattern',
            xaxis_title='Policy Year',
            yaxis_title='GCV Amount'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        gcv_data = {
            'premium': premium,
            'term': term,
            'interest_rate': interest_rate,
            'surrender_charge': surrender_charge
        }
        
        # Generate and display narrative
        narrative = self.narrative_generator.generate_gcv_narrative(gcv_data)
        st.markdown(narrative)
    
    def _render_dividend_analysis(self):
        """Render dividend analysis section."""
        st.header("Dividend Analysis")
        
        # Parameters
        col1, col2 = st.columns(2)
        with col1:
            initial_dividend = st.number_input("Initial Dividend", 100, 1000, 500)
            growth_rate = st.slider("Growth Rate (%)", 0.0, 10.0, 5.0, 0.1)
        with col2:
            years = st.number_input("Projection Years", 5, 20, 10)
            volatility = st.slider("Volatility (%)", 0.0, 20.0, 10.0, 0.1)
        
        # Generate sample dividend projections
        time = list(range(years + 1))
        base_dividends = [
            initial_dividend * (1 + growth_rate/100) ** year
            for year in time
        ]
        
        # Generate multiple scenarios
        scenarios = 50
        all_scenarios = []
        for _ in range(scenarios):
            scenario = [
                base * (1 + np.random.normal(0, volatility/100))
                for base in base_dividends
            ]
            all_scenarios.append(scenario)
        
        # Plot dividend projections
        fig = go.Figure()
        
        # Add individual scenarios
        for scenario in all_scenarios:
            fig.add_trace(go.Scatter(
                x=time,
                y=scenario,
                mode='lines',
                line=dict(color='lightblue', width=1),
                showlegend=False
            ))
        
        # Add base scenario
        fig.add_trace(go.Scatter(
            x=time,
            y=base_dividends,
            mode='lines',
            name='Base Scenario',
            line=dict(color='blue', width=3)
        ))
        
        fig.update_layout(
            title='Dividend Projections with Uncertainty',
            xaxis_title='Year',
            yaxis_title='Dividend Amount'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        dividend_data = {
            'initial_dividend': initial_dividend,
            'growth_rate': growth_rate,
            'volatility': volatility,
            'years': years
        }
        
        # Generate and display narrative
        narrative = self.narrative_generator.generate_dividend_narrative(dividend_data)
        st.markdown(narrative)
    
    def _render_stress_testing(self):
        """Render stress testing section."""
        st.header("Stress Testing")
        
        # Stress scenarios
        scenarios = {
            'Base Case': [0, 0, 0],
            'Market Crash': [-30, -20, -15],
            'Interest Rate Spike': [-10, -5, 5],
            'Pandemic Impact': [-25, -15, -10],
            'Economic Boom': [15, 10, 5]
        }
        
        # Parameters
        selected_scenario = st.selectbox("Select Stress Scenario", list(scenarios.keys()))
        
        # Display scenario impact
        impact = scenarios[selected_scenario]
        metrics = st.columns(3)
        metrics[0].metric("Portfolio Value Impact", f"{impact[0]}%")
        metrics[1].metric("Solvency Ratio Impact", f"{impact[1]}%")
        metrics[2].metric("Revenue Impact", f"{impact[2]}%")
        
        # Generate sample stress test results
        periods = 12
        base_value = 100
        stressed_values = []
        
        for i in range(periods):
            if i < 3:  # Initial shock
                shock = impact[0] / 3
            else:  # Recovery
                shock = -impact[0] / 9
            
            stressed_values.append(base_value * (1 + shock/100))
            base_value = stressed_values[-1]
        
        # Plot stress test results
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(periods)),
            y=[100] * periods,
            mode='lines',
            name='Base Line',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=list(range(periods)),
            y=stressed_values,
            mode='lines',
            name='Stress Scenario',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title=f'Stress Test Results: {selected_scenario}',
            xaxis_title='Month',
            yaxis_title='Portfolio Value (Indexed)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        stress_data = {
            'scenario': selected_scenario,
            'impacts': impact
        }
        
        # Generate and display narrative
        narrative = self.narrative_generator.generate_stress_test_narrative(stress_data)
        st.markdown(narrative)
    
    def _render_sensitivity_analysis(self):
        """Render sensitivity analysis section."""
        st.header("Sensitivity Analysis")
        
        # Parameters
        col1, col2 = st.columns(2)
        with col1:
            base_value = st.number_input("Base Portfolio Value", 100000, 1000000, 500000)
            interest_range = st.slider("Interest Rate Range (%)", -2.0, 2.0, (-1.0, 1.0))
        with col2:
            mortality_range = st.slider("Mortality Range (%)", -20.0, 20.0, (-10.0, 10.0))
            lapse_range = st.slider("Lapse Rate Range (%)", -5.0, 5.0, (-2.0, 2.0))
        
        # Generate sensitivity data
        interest_points = np.linspace(interest_range[0], interest_range[1], 10)
        mortality_points = np.linspace(mortality_range[0], mortality_range[1], 10)
        lapse_points = np.linspace(lapse_range[0], lapse_range[1], 10)
        
        # Calculate impacts
        interest_impact = [base_value * (1 + x/100) for x in interest_points]
        mortality_impact = [base_value * (1 + x/100) for x in mortality_points]
        lapse_impact = [base_value * (1 + x/100) for x in lapse_points]
        
        # Plot sensitivity analysis
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=interest_points,
            y=interest_impact,
            mode='lines',
            name='Interest Rate'
        ))
        fig.add_trace(go.Scatter(
            x=mortality_points,
            y=mortality_impact,
            mode='lines',
            name='Mortality'
        ))
        fig.add_trace(go.Scatter(
            x=lapse_points,
            y=lapse_impact,
            mode='lines',
            name='Lapse Rate'
        ))
        
        fig.update_layout(
            title='Portfolio Value Sensitivity',
            xaxis_title='Parameter Change (%)',
            yaxis_title='Portfolio Value'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        sensitivity_data = {
            'base_value': base_value,
            'ranges': {
                'Interest Rate': interest_range,
                'Mortality': mortality_range,
                'Lapse Rate': lapse_range
            }
        }
        
        # Generate and display narrative
        narrative = self.narrative_generator.generate_sensitivity_narrative(sensitivity_data)
        st.markdown(narrative)

if __name__ == "__main__":
    dashboard = ModelDashboard()
    dashboard.run()
