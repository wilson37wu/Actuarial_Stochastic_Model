"""Visualization module for the dashboard."""
import streamlit as st
import plotly.graph_objects as go
from typing import Optional

class Visualization:
    """Handle visualization functionality."""
    
    def __init__(self):
        """Initialize visualization settings."""
        self.chart_theme = {
            'layout': {
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white',
                'font': {
                    'color': 'black',
                    'size': 12
                },
                'xaxis': {
                    'gridcolor': '#E5E5E5',
                    'zerolinecolor': '#E5E5E5',
                    'title': {
                        'font': {
                            'color': 'black',
                            'size': 14
                        }
                    },
                    'tickfont': {
                        'color': 'black',
                        'size': 12
                    }
                },
                'yaxis': {
                    'gridcolor': '#E5E5E5',
                    'zerolinecolor': '#E5E5E5',
                    'title': {
                        'font': {
                            'color': 'black',
                            'size': 14
                        }
                    },
                    'tickfont': {
                        'color': 'black',
                        'size': 12
                    }
                }
            }
        }
    
    def create_plot_container(self, fig: go.Figure, title: str):
        """Create a plot container with consistent styling.
        
        Args:
            fig: Plotly figure to display
            title: Title for the plot
        """
        # Apply theme to figure
        theme_layout = self.chart_theme['layout'].copy()
        
        # Add title configuration
        theme_layout['title'] = {
            'text': title,
            'font': {
                'color': 'black',
                'size': 16,
                'weight': 'bold'
            }
        }
        
        # Add legend configuration
        theme_layout['showlegend'] = True
        theme_layout['legend'] = {
            'yanchor': "top",
            'y': 0.99,
            'xanchor': "left",
            'x': 0.01,
            'bgcolor': 'white',
            'bordercolor': 'black',
            'borderwidth': 1,
            'font': {'color': 'black', 'size': 12}
        }
        
        # Add margin configuration
        theme_layout['margin'] = {'l': 50, 'r': 50, 't': 50, 'b': 50}
        
        # Update layout with theme
        fig.update_layout(**theme_layout)
        
        # Update trace colors for better contrast
        colors = [
            '#1f77b4',  # Blue
            '#d62728',  # Red
            '#2ca02c',  # Green
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Yellow-green
            '#17becf'   # Cyan
        ]
        
        for i, trace in enumerate(fig.data):
            if trace.type == 'scatter':
                trace.line.color = colors[i % len(colors)]
                trace.line.width = 2
            elif trace.type == 'bar':
                trace.marker.color = colors[i % len(colors)]
                trace.marker.line.width = 1
                trace.marker.line.color = 'black'
            elif trace.type == 'pie':
                trace.marker.colors = colors
                trace.textfont.color = 'black'
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)
    
    def apply_theme(self):
        """Apply theme to all plots."""
        # Set default plotly theme
        import plotly.io as pio
        pio.templates.default = "plotly_white"
        
        # Update global font
        pio.templates["plotly_white"].layout.font.update(
            family="Arial, sans-serif",
            size=12,
            color="black"
        )
