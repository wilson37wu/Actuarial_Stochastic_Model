"""
Asset Liability Management (ALM) Module

This module provides tools and functionality for Asset-Liability Management,
including strategy implementation, risk metrics, and reporting.
"""

from .strategy import ALMStrategy
from .config import ALMConfig, AssetClassConfig, DEFAULT_ASSET_CLASSES, CORRELATION_MATRIX

__all__ = [
    'ALMStrategy',
    'ALMConfig',
    'AssetClassConfig',
    'DEFAULT_ASSET_CLASSES',
    'CORRELATION_MATRIX'
] 