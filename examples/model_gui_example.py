"""
Example script demonstrating the use of the model input GUI.
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_gui import launch_gui

if __name__ == '__main__':
    # Launch the GUI
    launch_gui()
