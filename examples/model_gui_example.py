"""
Example script demonstrating the use of the model input GUI.
"""
import sys
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Set up logging
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"model_gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Install required packages
required_packages = ['openpyxl']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        logger.info(f"Installing required package: {package}")
        os.system(f"pip install {package}")
        __import__(package)

try:
    from src.enums import (
        Sex, SmokingStatus, OccupationClass,
        UnderwritingClass, ProductType, PremiumMode, DividendOption
    )
    # You can use either of these imports:
    from src.model_gui import ModelInputGUI  # Backward compatible way
    # from src.gui.main import ModelGUI as ModelInputGUI  # New way
except Exception as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

def main():
    try:
        logger.info("Starting Model GUI application")
        gui = ModelInputGUI()
        gui.run()
    except Exception as e:
        logger.error(f"Error running Model GUI: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Application terminated with error")
        sys.exit(1)
