"""
Constants and parameters for HKRBC calculations.
References Cap 41R - Insurance (Valuation and Capital) Rules.
"""

from enum import Enum
from typing import Dict
from pathlib import Path

# Reference document path
TECHNICAL_SPECS_DIR = Path(__file__).parent.parent.parent / "docs" / "hkrbc" / "technical_specs"
CAP_41R_PATH = TECHNICAL_SPECS_DIR / "Cap_41R_Consolidated.pdf"

class CapitalTier(Enum):
    """Capital tiers as defined in Cap 41R Part 5."""
    UNLIMITED_TIER_1 = "Unlimited Tier 1"
    LIMITED_TIER_1 = "Limited Tier 1"
    TIER_2 = "Tier 2"

# Capital tier limits as percentage of PCA (Cap 41R Part 5)
CAPITAL_TIER_LIMITS: Dict[CapitalTier, float] = {
    CapitalTier.UNLIMITED_TIER_1: float('inf'),  # No limit
    CapitalTier.LIMITED_TIER_1: 0.10,  # 10% of PCA
    CapitalTier.TIER_2: 0.50,  # 50% of PCA
}

# Minimum capital requirements (Cap 41R Section 13AA)
MINIMUM_CAPITAL_AMOUNT_HKD = 20_000_000  # HK$20 million

# IA data URLs
IA_BASE_URL = "https://www.ia.org.hk/en/supervision/reg_insurers_lloyd"
RISK_FREE_CURVE_URL_TEMPLATE = f"{IA_BASE_URL}/files/%Y-%m_Specified_Risk-free_Yield_Curve.xlsx"
CCA_LEVELS_URL = f"{IA_BASE_URL}/files/Historical_CCA_Levels.xlsx"
