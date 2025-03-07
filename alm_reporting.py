"""
ALM Reporting Module

This module handles visualization and reporting for the ALM framework,
including charts and Excel report generation.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict
import numpy as np
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

def create_excel_report(
    strategy_params: Dict,
    liability_data: pd.DataFrame,
    asset_data: pd.DataFrame,
    risk_metrics: pd.DataFrame,
    stress_tests: pd.DataFrame,
    output_dir: str = "outputs"
) -> str:
    """
    Create a comprehensive Excel report with multiple sheets.
    
    Args:
        strategy_params: Dictionary of ALM strategy parameters
        liability_data: DataFrame of liability cash flows
        asset_data: DataFrame of asset cash flows
        risk_metrics: DataFrame of risk metrics
        stress_tests: DataFrame of stress test results
        output_dir: Directory for output files
        
    Returns:
        str: Path to the generated Excel file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"alm_report_{timestamp}.xlsx")
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write strategy parameters
        pd.DataFrame([strategy_params]).T.to_excel(writer, sheet_name='Strategy Parameters')
        
        # Write cash flow data
        liability_data.to_excel(writer, sheet_name='Liability Cash Flows')
        asset_data.to_excel(writer, sheet_name='Asset Cash Flows')
        
        # Write risk metrics
        risk_metrics.to_excel(writer, sheet_name='Risk Metrics')
        
        # Write stress test results
        stress_tests.to_excel(writer, sheet_name='Stress Tests')
        
        # Get workbook and create formats
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#0066cc',
            'border': 1
        })
        
        # Format each worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Format headers
            for col_num, value in enumerate(pd.DataFrame([strategy_params]).T.columns.values):
                worksheet.write(0, col_num + 1, value, header_format)
            
            # Adjust column widths
            worksheet.set_column('A:Z', 15)
            
            # Add conditional formatting for risk metrics
            if sheet_name == 'Risk Metrics':
                worksheet.conditional_format('B2:Z1000', {
                    'type': '3_color_scale',
                    'min_color': "#63BE7B",
                    'mid_color': "#FFEB84",
                    'max_color': "#F8696B"
                })
    
    return output_file

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

def generate_alm_report(
    strategy: 'ALMStrategy',
    liability_cfs: List[float],
    asset_cfs: List[float],
    risk_metrics: Dict[str, List[float]],
    stress_results: Dict[str, float],
    output_dir: str = "outputs"
) -> None:
    """
    Generate a comprehensive ALM report including visualizations and Excel output.
    
    Args:
        strategy: ALM strategy instance
        liability_cfs: List of liability cash flows
        asset_cfs: List of asset cash flows
        risk_metrics: Dictionary of risk metrics
        stress_results: Dictionary of stress test results
        output_dir: Directory for output files
    """
    # Create DataFrames for reporting
    years = list(range(1, len(liability_cfs) + 1))
    
    liability_df = pd.DataFrame({
        'Year': years,
        'Cash Flow': liability_cfs,
        'Present Value': [cf / (1 + 0.05)**t for t, cf in enumerate(liability_cfs, 1)]
    })
    
    asset_df = pd.DataFrame({
        'Year': years,
        'Cash Flow': asset_cfs,
        'Present Value': [cf / (1 + 0.05)**t for t, cf in enumerate(asset_cfs, 1)]
    })
    
    risk_metrics_df = pd.DataFrame(risk_metrics, index=years)
    
    stress_df = pd.DataFrame([stress_results]).T
    
    # Create visualizations
    cashflow_chart = create_cashflow_chart(liability_cfs, asset_cfs, years)
    funding_ratio_chart = create_funding_ratio_chart(
        [a/l for a, l in zip(asset_cfs, liability_cfs)],
        years
    )
    risk_chart = create_risk_metrics_chart(risk_metrics, years)
    
    # Generate Excel report
    strategy_params = {
        'Initial Assets': strategy.initial_assets,
        'Target Funding Ratio': strategy.target_funding_ratio,
        'Max Duration Gap': strategy.max_duration_gap,
        'Min Liquidity Ratio': strategy.min_liquidity_ratio
    }
    
    excel_file = create_excel_report(
        strategy_params,
        liability_df,
        asset_df,
        risk_metrics_df,
        stress_df,
        output_dir
    )
    
    # Create and save dashboard
    dashboard_file = create_summary_dashboard([cashflow_chart, funding_ratio_chart, risk_chart], output_dir)
    
    # Prepare data for written report
    liability_data = {
        'cash_flows': liability_cfs,
        'present_value': sum(cf / (1 + 0.05)**t for t, cf in enumerate(liability_cfs, 1))
    }
    
    asset_data = {
        'cash_flows': asset_cfs,
        'present_value': sum(cf / (1 + 0.05)**t for t, cf in enumerate(asset_cfs, 1))
    }
    
    # Generate written report
    from alm_written_report import create_written_report
    create_written_report(
        strategy_params,
        liability_data,
        asset_data,
        risk_metrics,
        stress_results,
        dashboard_file,
        output_dir
    ) 