"""Scenario analysis module."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List

from .visualization import Visualization
from ..gcv_calculator import GCVCalculator
from ..dividend_tracker import DividendTracker

class ScenarioAnalysis:
    """Handle scenario analysis functionality."""
    
    def __init__(self, calculator: GCVCalculator, tracker: DividendTracker):
        """Initialize scenario analysis."""
        self.viz = Visualization()
        self.calculator = calculator
        self.tracker = tracker
    
    def render(self):
        """Render scenario analysis section."""
        st.subheader("Scenario Analysis")
        
        tab1, tab2 = st.tabs(["Stress Testing", "Monte Carlo"])
        
        with tab1:
            self.render_stress_testing()
        
        with tab2:
            self.render_monte_carlo()
    
    def render_stress_testing(self):
        """Render stress testing section."""
        st.subheader("Stress Testing")
        
        # Add stress test parameters
        stress_params = {
            'Interest Rate': st.slider("Interest Rate Shock (%)", -50, 50, 0),
            'Mortality': st.slider("Mortality Shock (%)", -30, 30, 0),
            'Lapse': st.slider("Lapse Rate Shock (%)", -20, 20, 0)
        }
        
        # Calculate stressed scenarios
        base_values = self._calculate_base_scenario()
        stressed_values = self._calculate_stressed_scenario(stress_params)
        
        # Create figure
        fig = go.Figure()
        
        # Add base scenario
        fig.add_trace(go.Scatter(
            x=list(range(len(base_values))),
            y=base_values,
            name='Base Scenario',
            mode='lines'
        ))
        
        # Add stressed scenario
        fig.add_trace(go.Scatter(
            x=list(range(len(stressed_values))),
            y=stressed_values,
            name='Stressed Scenario',
            mode='lines'
        ))
        
        fig.update_layout(
            title="Scenario Analysis",
            xaxis_title="Policy Year",
            yaxis_title="GCV Value",
            hovermode='x unified'
        )
        
        self.viz.create_plot_container(fig, "Scenario Paths")
    
    def render_monte_carlo(self):
        """Render Monte Carlo simulation section."""
        st.subheader("Monte Carlo Simulation")
        
        # Add Monte Carlo parameters
        num_sims = st.slider("Number of Simulations", 100, 1000, 500)
        num_years = st.slider("Projection Years", 5, 30, 20)
        
        # Run simulations
        results = self._run_monte_carlo(num_sims, num_years)
        
        # Create figure
        fig = go.Figure()
        
        # Add simulation paths
        for i in range(num_sims):
            fig.add_trace(go.Scatter(
                x=list(range(num_years)),
                y=results[i],
                name=f'Sim {i+1}',
                mode='lines',
                opacity=0.1,
                showlegend=False
            ))
        
        # Add mean path
        mean_path = np.mean(results, axis=0)
        fig.add_trace(go.Scatter(
            x=list(range(num_years)),
            y=mean_path,
            name='Mean Path',
            mode='lines',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Monte Carlo Simulation",
            xaxis_title="Policy Year",
            yaxis_title="GCV Value",
            hovermode='x unified'
        )
        
        self.viz.create_plot_container(fig, "Monte Carlo Paths")
    
    def _calculate_base_scenario(self) -> List[float]:
        """Calculate base scenario values."""
        years = range(30)
        return [
            self.calculator.calculate_gcv('M', year, 5000, 100000, 80000)
            for year in years
        ]
    
    def _calculate_stressed_scenario(self, stress_params: Dict[str, float]) -> List[float]:
        """Calculate stressed scenario values."""
        years = range(30)
        values = []
        
        # Store original parameters
        orig_rate = self.calculator.valuation_rate
        
        try:
            # Apply stress
            if 'Interest Rate' in stress_params:
                self.calculator.valuation_rate *= (1 + stress_params['Interest Rate']/100)
            
            # Calculate stressed values
            values = [
                self.calculator.calculate_gcv('M', year, 5000, 100000, 80000)
                for year in years
            ]
        finally:
            # Restore original parameters
            self.calculator.valuation_rate = orig_rate
        
        return values
    
    def _run_monte_carlo(self, num_sims: int, num_years: int) -> np.ndarray:
        """Run Monte Carlo simulation."""
        results = np.zeros((num_sims, num_years))
        
        for i in range(num_sims):
            # Generate random shocks
            rate_path = np.random.normal(0, 0.01, num_years)  # 1% std dev
            
            # Calculate path
            for j in range(num_years):
                self.calculator.valuation_rate = max(0.01, 0.035 + rate_path[j])
                results[i,j] = self.calculator.calculate_gcv(
                    'M', j, 5000, 100000, 80000
                )
        
        return results
