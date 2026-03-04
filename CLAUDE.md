# CLAUDE.md — Actuarial Stochastic Model

This document gives AI assistants a complete orientation to the codebase: what it does, how it is organised, how to develop against it, and the conventions to follow.

---

## Project Overview

**Actuarial Stochastic Model** is a Python framework for stochastic analysis of life-insurance products and portfolios. Its four major capability areas are:

| Area | Description |
|---|---|
| Economic Scenario Generation | Hull-White interest rate model, Merton jump-diffusion equity model, mean-reverting credit spreads and inflation |
| Asset-Liability Management (ALM) | Funding-ratio monitoring, duration-gap analysis, stress testing, rebalancing, reporting (Excel + PDF) |
| Insurance Product Modelling | Term life, whole life, participating (bonus & cash-dividend) products with full cash-flow projections |
| HKRBC Capital Framework | Market risk, insurance risk, and operational risk charges per Hong Kong Cap 41R rules |

The interactive front-end is a **Streamlit dashboard** (`src/dashboard/dashboard.py`).

Python ≥ 3.11 is required. The virtual environment is conventionally named `venv_py311`.

---

## Repository Layout

```
Actuarial_Stochastic_Model/
├── src/                            # All source code
│   ├── __init__.py
│   ├── enums.py                    # Shared enumerations (canonical source of truth)
│   │
│   ├── config/                     # Configuration management
│   │   ├── base_config.py          # Abstract BaseConfig with JSON loading & validation
│   │   └── model_config.py         # Concrete ModelConfig (validates economic/asset/liability/product params)
│   │
│   ├── models/                     # Core model implementations
│   │   ├── assets/                 # Asset models
│   │   │   ├── asset_model.py      # AssetModel – orchestrates fixed-income + equity projections
│   │   │   ├── fixed_income.py     # FixedIncomeModel, Bond dataclass
│   │   │   └── public_equity.py    # EquityModel, Equity dataclass
│   │   ├── liabilities/            # Liability calculations
│   │   │   ├── liability.py        # LiabilityModel, CashFlowProjection
│   │   │   └── actuarial_assumptions.py  # MortalityTable, LapseAssumption, InflationAssumption
│   │   ├── products/               # Insurance product models
│   │   │   ├── base.py             # BaseInsuranceContract (dataclass)
│   │   │   ├── term.py             # Term life
│   │   │   ├── whole_life.py       # Whole life
│   │   │   ├── whole_life_insurance.py
│   │   │   ├── participating_bonus.py   # PAR with bonus
│   │   │   ├── participating_cash.py    # PAR with cash dividend
│   │   │   ├── products.py         # Product factory / combined exports
│   │   │   ├── data_classes.py     # PolicyValues, PolicyLoan
│   │   │   └── enums.py            # Product-level enums (local, mirrors src/enums.py)
│   │   ├── alm/                    # ALM strategy module
│   │   │   ├── config.py
│   │   │   ├── strategy.py         # ALMStrategy, LiabilityCashFlow, AssetCashFlow
│   │   │   ├── utils/calculations.py
│   │   │   └── reporting/          # Excel, PDF, and visualisation reports
│   │   └── data_generator.py       # Synthetic data generation utilities
│   │
│   ├── actuarial_stochastic_model/ # Installable package (pyproject.toml / setup.py)
│   │   ├── enums.py
│   │   └── models/
│   │       ├── data_classes.py
│   │       ├── data_generator.py
│   │       └── liabilities/        # mortality.py, lapse.py, inflation.py, liability_model.py
│   │
│   ├── hkrbc/                      # HKRBC (Hong Kong Risk-Based Capital) module
│   │   ├── constants.py            # Cap 41R constants, CapitalTier enum, IA data URLs
│   │   ├── capital_calculator/
│   │   │   ├── base.py
│   │   │   ├── main_aggregator.py
│   │   │   ├── market_risk/        # interest_rate, credit_spread, equity, property, currency, aggregator
│   │   │   ├── insurance_risk/     # mortality, lapse, longevity, aggregator
│   │   │   └── operational_risk.py
│   │   ├── valuation/
│   │   │   ├── asset_valuer.py
│   │   │   └── liability_valuer.py
│   │   ├── reporting/
│   │   │   ├── excel_report.py
│   │   │   └── pdf_report.py
│   │   └── data_provider/
│   │       └── ia_downloader.py    # Downloads IA risk-free yield curve & CCA levels
│   │
│   ├── dashboard/                  # Streamlit dashboard package
│   │   ├── dashboard.py            # Main Streamlit app entry point
│   │   ├── main.py
│   │   ├── run_dashboard.py
│   │   ├── gcv_analysis.py
│   │   ├── portfolio_analysis.py
│   │   ├── scenario_analysis.py
│   │   ├── sensitivity_analysis.py
│   │   ├── data_export.py
│   │   └── visualization.py
│   ├── dashboard_components/       # Reusable Streamlit UI components
│   │   ├── cash_flow_analysis.py
│   │   ├── dividend_analysis.py
│   │   ├── financial_analysis.py
│   │   ├── gcv_analysis.py
│   │   └── styling.py
│   │
│   ├── dashboard.py                # Legacy top-level dashboard shim
│   ├── alm_engine.py               # ALMEngine (stochastic projection runner, ProcessPoolExecutor)
│   ├── cash_flow_model.py          # DynamicCashFlowModel, CashFlow
│   ├── economic_scenario.py        # EconomicFactors dataclass
│   ├── economic_scenario_generator.py  # EconomicScenarioGenerator (Hull-White, Merton)
│   ├── financial_models.py
│   ├── gcv_calculator.py           # GCVCalculator, GCVParameters, GradingPattern, ProductVariant
│   ├── dividend_tracker.py         # DividendTracker
│   ├── investment.py               # InvestmentPortfolio, AssetParameters, PortfolioType
│   ├── actuarial_assumptions.py    # Top-level assumption factories (legacy shim)
│   ├── actuarial_calculations.py
│   ├── enums.py                    # Canonical enum definitions
│   ├── main.py
│   ├── model_gui.py
│   └── gui/                        # Tkinter-based GUI
│       ├── main.py
│       ├── tabs.py
│       ├── widgets.py
│       └── styles.py
│
├── config/
│   └── default_config.json         # Default model parameters (economic, assets, liabilities, products)
│
├── data/
│   └── assumptions/                # CSV assumptions tables
│       ├── mortality_rates.csv
│       ├── lapse_rates.csv
│       ├── expense_rates.csv
│       ├── interest_rates.csv
│       ├── inflation_rates.csv
│       ├── asset_allocation.csv
│       ├── market_assumptions.csv
│       ├── correlation_matrix.csv
│       ├── trading_costs.csv
│       └── rebalancing_rules.csv
│
├── examples/                       # Runnable example scripts
│   ├── quickstart.py
│   ├── equity_model_example.py
│   ├── fixed_income_examples.py
│   ├── dividend_analysis_example.py
│   ├── liability_model_example.py
│   ├── portfolio_projection_example.py
│   ├── product_cashflow_test.py
│   ├── policy_data_test.py
│   ├── model_gui_example.py
│   └── generate_hkrbc_report.py
│
├── tests/                          # pytest test suite
│   ├── test_financial_models.py
│   ├── test_fixed_income.py
│   ├── test_investment.py
│   ├── test_dashboard.py
│   ├── test_model_performance.py
│   ├── test_small_scenario.py
│   └── hkrbc/
│       ├── test_market_risk.py
│       ├── test_insurance_risk.py
│       └── test_reporting.py
│
├── docs/
│   ├── ARCHITECTURE.md             # Mermaid flowchart of core components
│   ├── development_setup.md        # Full dev-environment guide
│   ├── project_structure.md        # Directory tree reference
│   ├── example_guide.md
│   └── hkrbc/README.md
│
├── output/                         # Generated reports (gitignored binary outputs)
│   ├── alm_written_report_*.pdf
│   └── hkrbc_reports/
│
├── .streamlit/config.toml          # Streamlit server settings
├── requirements.txt                # pip dependencies
├── pyproject.toml                  # Build system + pytest config
├── setup.py                        # setuptools (legacy)
├── run_dashboard.py                # Root-level dashboard launcher shim
├── generate_scenarios.py           # Standalone scenario generation script
├── model_inputs.json               # Sample model inputs
├── model_settings.json             # Model run settings
└── .gitignore
```

