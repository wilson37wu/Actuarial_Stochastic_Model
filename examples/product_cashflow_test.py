"""Example script demonstrating product cash flow projections with assumption exports.

This script shows how to:
1. Set up a liability model with various assumptions
2. Project cash flows for different products
3. Export assumptions to Excel for audit purposes
"""

from datetime import date
from pathlib import Path

import pandas as pd

from actuarial_stochastic_model.models.liabilities import (
    LiabilityModel, MortalityTable, LapseAssumption, InflationAssumption
)
from actuarial_stochastic_model.models.products import TermInsurance, WholeLifeInsurance
from actuarial_stochastic_model.enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy
)

def main():
    # Set up assumptions
    mortality = MortalityTable.from_csv('data/assumptions/mortality_rates.csv')
    lapse = LapseAssumption.from_csv('data/assumptions/lapse_rates.csv')
    inflation = InflationAssumption.from_csv('data/assumptions/inflation_rates.csv')
    
    # Create liability model
    model = LiabilityModel(
        mortality_table=mortality,
        lapse_assumption=lapse,
        inflation_assumption=inflation,
        minimum_dividend_rate=0.01,
        shareholder_cost_rate=0.02
    )
    
    # Add sample contracts
    term_insurance = TermInsurance(
        policy_number="T123456",
        issue_date=date(2024, 1, 1),
        term_years=20,
        sum_assured=100000,
        premium=1200,
        sex=Sex.MALE,
        underwriting_class=UnderwritingClass.STANDARD,
        smoking_status=SmokingStatus.NON_SMOKER,
        occupation_class=OccupationClass.CLASS_1
    )
    
    whole_life = WholeLifeInsurance(
        policy_number="WL789012",
        issue_date=date(2024, 1, 1),
        sum_assured=200000,
        premium=2400,
        sex=Sex.FEMALE,
        underwriting_class=UnderwritingClass.PREFERRED,
        smoking_status=SmokingStatus.NON_SMOKER,
        occupation_class=OccupationClass.CLASS_1,
        dividend_option=DividendOption.PAID_UP_ADDITIONS,
        investment_strategy=InvestmentStrategy.BALANCED
    )
    
    model.add_contract(term_insurance)
    model.add_contract(whole_life)
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Project cash flows and export assumptions
    valuation_date = date(2024, 1, 1)
    cashflows = model.project_cashflows(
        valuation_date=valuation_date,
        projection_years=30,
        time_step='M',
        export_assumptions=True,
        assumptions_file=str(output_dir / "model_assumptions.xlsx")
    )
    
    # Save cash flow projections
    cashflows.to_excel(output_dir / "cashflow_projections.xlsx")
    
    print("Cash flow projections completed!")
    print(f"Results saved to: {output_dir}")
    print("Files generated:")
    print("1. cashflow_projections.xlsx - Detailed cash flow projections")
    print("2. model_assumptions.xlsx - All assumptions used in the model for audit")

if __name__ == "__main__":
    main()