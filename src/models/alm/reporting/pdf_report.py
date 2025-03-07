"""
ALM PDF Report Module

This module generates comprehensive PDF reports for the ALM framework,
documenting analysis, calculations, and results.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from datetime import datetime
import os
from typing import List, Dict
import matplotlib.pyplot as plt

def format_currency(value: float) -> str:
    """Format number as currency string."""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format number as percentage string."""
    return f"{value:.2%}"

def create_written_report(
    strategy_params: Dict,
    liability_data: Dict,
    asset_data: Dict,
    risk_metrics: Dict[str, List[float]],
    stress_results: Dict[str, float],
    charts_path: str,
    output_dir: str = "outputs"
) -> None:
    """
    Generate a comprehensive written report in PDF format.
    
    Args:
        strategy_params: Dictionary of ALM strategy parameters
        liability_data: Dictionary containing liability analysis data
        asset_data: Dictionary containing asset analysis data
        risk_metrics: Dictionary of risk metrics
        stress_results: Dictionary of stress test results
        charts_path: Path to the dashboard image
        output_dir: Directory for output files
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"alm_written_report_{timestamp}.pdf")
    
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create custom style for tables
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    # Build content
    content = []
    
    # Title
    content.append(Paragraph("Asset Liability Management (ALM) Analysis Report", title_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 24))
    
    # Executive Summary
    content.append(Paragraph("Executive Summary", heading_style))
    content.append(Spacer(1, 12))
    summary_text = f"""
    This report presents a comprehensive analysis of the Asset-Liability Management (ALM) strategy 
    with initial assets of {format_currency(strategy_params['Initial Assets'])} and a target funding 
    ratio of {format_percentage(strategy_params['Target Funding Ratio'])}. The analysis includes cash flow 
    projections, risk metrics, and stress testing results.
    """
    content.append(Paragraph(summary_text, normal_style))
    content.append(Spacer(1, 24))
    
    # Strategy Parameters
    content.append(Paragraph("Strategy Parameters", heading_style))
    content.append(Spacer(1, 12))
    param_data = [["Parameter", "Value"]]
    for key, value in strategy_params.items():
        if isinstance(value, float):
            if "ratio" in key.lower():
                value = format_percentage(value)
            else:
                value = format_currency(value)
        param_data.append([key, value])
    
    param_table = Table(param_data, colWidths=[4*inch, 2*inch])
    param_table.setStyle(table_style)
    content.append(param_table)
    content.append(Spacer(1, 24))
    
    # Cash Flow Analysis
    content.append(Paragraph("Cash Flow Analysis", heading_style))
    content.append(Spacer(1, 12))
    
    cf_text = f"""
    The analysis projects cash flows over a {len(liability_data['cash_flows'])} year period. 
    The liability cash flows show an annual growth rate of 2%, while asset cash flows are 
    structured to provide increasing coverage over time. The present value of assets is 
    {format_currency(asset_data['present_value'])} against liabilities of 
    {format_currency(liability_data['present_value'])}.
    """
    content.append(Paragraph(cf_text, normal_style))
    content.append(Spacer(1, 24))
    
    # Risk Metrics
    content.append(Paragraph("Risk Metrics", heading_style))
    content.append(Spacer(1, 12))
    
    risk_text = f"""
    Key risk metrics show a duration of {risk_metrics['Duration'][-1]:.2f} years and 
    convexity of {risk_metrics['Convexity'][-1]:.2f}. The stress testing reveals a potential 
    impact of {format_percentage(stress_results['Percentage Change'])} under combined market shocks.
    """
    content.append(Paragraph(risk_text, normal_style))
    content.append(Spacer(1, 24))
    
    # Stress Test Results
    content.append(Paragraph("Stress Test Results", heading_style))
    content.append(Spacer(1, 12))
    
    stress_data = [["Metric", "Value"]]
    for key, value in stress_results.items():
        if isinstance(value, float):
            if "percentage" in key.lower():
                value = format_percentage(value)
            else:
                value = format_currency(value)
        stress_data.append([key, value])
    
    stress_table = Table(stress_data, colWidths=[4*inch, 2*inch])
    stress_table.setStyle(table_style)
    content.append(stress_table)
    content.append(Spacer(1, 24))
    
    # Visualizations
    content.append(Paragraph("Visualizations", heading_style))
    content.append(Spacer(1, 12))
    
    # Add the dashboard image
    img = Image(charts_path)
    img.drawHeight = 6*inch
    img.drawWidth = 8*inch
    content.append(img)
    content.append(Spacer(1, 24))
    
    # Conclusions and Recommendations
    content.append(Paragraph("Conclusions and Recommendations", heading_style))
    content.append(Spacer(1, 12))
    
    conclusions_text = f"""
    Based on the analysis:
    
    1. The current funding ratio shows {'adequate' if stress_results['Percentage Change'] > -0.1 else 'concerning'} 
       resilience to market stresses.
    
    2. Duration gap is {'within' if abs(risk_metrics['Duration'][-1]) <= strategy_params['Max Duration Gap'] else 'outside'} 
       the target range.
    
    3. Cash flow matching indicates {'sufficient' if asset_data['present_value'] >= liability_data['present_value'] else 'insufficient'} 
       coverage of projected liabilities.
    
    Recommendations:
    
    1. {'Maintain current strategy' if stress_results['Percentage Change'] > -0.1 else 'Consider additional risk mitigation'}
    
    2. {'Continue monitoring' if abs(risk_metrics['Duration'][-1]) <= strategy_params['Max Duration Gap'] else 'Adjust portfolio duration'}
    
    3. {'Regular stress testing' if asset_data['present_value'] >= liability_data['present_value'] else 'Increase funding level'}
    """
    content.append(Paragraph(conclusions_text, normal_style))
    
    # Build the PDF
    doc.build(content)
    
    print(f"Written report generated: {output_file}") 