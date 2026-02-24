"""
Data classes for insurance products.
"""
from dataclasses import dataclass
from datetime import date

@dataclass
class PolicyLoan:
    """Policy loan information."""
    amount: float
    interest_rate: float
    outstanding_interest: float = 0.0
    issue_date: date = None

@dataclass
class DividendHistory:
    """Dividend payment history."""
    declaration_date: date
    amount: float
    dividend_type: str = "CASH"

@dataclass
class BonusHistory:
    """Bonus declaration history."""
    declaration_date: date
    amount: float
    face_amount: float

@dataclass
class PolicyValues:
    """Policy values including cash value and non-forfeiture options."""
    cash_value: float
    surrender_value: float
    death_benefit: float
    loan_balance: float = 0.0
    reduced_paid_up_value: float = 0.0
    extended_term_period: int = 0
