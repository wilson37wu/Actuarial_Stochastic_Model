"""
Example script to generate HKRBC capital requirement reports.
"""

import os
from src.hkrbc.capital_calculator.base import RiskChargeResult
from src.hkrbc.reporting.excel_report import ExcelReportGenerator
from src.hkrbc.reporting.pdf_report import PDFReportGenerator

def create_sample_results():
    """Create sample risk charge results for demonstration."""
    # Market Risk Components
    interest_rate = RiskChargeResult(
        risk_name="Interest Rate Risk",
        gross_charge=500_000_000,
        net_charge=450_000_000,
        diversification_benefit=50_000_000
    )
    
    equity = RiskChargeResult(
        risk_name="Equity Risk",
        gross_charge=300_000_000,
        net_charge=270_000_000,
        diversification_benefit=30_000_000
    )
    
    market_risk = RiskChargeResult(
        risk_name="Market Risk",
        gross_charge=800_000_000,
        net_charge=680_000_000,
        diversification_benefit=120_000_000,
        sub_risks={
            "Interest Rate Risk": interest_rate,
            "Equity Risk": equity
        }
    )
    
    # Insurance Risk Components
    mortality = RiskChargeResult(
        risk_name="Mortality Risk",
        gross_charge=200_000_000,
        net_charge=180_000_000,
        diversification_benefit=20_000_000
    )
    
    longevity = RiskChargeResult(
        risk_name="Longevity Risk",
        gross_charge=150_000_000,
        net_charge=135_000_000,
        diversification_benefit=15_000_000
    )
    
    lapse = RiskChargeResult(
        risk_name="Lapse Risk",
        gross_charge=250_000_000,
        net_charge=225_000_000,
        diversification_benefit=25_000_000
    )
    
    insurance_risk = RiskChargeResult(
        risk_name="Insurance Risk",
        gross_charge=600_000_000,
        net_charge=480_000_000,
        diversification_benefit=120_000_000,
        sub_risks={
            "Mortality Risk": mortality,
            "Longevity Risk": longevity,
            "Lapse Risk": lapse
        }
    )
    
    # Operational Risk
    operational_risk = RiskChargeResult(
        risk_name="Operational Risk",
        gross_charge=100_000_000,
        net_charge=100_000_000,
        diversification_benefit=0
    )
    
    # Total Capital Requirement
    total_result = RiskChargeResult(
        risk_name="Total Capital Requirement",
        gross_charge=1_500_000_000,
        net_charge=1_200_000_000,
        diversification_benefit=300_000_000,
        sub_risks={
            "Market Risk": market_risk,
            "Insurance Risk": insurance_risk,
            "Operational Risk": operational_risk
        }
    )
    
    return total_result

def main():
    """Generate sample HKRBC reports."""
    # Create output directory
    output_dir = "output/hkrbc_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate sample results
    results = create_sample_results()
    
    # Generate Excel report
    excel_path = os.path.join(output_dir, "hkrbc_capital_requirements.xlsx")
    excel_generator = ExcelReportGenerator()
    excel_generator.generate_report(results, excel_path)
    print(f"Excel report generated: {excel_path}")
    
    # Generate PDF report
    pdf_path = os.path.join(output_dir, "hkrbc_capital_requirements.pdf")
    pdf_generator = PDFReportGenerator()
    pdf_generator.generate_report(results, pdf_path)
    print(f"PDF report generated: {pdf_path}")

if __name__ == "__main__":
    main()
