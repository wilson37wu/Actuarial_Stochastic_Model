"""
Interactive dashboard for actuarial model analysis.
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Tuple, Optional

# Use absolute imports
from src.dashboard_components import styling
from src.dashboard_components import gcv_analysis
from src.dashboard_components import dividend_analysis
from src.dashboard_components import cash_flow_analysis
from src.dividend_tracker import DividendTracker
from src.gcv_calculator import GCVCalculator, GradingPattern, GCVParameters
from src.visualization import ModelVisualizer
from src.fixed_income import FixedIncomeModel, Bond
from src.public_equity import EquityModel, Equity
from src.liability import LiabilityModel
from src.actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption,
    create_sample_mortality_table, create_sample_lapse_assumption,
    create_sample_inflation_assumption, ActuarialAssumptions
)
from src.investment import (
    InvestmentPortfolio, AssetParameters, AssetClass,
    PortfolioType, InvestmentAssumptions
)
from src.visualizers.gcv_visualizer import GCVVisualizer

@dataclass
class BondParameters:
    """Parameters for bond portfolio."""
    duration: float = 5.0
    credit_quality: str = 'AA'
    yield_rate: float = 0.04

class ModelDashboard:
    """Interactive dashboard for model analysis."""
    
    def __init__(self):
        """Initialize dashboard components."""
        # Initialize core components
        self.tracker = DividendTracker()
        self.calculator = GCVCalculator(
            valuation_rate=0.035,
            parameters=GCVParameters(
                base_percentage=0.7,
                initial_gcv_percentage=0.5,
                grading_years=10,
                minimum_gcv_percentage=0.05,
                grading_pattern=GradingPattern.LINEAR
            )
        )
        self.visualizer = GCVVisualizer(self.calculator)
        
        # Initialize investment components
        self.fixed_income = FixedIncomeModel({
            'default_recovery_rates': {
                'AAA': 0.95, 'AA': 0.90, 'A': 0.85,
                'BBB': 0.75, 'BB': 0.65, 'B': 0.45
            }
        })
        
        # Create sample bond portfolio
        self.bond_portfolio = [
            Bond(
                id='BOND1',
                par_value=1000000,
                coupon_rate=0.04,
                maturity_date=date(2030, 1, 1),
                payment_frequency=2,
                credit_rating='AA',
                issue_date=date(2024, 1, 1),
                purchase_price=1000000
            )
        ]
        # Add bonds to fixed income model
        self.fixed_income.add_bonds(self.bond_portfolio)
        
        self.equity = EquityModel({
            'market_volatility': 0.15,
            'expected_return': 0.08,
            'dividend_yield': 0.02
        })
        
        # Create sample equity portfolio
        self.equity_portfolio = [
            Equity(
                id='STOCK1',
                quantity=10000,
                initial_price=100.0,
                dividend_yield=0.02,
                beta=1.0,
                sector='Technology',
                purchase_date=date(2024, 1, 1)
            )
        ]
        
        # Initialize assumptions
        actuarial_assumptions = ActuarialAssumptions()
        investment_assumptions = InvestmentAssumptions()
        
        # Initialize liability model
        self.liability_model = LiabilityModel(
            mortality_table=create_sample_mortality_table(actuarial_assumptions),
            lapse_assumption=create_sample_lapse_assumption(actuarial_assumptions),
            inflation_assumption=create_sample_inflation_assumption(actuarial_assumptions),
            minimum_dividend_rate=0.01,
            shareholder_cost_rate=0.02
        )
        
        # Initialize investment portfolio
        self.investment_portfolio = InvestmentPortfolio(
            portfolio_type=PortfolioType.BALANCED,
            initial_balance=1000000.0,
            assumptions=investment_assumptions
        )
        
        # Initialize sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize sample data for analysis."""
        np.random.seed(42)  # For reproducibility
        
        # Generate sample policies and their data
        n_policies = 3
        n_periods = 20
        
        for policy_id in range(n_policies):
            policy_number = f"POL{policy_id+1:03d}"
            face_amount = 100000 * (policy_id + 1)  # Different face amounts
            
            # Generate sample asset returns (normally distributed around 7% with 15% volatility)
            asset_returns = np.random.normal(0.07, 0.15, n_periods)
            
            # Calculate dividends for each period
            for period in range(n_periods):
                self.tracker.calculate_dividend(
                    policy_number=policy_number,
                    asset_return=asset_returns[period],
                    face_amount=face_amount,
                    valuation_date=date(2024, 1, 1)  # Sample date
                )

    def _apply_grading_pattern(self, year: int, pattern: GradingPattern) -> float:
        """Apply the specified grading pattern to calculate value for given year."""
        # Set up default stepwise points if using stepwise pattern
        if pattern == GradingPattern.STEPWISE and not self.calculator.parameters.stepwise_points:
            self.calculator.parameters.stepwise_points = {
                0: 1.0,
                5: 0.8,
                10: 0.6,
                15: 0.4,
                20: 0.2,
                25: 0.0
            }
            
        if pattern == GradingPattern.LINEAR:
            # Convert to float to ensure float return type
            return float(max(0, 1.0 - (year / self.calculator.parameters.grading_years)))
        elif pattern == GradingPattern.S_CURVE:
            return self.calculator._apply_s_curve_grading(year)
        elif pattern == GradingPattern.STEPWISE:
            return self.calculator._apply_stepwise_grading(year)
        elif pattern == GradingPattern.EXPONENTIAL:
            return self.calculator._apply_exponential_grading(year)
        elif pattern == GradingPattern.DUAL_PHASE:
            return self.calculator._apply_dual_phase_grading(year)
        elif pattern == GradingPattern.DYNAMIC:
            return self.calculator._apply_dynamic_grading(year)
        elif pattern == GradingPattern.HYBRID:
            return self.calculator._apply_hybrid_grading(year)
        else:
            return float(max(0, 1.0 - (year / self.calculator.parameters.grading_years)))

    def run(self):
        """Run the dashboard."""
        st.title("Actuarial Model Analysis Dashboard")
        
        # Add sidebar for navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox(
            "Choose a section",
            ["GCV Analysis", "Dividend Analysis", "Investment Analysis", 
             "Liability Analysis", "Portfolio Analysis", "Scenario Analysis", "Cash Flow Analysis"]
        )
        
        # Display the selected section
        if page == "GCV Analysis":
            st.header("Guaranteed Cash Value Analysis")
            self._run_gcv_analysis()
        elif page == "Dividend Analysis":
            st.header("Dividend Analysis")
            self._run_dividend_analysis()
        elif page == "Investment Analysis":
            st.header("Investment Analysis")
            self._run_investment_analysis()
        elif page == "Liability Analysis":
            st.header("Liability Analysis")
            self._run_liability_analysis()
        elif page == "Portfolio Analysis":
            st.header("Portfolio Analysis")
            self._run_portfolio_analysis()
        elif page == "Scenario Analysis":
            st.header("Scenario Analysis")
            self._run_scenario_analysis()
        else:  # Cash Flow Analysis
            st.header("Cash Flow Analysis")
            self._run_cash_flow_analysis()

    def _run_gcv_analysis(self):
        """Run GCV analysis section."""
        # Help button at the top
        if st.button("📖 Parameter Guide", key="gcv_help_btn"):
            st.session_state.show_gcv_guide = not st.session_state.get('show_gcv_guide', False)
        
        # Show parameter guide if enabled
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
            
            ### Product Parameters
            - **Annual Premium**: Yearly premium payment
              - Higher premium = higher guaranteed values
              - Typical range varies by face amount
            
            - **Face Amount**: Death benefit amount
              - Base for GCV percentage calculations
              - Typical range: 5-20x annual premium
            
            - **Valuation Rate** (2-5%)
              - Interest rate for present value calculations
              - Higher rate reduces present values
            """)
            st.markdown("---")  # Add separator after guide
        
        # Parameters
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("GCV Parameters")
            base_percentage = st.slider(
                "Base Percentage",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                key="base_percentage"
            )
            initial_gcv = st.slider(
                "Initial GCV Percentage",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                key="initial_gcv"
            )
            grading_years = st.slider(
                "Grading Years",
                min_value=5,
                max_value=30,
                value=10,
                step=1,
                key="grading_years"
            )
            min_gcv = st.slider(
                "Minimum GCV Percentage",
                min_value=0.0,
                max_value=0.5,
                value=0.05,
                step=0.05,
                key="min_gcv"
            )
            
            pattern = st.selectbox(
                "Grading Pattern",
                options=[p.name for p in GradingPattern],
                index=0,
                key="pattern"
            )
        
        with col2:
            st.subheader("Product Parameters")
            premium = st.number_input(
                "Annual Premium",
                min_value=1000,
                max_value=1000000,
                value=10000,
                step=1000,
                key="premium"
            )
            face_amount = st.number_input(
                "Face Amount",
                min_value=10000,
                max_value=10000000,
                value=100000,
                step=10000,
                key="face_amount"
            )
            valuation_rate = st.slider(
                "Valuation Rate",
                min_value=0.01,
                max_value=0.10,
                value=0.035,
                step=0.005,
                format="%.3f",
                key="valuation_rate"
            )
        
        # Add Calculate button
        if st.button("Calculate GCV", key="calculate_gcv"):
            # Update calculator parameters
            self.calculator.parameters = GCVParameters(
                base_percentage=base_percentage,
                initial_gcv_percentage=initial_gcv,
                grading_years=grading_years,
                minimum_gcv_percentage=min_gcv,
                grading_pattern=GradingPattern[pattern]
            )
            self.calculator.valuation_rate = valuation_rate
            
            # Calculate GCV for multiple policy years
            gcv_values = []
            for year in range(1, 21):  # Calculate for 20 years
                gcv_value = self.calculator.calculate_gcv(
                    sex='M',  # Assuming male for this example
                    policy_year=year,
                    premium=st.session_state.get('premium', 5000),
                    face_amount=st.session_state.get('face_amount', 100000),
                    pv_premium=st.session_state.get('premium', 5000) / (1 + st.session_state.get('interest_rate', 0.04))
                )
                gcv_values.append({'Year': year, 'GCV Value': gcv_value})
            
            gcv_results_df = pd.DataFrame(gcv_values)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Initial GCV", f"{gcv_results_df['GCV Value'].iloc[0]:.2%}")
            with col2:
                st.metric("Mid-Point GCV", f"{gcv_results_df['GCV Value'].iloc[10]:.2%}")
            with col3:
                st.metric("Final GCV", f"{gcv_results_df['GCV Value'].iloc[-1]:.2%}")
            with col4:
                st.metric("Average GCV", f"{gcv_results_df['GCV Value'].mean():.2%}")
            
            # Display analysis
            st.subheader("Analysis Results")
            tab1, tab2, tab3 = st.tabs(["GCV Patterns", "3D Surface", "Pattern Derivatives"])
            
            with tab1:
                st.plotly_chart(self._plot_gcv_patterns(max_years=30), use_container_width=True)
                
            with tab2:
                st.plotly_chart(self._plot_3d_gcv_surface(), use_container_width=True)
                
            with tab3:
                st.plotly_chart(self._plot_pattern_derivatives(max_years=30), use_container_width=True)

    def _run_dividend_analysis(self):
        """Run dividend analysis section."""
        st.subheader("Dividend Analysis Parameters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            n_policies = st.number_input("Number of Policies", 1, 10, 3, key="n_policies")
        with col2:
            n_periods = st.number_input("Number of Periods", 5, 100, 20, key="n_periods")
        with col3:
            min_return = st.slider("Minimum Return", -0.10, 0.0, -0.05, step=0.01, key="min_return")
        
        if st.button("Calculate Dividends", key="calculate_dividends"):
            # Reset tracker
            self.tracker.reset()
            
            # Generate policies and calculate dividends
            for i in range(n_policies):
                policy_number = f"POL_{i+1}"
                self.tracker.initialize_account(policy_number)
                
                # Generate returns and calculate dividends for each period
                returns = np.random.normal(0.06, 0.12, n_periods)
                returns = np.maximum(returns, min_return)  # Apply minimum return
                
                for t, ret in enumerate(returns):
                    # Calculate dividend for this period
                    self.tracker.calculate_dividend(
                        policy_number=policy_number,
                        asset_return=ret,
                        face_amount=100000,  # Example face amount
                        valuation_date=date(2024, 1, 1)  # Example date
                    )
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Return", f"{self.tracker.get_average_return():.2%}")
            with col2:
                st.metric("Total Dividends", f"${self.tracker.get_total_dividends():,.2f}")
            with col3:
                active_policies = len([acc for acc in self.tracker.accounts.values() 
                                    if len(acc.dividend_history) > 0])
                st.metric("Policies with Dividends", f"{active_policies}/{n_policies}")
            with col4:
                avg_dividend = (self.tracker.get_total_dividends() / n_policies 
                              if n_policies > 0 else 0)
                st.metric("Average Dividend per Policy", f"${avg_dividend:,.2f}")
            
            # Visualization area
            st.subheader("Analysis Results")
            tab1, tab2, tab3 = st.tabs(["Returns vs Dividends", "Tracking Balance", "Recovery Metrics"])
            
            with tab1:
                fig = self._plot_returns_vs_dividends()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig = self._plot_tracking_balance()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                fig = self._plot_recovery_metrics()
                st.plotly_chart(fig, use_container_width=True)

    def _plot_returns_vs_dividends(self):
        """Plot returns vs dividends relationship with high contrast colors."""
        returns = self.tracker.get_returns()
        dividends = self.tracker.get_dividends()
        periods = list(range(1, len(returns) + 1))
        
        fig = go.Figure()
        
        # Add returns line
        fig.add_trace(go.Scatter(
            x=periods,
            y=returns,
            name='Returns',
            line=dict(color='#FF0000', width=2),  # Bright red
            mode='lines+markers'
        ))
        
        # Add dividends line
        fig.add_trace(go.Scatter(
            x=periods,
            y=dividends,
            name='Dividends',
            line=dict(color='#0000FF', width=2),  # Bright blue
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Investment Returns vs Dividends',
            xaxis_title='Period',
            yaxis_title='Rate',
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        # Add grid lines
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        return fig

    def _plot_tracking_balance(self):
        """Plot tracking account balance with high contrast colors."""
        balances = self.tracker.get_tracking_balances()
        periods = list(range(1, len(balances) + 1))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=periods,
            y=balances,
            name='Balance',
            line=dict(color='#00AA00', width=2),  # Bright green
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(0, 170, 0, 0.1)'  # Light green fill
        ))
        
        fig.update_layout(
            title='Tracking Account Balance',
            xaxis_title='Period',
            yaxis_title='Balance ($)',
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12)
        )
        
        # Add grid lines
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        return fig

    def _plot_recovery_metrics(self):
        """Plot recovery metrics with high contrast colors."""
        metrics = self.tracker.analyze_recovery_metrics(policy_number="POL_1")  # Example policy number
        
        if not metrics:
            return go.Figure()
        
        fig = go.Figure()
        
        # Add recovery efficiency line
        recovery_efficiency = metrics.get('recovery_efficiency', 0)
        fig.add_trace(go.Scatter(
            x=[0],
            y=[recovery_efficiency],
            name='Recovery Efficiency',
            line=dict(color='#AA00AA', width=2),  # Bright purple
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Recovery Metrics Over Time',
            xaxis_title='Period',
            yaxis_title='Metric Value',
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12)
        )
        
        # Add grid lines
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        return fig

    def _run_investment_analysis(self):
        """Run investment analysis section."""
        st.subheader("Investment Analysis Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fixed Income Portfolio")
            duration = st.slider("Duration (Years)", 1.0, 10.0, 5.0, key="fi_duration")
            credit_quality = st.selectbox(
                "Credit Quality", 
                ["AAA", "AA", "A", "BBB"],
                key="fi_credit_quality"
            )
            yield_rate = st.slider(
                "Yield Rate", 
                0.01, 0.10, 0.04, 
                step=0.01,
                key="fi_yield_rate"
            )
            
        with col2:
            st.subheader("Equity Portfolio")
            expected_return = st.slider(
                "Expected Return", 
                0.05, 0.15, 0.08, 
                step=0.01,
                key="eq_expected_return"
            )
            volatility = st.slider(
                "Volatility", 
                0.10, 0.30, 0.15, 
                step=0.01,
                key="eq_volatility"
            )
            dividend_yield = st.slider(
                "Dividend Yield", 
                0.01, 0.05, 0.02, 
                step=0.01,
                key="eq_dividend_yield"
            )

        if st.button("Calculate Returns", key="calculate_returns"):
            # Update fixed income parameters
            self.fixed_income.update_parameters({
                'default_recovery_rates': {
                    'AAA': 0.95, 'AA': 0.90, 'A': 0.85,
                    'BBB': 0.75, 'BB': 0.65, 'B': 0.45
                }
            })
            
            # Update equity parameters
            self.equity.update_parameters({
                'market_volatility': volatility,
                'expected_return': expected_return,
                'dividend_yield': dividend_yield
            })
            
            # Display results
            st.subheader("Analysis Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Fixed Income Returns")
                fixed_income_returns = self.fixed_income.project_returns(n_periods=12)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(1, 13)),
                    y=fixed_income_returns,
                    name='Fixed Income',
                    line=dict(color='#00AA00', width=2),  # Bright green
                    mode='lines+markers'
                ))
                fig.update_layout(
                    title='Projected Fixed Income Returns',
                    xaxis_title='Month',
                    yaxis_title='Return',
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Equity Returns")
                equity_returns = self.equity.project_returns(n_periods=12)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(1, 13)),
                    y=equity_returns,
                    name='Equity',
                    line=dict(color='#FF0000', width=2),  # Bright red
                    mode='lines+markers'
                ))
                fig.update_layout(
                    title='Projected Equity Returns',
                    xaxis_title='Month',
                    yaxis_title='Return',
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                st.plotly_chart(fig, use_container_width=True)

    def _run_liability_analysis(self):
        """Run liability analysis section."""
        st.subheader("Liability Model Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mortality_multiplier = st.slider("Mortality Multiplier", 0.5, 1.5, 1.0)
            self.liability_model.mortality_table.set_multiplier(mortality_multiplier)
        
        with col2:
            lapse_rate = st.slider("Base Lapse Rate", 0.01, 0.10, 0.03)
            self.liability_model.lapse_assumption.set_base_rate(lapse_rate)
        
        with col3:
            inflation_rate = st.slider("Inflation Rate", 0.01, 0.05, 0.02)
            self.liability_model.inflation_assumption.set_rate(inflation_rate)
        
        # Project liabilities
        liability_projection = self.liability_model.project_liabilities(n_years=30)
        
        # Create line chart with specific columns
        st.line_chart(
            liability_projection,
            x='Date',
            y=['Net_Liability', 'PV_Liability']
        )
        
        # Show detailed cash flow components
        st.subheader("Cash Flow Components")
        components_to_plot = [
            'Premium', 'Death_Benefit', 'Surrender', 'Expenses',
            'Dividends', 'Policy_Loans', 'Loan_Repayments', 'Withdrawals'
        ]
        st.line_chart(
            liability_projection,
            x='Date',
            y=components_to_plot
        )
    
    def _run_portfolio_analysis(self):
        """Run portfolio analysis section."""
        st.subheader("Portfolio Allocation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            equity_allocation = st.slider("Equity Allocation", 0.0, 1.0, 0.6)
            fixed_income_allocation = 1.0 - equity_allocation
            
            # Split equity between large and small cap
            large_cap_ratio = 0.7  # 70% large cap, 30% small cap
            small_cap_ratio = 0.3
            
            # Split fixed income between gov and corp bonds
            gov_bond_ratio = 0.5  # 50-50 split
            corp_bond_ratio = 0.5
            
            self.investment_portfolio.update_allocation({
                AssetClass.LARGE_CAP_EQUITY: equity_allocation * large_cap_ratio,
                AssetClass.SMALL_CAP_EQUITY: equity_allocation * small_cap_ratio,
                AssetClass.GOVERNMENT_BOND: fixed_income_allocation * gov_bond_ratio,
                AssetClass.CORPORATE_BOND: fixed_income_allocation * corp_bond_ratio
            })
            
            # Show current allocation
            fig = go.Figure(data=[go.Pie(
                labels=["Large Cap Equity", "Small Cap Equity", 
                       "Government Bonds", "Corporate Bonds"],
                values=[equity_allocation * large_cap_ratio,
                       equity_allocation * small_cap_ratio,
                       fixed_income_allocation * gov_bond_ratio,
                       fixed_income_allocation * corp_bond_ratio]
            )])
            st.plotly_chart(fig)
        
        with col2:
            st.subheader("Portfolio Metrics")
            metrics = self.investment_portfolio.get_portfolio_metrics()
            
            st.write(f"Expected Return: {metrics['expected_return']:.1%}")
            st.write(f"Portfolio Risk: {metrics['volatility']:.1%}")
            st.write(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

    def _run_scenario_analysis(self):
        """Run scenario analysis section."""
        st.subheader("Scenario Analysis")
        
        scenario_type = st.selectbox(
            "Scenario Type",
            ["Base Case", "Stress Test", "Best Case", "Worst Case"]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            n_years = st.slider("Projection Years", 1, 30, 10)
            n_scenarios = st.slider("Number of Scenarios", 100, 1000, 500)
        
        # Run scenarios
        scenario_params = {
            'Parameters': [
                'Base Scenario',
                'Time Horizon',
                'Confidence Level'
            ],
            'Value': [
                'Current Market',
                st.session_state.get('time_horizon', 5),
                st.session_state.get('confidence_level', 0.95)
            ]
        }
        scenario_params_df = pd.DataFrame(scenario_params)

        # Generate scenario results
        n_periods = st.session_state.get('time_horizon', 5) * 12
        scenario_data = []
        
        # Base scenario
        base_return = self.investment_portfolio.calculate_expected_return()
        scenario_data.append({
            'Scenario': 'Base',
            'Expected Return': base_return,
            'Risk': self.investment_portfolio.calculate_volatility(),
            'VaR': self.investment_portfolio.calculate_var()
        })
        
        # Stress scenarios
        stress_scenarios = {
            'Recession': {'return_mult': 0.5, 'vol_mult': 2.0},
            'Recovery': {'return_mult': 1.5, 'vol_mult': 0.8}
        }
        
        for scenario, mults in stress_scenarios.items():
            scenario_data.append({
                'Scenario': scenario,
                'Expected Return': base_return * mults['return_mult'],
                'Risk': self.investment_portfolio.calculate_volatility() * mults['vol_mult'],
                'VaR': self.investment_portfolio.calculate_var() * mults['vol_mult']
            })
        
        scenario_results_df = pd.DataFrame(scenario_data)
        
        # Plot scenario results
        fig = go.Figure()
        for i in range(min(10, n_scenarios)):  # Plot first 10 scenarios
            fig.add_trace(go.Scatter(
                y=np.random.normal(0, 1, n_periods),  # Use correct column names
                mode='lines',
                name=f'Scenario {i+1}',
                opacity=0.3
            ))
        
        fig.add_trace(go.Scatter(
            y=np.mean(np.random.normal(0, 1, (n_scenarios, n_periods)), axis=0),
            mode='lines',
            name='Mean',
            line=dict(color='red', width=2)
        ))
        
        st.plotly_chart(fig)

    def _run_cash_flow_analysis(self):
        """Run cash flow analysis section."""
        cash_flow_model = self.investment_portfolio.get_cash_flow_model()
        asset_model = self.investment_portfolio.get_asset_model()
        render_cash_flow_analysis(cash_flow_model, asset_model)

    def _plot_gcv_patterns(self, max_years: int = 30) -> go.Figure:
        """Plot GCV patterns comparison."""
        years = np.arange(max_years + 1)
        fig = go.Figure()
        
        for pattern in GradingPattern:
            values = [self._apply_grading_pattern(year, pattern) for year in years]
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                name=pattern.name,
                mode='lines',
            ))
        
        fig.update_layout(
            title="GCV Grading Patterns Comparison",
            xaxis_title="Policy Year",
            yaxis_title="GCV Factor",
            showlegend=True
        )
        return fig
    
    def _plot_3d_gcv_surface(self) -> go.Figure:
        """Create 3D surface plot of GCV values."""
        years = np.linspace(0, 30, 31)
        rates = np.linspace(0.01, 0.10, 10)
        X, Y = np.meshgrid(years, rates)
        Z = np.zeros_like(X)
        
        for i in range(len(years)):
            for j in range(len(rates)):
                # Store original valuation rate
                orig_rate = self.calculator.valuation_rate
                # Update rate temporarily
                self.calculator.valuation_rate = rates[j]
                # Calculate GCV
                Z[j,i] = self._apply_grading_pattern(int(years[i]), self.calculator.parameters.grading_pattern)
                # Restore original rate
                self.calculator.valuation_rate = orig_rate
        
        fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z)])
        fig.update_layout(
            title='GCV Surface Analysis',
            scene=dict(
                xaxis_title='Policy Year',
                yaxis_title='Interest Rate',
                zaxis_title='GCV Factor'
            ),
            width=800,
            height=800
        )
        return fig
    
    def _plot_pattern_derivatives(self, max_years: int = 30) -> go.Figure:
        """Plot pattern derivatives."""
        years = np.arange(max_years)
        fig = go.Figure()
        
        for pattern in GradingPattern:
            # Calculate derivatives using central differences
            values = [self._apply_grading_pattern(year, pattern) for year in years]
            derivatives = np.gradient(values)
            
            fig.add_trace(go.Scatter(
                x=years,
                y=derivatives,
                name=pattern.name,
                mode='lines',
            ))
        
        fig.update_layout(
            title="GCV Pattern Derivatives",
            xaxis_title="Policy Year",
            yaxis_title="Rate of Change",
            showlegend=True
        )
        return fig

    def _plot_mixed_pattern(self, weights: Dict[str, float], max_years: int = 30) -> go.Figure:
        """Plot mixed GCV pattern."""
        years = np.arange(max_years)
        mixed_values = np.zeros(max_years)
        
        for pattern_name, weight in weights.items():
            pattern = GradingPattern.__members__[pattern_name]
            mixed_values += np.array([
                self._apply_grading_pattern(year, pattern)
                for year in years
            ]) * weight
        
        return self.visualizer.plot_gcv_patterns(
            {'Mixed Pattern': mixed_values.tolist()},
            years
        )
    
    def _plot_product_variant_gcv(self,
                                premium: float,
                                face_amount: float,
                                pv_premium: float,
                                max_years: int = 30) -> go.Figure:
        """Plot GCV values for different product variants."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_variant_comparison(self) -> go.Figure:
        """Plot variant comparison."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_parameter_sensitivity(self) -> go.Figure:
        """Plot parameter sensitivity."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_two_way_sensitivity(self) -> go.Figure:
        """Plot two-way sensitivity analysis."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_historical_trends(self) -> go.Figure:
        """Plot historical trends."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_pattern_evolution(self) -> go.Figure:
        """Plot pattern evolution."""
        # Placeholder implementation
        return go.Figure()
    
    def _plot_3d_surface(self, X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> go.Figure:
        """Plot 3D surface."""
        return self.visualizer.plot_3d_surface(
            X, Y, Z,
            title='GCV Surface Analysis',
            x_label='Policy Year',
            y_label='Interest Rate',
            z_label='GCV Factor'
        )
    
    def _plot_dividend_analysis(self,
                              returns: List[float],
                              dividends: List[float],
                              periods: List[int]) -> Tuple[go.Figure, go.Figure]:
        """Plot dividend analysis."""
        return self.visualizer.plot_dividend_analysis(returns, dividends, periods)
    
    def _plot_portfolio_composition(self,
                                  products: Dict[str, float],
                                  metrics: Dict[str, float]) -> go.Figure:
        """Plot portfolio composition."""
        return self.visualizer.plot_portfolio_composition(products, metrics)
    
    def _plot_sensitivity_analysis(self,
                                 parameter: str,
                                 values: np.ndarray,
                                 results: np.ndarray,
                                 baseline: Optional[float] = None) -> go.Figure:
        """Plot sensitivity analysis."""
        return self.visualizer.plot_sensitivity_analysis(
            parameter, values, results, baseline
        )

    def export_to_excel(self):
        """Export all dashboard results to an Excel file with enhanced formatting."""
        current_time = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f'actuarial_analysis_results_{current_time}.xlsx'

        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 12,
                'bg_color': '#4B0082',  # Dark purple
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            subheader_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'bg_color': '#E6E6FA',  # Light purple
                'border': 1
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0.00',
                'border': 1
            })
            
            percent_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })

            # 1. GCV Analysis Sheet
            gcv_params = {
                'Parameters': [
                    'Face Amount',
                    'Premium',
                    'Interest Rate',
                    'Expense Rate',
                    'Mortality Rate'
                ],
                'Value': [
                    st.session_state.get('face_amount', 100000),
                    st.session_state.get('premium', 5000),
                    st.session_state.get('interest_rate', 0.04),
                    st.session_state.get('expense_rate', 0.05),
                    st.session_state.get('mortality_rate', 0.003)
                ]
            }
            gcv_params_df = pd.DataFrame(gcv_params)
            
            # Calculate GCV for multiple policy years
            gcv_values = []
            for year in range(1, 21):  # Calculate for 20 years
                gcv_value = self.calculator.calculate_gcv(
                    sex='M',  # Assuming male for this example
                    policy_year=year,
                    premium=st.session_state.get('premium', 5000),
                    face_amount=st.session_state.get('face_amount', 100000),
                    pv_premium=st.session_state.get('premium', 5000) / (1 + st.session_state.get('interest_rate', 0.04))
                )
                gcv_values.append({'Year': year, 'GCV Value': gcv_value})
            
            gcv_results_df = pd.DataFrame(gcv_values)

            self._write_to_excel(
                writer, 'GCV Analysis', 
                [('Parameters', gcv_params_df), ('Results', gcv_results_df)],
                header_format, number_format, percent_format, currency_format
            )

            # 2. Dividend Analysis Sheet
            dividend_params = {
                'Parameter': ['Number of Policies', 'Number of Periods', 'Minimum Return'],
                'Value': [
                    st.session_state.get('n_policies', 3),
                    st.session_state.get('n_periods', 20),
                    st.session_state.get('min_return', -0.05)
                ]
            }
            dividend_params_df = pd.DataFrame(dividend_params)
            
            dividend_results = {
                'Metric': [
                    'Average Return',
                    'Total Dividends',
                    'Policies with Dividends',
                    'Average Dividend per Policy'
                ],
                'Value': [
                    self.tracker.get_average_return(),
                    self.tracker.get_total_dividends(),
                    len([acc for acc in self.tracker.accounts.values() 
                         if len(acc.dividend_history) > 0]),
                    self.tracker.get_total_dividends() / len(self.tracker.accounts) 
                    if self.tracker.accounts else 0
                ]
            }
            dividend_results_df = pd.DataFrame(dividend_results)

            self._write_to_excel(
                writer, 'Dividend Analysis',
                [('Parameters', dividend_params_df), ('Results', dividend_results_df)],
                header_format, number_format, percent_format, currency_format
            )

            # 3. Investment Analysis Sheet
            investment_params = {
                'Parameter': [
                    'Duration (Years)',
                    'Credit Quality',
                    'Yield Rate',
                    'Expected Return',
                    'Volatility',
                    'Dividend Yield'
                ],
                'Value': [
                    st.session_state.get('fi_duration', 5.0),
                    st.session_state.get('fi_credit_quality', 'AA'),
                    st.session_state.get('fi_yield_rate', 0.04),
                    st.session_state.get('eq_expected_return', 0.08),
                    st.session_state.get('eq_volatility', 0.15),
                    st.session_state.get('eq_dividend_yield', 0.02)
                ]
            }
            investment_params_df = pd.DataFrame(investment_params)

            returns_data = {
                'Period': list(range(1, 13)),
                'Fixed Income Returns': self.fixed_income.project_returns(n_periods=12),
                'Equity Returns': self.equity.project_returns(n_periods=12)
            }
            returns_df = pd.DataFrame(returns_data)

            self._write_to_excel(
                writer, 'Investment Analysis',
                [('Parameters', investment_params_df), ('Returns', returns_df)],
                header_format, number_format, percent_format, currency_format
            )

            # 4. Portfolio Analysis Sheet
            portfolio_params = {
                'Parameter': [
                    'Fixed Income Allocation',
                    'Equity Allocation',
                    'Rebalancing Frequency',
                    'Risk Tolerance'
                ],
                'Value': [
                    st.session_state.get('fi_allocation', 0.6),
                    st.session_state.get('eq_allocation', 0.4),
                    st.session_state.get('rebalancing_freq', 'Quarterly'),
                    st.session_state.get('risk_tolerance', 'Medium')
                ]
            }
            portfolio_params_df = pd.DataFrame(portfolio_params)

            portfolio_metrics = {
                'Metric': [
                    'Expected Return',
                    'Portfolio Volatility',
                    'Sharpe Ratio',
                    'Value at Risk (95%)'
                ],
                'Value': [
                    self.investment_portfolio.calculate_expected_return(),
                    self.investment_portfolio.calculate_volatility(),
                    self.investment_portfolio.calculate_sharpe_ratio(),
                    self.investment_portfolio.calculate_var()
                ]
            }
            portfolio_metrics_df = pd.DataFrame(portfolio_metrics)

            self._write_to_excel(
                writer, 'Portfolio Analysis',
                [('Parameters', portfolio_params_df), ('Metrics', portfolio_metrics_df)],
                header_format, number_format, percent_format, currency_format
            )

            # 5. Scenario Analysis Sheet
            scenario_params = {
                'Parameter': [
                    'Base Scenario',
                    'Time Horizon',
                    'Confidence Level'
                ],
                'Value': [
                    'Current Market',
                    st.session_state.get('time_horizon', 5),
                    st.session_state.get('confidence_level', 0.95)
                ]
            }
            scenario_params_df = pd.DataFrame(scenario_params)

            scenario_results = {
                'Scenario': ['Base', 'Recession', 'Recovery'],
                'Expected Return': [self.investment_portfolio.calculate_expected_return(),
                                   self.investment_portfolio.calculate_expected_return() * 0.5,
                                   self.investment_portfolio.calculate_expected_return() * 1.5],
                'Risk': [self.investment_portfolio.calculate_volatility(),
                        self.investment_portfolio.calculate_volatility() * 2.0,
                        self.investment_portfolio.calculate_volatility() * 0.8],
                'VaR': [self.investment_portfolio.calculate_var(),
                       self.investment_portfolio.calculate_var() * 2.0,
                       self.investment_portfolio.calculate_var() * 0.8]
            }
            scenario_results_df = pd.DataFrame(scenario_results)

            self._write_to_excel(
                writer, 'Scenario Analysis',
                [('Parameters', scenario_params_df), ('Results', scenario_results_df)],
                header_format, number_format, percent_format, currency_format
            )

        st.success(f'Results exported to {filename} with enhanced formatting')

    def _prepare_dataframe(self, df):
        """Prepare DataFrame for Excel export by converting all values to appropriate types."""
        def convert_cell(val):
            if isinstance(val, list):
                return ', '.join(str(x) for x in val)
            if isinstance(val, (int, float)):
                return float(val)
            if val is None:
                return ''
            return str(val)
        
        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Convert all values in the DataFrame
        for col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(convert_cell)
        
        return df_copy

    def _write_to_excel(self, writer, sheet_name, data_sections, header_format, 
                       number_format, percent_format, currency_format):
        """Helper method to write a section to Excel with consistent formatting."""
        # Create worksheet if it doesn't exist
        if sheet_name not in writer.sheets:
            workbook = writer.book
            worksheet = workbook.add_worksheet(sheet_name)
            writer.sheets[sheet_name] = worksheet
        else:
            worksheet = writer.sheets[sheet_name]
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:Z', 15)
        
        current_row = 0
        
        for section_name, df in data_sections:
            # Prepare data
            df = self._prepare_dataframe(df)
            
            # Write section header
            worksheet.write(current_row, 0, f'{sheet_name} - {section_name}', header_format)
            current_row += 1
            
            # Write column headers
            for col_idx, col in enumerate(df.columns):
                worksheet.write(current_row, col_idx, str(col), header_format)
            current_row += 1
            
            # Write data
            for row_idx, row in df.iterrows():
                for col_idx, (col_name, value) in enumerate(row.items()):
                    try:
                        # Try to convert to float for numeric columns
                        if isinstance(value, str) and any(x in col_name.lower() for x in ['rate', 'return', 'amount', 'value']):
                            try:
                                value = float(value.replace('%', '').replace('$', '').replace(',', ''))
                            except (ValueError, TypeError):
                                pass
                        
                        # Apply appropriate format
                        if isinstance(value, (int, float)):
                            if any(x in col_name.lower() for x in ['rate', 'return', 'percentage']):
                                worksheet.write_number(current_row + row_idx, col_idx, value, percent_format)
                            elif any(x in col_name.lower() for x in ['amount', 'value', 'premium']):
                                worksheet.write_number(current_row + row_idx, col_idx, value, currency_format)
                            else:
                                worksheet.write_number(current_row + row_idx, col_idx, value, number_format)
                        else:
                            worksheet.write_string(current_row + row_idx, col_idx, str(value), number_format)
                    except Exception as e:
                        # If any error occurs, write as string
                        worksheet.write_string(current_row + row_idx, col_idx, str(value), number_format)
            
            current_row += len(df) + 2  # Add space between sections

    def _prepare_gcv_data(self):
        """Prepare GCV data for Excel export."""
        params_df = pd.DataFrame({
            'Parameter': ['Face Amount', 'Premium', 'Interest Rate', 'Expense Rate', 'Mortality Rate'],
            'Value': [
                st.session_state.get('face_amount', 100000),
                st.session_state.get('premium', 5000),
                st.session_state.get('interest_rate', 0.04),
                st.session_state.get('expense_rate', 0.05),
                st.session_state.get('mortality_rate', 0.003)
            ]
        })
        
        results = []
        for year in range(1, 21):
            gcv_value = self.calculator.calculate_gcv(
                sex='M',
                policy_year=year,
                premium=st.session_state.get('premium', 5000),
                face_amount=st.session_state.get('face_amount', 100000),
                pv_premium=st.session_state.get('premium', 5000) / (1 + st.session_state.get('interest_rate', 0.04))
            )
            results.append({'Year': year, 'GCV Value': gcv_value})
        
        results_df = pd.DataFrame(results)
        
        return [('Parameters', params_df), ('Results', results_df)]

    def _prepare_dividend_data(self):
        """Prepare dividend data for Excel export."""
        params_df = pd.DataFrame({
            'Parameter': ['Number of Policies', 'Number of Periods', 'Minimum Return'],
            'Value': [
                st.session_state.get('n_policies', 3),
                st.session_state.get('n_periods', 20),
                st.session_state.get('min_return', -0.05)
            ]
        })
        
        results_df = pd.DataFrame({
            'Metric': [
                'Average Return',
                'Total Dividends',
                'Policies with Dividends',
                'Average Dividend per Policy'
            ],
            'Value': [
                self.tracker.get_average_return(),
                self.tracker.get_total_dividends(),
                len([acc for acc in self.tracker.accounts.values() 
                     if len(acc.dividend_history) > 0]),
                self.tracker.get_total_dividends() / len(self.tracker.accounts) 
                if self.tracker.accounts else 0
            ]
        })
        
        return [('Parameters', params_df), ('Results', results_df)]

    def _prepare_investment_data(self):
        """Prepare investment data for Excel export."""
        params_df = pd.DataFrame({
            'Parameter': [
                'Duration (Years)',
                'Credit Quality',
                'Yield Rate',
                'Expected Return',
                'Volatility',
                'Dividend Yield'
            ],
            'Value': [
                st.session_state.get('fi_duration', 5.0),
                st.session_state.get('fi_credit_quality', 'AA'),
                st.session_state.get('fi_yield_rate', 0.04),
                st.session_state.get('eq_expected_return', 0.08),
                st.session_state.get('eq_volatility', 0.15),
                st.session_state.get('eq_dividend_yield', 0.02)
            ]
        })
        
        returns_df = pd.DataFrame({
            'Period': list(range(1, 13)),
            'Fixed Income Returns': self.fixed_income.project_returns(n_periods=12),
            'Equity Returns': self.equity.project_returns(n_periods=12)
        })
        
        return [('Parameters', params_df), ('Returns', returns_df)]

    def _prepare_portfolio_data(self):
        """Prepare portfolio data for Excel export."""
        params_df = pd.DataFrame({
            'Parameter': [
                'Fixed Income Allocation',
                'Equity Allocation',
                'Rebalancing Frequency',
                'Risk Tolerance'
            ],
            'Value': [
                st.session_state.get('fi_allocation', 0.6),
                st.session_state.get('eq_allocation', 0.4),
                st.session_state.get('rebalancing_freq', 'Quarterly'),
                st.session_state.get('risk_tolerance', 'Medium')
            ]
        })
        
        metrics_df = pd.DataFrame({
            'Metric': [
                'Expected Return',
                'Portfolio Volatility',
                'Sharpe Ratio',
                'Value at Risk (95%)'
            ],
            'Value': [
                self.investment_portfolio.calculate_expected_return(),
                self.investment_portfolio.calculate_volatility(),
                self.investment_portfolio.calculate_sharpe_ratio(),
                self.investment_portfolio.calculate_var()
            ]
        })
        
        return [('Parameters', params_df), ('Metrics', metrics_df)]

    def _prepare_scenario_data(self):
        """Prepare scenario data for Excel export."""
        params_df = pd.DataFrame({
            'Parameter': ['Base Scenario', 'Time Horizon', 'Confidence Level'],
            'Value': [
                'Current Market',
                st.session_state.get('time_horizon', 5),
                st.session_state.get('confidence_level', 0.95)
            ]
        })
        
        base_return = self.investment_portfolio.calculate_expected_return()
        base_vol = self.investment_portfolio.calculate_volatility()
        base_var = self.investment_portfolio.calculate_var()
        
        scenarios_df = pd.DataFrame({
            'Scenario': ['Base', 'Recession', 'Recovery'],
            'Expected Return': [
                base_return,
                base_return * 0.5,
                base_return * 1.5
            ],
            'Risk': [
                base_vol,
                base_vol * 2.0,
                base_vol * 0.8
            ],
            'VaR': [
                base_var,
                base_var * 2.0,
                base_var * 0.8
            ]
        })
        
        return [('Parameters', params_df), ('Scenarios', scenarios_df)]

    def run_with_export(self):
        """Run the dashboard with export functionality."""
        st.title("Actuarial Model Analysis Dashboard")
        
        # Add sidebar for navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox(
            "Choose a section",
            ["GCV Analysis", "Dividend Analysis", "Investment Analysis", 
             "Liability Analysis", "Portfolio Analysis", "Scenario Analysis", "Cash Flow Analysis"]
        )
        
        # Display the selected section
        if page == "GCV Analysis":
            st.header("Guaranteed Cash Value Analysis")
            self._run_gcv_analysis()
        elif page == "Dividend Analysis":
            st.header("Dividend Analysis")
            self._run_dividend_analysis()
        elif page == "Investment Analysis":
            st.header("Investment Analysis")
            self._run_investment_analysis()
        elif page == "Liability Analysis":
            st.header("Liability Analysis")
            self._run_liability_analysis()
        elif page == "Portfolio Analysis":
            st.header("Portfolio Analysis")
            self._run_portfolio_analysis()
        elif page == "Scenario Analysis":
            st.header("Scenario Analysis")
            self._run_scenario_analysis()
        else:  # Cash Flow Analysis
            st.header("Cash Flow Analysis")
            self._run_cash_flow_analysis()

        # Add export button
        if st.button('Export to Excel'):
            self.export_to_excel()

def main():
    st.error_container = st.empty()

    def update_error_status(error):
        st.error_container.error(f"🚨 System Error: {str(error)}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Actuarial Model Analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    from dashboard_components.cash_flow_analysis import render_cash_flow_analysis
    
    dashboard = ModelDashboard()
    dashboard.run_with_export()
    main()
