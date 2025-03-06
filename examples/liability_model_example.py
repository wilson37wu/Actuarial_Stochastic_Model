"""
Example script demonstrating the liability model with various product features.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import date, timedelta
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption
)
from src.enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy, PremiumMode, NonForfeitureOption
)
from src.products import (
    TermInsurance, WholeLifeInsurance, ParticipatingWholeLife,
    UniversalLife, UnitLinkedInsurance
)
from src.liability import LiabilityModel
from src.gcv_calculator import GCVParameters, GradingPattern, ProductVariant

# Set up assumptions
mortality = MortalityTable(
    base_rates={  # Simplified rates
        0: 0.001, 30: 0.002, 50: 0.005, 70: 0.01, 90: 0.1
    }
)

lapse = LapseAssumption(
    base_rates={  # Duration-based rates
        0: 0.15, 1: 0.12, 2: 0.09, 5: 0.06, 10: 0.03
    }
)

inflation = InflationAssumption(
    base_rate=0.02,
    wage_inflation=0.03,
    medical_inflation=0.05
)

# Generate sample investment returns
def generate_investment_returns(start_date: date,
                              years: int,
                              mean_return: float = 0.06,
                              volatility: float = 0.12) -> Dict[date, float]:
    """Generate monthly investment returns."""
    monthly_mean = mean_return / 12
    monthly_vol = volatility / np.sqrt(12)
    months = years * 12
    
    returns = np.random.normal(
        monthly_mean,
        monthly_vol,
        months
    )
    
    dates = [
        start_date + timedelta(days=30*i)
        for i in range(months)
    ]
    
    return dict(zip(dates, returns))

# Create sample contracts
valuation_date = date(2024, 1, 1)
investment_returns = generate_investment_returns(
    valuation_date, 
    years=10
)

# Term Insurance
term = TermInsurance(
    policy_number="T001",
    issue_date=valuation_date,
    term_length=20,
    premium=1000,
    face_amount=100000,
    issue_age=35,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.PROFESSIONAL,
    underwriting_class=UnderwritingClass.PREFERRED,
    premium_mode=PremiumMode.ANNUAL
)

# Whole Life with Premium Flexibility
whole_life = WholeLifeInsurance(
    policy_number="WL001",
    issue_date=valuation_date,
    term_length=95,  # To age 95
    premium=2000,
    face_amount=200000,
    issue_age=40,
    sex=Sex.FEMALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.PROFESSIONAL,
    underwriting_class=UnderwritingClass.STANDARD,
    premium_mode=PremiumMode.MONTHLY,
    guaranteed_rate=0.03,
    premium_holiday_available=True,
    max_premium_holiday=24  # 2 years
)

# Participating Whole Life with Dividends
par_whole_life = ParticipatingWholeLife(
    policy_number="PWL001",
    issue_date=valuation_date,
    term_length=95,
    premium=3000,
    face_amount=300000,
    issue_age=45,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.SMOKER,
    occupation_class=OccupationClass.TECHNICAL,
    underwriting_class=UnderwritingClass.STANDARD,
    guaranteed_rate=0.03,
    dividend_option=DividendOption.PAID_UP_ADDITIONS,
    dividend_scale=0.8,
    nonforfeiture_option=NonForfeitureOption.REDUCED_PAID_UP
)

# Universal Life with Flexible Premium
ul = UniversalLife(
    policy_number="UL001",
    issue_date=valuation_date,
    term_length=95,
    premium=1500,
    initial_face_amount=150000,
    issue_age=30,
    sex=Sex.FEMALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.PROFESSIONAL,
    underwriting_class=UnderwritingClass.PREFERRED,
    min_guaranteed_rate=0.02,
    current_credited_rate=0.04,
    cost_of_insurance={  # Simplified COI rates
        30: 0.001, 40: 0.002, 50: 0.004, 60: 0.008
    },
    min_premium=500,
    max_premium=5000,
    premium_mode=PremiumMode.MONTHLY  
)

# Unit-Linked with Target Date Strategy
unit_linked = UnitLinkedInsurance(
    policy_number="UL002",
    issue_date=valuation_date,
    term_length=95,
    premium=2000,
    initial_face_amount=200000,
    issue_age=35,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.PROFESSIONAL,
    underwriting_class=UnderwritingClass.PREFERRED,
    investment_strategy="TARGET_2045",
    fund_allocation={
        "LARGE_CAP_EQUITY": 0.4,
        "INTERNATIONAL_EQUITY": 0.3,
        "CORPORATE_BOND": 0.2,
        "MONEY_MARKET": 0.1
    },
    fund_charges={
        "LARGE_CAP_EQUITY": 0.005,
        "INTERNATIONAL_EQUITY": 0.007,
        "CORPORATE_BOND": 0.004,
        "MONEY_MARKET": 0.002
    },
    premium_mode=PremiumMode.MONTHLY  
)

# Create sample GCV parameters for different product variants
standard_gcv_params = GCVParameters(
    base_percentage=0.7,
    initial_gcv_percentage=0.5,
    grading_years=10,
    minimum_gcv_percentage=0.05,
    grading_pattern=GradingPattern.LINEAR,
    product_variant=ProductVariant.STANDARD
)

high_early_value_params = GCVParameters(
    base_percentage=0.8,
    initial_gcv_percentage=0.6,
    grading_years=12,
    minimum_gcv_percentage=0.06,
    grading_pattern=GradingPattern.S_CURVE,
    product_variant=ProductVariant.HIGH_EARLY_VALUE
)

level_gcv_params = GCVParameters(
    base_percentage=0.75,
    initial_gcv_percentage=0.55,
    grading_years=15,
    minimum_gcv_percentage=0.07,
    grading_pattern=GradingPattern.STEPWISE,
    product_variant=ProductVariant.LEVEL_GCV,
    stepwise_points={
        0: 1.0,
        5: 0.8,
        10: 0.6,
        15: 0.4
    }
)

# Create sample contracts with different GCV parameters
standard_wl = WholeLifeInsurance(
    policy_number="WL001",
    issue_date=date(2024, 1, 1),
    face_amount=100000,
    issue_age=35,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.STANDARD,
    product_variant=ProductVariant.STANDARD,
    gcv_parameters=standard_gcv_params
)

high_early_wl = WholeLifeInsurance(
    policy_number="WL002",
    issue_date=date(2024, 1, 1),
    face_amount=100000,
    issue_age=35,
    sex=Sex.FEMALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.STANDARD,
    product_variant=ProductVariant.HIGH_EARLY_VALUE,
    gcv_parameters=high_early_value_params
)

level_wl = WholeLifeInsurance(
    policy_number="WL003",
    issue_date=date(2024, 1, 1),
    face_amount=100000,
    issue_age=35,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    occupation_class=OccupationClass.STANDARD,
    product_variant=ProductVariant.LEVEL_GCV,
    gcv_parameters=level_gcv_params
)

# Create and run liability model
model = LiabilityModel(
    mortality_table=mortality,
    lapse_assumption=lapse,
    inflation_assumption=inflation,
    investment_returns=investment_returns
)

# Add contracts
model.add_contract(term)
model.add_contract(whole_life)
model.add_contract(par_whole_life)
model.add_contract(ul)
model.add_contract(unit_linked)
model.add_contract(standard_wl)
model.add_contract(high_early_wl)
model.add_contract(level_wl)

# Project cash flows
projection = model.project_cashflows(
    valuation_date=valuation_date,
    projection_years=30,
    time_step='M'
)

# Calculate present values
discount_rates = {
    d: 0.05 for d in projection.time_points  # Simplified 5% discount rate
}
present_values = projection.calculate_present_values(discount_rates)

# Print results
print("\nPresent Value of Cash Flows:")
for cf_type, value in present_values.items():
    print(f"{cf_type}: ${value:,.2f}")

# Create visualizations
def plot_cashflows(projection: pd.DataFrame, filename: str):
    """Plot cash flow components."""
    plt.figure(figsize=(12, 6))
    
    # Main cash flows
    plt.subplot(2, 1, 1)
    plt.plot(projection.index, projection.Premium, label='Premium')
    plt.plot(projection.index, projection.Death_Benefit, label='Death Benefit')
    plt.plot(projection.index, projection.Surrender, label='Surrender')
    plt.title('Main Insurance Cash Flows')
    plt.legend()
    plt.grid(True)
    
    # Additional features
    plt.subplot(2, 1, 2)
    plt.plot(projection.index, projection.Dividends, label='Dividends')
    plt.plot(projection.index, projection.Policy_Loans, label='Policy Loans')
    plt.plot(projection.index, projection.Withdrawals, label='Withdrawals')
    plt.title('Additional Features')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Plot results
df = projection.to_dataframe()
df.index = pd.to_datetime(df.index)  # Convert index to datetime
plot_cashflows(df, 'cashflow_projection.png')

# Plot cash flows by product variant
for contract in model.contracts:
    if contract.product_type == ProductType.WHOLE_LIFE:
        contract_df = df[df['Policy_Number'] == contract.policy_number]
        plt.figure(figsize=(12, 6))
        plt.plot(contract_df.index, contract_df['Surrender'], label='Surrender Value')
        plt.plot(contract_df.index, contract_df['Death_Benefit'], label='Death Benefit')
        plt.plot(contract_df.index, contract_df['Dividends'], label='Dividends')
        plt.title(f'Cash Flows - {contract.product_variant.value}')
        plt.xlabel('Date')
        plt.ylabel('Amount')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'cashflow_projection_{contract.product_variant.value}.png')
        plt.close()

# Export to Excel
writer = pd.ExcelWriter('liability_projection.xlsx', engine='openpyxl')

# Monthly cash flows
df.to_excel(writer, sheet_name='Monthly_Cashflows')

# Annual summaries
annual_df = df.resample('Y').sum()
annual_df.to_excel(writer, sheet_name='Annual_Summary')

# Present values
pd.Series(present_values).to_excel(writer, sheet_name='Present_Values')

# Product mix analysis
product_mix = pd.DataFrame({
    'Product': [c.product_type.name for c in model.contracts],
    'Face_Amount': [c.face_amount for c in model.contracts],
    'Premium': [c.premium for c in model.contracts],
    'Issue_Age': [c.issue_age for c in model.contracts]
})
product_mix.to_excel(writer, sheet_name='Product_Mix')

# Monthly cash flows by variant
for contract in model.contracts:
    if contract.product_type == ProductType.WHOLE_LIFE:
        contract_df = df[df['Policy_Number'] == contract.policy_number]
        sheet_name = f'Monthly_{contract.product_variant.value}'
        contract_df.to_excel(writer, sheet_name=sheet_name)

# Annual summaries by variant
annual_df = df.resample('Y').sum()
for contract in model.contracts:
    if contract.product_type == ProductType.WHOLE_LIFE:
        contract_df = annual_df[annual_df['Policy_Number'] == contract.policy_number]
        sheet_name = f'Annual_{contract.product_variant.value}'
        contract_df.to_excel(writer, sheet_name=sheet_name)

# Present values by variant
pv_df = pd.DataFrame({
    'Product_Variant': [c.product_variant.value for c in model.contracts if c.product_type == ProductType.WHOLE_LIFE],
    'Policy_Number': [c.policy_number for c in model.contracts if c.product_type == ProductType.WHOLE_LIFE],
    'PV_Premium': [c.get_premium_pv() for c in model.contracts if c.product_type == ProductType.WHOLE_LIFE],
    'PV_Death_Benefit': [projection.calculate_present_values(
        discount_rates={d: 0.035 for d in df.index}
    )['Death_Benefit'] for c in model.contracts if c.product_type == ProductType.WHOLE_LIFE],
    'PV_Surrender': [projection.calculate_present_values(
        discount_rates={d: 0.035 for d in df.index}
    )['Surrender'] for c in model.contracts if c.product_type == ProductType.WHOLE_LIFE]
})
pv_df.to_excel(writer, sheet_name='Present_Values')

writer.close()
