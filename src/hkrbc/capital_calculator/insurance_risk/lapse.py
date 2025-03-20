"""
Lapse risk capital calculation.
References Cap 41R Section 29 for lapse stress scenarios.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from ..base import RiskModule, RiskChargeResult

@dataclass
class LapseStress:
    """Lapse stress parameters from Cap 41R."""
    mass_lapse_rate: float = 0.30  # 30% immediate surrender
    up_stress: float = 0.50  # 50% permanent increase
    down_stress: float = 0.50  # 50% permanent decrease

class LapseRiskModule(RiskModule):
    """
    Calculates capital charge for lapse risk.
    Considers mass lapse and permanent changes in lapse rates.
    """
    
    def __init__(self):
        """Initialize lapse risk module."""
        super().__init__("Lapse Risk")
        self.stress = LapseStress()
        
    def calculate_mass_lapse_impact(
        self,
        policy_values: np.ndarray,
        surrender_values: np.ndarray
    ) -> float:
        """
        Calculate impact of mass lapse event.
        
        Args:
            policy_values: Policy values by policy
            surrender_values: Surrender values by policy
            
        Returns:
            Net impact of mass lapse stress
        """
        # Calculate loss on mass surrender
        loss_on_surrender = policy_values - surrender_values
        
        # Apply mass lapse rate
        return np.sum(loss_on_surrender * self.stress.mass_lapse_rate)
        
    def calculate_trend_stress_impact(
        self,
        lapse_rates: np.ndarray,
        policy_cashflows: np.ndarray,
        discount_factors: np.ndarray,
        stress_type: str
    ) -> float:
        """
        Calculate impact of permanent change in lapse rates.
        
        Args:
            lapse_rates: Base lapse rates by duration
            policy_cashflows: Projected policy cashflows
            discount_factors: Risk-free discount factors
            stress_type: Either 'up' or 'down'
            
        Returns:
            Net impact of trend stress
        """
        stress = (
            self.stress.up_stress if stress_type == 'up'
            else -self.stress.down_stress
        )
        
        # Apply stress to lapse rates
        stressed_rates = np.clip(lapse_rates * (1 + stress), 0, 1)
        
        # Calculate persistency rates
        base_persistency = np.cumprod(1 - lapse_rates, axis=0)
        stressed_persistency = np.cumprod(1 - stressed_rates, axis=0)
        
        # Calculate present value of cashflows
        base_pv = np.sum(base_persistency * policy_cashflows * discount_factors)
        stressed_pv = np.sum(stressed_persistency * policy_cashflows * discount_factors)
        
        return stressed_pv - base_pv
        
    def calculate_risk_charge(
        self,
        lapse_data: Dict[str, np.ndarray]
    ) -> RiskChargeResult:
        """
        Calculate lapse risk charge.
        
        Args:
            lapse_data: Dictionary containing:
                - lapse_rates: Base lapse rates
                - policy_values: Policy values
                - surrender_values: Surrender values
                - policy_cashflows: Projected policy cashflows
                - discount_factors: Risk-free discount factors
            
        Returns:
            Lapse risk capital charge
        """
        # Calculate mass lapse impact
        mass_impact = self.calculate_mass_lapse_impact(
            lapse_data['policy_values'],
            lapse_data['surrender_values']
        )
        
        # Calculate trend stress impacts
        up_impact = self.calculate_trend_stress_impact(
            lapse_data['lapse_rates'],
            lapse_data['policy_cashflows'],
            lapse_data['discount_factors'],
            'up'
        )
        
        down_impact = self.calculate_trend_stress_impact(
            lapse_data['lapse_rates'],
            lapse_data['policy_cashflows'],
            lapse_data['discount_factors'],
            'down'
        )
        
        # Take maximum of trend stresses
        trend_impact = max(abs(up_impact), abs(down_impact))
        trend_type = "Up Stress" if abs(up_impact) > abs(down_impact) else "Down Stress"
        
        # Combine mass lapse and trend stress
        correlation_matrix = np.array([
            [1.0, 0.0],  # Mass lapse
            [0.0, 1.0]   # Trend stress
        ])
        
        charges = [abs(mass_impact), trend_impact]
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
                "Mass Lapse": RiskChargeResult(
                    risk_name="Mass Lapse",
                    gross_charge=abs(mass_impact),
                    net_charge=abs(mass_impact)
                ),
                trend_type: RiskChargeResult(
                    risk_name=trend_type,
                    gross_charge=trend_impact,
                    net_charge=trend_impact
                )
            }
        )
