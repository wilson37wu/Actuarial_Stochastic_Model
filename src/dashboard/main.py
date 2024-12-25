"""Main dashboard module."""
import streamlit as st
from typing import Dict

from .gcv_analysis import GCVAnalysis
from .scenario_analysis import ScenarioAnalysis
from .sensitivity_analysis import SensitivityAnalysis
from .portfolio_analysis import PortfolioAnalysis
from .visualization import Visualization
from .data_export import DataExport

from ..gcv_calculator import GCVCalculator, GCVParameters, GradingPattern
from ..dividend_tracker import DividendTracker, DividendAccount

class Dashboard:
    """Main dashboard class."""
    
    def __init__(self, calculator: GCVCalculator, tracker: DividendTracker):
        """Initialize dashboard components.
        
        Args:
            calculator: GCV calculator instance
            tracker: Dividend tracker instance
        """
        self.calculator = calculator
        self.tracker = tracker
        
        self.gcv = GCVAnalysis(self.calculator)
        self.scenario = ScenarioAnalysis(self.calculator, self.tracker)
        self.sensitivity = SensitivityAnalysis(self.calculator)
        self.portfolio = PortfolioAnalysis(self.calculator, self.tracker)
        self.viz = Visualization()
        self.export = DataExport()
    
    def run(self):
        """Run the dashboard."""
        st.set_page_config(
            page_title="Actuarial Model Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better contrast
        st.markdown("""
            <style>
                .stApp {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                .main .block-container {
                    background-color: #FFE6E6;
                    padding: 2rem;
                    border-radius: 10px;
                }
                h1, h2, h3, h4, h5, h6, p, span, div {
                    color: #000000 !important;
                }
                /* Button styles */
                .stButton>button {
                    background-color: #404040 !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 4px !important;
                    padding: 0.5rem 1rem !important;
                    font-weight: 500 !important;
                }
                .stButton>button:hover {
                    background-color: #505050 !important;
                }
                
                /* Select box styles */
                .stSelectbox>div>div {
                    background-color: #404040 !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 4px !important;
                }
                .stSelectbox>div>div:hover {
                    background-color: #505050 !important;
                }
                
                /* Text input styles */
                .stTextInput>div>div>input {
                    background-color: #FFFFFF !important;
                    color: #FF4B4B !important;
                    border: 1px solid #FF4B4B !important;
                    border-radius: 4px !important;
                    font-weight: 500 !important;
                }
                .stTextInput>div>div>input:focus {
                    border-color: #FF4B4B !important;
                    box-shadow: 0 0 0 1px #FF4B4B !important;
                }
                
                .stSlider>div>div {
                    background-color: #FFE6E6;
                }
                .sidebar .sidebar-content {
                    background-color: #FFE6E6;
                    color: #000000;
                }
                .streamlit-expanderHeader {
                    color: #000000 !important;
                    background-color: #FFE6E6;
                }
                .stMarkdown {
                    color: #000000;
                }
                .stDataFrame {
                    color: #000000;
                }
                .stPlotlyChart {
                    color: #000000;
                }
                .css-1d391kg, .css-12oz5g7 {
                    background-color: #FFE6E6;
                }
                
                /* Dropdown menu items */
                .stSelectbox ul {
                    background-color: #404040 !important;
                }
                .stSelectbox ul li {
                    color: #FFFFFF !important;
                }
                .stSelectbox ul li:hover {
                    background-color: #505050 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Add theme customization
        self.viz.apply_theme()
        
        st.title("Actuarial Model Analysis Dashboard")
        
        # Sidebar for global controls
        with st.sidebar:
            st.header("Controls")
            analysis_type = st.selectbox(
                "Select Analysis Type",
                ["GCV Analysis", "Dividend Analysis", "Stress Testing", 
                 "Sensitivity Analysis", "Portfolio Analysis"]
            )
            
            if analysis_type == "GCV Analysis":
                self.gcv.render()
            elif analysis_type == "Stress Testing":
                self.scenario.render_stress_testing()
            elif analysis_type == "Sensitivity Analysis":
                self.sensitivity.render()
            elif analysis_type == "Portfolio Analysis":
                self.portfolio.render()
            
            # Add export options
            st.sidebar.markdown("---")
            st.sidebar.subheader("Export Options")
            self.export.render_export_options()
