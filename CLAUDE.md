# CLAUDE.md — Actuarial Stochastic Model

This file provides essential context for AI assistants working in this codebase.

---

## Project Overview

A comprehensive actuarial modeling framework for stochastic analysis of insurance products and
portfolios. Core capabilities include:

- **Insurance product modeling** — Term, Whole Life, and Participating (bonus/cash dividend) products
- **Asset-Liability Management (ALM)** — Integrated stochastic projections of assets and liabilities
- **Economic scenario generation** — Hull-White interest rate model, Merton jump-diffusion equity model
- **HKRBC regulatory compliance** — Hong Kong Risk-Based Capital calculations per Cap 41R
- **Interactive dashboard** — Streamlit-based UI for analysis and reporting
- **Risk analytics** — VaR, CTE, duration, convexity, diversification benefits

**Python 3.11+ required.** Version: `0.1.0`.

---

## Repository Structure

```
Actuarial_Stochastic_Model/
├── src/                               # All source code
│   ├── actuarial_stochastic_model/    # Main installable package
│   │   ├── __init__.py                # Package exports (public API)
│   │   ├── enums.py                   # Canonical enumerations
│   │   └── models/
│   │       ├── data_classes.py        # Policy dataclasses (TermPolicy, WholeLifePolicy, ParticipatingPolicy)
│   │       ├── data_generator.py      # PolicyDataGenerator
│   │       └── liabilities/
│   │           ├── liability_model.py # LiabilityModel — projects cash flows
│   │           ├── mortality.py       # MortalityTable
│   │           ├── lapse.py           # LapseAssumption
│   │           └── inflation.py       # InflationAssumption
│   ├── hkrbc/                         # HKRBC regulatory module
│   │   ├── constants.py               # Cap 41R constants, URLs, enums
│   │   ├── capital_calculator/
│   │   │   ├── base.py                # RiskModule (ABC), RiskChargeResult, RiskAggregator
│   │   │   ├── main_aggregator.py     # MainRiskAggregator (Market + Insurance + Operational)
│   │   │   ├── operational_risk.py    # OperationalRiskModule
│   │   │   ├── market_risk/           # Equity, interest rate, currency, property, credit spread
│   │   │   │   ├── aggregator.py
│   │   │   │   ├── interest_rate.py   # Cap 41R Section 24 stress factors
│   │   │   │   ├── equity.py
│   │   │   │   ├── credit_spread.py
│   │   │   │   ├── currency.py
│   │   │   │   └── property.py
│   │   │   └── insurance_risk/        # Mortality, longevity, lapse
│   │   │       ├── aggregator.py
│   │   │       ├── mortality.py
│   │   │       ├── longevity.py
│   │   │       └── lapse.py
│   │   ├── valuation/
│   │   │   ├── asset_valuer.py
│   │   │   └── liability_valuer.py
│   │   ├── data_provider/
│   │   │   └── ia_downloader.py       # Downloads data from HK Insurance Authority
│   │   └── reporting/
│   │       ├── excel_report.py        # ExcelReportGenerator
│   │       └── pdf_report.py          # PDF report generation
│   ├── config/
│   │   ├── base_config.py             # BaseConfig (loads JSON config)
│   │   └── model_config.py            # ModelConfig with validation logic
│   ├── models/                        # Legacy/extended model implementations
│   │   ├── assets/
│   │   │   ├── asset_model.py         # Base asset model
│   │   │   ├── public_equity.py       # Equity with sector analysis
│   │   │   └── fixed_income.py        # Fixed income with duration matching
│   │   ├── liabilities/               # Additional liability implementations
│   │   ├── products/
│   │   │   ├── base.py                # BaseInsuranceContract (GCV parameters)
│   │   │   ├── data_classes.py        # Product-specific data structures
│   │   │   ├── term_insurance.py
│   │   │   ├── whole_life_insurance.py
│   │   │   ├── participating_bonus.py # Reversionary bonus product
│   │   │   └── participating_cash.py  # Cash dividend product
│   │   └── alm/
│   │       ├── config.py
│   │       ├── strategy.py
│   │       ├── reporting/             # ALM Excel/PDF/visualization reports
│   │       └── utils/calculations.py
│   ├── dashboard/                     # Streamlit dashboard components
│   │   ├── dashboard.py               # ModelDashboard (main class)
│   │   ├── gcv_analysis.py
│   │   ├── portfolio_analysis.py
│   │   ├── scenario_analysis.py
│   │   ├── sensitivity_analysis.py
│   │   ├── data_export.py
│   │   └── visualization.py
│   ├── dashboard_components/          # Reusable dashboard UI components
│   │   ├── cash_flow_analysis.py
│   │   ├── dividend_analysis.py
│   │   ├── financial_analysis.py
│   │   └── gcv_analysis.py
│   ├── gui/                           # Legacy tkinter GUI
│   │   ├── main.py
│   │   ├── tabs.py
│   │   ├── widgets.py
│   │   └── styles.py
│   ├── visualizers/
│   │   └── gcv_visualizer.py
│   ├── alm_engine.py                  # ALMEngine (ProcessPoolExecutor for stochastic runs)
│   ├── economic_scenario_generator.py # EconomicScenarioGenerator
│   ├── actuarial_assumptions.py       # Mortality tables, lapse rates, expenses (~21KB)
│   ├── actuarial_calculations.py      # Core actuarial math utilities
│   ├── gcv_calculator.py              # GCV with 9 grading patterns (~21KB)
│   ├── dividend_tracker.py            # Dividend history and tracking (~15KB)
│   ├── investment.py                  # Investment portfolio management (~28KB)
│   ├── financial_models.py            # Financial modeling utilities
│   ├── cash_flow_model.py             # Dynamic cash flow modeling
│   ├── economic_scenario.py           # Economic scenario definitions
│   ├── narrative_generator.py         # Narrative text generation for reports
│   ├── enums.py                       # Legacy enums (prefer actuarial_stochastic_model/enums.py)
│   ├── dashboard.py                   # Legacy dashboard
│   ├── model_gui.py                   # GUI model wrapper
│   ├── main.py                        # Streamlit entry point
│   └── tests/alm/test_alm.py          # Internal ALM tests (non-standard location)
├── tests/                             # Primary test suite
│   ├── test_dashboard.py
│   ├── test_financial_models.py
│   ├── test_fixed_income.py
│   ├── test_investment.py
│   ├── test_model_performance.py
│   ├── test_small_scenario.py
│   └── hkrbc/
│       ├── test_insurance_risk.py
│       ├── test_market_risk.py
│       └── test_reporting.py
├── config/
│   └── default_config.json            # Default model configuration
├── data/
│   ├── scenarios/                     # Economic scenario data
│   └── assumptions/                   # Actuarial assumption tables
├── docs/
│   ├── ARCHITECTURE.md
│   ├── development_setup.md
│   ├── example_guide.md
│   ├── project_structure.md
│   └── hkrbc/README.md
├── examples/                          # Runnable example scripts
├── output/                            # Generated reports and results
├── .streamlit/config.toml             # Streamlit theme configuration
├── pyproject.toml                     # Build config + pytest settings
├── requirements.txt                   # Runtime + dev dependencies
├── setup.py                           # Package setup
├── run_dashboard.py                   # Dashboard launcher (root level)
├── generate_scenarios.py              # Scenario generation runner
├── model_inputs.json                  # Snapshot of model inputs
└── model_settings.json                # Runtime model settings
```

