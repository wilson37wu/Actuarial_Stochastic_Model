"""
Property risk capital calculation.
References Cap 41R Section 27.
"""

from typing import Dict, List
from ..base import RiskModule, RiskChargeResult

class PropertyRiskModule(RiskModule):
    """
    Calculates capital charge for property risk.
    Applies 25% stress to property values.
    """
    
    def __init__(self):
        """Initialize property risk module."""
        super().__init__("Property Risk")
        self.stress_factor = 0.25  # -25% stress
        
    def calculate_risk_charge(
        self,
        property_exposures: List[Dict[str, float]]
    ) -> RiskChargeResult:
        """
        Calculate property risk charge.
        
        Args:
            property_exposures: List of property exposures with keys:
                - market_value: Market value of property
                - type: Property type (e.g., 'commercial', 'residential')
            
        Returns:
            Property risk capital charge
        """
        sub_charges: Dict[str, RiskChargeResult] = {}
        total_charge = 0.0
        
        # Calculate charge for each property
        for i, exposure in enumerate(property_exposures):
            market_value = exposure['market_value']
            property_type = exposure['type']
            
            # Apply stress
            charge = market_value * self.stress_factor
            
            sub_charges[f"{property_type}_{i}"] = RiskChargeResult(
                risk_name=f"{property_type.title()} Property {i}",
                gross_charge=charge,
                net_charge=charge
            )
            total_charge += charge
            
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge,  # No management actions considered
            sub_risks=sub_charges
        )