---

## Key Architectural Concepts

### 1. Configuration System
- `config/default_config.json` is the single source of model parameters.
- `src/config/base_config.py` provides `BaseConfig`: loads JSON, stores in `_config_data`, offers generic `get()`.
- `src/config/model_config.py` provides `ModelConfig(BaseConfig)`: validates ranges for economic, asset, liability, and product sections. Raises `ValueError` on invalid parameters.
- Asset allocations **must sum to 1.0** (validated with `np.isclose`, tolerance `1e-6`).
- Interest rate mean must be in `[0, 0.15]`; volatility in `[0, 0.10]`.

### 2. Economic Scenario Generation (`src/economic_scenario_generator.py`)
- Uses `ScenarioConfig` dataclass for all stochastic parameters.
- `EconomicScenarioGenerator.generate_scenarios(num_scenarios, projection_years)` returns a dict of NumPy arrays shaped `(time_steps, num_scenarios)` with keys: `short_rate`, `long_rate`, `equity_return`, `credit_spread`, `inflation`.
- **Interest rates**: Hull-White mean-reverting model.
- **Equity returns**: Merton jump-diffusion model (parameters: `jump_intensity`, `jump_mean`, `jump_vol`).
- **Credit spreads and inflation**: mean-reverting (Ornstein-Uhlenbeck style).
- Annual time step (`dt = 1.0`) by default.

