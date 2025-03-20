"""
Excel report generator for HKRBC capital calculations.
"""

import pandas as pd
from typing import Dict
from ..capital_calculator.base import RiskChargeResult

class ExcelReportGenerator:
    """Generates Excel reports for HKRBC capital calculations."""
    
    def __init__(self):
        """Initialize report generator."""
        self.risk_order = [
            'Market Risk',
            'Insurance Risk',
            'Operational Risk'
        ]
        
        self.market_risk_order = [
            'Interest Rate Risk',
            'Credit Spread Risk',
            'Equity Risk',
            'Property Risk',
            'Currency Risk'
        ]
        
        self.insurance_risk_order = [
            'Mortality Risk',
            'Longevity Risk',
            'Lapse Risk'
        ]
        
    def _create_risk_summary_df(
        self,
        result: RiskChargeResult,
        indent_level: int = 0
    ) -> pd.DataFrame:
        """
        Create summary DataFrame for a risk module and its sub-risks.
        
        Args:
            result: Risk charge result to summarize
            indent_level: Indentation level for risk name
            
        Returns:
            DataFrame with risk summary
        """
        rows = []
        
        # Add main risk row
        rows.append({
            'Risk Module': '  ' * indent_level + result.risk_name,
            'Gross Charge': result.gross_charge,
            'Diversification Benefit': result.diversification_benefit,
            'Net Charge': result.net_charge
        })
        
        # Add sub-risks in specified order
        if result.sub_risks:
            order_map = {
                'Market Risk': self.market_risk_order,
                'Insurance Risk': self.insurance_risk_order
            }
            
            order = order_map.get(result.risk_name, [])
            sub_risks = result.sub_risks
            
            # Sort sub-risks if order is specified
            if order:
                sorted_risks = [(name, sub_risks[name]) for name in order
                              if name in sub_risks]
            else:
                sorted_risks = sub_risks.items()
            
            # Add each sub-risk
            for _, sub_result in sorted_risks:
                sub_df = self._create_risk_summary_df(
                    sub_result,
                    indent_level + 1
                )
                rows.extend(sub_df.to_dict('records'))
        
        return pd.DataFrame(rows)
        
    def generate_report(
        self,
        result: RiskChargeResult,
        output_path: str
    ) -> None:
        """
        Generate Excel report with HKRBC capital calculations.
        
        Args:
            result: Overall risk charge result
            output_path: Path to save Excel file
        """
        # Create Excel writer
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        workbook = writer.book
        
        # Create summary sheet
        summary_df = self._create_risk_summary_df(result)
        summary_df.to_excel(
            writer,
            sheet_name='Risk Summary',
            index=False,
            startrow=1
        )
        
        # Get worksheet
        worksheet = writer.sheets['Risk Summary']
        
        # Add title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })
        worksheet.merge_range(
            'A1:D1',
            'HKRBC Capital Requirements Summary',
            title_format
        )
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0',
            'border': 1
        })
        
        percent_format = workbook.add_format({
            'num_format': '0.00%',
            'border': 1
        })
        
        # Apply formats
        for col in range(len(summary_df.columns)):
            worksheet.write(1, col, summary_df.columns[col], header_format)
            
        # Set column formats
        worksheet.set_column('A:A', 40)  # Risk Module
        worksheet.set_column('B:D', 20, number_format)  # Number columns
        
        # Add total row
        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0'
        })
        
        last_row = len(summary_df) + 2
        worksheet.write(
            last_row, 0,
            'Total Capital Requirement',
            total_format
        )
        
        for col in range(1, 4):
            worksheet.write(
                last_row, col,
                f'=SUM({chr(65+col)}3:{chr(65+col)}{last_row})',
                total_format
            )
        
        # Save workbook
        writer.close()
