"""GCV Analysis dashboard component."""
import streamlit as st
from ..gcv_calculator import GradingPattern

def render_controls():
    """Render GCV analysis controls in sidebar."""
    st.sidebar.subheader("GCV Parameters")
    
    pattern_weights = {}
    if st.sidebar.checkbox("Enable Pattern Mixing"):
        st.sidebar.subheader("Pattern Weights")
        total_weight = 0
        for pattern in GradingPattern.__members__.keys():
            weight = st.sidebar.slider(f"{pattern} Weight", 0.0, 1.0, 0.0)
            pattern_weights[pattern] = weight
            total_weight += weight
        
        if total_weight > 0:
            pattern_weights = {k: v/total_weight for k, v in pattern_weights.items()}
    
    show_3d = st.sidebar.checkbox("Show 3D Visualization")
    
    return {
        "pattern_weights": pattern_weights,
        "show_3d": show_3d
    }

def render_results(params, visualizer):
    """Render GCV analysis results in main area."""
    st.subheader("GCV Analysis Results")
    
    # Main area chart display
    if params["show_3d"]:
        fig = visualizer.plot_3d_gcv_surface()
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig = visualizer.plot_gcv_patterns(max_years=30)
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
        with col2:
            if params["pattern_weights"]:
                fig = visualizer.plot_mixed_pattern(params["pattern_weights"], max_years=30)
            else:
                fig = visualizer.plot_pattern_derivatives(max_years=30)
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    
    # Additional tabs for other analyses
    tab1, tab2, tab3 = st.tabs([
        "Product Comparison", "Sensitivity", "Historical Analysis"
    ])
    
    with tab1:
        render_product_comparison(visualizer)
    
    with tab2:
        render_gcv_sensitivity(visualizer)
    
    with tab3:
        render_historical_analysis(visualizer)

def render_product_comparison(visualizer):
    """Render product comparison analysis."""
    st.subheader("Product Comparison")
    col1, col2 = st.columns(2)
    with col1:
        fig = visualizer.plot_product_variant_gcv(
            premium=1000,
            face_amount=100000,
            pv_premium=10000,
            max_years=30
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def render_gcv_sensitivity(visualizer):
    """Render GCV sensitivity analysis."""
    st.subheader("Sensitivity Analysis")
    col1, col2 = st.columns(2)
    with col1:
        fig = visualizer.plot_gcv_sensitivity()
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def render_historical_analysis(visualizer):
    """Render historical analysis."""
    st.subheader("Historical Analysis")
    col1, col2 = st.columns(2)
    with col1:
        fig = visualizer.plot_historical_gcv()
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
