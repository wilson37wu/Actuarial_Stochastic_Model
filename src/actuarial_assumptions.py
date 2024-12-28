"""
Module for actuarial assumptions.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.interpolate import interp1d

from .enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType
)

class ActuarialAssumptions:
    """Class to manage actuarial assumptions loaded from external files."""
    
    # Default values in case files are missing or corrupted
    DEFAULT_MORTALITY = {
        'male': {0: 0.00509, 20: 0.00095, 40: 0.00257, 60: 0.01843, 80: 0.11474},
        'female': {0: 0.00418, 20: 0.00037, 40: 0.00162, 60: 0.01046, 80: 0.06456}
    }
    
    DEFAULT_EXPENSES = {
        'acquisition_expense': 0.05,
        'maintenance_expense': 0.02,
        'investment_expense': 0.001,
        'claim_expense': 0.01
    }
    
    DEFAULT_INTEREST = {
        'risk_free_rate': 0.03,
        'credit_spread_aa': 0.01,
        'credit_spread_a': 0.02,
        'credit_spread_bbb': 0.03,
        'equity_risk_premium': 0.06,
        'real_estate_risk_premium': 0.04,
        'liquidity_premium': 0.005,
        'inflation_rate': 0.02
    }
    
    DEFAULT_LAPSE = {
        1: {'base': 0.15, 'shock_up': 0.30, 'shock_down': 0.075},
        5: {'base': 0.07, 'shock_up': 0.14, 'shock_down': 0.035},
        10: {'base': 0.03, 'shock_up': 0.06, 'shock_down': 0.015}
    }

    def __init__(self, assumption_dir=None):
        """Initialize assumptions from external files or defaults."""
        if assumption_dir is None:
            assumption_dir = Path(__file__).parent.parent / 'assumptions'
        self.assumption_dir = Path(assumption_dir)
        
        # Load assumptions
        self._load_mortality_rates()
        self._load_expense_rates()
        self._load_interest_rates()
        self._load_lapse_rates()

    def _load_mortality_rates(self):
        """Load mortality rates from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'mortality_rates.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.mortality_rates = {
                    'male': dict(zip(df['age'], df['male_rate'])),
                    'female': dict(zip(df['age'], df['female_rate']))
                }
            else:
                self.mortality_rates = self.DEFAULT_MORTALITY
        except Exception as e:
            print(f"Error loading mortality rates: {e}")
            self.mortality_rates = self.DEFAULT_MORTALITY

    def _load_expense_rates(self):
        """Load expense rates from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'expense_rates.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.expense_rates = dict(zip(df['expense_type'], df['rate']))
            else:
                self.expense_rates = self.DEFAULT_EXPENSES
        except Exception as e:
            print(f"Error loading expense rates: {e}")
            self.expense_rates = self.DEFAULT_EXPENSES

    def _load_interest_rates(self):
        """Load interest rates from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'interest_rates.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.interest_rates = dict(zip(df['rate_type'], df['value']))
            else:
                self.interest_rates = self.DEFAULT_INTEREST
        except Exception as e:
            print(f"Error loading interest rates: {e}")
            self.interest_rates = self.DEFAULT_INTEREST

    def _load_lapse_rates(self):
        """Load lapse rates from CSV file or use defaults."""
        try:
            file_path = self.assumption_dir / 'lapse_rates.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.lapse_rates = {}
                for _, row in df.iterrows():
                    year = row['policy_year']
                    if year == '10+':
                        year = 10
                    self.lapse_rates[int(year)] = {
                        'base': row['base_rate'],
                        'shock_up': row['shock_up'],
                        'shock_down': row['shock_down']
                    }
            else:
                self.lapse_rates = self.DEFAULT_LAPSE
        except Exception as e:
            print(f"Error loading lapse rates: {e}")
            self.lapse_rates = self.DEFAULT_LAPSE

    def get_mortality_rate(self, age, sex='M'):
        """Get mortality rate for given age and sex."""
        sex_key = 'male' if sex.upper() == 'M' else 'female'
        rates = self.mortality_rates[sex_key]
        
        # Find closest age if exact age not in table
        available_ages = sorted(rates.keys())
        if age in rates:
            return rates[age]
        elif age < min(available_ages):
            return rates[min(available_ages)]
        elif age > max(available_ages):
            return rates[max(available_ages)]
        else:
            # Linear interpolation
            lower_age = max(x for x in available_ages if x < age)
            upper_age = min(x for x in available_ages if x > age)
            rate_diff = rates[upper_age] - rates[lower_age]
            age_diff = upper_age - lower_age
            return rates[lower_age] + rate_diff * (age - lower_age) / age_diff

    def get_expense_rate(self, expense_type):
        """Get expense rate for given type."""
        return self.expense_rates.get(expense_type, 0.0)

    def get_interest_rate(self, rate_type):
        """Get interest rate for given type."""
        return self.interest_rates.get(rate_type, 0.0)

    def get_lapse_rate(self, policy_year, scenario='base'):
        """Get lapse rate for given policy year and scenario."""
        if policy_year >= 10:
            policy_year = 10
            
        # Find closest year if exact year not in table
        available_years = sorted(self.lapse_rates.keys())
        if policy_year in self.lapse_rates:
            return self.lapse_rates[policy_year][scenario]
        else:
            # Linear interpolation
            lower_year = max(x for x in available_years if x < policy_year)
            upper_year = min(x for x in available_years if x > policy_year)
            rate_diff = (self.lapse_rates[upper_year][scenario] - 
                        self.lapse_rates[lower_year][scenario])
            year_diff = upper_year - lower_year
            return (self.lapse_rates[lower_year][scenario] + 
                   rate_diff * (policy_year - lower_year) / year_diff)

    def export_assumptions(self, output_dir=None):
        """Export current assumptions to CSV files."""
        if output_dir is None:
            output_dir = self.assumption_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export mortality rates
        mortality_data = []
        ages = sorted(set(list(self.mortality_rates['male'].keys()) + 
                        list(self.mortality_rates['female'].keys())))
        for age in ages:
            mortality_data.append({
                'age': age,
                'male_rate': self.mortality_rates['male'].get(age, np.nan),
                'female_rate': self.mortality_rates['female'].get(age, np.nan)
            })
        pd.DataFrame(mortality_data).to_csv(
            output_dir / 'mortality_rates.csv', index=False)

        # Export expense rates
        expense_data = [
            {'expense_type': k, 'rate': v, 'unit': 'per_premium'}
            for k, v in self.expense_rates.items()
        ]
        pd.DataFrame(expense_data).to_csv(
            output_dir / 'expense_rates.csv', index=False)

        # Export interest rates
        interest_data = [
            {'rate_type': k, 'value': v, 'duration': 1}
            for k, v in self.interest_rates.items()
        ]
        pd.DataFrame(interest_data).to_csv(
            output_dir / 'interest_rates.csv', index=False)

        # Export lapse rates
        lapse_data = [
            {
                'policy_year': '10+' if k == 10 else k,
                'base_rate': v['base'],
                'shock_up': v['shock_up'],
                'shock_down': v['shock_down']
            }
            for k, v in self.lapse_rates.items()
        ]
        pd.DataFrame(lapse_data).to_csv(
            output_dir / 'lapse_rates.csv', index=False)

