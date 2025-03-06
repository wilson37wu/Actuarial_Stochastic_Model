# Actuarial Stochastic Model

A comprehensive actuarial modeling framework for stochastic analysis of insurance products and portfolios.

## Project Structure

```
actuarial_stochastic_model/
├── src/                    # Source code
│   ├── config/            # Configuration management
│   │   ├── base_config.py # Base configuration class
│   │   └── model_config.py# Model-specific configuration
│   ├── models/            # Model implementations
│   │   ├── assets/       # Asset models (equity, fixed income)
│   │   ├── liabilities/  # Liability calculations
│   │   └── products/     # Insurance product models
│   └── utils/            # Utility functions
├── data/                  # Data files
│   ├── scenarios/        # Economic scenarios
│   └── assumptions/      # Model assumptions
├── outputs/              # Generated outputs
│   ├── results/         # Analysis results
│   └── reports/         # Generated reports
├── examples/             # Example scripts
├── tests/               # Test suite
└── docs/                # Documentation
```

## Features

### Asset Models
- Public equity with sector analysis
- Fixed income with duration matching
- Asset allocation optimization

### Liability Models
- Mortality projections
- Dynamic lapse modeling
- Expense analysis

### Product Models
- Term life insurance
- Whole life insurance
- Participating products
  - Bonus-based
  - Cash dividend

### Configuration System
- Centralized parameter management
- Validation rules
- Type checking
- Easy parameter updates

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wilson37wu/actuarial_stochastic_model.git
cd actuarial_stochastic_model
```

2. Create a virtual environment (Python 3.11 recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Configure your model parameters in `config/default_config.json`

2. Run example analysis:
```python
from src.models import EquityModel, ParticipatingBonusProduct
from src.config.model_config import ModelConfig

# Load configuration
config = ModelConfig("config/default_config.json")

# Create models
equity_model = EquityModel(config)
product = ParticipatingBonusProduct(config)

# Run analysis
results = product.project_cashflows(equity_model)
```

## Documentation

Detailed documentation is available in the `docs/` directory:
- Model specifications
- API reference
- Example workflows

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
