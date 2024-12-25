"""
Script to run the actuarial model dashboard.
"""
import streamlit as st
from src.dashboard.dashboard import ModelDashboard

def main():
    """Run the dashboard."""
    dashboard = ModelDashboard()
    dashboard.run()

if __name__ == '__main__':
    main()
