"""
Interactive dashboard for actuarial model analysis.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Tuple, Optional
from src.dashboard_components import styling
from src.dashboard_components import gcv_analysis
from src.dashboard_components import dividend_analysis
from src.dividend_tracker import DividendTracker
from src.gcv_calculator import GCVCalculator, GradingPattern, GCVParameters
from src.visualization import ModelVisualizer
from src.fixed_income import FixedIncomeModel, Bond
from src.public_equity import EquityModel, Equity
from src.liability import LiabilityModel
from src.actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption,
    create_sample_mortality_table, create_sample_lapse_assumption,
    create_sample_inflation_assumption
)
from src.investment import InvestmentPortfolio, AssetParameters, AssetClass

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
        self.visualizer = ModelVisualizer()
        
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
        
        # Initialize liability model
        self.liability_model = LiabilityModel(
            mortality_table=create_sample_mortality_table(),
            lapse_assumption=create_sample_lapse_assumption(),
            inflation_assumption=create_sample_inflation_assumption(),
            minimum_dividend_rate=0.01,
            shareholder_cost_rate=0.02
        )
        
        # Initialize investment portfolio
        self.investment_portfolio = InvestmentPortfolio(
            initial_allocation={
                AssetClass.LARGE_CAP_EQUITY: 0.4,
                AssetClass.SMALL_CAP_EQUITY: 0.2,
                AssetClass.GOVERNMENT_BOND: 0.2,
                AssetClass.CORPORATE_BOND: 0.2
            },
            asset_params={
                AssetClass.LARGE_CAP_EQUITY: AssetParameters(expected_return=0.08, volatility=0.15),
                AssetClass.SMALL_CAP_EQUITY: AssetParameters(expected_return=0.10, volatility=0.20),
                AssetClass.GOVERNMENT_BOND: AssetParameters(expected_return=0.03, volatility=0.03),
                AssetClass.CORPORATE_BOND: AssetParameters(expected_return=0.04, volatility=0.05)
            }
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
             "Liability Analysis", "Portfolio Analysis", "Scenario Analysis"]
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
        else:  # Scenario Analysis
            st.header("Scenario Analysis")
            self._run_scenario_analysis()

    def _run_gcv_analysis(self):
        """Run GCV analysis section."""
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
            
            # Calculate summary statistics
            years = list(range(grading_years + 1))
            gcv_values = [self._apply_grading_pattern(year, GradingPattern[pattern]) for year in years]
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Initial GCV", f"{gcv_values[0]:.2%}")
            with col2:
                st.metric("Mid-Point GCV", f"{gcv_values[grading_years//2]:.2%}")
            with col3:
                st.metric("Final GCV", f"{gcv_values[-1]:.2%}")
            with col4:
                st.metric("Average GCV", f"{sum(gcv_values)/len(gcv_values):.2%}")
            
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
        scenarios = self.investment_portfolio.generate_scenarios(
            n_periods=n_years * 12,  # Convert years to months
            n_scenarios=n_scenarios,
            seed=42  # For reproducibility
        )
        
        # Plot scenario results
        fig = go.Figure()
        for i in range(min(10, n_scenarios)):  # Plot first 10 scenarios
            fig.add_trace(go.Scatter(
                y=scenarios[f'Scenario_{i+1}'],  # Use correct column names
                mode='lines',
                name=f'Scenario {i+1}',
                opacity=0.3
            ))
        
        fig.add_trace(go.Scatter(
            y=np.mean(scenarios, axis=0),
            mode='lines',
            name='Mean',
            line=dict(color='red', width=2)
        ))
        
        st.plotly_chart(fig)

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

if __name__ == "__main__":
    st.set_page_config(
        page_title="Actuarial Model Analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    dashboard = ModelDashboard()
    dashboard.run()
