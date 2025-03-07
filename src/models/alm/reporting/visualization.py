"""
ALM Visualization Module

This module provides visualization functionality for the ALM framework,
including charts and dashboards.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict
from datetime import datetime
import os

def create_cashflow_chart(
    liability_cashflows: List[float],
    asset_cashflows: List[float],
    years: List[int],
    title: str = "Asset-Liability Cash Flow Matching"
) -> plt.Figure:
    """Create a bar chart comparing asset and liability cash flows."""
    fig = plt.figure(figsize=(10, 6))
    x = np.arange(len(years))
    width = 0.35
    
    plt.bar(x - width/2, liability_cashflows, width, label='Liabilities', color='red', alpha=0.6)
    plt.bar(x + width/2, asset_cashflows, width, label='Assets', color='blue', alpha=0.6)
    
    plt.xlabel('Year')
    plt.ylabel('Cash Flow Amount ($)')
    plt.title(title)
    plt.xticks(x, years)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    return fig

def create_funding_ratio_chart(
    funding_ratios: List[float],
    years: List[int],
    target_ratio: float = 1.05,
    min_ratio: float = 0.95
) -> plt.Figure:
    """Create a line chart showing funding ratio evolution."""
    fig = plt.figure(figsize=(10, 6))
    
    plt.plot(years, funding_ratios, 'b-', label='Funding Ratio', marker='o')
    plt.axhline(y=target_ratio, color='g', linestyle='--', label='Target Ratio')
    plt.axhline(y=min_ratio, color='r', linestyle='--', label='Minimum Ratio')
    
    plt.fill_between(years, min_ratio, target_ratio, color='yellow', alpha=0.2, label='Warning Zone')
    plt.fill_between(years, [min_ratio] * len(years), [min(min_ratio, min(funding_ratios))] * len(years),
                    color='red', alpha=0.2, label='Danger Zone')
    
    plt.xlabel('Year')
    plt.ylabel('Funding Ratio')
    plt.title('Funding Ratio Evolution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    return fig

def create_risk_metrics_chart(
    metrics: Dict[str, List[float]],
    years: List[int]
) -> plt.Figure:
    """Create a multi-line chart showing risk metrics evolution."""
    fig = plt.figure(figsize=(12, 6))
    
    for metric_name, values in metrics.items():
        plt.plot(years, values, marker='o', label=metric_name)
    
    plt.xlabel('Year')
    plt.ylabel('Value')
    plt.title('Risk Metrics Evolution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    return fig

def create_summary_dashboard(
    figs: List[plt.Figure],
    output_dir: str = "outputs"
) -> str:
    """
    Create a summary dashboard combining multiple charts.
    
    Returns:
        str: Path to the generated dashboard image
    """
    # Create a new figure with a specific size
    dashboard = plt.figure(figsize=(20, 15))
    
    # Create a grid of subplots
    gs = dashboard.add_gridspec(2, 2)
    
    # Add each figure to the dashboard
    for i, fig in enumerate(figs):
        row = i // 2
        col = i % 2
        
        # Create a new subplot
        ax = dashboard.add_subplot(gs[row, col])
        
        # Copy the content from the original figure
        for ax_orig in fig.axes:
            # Store all lines and their properties
            lines_data = []
            for line in ax_orig.lines:
                lines_data.append({
                    'xdata': line.get_xdata(),
                    'ydata': line.get_ydata(),
                    'color': line.get_color(),
                    'label': line.get_label(),
                    'linestyle': line.get_linestyle(),
                    'marker': line.get_marker()
                })
            
            # Store all patches and their properties
            patches_data = []
            for patch in ax_orig.patches:
                patches_data.append({
                    'x': patch.get_x(),
                    'width': patch.get_width(),
                    'height': patch.get_height(),
                    'color': patch.get_facecolor(),
                    'alpha': patch.get_alpha()
                })
            
            # Clear the subplot
            ax.clear()
            
            # Recreate lines
            for line_data in lines_data:
                ax.plot(line_data['xdata'], line_data['ydata'],
                       color=line_data['color'],
                       label=line_data['label'],
                       linestyle=line_data['linestyle'],
                       marker=line_data['marker'])
            
            # Recreate patches
            for patch_data in patches_data:
                new_patch = plt.Rectangle((patch_data['x'], 0),
                                        patch_data['width'],
                                        patch_data['height'],
                                        color=patch_data['color'],
                                        alpha=patch_data['alpha'])
                ax.add_patch(new_patch)
            
            # Copy labels and title
            ax.set_xlabel(ax_orig.get_xlabel())
            ax.set_ylabel(ax_orig.get_ylabel())
            ax.set_title(ax_orig.get_title())
            
            # Add legend if there are labeled artists
            if lines_data and any(ld['label'] and not ld['label'].startswith('_') for ld in lines_data):
                ax.legend()
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Copy axis limits
            ax.set_xlim(ax_orig.get_xlim())
            ax.set_ylim(ax_orig.get_ylim())
    
    # Adjust layout and save
    plt.tight_layout()
    output_file = os.path.join(output_dir, f"alm_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    dashboard.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close('all')
    
    return output_file 