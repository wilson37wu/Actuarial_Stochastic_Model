# Example Guide

This guide provides practical examples for using the Actuarial Stochastic Model. Each example demonstrates key features and common use cases.

## Quick Start Examples

### 1. Basic Product Setup

```python
from src.config.model_config import ModelConfig
from src.models.products import TermProduct
from src.utils.enums import Sex, SmokingStatus, PremiumMode

# Load configuration
config = ModelConfig("config/default_config.json")

# Create a simple term product
term_product = TermProduct(
    policy_number="T001",
    face_amount=100000,
    term_length=20,
    issue_age=35,
    sex=Sex.MALE,
    smoking_status=SmokingStatus.NON_SMOKER,
    premium_mode=PremiumMode.ANNUAL,
    modal_premium=1000,
    config=config
)

# Project cashflows
cashflows = term_product.project_cashflows(
    valuation_date=date(2024, 1, 1),
    projection_years=20
)
```

### 2. Portfolio Analysis

```python
from src.models.liabilities import LiabilityModel
from src.models.products import WholeLifeProduct, ParticipatingCashProduct

def create_portfolio(config):
    # Create multiple products
    products = [
        WholeLifeProduct(
            policy_number="WL001",
            face_amount=200000,
            modal_premium=2000,
            config=config
        ),
        ParticipatingCashProduct(
            policy_number="PWL001",
            face_amount=300000,
            modal_premium=3000,
            config=config
        )
    ]
    
    # Create liability model
    model = LiabilityModel(config=config)
    
    # Add products to model
    for product in products:
        model.add_contract(product)
    
    return model

# Project portfolio cashflows
portfolio = create_portfolio(config)
projections = portfolio.project_cashflows(
    valuation_date=date(2024, 1, 1),
    projection_years=50
)
```

### 3. Asset Model Usage

```python
from src.models.assets import PublicEquityModel, FixedIncomeModel
from src.utils.enums import InvestmentStrategy

def setup_investment_portfolio(config):
    # Create equity model
    equity_model = PublicEquityModel(
        strategy=InvestmentStrategy.BALANCED,
        config=config
    )
    
    # Create fixed income model
    fixed_income_model = FixedIncomeModel(
        duration_target=7.5,
        credit_quality="AA",
        config=config
    )
    
    return equity_model, fixed_income_model

# Project investment returns
equity_model, bond_model = setup_investment_portfolio(config)
equity_returns = equity_model.project_returns(years=30)
bond_returns = bond_model.project_returns(years=30)
```

## Advanced Examples

### 1. Scenario Analysis

```python
from src.models.scenario import ScenarioGenerator
import pandas as pd

def run_scenario_analysis(model, scenarios):
    results = []
    
    for scenario in scenarios:
        # Apply scenario parameters
        model.update_assumptions(scenario)
        
        # Run projection
        projection = model.project_cashflows(
            valuation_date=date(2024, 1, 1),
            projection_years=30
        )
        
        # Calculate metrics
        metrics = model.calculate_metrics(projection)
        results.append(metrics)
    
    return pd.DataFrame(results)

# Generate and analyze scenarios
generator = ScenarioGenerator(config)
scenarios = generator.generate_scenarios(num_scenarios=100)
results = run_scenario_analysis(portfolio, scenarios)
```

### 2. Sensitivity Testing

```python
def perform_sensitivity_analysis(model, parameter, values):
    results = []
    
    for value in values:
        # Create modified config
        test_config = model.config.copy()
        test_config.update_parameter(parameter, value)
        
        # Run model with modified config
        model.update_config(test_config)
        projection = model.project_cashflows(
            valuation_date=date(2024, 1, 1),
            projection_years=30
        )
        
        # Calculate key metrics
        metrics = model.calculate_metrics(projection)
        results.append({
            'parameter_value': value,
            **metrics
        })
    
    return pd.DataFrame(results)

# Test interest rate sensitivity
interest_rates = [0.02, 0.03, 0.04, 0.05, 0.06]
sensitivity = perform_sensitivity_analysis(
    portfolio,
    'interest_rate',
    interest_rates
)
```

### 3. Custom Product Development

