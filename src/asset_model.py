import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Literal
from datetime import date
from .fixed_income import FixedIncomeModel, Bond
from .public_equity import EquityModel, Equity

class AssetModel:
    """Asset cash flow model with dynamic linking capabilities to liability model."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio = {}
        self.scenarios = None
        self.fixed_income_model = FixedIncomeModel(config.get('fixed_income', {}))
        self.equity_model = EquityModel(config.get('equity', {}))
        
    def set_economic_scenarios(self, scenarios: pd.DataFrame):
        """Set economic scenarios for asset projections."""
        self.scenarios = scenarios
        
    def project_fixed_income(self, bonds: List[Bond], scenario_idx: int) -> pd.DataFrame:
        """Project fixed income cash flows under given scenario."""
        if self.scenarios is None:
            raise ValueError("Economic scenarios must be set before projection")
            
        scenario_data = self.scenarios.iloc[scenario_idx:scenario_idx+1]
        start_date = scenario_data.index[0]
        end_date = start_date + pd.DateOffset(months=59)  # Project for 60 months
        
        projection_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq='M'
        ).date
        
        all_cashflows = []
        
        for bond in bonds:
            cf = self.fixed_income_model.project_cashflows(
                bond,
                projection_dates,
                scenario_data
            )
            cf['instrument_id'] = bond.id
            all_cashflows.append(cf)
            
        if not all_cashflows:
            return pd.DataFrame()
            
        return pd.concat(all_cashflows, ignore_index=True)
        
    def calculate_portfolio_metrics(self, bonds: List[Bond], yield_curve: pd.Series) -> Dict:
        """Calculate key metrics for the fixed income portfolio."""
        metrics = {
            'total_market_value': 0.0,
            'weighted_duration': 0.0,
            'weighted_convexity': 0.0
        }
        
        total_value = 0
        
        for bond in bonds:
            # Use the yield rate corresponding to the bond's term
            term_to_maturity = (bond.maturity_date - date.today()).days / 365
            yield_rate = np.interp(
                term_to_maturity,
                yield_curve.index,
                yield_curve.values
            )
            
            duration = self.fixed_income_model.calculate_duration(bond, yield_rate)
            convexity = self.fixed_income_model.calculate_convexity(bond, yield_rate)
            
            metrics['total_market_value'] += bond.purchase_price
            metrics['weighted_duration'] += duration * bond.purchase_price
            metrics['weighted_convexity'] += convexity * bond.purchase_price
            total_value += bond.purchase_price
        
        if total_value > 0:
            metrics['weighted_duration'] /= total_value
            metrics['weighted_convexity'] /= total_value
            
        return metrics
        
    def project_equity(self, equities: List[Equity], scenario_idx: int) -> pd.DataFrame:
        """Project equity cash flows including dividends under given scenario."""
        if self.scenarios is None:
            raise ValueError("Economic scenarios must be set before projection")
            
        scenario_data = self.scenarios.iloc[scenario_idx:scenario_idx+1]
        start_date = scenario_data.index[0]
        end_date = start_date + pd.DateOffset(months=59)  # Project for 60 months
        
        projection_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq='M'
        ).date
        
        # Create scenario rates for the projection period
        scenario_rates = pd.DataFrame({
            'equity_return': [scenario_data['equity_return'].iloc[0]] * len(projection_dates),
            'risk_free_rate': [scenario_data['risk_free_rate'].iloc[0]] * len(projection_dates)
        }, index=projection_dates)
        
        all_cashflows = []
        
        for equity in equities:
            cf = self.equity_model.project_cashflows(
                equity,
                projection_dates,
                scenario_rates
            )
            all_cashflows.append(cf)
            
        if not all_cashflows:
            return pd.DataFrame()
            
        return pd.concat(all_cashflows, ignore_index=True)
        
    def calculate_reinvestment(self, available_cash: float, projection_date: pd.Timestamp,
                             scenario_idx: int) -> Dict:
        """Calculate reinvestment strategy based on available cash."""
        # Implementation for reinvestment logic
        pass
        
    def rebalance_portfolio(self, current_allocation: Dict, target_allocation: Dict,
                          tolerance: float = 0.05) -> Dict:
        """Rebalance portfolio based on target allocation."""
        # Implementation for portfolio rebalancing
        pass
        
    def calculate_key_metrics(self) -> Dict:
        """Calculate key risk metrics for the asset portfolio."""
        # Implementation for risk metrics calculation
        pass

    def project_portfolio(
        self,
        bonds: List[Bond],
        equities: List[Equity],
        valuation_date: date,
        scenario_idx: int,
        projection_years: int = 100,
        frequency: Literal['monthly', 'annual'] = 'monthly',
        output_path: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """Project both fixed income and equity cash flows.
        
        Args:
            bonds: List of bonds to project
            equities: List of equities to project
            valuation_date: Starting date for projections
            scenario_idx: Index of the scenario to use
            projection_years: Number of years to project (default: 100)
            frequency: Projection frequency ('monthly' or 'annual', default: 'monthly')
            output_path: Optional path to export results to Excel
            
        Returns:
            Dictionary containing DataFrames for:
                - fixed_income_cf: Fixed income cash flows
                - equity_cf: Equity cash flows and market values
                - combined_cf: Combined portfolio cash flows
        """
        if self.scenarios is None:
            raise ValueError("Economic scenarios must be set before projection")
            
        # Create projection dates
        freq = 'M' if frequency == 'monthly' else 'A'
        periods = projection_years * (12 if frequency == 'monthly' else 1)
        
        projection_dates = pd.date_range(
            start=valuation_date,
            periods=periods + 1,  # +1 to include the start date
            freq=freq
        ).date
        
        # Project fixed income
        fixed_income_cf = self.project_fixed_income(bonds, scenario_idx)
        if not fixed_income_cf.empty:
            fixed_income_cf['asset_type'] = 'fixed_income'
        
        # Project equity
        equity_cf = self.project_equity(equities, scenario_idx)
        if not equity_cf.empty:
            equity_cf['asset_type'] = 'equity'
        
        # Combine and process cash flows
        all_cf = pd.concat([fixed_income_cf, equity_cf], ignore_index=True)
        
        # Calculate portfolio-level metrics
        portfolio_cf = all_cf.groupby(['date', 'asset_type']).agg({
            'market_value': 'sum',
            'dividend_amount': 'sum',  # Will be NaN for fixed income
            'total_return': 'mean'     # Average return by asset type
        }).reset_index()
        
        # Calculate total portfolio metrics
        total_portfolio = all_cf.groupby('date').agg({
            'market_value': 'sum',
            'dividend_amount': 'sum',
            'total_return': lambda x: (x * all_cf.loc[x.index, 'market_value']).sum() / all_cf.loc[x.index, 'market_value'].sum()
        }).reset_index()
        total_portfolio['asset_type'] = 'total_portfolio'
        
        # Combine all portfolio views
        portfolio_cf = pd.concat([portfolio_cf, total_portfolio], ignore_index=True)
        
        results = {
            'fixed_income_cf': fixed_income_cf,
            'equity_cf': equity_cf,
            'portfolio_cf': portfolio_cf
        }
        
        # Export to Excel if path provided
        if output_path:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                fixed_income_cf.to_excel(writer, sheet_name='Fixed Income CF', index=False)
                equity_cf.to_excel(writer, sheet_name='Equity CF', index=False)
                portfolio_cf.to_excel(writer, sheet_name='Portfolio Summary', index=False)
        
        return results
