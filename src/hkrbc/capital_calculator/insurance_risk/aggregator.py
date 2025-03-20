"""
Insurance risk aggregation module.
References Cap 41R Schedule 1 for correlation matrix.
"""

import numpy as np
from typing import Dict
from ..base import RiskModule, RiskChargeResult
from .mortality import MortalityRiskModule
from .longevity import LongevityRiskModule
from .lapse import LapseRiskModule

class InsuranceRiskAggregator(RiskModule):
    """
    Aggregates all insurance risk components using correlation matrix.
    """
    
    def __init__(self):
        """Initialize insurance risk aggregator with all sub-modules."""
        super().__init__("Insurance Risk")
        
        # Initialize sub-modules
        self.add_sub_module(MortalityRiskModule())
        self.add_sub_module(LongevityRiskModule())
        self.add_sub_module(LapseRiskModule())
        
        # Correlation matrix from Cap 41R Schedule 1
        self.correlation_matrix = np.array([
            # MOR   LON   LAP
            [1.00, -0.25, 0.00],  # Mortality
            [-0.25, 1.00, 0.00],  # Longevity
            [0.00, 0.00, 1.00]    # Lapse
        ])
        
    def calculate_risk_charge(
        self,
        insurance_data: Dict[str, Dict]
    ) -> RiskChargeResult:
        """
        Calculate total insurance risk charge with diversification.
        
        Args:
            insurance_data: Dictionary containing data for each risk module:
                {
                    'mortality': {...},
                    'longevity': {...},
                    'lapse': {...}
                }
            
        Returns:
            Total insurance risk capital charge
        """
        # Calculate charges for each sub-module
        sub_charges: Dict[str, RiskChargeResult] = {}
        
        for module in self._sub_modules:
            module_data = insurance_data.get(
                module.name.lower().replace(' ', '_'),
                {}
            )
            sub_charges[module.name] = module.calculate_risk_charge(module_data)
            
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
