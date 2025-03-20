"""
Operational risk capital calculation module.
References:
- Cap 41R Part 5, Division 6: Operational Risk
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
from .base import RiskModule, RiskChargeResult

@dataclass
class OperationalRiskFactors:
    """
    Operational risk factors as defined in Cap 41R Section 32.
    """
    premium_factor: float = 0.04  # 4% of premium
    technical_provision_factor: float = 0.0045  # 0.45% of technical provisions
    expense_factor: float = 0.25  # 25% of expenses for unit-linked business

class OperationalRiskModule(RiskModule):
    """
    Calculates capital charge for operational risk.
    References Cap 41R Section 32.
    """
    
    def __init__(self):
        """Initialize operational risk module."""
        super().__init__("Operational Risk")
        self.factors = OperationalRiskFactors()
        
    def calculate_risk_charge(
        self,
        annual_premium: float,
        technical_provisions: float,
        unit_linked_expenses: float = 0.0
    ) -> RiskChargeResult:
        """
        Calculate operational risk charge based on business volume metrics.
        
        Args:
            annual_premium: Annual premium income
            technical_provisions: Total technical provisions
            unit_linked_expenses: Annual expenses for unit-linked business
            
        Returns:
            Operational risk capital charge
        """
        # Calculate component charges
        premium_charge = annual_premium * self.factors.premium_factor
        provision_charge = technical_provisions * self.factors.technical_provision_factor
        expense_charge = unit_linked_expenses * self.factors.expense_factor
        
        # Take maximum of premium and provision based charge
        base_charge = max(premium_charge, provision_charge)
        
        # Add unit-linked expense charge
        total_charge = base_charge + expense_charge
        
        return RiskChargeResult(
            risk_name=self.name,
            gross_charge=total_charge,
            net_charge=total_charge,  # No management actions considered
            sub_risks={
                "Premium Based": RiskChargeResult(
                    risk_name="Premium Based",
                    gross_charge=premium_charge,
                    net_charge=premium_charge
                ),
                "Technical Provision Based": RiskChargeResult(
                    risk_name="Technical Provision Based",
                    gross_charge=provision_charge,
                    net_charge=provision_charge
                ),
                "Unit-Linked Expense Based": RiskChargeResult(
                    risk_name="Unit-Linked Expense Based",
                    gross_charge=expense_charge,
                    net_charge=expense_charge
                )
            }
        )
