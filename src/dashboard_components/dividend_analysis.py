"""Dividend Analysis dashboard component."""
import streamlit as st

def render_controls():
    """Render dividend analysis controls."""
    st.sidebar.subheader("Dividend Parameters")
    n_policies = st.sidebar.number_input("Number of Policies", 1, 10, 3)
    n_periods = st.sidebar.number_input("Number of Periods", 5, 100, 20)
    
    return {
        "n_policies": n_policies,
        "n_periods": n_periods
    }

def render_results(params, visualizer):
    """Render dividend analysis results."""
    st.subheader("Dividend Performance Analysis")
    
    tab1, tab2, tab3 = st.tabs([
        "Returns & Dividends",
        "Recovery Analysis",
        "Detailed Reports"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig = visualizer._plot_returns_vs_dividends()
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = visualizer._plot_tracking_balance()
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            fig = visualizer._plot_recovery_metrics()
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            fig = visualizer._plot_recovery_projection()
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        render_detailed_reports(visualizer)
