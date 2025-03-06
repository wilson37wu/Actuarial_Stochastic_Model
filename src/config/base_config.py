"""Base configuration class for the actuarial stochastic model.

This module provides a standardized configuration interface with validation
and type checking for all model parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
from pathlib import Path
import pandas as pd

@dataclass
class BaseConfig:
    """Base configuration class with validation and conversion utilities."""
    
    config_path: Optional[str] = None
    _config_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Load configuration if path provided."""
        if self.config_path:
            self.load_config(self.config_path)
    
    def load_config(self, path: str) -> None:
        """Load configuration from JSON file.
        
        Args:
            path: Path to configuration file
        """
        with open(path, 'r') as f:
            self._config_data = json.load(f)
        self.validate()
    
    def save_config(self, path: str) -> None:
        """Save configuration to JSON file.
        
        Args:
            path: Path to save configuration
        """
        with open(path, 'w') as f:
            json.dump(self._config_data, f, indent=4)
    
    def validate(self) -> None:
        """Validate configuration parameters.
        
        Raises:
            ValueError: If validation fails
        """
        pass  # Implement in child classes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config_data
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert configuration to DataFrame for analysis."""
        return pd.DataFrame.from_dict(self._config_data, orient='index', columns=['Value'])
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """Update configuration parameters.
        
        Args:
            new_config: New configuration parameters
        """
        self._config_data.update(new_config)
        self.validate()
