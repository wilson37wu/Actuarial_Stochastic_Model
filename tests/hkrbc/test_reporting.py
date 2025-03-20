"""
Tests for HKRBC reporting functionality.
"""

import unittest
import os
import pandas as pd
from src.hkrbc.capital_calculator.base import RiskChargeResult
from src.hkrbc.reporting.excel_report import ExcelReportGenerator
from src.hkrbc.reporting.pdf_report import PDFReportGenerator

class TestReporting(unittest.TestCase):
    """Test report generation functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample risk charge results
        self.market_risk = RiskChargeResult(
            risk_name="Market Risk",
            gross_charge=1000000,
            net_charge=800000,
            diversification_benefit=200000,
            sub_risks={
                "Interest Rate Risk": RiskChargeResult(
                    risk_name="Interest Rate Risk",
                    gross_charge=500000,
                    net_charge=500000
                ),
                "Equity Risk": RiskChargeResult(
                    risk_name="Equity Risk",
                    gross_charge=600000,
                    net_charge=600000
                )
            }
        )
        
        self.insurance_risk = RiskChargeResult(
            risk_name="Insurance Risk",
            gross_charge=800000,
            net_charge=600000,
            diversification_benefit=200000,
            sub_risks={
                "Mortality Risk": RiskChargeResult(
                    risk_name="Mortality Risk",
                    gross_charge=400000,
                    net_charge=400000
                ),
                "Lapse Risk": RiskChargeResult(
                    risk_name="Lapse Risk",
                    gross_charge=500000,
                    net_charge=500000
                )
            }
        )
        
        self.total_result = RiskChargeResult(
            risk_name="Total Capital Requirement",
            gross_charge=2000000,
            net_charge=1500000,
            diversification_benefit=500000,
            sub_risks={
                "Market Risk": self.market_risk,
                "Insurance Risk": self.insurance_risk
            }
        )
        
        # Create output directory
        self.output_dir = "test_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def test_excel_report(self):
        """Test Excel report generation."""
        excel_path = os.path.join(self.output_dir, "hkrbc_report.xlsx")
        
        # Generate report
        generator = ExcelReportGenerator()
        generator.generate_report(self.total_result, excel_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(excel_path))
        
        # Load and verify content
        df = pd.read_excel(excel_path, sheet_name="Risk Summary")
        
        # Check main risk modules
        self.assertIn("Market Risk", df["Risk Module"].values)
        self.assertIn("Insurance Risk", df["Risk Module"].values)
        
        # Check totals
        total_row = df.iloc[-1]
        self.assertEqual(total_row["Gross Charge"], 2000000)
        self.assertEqual(total_row["Net Charge"], 1500000)
        
    def test_pdf_report(self):
        """Test PDF report generation."""
        pdf_path = os.path.join(self.output_dir, "hkrbc_report.pdf")
        
        # Generate report
        generator = PDFReportGenerator()
        generator.generate_report(self.total_result, pdf_path)
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 0)
        
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

if __name__ == '__main__':
    unittest.main()
