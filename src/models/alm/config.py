"""
Asset Liability Management (ALM) Configuration

This module defines the configuration parameters and constraints used in the ALM system.
It includes risk limits, rebalancing thresholds, transaction costs, and asset class
characteristics.

The configuration is organized into three main components:
1. ALMConfig: General ALM strategy parameters
2. AssetClassConfig: Individual asset class characteristics
3. Default configurations and correlation matrices

Example:
    >>> config = ALMConfig()
    >>> print(config.target_funding_ratio)
    1.05
    >>> govt_bonds = DEFAULT_ASSET_CLASSES["government_bonds"]
    >>> print(govt_bonds.duration)
    7.0
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ALMConfig:
    """
    Configuration parameters for the ALM strategy.
    
    This class defines the key parameters and constraints used in the ALM strategy,
    including risk limits, rebalancing thresholds, and transaction costs.
    
    Attributes:
        max_duration_gap (float): Maximum allowed duration mismatch between assets and liabilities
        min_funding_ratio (float): Minimum acceptable funding ratio
        target_funding_ratio (float): Target funding ratio for the strategy
        max_funding_ratio (float): Maximum allowed funding ratio
        min_liquidity_ratio (float): Minimum required liquidity ratio
        funding_ratio_threshold (float): Threshold for funding ratio rebalancing
        duration_gap_threshold (float): Threshold for duration gap rebalancing
        tracking_error_threshold (float): Maximum allowed tracking error
        confidence_level (float): Confidence level for risk metrics
        risk_aversion (float): Risk aversion parameter for optimization
        fixed_transaction_cost (float): Fixed cost per transaction
        variable_transaction_cost_bps (float): Variable transaction cost in basis points
        min_allocation (Dict[str, float]): Minimum allocation constraints by asset class
        max_allocation (Dict[str, float]): Maximum allocation constraints by asset class
        stress_scenarios (Dict[str, Dict[str, float]]): Defined stress test scenarios
    """
    
    # Risk limits
    max_duration_gap: float = 1.0
    min_funding_ratio: float = 0.95
    target_funding_ratio: float = 1.05
    max_funding_ratio: float = 1.15
    min_liquidity_ratio: float = 0.15
    
    # Rebalancing thresholds
    funding_ratio_threshold: float = 0.05
    duration_gap_threshold: float = 0.5
    tracking_error_threshold: float = 0.02
    
    # Risk parameters
    confidence_level: float = 0.95
    risk_aversion: float = 2.0
    
    # Transaction costs
    fixed_transaction_cost: float = 100
    variable_transaction_cost_bps: float = 10
    
    # Asset class constraints
    min_allocation: Dict[str, float] = None
    max_allocation: Dict[str, float] = None
    
    # Stress test scenarios
    stress_scenarios: Dict[str, Dict[str, float]] = None
    
    def __post_init__(self):
        """
        Initialize default values for dictionaries if not provided.
        
        This method sets up default allocation constraints and stress test scenarios
        if they are not explicitly provided during initialization.
        """
        if self.min_allocation is None:
            self.min_allocation = {
                "government_bonds": 0.2,
                "corporate_bonds": 0.1,
                "equities": 0.0,
                "cash": 0.05
            }
        
        if self.max_allocation is None:
            self.max_allocation = {
                "government_bonds": 0.8,
                "corporate_bonds": 0.4,
                "equities": 0.3,
                "cash": 0.2
            }
        
        if self.stress_scenarios is None:
            self.stress_scenarios = {
                "base": {
                    "interest_rate_shock": 0.01,
                    "credit_spread_shock": 0.005,
                    "equity_shock": -0.10,
                    "inflation_shock": 0.02
                },
                "severe": {
                    "interest_rate_shock": 0.02,
                    "credit_spread_shock": 0.01,
                    "equity_shock": -0.20,
                    "inflation_shock": 0.04
                },
                "extreme": {
                    "interest_rate_shock": 0.03,
                    "credit_spread_shock": 0.02,
                    "equity_shock": -0.30,
                    "inflation_shock": 0.06
                }
            }

@dataclass
class AssetClassConfig:
    """
    Configuration for individual asset classes.
    
    This class defines the characteristics and parameters for each asset class
    used in the ALM strategy.
    
    Attributes:
        name (str): Name of the asset class
        expected_return (float): Expected annual return
        volatility (float): Annual return volatility
        duration (float): Interest rate sensitivity
        credit_quality (str): Credit rating or quality indicator
        liquidity_score (float): Liquidity score (1-10, 10 being most liquid)
    """
    name: str
    expected_return: float
    volatility: float
    duration: float
    credit_quality: str
    liquidity_score: float  # 1-10, 10 being most liquid
    
    def __post_init__(self):
        """Validate liquidity score is within acceptable range."""
        assert 0 <= self.liquidity_score <= 10, "Liquidity score must be between 0 and 10"

# Default asset class configurations
DEFAULT_ASSET_CLASSES = {
    "government_bonds": AssetClassConfig(
        name="government_bonds",
        expected_return=0.03,
        volatility=0.05,
        duration=7.0,
        credit_quality="AAA",
        liquidity_score=9
    ),
    "corporate_bonds": AssetClassConfig(
        name="corporate_bonds",
        expected_return=0.04,
        volatility=0.08,
        duration=5.0,
        credit_quality="BBB",
        liquidity_score=7
    ),
    "equities": AssetClassConfig(
        name="equities",
        expected_return=0.07,
        volatility=0.15,
        duration=0.0,
        credit_quality="N/A",
        liquidity_score=8
    ),
    "cash": AssetClassConfig(
        name="cash",
        expected_return=0.02,
        volatility=0.01,
        duration=0.0,
        credit_quality="AAA",
        liquidity_score=10
    )
}

# Correlation matrix between asset classes
CORRELATION_MATRIX = {
    "government_bonds": {
        "government_bonds": 1.0,
        "corporate_bonds": 0.7,
        "equities": -0.2,
        "cash": 0.2
    },
    "corporate_bonds": {
        "government_bonds": 0.7,
        "corporate_bonds": 1.0,
        "equities": 0.3,
        "cash": 0.1
    },
    "equities": {
        "government_bonds": -0.2,
        "corporate_bonds": 0.3,
        "equities": 1.0,
        "cash": -0.1
    },
    "cash": {
        "government_bonds": 0.2,
        "corporate_bonds": 0.1,
        "equities": -0.1,
        "cash": 1.0
    }
} 