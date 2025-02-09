import numpy as np
from typing import Dict, List

class ActuarialCalculations:
    """Centralized actuarial calculation engine"""

    @staticmethod
    def calculate_mortality_rates(age: int, sex: str, mortality_table: Dict[int, float]) -> float:
        """Get mortality rate with age adjustment"""
        base_rate = mortality_table.get(age, 0.0)
        return base_rate * 1.1 if sex == 'male' else base_rate * 0.9

    @staticmethod
    def calculate_lapse_rates(duration: int, product_type: str, lapse_assumptions: Dict) -> float:
        """Calculate dynamic lapse rates"""
        base_rate = lapse_assumptions.get('base_rates', {}).get(duration, 0.05)
        product_factor = lapse_assumptions.get('product_factors', {}).get(product_type, 1.0)
        return base_rate * product_factor

    @staticmethod
    def calculate_expenses(annual_premium: float, policy_duration: int, expense_factors: Dict) -> float:
        """Calculate expense allocation"""
        fixed = expense_factors.get('fixed', 50.0)
        variable = annual_premium * expense_factors.get('variable_rate', 0.02)
        return fixed + variable * (1 - 0.95 ** policy_duration)
