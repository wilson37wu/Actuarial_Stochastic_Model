"""
ALM Excel Report Module

This module provides Excel report generation functionality for the ALM framework.
"""

import pandas as pd
from datetime import datetime
import os
from typing import Dict

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