### 3. Cash Flow Model (`src/cash_flow_model.py`)
- `CashFlow` represents a single cash event: `amount`, `time_step`, `flow_type`, `policy_id`, `scenario_id`, `date`.
- `DynamicCashFlowModel` takes `mortality_table`, `lapse_rates`, `expense_factors`, `investment_strategy`.
- `project_liability_flows(economic_scenarios, policy_data)` — vectorised over policy ages using `pd.Series`.

### 4. ALM Engine (`src/alm_engine.py`)
- `ALMEngine` coordinates liability model + asset model + scenarios.
- `run_stochastic_projection(num_scenarios, projection_years)` uses `concurrent.futures.ProcessPoolExecutor` for parallel scenario runs.
- Risk metrics: VaR (95%), CTE (95%), duration, convexity.

### 5. ALM Strategy (`src/models/alm/strategy.py`)
- `LiabilityCashFlow` and `AssetCashFlow` are dataclasses holding time-period, expected amount, uncertainty, and discounted value.
- `ALMStrategy` manages funding ratio, duration gap, liquidity, and rebalancing triggers.

### 6. Asset Models (`src/models/assets/`)
- `AssetModel` orchestrates `FixedIncomeModel` and `EquityModel`.
- `project_fixed_income(bonds, scenario_idx)` — monthly projections over 60-month horizon.
- `calculate_portfolio_metrics` returns total market value, weighted duration, weighted convexity.
- Default asset allocation: 60% equity / 35% fixed income / 5% cash.
- Fixed-income credit quality: 30% AAA, 30% AA, 40% A. Duration target: 7.0 years.

### 7. Liability & Product Models (`src/models/liabilities/`, `src/models/products/`)
- `BaseInsuranceContract` (dataclass in `src/models/products/base.py`) holds all policy fields with strong typing via enums.
- Products: `TermLifeInsurance`, `WholeLifeInsurance`, `ParticipatingBonusProduct`, `ParticipatingCashProduct`.
- `CashFlowProjection` dataclass captures time-series of premiums, death benefits, surrenders, expenses, dividends, policy loans, withdrawals.
- Mortality uses the 2012 IAM table by default with `0.01` annual improvement.
- Base lapse rate `0.05`, dynamic factor `0.5`.

### 8. HKRBC Module (`src/hkrbc/`)
- Implements Hong Kong Insurance Authority Cap 41R risk-based capital rules.
- **Market risk**: interest rate (up/down stress), credit spread, equity, property, currency; all aggregated by `MarketRiskAggregator`.
- **Insurance risk**: mortality, longevity, lapse; aggregated by insurance risk aggregator.
- **Operational risk**: `operational_risk.py`.
- **Capital tiers** (from `constants.py`): Unlimited Tier 1 (no limit), Limited Tier 1 (≤10% PCA), Tier 2 (≤50% PCA). Minimum capital: HK$20 million.
- `ia_downloader.py` fetches live risk-free yield curves and CCA levels from `ia.org.hk`.
- Reports available as Excel (`excel_report.py`) and PDF (`pdf_report.py`).

### 9. Dashboard (`src/dashboard/dashboard.py`)
- Built on **Streamlit** + **Plotly** for interactive charts.
- Uses absolute imports from `src.*`; run from the project root.
- Tabs/components in `src/dashboard_components/`: cash flow, dividend, financial, GCV analysis, styling.
- GCV (Guaranteed Cash Value) analysis via `src/gcv_calculator.py` with `GCVParameters`, `GradingPattern`, `ProductVariant`.

