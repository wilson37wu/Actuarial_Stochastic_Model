"""GCV analysis module."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List

from .visualization import Visualization
from ..gcv_calculator import GCVCalculator

class GCVAnalysis:
    """Handle GCV analysis functionality."""
    
    def __init__(self, calculator: GCVCalculator):
        """Initialize GCV analysis."""
        self.viz = Visualization()
        self.calculator = calculator
    
    def render(self):
        """Render GCV analysis section."""
        st.subheader("GCV Analysis")
        
        # Add controls
        col1, col2 = st.columns(2)
        
        with col1:
            enable_pattern = st.checkbox(
                "Enable Pattern Mixing",
                value=False
            )
            show_3d = st.checkbox(
                "Show 3D Visualization",
                value=False
            )
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "Pattern Analysis",
            "Product Comparison",
            "Sensitivity Analysis"
        ])
        
        with tab1:
            if enable_pattern:
                self._render_pattern_analysis()
            else:
                self._plot_gcv_patterns(max_years=30)
        
        with tab2:
            self._render_product_comparison()
        
        with tab3:
            if show_3d:
                self._render_3d_sensitivity()
            else:
                self._render_2d_sensitivity()
    
    def _render_pattern_analysis(self):
        """Render pattern analysis section."""
        st.subheader("Pattern Analysis")
        
        # Add pattern mixing controls
        patterns = st.multiselect(
            "Select Patterns",
            ["Level", "Increasing", "Decreasing"],
            default=["Level"]
        )
        
        # Create figure
        fig = go.Figure()
        
        for pattern in patterns:
            years = list(range(30))
            if pattern == "Level":
                values = [5000] * 30
            elif pattern == "Increasing":
                values = [5000 * (1 + 0.03) ** year for year in years]
            else:  # Decreasing
                values = [5000 * (1 - 0.02) ** year for year in years]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                name=pattern,
                mode='lines'
            ))
        
        fig.update_layout(
            xaxis_title="Policy Year",
            yaxis_title="Premium Amount",
            hovermode='x unified'
        )
        
        self.viz.create_plot_container(fig, "Premium Patterns")
    
    def _plot_gcv_patterns(self, max_years: int = 30):
        """Plot GCV patterns."""
        # Calculate GCV values
        years = list(range(max_years))
        gcv_values = [
            self.calculator.calculate_gcv('M', year, 5000, 100000, 80000)
            for year in years
        ]
        
        # Create figure
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=years,
            y=gcv_values,
            name='GCV',
            mode='lines',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="Policy Year",
            yaxis_title="GCV Value",
            hovermode='x unified'
        )
        
        self.viz.create_plot_container(fig, "GCV Pattern")
    
    def _render_product_comparison(self):
        """Render product comparison section."""
        st.subheader("Product Comparison")
        
        # Add product selection
        products = st.multiselect(
            "Select Products",
            ["Standard", "High Cash Value", "Low Premium"],
            default=["Standard"]
        )
        
        # Create figure
        fig = go.Figure()
        
        for product in products:
            years = list(range(30))
            if product == "Standard":
                values = [
                    self.calculator.calculate_gcv('M', year, 5000, 100000, 80000)
                    for year in years
                ]
            elif product == "High Cash Value":
                values = [
                    self.calculator.calculate_gcv('M', year, 7500, 100000, 90000)
                    for year in years
                ]
            else:  # Low Premium
                values = [
                    self.calculator.calculate_gcv('M', year, 3000, 80000, 60000)
                    for year in years
                ]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                name=product,
                mode='lines'
            ))
        
        fig.update_layout(
            xaxis_title="Policy Year",
            yaxis_title="GCV Value",
            hovermode='x unified'
        )
        
        self.viz.create_plot_container(fig, "Product Comparison")
    
    def _render_2d_sensitivity(self):
        """Render 2D sensitivity analysis."""
        st.subheader("2D Sensitivity Analysis")
        
        # Add sensitivity parameters
        premium_range = np.linspace(3000, 7000, 20)
        face_amount_range = np.linspace(50000, 150000, 20)
        
        # Calculate sensitivity surface
        z = np.zeros((len(premium_range), len(face_amount_range)))
        for i, premium in enumerate(premium_range):
            for j, face in enumerate(face_amount_range):
                z[i,j] = self.calculator.calculate_gcv(
                    'M', 0, premium, face, face * 0.8
                )
        
        # Create figure
        fig = go.Figure(data=[
            go.Contour(
                z=z,
                x=face_amount_range,
                y=premium_range,
                colorscale='Viridis'
            )
        ])
        
        fig.update_layout(
            xaxis_title="Face Amount",
            yaxis_title="Premium",
            hovermode='closest'
        )
        
        self.viz.create_plot_container(fig, "Sensitivity Analysis")
    
    def _render_3d_sensitivity(self):
        """Render 3D sensitivity analysis."""
        st.subheader("3D Sensitivity Analysis")
        
        # Add sensitivity parameters
        premium_range = np.linspace(3000, 7000, 20)
        face_amount_range = np.linspace(50000, 150000, 20)
        
        # Calculate sensitivity surface
        z = np.zeros((len(premium_range), len(face_amount_range)))
        for i, premium in enumerate(premium_range):
            for j, face in enumerate(face_amount_range):
                z[i,j] = self.calculator.calculate_gcv(
                    'M', 0, premium, face, face * 0.8
                )
        
        # Create figure
        fig = go.Figure(data=[
            go.Surface(
                z=z,
                x=face_amount_range,
                y=premium_range,
                colorscale='Viridis'
            )
        ])
        
        fig.update_layout(
            scene=dict(
                xaxis_title="Face Amount",
                yaxis_title="Premium",
                zaxis_title="GCV Value"
            ),
            hovermode='closest'
        )
        
        self.viz.create_plot_container(fig, "3D Sensitivity Analysis")
