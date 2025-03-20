"""
PDF report generator for HKRBC capital calculations.
"""

from typing import Dict, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from ..capital_calculator.base import RiskChargeResult

class PDFReportGenerator:
    """Generates PDF reports for HKRBC capital calculations."""
    
    def __init__(self):
        """Initialize report generator."""
        self.styles = getSampleStyleSheet()
        
        # Add custom styles
        self.styles.add(
            ParagraphStyle(
                name='RiskModule',
                parent=self.styles['Normal'],
                leftIndent=20,
                spaceAfter=6
            )
        )
        
    def _format_number(self, number: float) -> str:
        """Format number with thousands separator."""
        return f"{number:,.0f}"
        
    def _create_risk_summary_table(
        self,
        result: RiskChargeResult,
        indent_level: int = 0
    ) -> List[List[str]]:
        """
        Create table data for a risk module and its sub-risks.
        
        Args:
            result: Risk charge result to summarize
            indent_level: Indentation level for risk name
            
        Returns:
            List of table rows
        """
        rows = []
        
        # Add header row
        if indent_level == 0:
            rows.append([
                'Risk Module',
                'Gross Charge',
                'Diversification\nBenefit',
                'Net Charge'
            ])
        
        # Add main risk row
        rows.append([
            '  ' * indent_level + result.risk_name,
            self._format_number(result.gross_charge),
            self._format_number(result.diversification_benefit),
            self._format_number(result.net_charge)
        ])
        
        # Add sub-risks
        if result.sub_risks:
            for sub_result in result.sub_risks.values():
                sub_rows = self._create_risk_summary_table(
                    sub_result,
                    indent_level + 1
                )[1:]  # Skip header row for sub-risks
                rows.extend(sub_rows)
        
        return rows
        
    def generate_report(
        self,
        result: RiskChargeResult,
        output_path: str
    ) -> None:
        """
        Generate PDF report with HKRBC capital calculations.
        
        Args:
            result: Overall risk charge result
            output_path: Path to save PDF file
        """
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create story elements
        story = []
        
        # Add title
        title = Paragraph(
            'HKRBC Capital Requirements Report',
            self.styles['Title']
        )
        story.append(title)
        
        # Add date
        date = Paragraph(
            f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            self.styles['Normal']
        )
        story.append(date)
        story.append(Spacer(1, 12))
        
        # Create summary table
        table_data = self._create_risk_summary_table(result)
        table = Table(table_data)
        
        # Style the table
        style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ])
        
        table.setStyle(style)
        story.append(table)
        
        # Add notes
        story.append(Spacer(1, 20))
        notes = [
            Paragraph('Notes:', self.styles['Heading2']),
            Paragraph(
                '1. All figures are in HKD.',
                self.styles['Normal']
            ),
            Paragraph(
                '2. Calculations follow Cap 41R requirements.',
                self.styles['Normal']
            ),
            Paragraph(
                '3. Diversification benefits are calculated using correlation matrices from Cap 41R Schedule 1.',
                self.styles['Normal']
            )
        ]
        story.extend(notes)
        
        # Build document
        doc.build(story)
