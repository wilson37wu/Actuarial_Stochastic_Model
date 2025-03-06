"""
Quickstart example demonstrating common use cases of the Actuarial Stochastic Model.
This script shows:
1. Basic model setup
2. Product creation
3. Cashflow projection
4. Result analysis
"""
from datetime import date
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from src.config.model_config import ModelConfig
from src.models.products import TermProduct, WholeLifeProduct
from src.models.liabilities import LiabilityModel
from src.utils.enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, PremiumMode
)

def setup_model():
    """Set up the basic model configuration."""
    config = ModelConfig("config/default_config.json")
    model = LiabilityModel(config=config)
    return model, config

def create_sample_products(config):
    """Create sample insurance products."""
    # Common parameters
    common_params = {
        'issue_date': date(2024, 1, 1),
        'issue_age': 35,
        'sex': Sex.MALE,
        'smoking_status': SmokingStatus.NON_SMOKER,
        'occupation_class': OccupationClass.PROFESSIONAL,
        'underwriting_class': UnderwritingClass.STANDARD,
        'premium_mode': PremiumMode.ANNUAL
    }
    
    # Create products
    products = [
        TermProduct(
            policy_number="T001",
            face_amount=100000,
            term_length=20,
            modal_premium=1000,
            config=config,
            **common_params
        ),
        WholeLifeProduct(
            policy_number="WL001",
            face_amount=200000,
            modal_premium=2000,
            config=config,
            **common_params
        )
    ]
    
    return products

def analyze_results(projection, products):
    """Analyze and visualize projection results."""
    # Create output directory if it doesn't exist
    output_dir = Path('outputs/reports')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Basic cashflow plot
    plt.figure(figsize=(12, 6))
    plt.plot(
        projection.index,
        projection['premium_income'],
        label='Premium Income'
    )
    plt.plot(
        projection.index,
        projection['benefit_outgo'],
        label='Benefit Outgo'
    )
    plt.title('Projected Cashflows')
    plt.xlabel('Projection Year')
    plt.ylabel('Amount')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / 'quickstart_cashflows.png')
    plt.close()
    
    # 2. Export to Excel
    writer = pd.ExcelWriter(
        output_dir / 'quickstart_results.xlsx',
        engine='openpyxl'
    )
    
    # Summary by product
    summary = projection.groupby('policy_number').agg({
        'premium_income': 'sum',
        'benefit_outgo': 'sum',
        'net_cashflow': 'sum'
    })
    summary.to_excel(writer, sheet_name='Summary')
    
    # Detailed projections
    projection.to_excel(writer, sheet_name='Projections')
    
    # Product details
    product_details = pd.DataFrame([
        {
            'policy_number': p.policy_number,
            'product_type': p.product_type.name,
            'face_amount': p.face_amount,
            'annual_premium': p.get_annual_premium()
        }
        for p in products
    ])
    product_details.to_excel(writer, sheet_name='Products')
    
    writer.save()
    print(f"Results exported to {output_dir}")

def main():
    """Main execution function."""
    # 1. Setup model
    model, config = setup_model()
    print("Model setup complete")
    
    # 2. Create products
    products = create_sample_products(config)
    for product in products:
        model.add_contract(product)
    print(f"Added {len(products)} products to model")
    
    # 3. Project cashflows
    valuation_date = date(2024, 1, 1)
    projection = model.project_cashflows(
        valuation_date=valuation_date,
        projection_years=50,
        time_step='M'  # Monthly timesteps
    )
    print("Cashflow projection complete")
    
    # 4. Analyze results
    analyze_results(projection, products)
    print("Analysis complete")

if __name__ == "__main__":
    main()
