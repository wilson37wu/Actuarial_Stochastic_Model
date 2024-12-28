"""Visualizer for GCV analysis."""
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from ..gcv_calculator import GCVCalculator, GradingPattern, ProductVariant, GCVParameters

class GCVVisualizer:
    """Visualizer for GCV analysis."""
    
    def __init__(self, calculator: GCVCalculator):
        """Initialize visualizer with a GCV calculator."""
        self.calculator = calculator
        
    def calculate_achieved_irr(self, target_year: int) -> float:
        """Calculate achieved IRR at target year."""
        premium = 10000  # Example premium
        face_amount = 100000  # Example face amount
        
        # Get GCV values for each year
        gcv_values = []
        for year in range(target_year + 1):
            gcv = self.calculator.calculate_gcv(
                policy_year=year,
                premium=premium,
                face_amount=face_amount
            )
            gcv_values.append(gcv)
            
        # Calculate IRR
        return self.calculator.calculate_irr(
            premiums=[premium] * target_year,
            cash_values=gcv_values
        )
        
    def plot_gcv_patterns(self, max_years: int = 30) -> go.Figure:
        """Plot GCV patterns over time."""
        years = list(range(max_years + 1))
        premium = 10000  # Example premium
        face_amount = 100000  # Example face amount
        
        # Calculate GCV for each year
        gcv_values = []
        for year in years:
            gcv = self.calculator.calculate_gcv(
                policy_year=year,
                premium=premium,
                face_amount=face_amount
            )
            gcv_values.append(gcv / face_amount)  # Convert to percentage
            
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=gcv_values,
            mode='lines+markers',
            name='GCV Pattern',
            line=dict(width=2)
        ))
        
        # Add target IRR line if applicable
        if (self.calculator.parameters.target_irr and 
            self.calculator.parameters.target_year):
            target_irr = self.calculator.parameters.target_irr
            target_year = self.calculator.parameters.target_year
            fig.add_hline(
                y=target_irr,
                line_dash="dash",
                annotation_text=f"Target IRR: {target_irr*100:.1f}%",
                line_color="red"
            )
            fig.add_vline(
                x=target_year,
                line_dash="dash",
                annotation_text=f"Target Year: {target_year}",
                line_color="red"
            )
        
        # Update layout
        fig.update_layout(
            title="GCV Pattern Over Time",
            xaxis_title="Policy Year",
            yaxis_title="GCV Factor",
            showlegend=True,
            hovermode='x unified'
        )
        return fig
    
    def plot_mixed_pattern(self, pattern_weights: Dict[str, float], max_years: int = 30) -> go.Figure:
        """Plot mixed GCV pattern with weights."""
        years = list(range(max_years + 1))
        patterns = []
        
        # Calculate each pattern's contribution
        for pattern_name, weight in pattern_weights.items():
            if weight > 0:
                pattern_values = []
                temp_params = GCVParameters(
                    grading_pattern=GradingPattern[pattern_name],
                    **{k: v for k, v in self.calculator.parameters.__dict__.items() 
                       if k not in ['grading_pattern', 'pattern_weights']}
                )
                temp_calc = GCVCalculator(
                    valuation_rate=self.calculator.valuation_rate,
                    parameters=temp_params
                )
                
                for year in years:
                    gcv = temp_calc.calculate_gcv(
                        policy_year=year,
                        premium=10000,
                        face_amount=100000
                    )
                    pattern_values.append((gcv / 100000) * weight)
                patterns.append({
                    'pattern': pattern_name,
                    'years': years,
                    'values': pattern_values
                })
        
        # Create plot
        fig = go.Figure()
        
        # Add individual pattern traces
        for pattern in patterns:
            fig.add_trace(go.Scatter(
                x=pattern['years'],
                y=pattern['values'],
                name=pattern['pattern'],
                stackgroup='patterns',
                line=dict(width=0)
            ))
        
        # Update layout
        fig.update_layout(
            title="Mixed GCV Pattern Components",
            xaxis_title="Policy Year",
            yaxis_title="GCV Factor",
            showlegend=True,
            hovermode='x unified'
        )
        return fig
    
    def plot_pattern_derivatives(self, max_years: int = 30) -> go.Figure:
        """Plot pattern derivatives (rate of change)."""
        years = list(range(max_years))
        premium = 10000
        face_amount = 100000
        
        # Calculate GCV values
        gcv_values = []
        for year in range(max_years + 1):
            gcv = self.calculator.calculate_gcv(
                policy_year=year,
                premium=premium,
                face_amount=face_amount
            )
            gcv_values.append(gcv / face_amount)
            
        # Calculate derivatives
        first_derivative = np.diff(gcv_values)
        second_derivative = np.diff(first_derivative)
        
        # Create plot
        fig = go.Figure()
        
        # Add first derivative
        fig.add_trace(go.Scatter(
            x=years,
            y=first_derivative,
            mode='lines',
            name='Rate of Change',
            line=dict(width=2)
        ))
        
        # Add second derivative
        fig.add_trace(go.Scatter(
            x=years[:-1],
            y=second_derivative,
            mode='lines',
            name='Acceleration',
            line=dict(width=2, dash='dash')
        ))
        
        # Update layout
        fig.update_layout(
            title="GCV Pattern Derivatives",
            xaxis_title="Policy Year",
            yaxis_title="Rate of Change",
            showlegend=True,
            hovermode='x unified'
        )
        return fig
    
    def plot_3d_gcv_surface(self) -> go.Figure:
        """Plot 3D surface of GCV patterns."""
        years = np.arange(0, 31)
        premiums = np.linspace(5000, 50000, 20)
        face_amounts = np.linspace(50000, 500000, 20)
        
        # Create meshgrid
        Y, Z = np.meshgrid(premiums, face_amounts)
        X = np.zeros_like(Y)
        
        # Calculate GCV for each point
        for i, year in enumerate(years):
            gcv_slice = np.zeros_like(Y)
            for j in range(len(premiums)):
                for k in range(len(face_amounts)):
                    gcv = self.calculator.calculate_gcv(
                        policy_year=year,
                        premium=premiums[j],
                        face_amount=face_amounts[k]
                    )
                    gcv_slice[k, j] = gcv / face_amounts[k]  # Convert to percentage
            
            if i == 0:
                values = gcv_slice[np.newaxis, :, :]
            else:
                values = np.concatenate([values, gcv_slice[np.newaxis, :, :]])
                
        # Create animation frames
        frames = []
        for i in range(len(years)):
            frame = go.Frame(
                data=[go.Surface(
                    x=Y,
                    y=Z,
                    z=values[i],
                    colorscale='Viridis',
                    showscale=True
                )],
                name=str(years[i])
            )
            frames.append(frame)
            
        # Create base figure
        fig = go.Figure(
            data=[go.Surface(
                x=Y,
                y=Z,
                z=values[0],
                colorscale='Viridis',
                showscale=True
            )],
            frames=frames
        )
        
        # Add slider
        fig.update_layout(
            title="GCV Surface Over Time",
            scene=dict(
                xaxis_title="Premium",
                yaxis_title="Face Amount",
                zaxis_title="GCV Factor"
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[dict(
                    label="Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=100, redraw=True),
                        fromcurrent=True,
                        mode='immediate'
                    )]
                )]
            )],
            sliders=[dict(
                steps=[dict(
                    method='animate',
                    args=[[str(year)], dict(
                        mode='immediate',
                        frame=dict(duration=100, redraw=True),
                        transition=dict(duration=0)
                    )],
                    label=str(year)
                ) for year in years]
            )]
        )
        return fig
