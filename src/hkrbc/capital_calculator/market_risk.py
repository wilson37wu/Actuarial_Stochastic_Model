"""
Market risk capital calculation module.
References:
- Cap 41R Part 5, Division 3: Market Risk
"""

from typing import Dict, List, Optional
import numpy as np
from .base import RiskModule, RiskChargeResult

class InterestRateRiskModule(RiskModule):
    """
    Calculates capital charge for interest rate risk.
    References Cap 41R Section 24.
    """
    
    def __init__(self):
        """Initialize interest rate risk module."""
        super().__init__("Interest Rate Risk")
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate interest rate risk charge.
        Considers both upward and downward stress scenarios.
        """
        # TODO: Implement stress scenarios from Cap 41R
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=0.0,  # Placeholder
            net_charge=0.0
        )

class CreditSpreadRiskModule(RiskModule):
    """
    Calculates capital charge for credit spread risk.
    References Cap 41R Section 25.
    """
    
    def __init__(self):
        """Initialize credit spread risk module."""
        super().__init__("Credit Spread Risk")
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """Calculate credit spread risk charge."""
        # TODO: Implement based on credit quality and duration
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=0.0,  # Placeholder
            net_charge=0.0
        )

class MarketRiskModule(RiskModule):
    """
    Aggregates all market risk components.
    References Cap 41R Schedule 1 for correlation matrix.
    """
    
    def __init__(self):
        """Initialize market risk module with sub-modules."""
        super().__init__("Market Risk")
        
        # Add sub-modules
        self.add_sub_module(InterestRateRiskModule())
        self.add_sub_module(CreditSpreadRiskModule())
        # TODO: Add other market risk modules (equity, property, currency)
        
        # Market risk correlation matrix from Cap 41R Schedule 1
        self.correlation_matrix = np.array([
            [1.0, 0.25],  # Placeholder 2x2 matrix
            [0.25, 1.0]
        ])
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate total market risk charge with diversification.
        """
        # Calculate charges for each sub-module
        sub_charges: Dict[str, RiskChargeResult] = {
            module.name: module.calculate_risk_charge()
            for module in self._sub_modules
        }
        
        # Extract gross charges for diversification calculation
        charges_list = [charge.gross_charge for charge in sub_charges.values()]
        
        # Calculate diversification benefit
        div_benefit = self.calculate_diversification_benefit(
            charges_list, self.correlation_matrix
        )
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=sum(charges_list),
            net_charge=sum(charges_list) - div_benefit,
            diversification_benefit=div_benefit,
            sub_risks=sub_charges
        )
