"""
Interest rate risk capital calculation.
References Cap 41R Section 24.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from ..base import RiskModule, RiskChargeResult

@dataclass
class InterestRateStress:
    """Interest rate stress parameters."""
    up_stress: List[Tuple[int, float]]  # (term, stress_factor) pairs
    down_stress: List[Tuple[int, float]]  # (term, stress_factor) pairs

class InterestRateRiskModule(RiskModule):
    """
    Calculates capital charge for interest rate risk.
    Applies stress to the risk-free interest rate term structure.
    """
    
    def __init__(self):
        """Initialize interest rate risk module."""
        super().__init__("Interest Rate Risk")
        self._setup_stress_factors()
        
    def _setup_stress_factors(self):
        """
        Set up interest rate stress factors as per Cap 41R Section 24.
        """
        # Stress factors from Cap 41R Table 24
        self.stress = InterestRateStress(
            up_stress=[
                (1, 0.70),   # 1 year: +70%
                (2, 0.70),   # 2 years: +70%
                (5, 0.65),   # 5 years: +65%
                (10, 0.60),  # 10 years: +60%
                (20, 0.55),  # 20 years: +55%
                (30, 0.50)   # 30+ years: +50%
            ],
            down_stress=[
                (1, -0.75),   # 1 year: -75%
                (2, -0.65),   # 2 years: -65%
                (5, -0.56),   # 5 years: -56%
                (10, -0.50),  # 10 years: -50%
                (20, -0.45),  # 20 years: -45%
                (30, -0.40)   # 30+ years: -40%
            ]
        )
        
    def _interpolate_stress(
        self,
        term: float,
        stress_points: List[Tuple[int, float]]
    ) -> float:
        """
        Interpolate stress factor for a given term.
        
        Args:
            term: Term in years
            stress_points: List of (term, stress) pairs
            
        Returns:
            Interpolated stress factor
        """
        # Handle terms beyond last point
        if term >= stress_points[-1][0]:
            return stress_points[-1][1]
            
        # Find surrounding points
        for i in range(len(stress_points) - 1):
            t1, s1 = stress_points[i]
            t2, s2 = stress_points[i + 1]
            
            if t1 <= term <= t2:
                # Linear interpolation
                return s1 + (s2 - s1) * (term - t1) / (t2 - t1)
                
        return stress_points[0][1]  # For terms below first point
        
    def calculate_stressed_rates(
        self,
        terms: np.ndarray,
        rates: np.ndarray,
        stress_type: str
    ) -> np.ndarray:
        """
        Calculate stressed interest rates.
        
        Args:
            terms: Array of terms in years
            rates: Array of risk-free rates
            stress_type: Either 'up' or 'down'
            
        Returns:
            Array of stressed rates
        """
        stress_points = (
            self.stress.up_stress if stress_type == 'up'
            else self.stress.down_stress
        )
        
        stressed_rates = np.zeros_like(rates)
        for i, (term, rate) in enumerate(zip(terms, rates)):
            stress = self._interpolate_stress(term, stress_points)
            absolute_change = rate * stress
            stressed_rates[i] = max(rate + absolute_change, 0.0)
            
        return stressed_rates
        
    def calculate_risk_charge(
        self,
        terms: np.ndarray,
        rates: np.ndarray,
        asset_values: Dict[str, float],
        liability_values: Dict[str, float]
    ) -> RiskChargeResult:
        """
        Calculate interest rate risk charge.
        
        Args:
            terms: Array of terms in years
            rates: Array of risk-free rates
            asset_values: Dict of asset values by type
            liability_values: Dict of liability values by type
            
        Returns:
            Interest rate risk capital charge
        """
        # Calculate stressed rates
        up_rates = self.calculate_stressed_rates(terms, rates, 'up')
        down_rates = self.calculate_stressed_rates(terms, rates, 'down')
        
        # TODO: Calculate impact on assets and liabilities
        # This requires integration with asset and liability valuation modules
        
        # Placeholder calculation
        up_impact = 0.0
        down_impact = 0.0
        
        # Take the larger impact
        gross_charge = max(abs(up_impact), abs(down_impact))
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=gross_charge,
            net_charge=gross_charge,  # TODO: Consider management actions
            sub_risks={
                "Up Stress": RiskChargeResult(
                    risk_name="Up Stress",
                    gross_charge=abs(up_impact),
                    net_charge=abs(up_impact)
                ),
                "Down Stress": RiskChargeResult(
                    risk_name="Down Stress",
                    gross_charge=abs(down_impact),
                    net_charge=abs(down_impact)
                )
            }
        )
