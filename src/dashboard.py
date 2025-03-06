"""
Interactive dashboard for actuarial model analysis.
"""
import streamlit as st
import plotly.graph_objects as go
from .dashboard_components import styling
from .dashboard_components import gcv_analysis
from .dashboard_components import dividend_analysis
from .dividend_tracker import DividendTracker
from .gcv_calculator import GCVCalculator, GradingPattern
from .visualization import ModelVisualizer

class ModelDashboard:
    """Interactive dashboard for model analysis."""
    
    def __init__(self):
        """Initialize dashboard components."""
        self.tracker = DividendTracker()
        self.calculator = GCVCalculator()
        self.visualizer = ModelVisualizer()
    
    def run(self):
        """Run the dashboard."""
        # Configure page layout
        st.set_page_config(
            page_title="Actuarial Model Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply dashboard theme
        styling.apply_dashboard_theme()
        
        # Sidebar
        with st.sidebar:
            st.image("https://www.codeium.com/images/logo-dark.png", width=200)
            st.title("Model Parameters")
            
            # Analysis type selector
            analysis_type = st.selectbox(
                "Select Analysis Type",
                ["GCV Analysis", "Dividend Analysis", "Stress Testing", 
                 "Sensitivity Analysis", "Portfolio Analysis"]
            )
            
            # Parameters based on analysis type
            if analysis_type == "GCV Analysis":
                pattern_weights = {}
                st.subheader("GCV Parameters")
                
                show_3d = st.checkbox("Show 3D Visualization")
                
                with st.expander("Pattern Mixing", expanded=False):
                    enable_mixing = st.checkbox("Enable Pattern Mixing")
                    if enable_mixing:
                        total_weight = 0
                        for pattern in GradingPattern.__members__.keys():
                            weight = st.slider(f"{pattern} Weight", 0.0, 1.0, 0.0)
                            pattern_weights[pattern] = weight
                            total_weight += weight
                        
                        if total_weight > 0:
                            pattern_weights = {k: v/total_weight for k, v in pattern_weights.items()}
                
                params = {
                    "pattern_weights": pattern_weights if enable_mixing else {},
                    "show_3d": show_3d
                }
            
            elif analysis_type == "Dividend Analysis":
                st.subheader("Dividend Parameters")
                n_policies = st.number_input("Number of Policies", 1, 10, 3)
                n_periods = st.number_input("Number of Periods", 5, 100, 20)
                
                params = {
                    "n_policies": n_policies,
                    "n_periods": n_periods
                }
            
            elif analysis_type == "Stress Testing":
                st.subheader("Stress Test Parameters")
                
                scenario_type = st.selectbox(
                    "Scenario Generation Method",
                    ["Historical", "Monte Carlo", "Custom", "Regime Switching"]
                )
                
                if scenario_type == "Monte Carlo":
                    n_scenarios = st.number_input("Number of Scenarios", 100, 10000, 1000)
                    n_years = st.number_input("Projection Years", 1, 50, 10)
                    
                    st.subheader("Asset Correlations")
                    assets = ["Equity", "Bonds", "Real Estate"]
                    corr_matrix = np.eye(len(assets))
                    for i in range(len(assets)):
                        for j in range(i+1, len(assets)):
                            corr = st.slider(
                                f"{assets[i]}-{assets[j]} Correlation",
                                -1.0, 1.0, 0.0
                            )
                            corr_matrix[i,j] = corr_matrix[j,i] = corr
                    
                    params = {
                        "scenario_type": scenario_type,
                        "n_scenarios": n_scenarios,
                        "n_years": n_years,
                        "corr_matrix": corr_matrix
                    }
                
                elif scenario_type == "Regime Switching":
                    n_regimes = st.number_input("Number of Regimes", 2, 5, 2)
                    regime_params = {}
                    for i in range(n_regimes):
                        st.subheader(f"Regime {i+1}")
                        regime_params[i] = {
                            'mean': st.number_input(f"Mean Return {i+1}", -0.5, 0.5, 0.06),
                            'vol': st.number_input(f"Volatility {i+1}", 0.0, 1.0, 0.12),
                            'duration': st.number_input(f"Avg Duration {i+1}", 1, 120, 24)
                        }
                    
                    params = {
                        "scenario_type": scenario_type,
                        "regime_params": regime_params
                    }
            
            elif analysis_type == "Sensitivity Analysis":
                st.subheader("Sensitivity Parameters")
                
                parameters = {
                    'Mortality': {'min': 0.5, 'max': 2.0, 'default': 1.0},
                    'Lapse': {'min': 0.0, 'max': 0.3, 'default': 0.05},
                    'Interest': {'min': 0.0, 'max': 0.15, 'default': 0.06},
                    'Expense': {'min': 0.5, 'max': 2.0, 'default': 1.0}
                }
                
                selected_params = st.multiselect(
                    "Select Parameters",
                    list(parameters.keys()),
                    default=list(parameters.keys())[:2]
                )
                
                analysis_type = st.selectbox(
                    "Analysis Type",
                    ["One-Way", "Two-Way", "Tornado", "Surface"]
                )
                
                params = {
                    "selected_params": selected_params,
                    "analysis_type": analysis_type
                }
            
            else:  # Portfolio Analysis
                st.subheader("Portfolio Parameters")
                
                products = {
                    'Traditional': st.number_input("Traditional %", 0, 100, 40),
                    'Universal': st.number_input("Universal %", 0, 100, 30),
                    'Term': st.number_input("Term %", 0, 100, 20),
                    'Annuity': st.number_input("Annuity %", 0, 100, 10)
                }
                
                params = products
        
        # Main content area
        st.title("Actuarial Model Analysis Dashboard")
        st.markdown(
            "<p style='text-align: right; color: #666666; font-style: italic; margin-top: -20px;'>"
            "Created using Windsurf</p>", 
            unsafe_allow_html=True
        )
        
        # Overview metrics
        if analysis_type == "GCV Analysis":
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Active Patterns", len(params["pattern_weights"]) if params["pattern_weights"] else "N/A")
            with col2:
                st.metric("Total Weight", "100%" if params["pattern_weights"] else "N/A")
            with col3:
                st.metric("Visualization", "3D" if params["show_3d"] else "2D")
            with col4:
                st.metric("Analysis Mode", "Pattern Analysis" if not params["pattern_weights"] else "Pattern Mixing")
        
        elif analysis_type == "Dividend Analysis":
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Policies", params["n_policies"])
            with col2:
                st.metric("Time Periods", params["n_periods"])
            with col3:
                st.metric("Average Return", f"{self.tracker.get_average_return():.2%}")
            with col4:
                st.metric("Total Dividends", f"${self.tracker.get_total_dividends():,.2f}")
        
        # Main visualization area
        st.divider()
        
        if analysis_type == "GCV Analysis":
            # Main GCV visualization
            if params["show_3d"]:
                fig = self._plot_3d_gcv_surface()
                st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    fig = self._plot_gcv_patterns(max_years=30)
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    if params["pattern_weights"]:
                        fig = self._plot_mixed_pattern(params["pattern_weights"], max_years=30)
                    else:
                        fig = self._plot_pattern_derivatives(max_years=30)
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            
            # Additional analysis sections
            st.divider()
            
            tab1, tab2, tab3 = st.tabs([
                "🔄 Product Comparison", 
                "📊 Sensitivity Analysis",
                "📈 Historical Trends"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Product Variant Analysis")
                    fig = self._plot_product_variant_gcv(
                        premium=1000,
                        face_amount=100000,
                        pv_premium=10000,
                        max_years=30
                    )
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    st.subheader("Variant Comparison")
                    fig = self._plot_variant_comparison()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Parameter Sensitivity")
                    fig = self._plot_parameter_sensitivity()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    st.subheader("Two-Way Analysis")
                    fig = self._plot_two_way_sensitivity()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            
            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Historical Trends")
                    fig = self._plot_historical_trends()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    st.subheader("Pattern Evolution")
                    fig = self._plot_pattern_evolution()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
        elif analysis_type == "Dividend Analysis":
            tab1, tab2 = st.tabs([
                "📈 Performance Analysis",
                "💰 Recovery Analysis"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Returns vs Dividends")
                    fig = self._plot_returns_vs_dividends()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    st.subheader("Account Balance")
                    fig = self._plot_tracking_balance()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Recovery Metrics")
                    fig = self._plot_recovery_metrics()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                
                with col2:
                    st.subheader("Recovery Projection")
                    fig = self._plot_recovery_projection()
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
        elif analysis_type == "Stress Testing":
            tab1, tab2, tab3 = st.tabs([
                "Scenario Analysis", "Risk Metrics", "Tail Events"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    fig = self._plot_scenario_paths(params)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = self._plot_scenario_distribution(params)
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                self._render_risk_metrics(params)
                
            with tab3:
                self._render_tail_analysis(params)
        
        elif analysis_type == "Sensitivity Analysis":
            if params["analysis_type"] == "One-Way":
                for param in params["selected_params"]:
                    values = np.linspace(
                        parameters[param]['min'],
                        parameters[param]['max'],
                        100
                    )
                    results = self._calculate_sensitivity(param, values)
                    fig = self._plot_one_way_sensitivity(param, values, results)
                    st.plotly_chart(fig, use_container_width=True)
                    
            elif params["analysis_type"] == "Two-Way":
                if len(params["selected_params"]) >= 2:
                    param1, param2 = st.selectbox("Parameter 1", params["selected_params"]), \
                                    st.selectbox("Parameter 2", params["selected_params"])
                    if param1 != param2:
                        fig = self._plot_two_way_sensitivity(
                            param1, param2, parameters
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        else:  # Portfolio Analysis
            tab1, tab2, tab3 = st.tabs([
                "Portfolio Metrics", "Risk Analysis", "Profitability"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    fig = self._plot_portfolio_composition(params)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = self._plot_portfolio_metrics(params)
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                self._render_portfolio_risk_analysis(params)
                
            with tab3:
                self._render_portfolio_profitability(params)
        
        # Footer
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                "<p style='text-align: center; color: #666666;'>"
                " 2024 Actuarial Model Analysis Dashboard. All rights reserved.</p>",
                unsafe_allow_html=True
            )
    
    # ... rest of the code remains the same ...
