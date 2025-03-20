"""
Market risk aggregation module.
References Cap 41R Schedule 1 for correlation matrix.
"""

import numpy as np
from typing import Dict, Optional
from ..base import RiskModule, RiskChargeResult
from .interest_rate import InterestRateRiskModule
from .credit_spread import CreditSpreadRiskModule
from .equity import EquityRiskModule
from .property import PropertyRiskModule
from .currency import CurrencyRiskModule

class MarketRiskAggregator(RiskModule):
    """
    Aggregates all market risk components using correlation matrix.
    """
    
    def __init__(self):
        """Initialize market risk aggregator with all sub-modules."""
        super().__init__("Market Risk")
        
        # Initialize sub-modules
        self.add_sub_module(InterestRateRiskModule())
        self.add_sub_module(CreditSpreadRiskModule())
        self.add_sub_module(EquityRiskModule())
        self.add_sub_module(PropertyRiskModule())
        self.add_sub_module(CurrencyRiskModule())
        
        # Correlation matrix from Cap 41R Schedule 1
        self.correlation_matrix = np.array([
            # IR    CS    EQ    PR    FX
            [1.00, 0.25, 0.25, 0.25, 0.25],  # Interest Rate
            [0.25, 1.00, 0.75, 0.50, 0.25],  # Credit Spread
            [0.25, 0.75, 1.00, 0.75, 0.25],  # Equity
            [0.25, 0.50, 0.75, 1.00, 0.25],  # Property
            [0.25, 0.25, 0.25, 0.25, 1.00]   # Currency
        ])
        
    def calculate_risk_charge(
        self,
        market_data: Dict[str, Dict]
    ) -> RiskChargeResult:
        """
        Calculate total market risk charge with diversification.
        
        Args:
            market_data: Dictionary containing data for each risk module:
                {
                    'interest_rate': {...},
                    'credit_spread': {...},
                    'equity': {...},
                    'property': {...},
                    'currency': {...}
                }
            
        Returns:
            Total market risk capital charge
        """
        # Calculate charges for each sub-module
        sub_charges: Dict[str, RiskChargeResult] = {}
        
        for module in self._sub_modules:
            module_data = market_data.get(module.name.lower().replace(' ', '_'), {})
            sub_charges[module.name] = module.calculate_risk_charge(**module_data)
            
        # Extract gross charges for diversification calculation
        charges_list = [charge.gross_charge for charge in sub_charges.values()]
        
        # Calculate diversification benefit
        div_benefit = self.calculate_diversification_benefit(
            charges_list, self.correlation_matrix
        )
        
        total_charge = sum(charges_list)
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge - div_benefit,
            diversification_benefit=div_benefit,
            sub_risks=sub_charges
        )
