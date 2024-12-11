import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date

@dataclass
class Bond:
    """Represents a fixed income security."""
    id: str
    par_value: float
    coupon_rate: float
    maturity_date: date
    payment_frequency: int  # payments per year
    credit_rating: str
    issue_date: date
    purchase_price: float
    currency: str = 'USD'
    
class FixedIncomeModel:
    """Fixed Income cash flow projection model."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.credit_transition_matrix = self._load_credit_transition_matrix()
        self.default_recovery_rates = self._load_recovery_rates()
        
    def _load_credit_transition_matrix(self) -> pd.DataFrame:
        """Load credit rating transition matrix."""
        # Example transition matrix (should be loaded from config in practice)
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
        matrix = np.array([
            [0.9240, 0.0743, 0.0010, 0.0006, 0.0001, 0.0000, 0.0000, 0.0000],
            [0.0064, 0.9066, 0.0799, 0.0060, 0.0006, 0.0004, 0.0000, 0.0001],
            [0.0007, 0.0227, 0.9105, 0.0592, 0.0052, 0.0013, 0.0002, 0.0002],
            [0.0001, 0.0027, 0.0529, 0.8847, 0.0506, 0.0070, 0.0014, 0.0006],
            [0.0002, 0.0011, 0.0043, 0.0648, 0.8346, 0.0793, 0.0122, 0.0035],
            [0.0000, 0.0011, 0.0018, 0.0056, 0.0668, 0.8378, 0.0757, 0.0112],
            [0.0000, 0.0000, 0.0016, 0.0098, 0.0196, 0.1029, 0.7748, 0.0913],
        ])
        return pd.DataFrame(matrix, index=ratings[:-1], columns=ratings)
    
    def _load_recovery_rates(self) -> Dict[str, float]:
        """Load recovery rates by credit rating."""
        return {
            'AAA': 0.95,
            'AA': 0.90,
            'A': 0.85,
            'BBB': 0.75,
            'BB': 0.65,
            'B': 0.45,
            'CCC': 0.35,
            'D': 0.25
        }
    
    def project_cashflows(self, bond: Bond, projection_dates: List[date],
                         scenario_rates: pd.DataFrame) -> pd.DataFrame:
        """Project cash flows for a bond under given interest rate scenario."""
        cashflows = []
        current_rating = bond.credit_rating
        
        for proj_date in projection_dates:
            if proj_date < bond.maturity_date:
                # Calculate scheduled payments
                if self._is_payment_date(proj_date, bond):
                    coupon_payment = self._calculate_coupon_payment(bond)
                    
                    # Convert date to timestamp for pandas indexing
                    scenario_date = pd.Timestamp(proj_date)
                    
                    # Apply credit risk
                    payment_adjustment = self._apply_credit_risk(
                        coupon_payment, 
                        current_rating, 
                        scenario_rates.loc[scenario_date, 'credit_spread']
                    )
                    
                    cashflows.append({
                        'date': proj_date,
                        'coupon': payment_adjustment,
                        'principal': 0.0,
                        'credit_rating': current_rating
                    })
                    
                # Update credit rating based on transition probability
                current_rating = self._simulate_rating_transition(current_rating)
                
            elif proj_date == bond.maturity_date:
                # Final coupon and principal payment
                coupon_payment = self._calculate_coupon_payment(bond)
                principal_payment = bond.par_value
                
                # Convert date to timestamp for pandas indexing
                scenario_date = pd.Timestamp(proj_date)
                
                # Apply credit risk to final payments
                payment_adjustment = self._apply_credit_risk(
                    coupon_payment + principal_payment,
                    current_rating,
                    scenario_rates.loc[scenario_date, 'credit_spread']
                )
                
                cashflows.append({
                    'date': proj_date,
                    'coupon': coupon_payment * (payment_adjustment / (coupon_payment + principal_payment)),
                    'principal': principal_payment * (payment_adjustment / (coupon_payment + principal_payment)),
                    'credit_rating': current_rating
                })
        
        return pd.DataFrame(cashflows)
    
    def _is_payment_date(self, test_date: date, bond: Bond) -> bool:
        """Check if the date is a coupon payment date."""
        if test_date < bond.issue_date or test_date > bond.maturity_date:
            return False
            
        months_between = (test_date.year - bond.issue_date.year) * 12 + \
                        test_date.month - bond.issue_date.month
        return months_between % (12 / bond.payment_frequency) == 0
    
    def _calculate_coupon_payment(self, bond: Bond) -> float:
        """Calculate coupon payment amount."""
        return bond.par_value * bond.coupon_rate / bond.payment_frequency
    
    def _apply_credit_risk(self, payment: float, rating: str,
                          credit_spread: float) -> float:
        """Apply credit risk adjustment to payment."""
        if rating == 'D':
            return payment * self.default_recovery_rates[rating]
        return payment * (1 - credit_spread * (1 - self.default_recovery_rates[rating]))
    
    def _simulate_rating_transition(self, current_rating: str) -> str:
        """Simulate credit rating transition."""
        if current_rating == 'D':
            return 'D'
            
        transition_probs = self.credit_transition_matrix.loc[current_rating]
        return np.random.choice(
            transition_probs.index,
            p=transition_probs.values
        )
    
    def calculate_duration(self, bond: Bond, yield_rate: float) -> float:
        """Calculate modified duration of the bond."""
        cashflows = self.project_cashflows(
            bond,
            [bond.maturity_date],
            pd.DataFrame({'credit_spread': [0.0]}, index=[bond.maturity_date])
        )
        
        duration = 0
        price = 0
        
        for _, cf in cashflows.iterrows():
            t = (cf['date'] - bond.issue_date).days / 365
            pv_factor = 1 / (1 + yield_rate) ** t
            cf_amount = cf['coupon'] + cf['principal']
            
            duration += t * cf_amount * pv_factor
            price += cf_amount * pv_factor
            
        return duration / price / (1 + yield_rate)
    
    def calculate_convexity(self, bond: Bond, yield_rate: float) -> float:
        """Calculate convexity of the bond."""
        cashflows = self.project_cashflows(
            bond,
            [bond.maturity_date],
            pd.DataFrame({'credit_spread': [0.0]}, index=[bond.maturity_date])
        )
        
        convexity = 0
        price = 0
        
        for _, cf in cashflows.iterrows():
            t = (cf['date'] - bond.issue_date).days / 365
            pv_factor = 1 / (1 + yield_rate) ** t
            cf_amount = cf['coupon'] + cf['principal']
            
            convexity += t * (t + 1) * cf_amount * pv_factor
            price += cf_amount * pv_factor
            
        return convexity / price / (1 + yield_rate) ** 2
