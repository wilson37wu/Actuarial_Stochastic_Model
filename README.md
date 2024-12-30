# Stochastic Actuarial Model for Insurance Contract Liability

## Project Overview
Implementation of a stochastic model for insurance contract liability evaluation with integrated asset-liability modeling capabilities. The model features advanced economic scenario generation, dynamic cash flow modeling, and comprehensive risk metrics calculation.

## Latest Features (December 2024)

### Economic Scenario Generation
- Hull-White interest rate model for short and long rates
- Merton jump-diffusion model for equity returns
- Jarrow-Turnbull model for credit risk
- Heston stochastic volatility model
- Correlated inflation scenarios

### Cash Flow Modeling
- Dynamic policy behavior modeling
- Mortality and lapse assumptions
- Premium and benefit calculations
- Surrender value determination
- Expense modeling

### Risk Metrics
- Value at Risk (VaR) calculations
- Conditional Tail Expectation (CTE)
- NPV distribution analysis
- Sensitivity testing capabilities
- Stress scenario analysis

## Technical Requirements

### Software Requirements
- Python 3.9+
- NumPy for numerical computations
- Pandas for data manipulation
- SciPy for statistical functions
- Streamlit for dashboard interface
- PyTest for testing

### Hardware Requirements
- Multi-core processor recommended
- Minimum 16GB RAM
- SSD storage recommended for large datasets

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Actuarial_Stochastic_Model.git
cd Actuarial_Stochastic_Model
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Model

### Dashboard Interface
Launch the interactive dashboard:
```bash
streamlit run src/dashboard/dashboard.py
```

### Command Line Interface
Run scenario analysis from command line:
```bash
python run_model.py --scenarios 1000 --years 30
```

## Model Components

### Economic Scenario Generator (ESG)
- Interest rate modeling (Hull-White)
- Equity returns (Merton jump-diffusion)
- Credit spreads (Jarrow-Turnbull)
- Inflation scenarios
- Asset correlations

### Asset-Liability Model
1. Asset Components:
   - Fixed income portfolio
   - Equity investments
   - Cash and equivalents
   - Alternative investments

2. Liability Components:
   - Policy cash flows
   - Benefit payments
   - Premium income
   - Expenses
   - Surrenders

3. Integration Features:
   - Dynamic asset allocation
   - Cash flow matching
   - Duration management
   - Rebalancing strategies

### Risk Analytics
- VaR and CTE calculations
- Sensitivity analysis
- Stress testing
- Key rate durations
- Portfolio analytics

## Testing Framework

### Unit Tests
- Scenario generation validation
- Cash flow calculation testing
- Risk metric verification
- Model consistency checks

### Integration Tests
- End-to-end model validation
- Scenario consistency
- Portfolio rebalancing
- Risk metric aggregation

## Dashboard Features

### Input Parameters
1. Economic Scenarios:
   - Interest rate parameters
   - Equity market settings
   - Credit spread configurations
   - Inflation assumptions

2. Policy Parameters:
   - Mortality assumptions
   - Lapse rates
   - Expense factors
   - Investment strategy

### Visualizations
1. Scenario Analysis:
   - Interest rate paths
   - Equity returns
   - Credit spread evolution
   - Inflation trajectories

2. Cash Flow Analysis:
   - Premium patterns
   - Benefit payments
   - Net cash flows
   - Present value distributions

3. Risk Metrics:
   - VaR analysis
   - CTE calculations
   - Sensitivity measures
   - Stress test results

## Documentation

### Model Documentation
Detailed documentation is available in the `docs` folder:
- Model methodology
- Implementation details
- Validation procedures
- User guides

### API Documentation
API documentation is available for all major components:
- ESG interfaces
- Model classes
- Utility functions
- Risk calculators

## Contributing
Contributions are welcome! Please read our contributing guidelines and code of conduct before submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Financial modeling community
- Open-source contributors
- Academic research partners

## Contact
For questions and support, please open an issue in the GitHub repository.