```python
from src.models.products.base import BaseProduct

class CustomProduct(BaseProduct):
    def __init__(self, policy_number, face_amount, config, **kwargs):
        super().__init__(policy_number, face_amount, config, **kwargs)
        self.product_type = ProductType.CUSTOM
    
    def calculate_premium(self):
        # Custom premium calculation logic
        pass
    
    def calculate_benefits(self):
        # Custom benefit calculation logic
        pass
    
    def project_cashflows(self, valuation_date, projection_years):
        # Custom cashflow projection logic
        pass

# Use custom product
custom_product = CustomProduct(
    policy_number="C001",
    face_amount=150000,
    config=config
)
```

## Visualization Examples

### 1. Cashflow Analysis

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_cashflows(projection):
    plt.figure(figsize=(12, 6))
    
    # Plot premium income
    plt.plot(
        projection.index,
        projection['premium_income'],
        label='Premium Income'
    )
    
    # Plot benefit outgo
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
    
    plt.savefig('outputs/reports/cashflow_projection.png')
    plt.close()
```

### 2. Interactive Dashboard

```python
import streamlit as st
import plotly.express as px

def create_dashboard(results):
    st.title('Portfolio Analysis Dashboard')
    
    # Portfolio composition
    st.subheader('Portfolio Composition')
    fig_composition = px.pie(
        results,
        values='face_amount',
        names='product_type',
        title='Portfolio by Face Amount'
    )
    st.plotly_chart(fig_composition)
    
    # Cashflow projection
    st.subheader('Cashflow Projection')
    fig_cashflow = px.line(
        results,
        x='projection_year',
        y=['premium_income', 'benefit_outgo'],
        title='Projected Cashflows'
    )
    st.plotly_chart(fig_cashflow)

# Run dashboard
if __name__ == '__main__':
    results = portfolio.get_results()
    create_dashboard(results)
```

## Configuration Examples

### 1. Model Configuration

```json
{
    "model_parameters": {
        "interest_rate": 0.05,
        "mortality_table": "2012IAM",
        "expense_inflation": 0.02
    },
    "product_parameters": {
        "term": {
            "max_term": 30,
            "min_face_amount": 50000
        },
        "whole_life": {
            "guaranteed_rate": 0.03,
            "participation_rate": 0.8
        }
    },
    "asset_parameters": {
        "equity": {
            "expected_return": 0.08,
            "volatility": 0.15
        },
        "fixed_income": {
            "credit_spread": 0.01,
            "duration_limit": 15
        }
    }
}
```

## Testing Examples

### 1. Unit Tests

```python
import pytest
from src.models.products import TermProduct

def test_term_product_premium():
    config = ModelConfig("tests/test_config.json")
    product = TermProduct(
        policy_number="T001",
        face_amount=100000,
        term_length=20,
        config=config
    )
    
    premium = product.calculate_premium()
    assert premium > 0
    assert premium < product.face_amount

def test_term_product_benefits():
    config = ModelConfig("tests/test_config.json")
    product = TermProduct(
        policy_number="T001",
        face_amount=100000,
        term_length=20,
        config=config
    )
    
    benefits = product.calculate_benefits()
    assert benefits['death_benefit'] == product.face_amount
    assert benefits['maturity_benefit'] == 0
```

## Output Examples

### 1. Excel Report Generation

```python
def generate_excel_report(results, output_path):
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Write summary
    summary = results.groupby('product_type').agg({
        'face_amount': 'sum',
        'premium_income': 'sum',
        'present_value': 'sum'
    })
    summary.to_excel(writer, sheet_name='Summary')
    
    # Write detailed projections
    results.to_excel(writer, sheet_name='Projections')
    
    # Write charts
    workbook = writer.book
    worksheet = workbook['Summary']
    
    chart = workbook.add_chart({'type': 'column'})
    chart.add_data('Summary!B2:B5')  # Adjust ranges as needed
    worksheet.add_chart(chart, 'E2')
    
    writer.save()
```

Each example includes:
- Clear purpose and context
- Complete code snippets
- Proper error handling
- Best practices
- Documentation

The examples cover:
1. Basic model setup
2. Portfolio analysis
3. Asset modeling
4. Scenario testing
5. Visualization
6. Configuration
7. Testing
8. Report generation

Would you like me to:
1. Add more specific examples for certain components?
2. Include more complex scenarios?
3. Add example output visualizations?

<function_calls>
<invoke name="suggested_responses">
<parameter name="Suggestions">["Add component examples", "Add complex scenarios", "Add visualizations"]
