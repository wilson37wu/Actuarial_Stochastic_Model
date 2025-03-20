"""Module for downloading data from Hong Kong Insurance Authority."""

import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests
from ..constants import RISK_FREE_CURVE_URL_TEMPLATE, CCA_LEVELS_URL

class IADataDownloader:
    """Handles downloading and parsing of IA data."""
    
    def __init__(self, cache_dir: str = "data/hkrbc"):
        """
        Initialize downloader with cache directory.
        
        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_risk_free_rates(self, as_of_date: datetime) -> pd.DataFrame:
        """
        Get risk-free rates for specified date.
        Downloads from IA website if not in cache.
        
        Args:
            as_of_date: Date to get rates for
            
        Returns:
            DataFrame containing risk-free rates
        """
        url = as_of_date.strftime(RISK_FREE_CURVE_URL_TEMPLATE)
        cache_file = self.cache_dir / f"risk_free_{as_of_date:%Y%m}.xlsx"
        
        if not cache_file.exists():
            self._download_file(url, cache_file)
            
        return pd.read_excel(cache_file)
        
    def get_cca_levels(self) -> pd.DataFrame:
        """
        Get historical CCA levels.
        Downloads from IA website if not in cache.
        
        Returns:
            DataFrame containing CCA levels
        """
        cache_file = self.cache_dir / "cca_levels.xlsx"
        
        if not cache_file.exists():
            self._download_file(CCA_LEVELS_URL, cache_file)
            
        return pd.read_excel(cache_file)
        
    def _download_file(self, url: str, target_path: Path) -> None:
        """
        Download file from URL to target path.
        
        Args:
            url: URL to download from
            target_path: Path to save file to
        """
        response = requests.get(url)
        response.raise_for_status()
        
        with open(target_path, "wb") as f:
            f.write(response.content)
