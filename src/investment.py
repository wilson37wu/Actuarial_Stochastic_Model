"""
Module for investment strategies and asset modeling.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from datetime import date
from .enums import AssetClass

@dataclass
class AssetParameters:
    """Parameters for asset return modeling."""
    expected_return: float
    volatility: float
    correlation: Dict[str, float] = None  # Correlation with other assets
    credit_spread: Optional[float] = None  # For fixed income
    duration: Optional[float] = None      # For fixed income
    dividend_yield: Optional[float] = None # For equity

class PortfolioType(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

@dataclass
class TradingCost:
    fixed_cost: float
    variable_cost: float
    minimum_cost: float
    maximum_cost: float

class InvestmentAssumptions:
    """Class to manage investment-related assumptions loaded from external files."""
    
    # Default values in case files are missing or corrupted
    DEFAULT_ASSET_ALLOCATION = {
        'conservative': {
            'government_bonds': {'target': 0.60, 'min': 0.50, 'max': 0.70},
            'corporate_bonds': {'target': 0.30, 'min': 0.20, 'max': 0.40},
            'public_equity': {'target': 0.10, 'min': 0.05, 'max': 0.15}
        },
        'balanced': {
            'government_bonds': {'target': 0.40, 'min': 0.30, 'max': 0.50},
            'corporate_bonds': {'target': 0.30, 'min': 0.20, 'max': 0.40},
            'public_equity': {'target': 0.30, 'min': 0.20, 'max': 0.40}
        },
        'aggressive': {
            'government_bonds': {'target': 0.20, 'min': 0.10, 'max': 0.30},
            'corporate_bonds': {'target': 0.20, 'min': 0.10, 'max': 0.30},
            'public_equity': {'target': 0.60, 'min': 0.50, 'max': 0.70}
        }
    }
    
    DEFAULT_MARKET_ASSUMPTIONS = {
        'government_bonds': {'return': 0.03, 'volatility': 0.05},
        'corporate_bonds': {'return': 0.04, 'volatility': 0.08},
        'public_equity': {'return': 0.08, 'volatility': 0.15},
        'real_estate': {'return': 0.06, 'volatility': 0.12},
        'private_equity': {'return': 0.12, 'volatility': 0.25},
        'hedge_funds': {'return': 0.07, 'volatility': 0.10},
        'commodities': {'return': 0.05, 'volatility': 0.20},
        'cash': {'return': 0.02, 'volatility': 0.01}
    }
    
    DEFAULT_CORRELATION = np.array([
        [1.00, 0.80, 0.20, 0.30, 0.15, 0.25, 0.10, 0.50],
        [0.80, 1.00, 0.30, 0.35, 0.20, 0.30, 0.15, 0.45],
        [0.20, 0.30, 1.00, 0.60, 0.70, 0.65, 0.40, 0.10],
        [0.30, 0.35, 0.60, 1.00, 0.55, 0.50, 0.35, 0.15],
        [0.15, 0.20, 0.70, 0.55, 1.00, 0.60, 0.45, 0.05],
        [0.25, 0.30, 0.65, 0.50, 0.60, 1.00, 0.50, 0.20],
        [0.10, 0.15, 0.40, 0.35, 0.45, 0.50, 1.00, 0.05],
        [0.50, 0.45, 0.10, 0.15, 0.05, 0.20, 0.05, 1.00]
    ])
    
    DEFAULT_TRADING_COSTS = {
        'government_bonds': TradingCost(0.0001, 0.0005, 5, 1000),
        'corporate_bonds': TradingCost(0.0002, 0.0010, 10, 2000),
        'public_equity': TradingCost(0.0003, 0.0015, 15, 3000),
        'real_estate': TradingCost(0.0100, 0.0200, 1000, 10000),
        'private_equity': TradingCost(0.0150, 0.0250, 2000, 20000),
        'hedge_funds': TradingCost(0.0200, 0.0300, 2500, 25000),
        'commodities': TradingCost(0.0005, 0.0020, 20, 4000),
        'cash': TradingCost(0.0000, 0.0001, 1, 100)
    }

    def __init__(self, assumption_dir=None):
        """Initialize investment assumptions from external files."""
        if assumption_dir is None:
            assumption_dir = Path(__file__).parent.parent / 'assumptions'
        self.assumption_dir = Path(assumption_dir)
        
        # Load assumptions
        self._load_asset_allocation()
        self._load_market_assumptions()
        self._load_correlation_matrix()
        self._load_trading_costs()
        self._load_rebalancing_rules()

    def _load_asset_allocation(self):
        """Load asset allocation from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'asset_allocation.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.asset_allocation = {}
                for portfolio_type in df['portfolio_type'].unique():
                    portfolio_df = df[df['portfolio_type'] == portfolio_type]
                    self.asset_allocation[portfolio_type] = {
                        row['asset_class']: {
                            'target': row['target_allocation'],
                            'min': row['min_allocation'],
                            'max': row['max_allocation']
                        }
                        for _, row in portfolio_df.iterrows()
                    }
            else:
                self.asset_allocation = self.DEFAULT_ASSET_ALLOCATION
        except Exception as e:
            print(f"Error loading asset allocation: {e}")
            self.asset_allocation = self.DEFAULT_ASSET_ALLOCATION

    def _load_market_assumptions(self):
        """Load market assumptions from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'market_assumptions.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.market_assumptions = {
                    row['asset_class']: {
                        'return': row['value'],
                        'volatility': row['volatility']
                    }
                    for _, row in df.iterrows()
                }
            else:
                self.market_assumptions = self.DEFAULT_MARKET_ASSUMPTIONS
        except Exception as e:
            print(f"Error loading market assumptions: {e}")
            self.market_assumptions = self.DEFAULT_MARKET_ASSUMPTIONS

    def _load_correlation_matrix(self):
        """Load correlation matrix from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'correlation_matrix.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                correlation_values = df.iloc[:, 1:].values
                self.correlation_matrix = correlation_values
            else:
                self.correlation_matrix = self.DEFAULT_CORRELATION
        except Exception as e:
            print(f"Error loading correlation matrix: {e}")
            self.correlation_matrix = self.DEFAULT_CORRELATION

    def _load_trading_costs(self):
        """Load trading costs from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'trading_costs.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.trading_costs = {
                    row['asset_class']: TradingCost(
                        fixed_cost=row['fixed_cost'],
                        variable_cost=row['variable_cost'],
                        minimum_cost=row['minimum_cost'],
                        maximum_cost=row['maximum_cost']
                    )
                    for _, row in df.iterrows()
                }
            else:
                self.trading_costs = self.DEFAULT_TRADING_COSTS
        except Exception as e:
            print(f"Error loading trading costs: {e}")
            self.trading_costs = self.DEFAULT_TRADING_COSTS

    def _load_rebalancing_rules(self):
        """Load rebalancing rules from CSV file."""
        try:
            file_path = self.assumption_dir / 'rebalancing_rules.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.rebalancing_rules = df.to_dict('records')
            else:
                self.rebalancing_rules = [
                    {
                        'portfolio_type': pt.value,
                        'rebalancing_frequency': 'quarterly',
                        'threshold_type': 'absolute',
                        'threshold_value': 0.05
                    }
                    for pt in PortfolioType
                ]
        except Exception as e:
            print(f"Error loading rebalancing rules: {e}")
            self.rebalancing_rules = [
                {
                    'portfolio_type': pt.value,
                    'rebalancing_frequency': 'quarterly',
                    'threshold_type': 'absolute',
                    'threshold_value': 0.05
                }
                for pt in PortfolioType
            ]

    def get_asset_allocation(self, portfolio_type: str) -> Dict[str, Dict[str, float]]:
        """Get asset allocation for given portfolio type."""
        return self.asset_allocation.get(portfolio_type.lower(), {})

    def get_market_assumptions(self, asset_class: Union[str, AssetClass]) -> Dict[str, float]:
        """Get market assumptions for an asset class."""
        if isinstance(asset_class, AssetClass):
            asset_key = asset_class.name.lower()
        else:
            asset_key = str(asset_class).lower()
        return self.market_assumptions.get(asset_key, {'return': 0.0, 'volatility': 0.0})

    def get_correlation(self, asset1_id: int, asset2_id: int) -> float:
        """Get correlation between two assets."""
        if 0 <= asset1_id < len(self.correlation_matrix) and 0 <= asset2_id < len(self.correlation_matrix):
            return self.correlation_matrix[asset1_id][asset2_id]
        return 1.0 if asset1_id == asset2_id else 0.0

    def get_trading_cost(self, asset_class: str) -> TradingCost:
        """Get trading costs for given asset class."""
        return self.trading_costs.get(asset_class.lower(), TradingCost(0.0, 0.0, 0.0, float('inf')))

    def get_rebalancing_rule(self, portfolio_type: str) -> Dict:
        """Get rebalancing rules for given portfolio type."""
        return next(
            (rule for rule in self.rebalancing_rules 
             if rule['portfolio_type'].lower() == portfolio_type.lower()),
            {
                'rebalancing_frequency': 'quarterly',
                'threshold_type': 'absolute',
                'threshold_value': 0.05
            }
        )

    def export_assumptions(self, output_dir=None):
        """Export current assumptions to CSV files."""
        if output_dir is None:
            output_dir = self.assumption_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export asset allocation
        allocation_data = []
        for portfolio_type, allocations in self.asset_allocation.items():
            for asset_class, details in allocations.items():
                allocation_data.append({
                    'portfolio_type': portfolio_type,
                    'asset_class': asset_class,
                    'target_allocation': details['target'],
                    'min_allocation': details['min'],
                    'max_allocation': details['max']
                })
        pd.DataFrame(allocation_data).to_csv(
            output_dir / 'asset_allocation.csv', index=False)

        # Export market assumptions
        market_data = []
        for asset_class, details in self.market_assumptions.items():
            market_data.append({
                'asset_class': asset_class,
                'parameter': 'expected_return',
                'value': details['return'],
                'volatility': details['volatility'],
                'correlation_id': list(self.market_assumptions.keys()).index(asset_class) + 1
            })
        pd.DataFrame(market_data).to_csv(
            output_dir / 'market_assumptions.csv', index=False)

        # Export correlation matrix
        correlation_df = pd.DataFrame(
            self.correlation_matrix,
            columns=range(1, len(self.correlation_matrix) + 1)
        )
        correlation_df.insert(0, 'correlation_id', range(1, len(self.correlation_matrix) + 1))
        correlation_df.to_csv(output_dir / 'correlation_matrix.csv', index=False)

        # Export trading costs
        trading_data = []
        for asset_class, costs in self.trading_costs.items():
            trading_data.append({
                'asset_class': asset_class,
                'fixed_cost': costs.fixed_cost,
                'variable_cost': costs.variable_cost,
                'minimum_cost': costs.minimum_cost,
                'maximum_cost': costs.maximum_cost
            })
        pd.DataFrame(trading_data).to_csv(
            output_dir / 'trading_costs.csv', index=False)

        # Export rebalancing rules
        pd.DataFrame(self.rebalancing_rules).to_csv(
            output_dir / 'rebalancing_rules.csv', index=False)

class InvestmentPortfolio:
    """Investment portfolio with dynamic asset allocation and rebalancing."""
    
    def __init__(self, portfolio_type: PortfolioType, initial_balance: float = 0.0,
                 assumptions: Optional[InvestmentAssumptions] = None):
        """Initialize investment portfolio."""
        self.portfolio_type = portfolio_type.value
        self.balance = initial_balance
        self.assumptions = assumptions or InvestmentAssumptions()
        
        # Initialize portfolio based on target allocation
        self.allocation = self.assumptions.get_asset_allocation(self.portfolio_type)
        self.holdings = {
            asset: {'amount': initial_balance * alloc['target']}
            for asset, alloc in self.allocation.items()
        }
        
        # Initialize performance tracking
        self.performance_history = []
        self.rebalancing_history = []
        
    def calculate_expected_return(self) -> float:
        """Calculate portfolio expected return based on current allocation."""
        return sum(
            amount['amount'] / self.balance * self.assumptions.get_market_assumptions(asset)['return']
            for asset, amount in self.holdings.items()
        )

    def calculate_volatility(self) -> float:
        """Calculate portfolio volatility using correlation matrix."""
        weights = np.array([
            amount['amount'] / self.balance
            for amount in self.holdings.values()
        ])
        
        vols = np.array([
            self.assumptions.get_market_assumptions(asset)['volatility']
            for asset in self.holdings.keys()
        ])
        
        corr_matrix = self.assumptions.correlation_matrix[:len(weights), :len(weights)]
        cov_matrix = np.outer(vols, vols) * corr_matrix
        
        return np.sqrt(weights.T @ cov_matrix @ weights)

    def calculate_var(self, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk at given confidence level."""
        z_score = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}.get(confidence_level, 1.65)
        return self.balance * self.calculate_volatility() * z_score

    def calculate_sharpe_ratio(self, risk_free_rate: Optional[float] = None) -> float:
        """Calculate Sharpe ratio."""
        if risk_free_rate is None:
            risk_free_rate = self.assumptions.get_market_assumptions('government_bonds')['return']
        
        excess_return = self.calculate_expected_return() - risk_free_rate
        volatility = self.calculate_volatility()
        
        return excess_return / volatility if volatility > 0 else 0.0

    def rebalance(self, force: bool = False) -> bool:
        """Rebalance portfolio if needed or forced."""
        rule = self.assumptions.get_rebalancing_rule(self.portfolio_type)
        threshold = rule['threshold_value']
        
        # Check if rebalancing is needed
        need_rebalancing = force
        if not need_rebalancing:
            for asset, alloc in self.allocation.items():
                current_weight = self.holdings[asset]['amount'] / self.balance
                target_weight = alloc['target']
                if abs(current_weight - target_weight) > threshold:
                    need_rebalancing = True
                    break
        
        if need_rebalancing:
            # Calculate and apply trades
            trades = {}
            total_cost = 0.0
            
            for asset, alloc in self.allocation.items():
                target_amount = self.balance * alloc['target']
                current_amount = self.holdings[asset]['amount']
                trade_amount = target_amount - current_amount
                
                if abs(trade_amount) > 0:
                    # Calculate trading cost
                    cost = self._calculate_trading_cost(asset, abs(trade_amount))
                    total_cost += cost
                    
                    trades[asset] = {
                        'amount': trade_amount,
                        'cost': cost
                    }
            
            # Apply trades if total cost is acceptable
            if total_cost < self.balance * 0.001:  # Cost threshold of 0.1%
                for asset, trade in trades.items():
                    self.holdings[asset]['amount'] += trade['amount']
                self.balance -= total_cost
                
                # Record rebalancing
                self.rebalancing_history.append({
                    'date': pd.Timestamp.now(),
                    'trades': trades,
                    'total_cost': total_cost
                })
                return True
        
        return False

    def update_allocation(self, new_allocation: Dict[str, float]) -> None:
        """Update portfolio allocation with new target weights.
        
        Args:
            new_allocation: Dictionary mapping asset names to target weights
        """
        # Validate allocation sums to 1
        total_weight = sum(new_allocation.values())
        if not np.isclose(total_weight, 1.0, rtol=1e-5):
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
            
        # Update allocation targets
        for asset, weight in new_allocation.items():
            if asset not in self.allocation:
                self.allocation[asset] = {'target': weight, 'min': 0.0, 'max': 1.0}
            else:
                self.allocation[asset]['target'] = weight
                
        # Update holdings based on new allocation
        for asset, weight in new_allocation.items():
            target_amount = self.balance * weight
            if asset not in self.holdings:
                self.holdings[asset] = {'amount': target_amount}
            else:
                self.holdings[asset]['amount'] = target_amount
                
        # Force rebalancing to match new allocation
        self.rebalance(force=True)

    def get_portfolio_metrics(self) -> Dict[str, float]:
        """Get portfolio performance and risk metrics."""
        metrics = {}
        
        # Return metrics
        metrics['expected_return'] = self.calculate_expected_return()
        metrics['volatility'] = self.calculate_volatility()
        metrics['sharpe_ratio'] = self.calculate_sharpe_ratio()
        metrics['var_95'] = self.calculate_var(confidence_level=0.95)
        
        # Income metrics
        current_yield = 0.0
        duration = 0.0
        total_fixed_income = 0.0
        
        for asset, holding in self.holdings.items():
            amount = holding['amount']
            asset_params = self.assumptions.get_market_assumptions(asset)
            
            # Calculate yield contribution
            if 'dividend_yield' in asset_params and asset_params['dividend_yield']:
                current_yield += asset_params['dividend_yield'] * (amount / self.balance)
            
            # Calculate duration for fixed income
            if 'duration' in asset_params and asset_params['duration']:
                weight = amount / self.balance
                duration += asset_params['duration'] * weight
                total_fixed_income += weight
        
        metrics['current_yield'] = current_yield
        metrics['duration'] = duration if total_fixed_income > 0 else 0.0
        
        # Risk metrics relative to benchmark
        benchmark_return = 0.06  # Example benchmark return
        benchmark_vol = 0.10     # Example benchmark volatility
        
        # Calculate tracking error
        if len(self.performance_history) > 0:
            returns = pd.DataFrame(self.performance_history)['return']
            tracking_error = np.std(returns - benchmark_return) * np.sqrt(252)
            metrics['tracking_error'] = tracking_error
            
            # Calculate information ratio
            excess_return = self.calculate_expected_return() - benchmark_return
            metrics['information_ratio'] = excess_return / tracking_error if tracking_error > 0 else 0.0
            
            # Calculate beta and alpha
            portfolio_vol = self.calculate_volatility()
            correlation = 0.8  # Example correlation with market
            beta = correlation * (portfolio_vol / benchmark_vol)
            metrics['beta'] = beta
            
            alpha = excess_return - beta * benchmark_return
            metrics['alpha'] = alpha
        else:
            metrics.update({
                'tracking_error': 0.0,
                'information_ratio': 0.0,
                'beta': 1.0,
                'alpha': 0.0
            })
        
        return metrics

    def _calculate_trading_cost(self, asset: str, amount: float) -> float:
        """Calculate trading cost for given asset and amount."""
        cost = self.assumptions.get_trading_cost(asset)
        total_cost = cost.fixed_cost + amount * cost.variable_cost
        return max(min(total_cost, cost.maximum_cost), cost.minimum_cost)

    def update_performance(self, date: pd.Timestamp, market_returns: Dict[str, float]):
        """Update portfolio performance based on market returns."""
        for asset, holding in self.holdings.items():
            if asset in market_returns:
                holding['amount'] *= (1 + market_returns[asset])
        
        new_balance = sum(holding['amount'] for holding in self.holdings.values())
        period_return = (new_balance - self.balance) / self.balance
        
        self.performance_history.append({
            'date': date,
            'balance': new_balance,
            'return': period_return
        })
        
        self.balance = new_balance

