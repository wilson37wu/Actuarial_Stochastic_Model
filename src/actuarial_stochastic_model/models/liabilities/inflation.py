"""
Inflation rate assumptions and calculations.
"""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

class InflationAssumption:
    """Inflation rates by type and projection year."""
    
    @classmethod
    def from_csv(cls, filepath: str) -> 'InflationAssumption':
        """Load inflation rates from a CSV file."""
        df = pd.read_csv(filepath)
        return cls(df)
    
    def __init__(self, rates: pd.DataFrame):
        """Initialize with inflation rates."""
        self.rates = rates
        
    def get_rate(self, year: int, inflation_type: str = 'general') -> float:
        """Get inflation rate for given projection year and type."""
        if year < 0:
            raise ValueError("Year must be non-negative")
        
        # Default to reasonable rates if not found
        default_rates = {
            'general': 0.02,
            'medical': 0.04,
            'expense': 0.03
        }
        return self.rates.get((year, inflation_type), default_rates.get(inflation_type, 0.02))
