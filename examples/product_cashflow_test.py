"""
Test script to generate cash flow projections for different insurance products.

This example demonstrates how to:
1. Configure and initialize different insurance products
2. Set up actuarial assumptions
3. Project cash flows and analyze results
"""
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np

from src.config.model_config import ModelConfig
from src.models.liabilities import LiabilityModel
from src.models.products import (
    TermProduct, WholeLifeProduct,
    ParticipatingCashProduct, ParticipatingBonusProduct
)
from src.models.products.base import BaseProduct
from src.utils.enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy, PremiumMode
)

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

def create_test_products(config: ModelConfig, valuation_date: date) -> List[BaseProduct]:
    """Create test instances of each product type.
    
    Args:
        config: Model configuration containing product parameters
        valuation_date: Valuation date for the products
        
    Returns:
        List of product instances
    """
    # Common parameters
    common_params = {
        'issue_date': valuation_date,
        'issue_age': 35,
        'sex': Sex.MALE,
        'smoking_status': SmokingStatus.NON_SMOKER,
        'occupation_class': OccupationClass.PROFESSIONAL,
        'underwriting_class': UnderwritingClass.STANDARD,
        'premium_mode': PremiumMode.ANNUAL
    }
    
    # Create products using configuration
    products = []
    
    # Term Insurance
    term = TermProduct(
        policy_number="T001",
        face_amount=100000,
        term_length=20,
        modal_premium=1000,
        config=config,
        **common_params
    )
    products.append(term)
    
    # Whole Life
    whole_life = WholeLifeProduct(
        policy_number="WL001",
        face_amount=200000,
        modal_premium=2000,
        config=config,
        **common_params
    )
    products.append(whole_life)
    
    # Participating Whole Life with Cash Dividends
    par_cash = ParticipatingCashProduct(
        policy_number="PWL001",
        face_amount=300000,
        modal_premium=3000,
        config=config,
        **common_params
    )
    products.append(par_cash)
    
    # Participating Whole Life with Reversionary Bonuses
    par_bonus = ParticipatingBonusProduct(
        policy_number="PWL002",
        face_amount=300000,
        modal_premium=3000,
        config=config,
        **common_params
    )
    products.append(par_bonus)
    
    return products

def main():
    """Main execution function."""
    # Load configuration
    config = ModelConfig("config/default_config.json")
    
    # Create valuation date and investment returns
    valuation_date = date(2024, 1, 1)
    investment_returns = generate_investment_returns(
        valuation_date, 
        years=100
    )
    
    # Create test products
    products = create_test_products(config, valuation_date)
    
    # Create liability model
    model = LiabilityModel(config=config)
    
    # Add contracts to model
    for product in products:
        model.add_contract(product)
    
    # Project cash flows
    projection = model.project_cashflows(
        valuation_date=valuation_date,
        projection_years=100,
        time_step='M'
    )
    
    # Calculate present values
    present_values = model.calculate_present_values()
    
    # Export results
    export_results(projection, present_values, products)

def export_results(projection: pd.DataFrame, present_values: Dict, products: List[BaseProduct]):
    """Export results to Excel files.
    
    Args:
        projection: Projected cash flows
        present_values: Present values by product
        products: List of product instances
    """
    output_path = Path('outputs/reports/product_cashflow_projection.xlsx')
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Monthly cash flows by product
    df = projection.reset_index()
    df['Time_Point'] = pd.to_datetime(df['Time_Point'])
    
    # Split by product type
    for product in products:
        product_df = df[df['Policy_Number'] == product.policy_number]
        sheet_name = f'Monthly_{product.product_type.name}'
        product_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Annual summaries
    annual_df = df.set_index('Time_Point').resample('Y').sum()
    annual_df.to_excel(writer, sheet_name='Annual_Summary')
    
    # Present values
    pd.Series(present_values).to_excel(writer, sheet_name='Present_Values')
    
    # Product mix analysis
    product_mix = pd.DataFrame({
        'Product': [p.product_type.name for p in products],
        'Face_Amount': [p.face_amount for p in products],
        'Premium': [p.get_annual_premium() for p in products],
        'Issue_Age': [p.issue_age for p in products]
    })
    product_mix.to_excel(writer, sheet_name='Product_Mix', index=False)
    
    writer.save()
    print(f"Results exported to {output_path}")

if __name__ == "__main__":
    main()