"""Dashboard styling and theme configuration."""
import streamlit as st

def apply_dashboard_theme():
    """Apply the dashboard theme and styling."""
    st.markdown("""
        <style>
        /* Sidebar styling */
        section[data-testid="stSidebar"] > div {
            background-color: #0E1117;
            padding: 4rem 2rem;
        }
        
        /* Make ALL sidebar text white */
        section[data-testid="stSidebar"] * {
            color: white !important;
        }
        
        /* Style dropdown/selectbox */
        section[data-testid="stSidebar"] .stSelectbox > div > div {
            background-color: #262730 !important;
        }
        
        /* Style dropdown options */
        section[data-testid="stSidebar"] .stSelectbox [role="listbox"] {
            background-color: #262730 !important;
        }
        
        section[data-testid="stSidebar"] .stSelectbox [role="option"] {
            background-color: #262730 !important;
            color: white !important;
        }
        
        section[data-testid="stSidebar"] .stSelectbox [role="option"]:hover {
            background-color: #404040 !important;
        }
        
        /* Style number inputs */
        section[data-testid="stSidebar"] .stNumberInput input {
            color: white !important;
            background-color: #262730 !important;
        }
        
        /* Style sliders */
        section[data-testid="stSidebar"] .stSlider {
            color: white !important;
        }
        
        /* Main content area */
        .main .block-container {
            padding: 2rem 5rem;
        }
        
        /* Error message section */
        .error-section {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 20%;
            background-color: #0E1117;
            color: #ff4b4b;
            padding: 1rem;
            overflow-y: auto;
        }
        </style>
    """, unsafe_allow_html=True)