---

## Setup and Installation

```bash
# Clone and enter repository
git clone https://github.com/wilson37wu/Actuarial_Stochastic_Model.git
cd Actuarial_Stochastic_Model

# Create and activate virtual environment (named venv_py311 in this project)
python3.11 -m venv venv_py311
source venv_py311/bin/activate        # Unix/macOS
.\venv_py311\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode (for imports to work correctly)
pip install -e .
```

The virtual environment directory is `venv_py311/` (already in `.gitignore`).

---

## Development Workflows

### Running Tests

```bash
# Run all tests (configured via pyproject.toml)
pytest

# With coverage report
pytest --cov=src tests/

# Run a specific test file
pytest tests/hkrbc/test_insurance_risk.py -v

# Run HKRBC tests only
pytest tests/hkrbc/ -v
```

Test configuration in `pyproject.toml`:
- `testpaths = ["tests"]`
- `python_files = ["test_*.py"]`
- `addopts = "-v --cov=actuarial_stochastic_model"`

Note: There is also a test at `src/tests/alm/test_alm.py` outside the standard test directory.

### Code Quality

```bash
# Format code (PEP 8 style enforced by black)
black src/ tests/ examples/

# Lint check
flake8 src/ tests/ examples/
```

### Launching the Dashboard

```bash
# Primary method (Streamlit)
streamlit run src/dashboard/dashboard.py

# Alternative launcher scripts
python run_dashboard.py

# Legacy tkinter GUI
python src/gui/main.py
```