---

## Enumerations (Canonical Definitions — `src/enums.py`)

| Enum | Members |
|---|---|
| `AssetClass` | CASH, MONEY_MARKET, GOVERNMENT_BOND, CORPORATE_BOND, HIGH_YIELD_BOND, LARGE_CAP_EQUITY, SMALL_CAP_EQUITY, INTERNATIONAL_EQUITY, EMERGING_MARKETS, REAL_ESTATE |
| `Sex` | MALE, FEMALE |
| `SmokingStatus` | NON_SMOKER, SMOKER |
| `OccupationClass` | CLASS_1 (Professional), CLASS_2 (Technical), CLASS_3 (Light Manual), CLASS_4 (Heavy Manual) |
| `UnderwritingClass` | PREFERRED, STANDARD, SUBSTANDARD |
| `ProductType` | TERM, WHOLE_LIFE, PARTICIPATING, UNIVERSAL_LIFE, UNIT_LINKED |
| `DividendOption` | CASH, PREMIUM_REDUCTION, PAID_UP_ADDITIONS, ACCUMULATE |
| `InvestmentStrategy` | CONSERVATIVE, BALANCED, AGGRESSIVE, CUSTOM |
| `PremiumMode` | ANNUAL, SEMI_ANNUAL, QUARTERLY, MONTHLY, SINGLE, FLEXIBLE |
| `PremiumStatus` | PAYING, PAID_UP, WAIVED, LOAN, OVERDUE |

> **Note**: `src/models/products/products.py` re-declares some of these locally. Prefer `src/enums.py` for new code.

---

## Development Workflows

### Environment Setup

```bash
# Python 3.11+ required
python -m venv venv_py311
source venv_py311/bin/activate          # Windows: venv_py311\Scripts\activate

pip install -r requirements.txt
pip install -e ".[dev]"                 # installs package in editable mode
```

### Running the Dashboard

```bash
# From project root
streamlit run src/dashboard/dashboard.py
# or
python run_dashboard.py
```

### Running Tests

```bash
pytest                                  # run all tests (configured in pyproject.toml)
pytest --cov=src tests/                 # with coverage report
pytest tests/hkrbc/                     # HKRBC tests only
```

Test configuration (`pyproject.toml`):
- `testpaths = ["tests"]`
- `python_files = ["test_*.py"]`
- Coverage target: `actuarial_stochastic_model` package.

Tests use the `unittest.TestCase` style (not bare pytest functions).

### Code Quality

```bash
black src/ tests/ examples/             # auto-format
flake8 src/ tests/ examples/            # style lint
```

### Running Examples

```bash
python examples/quickstart.py
python examples/product_cashflow_test.py
python examples/generate_hkrbc_report.py
```

### Generating Economic Scenarios (Standalone)

```bash
python generate_scenarios.py
```

---

## Configuration Reference (`config/default_config.json`)

```json
{
  "economic": {
    "interest_rate_mean": 0.03,   // Hull-White long-run mean
    "interest_rate_vol": 0.02,
    "equity_return_mean": 0.08,
    "equity_return_vol": 0.15,
    "correlation": { "interest_equity": -0.2 }
  },
  "assets": {
    "allocation": { "equity": 0.6, "fixed_income": 0.35, "cash": 0.05 },
    "equity": {
      "market_volatility": 0.15,
      "dividend_yield": 0.02,
      "sector_weights": { "Technology": 0.25, "Financial": 0.20, ... }
    },
    "fixed_income": {
      "duration_target": 7.0,
      "credit_quality": { "AAA": 0.3, "AA": 0.3, "A": 0.4 }
    }
  },
  "liabilities": {
    "mortality": { "table": "2012IAM", "improvement": 0.01 },
    "lapse": { "base_rate": 0.05, "dynamic_factor": 0.5 },
    "expense": { "acquisition": 100, "maintenance": 50 }
  },
  "products": {
    "WL_001": { "type": "whole_life", "premium_type": "level", ... },
    "PAR_001": { "type": "participating", "bonus_rate": 0.04, ... }
  }
}
```

Always go through `ModelConfig` to read parameters — do not parse the JSON directly in model code.

---

## Code Conventions

