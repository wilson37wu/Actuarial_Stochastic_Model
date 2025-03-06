# Project Structure and Organization

This document outlines the organization and structure of the Actuarial Stochastic Model project.

## Directory Structure

```
actuarial_stochastic_model/
├── src/                    # Source code
│   ├── config/            # Configuration management
│   │   ├── base_config.py # Base configuration class
│   │   └── model_config.py# Model-specific configuration
│   ├── models/            # Core model implementations
│   │   ├── assets/       # Asset models
│   │   │   ├── public_equity.py
│   │   │   └── fixed_income.py
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

## Component Organization

### 1. Configuration System (`src/config/`)
- **base_config.py**: Abstract base configuration with validation
- **model_config.py**: Concrete configuration implementation
- Configuration files stored in `config/`
  - Default configuration in `default_config.json`
  - Environment-specific overrides

### 2. Model Components (`src/models/`)

#### Asset Models (`models/assets/`)
- Public equity implementation
- Fixed income modeling
- Asset allocation utilities
- Market data integration

#### Liability Models (`models/liabilities/`)
- Core liability calculations
- Mortality projections
- Lapse modeling
- Expense analysis

#### Product Models (`models/products/`)
- Base product class
- Term life implementation
- Whole life products
- Participating products
  - Cash dividend version
  - Bonus version

### 3. Data Management (`data/`)

#### Scenarios (`data/scenarios/`)
- Economic scenario files
- Market data inputs
- Stress test scenarios

#### Assumptions (`data/assumptions/`)
- Mortality tables
- Lapse assumptions
- Expense factors
- Investment parameters

### 4. Output Organization (`outputs/`)

#### Results (`outputs/results/`)
- Analysis outputs
- Model run results
- Optimization results

#### Reports (`outputs/reports/`)
- Generated Excel reports
- Analysis summaries
- Portfolio projections

## Best Practices

### 1. Code Organization
- Keep related functionality together
- Use clear, descriptive module names
- Maintain consistent file naming conventions
- Follow Python package structure

### 2. Configuration Management
- Use centralized configuration
- Validate all parameters
- Document configuration options
- Support environment-specific settings

### 3. Data Handling
- Separate input data from code
- Use standardized data formats
- Implement data validation
- Maintain data versioning

### 4. Output Management
- Use consistent output locations
- Implement clear naming conventions
- Separate results from reports
- Clean up temporary files

## Development Workflow

1. **Code Changes**
   - Create feature branch
   - Implement changes
   - Update tests
   - Create pull request

2. **Configuration Updates**
   - Update default configuration
   - Document new parameters
   - Validate changes
   - Update examples

3. **Data Management**
   - Store new data in appropriate location
   - Update data documentation
   - Validate data format
   - Clean up old data

4. **Testing**
   - Run unit tests
   - Update test data
   - Verify outputs
   - Clean up test artifacts

## Future Considerations

1. **Scalability**
   - Modular design for easy extension
   - Clear interfaces between components
   - Efficient data handling
   - Resource management

2. **Maintenance**
   - Regular cleanup of outputs
   - Version control best practices
   - Documentation updates
   - Dependency management

3. **Integration**
   - API design for external systems
   - Standard data formats
   - Clear integration points
   - Error handling