### Running Examples

```bash
python examples/quickstart.py
python examples/product_cashflow_test.py
python examples/generate_hkrbc_report.py
python examples/liability_model_example.py
```

### Generating Economic Scenarios

```bash
python generate_scenarios.py
```

---

## Architecture and Data Flow

```
EconomicScenarioGenerator
  (Hull-White rates, Merton equity, credit spreads, inflation)
        │
        ▼
    ALMEngine  ──── ProcessPoolExecutor (parallel scenarios)
    ┌────┴────┐
    │         │
AssetModel  LiabilityModel
    │         │
    └────┬────┘
         │
    Cash Flows (merged)
         │
    Risk Metrics (VaR 95%, CTE 95%, duration, convexity)
         │
    Dashboard / Reports (Streamlit / Excel / PDF)
```

### Product Class Hierarchy

```
BaseInsuranceContract  (src/models/products/base.py)
├── TermInsurance
├── WholeLifeInsurance
├── ParticipatingWholeLifeBonus   (reversionary bonus)
└── ParticipatingCashDividend     (cash dividend)
```

### HKRBC Capital Hierarchy (Cap 41R)

```
MainRiskAggregator
├── MarketRiskAggregator
│   ├── InterestRateRiskModule    (Cap 41R Section 24 stress factors)
│   ├── CreditSpreadRiskModule
│   ├── EquityRiskModule
│   ├── PropertyRiskModule
│   └── CurrencyRiskModule
├── InsuranceRiskAggregator
│   ├── MortalityRiskModule
│   ├── LongevityRiskModule
│   └── LapseRiskModule
└── OperationalRiskModule
```

Correlation matrices from Cap 41R Schedule 1:
- Top-level: Market/Insurance/Operational — 0.25 cross-correlation
- Risk aggregation uses `sqrt(charges^T @ correlation_matrix @ charges)`

---

## Key Modules Reference

### `src/actuarial_stochastic_model/` (Main Package)

The installable package. Public API exposed via `__init__.py`:
- `PolicyDataGenerator` — generates synthetic policy portfolios
- `TermPolicy`, `WholeLifePolicy`, `ParticipatingPolicy` — policy dataclasses
- `LiabilityModel` — projects cash flows across a policy portfolio
- `MortalityTable`, `LapseAssumption`, `InflationAssumption` — assumption objects
- Enums: `Sex`, `UnderwritingClass`, `SmokingStatus`, `OccupationClass`, `ProductType`, `DividendOption`, `InvestmentStrategy`

### `src/hkrbc/` (Regulatory Module)

Implements Hong Kong Risk-Based Capital framework (Cap 41R — Insurance (Valuation and Capital) Rules).

- **Minimum capital**: HK$20 million (`MINIMUM_CAPITAL_AMOUNT_HKD`)
- **Capital tiers**: Unlimited Tier 1, Limited Tier 1 (10% of PCA), Tier 2 (50% of PCA)
- **IA data download**: Risk-free yield curves and CCA levels from `ia.org.hk`
- All regulatory references cite specific Cap 41R sections in docstrings

### `src/alm_engine.py` — ALMEngine