class TargetDateStrategy:
    """Target date investment strategy."""
    
    def __init__(self, 
                 target_year: int,
                 initial_equity: float = 0.9,
                 final_equity: float = 0.3):
        """Initialize target date strategy."""
        self.target_year = target_year
        self.initial_equity = initial_equity
        self.final_equity = final_equity
        
        # Define glide path
        years_to_target = max(0, target_year - date.today().year)
        self.years_to_retirement = years_to_target
        
        # Initialize conservative allocation
        self.conservative = {
            AssetClass.CASH: 0.05,
            AssetClass.MONEY_MARKET: 0.10,
            AssetClass.GOVERNMENT_BOND: 0.35,
            AssetClass.CORPORATE_BOND: 0.20,
            AssetClass.LARGE_CAP_EQUITY: 0.20,
            AssetClass.INTERNATIONAL_EQUITY: 0.10
        }
        
        # Initialize aggressive allocation
        self.aggressive = {
            AssetClass.CASH: 0.02,
            AssetClass.MONEY_MARKET: 0.03,
            AssetClass.GOVERNMENT_BOND: 0.05,
            AssetClass.CORPORATE_BOND: 0.10,
            AssetClass.LARGE_CAP_EQUITY: 0.40,
            AssetClass.SMALL_CAP_EQUITY: 0.15,
            AssetClass.INTERNATIONAL_EQUITY: 0.15,
            AssetClass.EMERGING_MARKETS: 0.10
        }
    
    def get_allocation(self, current_date: date) -> Dict[AssetClass, float]:
        """Get target allocation based on current date."""
        years_remaining = max(0, self.target_year - current_date.year)
        equity_weight = self._calculate_equity_weight(years_remaining)
        
        # Interpolate between conservative and aggressive allocations
        allocation = {}
        all_assets = set(self.conservative.keys()) | set(self.aggressive.keys())
        
        for asset in all_assets:
            conservative_alloc = self.conservative.get(asset, 0.0)
            aggressive_alloc = self.aggressive.get(asset, 0.0)
            allocation[asset] = (
                conservative_alloc * (1 - equity_weight) +
                aggressive_alloc * equity_weight
            )
        
        return allocation
    
    def _calculate_equity_weight(self, years_remaining: int) -> float:
        """Calculate equity weight based on years to target date."""
        if years_remaining >= self.years_to_retirement:
            return self.initial_equity
        elif years_remaining <= 0:
            return self.final_equity
        else:
            # Linear interpolation
            progress = years_remaining / self.years_to_retirement
            return self.final_equity + (
                self.initial_equity - self.final_equity
            ) * progress

