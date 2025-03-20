"""
Mortality table and related calculations.
"""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

class MortalityTable:
    """Mortality rates by age and other factors."""
    
    @classmethod
    def from_csv(cls, filepath: str) -> 'MortalityTable':
        """Load mortality rates from a CSV file."""
        df = pd.read_csv(filepath)
        return cls(df)
    
    def __init__(self, rates: pd.DataFrame):
        """Initialize with mortality rates."""
        self.rates = rates
        
    def get_rate(self, age: int, sex: str) -> float:
        """Get mortality rate for given age and sex."""
        if age < 0 or age > 120:
            raise ValueError("Age must be between 0 and 120")
        
        # Default to a reasonable rate if not found
        return self.rates.get((age, sex), 0.001)
