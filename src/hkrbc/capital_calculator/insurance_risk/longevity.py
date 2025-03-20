"""
Longevity risk capital calculation.
References Cap 41R Section 27 for longevity stress scenarios.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np
from ..base import RiskModule, RiskChargeResult

@dataclass
class LongevityStress:
    """Longevity stress parameters from Cap 41R."""
    mortality_reduction: float = 0.20  # 20% permanent decrease

class LongevityRiskModule(RiskModule):
    """
    Calculates capital charge for longevity risk.
    Considers permanent decrease in mortality rates.
    """
    
    def __init__(self):
        """Initialize longevity risk module."""
        super().__init__("Longevity Risk")
        self.stress = LongevityStress()
        
    def calculate_stress_impact(
        self,
        mortality_rates: np.ndarray,
        annuity_payments: np.ndarray,
        discount_factors: np.ndarray
    ) -> float:
        """
        Calculate impact of permanent decrease in mortality rates.
        
        Args:
            mortality_rates: Base mortality rates by age/duration
            annuity_payments: Annual annuity payments by policy
            discount_factors: Risk-free discount factors
            
        Returns:
            Net impact of longevity stress
        """
        # Apply stress to mortality rates
        stressed_rates = mortality_rates * (1 - self.stress.mortality_reduction)
        
        # Calculate survival probabilities
        base_survival = np.cumprod(1 - mortality_rates, axis=0)
        stressed_survival = np.cumprod(1 - stressed_rates, axis=0)
        
        # Calculate present value of annuity payments
        base_pv = np.sum(base_survival * annuity_payments * discount_factors)
        stressed_pv = np.sum(stressed_survival * annuity_payments * discount_factors)
        
        return stressed_pv - base_pv
        
    def calculate_risk_charge(
        self,
        longevity_data: Dict[str, np.ndarray]
    ) -> RiskChargeResult:
        """
        Calculate longevity risk charge.
        
        Args:
            longevity_data: Dictionary containing:
                - mortality_rates: Base mortality rates
                - annuity_payments: Annual annuity payments
                - discount_factors: Risk-free discount factors
            
        Returns:
            Longevity risk capital charge
        """
        # Calculate stress impact
        impact = self.calculate_stress_impact(
            longevity_data['mortality_rates'],
            longevity_data['annuity_payments'],
            longevity_data['discount_factors']
        )
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=abs(impact),
            net_charge=abs(impact),  # No management actions considered
            sub_risks={
                "Base Stress": RiskChargeResult(
                    risk_name="Base Stress",
                    gross_charge=abs(impact),
                    net_charge=abs(impact)
                )
            }
        )