- `run_stochastic_projection(num_scenarios, projection_years)` — uses `ProcessPoolExecutor`
- `calculate_risk_metrics(results)` — returns `var_95`, `cte_95`, `duration`, `convexity`
- Requires `set_liability_model()` and `set_asset_model()` before running

### `src/economic_scenario_generator.py` — EconomicScenarioGenerator

Configured via `ScenarioConfig` dataclass. Generates scenarios for:
- `short_rate` — Hull-White mean-reverting model
- `long_rate` — short rate + 1% term premium
- `equity_return` — Merton jump-diffusion model
- `credit_spread` — mean-reverting process
- `inflation` — mean-reverting process

### `src/config/` — Configuration System

```python
from src.config.model_config import ModelConfig
config = ModelConfig("config/default_config.json")

# Access sections
config.economic_params    # interest_rate_mean, interest_rate_vol, equity_return_mean, ...
config.asset_params       # allocation, equity, fixed_income settings
config.liability_params   # mortality table, lapse rates, expenses
config.product_params     # per-product parameters keyed by product ID
config.validate()         # raises ValueError if any parameter is out of range
```

Validation rules enforced by `ModelConfig.validate()`:
- `interest_rate_mean`: 0–15%
- `interest_rate_vol`: 0–10%
- `market_volatility`: 0–50%
- `base_lapse_rate`: 0–30%
- Asset allocations must sum to 100%
- Participating product `bonus_rate`: 0–10%

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/default_config.json` | Model parameters (economic, assets, liabilities, products) |
| `model_settings.json` | Runtime settings (asset/liability mix, projection years, premium mode) |
| `model_inputs.json` | Snapshot of model inputs for reproducibility |
| `.streamlit/config.toml` | Streamlit UI theme (red primary color, white background) |
| `pyproject.toml` | Build system + pytest configuration |
| `requirements.txt` | All dependencies including dev tools |

Default asset allocation (`config/default_config.json`):
- Equity: 60%, Fixed Income: 35%, Cash: 5%

Default mortality table: `2012IAM` with 1% annual improvement.

---

## Enumerations

All canonical enums live in `src/actuarial_stochastic_model/enums.py`:

| Enum | Values |
|------|--------|
| `Sex` | MALE, FEMALE |
| `SmokingStatus` | NON_SMOKER, SMOKER |
| `OccupationClass` | CLASS_1 (Professional), CLASS_2 (Technical), CLASS_3 (Light Manual), CLASS_4 (Heavy Manual) |
| `UnderwritingClass` | PREFERRED, STANDARD, SUBSTANDARD |
| `ProductType` | TERM, WHOLE_LIFE, PARTICIPATING, UNIVERSAL_LIFE, UNIT_LINKED |
| `DividendOption` | CASH, PREMIUM_REDUCTION, PAID_UP_ADDITIONS, ACCUMULATE |
| `InvestmentStrategy` | CONSERVATIVE, BALANCED, AGGRESSIVE, CUSTOM |
| `PremiumMode` | ANNUAL, SEMI_ANNUAL, QUARTERLY, MONTHLY, SINGLE, FLEXIBLE |
| `PremiumStatus` | PAYING, PAID_UP, WAIVED, LOAN, OVERDUE |
| `NonForfeitureOption` | REDUCED_PAID_UP, EXTENDED_TERM, CASH_SURRENDER, AUTOMATIC_PREMIUM_LOAN |
| `AssetClass` | CASH, MONEY_MARKET, GOVERNMENT_BOND, CORPORATE_BOND, HIGH_YIELD_BOND, LARGE_CAP_EQUITY, SMALL_CAP_EQUITY, INTERNATIONAL_EQUITY, EMERGING_MARKETS, REAL_ESTATE |

There is also a legacy `src/enums.py`; prefer the package version for new code.

---

## Coding Conventions

### Style
- **PEP 8** enforced via `flake8`; formatted with `black`
- **Type hints** on all function signatures
- **Docstrings** on all public classes and methods; reference regulatory documents where applicable
- `snake_case` for functions, methods, and variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for module-level constants

### Patterns
- **Dataclasses** (`@dataclass`) for data-holding structs (policies, risk results, config)
- **Abstract base classes** (`ABC`) for extensible risk modules — extend `RiskModule` for new risk types
- **`RiskChargeResult` dataclass** as the standard return type for all capital calculations: `risk_name`, `gross_charge`, `net_charge`, `diversification_benefit`, `sub_risks`
- **Composition over inheritance** in the risk aggregation hierarchy
- **`Optional[str]`** for nullable file paths; `Union[...]` for polymorphic policy containers
- Regulatory references always cited in docstrings (e.g., `Cap 41R Section 24`)

### Testing Conventions
- Tests use `unittest.TestCase` with `setUp` for fixtures
- Test method names describe the scenario: `test_level_stress`, `test_mass_lapse`
- HKRBC tests use realistic stress factors from Cap 41R examples
- Assertions verify financial direction (`assertGreater(impact, 0)`) and relationships (`assertLess(net_charge, gross_charge)`)

### Adding New Risk Modules (HKRBC)
1. Subclass `RiskModule` from `src/hkrbc/capital_calculator/base.py`
2. Implement `calculate_risk_charge()` returning a `RiskChargeResult`
3. Use `calculate_diversification_benefit()` from the base class for sub-risk aggregation
4. Register in the appropriate aggregator (`MarketRiskAggregator` or `InsuranceRiskAggregator`)
5. Add tests to `tests/hkrbc/`

### Adding New Insurance Products
1. Subclass `BaseInsuranceContract` from `src/models/products/base.py`
2. Add corresponding `ProductType` enum value if the product is new
3. Create a matching dataclass in `src/actuarial_stochastic_model/models/data_classes.py`
4. Export from `src/actuarial_stochastic_model/__init__.py`

---

## Architecture Notes and Known Issues

### Dual Module Structure
There are two parallel module structures:
- `src/actuarial_stochastic_model/` — the canonical installable package (use this for new code)
- `src/models/` — extended legacy models with additional product implementations

Both coexist; the installable package is the authoritative public API.

### Test Location Anomaly
`src/tests/alm/test_alm.py` is inside the `src/` directory instead of the top-level `tests/`. pytest's configured `testpaths = ["tests"]` will not auto-discover it. Run explicitly if needed:
```bash
pytest src/tests/alm/test_alm.py
```

### Streamlit Dashboard Entry Points
Multiple entry points exist:
- `streamlit run src/dashboard/dashboard.py` — recommended
- `python run_dashboard.py` — uses `src/dashboard/dashboard.py` via import
- `src/main.py` and `src/dashboard.py` — legacy; kept for backward compatibility

### Output Directory
Generated files (Excel reports, PDFs, scenario CSVs) go to `output/`. Excel files are gitignored (`*.xlsx`). PNG images and log files are also gitignored.

### HKRBC Data Downloads
`src/hkrbc/data_provider/ia_downloader.py` fetches risk-free yield curves from `ia.org.hk`. This requires internet access and may need date-parameterized URLs defined in `constants.py`.

---

## Dependencies Summary

### Runtime
| Package | Purpose |
|---------|---------|
| `numpy` | Vectorized numerical computations, correlation matrices |
| `pandas` | DataFrames for cash flows, assumptions, reports |
| `scipy` | Statistical functions, optimization |
| `matplotlib` / `seaborn` | Static charts |
| `plotly` | Interactive charts in dashboard |
| `streamlit` | Web dashboard framework |
| `openpyxl` / `xlsxwriter` | Excel file generation |

### Development
| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `black` | Code formatter |
| `flake8` | Style linter |

---

## Git Workflow

- Default branch: `master`
- Feature branches: `feature/<description>`
- No CI/CD pipelines configured; testing is manual via pytest
- Do not commit: `*.xlsx`, `*.xls`, `*.png`, `*.log`, `venv_py311/`, `__pycache__/`
- HKRBC technical spec PDFs are gitignored: `docs/hkrbc/technical_specs/*.pdf`
