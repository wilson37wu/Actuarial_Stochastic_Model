"""
Main risk aggregation module.
References:
- Cap 41R Schedule 1: Correlation matrices for risk aggregation
- DTT Implementation Guide Section 4: Risk aggregation methodology
"""

from typing import Dict
import numpy as np
from .base import RiskModule, RiskChargeResult
from .market_risk.aggregator import MarketRiskAggregator
from .insurance_risk.aggregator import InsuranceRiskAggregator
from .operational_risk import OperationalRiskModule

class MainRiskAggregator(RiskModule):
    """
    Main aggregator for all risk modules under HKRBC.
    Implements the correlation-based aggregation as specified in Cap 41R.
    """
    
    def __init__(self):
        """Initialize main risk aggregator with all major risk modules."""
        super().__init__("Total Capital Requirement")
        
        # Initialize major risk modules
        self.add_sub_module(MarketRiskAggregator())
        self.add_sub_module(InsuranceRiskAggregator())
        self.add_sub_module(OperationalRiskModule())
        
        # Correlation matrix from Cap 41R Schedule 1
        self.correlation_matrix = np.array([
            # MKT   INS   OPR
            [1.00, 0.25, 0.25],  # Market
            [0.25, 1.00, 0.25],  # Insurance
            [0.25, 0.25, 1.00]   # Operational
        ])
        
    def calculate_risk_charge(
        self,
        valuation_data: Dict[str, Dict]
    ) -> RiskChargeResult:
        """
        Calculate total capital requirement with diversification.
        
        Args:
            valuation_data: Dictionary containing data for each major risk:
                {
                    'market_risk': {...},
                    'insurance_risk': {...},
                    'operational_risk': {
                        'annual_premium': float,
                        'technical_provisions': float,
                        'unit_linked_expenses': float
                    }
                }
            
        Returns:
            Total capital requirement under HKRBC
        """
        # Calculate charges for each major risk module
        sub_charges: Dict[str, RiskChargeResult] = {}
        
        for module in self._sub_modules:
            module_data = valuation_data.get(
                module.name.lower().replace(' ', '_'),
                {}
            )
            
            if isinstance(module, OperationalRiskModule):
                sub_charges[module.name] = module.calculate_risk_charge(
                    **module_data
                )
            else:
                sub_charges[module.name] = module.calculate_risk_charge(
                    module_data
                )
            
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
