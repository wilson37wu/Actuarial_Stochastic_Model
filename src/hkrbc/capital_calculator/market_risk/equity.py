"""
Equity risk capital calculation.
References Cap 41R Section 26.
"""

from dataclasses import dataclass
from typing import Dict, List
from ..base import RiskModule, RiskChargeResult

@dataclass
class EquityStressFactors:
    """Equity stress factors by type."""
    type_1: float = 0.39  # Type 1 equities: -39%
    type_2: float = 0.49  # Type 2 equities: -49%
    strategic: float = 0.22  # Strategic holdings: -22%

class EquityRiskModule(RiskModule):
    """
    Calculates capital charge for equity risk.
    Applies stress based on equity type and strategic nature.
    """
    
    def __init__(self):
        """Initialize equity risk module."""
        super().__init__("Equity Risk")
        self.stress_factors = EquityStressFactors()
        
    def calculate_risk_charge(
        self,
        equity_exposures: List[Dict[str, float]]
    ) -> RiskChargeResult:
        """
        Calculate equity risk charge.
        
        Args:
            equity_exposures: List of equity exposures with keys:
                - market_value: Market value of equity holding
                - type: Equity type ('type_1', 'type_2', 'strategic')
            
        Returns:
            Equity risk capital charge
        """
        sub_charges: Dict[str, float] = {
            'type_1': 0.0,
            'type_2': 0.0,
            'strategic': 0.0
        }
        
        # Calculate charges by type
        for exposure in equity_exposures:
            equity_type = exposure['type']
            market_value = exposure['market_value']
            
            if equity_type == 'type_1':
                stress = self.stress_factors.type_1
            elif equity_type == 'type_2':
                stress = self.stress_factors.type_2
            else:  # strategic
                stress = self.stress_factors.strategic
                
            sub_charges[equity_type] += market_value * stress
            
        # Create sub-risk results
        sub_risks = {
            name: RiskChargeResult(
                risk_name=f"{name.title()} Equities",
                gross_charge=charge,
                net_charge=charge
            )
            for name, charge in sub_charges.items()
        }
        
        # Calculate total charge with correlation
        # Correlation matrix from Cap 41R Schedule 1
        correlation_matrix = np.array([
            [1.0, 0.75, 0.0],  # Type 1
            [0.75, 1.0, 0.0],  # Type 2
            [0.0, 0.0, 1.0]    # Strategic
        ])
        
        charges_list = list(sub_charges.values())
        div_benefit = self.calculate_diversification_benefit(
            charges_list, correlation_matrix
        )
        
        total_charge = sum(charges_list)
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge - div_benefit,
            diversification_benefit=div_benefit,
            sub_risks=sub_risks
        )
