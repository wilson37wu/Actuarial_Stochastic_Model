"""
Module for actuarial assumptions.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from ...enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType
)

@dataclass
class MortalityTable:
    """Mortality table with rates by age and characteristics."""

    def __init__(self, base_rates: Dict[int, float]):
        """Initialize mortality table."""
        self.base_rates = base_rates
        self._create_interpolator()

        # Adjustment factors
        self.sex_factors = {
            Sex.MALE: 1.0,
            Sex.FEMALE: 0.8
        }

        self.smoking_factors = {
            SmokingStatus.NON_SMOKER: 1.0,
            SmokingStatus.SMOKER: 2.0
        }

        self.occupation_factors = {
            OccupationClass.PROFESSIONAL: 0.9,
            OccupationClass.TECHNICAL: 1.0,
            OccupationClass.MANUAL: 1.2
        }

        self.underwriting_factors = {
            UnderwritingClass.PREFERRED: 0.8,
            UnderwritingClass.STANDARD: 1.0,
            UnderwritingClass.SUBSTANDARD: 1.5
        }

    def _create_interpolator(self):
        """Create interpolation function for rates."""
        ages = sorted(self.base_rates.keys())
        rates = [self.base_rates[age] for age in ages]
        self._interpolator = interp1d(
            ages, rates, kind='linear',
            bounds_error=False, fill_value=(rates[0], rates[-1])
        )

    def get_rate(self,
                 age: int,
                 sex: Sex = Sex.MALE,
                 smoking_status: Optional[SmokingStatus] = None,
                 occupation_class: Optional[OccupationClass] = None,
                 underwriting_class: Optional[UnderwritingClass] = None
                 ) -> float:
        """Get mortality rate for given characteristics."""
        base_rate = float(self._interpolator(age))

        # Apply adjustment factors
        rate = base_rate * self.sex_factors[sex]

        if smoking_status:
            rate *= self.smoking_factors[smoking_status]

        if occupation_class:
            rate *= self.occupation_factors[occupation_class]

        if underwriting_class:
            rate *= self.underwriting_factors[underwriting_class]

        return rate

    @classmethod
    def from_csv(cls, filepath: str) -> 'MortalityTable':
        """Create mortality table from CSV file."""
        df = pd.read_csv(filepath)
        base_rates = dict(zip(df['Age'], df['Base_Rate']))
        return cls(base_rates)

@dataclass
class LapseAssumption:
    """Lapse rate assumptions."""

    def __init__(self, base_rates: Dict[int, float]):
        """Initialize lapse assumption."""
        self.base_rates = base_rates
        self._create_interpolator()

        # Product type factors
        self.product_factors = {
            ProductType.TERM: 1.2,
            ProductType.WHOLE_LIFE: 0.8,
            ProductType.PARTICIPATING: 0.7,
            ProductType.UNIVERSAL_LIFE: 1.0,
            ProductType.UNIT_LINKED: 1.1
        }

        # Dynamic lapse factors
        self.dynamic_factors = {
            1: 2.0,  # High sensitivity in early years
            5: 1.5,  # Moderate sensitivity in middle years
            10: 1.2  # Lower sensitivity in later years
        }

    def _create_interpolator(self):
        """Create interpolation function for rates."""
        years = sorted(self.base_rates.keys())
        rates = [self.base_rates[year] for year in years]
        self._interpolator = interp1d(
            years, rates, kind='linear',
            bounds_error=False, fill_value=(rates[0], rates[-1])
        )

    def get_rate(self,
                 duration: int,
                 product_type: Optional[ProductType] = None) -> float:
        """Get lapse rate for given duration and product type."""
        base_rate = float(self._interpolator(duration))

        if product_type:
            base_rate *= self.product_factors[product_type]

        return base_rate

    def get_dynamic_factor(self, duration: int) -> float:
        """Get dynamic lapse factor for given duration."""
        years = sorted(self.dynamic_factors.keys())
        if duration >= max(years):
            return self.dynamic_factors[max(years)]
        elif duration <= min(years):
            return self.dynamic_factors[min(years)]
        else:
            # Linear interpolation
            lower_year = max(y for y in years if y < duration)
            upper_year = min(y for y in years if y > duration)
            factor_diff = self.dynamic_factors[upper_year] - self.dynamic_factors[lower_year]
            year_diff = upper_year - lower_year
            return (self.dynamic_factors[lower_year] +
                    factor_diff * (duration - lower_year) / year_diff)

    @classmethod
    def from_csv(cls, filepath: str) -> 'LapseAssumption':
        """Create lapse assumption from CSV file."""
        df = pd.read_csv(filepath)
        base_rates = dict(zip(df['Policy_Year'], df['Base_Rate']))
        return cls(base_rates)

@dataclass
class InflationAssumption:
    """Inflation rate assumptions."""

    def __init__(self,
                 base_rate: float,
                 wage_inflation: Optional[float] = None,
                 medical_inflation: Optional[float] = None):
        """Initialize inflation assumption."""
        self.base_rate = base_rate
        self.wage_inflation = wage_inflation or base_rate * 1.5
        self.medical_inflation = medical_inflation or base_rate * 2.0

    def get_rate(self,
                 projection_date: date,
                 is_wage: bool = False,
                 is_medical: bool = False) -> float:
        """Get inflation rate for given date and type."""
        if is_medical:
            return self.medical_inflation
        elif is_wage:
            return self.wage_inflation
        else:
            return self.base_rate

    def get_inflation_factor(self,
                             start_date: date,
                             end_date: date,
                             is_wage: bool = False,
                             is_medical: bool = False) -> float:
        """Get cumulative inflation factor between dates."""
        years = (end_date - start_date).days / 365.25
        rate = self.get_rate(end_date, is_wage, is_medical)
        return (1 + rate) ** years

    @classmethod
    def from_csv(cls, filepath: str) -> 'InflationAssumption':
        """Create inflation assumption from CSV file."""
        df = pd.read_csv(filepath)
        base_rate = float(df.loc[df['Type'] == 'Base', 'Rate'].iloc[0])
        wage_rate = float(df.loc[df['Type'] == 'Wage', 'Rate'].iloc[0])
        medical_rate = float(df.loc[df['Type'] == 'Medical', 'Rate'].iloc[0])
        return cls(base_rate, wage_rate, medical_rate)
