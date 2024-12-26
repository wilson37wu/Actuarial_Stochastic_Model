"""
Module for tracking and calculating non-guaranteed cash dividends.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date
import numpy as np
import pandas as pd

@dataclass
class DividendAccount:
    """Tracks dividend-related accumulation and distributions."""
    cumulative_asset_return: float = 0.0
    cumulative_shareholder_cost: float = 0.0
    minimum_dividend_rate: float = 0.01  # 1% minimum dividend
    shareholder_cost_rate: float = 0.02  # 2% cost when paying minimum dividend
    tracking_balance: float = 0.0  # Cumulative gain/loss tracking
    dividend_history: List[float] = field(default_factory=list)
    asset_return_history: List[float] = field(default_factory=list)

class DividendTracker:
    """Manages non-guaranteed cash dividend calculations and tracking."""
    
    def __init__(self,
                 minimum_dividend_rate: float = 0.01,
                 shareholder_cost_rate: float = 0.02):
        """Initialize dividend tracker.
        
        Args:
            minimum_dividend_rate: Minimum dividend rate to maintain
            shareholder_cost_rate: Cost rate borne by shareholders when paying minimum
        """
        self.accounts: Dict[str, DividendAccount] = {}
        self.minimum_dividend_rate = minimum_dividend_rate
        self.shareholder_cost_rate = shareholder_cost_rate
    
    def initialize_account(self, policy_number: str) -> None:
        """Initialize tracking account for a policy."""
        self.accounts[policy_number] = DividendAccount(
            minimum_dividend_rate=self.minimum_dividend_rate,
            shareholder_cost_rate=self.shareholder_cost_rate
        )
    
    def calculate_dividend(self,
                         policy_number: str,
                         asset_return: float,
                         face_amount: float,
                         valuation_date: date) -> float:
        """Calculate cash dividend based on asset return and tracking account.
        
        Args:
            policy_number: Policy identifier
            asset_return: Current period asset return
            face_amount: Policy face amount
            valuation_date: Current valuation date
            
        Returns:
            Cash dividend amount for the period
        """
        if policy_number not in self.accounts:
            self.initialize_account(policy_number)
            
        account = self.accounts[policy_number]
        
        # Update asset return history
        account.asset_return_history.append(asset_return)
        
        # Simple dividend calculation:
        # - If asset return > minimum rate, pay excess as dividend
        # - If asset return < minimum rate, accumulate deficit in tracking account
        excess_return = max(0, asset_return - self.minimum_dividend_rate)
        deficit = min(0, asset_return - self.minimum_dividend_rate)
        
        # Update tracking balance
        account.tracking_balance += deficit * face_amount
        
        # Calculate dividend
        dividend = excess_return * face_amount
        
        # If tracking balance is positive, use it to enhance dividend
        if account.tracking_balance > 0:
            recovery_amount = min(account.tracking_balance, dividend * 0.5)
            dividend += recovery_amount
            account.tracking_balance -= recovery_amount
        
        account.dividend_history.append(dividend)
        return dividend

    def get_account_status(self, policy_number: str) -> Dict[str, float]:
        """Get current status of dividend tracking account.
        
        Args:
            policy_number: Policy identifier
            
        Returns:
            Dict containing tracking account metrics
        """
        if policy_number not in self.accounts:
            return {}
            
        account = self.accounts[policy_number]
        return {
            'cumulative_asset_return': account.cumulative_asset_return,
            'cumulative_shareholder_cost': account.cumulative_shareholder_cost,
            'tracking_balance': account.tracking_balance,
            'total_dividends_paid': sum(account.dividend_history),
            'average_dividend_rate': (
                np.mean(account.dividend_history) if account.dividend_history else 0
            ),
            'average_asset_return': (
                np.mean(account.asset_return_history) if account.asset_return_history else 0
            )
        }
    
    def reset_account(self, policy_number: str) -> None:
        """Reset tracking account for a policy."""
        if policy_number in self.accounts:
            self.accounts[policy_number] = DividendAccount(
                minimum_dividend_rate=self.minimum_dividend_rate,
                shareholder_cost_rate=self.shareholder_cost_rate
            )
    
    def reset(self) -> None:
        """Reset all dividend tracking accounts."""
        self.accounts.clear()

    def run_stress_test(self,
                       policy_number: str,
                       face_amount: float,
                       scenarios: Dict[str, List[float]],
                       reset_after_each: bool = True) -> Dict[str, Dict[str, List[float]]]:
        """Run stress tests using predefined scenarios.
        
        Args:
            policy_number: Policy identifier
            face_amount: Policy face amount
            scenarios: Dictionary of scenario names to lists of asset returns
            reset_after_each: Whether to reset account between scenarios
            
        Returns:
            Dictionary of results by scenario and metric
        """
        results = {}
        original_account = self.accounts.get(policy_number)
        
        for scenario_name, returns in scenarios.items():
            if reset_after_each:
                self.reset_account(policy_number)
                
            scenario_results = {
                'dividends': [],
                'tracking_balance': [],
                'shareholder_cost': []
            }
            
            for ret in returns:
                dividend = self.calculate_dividend(
                    policy_number=policy_number,
                    asset_return=ret,
                    face_amount=face_amount,
                    valuation_date=date.today()  # Dummy date for stress test
                )
                
                account = self.accounts[policy_number]
                scenario_results['dividends'].append(dividend)
                scenario_results['tracking_balance'].append(account.tracking_balance)
                scenario_results['shareholder_cost'].append(
                    account.cumulative_shareholder_cost
                )
            
            results[scenario_name] = scenario_results
        
        # Restore original account if it existed
        if original_account and reset_after_each:
            self.accounts[policy_number] = original_account
            
        return results
    
    def analyze_recovery_metrics(self,
                               policy_number: str) -> Dict[str, float]:
        """Analyze recovery metrics for a policy.
        
        Returns:
            Dictionary of recovery metrics
        """
        account = self.accounts.get(policy_number)
        if not account:
            return {}
            
        asset_returns = account.asset_return_history
        dividends = account.dividend_history
        
        if not asset_returns or not dividends:
            return {}
            
        metrics = {
            'total_positive_returns': sum(r for r in asset_returns if r > 0),
            'total_negative_returns': sum(r for r in asset_returns if r < 0),
            'recovery_efficiency': 0.0,  # Will be calculated
            'minimum_dividend_frequency': 0.0,  # Will be calculated
            'average_recovery_time': 0.0,  # Will be calculated
        }
        
        # Calculate recovery efficiency
        positive_returns_used = sum(
            max(0, r) for r in asset_returns
            if account.tracking_balance < 0
        )
        if metrics['total_positive_returns'] > 0:
            metrics['recovery_efficiency'] = (
                positive_returns_used / metrics['total_positive_returns']
            )
        
        # Calculate minimum dividend frequency
        min_dividend_count = sum(
            1 for d in dividends
            if abs(d - account.minimum_dividend_rate) < 1e-6
        )
        metrics['minimum_dividend_frequency'] = (
            min_dividend_count / len(dividends)
            if dividends else 0
        )
        
        # Calculate average recovery time
        if asset_returns:
            negative_periods = []
            current_negative = 0
            for ret in asset_returns:
                if ret < 0:
                    current_negative += 1
                elif current_negative > 0:
                    negative_periods.append(current_negative)
                    current_negative = 0
            
            metrics['average_recovery_time'] = (
                sum(negative_periods) / len(negative_periods)
                if negative_periods else 0
            )
        
        return metrics
    
    def generate_dividend_report(self,
                               policy_number: str) -> pd.DataFrame:
        """Generate detailed dividend report for a policy.
        
        Returns:
            DataFrame with detailed dividend analysis
        """
        account = self.accounts.get(policy_number)
        if not account:
            return pd.DataFrame()
            
        data = []
        for i, (ret, div) in enumerate(zip(
            account.asset_return_history,
            account.dividend_history
        )):
            data.append({
                'Period': i + 1,
                'Asset_Return': ret,
                'Dividend_Rate': div,
                'Tracking_Balance': account.tracking_balance,
                'Cumulative_Return': sum(account.asset_return_history[:i+1]),
                'Cumulative_Dividend': sum(account.dividend_history[:i+1]),
                'Shareholder_Cost': account.cumulative_shareholder_cost,
                'Is_Minimum_Dividend': abs(div - account.minimum_dividend_rate) < 1e-6,
                'Return_Shortfall': max(0, -ret),
                'Recovery_Amount': max(0, ret) if account.tracking_balance < 0 else 0
            })
        
        return pd.DataFrame(data)
    
    def project_recovery_path(self,
                            policy_number: str,
                            assumed_return: float,
                            projection_years: int) -> pd.DataFrame:
        """Project recovery path assuming a constant future return.
        
        Args:
            policy_number: Policy identifier
            assumed_return: Assumed constant future return
            projection_years: Number of years to project
            
        Returns:
            DataFrame with projected recovery path
        """
        account = self.accounts.get(policy_number)
        if not account:
            return pd.DataFrame()
            
        initial_balance = account.tracking_balance
        if initial_balance >= 0:
            return pd.DataFrame()
            
        data = []
        current_balance = initial_balance
        
        for year in range(projection_years):
            recovery_amount = min(
                abs(current_balance),
                max(0, assumed_return)
            )
            current_balance += recovery_amount
            
            data.append({
                'Year': year + 1,
                'Starting_Balance': current_balance - recovery_amount,
                'Recovery_Amount': recovery_amount,
                'Ending_Balance': current_balance,
                'Fully_Recovered': current_balance >= 0
            })
            
            if current_balance >= 0:
                break
                
        return pd.DataFrame(data)
    
    def get_average_return(self) -> float:
        """Calculate average return across all accounts.
        
        Returns:
            Average return as a float
        """
        if not self.accounts:
            return 0.0
        
        total_return = 0.0
        total_accounts = len(self.accounts)
        
        for account in self.accounts.values():
            if account.asset_return_history:
                total_return += sum(account.asset_return_history) / len(account.asset_return_history)
        
        return total_return / total_accounts if total_accounts > 0 else 0.0

    def get_total_dividends(self) -> float:
        """Calculate total dividends paid across all accounts.
        
        Returns:
            Total dividends as a float
        """
        total_dividends = 0.0
        
        for account in self.accounts.values():
            total_dividends += sum(account.dividend_history)
        
        return total_dividends

    def get_returns(self) -> List[float]:
        """Get all returns across all accounts.
        
        Returns:
            List of returns. If multiple accounts exist, returns are averaged across accounts
            for each time period.
        """
        if not self.accounts:
            return []
        
        # Get max length of return history
        max_periods = max(
            len(account.asset_return_history) 
            for account in self.accounts.values()
        )
        
        # Initialize returns array
        returns = [0.0] * max_periods
        
        # Sum returns for each period
        for account in self.accounts.values():
            for i, ret in enumerate(account.asset_return_history):
                returns[i] += ret
        
        # Average returns across accounts
        n_accounts = len(self.accounts)
        returns = [ret / n_accounts for ret in returns]
        
        return returns

    def get_dividends(self) -> List[float]:
        """Get all dividends across all accounts.
        
        Returns:
            List of dividends. If multiple accounts exist, dividends are summed across accounts
            for each time period.
        """
        if not self.accounts:
            return []
        
        # Get max length of dividend history
        max_periods = max(
            len(account.dividend_history) 
            for account in self.accounts.values()
        )
        
        # Initialize dividends array
        dividends = [0.0] * max_periods
        
        # Sum dividends for each period
        for account in self.accounts.values():
            for i, div in enumerate(account.dividend_history):
                dividends[i] += div
        
        return dividends

    def get_tracking_balances(self) -> List[float]:
        """Get tracking balances for all accounts.
        
        Returns:
            List of tracking balances for each account.
        """
        return [account.tracking_balance for account in self.accounts.values()]
