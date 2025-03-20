"""
Credit spread risk capital calculation.
References Cap 41R Section 25.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from ..base import RiskModule, RiskChargeResult

@dataclass
class CreditSpreadFactors:
    """Credit spread risk factors by credit quality step."""
    duration_factor: float
    spread_factor: float
    recovery_rate: float = 0.5  # Default recovery rate

class CreditSpreadRiskModule(RiskModule):
    """
    Calculates capital charge for credit spread risk.
    Applies stress based on credit quality and duration.
    """
    
    def __init__(self):
        """Initialize credit spread risk module."""
        super().__init__("Credit Spread Risk")
        self._setup_risk_factors()
        
    def _setup_risk_factors(self):
        """
        Set up credit spread risk factors as per Cap 41R Section 25.
        """
        # Risk factors from Cap 41R Table 25
        self.risk_factors: Dict[int, CreditSpreadFactors] = {
            0: CreditSpreadFactors(  # AAA
                duration_factor=0.009,
                spread_factor=1.0
            ),
            1: CreditSpreadFactors(  # AA
                duration_factor=0.014,
                spread_factor=1.0
            ),
            2: CreditSpreadFactors(  # A
                duration_factor=0.019,
                spread_factor=1.0
            ),
            3: CreditSpreadFactors(  # BBB
                duration_factor=0.025,
                spread_factor=1.1
            ),
            4: CreditSpreadFactors(  # BB
                duration_factor=0.046,
                spread_factor=1.2
            ),
            5: CreditSpreadFactors(  # B
                duration_factor=0.063,
                spread_factor=1.3
            ),
            6: CreditSpreadFactors(  # CCC or lower
                duration_factor=0.083,
                spread_factor=1.5
            )
        }
        
    def calculate_bond_charge(
        self,
        market_value: float,
        duration: float,
        credit_quality: int
    ) -> float:
        """
        Calculate credit spread risk charge for a single bond.
        
        Args:
            market_value: Market value of the bond
            duration: Modified duration of the bond
            credit_quality: Credit quality step (0-6)
            
        Returns:
            Credit spread risk charge for the bond
        """
        if credit_quality not in self.risk_factors:
            raise ValueError(f"Invalid credit quality step: {credit_quality}")
            
        factors = self.risk_factors[credit_quality]
        
        # Calculate stress impact
        stress = factors.duration_factor * duration * factors.spread_factor
        return market_value * stress
        
    def calculate_risk_charge(
        self,
        bonds: List[Dict[str, float]]
    ) -> RiskChargeResult:
        """
        Calculate total credit spread risk charge.
        
        Args:
            bonds: List of bond dictionaries with keys:
                - market_value: Market value of the bond
                - duration: Modified duration
                - credit_quality: Credit quality step (0-6)
            
        Returns:
            Credit spread risk capital charge
        """
        sub_charges: Dict[str, RiskChargeResult] = {}
        total_charge = 0.0
        
        # Calculate charge for each bond
        for i, bond in enumerate(bonds):
            bond_charge = self.calculate_bond_charge(
                bond['market_value'],
                bond['duration'],
                bond['credit_quality']
            )
            
            sub_charges[f"Bond_{i}"] = RiskChargeResult(
                risk_name=f"Bond_{i}",
                gross_charge=bond_charge,
                net_charge=bond_charge
            )
            total_charge += bond_charge
            
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge,  # No management actions considered
            sub_risks=sub_charges
        )
