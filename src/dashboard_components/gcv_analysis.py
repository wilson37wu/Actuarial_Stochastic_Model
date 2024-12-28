"""GCV Analysis dashboard component."""
import streamlit as st
import pandas as pd
import numpy as np
from src.gcv_calculator import GradingPattern, ProductVariant

def render_controls():
    """Render GCV analysis controls in sidebar."""
    st.sidebar.subheader("GCV Parameters")
    
    # Add help button and parameter descriptions
    with st.sidebar:
        if st.button("📖 Parameter Guide", key="gcv_help_btn"):
            st.session_state.show_gcv_guide = not st.session_state.get('show_gcv_guide', False)
    
    # Show parameter guide in main area if enabled
    if st.session_state.get('show_gcv_guide', False):
        st.markdown("""
        ## GCV Parameter Guide
        
        ### Basic Parameters
        - **Base Percentage** (60-80%)
          - Percentage of present value of premiums used for GCV calculations
          - Higher values = more generous guaranteed values
          - Example: 70% means GCV is based on 70% of premium present value
        
        - **Initial GCV %** (40-60%)
          - Starting guaranteed cash value as % of face amount
          - Example: For $100,000 face amount, 50% = $50,000 initial GCV
          - Higher values are more attractive but increase cost
        
        - **Grading Years** (10-20 years)
          - Period over which GCV reduces to minimum
          - Longer period = smoother reduction
          - Shorter period = lower cost
        
        - **Minimum GCV %** (5-10%)
          - Floor for guaranteed values
          - Higher values provide better guarantees but increase cost
        
        ### Grading Patterns
        - **Linear**: Simple straight-line reduction
        - **S-Curve**: Slower reduction in early/late years
        - **Stepwise**: Distinct steps at specific durations
        - **Target IRR**: Designed to achieve specific IRR
        
        ### Product Variants
        - **Standard**: Traditional whole life
        - **Low Premium**: Lower early values, focus on death benefit
        - **High Early Value**: Higher early cash values
        - **Education/Retirement**: Values aligned with specific needs
        """)
    
    # Basic parameters with help text
    base_percentage = st.sidebar.slider(
        "Base Percentage",
        0.0, 1.0, 0.7,
        help="Percentage of present value of premiums used as base for GCV (typical: 60-80%)"
    )
    
    initial_gcv = st.sidebar.slider(
        "Initial GCV %",
        0.0, 1.0, 0.5,
        help="Starting GCV as % of face amount. Example: 50% of $100k = $50k initial GCV"
    )
    
    grading_years = st.sidebar.slider(
        "Grading Years",
        1, 30, 10,
        help="Years to grade from initial to minimum GCV (typical: 10-20 years)"
    )
    
    min_gcv = st.sidebar.slider(
        "Minimum GCV %",
        0.0, 0.5, 0.05,
        help="Minimum guaranteed value as % of face amount (typical: 5-10%)"
    )
    
    # Grading pattern selection with description
    pattern = st.sidebar.selectbox(
        "Grading Pattern",
        options=list(GradingPattern.__members__.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
        help="""
        Method used to reduce GCV over time:
        • LINEAR: Straight-line reduction
        • S_CURVE: Slower early/late years, faster middle years
        • STEPWISE: Distinct steps at specific durations
        • TARGET_IRR: Pattern to achieve specific IRR
        """
    )
    
    # Target IRR controls with explanations
    use_target_irr = st.sidebar.checkbox(
        "Use Target IRR",
        help="Enable to specify a target internal rate of return"
    )
    target_irr = None
    target_year = None
    if use_target_irr:
        target_irr = st.sidebar.slider(
            "Target IRR %",
            0.0, 10.0, 2.0,
            help="Desired internal rate of return to achieve"
        ) / 100
        target_year = st.sidebar.slider(
            "Target Year",
            1, 30, 10,
            help="Policy year by which to achieve target IRR"
        )
    
    # External table upload with guidance
    use_external_table = st.sidebar.checkbox(
        "Use External Table",
        help="Upload custom GCV factors from CSV file"
    )
    external_table = None
    if use_external_table:
        st.sidebar.markdown("""
        📝 **CSV Format Requirements**:
        - Columns: Product, Year, Factor
        - Factor should be decimal (e.g., 0.8 for 80%)
        """)
        uploaded_file = st.sidebar.file_uploader(
            "Upload GCV Table (CSV)",
            type="csv",
            help="CSV file with columns: Product,Year,Factor"
        )
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                external_table = {}
                for product in df['Product'].unique():
                    product_df = df[df['Product'] == product]
                    external_table[product] = dict(zip(product_df['Year'], product_df['Factor']))
            except Exception as e:
                st.sidebar.error(f"Error loading CSV: {str(e)}")
    
    # Product variant selection with descriptions
    product_variant = st.sidebar.selectbox(
        "Product Variant",
        options=list(ProductVariant.__members__.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
        help="""
        Type of product affecting GCV calculation:
        • STANDARD: Traditional whole life
        • LOW_PREMIUM: Lower premium products
        • HIGH_EARLY_VALUE: Higher early cash values
        • LEVEL_GCV: More level GCV pattern
        • EDUCATION: Higher values during education years
        • RETIREMENT: Higher values near retirement
        """
    )
    
    # Pattern mixing controls with explanation
    pattern_weights = {}
    if st.sidebar.checkbox(
        "Enable Pattern Mixing",
        help="Combine multiple grading patterns with different weights"
    ):
        st.sidebar.markdown("Adjust weights for each pattern (total will be normalized to 100%)")
        st.sidebar.subheader("Pattern Weights")
        total_weight = 0
        for pat in GradingPattern.__members__.keys():
            weight = st.sidebar.slider(
                f"{pat.replace('_', ' ').title()} Weight",
                0.0, 1.0, 0.0,
                help=f"Weight for {pat.lower()} pattern in the mix"
            )
            pattern_weights[pat] = weight
            total_weight += weight
        
        if total_weight > 0:
            pattern_weights = {k: v/total_weight for k, v in pattern_weights.items()}
    
    show_3d = st.sidebar.checkbox(
        "Show 3D Visualization",
        help="Display 3D surface showing GCV variation with premium and face amount"
    )
    
    return {
        "base_percentage": base_percentage,
        "initial_gcv": initial_gcv,
        "grading_years": grading_years,
        "min_gcv": min_gcv,
        "pattern": GradingPattern[pattern],
        "target_irr": target_irr,
        "target_year": target_year,
        "external_table": external_table,
        "product_variant": ProductVariant[product_variant],
        "pattern_weights": pattern_weights,
        "show_3d": show_3d
    }

def render_results(params, visualizer):
    """Render GCV analysis results in main area."""
    st.subheader("GCV Analysis Results")
    
    # Show current parameter summary
    with st.expander("Current Parameters Summary", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            #### Basic Settings
            - **Initial GCV**: {:.1f}% of face amount at issue
            - **Base**: {:.1f}% of PV premiums
            - **Minimum**: {:.1f}% of face amount
            - **Grading Period**: {} years
            """.format(
                params["initial_gcv"] * 100,
                params["base_percentage"] * 100,
                params["min_gcv"] * 100,
                params["grading_years"]
            ))
        
        with col2:
            st.markdown("""
            #### Pattern Settings
            - **Method**: {}
            - **Product Type**: {}
            - **Pattern Mixing**: {}
            """.format(
                params["pattern"].value.replace("_", " ").title(),
                params["product_variant"].value.replace("_", " ").title(),
                "Enabled" if params["pattern_weights"] else "Disabled"
            ))
    
    # Display current IRR if target IRR is used
    if params.get("target_irr"):
        st.info(f"Target IRR: {params['target_irr']*100:.1f}% by year {params['target_year']}")
        achieved_irr = visualizer.calculate_achieved_irr(params["target_year"])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Achieved IRR",
                f"{achieved_irr*100:.1f}%",
                f"{(achieved_irr - params['target_irr'])*100:+.1f}%"
            )
        with col2:
            st.metric(
                "Target Year",
                f"Year {params['target_year']}"
            )
        with col3:
            st.metric(
                "IRR Gap",
                f"{abs(achieved_irr - params['target_irr'])*100:.2f}%",
                "Below Target" if achieved_irr < params['target_irr'] else "Above Target"
            )
    
    # Main area chart display
    if params["show_3d"]:
        with st.expander("3D Visualization Help", expanded=False):
            st.markdown("""
            The 3D surface shows how GCV varies with:
            - X-axis: Premium amount
            - Y-axis: Face amount
            - Z-axis: GCV factor
            
            Use the slider to see how the surface changes over policy years.
            """)
        fig = visualizer.plot_3d_gcv_surface()
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### GCV Pattern Over Time")
            fig = visualizer.plot_gcv_patterns(max_years=30)
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
        with col2:
            if params["pattern_weights"]:
                st.markdown("#### Pattern Mix Components")
                fig = visualizer.plot_mixed_pattern(params["pattern_weights"], max_years=30)
            else:
                st.markdown("#### Pattern Rate of Change")
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