### General Style
- **PEP 8** throughout; **black** is the canonical formatter (line length default).
- **Flake8** for lint enforcement.
- **Type hints** on all public functions and method signatures.
- **Docstrings** on all public classes and methods (Google-style or plain description).
- Use `@dataclass` for parameter containers and result objects.
- Use `ABC` / `abstractmethod` for model base classes.

### Naming
- Classes: `PascalCase` (e.g., `ALMEngine`, `FixedIncomeModel`).
- Functions/methods: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Private helpers: prefix with `_` (e.g., `_run_single_scenario`).
- Test classes: `Test<ComponentName>` with `unittest.TestCase`.
- Test methods: `test_<what_is_tested>`.

### Imports
- Standard library → third-party → local; separated by blank lines.
- Always use absolute imports from `src.*` in dashboard code.
- Within `src/models/`, use relative imports (e.g., `from ..enums import ...`).
- Avoid circular imports: enums live in `src/enums.py` and `src/models/products/enums.py` — prefer `src/enums.py` for new code.

### Numerical Computations
- Use NumPy for vectorised array operations; avoid Python loops over large arrays.
- Scenario arrays are always shaped `(time_steps, num_scenarios)`.
- Use `np.isclose(x, y, atol=1e-6)` for floating-point equality checks.
- Parallel scenario processing via `concurrent.futures.ProcessPoolExecutor`.

### Data
- Assumption CSVs live in `data/assumptions/`. Do not hard-code assumption values in model code.
- Excel outputs (`.xlsx`) are gitignored — never commit them.
- PDF reports go under `output/`. The `output/` directory is not gitignored for PDFs.
- HKRBC technical specs PDFs go under `docs/hkrbc/technical_specs/` (gitignored).

---

## Testing Guidelines

- Every new model feature should have a corresponding test in `tests/`.
- HKRBC tests reference specific Cap 41R scenarios — include the reference in the test docstring.
- Use `setUp` for shared test fixtures.
- Test both normal cases and edge cases (zero assets, extreme rates, etc.).
- Mock external network calls (`ia_downloader.py`) in unit tests.
- Run `pytest --cov=src tests/` before submitting changes and aim to keep coverage stable.

---

## Common Pitfalls

1. **Import path issues**: The project has two parallel module trees: `src/` (flat legacy modules) and `src/models/` (structured package). When adding code, be consistent with the existing import pattern in the file you are editing.
2. **Asset allocation validation**: Any code that updates asset allocations must ensure values sum to 1.0 before passing to `ModelConfig.validate()`.
3. **Enum duplication**: `DividendOption`, `InvestmentStrategy`, `PremiumStatus`, `NonForfeitureOption` are defined in both `src/enums.py` and `src/models/products/products.py`. Use `src/enums.py` for new code to avoid confusion.
4. **Dashboard entry point**: Use `src/dashboard/dashboard.py` as the canonical entry point, not the legacy `src/dashboard.py` shim.
5. **ProcessPoolExecutor in ALMEngine**: Scenario-level functions passed to the executor must be picklable — avoid passing lambda functions or closures.
6. **HKRBC data download**: `ia_downloader.py` makes live HTTP requests; wrap calls in try/except and provide offline fallbacks in tests.

---

## Adding a New Insurance Product

1. Create `src/models/products/<product_name>.py`.
2. Inherit from `BaseInsuranceContract` (`src/models/products/base.py`).
3. Implement a `project_cashflows(scenario: EconomicFactors) -> CashFlowProjection` method.
4. Register the product type in the `ProductType` enum (`src/enums.py`).
5. Add a product config section to `config/default_config.json`.
6. Add an example script in `examples/`.
7. Add tests in `tests/test_<product_name>.py`.

## Adding a New HKRBC Risk Module

1. Create `src/hkrbc/capital_calculator/<risk_category>/<module_name>.py`.
2. Inherit from `src/hkrbc/capital_calculator/base.py`.
3. Implement `calculate_risk_charge(...)` returning a result dataclass with `gross_charge` and `sub_risks`.
4. Register the module in the appropriate aggregator.
5. Add tests in `tests/hkrbc/test_<module_name>.py` referencing the Cap 41R section.

---

## Git Workflow

- Branch naming: `feature/<description>`, `fix/<description>`, `claude/<session-id>`.
- Commit messages: imperative mood, concise summary line, reference to what changed and why.
- Never commit: `.xlsx` files, `.png` files, `.log` files, `venv_py311/`, HKRBC technical spec PDFs, `.env`.
- PR process: create feature branch → implement + tests + docs → open PR against `master`.
