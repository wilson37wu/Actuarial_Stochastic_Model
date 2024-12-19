"""
Example script demonstrating the use of the model input GUI.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

try:
    import openpyxl
except ImportError:
    print("Installing required package: openpyxl")
    os.system("pip install openpyxl")
    import openpyxl

from src.enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType, PremiumMode, DividendOption
)
from src.model_gui import ModelInputGUI

if __name__ == "__main__":
    gui = ModelInputGUI()
    gui.run()
