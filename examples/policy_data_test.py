"""Example script demonstrating policy data generation and cash flow projections.

This script shows how to:
1. Generate a realistic mix of insurance policies
2. Set up a liability model with various assumptions
3. Project cash flows for the generated policy portfolio
4. Export results and assumptions to Excel for analysis
"""

from datetime import date
from pathlib import Path

import pandas as pd

from actuarial_stochastic_model import (
    PolicyDataGenerator,
    LiabilityModel,
    MortalityTable,
    LapseAssumption,
    InflationAssumption,
    ProductType,
    TermPolicy,
    WholeLifePolicy,
    ParticipatingPolicy
)

def main():
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize policy data generator
    print("Initializing policy data generator...")
    generator = PolicyDataGenerator(
        start_date=date(2020, 1, 1),
        end_date=date(2024, 12, 31),
        seed=42  # For reproducibility
    )
    
    try:
        # Generate a mix of 1000 policies
        print("Generating policy data...")
        policies = generator.generate_policy_mix(
            num_policies=1000,
            term_ratio=0.4,        # 40% term insurance
            whole_life_ratio=0.3,  # 30% whole life
            participating_ratio=0.3 # 30% participating whole life
        )
        
        # Generate summary statistics
        print("\nGenerating portfolio summary...")
        summary = pd.DataFrame({
            'Product Type': ['Term', 'Whole Life', 'Participating'],
            'Count': [
                len([p for p in policies if isinstance(p, TermPolicy)]),
                len([p for p in policies if isinstance(p, WholeLifePolicy) and not isinstance(p, ParticipatingPolicy)]),
                len([p for p in policies if isinstance(p, ParticipatingPolicy)])
            ]
        })
        
        # Calculate total sum assured and premium by product type
        for product_type, policy_class in [
            ('Term', TermPolicy),
            ('Whole Life', WholeLifePolicy),
            ('Participating', ParticipatingPolicy)
        ]:
            type_policies = [p for p in policies if isinstance(p, policy_class)]
            if product_type == 'Whole Life':
                type_policies = [p for p in type_policies if not isinstance(p, ParticipatingPolicy)]
                
            summary.loc[summary['Product Type'] == product_type, 'Total Sum Assured'] = \
                sum(p.sum_assured for p in type_policies)
            summary.loc[summary['Product Type'] == product_type, 'Total Annual Premium'] = \
                sum(p.premium for p in type_policies)
        
        # Format currency columns
        for col in ['Total Sum Assured', 'Total Annual Premium']:
            summary[col] = summary[col].map('${:,.2f}'.format)
        
        # Save summary statistics
        summary.to_excel(str(output_dir / "portfolio_summary.xlsx"), index=False)
        
        print("\nPortfolio Summary:")
        print(summary.to_string(index=False))
        print("\nSample policies generated successfully!")
        print(f"Results saved to: {output_dir}")
        print("Files generated:")
        print("1. portfolio_summary.xlsx - Summary statistics of generated portfolio")
        
        # Print sample policies
        print("\nSample policies from each type:")
        for policy_type, policy_list in [
            ("Term", [p for p in policies if isinstance(p, TermPolicy)]),
            ("Whole Life", [p for p in policies if isinstance(p, WholeLifePolicy) and not isinstance(p, ParticipatingPolicy)]),
            ("Participating", [p for p in policies if isinstance(p, ParticipatingPolicy)])
        ]:
            if policy_list:
                sample = policy_list[0]
                print(f"\n{policy_type} Insurance Sample:")
                print(f"  Policy Number: {sample.policy_number}")
                print(f"  Issue Date: {sample.issue_date}")
                print(f"  Sum Assured: ${sample.sum_assured:,.2f}")
                print(f"  Annual Premium: ${sample.premium:,.2f}")
                if isinstance(sample, TermPolicy):
                    print(f"  Term Years: {sample.term_years}")
                if isinstance(sample, ParticipatingPolicy):
                    print(f"  Bonus Rate: {sample.bonus_rate:.2%}")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == "__main__":
    main()
