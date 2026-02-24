"""
Module for generating sample policy data for testing and demonstration.
"""
from datetime import date, timedelta
import random
from typing import List, Optional

import numpy as np
import pandas as pd

from ..enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy
)
from .products import TermInsurance, WholeLifeInsurance

class PolicyDataGenerator:
    """Generate sample policy data with realistic distributions."""
    
    def __init__(self, 
                 start_date: date = date(2020, 1, 1),
                 end_date: Optional[date] = None,
                 seed: Optional[int] = None):
        """Initialize the generator with date range and optional seed."""
        self.start_date = start_date
        self.end_date = end_date or date.today()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Configuration for realistic policy distributions
        self.age_mean = 40
        self.age_std = 15
        self.min_age = 18
        self.max_age = 70
        
        self.sum_assured_configs = {
            ProductType.TERM: {
                'mean': 250000,
                'std': 150000,
                'min': 50000,
                'max': 1000000
            },
            ProductType.WHOLE_LIFE: {
                'mean': 500000,
                'std': 300000,
                'min': 100000,
                'max': 2000000
            },
            ProductType.PARTICIPATING: {
                'mean': 750000,
                'std': 400000,
                'min': 150000,
                'max': 3000000
            }
        }
        
        # Premium rates as percentage of sum assured
        self.premium_rates = {
            ProductType.TERM: {
                'base': 0.003,
                'age_factor': 0.0002,
                'variation': 0.001
            },
            ProductType.WHOLE_LIFE: {
                'base': 0.015,
                'age_factor': 0.0005,
                'variation': 0.003
            },
            ProductType.PARTICIPATING: {
                'base': 0.02,
                'age_factor': 0.0007,
                'variation': 0.004
            }
        }
    
    def _generate_issue_date(self) -> date:
        """Generate a random issue date within the specified range."""
        days_range = (self.end_date - self.start_date).days
        random_days = random.randint(0, days_range)
        return self.start_date + timedelta(days=random_days)
    
    def _generate_issue_age(self) -> int:
        """Generate a random issue age with realistic distribution."""
        while True:
            age = int(round(np.random.normal(self.age_mean, self.age_std)))
            if self.min_age <= age <= self.max_age:
                return age
    
    def _generate_sum_assured(self, product_type: ProductType) -> float:
        """Generate sum assured based on product type."""
        config = self.sum_assured_configs[product_type]
        while True:
            amount = np.random.normal(config['mean'], config['std'])
            if config['min'] <= amount <= config['max']:
                return round(amount / 1000) * 1000  # Round to nearest thousand
    
    def _calculate_premium(self, 
                         product_type: ProductType,
                         sum_assured: float,
                         issue_age: int) -> float:
        """Calculate premium based on product type, sum assured, and age."""
        rates = self.premium_rates[product_type]
        base_rate = rates['base']
        age_component = rates['age_factor'] * issue_age
        variation = random.uniform(-rates['variation'], rates['variation'])
        total_rate = base_rate + age_component + variation
        annual_premium = sum_assured * total_rate
        return round(annual_premium / 100) * 100  # Round to nearest hundred
    
    def generate_term_insurance(self) -> TermInsurance:
        """Generate a term insurance policy with realistic parameters."""
        issue_date = self._generate_issue_date()
        issue_age = self._generate_issue_age()
        sum_assured = self._generate_sum_assured(ProductType.TERM)
        
        return TermInsurance(
            policy_number=f"T{random.randint(100000, 999999)}",
            issue_date=issue_date,
            term_years=random.choice([10, 15, 20, 25, 30]),
            sum_assured=sum_assured,
            premium=self._calculate_premium(ProductType.TERM, sum_assured, issue_age),
            sex=random.choice(list(Sex)),
            underwriting_class=random.choice(list(UnderwritingClass)),
            smoking_status=random.choice(list(SmokingStatus)),
            occupation_class=random.choice(list(OccupationClass))
        )
    
    def generate_whole_life_insurance(self, participating: bool = False) -> WholeLifeInsurance:
        """Generate a whole life insurance policy with realistic parameters."""
        issue_date = self._generate_issue_date()
        issue_age = self._generate_issue_age()
        product_type = ProductType.PARTICIPATING if participating else ProductType.WHOLE_LIFE
        sum_assured = self._generate_sum_assured(product_type)
        
        return WholeLifeInsurance(
            policy_number=f"{'P' if participating else 'W'}{random.randint(100000, 999999)}",
            issue_date=issue_date,
            sum_assured=sum_assured,
            premium=self._calculate_premium(product_type, sum_assured, issue_age),
            sex=random.choice(list(Sex)),
            underwriting_class=random.choice(list(UnderwritingClass)),
            smoking_status=random.choice(list(SmokingStatus)),
            occupation_class=random.choice(list(OccupationClass)),
            dividend_option=random.choice(list(DividendOption)) if participating else DividendOption.CASH,
            investment_strategy=random.choice(list(InvestmentStrategy))
        )
    
    def generate_policy_mix(self, 
                          num_policies: int,
                          term_ratio: float = 0.4,
                          whole_life_ratio: float = 0.3,
                          participating_ratio: float = 0.3) -> List[dict]:
        """Generate a mix of policies with specified ratios."""
        if not np.isclose(term_ratio + whole_life_ratio + participating_ratio, 1.0):
            raise ValueError("Policy ratios must sum to 1.0")
        
        num_term = int(num_policies * term_ratio)
        num_whole_life = int(num_policies * whole_life_ratio)
        num_participating = num_policies - num_term - num_whole_life
        
        policies = []
        
        # Generate term insurance policies
        for _ in range(num_term):
            policy = self.generate_term_insurance()
            policies.append(policy)
        
        # Generate whole life insurance policies
        for _ in range(num_whole_life):
            policy = self.generate_whole_life_insurance(participating=False)
            policies.append(policy)
        
        # Generate participating whole life policies
        for _ in range(num_participating):
            policy = self.generate_whole_life_insurance(participating=True)
            policies.append(policy)
        
        return policies