class DynamicStrategy:
    """Dynamic investment strategy based on market conditions."""
    
    def __init__(self,
                 base_allocation: Dict[AssetClass, float],
                 max_deviation: float = 0.2):
        """Initialize dynamic strategy."""
        self.base_allocation = base_allocation
        self.max_deviation = max_deviation
        self.market_indicators = {
            'momentum': 0.0,    # Price momentum
            'volatility': 0.0,  # Market volatility
            'yield_curve': 0.0, # Yield curve slope
            'valuation': 0.0    # Market valuation metrics
        }
    
    def update_indicators(self,
                        momentum: float,
                        volatility: float,
                        yield_curve: float,
                        valuation: float):
        """Update market indicators."""
        self.market_indicators.update({
            'momentum': momentum,
            'volatility': volatility,
            'yield_curve': yield_curve,
            'valuation': valuation
        })
    
    def get_allocation(self) -> Dict[AssetClass, float]:
        """Get dynamic allocation based on market indicators."""
        # Calculate composite signal (-1 to 1)
        signal = (
            0.3 * self.market_indicators['momentum'] +
            -0.3 * self.market_indicators['volatility'] +
            0.2 * self.market_indicators['yield_curve'] +
            0.2 * self.market_indicators['valuation']
        )
        
        # Adjust allocations
        allocation = {}
        risk_assets = {
            AssetClass.LARGE_CAP_EQUITY,
            AssetClass.SMALL_CAP_EQUITY,
            AssetClass.INTERNATIONAL_EQUITY,
            AssetClass.EMERGING_MARKETS,
            AssetClass.HIGH_YIELD_BOND
        }
        
        safe_assets = {
            AssetClass.CASH,
            AssetClass.MONEY_MARKET,
            AssetClass.GOVERNMENT_BOND
        }
        
        for asset, base_alloc in self.base_allocation.items():
            if asset in risk_assets:
                # Increase risk assets when signal is positive
                adjustment = self.max_deviation * signal
            elif asset in safe_assets:
                # Decrease safe assets when signal is positive
                adjustment = -self.max_deviation * signal
            else:
                adjustment = 0.0
            
            allocation[asset] = max(0.0, min(1.0, base_alloc + adjustment))
        
        # Normalize allocations to sum to 1
        total = sum(allocation.values())
        return {k: v/total for k, v in allocation.items()}