class MortalityTable:
    """Mortality table with rates by age and characteristics."""
    
    def __init__(self, base_rates: Dict[int, float], assumptions: ActuarialAssumptions):
        """Initialize mortality table."""
        self.base_rates = base_rates
        self.assumptions = assumptions
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
    
    def set_multiplier(self, multiplier: float) -> None:
        """Set a multiplier for all mortality rates.
        
        Args:
            multiplier: Factor to multiply all rates by
        """
        # Store original rates if not already stored
        if not hasattr(self, '_original_rates'):
            self._original_rates = self.base_rates.copy()
        
        # Apply multiplier to original rates
        self.base_rates = {
            age: rate * multiplier
            for age, rate in self._original_rates.items()
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
    
    def __init__(self, base_rates: Dict[int, float], assumptions: ActuarialAssumptions):
        """Initialize lapse assumption."""
        self.base_rates = base_rates
        self.assumptions = assumptions
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

    def set_base_rate(self, rate: float) -> None:
        """Set a uniform base lapse rate for all durations.
        
        Args:
            rate: New base lapse rate to use
        """
        # Store original rates if not already stored
        if not hasattr(self, '_original_rates'):
            self._original_rates = self.base_rates.copy()
            
        # Set uniform rate for all durations
        self.base_rates = {
            duration: rate
            for duration in self._original_rates.keys()
        }
        
        # Recreate interpolator with new rates
        self._create_interpolator()

class InflationAssumption:
    """Inflation rate assumptions."""
    
    def __init__(self,
                 base_rate: float,
                 wage_inflation: Optional[float] = None,
                 medical_inflation: Optional[float] = None,
                 assumptions: ActuarialAssumptions = None):
        """Initialize inflation assumption."""
        self.base_rate = base_rate
        self.wage_inflation = wage_inflation or base_rate * 1.5
        self.medical_inflation = medical_inflation or base_rate * 2.0
        self.assumptions = assumptions
    
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

    def set_rate(self, rate: float) -> None:
        """Set base inflation rate and adjust related rates.
        
        Args:
            rate: New base inflation rate
        """
        # Store original rates if not already stored
        if not hasattr(self, '_original_rates'):
            self._original_rates = {
                'base': self.base_rate,
                'wage': self.wage_inflation,
                'medical': self.medical_inflation
            }
            
        # Update base rate
        self.base_rate = rate
        
        # Maintain relative relationships for wage and medical inflation
        if self._original_rates['base'] > 0:
            wage_ratio = self._original_rates['wage'] / self._original_rates['base']
            medical_ratio = self._original_rates['medical'] / self._original_rates['base']
        else:
            wage_ratio = 1.5  # Default wage inflation is 1.5x base
            medical_ratio = 2.0  # Default medical inflation is 2x base
            
        # Update related rates
        self.wage_inflation = rate * wage_ratio
        self.medical_inflation = rate * medical_ratio

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

def create_sample_mortality_table(assumptions: ActuarialAssumptions) -> MortalityTable:
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
        base_rates=ultimate_rates,
        assumptions=assumptions
    )

def create_sample_lapse_assumption(assumptions: ActuarialAssumptions) -> LapseAssumption:
    """Create sample lapse assumptions."""
    return LapseAssumption(
        base_rates={
            1: 0.05,  # 5% lapse rate in first year
            2: 0.04,  # 4% lapse rate in second year
            3: 0.03,  # 3% lapse rate in third year
            4: 0.02,  # 2% lapse rate in fourth year
            5: 0.01,  # 1% lapse rate in fifth year
        },
        assumptions=assumptions
    )

def create_sample_inflation_assumption(assumptions: ActuarialAssumptions) -> InflationAssumption:
    """Create sample inflation assumptions."""
    return InflationAssumption(
        base_rate=0.02,  # 2% base inflation
        wage_inflation=0.03,  # 3% wage inflation
        medical_inflation=0.04,  # 4% medical inflation
        assumptions=assumptions
    )
