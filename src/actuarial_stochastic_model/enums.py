"""
Common enumerations used across the actuarial model.
"""
from enum import Enum, auto

class AssetClass(Enum):
    """Asset classes for investment."""
    CASH = auto()
    MONEY_MARKET = auto()
    GOVERNMENT_BOND = auto()
    CORPORATE_BOND = auto()
    HIGH_YIELD_BOND = auto()
    LARGE_CAP_EQUITY = auto()
    SMALL_CAP_EQUITY = auto()
    INTERNATIONAL_EQUITY = auto()
    EMERGING_MARKETS = auto()
    REAL_ESTATE = auto()

class Sex(Enum):
    """Sex classification."""
    MALE = auto()
    FEMALE = auto()

class SmokingStatus(Enum):
    """Smoking status classification."""
    NON_SMOKER = auto()
    SMOKER = auto()

class OccupationClass(Enum):
    """Occupation class for underwriting."""
    CLASS_1 = auto()  # Professional/Office
    CLASS_2 = auto()  # Technical/Skilled
    CLASS_3 = auto()  # Light Manual
    CLASS_4 = auto()  # Heavy Manual

class UnderwritingClass(Enum):
    """Underwriting class."""
    PREFERRED = auto()
    STANDARD = auto()
    SUBSTANDARD = auto()

class ProductType(Enum):
    """Insurance product types."""
    TERM = auto()
    WHOLE_LIFE = auto()
    PARTICIPATING = auto()  # Combined PAR_WHOLE_LIFE
    UNIVERSAL_LIFE = auto()
    UNIT_LINKED = auto()

class DividendOption(Enum):
    """Dividend payment options for participating policies."""
    CASH = auto()           # Pay in cash
    PREMIUM_REDUCTION = auto()  # Reduce future premiums
    PAID_UP_ADDITIONS = auto()  # Purchase additional insurance
    ACCUMULATE = auto()     # Leave with insurer to accumulate interest

class InvestmentStrategy(Enum):
    """Investment strategy types."""
    CONSERVATIVE = auto()   # Low risk, mostly fixed income
    BALANCED = auto()       # Mix of equity and fixed income
    AGGRESSIVE = auto()     # High equity allocation
    CUSTOM = auto()         # Custom allocation strategy

class PremiumMode(Enum):
    """Premium payment frequency."""
    ANNUAL = auto()         # Once per year
    SEMI_ANNUAL = auto()    # Twice per year
    QUARTERLY = auto()      # Four times per year
    MONTHLY = auto()        # Monthly payments
    SINGLE = auto()         # Single premium
    FLEXIBLE = auto()       # Flexible payments (e.g., Universal Life)

class PremiumStatus(Enum):
    """Status of premium payments."""
    PAYING = auto()         # Regular premium payments
    PAID_UP = auto()        # No more premiums due
    WAIVED = auto()         # Premiums waived (e.g., disability)
    LOAN = auto()           # Premium paid by automatic loan
    OVERDUE = auto()        # Premium payment overdue

class NonForfeitureOption(Enum):
    """Non-forfeiture options."""
    REDUCED_PAID_UP = auto()    # Reduced paid-up insurance
    EXTENDED_TERM = auto()      # Extended term insurance
    CASH_SURRENDER = auto()     # Cash surrender value
    AUTOMATIC_PREMIUM_LOAN = auto()  # Automatic premium loan
