"""
Base classes for HKRBC capital calculation components.
References:
- Cap 41R Part 5: Capital Requirements
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

@dataclass
class RiskChargeResult:
    """Result of a risk charge calculation."""
    risk_name: str
    gross_charge: float
    net_charge: float  # After management actions
    diversification_benefit: float = 0.0
    sub_risks: Optional[Dict[str, 'RiskChargeResult']] = None

class RiskModule(ABC):
    """
    Abstract base class for risk modules.
    Each risk module calculates capital charges for a specific risk type.
    """
    
    def __init__(self, name: str):
        """Initialize risk module."""
        self.name = name
        self._sub_modules: List[RiskModule] = []
        
    @abstractmethod
    def calculate_risk_charge(self) -> RiskChargeResult:
        """Calculate risk charge for this module."""
        pass
    
    def add_sub_module(self, module: 'RiskModule') -> None:
        """Add a sub-module to this risk module."""
        self._sub_modules.append(module)
        
    def calculate_diversification_benefit(
        self,
        charges: List[float],
        correlation_matrix: np.ndarray
    ) -> float:
        """
        Calculate diversification benefit using correlation matrix.
        
        Args:
            charges: List of risk charges
            correlation_matrix: Correlation matrix between risks
            
        Returns:
            Diversification benefit amount
        """
        charges_array = np.array(charges)
        total_undiversified = np.sum(charges_array)
        
        # Calculate diversified total using correlation matrix
        diversified_total = np.sqrt(
            charges_array.T @ correlation_matrix @ charges_array
        )
        
        return total_undiversified - diversified_total

class RiskAggregator:
    """
    Aggregates risk charges across modules using correlation matrices.
    References Cap 41R Schedule 1 for correlation assumptions.
    """
    
    def __init__(self):
        """Initialize risk aggregator."""
        self.modules: Dict[str, RiskModule] = {}
        
    def add_module(self, module: RiskModule) -> None:
        """Add a risk module to the aggregator."""
        self.modules[module.name] = module
        
    def calculate_total_capital_requirement(self) -> RiskChargeResult:
        """
        Calculate total capital requirement across all modules.
        
        Returns:
            Total capital requirement with diversification
        """
        # Calculate individual module charges
        module_charges = {
            name: module.calculate_risk_charge()
            for name, module in self.modules.items()
        }
        
        # TODO: Implement correlation matrix from Cap 41R Schedule 1
        correlation_matrix = np.eye(len(module_charges))  # Placeholder
        
        # Calculate diversification benefit
        charges_list = [charge.gross_charge for charge in module_charges.values()]
        div_benefit = self.modules[list(self.modules.keys())[0]].calculate_diversification_benefit(
            charges_list, correlation_matrix
        )
        
        return RiskChargeResult(
            risk_name="Total Capital Requirement",
            gross_charge=sum(charges_list),
            net_charge=sum(charges_list) - div_benefit,
            diversification_benefit=div_benefit,
            sub_risks=module_charges
        )
