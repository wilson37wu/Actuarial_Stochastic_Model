"""Model configuration for actuarial stochastic models.

This module defines specific configuration parameters and validation rules
for different model components (assets, liabilities, scenarios).
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np
from .base_config import BaseConfig

@dataclass
class ModelConfig(BaseConfig):
    """Configuration for actuarial stochastic model components."""
    
    def validate(self) -> None:
        """Validate model configuration parameters.
        
        Validates:
        - Economic scenario parameters
        - Asset model parameters
        - Liability model parameters
        - Product parameters
        
        Raises:
            ValueError: If validation fails
        """
        self._validate_economic_params()
        self._validate_asset_params()
        self._validate_liability_params()
        self._validate_product_params()
    
    def _validate_economic_params(self) -> None:
        """Validate economic scenario parameters."""
        eco_params = self._config_data.get('economic', {})
        required_params = ['interest_rate_mean', 'interest_rate_vol', 'equity_return_mean']
        
        for param in required_params:
            if param not in eco_params:
                raise ValueError(f"Missing required economic parameter: {param}")
        
        # Validate parameter ranges
        if not (0 <= eco_params['interest_rate_mean'] <= 0.15):
            raise ValueError("Interest rate mean must be between 0% and 15%")
        if not (0 <= eco_params['interest_rate_vol'] <= 0.1):
            raise ValueError("Interest rate volatility must be between 0% and 10%")
    
    def _validate_asset_params(self) -> None:
        """Validate asset model parameters."""
        asset_params = self._config_data.get('assets', {})
        
        # Validate asset allocation
        allocations = asset_params.get('allocation', {})
        total_allocation = sum(allocations.values())
        if not np.isclose(total_allocation, 1.0, atol=1e-6):
            raise ValueError("Asset allocations must sum to 100%")
        
        # Validate equity parameters
        equity_params = asset_params.get('equity', {})
        if 'market_volatility' in equity_params:
            vol = equity_params['market_volatility']
            if not (0 <= vol <= 0.5):
                raise ValueError("Market volatility must be between 0% and 50%")
    
    def _validate_liability_params(self) -> None:
        """Validate liability model parameters."""
        liability_params = self._config_data.get('liabilities', {})
        
        # Validate mortality assumptions
        mortality = liability_params.get('mortality', {})
        if 'table' not in mortality:
            raise ValueError("Mortality table must be specified")
        
        # Validate lapse assumptions
        lapse = liability_params.get('lapse', {})
        if 'base_rate' in lapse:
            rate = lapse['base_rate']
            if not (0 <= rate <= 0.3):
                raise ValueError("Base lapse rate must be between 0% and 30%")
    
    def _validate_product_params(self) -> None:
        """Validate product-specific parameters."""
        products = self._config_data.get('products', {})
        
        for product_id, params in products.items():
            if 'type' not in params:
                raise ValueError(f"Product type not specified for {product_id}")
            
            # Validate participating product parameters
            if params['type'] == 'participating':
                if 'bonus_rate' not in params:
                    raise ValueError(f"Bonus rate not specified for participating product {product_id}")
                rate = params['bonus_rate']
                if not (0 <= rate <= 0.1):
                    raise ValueError(f"Bonus rate must be between 0% and 10% for {product_id}")
    
    @property
    def economic_params(self) -> Dict[str, Any]:
        """Get economic scenario parameters."""
        return self._config_data.get('economic', {})
    
    @property
    def asset_params(self) -> Dict[str, Any]:
        """Get asset model parameters."""
        return self._config_data.get('assets', {})
    
    @property
    def liability_params(self) -> Dict[str, Any]:
        """Get liability model parameters."""
        return self._config_data.get('liabilities', {})
    
    @property
    def product_params(self) -> Dict[str, Any]:
        """Get product-specific parameters."""
        return self._config_data.get('products', {})
