"""
Script to run the actuarial model dashboard.
"""
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import streamlit as st
from src.dashboard.dashboard import ModelDashboard

def main():
    """Run the dashboard."""
    dashboard = ModelDashboard()
    dashboard.run()

if __name__ == '__main__':
    main()
