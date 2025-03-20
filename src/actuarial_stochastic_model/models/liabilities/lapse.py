"""
Lapse rate assumptions and calculations.
"""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

class LapseAssumption:
    """Lapse rates by policy duration and other factors."""
    
    @classmethod
    def from_csv(cls, filepath: str) -> 'LapseAssumption':
        """Load lapse rates from a CSV file."""
        df = pd.read_csv(filepath)
        return cls(df)
    
    def __init__(self, rates: pd.DataFrame):
        """Initialize with lapse rates."""
        self.rates = rates
        
    def get_rate(self, duration: int, product_type: str) -> float:
        """Get lapse rate for given policy duration and product type."""
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        # Default to a reasonable rate if not found
        return self.rates.get((duration, product_type), 0.05)
