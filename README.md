# Stochastic Actuarial Model for Insurance Contract Liability

## Project Overview
Implementation of a stochastic model for insurance contract liability evaluation with integrated asset-liability modeling capabilities.

## Project Timeline and Milestones

### Phase 1: Setup and Requirements (2 weeks)
- Define detailed technical specifications
- Set up development environment
- Design system architecture
- Document data requirements

### Phase 2: Asset Model Development (6 weeks)
- Develop asset cash flow projection models
- Implement asset allocation strategy
- Create reinvestment logic
- Build credit risk modeling component
- Unit testing and validation

### Phase 3: Asset-Liability Integration (4 weeks)
- Integrate existing liability cash flow model
- Develop dynamic asset-liability matching logic
- Implement rebalancing strategies
- Create reporting framework

### Phase 4: Stochastic Engine (4 weeks)
- Implement scenario generator interface
- Develop parallel processing capabilities
- Create risk metric calculations
- Implement validation checks

### Phase 5: Testing and Validation (4 weeks)
- Comprehensive testing
- Model validation
- Documentation
- User acceptance testing

## Technical Requirements

### Software Requirements
- Python 3.9+
- NumPy for numerical computations
- Pandas for data manipulation
- SciPy for statistical functions
- Dask for parallel processing
- PyTest for testing
- Git for version control

### Hardware Requirements
- Multi-core processor for parallel scenario processing
- Minimum 32GB RAM recommended
- SSD storage for large dataset handling

## Key Model Components

### Asset Modeling
1. Fixed Income
   - Bond cash flow projection
   - Credit risk modeling
   - Reinvestment strategy
   - Duration matching

2. Equity
   - Dividend modeling
   - Capital gains/losses
   - Rebalancing rules

3. Other Assets
   - Real estate
   - Alternative investments
   - Cash and equivalents

### Integration Components
1. Dynamic Asset-Liability Management
   - Cash flow matching
   - Duration/convexity matching
   - Rebalancing triggers

2. Risk Metrics
   - Value at Risk (VaR)
   - Conditional Tail Expectation (CTE)
   - Duration/convexity measures
   - Key rate durations

## Modeling Considerations

### Actuarial Aspects
1. Liability Model Integration
   - Mortality assumptions
   - Lapse assumptions
   - Expense assumptions
   - Option/guarantee valuation

2. Economic Scenario Integration
   - Interest rate scenarios
   - Credit spread scenarios
   - Equity return scenarios
   - Correlation modeling

### Risk Management
1. Risk Metrics Calculation
   - Capital requirements
   - Solvency measures
   - Sensitivity analysis

2. Model Governance
   - Documentation requirements
   - Validation procedures
   - Audit trail
   - Change control

## Recent Updates

### December 2024 Updates
- Enhanced liability projection capabilities with adjustable parameters:
  - Mortality multiplier for sensitivity testing
  - Base lapse rate adjustments
  - Inflation rate scenarios
- Improved investment portfolio management:
  - Added bond portfolio tracking in FixedIncomeModel
  - Enhanced equity allocation strategies
  - Integrated dynamic asset allocation updates
- Enhanced dashboard visualization:
  - Split liability projections into net and present value views
  - Added detailed cash flow component analysis
  - Improved portfolio composition display

## Features

### Dashboard Components
1. **Liability Analysis**
   - Interactive mortality, lapse, and inflation adjustments
   - Net liability and present value projections
   - Detailed cash flow component breakdown
   
2. **Investment Analysis**
   - Fixed income portfolio management
   - Equity allocation strategies
   - Dynamic portfolio rebalancing
   
3. **Asset-Liability Management**
   - Integrated asset-liability projections
   - Dynamic hedging strategies
   - Risk metric calculations

### Model Components
1. **Fixed Income Model**
   - Bond portfolio management
   - Credit transition modeling
   - Default recovery calculations
   
2. **Equity Model**
   - Return projections
   - Dividend modeling
   - Volatility adjustments

3. **Liability Model**
   - Mortality assumptions
   - Lapse behavior
   - Inflation impacts

## Data Specifications

### Economic Scenarios

Economic scenarios should be provided as a pandas DataFrame with the following structure:

```python
scenarios_df = pd.DataFrame({
    'equity_return': float[],      # Monthly/Annual equity market returns (e.g., 0.08 for 8%)
    'risk_free_rate': float[],     # Risk-free rates (e.g., 0.03 for 3%)
}, index=pd.DatetimeIndex)         # DatetimeIndex with projection dates
```

### Fixed Income Specifications

#### Bond Data Structure
Each bond should be instantiated as a `Bond` class with the following attributes:

```python
Bond(
    id: str,                    # Unique identifier for the bond
    par_value: float,           # Face value of the bond
    coupon_rate: float,         # Annual coupon rate (e.g., 0.035 for 3.5%)
    maturity_date: date,        # Maturity date
    payment_frequency: int,      # Number of payments per year (e.g., 2 for semi-annual)
    credit_rating: str,         # Credit rating (e.g., 'AAA', 'AA', etc.)
    issue_date: date,           # Date of issuance
    purchase_price: float,      # Price at which the bond was purchased
    currency: str = 'USD'       # Currency of the bond (default: 'USD')
)
```

#### Fixed Income Model Configuration
The fixed income model requires configuration for credit spreads:

```python
fixed_income_config = {
    'credit_spread': {
        'AAA': float,           # Credit spread for AAA-rated bonds
        'AA': float,           # Credit spread for AA-rated bonds
        'A': float,            # Credit spread for A-rated bonds
        # ... other ratings
    }
}
```

### Public Equity Specifications

#### Equity Position Data Structure
Each equity position should be instantiated as an `Equity` class with the following attributes:

```python
Equity(
    id: str,                    # Unique identifier for the equity
    quantity: float,            # Number of shares
    initial_price: float,       # Price per share at start of projection
    dividend_yield: float,      # Annual dividend yield (e.g., 0.02 for 2%)
    beta: float,               # Market beta of the equity
    sector: str,               # Industry sector
    purchase_date: date,        # Date of purchase
    currency: str = 'USD'       # Currency (default: 'USD')
)
```

#### Equity Model Configuration
The equity model requires configuration for market parameters:

```python
equity_config = {
    'market_volatility': float,     # Overall market volatility (e.g., 0.15 for 15%)
    'sector_correlations': {        # Correlation matrix between sectors
        'Technology': {
            'Technology': 1.0,
            'Financial': float,
            'Healthcare': float,
            # ... other sectors
        },
        # ... other sectors
    }
}
```

### Liability Specifications

#### Insurance Contract Data Structure
Each insurance contract should be instantiated as an `InsuranceContract` class with the following attributes:

```python
InsuranceContract(
    id: str,                    # Unique identifier for the contract
    issue_date: date,           # Contract issue date
    maturity_date: date,        # Contract maturity date
    premium_pattern: Dict[date, float],  # Premium cash flows {date: amount}
    benefit_pattern: Dict[date, float],  # Benefit cash flows {date: amount}
    expense_pattern: Dict[date, float],  # Expense cash flows {date: amount}
    currency: str = 'USD'       # Currency of the contract (default: 'USD')
)
```

#### Liability Cash Flow Output
The liability model produces a DataFrame with the following structure:

```python
liability_cf = pd.DataFrame({
    'date': date,              # Projection date
    'contract_id': str,        # Contract identifier
    'premium': float,          # Premium cash flow
    'benefit': float,          # Benefit cash flow
    'expense': float,          # Expense cash flow
    'net_cashflow': float      # Net cash flow (premium - benefit - expense)
})
```

### Portfolio Projection Parameters

When projecting the entire portfolio, the following parameters can be specified:

```python
project_portfolio(
    bonds: List[Bond],              # List of bond positions
    equities: List[Equity],         # List of equity positions
    valuation_date: date,           # Starting date for projections
    scenario_idx: int,              # Index of scenario to use
    projection_years: int = 100,    # Number of years to project (default: 100)
    frequency: str = 'monthly',     # 'monthly' or 'annual'
    output_path: Optional[str]      # Path for Excel output (optional)
)
```

### Output Specifications

The model produces three main types of output DataFrames:

#### 1. Fixed Income Cash Flows
```python
fixed_income_cf = pd.DataFrame({
    'date': date,                   # Payment date
    'instrument_id': str,           # Bond identifier
    'coupon_payment': float,        # Coupon payment amount
    'principal_payment': float,     # Principal payment amount
    'total_cashflow': float,        # Total payment
    'market_value': float,          # Current market value
    'total_return': float           # Total return for the period
})
```

#### 2. Equity Cash Flows
```python
equity_cf = pd.DataFrame({
    'date': date,                   # Projection date
    'instrument_id': str,           # Equity identifier
    'market_value': float,          # Current market value
    'dividend_amount': float,       # Dividend payment
    'total_return': float           # Total return including price appreciation
})
```

#### 3. Portfolio Summary
```python
portfolio_cf = pd.DataFrame({
    'date': date,                   # Projection date
    'asset_type': str,              # 'fixed_income', 'equity', or 'total_portfolio'
    'market_value': float,          # Total market value
    'dividend_amount': float,       # Total dividend payments
    'total_return': float           # Portfolio-level return
})
```

## Excel Output Format

When exporting to Excel, the results are organized in three sheets:

1. **Fixed Income CF**: Detailed bond cash flows
2. **Equity CF**: Detailed equity projections
3. **Portfolio Summary**: Combined portfolio metrics

Each sheet follows the structure of its corresponding DataFrame as specified above.

## Dependencies
```txt
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
dask>=2021.6.0
pytest>=6.2.0
matplotlib>=3.4.0
seaborn>=0.11.0
