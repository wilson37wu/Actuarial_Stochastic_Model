"""
AI-driven narrative generator for actuarial analysis dashboard.
Provides dynamic insights and commentary based on portfolio metrics and analysis results.
"""
import numpy as np
from datetime import date
from typing import Dict, List, Any

class NarrativeGenerator:
    """Generates AI-driven narratives for dashboard analysis."""
    
    def __init__(self):
        self.risk_thresholds = {
            'low': 5.0,
            'medium': 12.0,
            'high': 20.0
        }
        self.return_thresholds = {
            'low': 4.0,
            'medium': 8.0,
            'high': 12.0
        }
    
    def generate_portfolio_narrative(self, portfolio_data: Dict[str, Any]) -> str:
        """Generate narrative for portfolio analysis."""
        allocation = portfolio_data.get('allocation', {})
        returns = portfolio_data.get('returns', {})
        risks = portfolio_data.get('risks', {})
        
        # Portfolio composition analysis
        largest_allocation = max(allocation.items(), key=lambda x: x[1])
        risk_level = self._assess_risk_level(risks)
        
        narrative = [
            f"## Portfolio Overview\n",
            f"The portfolio currently maintains a {risk_level} risk profile, ",
            f"with the largest allocation of {largest_allocation[1]:.1f}% in {largest_allocation[0]}. ",
        ]
        
        # Risk-return analysis
        avg_return = np.mean(list(returns.values()))
        narrative.append(
            f"The portfolio's expected return of {avg_return:.1f}% "
            f"is {self._evaluate_return_level(avg_return)}. "
        )
        
        # Diversification assessment
        diversification = self._assess_diversification(allocation)
        narrative.append(diversification)
        
        return " ".join(narrative)
    
    def generate_gcv_narrative(self, gcv_data: Dict[str, Any]) -> str:
        """Generate narrative for GCV analysis."""
        premium = gcv_data.get('premium', 0)
        term = gcv_data.get('term', 0)
        interest_rate = gcv_data.get('interest_rate', 0)
        surrender_charge = gcv_data.get('surrender_charge', 0)
        
        narrative = [
            f"## GCV Analysis Insights\n",
            f"The current policy structure with an annual premium of ${premium:,.2f} ",
            f"over a {term}-year term offers a guaranteed cash value build-up pattern "
            f"influenced by a {interest_rate:.1f}% interest rate. ",
            
            f"\n\nKey Observations:\n",
            f"- The surrender charge of {surrender_charge:.1f}% impacts early policy years, ",
            f"suggesting optimal retention beyond year {self._calculate_breakeven_year(premium, interest_rate, surrender_charge)}. ",
            
            self._analyze_gcv_pattern(premium, interest_rate, term)
        ]
        
        return " ".join(narrative)
    
    def generate_dividend_narrative(self, dividend_data: Dict[str, Any]) -> str:
        """Generate narrative for dividend analysis."""
        initial = dividend_data.get('initial_dividend', 0)
        growth = dividend_data.get('growth_rate', 0)
        volatility = dividend_data.get('volatility', 0)
        years = dividend_data.get('years', 0)
        
        narrative = [
            f"## Dividend Projection Analysis\n",
            f"Starting with an initial dividend of ${initial:.2f}, the projections show ",
            f"a {growth:.1f}% annual growth trajectory over {years} years. ",
            
            f"\n\nVolatility Analysis:\n",
            self._analyze_dividend_volatility(volatility),
            
            f"\n\nLong-term Outlook:\n",
            self._project_dividend_growth(initial, growth, years)
        ]
        
        return " ".join(narrative)
    
    def generate_stress_test_narrative(self, stress_data: Dict[str, Any]) -> str:
        """Generate narrative for stress testing analysis."""
        scenario = stress_data.get('scenario', 'Base Case')
        impacts = stress_data.get('impacts', [0, 0, 0])
        
        narrative = [
            f"## Stress Test Analysis\n",
            f"Under the {scenario} scenario, the portfolio shows the following responses:\n\n",
            
            self._analyze_stress_impacts(impacts),
            
            f"\n\nResilience Assessment:\n",
            self._evaluate_portfolio_resilience(impacts)
        ]
        
        return " ".join(narrative)
    
    def generate_sensitivity_narrative(self, sensitivity_data: Dict[str, Any]) -> str:
        """Generate narrative for sensitivity analysis."""
        base_value = sensitivity_data.get('base_value', 0)
        ranges = sensitivity_data.get('ranges', {})
        
        narrative = [
            f"## Sensitivity Analysis Insights\n",
            f"Based on a portfolio value of ${base_value:,.2f}, the analysis reveals:\n\n",
            
            self._analyze_parameter_sensitivity(ranges),
            
            f"\n\nKey Risk Factors:\n",
            self._identify_key_risk_factors(ranges)
        ]
        
        return " ".join(narrative)
    
    def _assess_risk_level(self, risks: Dict[str, float]) -> str:
        """Assess the overall risk level of the portfolio."""
        avg_risk = np.mean(list(risks.values()))
        if avg_risk < self.risk_thresholds['low']:
            return "conservative"
        elif avg_risk < self.risk_thresholds['medium']:
            return "moderate"
        else:
            return "aggressive"
    
    def _evaluate_return_level(self, return_value: float) -> str:
        """Evaluate the return level relative to market conditions."""
        if return_value < self.return_thresholds['low']:
            return "below market expectations"
        elif return_value < self.return_thresholds['medium']:
            return "in line with market expectations"
        else:
            return "exceeding market expectations"
    
    def _assess_diversification(self, allocation: Dict[str, float]) -> str:
        """Assess portfolio diversification."""
        num_assets = len(allocation)
        concentration = max(allocation.values()) / sum(allocation.values())
        
        if num_assets < 3:
            return "The portfolio shows limited diversification and may benefit from broader asset allocation."
        elif concentration > 0.5:
            return "While multiple assets are present, there's significant concentration risk in the largest position."
        else:
            return "The portfolio demonstrates healthy diversification across multiple asset classes."
    
    def _calculate_breakeven_year(self, premium: float, interest_rate: float, surrender_charge: float) -> int:
        """Calculate the breakeven year for GCV."""
        return max(1, int(surrender_charge / interest_rate))
    
    def _analyze_gcv_pattern(self, premium: float, interest_rate: float, term: int) -> str:
        """Analyze the GCV pattern and provide insights."""
        total_value = premium * term * (1 + interest_rate)
        annual_growth = (1 + interest_rate) ** (1/term) - 1
        
        return (f"\n\nValue Projection:\n"
                f"The policy is projected to accumulate ${total_value:,.2f} by maturity, "
                f"with an effective annual growth rate of {annual_growth:.1%}.")
    
    def _analyze_dividend_volatility(self, volatility: float) -> str:
        """Analyze dividend volatility and provide context."""
        if volatility < 5:
            return "The dividend stream shows high stability, suitable for income-focused investors."
        elif volatility < 15:
            return "Moderate dividend volatility suggests balanced growth and stability."
        else:
            return "High dividend volatility indicates potential for both significant growth and decline."
    
    def _project_dividend_growth(self, initial: float, growth: float, years: int) -> str:
        """Project dividend growth and provide insights."""
        final_value = initial * (1 + growth/100) ** years
        return (f"At the current growth rate, dividends are projected to reach "
                f"${final_value:.2f} by year {years}, representing a "
                f"{((final_value/initial - 1) * 100):.1f}% total increase.")
    
    def _analyze_stress_impacts(self, impacts: List[float]) -> str:
        """Analyze stress test impacts and provide detailed insights."""
        categories = ["Portfolio Value", "Solvency Ratio", "Revenue"]
        analysis = []
        
        for impact, category in zip(impacts, categories):
            if abs(impact) < 10:
                severity = "minimal"
            elif abs(impact) < 20:
                severity = "moderate"
            else:
                severity = "significant"
            
            analysis.append(f"- {category}: {severity} impact of {impact}%")
        
        return "\n".join(analysis)
    
    def _evaluate_portfolio_resilience(self, impacts: List[float]) -> str:
        """Evaluate overall portfolio resilience based on stress test results."""
        max_impact = max(map(abs, impacts))
        
        if max_impact < 10:
            return "The portfolio demonstrates strong resilience to stress scenarios."
        elif max_impact < 20:
            return "The portfolio shows moderate resilience, with some vulnerability to extreme scenarios."
        else:
            return "The portfolio exhibits significant sensitivity to stress scenarios, suggesting a need for risk mitigation."
    
    def _analyze_parameter_sensitivity(self, ranges: Dict[str, tuple]) -> str:
        """Analyze parameter sensitivity and provide insights."""
        analysis = []
        for param, (min_val, max_val) in ranges.items():
            range_size = abs(max_val - min_val)
            if range_size < 5:
                sensitivity = "low"
            elif range_size < 15:
                sensitivity = "moderate"
            else:
                sensitivity = "high"
            
            analysis.append(f"- {param}: {sensitivity} sensitivity with a range of ±{range_size:.1f}%")
        
        return "\n".join(analysis)
    
    def _identify_key_risk_factors(self, ranges: Dict[str, tuple]) -> str:
        """Identify and analyze key risk factors based on sensitivity ranges."""
        sorted_ranges = sorted(
            ranges.items(),
            key=lambda x: abs(x[1][1] - x[1][0]),
            reverse=True
        )
        
        factors = [
            f"- {param}: primary driver with ±{abs(max_val - min_val):.1f}% impact range"
            for param, (min_val, max_val) in sorted_ranges[:2]
        ]
        
        return "\n".join(factors)
