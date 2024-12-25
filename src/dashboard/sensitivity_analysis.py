"""Sensitivity analysis module."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List

from .visualization import Visualization
from ..gcv_calculator import GCVCalculator

class SensitivityAnalysis:
    """Handle sensitivity analysis functionality."""
    
    def __init__(self, calculator: GCVCalculator):
        """Initialize sensitivity analysis."""
        self.viz = Visualization()
        self.calculator = calculator
    
    def render(self):
        """Render sensitivity analysis section."""
        st.subheader("Sensitivity Analysis")
        
        # Parameter selection
        selected_params = st.multiselect(
            "Select Parameters for Analysis",
            ["Premium", "Face Amount", "Interest Rate"],
            default=["Premium"]
        )
        
        if selected_params:
            self._render_one_way_analysis(selected_params)
    
    def _render_one_way_analysis(self, params: List[str]):
        """Render one-way sensitivity analysis."""
        for param in params:
            # Get base value and range
            base_value = self._get_base_value(param)
            test_range = np.linspace(
                base_value * 0.5,
                base_value * 1.5,
                20
            )
            
            # Calculate sensitivity
            results = []
            for value in test_range:
                gcv = self._calculate_gcv_with_param(param, value)
                results.append(gcv)
            
            # Create figure
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=test_range,
                y=results,
                mode='lines+markers',
                name=param
            ))
            
            # Add base point
            base_gcv = self._calculate_gcv_with_param(param, base_value)
            fig.add_trace(go.Scatter(
                x=[base_value],
                y=[base_gcv],
                mode='markers',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='diamond'
                ),
                name='Base Value'
            ))
            
            fig.update_layout(
                title=f"Sensitivity to {param}",
                xaxis_title=param,
                yaxis_title="GCV Value",
                hovermode='x unified'
            )
            
            self.viz.create_plot_container(
                fig,
                f"One-Way Sensitivity: {param}"
            )
    
    def _get_base_value(self, param: str) -> float:
        """Get base value for parameter."""
        base_values = {
            "Premium": 5000,
            "Face Amount": 100000,
            "Interest Rate": 0.035
        }
        return base_values.get(param, 0)
    
    def _calculate_gcv_with_param(self, param: str, value: float) -> float:
        """Calculate GCV with modified parameter."""
        if param == "Premium":
            return self.calculator.calculate_gcv(
                'M', 0, value, 100000, 80000
            )
        elif param == "Face Amount":
            return self.calculator.calculate_gcv(
                'M', 0, 5000, value, value * 0.8
            )
        elif param == "Interest Rate":
            orig_rate = self.calculator.valuation_rate
            try:
                self.calculator.valuation_rate = value
                return self.calculator.calculate_gcv(
                    'M', 0, 5000, 100000, 80000
                )
            finally:
                self.calculator.valuation_rate = orig_rate
        return 0
