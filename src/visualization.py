"""Visualization utilities for the actuarial model."""
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, List, Optional, Tuple

class ModelVisualizer:
    """Visualization utilities for the actuarial model."""
    
    def __init__(self):
        """Initialize visualizer with default settings."""
        self.colors = px.colors.qualitative.Set3
        self.template = "plotly_dark"
        self.default_height = 500
        self.default_width = None  # Auto-width
    
    def plot_gcv_patterns(self,
                         patterns: Dict[str, List[float]],
                         years: List[int]) -> go.Figure:
        """Plot GCV patterns comparison.
        
        Args:
            patterns: Dictionary mapping pattern names to their values
            years: List of years to plot
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        for i, (name, values) in enumerate(patterns.items()):
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=values,
                    name=name,
                    line=dict(color=self.colors[i % len(self.colors)])
                )
            )
        
        fig.update_layout(
            title='GCV Grading Patterns Comparison',
            xaxis_title='Policy Year',
            yaxis_title='Grading Factor',
            template=self.template,
            height=self.default_height,
            width=self.default_width,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
        
        return fig
    
    def plot_pattern_derivatives(self,
                               patterns: Dict[str, Dict[str, List[float]]],
                               years: List[int]) -> go.Figure:
        """Plot pattern derivatives."""
        fig = go.Figure()
        
        for pattern_name, data in patterns.items():
            # Plot original values
            fig.add_trace(go.Scatter(
                x=years,
                y=data['values'],
                name=f"{pattern_name} Value",
                mode='lines'
            ))
            
            # Plot first derivative
            fig.add_trace(go.Scatter(
                x=years,
                y=data['deriv1'],
                name=f"{pattern_name} 1st Deriv",
                mode='lines',
                line=dict(dash='dash')
            ))
            
            # Plot second derivative
            fig.add_trace(go.Scatter(
                x=years,
                y=data['deriv2'],
                name=f"{pattern_name} 2nd Deriv",
                mode='lines',
                line=dict(dash='dot')
            ))
        
        fig.update_layout(
            title="GCV Pattern Derivatives",
            xaxis_title="Policy Year",
            yaxis_title="Value/Rate of Change",
            template=self.template,
            height=self.default_height,
            width=self.default_width,
            hovermode='x unified'
        )
        
        return fig
    
    def plot_3d_surface(self,
                       X: np.ndarray,
                       Y: np.ndarray,
                       Z: np.ndarray,
                       title: str,
                       x_label: str,
                       y_label: str,
                       z_label: str) -> go.Figure:
        """Create 3D surface plot."""
        fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z)])
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title=x_label,
                yaxis_title=y_label,
                zaxis_title=z_label,
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            template=self.template,
            width=800,
            height=800
        )
        
        return fig
    
    def plot_dividend_analysis(self,
                             returns: List[float],
                             dividends: List[float],
                             periods: List[int]) -> Tuple[go.Figure, go.Figure]:
        """Plot dividend analysis charts."""
        # Returns vs Dividends scatter
        scatter_fig = go.Figure()
        scatter_fig.add_trace(go.Scatter(
            x=returns,
            y=dividends,
            mode='markers',
            marker=dict(
                size=10,
                color=returns,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Return")
            ),
            text=periods,
            name='Returns vs Dividends'
        ))
        
        scatter_fig.update_layout(
            title='Returns vs Dividends Relationship',
            xaxis_title='Return (%)',
            yaxis_title='Dividend Amount',
            template=self.template,
            height=self.default_height,
            width=self.default_width
        )
        
        # Tracking balance line chart
        balance_fig = go.Figure()
        cumulative_returns = np.cumsum(returns)
        cumulative_dividends = np.cumsum(dividends)
        
        balance_fig.add_trace(go.Scatter(
            x=periods,
            y=cumulative_returns,
            name='Cumulative Returns',
            line=dict(color=self.colors[0])
        ))
        
        balance_fig.add_trace(go.Scatter(
            x=periods,
            y=cumulative_dividends,
            name='Cumulative Dividends',
            line=dict(color=self.colors[1])
        ))
        
        balance_fig.update_layout(
            title='Cumulative Returns and Dividends',
            xaxis_title='Period',
            yaxis_title='Amount',
            template=self.template,
            height=self.default_height,
            width=self.default_width
        )
        
        return scatter_fig, balance_fig
    
    def plot_portfolio_composition(self,
                                 products: Dict[str, float],
                                 metrics: Dict[str, float]) -> go.Figure:
        """Plot portfolio composition and metrics."""
        fig = go.Figure()
        
        # Create pie chart for composition
        fig.add_trace(go.Pie(
            labels=list(products.keys()),
            values=list(products.values()),
            domain=dict(x=[0, 0.45]),
            name="Composition",
            textinfo='label+percent'
        ))
        
        # Create bar chart for metrics
        fig.add_trace(go.Bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            text=[f"{v:.2f}" for v in metrics.values()],
            textposition='auto',
            domain=dict(x=[0.55, 1]),
            name="Metrics"
        ))
        
        fig.update_layout(
            title="Portfolio Analysis",
            template=self.template,
            height=500,
            showlegend=False,
            grid=dict(columns=2, rows=1)
        )
        
        return fig
    
    def plot_sensitivity_analysis(self,
                                parameter: str,
                                values: np.ndarray,
                                results: np.ndarray,
                                baseline: Optional[float] = None) -> go.Figure:
        """Plot sensitivity analysis."""
        fig = go.Figure()
        
        # Plot sensitivity curve
        fig.add_trace(go.Scatter(
            x=values,
            y=results,
            mode='lines+markers',
            name='Response'
        ))
        
        # Add baseline if provided
        if baseline is not None:
            fig.add_hline(
                y=baseline,
                line_dash="dash",
                annotation_text="Baseline",
                annotation_position="right"
            )
        
        # Calculate and plot elasticity
        elasticity = np.gradient(results) / np.gradient(values) * \
                    values[1:] / results[1:]
        
        fig.add_trace(go.Scatter(
            x=values[1:],
            y=elasticity,
            mode='lines',
            name='Elasticity',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f"Sensitivity to {parameter}",
            xaxis_title=parameter,
            yaxis_title="Response",
            template=self.template,
            height=self.default_height,
            width=self.default_width,
            yaxis2=dict(
                title="Elasticity",
                overlaying="y",
                side="right"
            ),
            hovermode='x unified'
        )
        
        return fig
