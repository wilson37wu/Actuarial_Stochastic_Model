"""
Currency risk capital calculation.
References Cap 41R Section 28.
"""

from typing import Dict, List
from ..base import RiskModule, RiskChargeResult

class CurrencyRiskModule(RiskModule):
    """
    Calculates capital charge for currency risk.
    Applies stress to net exposure in each foreign currency.
    """
    
    def __init__(self):
        """Initialize currency risk module."""
        super().__init__("Currency Risk")
        self.up_stress = 0.25    # +25% stress
        self.down_stress = 0.25  # -25% stress
        
    def calculate_risk_charge(
        self,
        currency_exposures: Dict[str, Dict[str, float]]
    ) -> RiskChargeResult:
        """
        Calculate currency risk charge.
        
        Args:
            currency_exposures: Dict of currency exposures:
                {currency_code: {
                    'assets': total_assets,
                    'liabilities': total_liabilities
                }}
            
        Returns:
            Currency risk capital charge
        """
        sub_charges: Dict[str, RiskChargeResult] = {}
        total_charge = 0.0
        
        # Calculate charge for each currency
        for currency, exposure in currency_exposures.items():
            net_exposure = exposure['assets'] - exposure['liabilities']
            
            # Apply stress in the more onerous direction
            up_impact = net_exposure * self.up_stress
            down_impact = net_exposure * self.down_stress
            
            charge = max(abs(up_impact), abs(down_impact))
            
            sub_charges[currency] = RiskChargeResult(
                risk_name=f"{currency} Exposure",
                gross_charge=charge,
                net_charge=charge,
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
            total_charge += charge
            
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge,  # No management actions considered
            sub_risks=sub_charges
        )
