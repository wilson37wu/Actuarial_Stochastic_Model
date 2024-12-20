"""
Module for actuarial assumptions.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.interpolate import interp1d

from .enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType
)

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
        
        # Add endpoints if needed
        if min(ages) > 0:
            ages = [0] + ages
            rates = [rates[0]] + rates
        if max(ages) < 100:
            ages = ages + [100]
            rates = rates + [1.0]  # 100% mortality at age 100
        
        self.interpolator = interp1d(
            ages, rates, kind='linear',
            bounds_error=False, fill_value=(rates[0], rates[-1])
        )
    
    def apply_multiplier(self, multiplier: float) -> None:
        """Apply a multiplier to all mortality rates.
        
        Args:
            multiplier: Factor to multiply all rates by
        """
        if multiplier <= 0:
            raise ValueError("Mortality multiplier must be positive")
        
        # Apply multiplier to base rates
        self.base_rates = {
            age: rate * multiplier
            for age, rate in self.base_rates.items()
        }
        
        # Recreate interpolator with new rates
        self._create_interpolator()
    
    def get_rate(self,
                 age: int,
                 sex: Sex,
                 smoking_status: SmokingStatus,
                 occupation_class: Optional[OccupationClass] = None,
                 underwriting_class: Optional[UnderwritingClass] = None
                 ) -> float:
        """Get mortality rate for given characteristics."""
        base_rate = float(self.interpolator(age))
        
        # Apply adjustment factors
        rate = base_rate
        rate *= self.sex_factors[sex]
        rate *= self.smoking_factors[smoking_status]
        
        if occupation_class:
            rate *= self.occupation_factors[occupation_class]
        if underwriting_class:
            rate *= self.underwriting_factors[underwriting_class]
        
        return min(1.0, rate)  # Cap at 100%

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
            ProductType.PAR_WHOLE_LIFE: 0.7,
            ProductType.UNIVERSAL_LIFE: 1.0,
            ProductType.UNIT_LINKED: 1.1
        }
    
    def _create_interpolator(self):
        """Create interpolation function for rates."""
        durations = sorted(self.base_rates.keys())
        rates = [self.base_rates[dur] for dur in durations]
        
        # Add endpoints if needed
        if min(durations) > 0:
            durations = [0] + durations
            rates = [rates[0]] + rates
        if max(durations) < 30:
            durations = durations + [30]
            rates = rates + [rates[-1]]
        
        self.interpolator = interp1d(
            durations, rates, kind='linear',
            bounds_error=False, fill_value=(rates[0], rates[-1])
        )
    
    def get_rate(self,
                 duration: int,
                 product_type: Optional[ProductType] = None) -> float:
        """Get lapse rate for given duration and product type."""
        base_rate = float(self.interpolator(duration))
        
        if product_type:
            base_rate *= self.product_factors[product_type]
        
        return min(1.0, base_rate)  # Cap at 100%

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
                 projection_year: int,
                 is_wage: bool = False,
                 is_medical: bool = False) -> float:
        """Get inflation rate for given year and type."""
        if is_medical:
            return self.medical_inflation
        elif is_wage:
            return self.wage_inflation
        else:
            return self.base_rate
    
    def get_inflation_factor(self,
                           projection_year: int,
                           is_wage: bool = False,
                           is_medical: bool = False) -> float:
        """Get cumulative inflation factor."""
        rate = self.get_rate(
            projection_year,
            is_wage=is_wage,
            is_medical=is_medical
        )
        return (1 + rate) ** projection_year

@dataclass
class MortalityImprovement:
    """Represents mortality improvement assumptions."""
    base_year: int
    annual_improvement: Dict[Tuple[int, int], float]  # (start_age, end_age): improvement rate
    
    def get_improvement_factor(self, age: int, projection_year: int) -> float:
        """Get cumulative mortality improvement factor."""
        # Find the applicable improvement rate for the age
        rate = 0.0
        for (start_age, end_age), improvement_rate in self.annual_improvement.items():
            if start_age <= age <= end_age:
                rate = improvement_rate
                break
        
        # Calculate cumulative improvement
        years_from_base = projection_year - self.base_year
        if years_from_base <= 0:
            return 1.0
        
        return (1 - rate) ** years_from_base

@dataclass
class SelectAndUltimateRates:
    """Represents select and ultimate mortality rates."""
    select_period: int  # Number of select years
    select_rates: Dict[Tuple[int, int], float]  # (issue_age, duration): rate
    ultimate_rates: Dict[int, float]  # age: rate
    
    def get_rate(self, issue_age: int, duration: int) -> float:
        """Get appropriate rate based on issue age and duration."""
        if duration < self.select_period:
            # Use select rate if available
            return self.select_rates.get(
                (issue_age, duration),
                self.ultimate_rates.get(issue_age + duration, 1.0)
            )
        # Use ultimate rate
        return self.ultimate_rates.get(issue_age + duration, 1.0)

@dataclass
class MortalityFactors:
    """Represents adjustment factors for mortality rates."""
    sex_factor: float  # Relative to male baseline
    uw_class_factor: float  # Relative to standard class
    smoking_factor: float  # Relative to never smoker
    occupation_factor: float  # Relative to Class 1
    
    @classmethod
    def get_sex_factor(cls, sex: Sex) -> float:
        """Get mortality factor for given sex."""
        sex_factors = {
            Sex.MALE: 1.0,
            Sex.FEMALE: 0.7,  # Females generally have lower mortality
        }
        return sex_factors[sex]
    
    @classmethod
    def get_uw_class_factor(cls, uw_class: UnderwritingClass) -> float:
        """Get mortality factor for given underwriting class."""
        uw_factors = {
            UnderwritingClass.PREFERRED: 0.5,   # 50% of standard
            UnderwritingClass.STANDARD: 1.0,         # Baseline
            UnderwritingClass.SUBSTANDARD: 1.5,    # +50%
        }
        return uw_factors[uw_class]
    
    @classmethod
    def get_smoking_factor(cls, smoking_status: SmokingStatus) -> float:
        """Get mortality factor for given smoking status."""
        smoking_factors = {
            SmokingStatus.NON_SMOKER: 1.0,    # Baseline
            SmokingStatus.SMOKER: 2.5,  # 150% higher than never smoker
        }
        return smoking_factors[smoking_status]
    
    @classmethod
    def get_occupation_factor(cls, occupation_class: OccupationClass) -> float:
        """Get mortality factor for given occupation class."""
        occupation_factors = {
            OccupationClass.PROFESSIONAL: 0.9,   # 10% lower
            OccupationClass.TECHNICAL: 1.0,   # Baseline
            OccupationClass.MANUAL: 1.2,   # 20% higher
        }
        return occupation_factors[occupation_class]

def create_sample_mortality_table() -> MortalityTable:
    """Create a sample mortality table with select and ultimate rates."""
    start_age = 20
    max_age = 100  # Maximum age in the table
    
    # Create ultimate rates using Gompertz-Makeham formula
    ultimate_rates = {}
    for age in range(start_age, max_age + 1):
        A = 0.0001  # Base mortality
        B = 0.00035  # Initial mortality rate
        C = 1.098    # Mortality increase rate (9.8% per year)
        x0 = start_age
        qx = A + B * (C ** (age - x0))
        ultimate_rates[age] = min(qx, 1.0)
    
    # Create select rates (lower mortality in early durations)
    select_rates = {}
    select_period = 5
    for issue_age in range(start_age, max_age - select_period + 1):
        for duration in range(select_period):
            # Select mortality is lower than ultimate, gradually approaching ultimate
            attained_age = min(issue_age + duration, max_age)
            ultimate_qx = ultimate_rates[attained_age]
            select_factor = 0.6 + (0.4 * duration / select_period)  # 60% to 100% of ultimate
            select_rates[(issue_age, duration)] = ultimate_qx * select_factor
    
    # Create mortality improvement assumptions
    improvement = MortalityImprovement(
        base_year=2024,
        annual_improvement={
            (20, 45): 0.02,   # 2% annual improvement for ages 20-45
            (46, 65): 0.015,  # 1.5% for ages 46-65
            (66, 85): 0.01,   # 1% for ages 66-85
            (86, 100): 0.005  # 0.5% for ages 86+
        }
    )
    
    return MortalityTable(
        base_rates=ultimate_rates
    )

def create_sample_lapse_assumption() -> LapseAssumption:
    """Create sample lapse assumptions."""
    return LapseAssumption(
        base_rates={
            1: 0.05,  # 5% lapse rate in first year
            2: 0.04,  # 4% lapse rate in second year
            3: 0.03,  # 3% lapse rate in third year
            4: 0.02,  # 2% lapse rate in fourth year
            5: 0.01,  # 1% lapse rate in fifth year
        }
    )

def create_sample_inflation_assumption() -> InflationAssumption:
    """Create sample inflation assumptions."""
    return InflationAssumption(
        base_rate=0.02,  # 2% base inflation
        wage_inflation=0.03,  # 3% wage inflation
        medical_inflation=0.04  # 4% medical inflation
    )
