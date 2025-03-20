"""
Mortality risk capital calculation.
References Cap 41R Section 26 for mortality stress scenarios.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
from ..base import RiskModule, RiskChargeResult

@dataclass
class MortalityStress:
    """Mortality stress parameters from Cap 41R."""
    level_stress: float = 0.15  # 15% permanent increase
    catastrophe_stress: float = 0.0015  # 0.15% one-off increase

class MortalityRiskModule(RiskModule):
    """
    Calculates capital charge for mortality risk.
    Considers both level and catastrophe stresses.
    """
    
    def __init__(self):
        """Initialize mortality risk module."""
        super().__init__("Mortality Risk")
        self.stress = MortalityStress()
        
    def calculate_level_stress_impact(
        self,
        mortality_rates: np.ndarray,
        sum_assured: np.ndarray,
        discount_factors: np.ndarray
    ) -> float:
        """
        Calculate impact of permanent increase in mortality rates.
        
        Args:
            mortality_rates: Base mortality rates by age/duration
            sum_assured: Sum assured amounts by policy
            discount_factors: Risk-free discount factors
            
        Returns:
            Net impact of level stress
        """
        # Apply stress to mortality rates
        stressed_rates = mortality_rates * (1 + self.stress.level_stress)
        
        # Calculate present value of death benefits
        base_pv = np.sum(mortality_rates * sum_assured * discount_factors)
        stressed_pv = np.sum(stressed_rates * sum_assured * discount_factors)
        
        return stressed_pv - base_pv
        
    def calculate_catastrophe_stress_impact(
        self,
        sum_assured: np.ndarray,
        discount_factors: np.ndarray
    ) -> float:
        """
        Calculate impact of mortality catastrophe.
        
        Args:
            sum_assured: Sum assured amounts by policy
            discount_factors: Risk-free discount factors
            
        Returns:
            Net impact of catastrophe stress
        """
        # Apply one-off increase to first year
        catastrophe_claims = sum_assured * self.stress.catastrophe_stress
        
        # Discount to present value
        return np.sum(catastrophe_claims * discount_factors[0])
        
    def calculate_risk_charge(
        self,
        mortality_data: Dict[str, np.ndarray]
    ) -> RiskChargeResult:
        """
        Calculate mortality risk charge.
        
        Args:
            mortality_data: Dictionary containing:
                - mortality_rates: Base mortality rates
                - sum_assured: Sum assured amounts
                - discount_factors: Risk-free discount factors
            
        Returns:
            Mortality risk capital charge
        """
        # Calculate level stress impact
        level_impact = self.calculate_level_stress_impact(
            mortality_data['mortality_rates'],
            mortality_data['sum_assured'],
            mortality_data['discount_factors']
        )
        
        # Calculate catastrophe stress impact
        cat_impact = self.calculate_catastrophe_stress_impact(
            mortality_data['sum_assured'],
            mortality_data['discount_factors']
        )
        
        # Combine stresses using correlation matrix
        correlation_matrix = np.array([
            [1.0, 0.25],  # Level
            [0.25, 1.0]   # Catastrophe
        ])
        
        charges = [abs(level_impact), abs(cat_impact)]
        div_benefit = self.calculate_diversification_benefit(
            charges, correlation_matrix
        )
        
        total_charge = sum(charges)
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge - div_benefit,
            diversification_benefit=div_benefit,
            sub_risks={
                "Level Stress": RiskChargeResult(
                    risk_name="Level Stress",
                    gross_charge=abs(level_impact),
                    net_charge=abs(level_impact)
                ),
                "Catastrophe Stress": RiskChargeResult(
                    risk_name="Catastrophe Stress",
                    gross_charge=abs(cat_impact),
                    net_charge=abs(cat_impact)
                )
            }
        )
