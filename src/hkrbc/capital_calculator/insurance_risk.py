"""
Insurance risk capital calculation module.
References:
- Cap 41R Part 5, Division 4: Insurance Risk
"""

from typing import Dict
import numpy as np
from .base import RiskModule, RiskChargeResult

class MortalityRiskModule(RiskModule):
    """
    Calculates capital charge for mortality risk.
    References Cap 41R Section 26.
    """
    
    def __init__(self):
        """Initialize mortality risk module."""
        super().__init__("Mortality Risk")
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate mortality risk charge.
        Applies permanent 15% increase in mortality rates.
        """
        # TODO: Implement mortality stress scenario
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=0.0,  # Placeholder
            net_charge=0.0
        )

class LongevityRiskModule(RiskModule):
    """
    Calculates capital charge for longevity risk.
    References Cap 41R Section 27.
    """
    
    def __init__(self):
        """Initialize longevity risk module."""
        super().__init__("Longevity Risk")
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate longevity risk charge.
        Applies permanent 20% decrease in mortality rates.
        """
        # TODO: Implement longevity stress scenario
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=0.0,  # Placeholder
            net_charge=0.0
        )

class LapseRiskModule(RiskModule):
    """
    Calculates capital charge for lapse risk.
    References Cap 41R Section 29.
    """
    
    def __init__(self):
        """Initialize lapse risk module."""
        super().__init__("Lapse Risk")
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate lapse risk charge.
        Considers mass lapse event and permanent changes in lapse rates.
        """
        # TODO: Implement lapse stress scenarios
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=0.0,  # Placeholder
            net_charge=0.0
        )

class InsuranceRiskModule(RiskModule):
    """
    Aggregates all insurance risk components.
    References Cap 41R Schedule 1 for correlation matrix.
    """
    
    def __init__(self):
        """Initialize insurance risk module with sub-modules."""
        super().__init__("Insurance Risk")
        
        # Add sub-modules
        self.add_sub_module(MortalityRiskModule())
        self.add_sub_module(LongevityRiskModule())
        self.add_sub_module(LapseRiskModule())
        # TODO: Add other insurance risk modules (disability, expense)
        
        # Insurance risk correlation matrix from Cap 41R Schedule 1
        self.correlation_matrix = np.array([
            [1.0, -0.25, 0.0],  # Mortality
            [-0.25, 1.0, 0.0],  # Longevity
            [0.0, 0.0, 1.0]     # Lapse
        ])
        
    def calculate_risk_charge(self) -> RiskChargeResult:
        """
        Calculate total insurance risk charge with diversification.
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
