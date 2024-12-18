"""
Example script demonstrating the use of the liability model.
"""
from datetime import date, timedelta
import pandas as pd

from src.liability import InsuranceContract, LiabilityModel

def create_sample_contract(
    contract_id: str,
    issue_date: date,
    term_years: int,
    annual_premium: float,
    death_benefit: float,
    annual_expense: float
) -> InsuranceContract:
    """Create a sample insurance contract with monthly cash flows."""
    maturity_date = date(issue_date.year + term_years, issue_date.month, issue_date.day)
    
    # Create monthly cash flow patterns
    premium_pattern = {}
    benefit_pattern = {}
    expense_pattern = {}
    
    current_date = issue_date
    monthly_premium = annual_premium / 12
    monthly_expense = annual_expense / 12
    
    while current_date <= maturity_date:
        premium_pattern[current_date] = monthly_premium
        benefit_pattern[current_date] = death_benefit / (12 * term_years)  # Simple linear death benefit
        expense_pattern[current_date] = monthly_expense
        
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, current_date.day)
        else:
            current_date = date(current_date.year, current_date.month + 1, current_date.day)
    
    return InsuranceContract(
        id=contract_id,
        issue_date=issue_date,
        maturity_date=maturity_date,
        premium_pattern=premium_pattern,
        benefit_pattern=benefit_pattern,
        expense_pattern=expense_pattern
    )

def main():
    # Create sample contracts
    contracts = [
        create_sample_contract(
            contract_id="TERM_001",
            issue_date=date(2024, 1, 1),
            term_years=20,
            annual_premium=1200,  # $1,200 annual premium
            death_benefit=100000,  # $100,000 death benefit
            annual_expense=100    # $100 annual expense
        ),
        create_sample_contract(
            contract_id="TERM_002",
            issue_date=date(2024, 6, 1),
            term_years=10,
            annual_premium=600,   # $600 annual premium
            death_benefit=50000,  # $50,000 death benefit
            annual_expense=50     # $50 annual expense
        )
    ]
    
    # Initialize liability model
    liability_model = LiabilityModel(contracts)
    
    # Project cash flows - monthly
    monthly_cf = liability_model.project_cashflows(
        valuation_date=date(2024, 1, 1),
        projection_years=30,
        frequency='monthly'
    )
    
    # Project cash flows - annual
    annual_cf = liability_model.project_cashflows(
        valuation_date=date(2024, 1, 1),
        projection_years=30,
        frequency='annual'
    )
    
    # Export results to Excel
    with pd.ExcelWriter('liability_projections.xlsx') as writer:
        monthly_cf.to_excel(writer, sheet_name='Monthly Cashflows', index=False)
        annual_cf.to_excel(writer, sheet_name='Annual Cashflows', index=False)
    
    print("Liability projections have been exported to 'liability_projections.xlsx'")
    
    # Display first few rows of monthly projections
    print("\nFirst few rows of monthly projections:")
    print(monthly_cf.head())

if __name__ == "__main__":
    main()
