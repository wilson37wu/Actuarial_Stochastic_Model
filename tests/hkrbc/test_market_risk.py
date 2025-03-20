"""
Tests for market risk calculations.
References Cap 41R test scenarios and DTT implementation examples.
"""

import unittest
import numpy as np
from src.hkrbc.capital_calculator.market_risk.interest_rate import InterestRateRiskModule
from src.hkrbc.capital_calculator.market_risk.credit_spread import CreditSpreadRiskModule
from src.hkrbc.capital_calculator.market_risk.equity import EquityRiskModule
from src.hkrbc.capital_calculator.market_risk.property import PropertyRiskModule
from src.hkrbc.capital_calculator.market_risk.currency import CurrencyRiskModule
from src.hkrbc.capital_calculator.market_risk.aggregator import MarketRiskAggregator

class TestInterestRateRisk(unittest.TestCase):
    """Test interest rate risk calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.module = InterestRateRiskModule()
        
        # Test data based on DTT example
        self.terms = np.array([1, 2, 5, 10, 20, 30])
        self.rates = np.array([0.02, 0.025, 0.03, 0.035, 0.04, 0.04])
        
    def test_stress_factors(self):
        """Test interest rate stress factors interpolation."""
        # Test up stress
        stressed_rates = self.module.calculate_stressed_rates(
            self.terms, self.rates, 'up'
        )
        self.assertTrue(np.all(stressed_rates >= self.rates))
        
        # Test down stress
        stressed_rates = self.module.calculate_stressed_rates(
            self.terms, self.rates, 'down'
        )
        self.assertTrue(np.all(stressed_rates <= self.rates))
        
    def test_risk_charge(self):
        """Test interest rate risk charge calculation."""
        result = self.module.calculate_risk_charge(
            terms=self.terms,
            rates=self.rates,
            asset_values={'bonds': 1000000},
            liability_values={'reserves': 900000}
        )
        
        self.assertGreater(result.gross_charge, 0)
        self.assertEqual(len(result.sub_risks), 2)  # Up and down stress

class TestEquityRisk(unittest.TestCase):
    """Test equity risk calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.module = EquityRiskModule()
        
        # Test data
        self.equity_exposures = [
            {'market_value': 1000000, 'type': 'type_1'},
            {'market_value': 500000, 'type': 'type_2'},
            {'market_value': 200000, 'type': 'strategic'}
        ]
        
    def test_risk_charge(self):
        """Test equity risk charge calculation."""
        result = self.module.calculate_risk_charge(self.equity_exposures)
        
        # Type 1 stress should be 39%
        type1_charge = result.sub_risks['type_1'].gross_charge
        self.assertAlmostEqual(
            type1_charge,
            1000000 * 0.39,
            delta=0.01
        )
        
        # Total charge should be less than sum of individual charges
        self.assertLess(
            result.net_charge,
            sum(r.gross_charge for r in result.sub_risks.values())
        )

class TestMarketRiskAggregation(unittest.TestCase):
    """Test market risk aggregation."""
    
    def setUp(self):
        """Set up test data."""
        self.aggregator = MarketRiskAggregator()
        
        # Test data
        self.market_data = {
            'interest_rate': {
                'terms': np.array([1, 2, 5, 10, 20, 30]),
                'rates': np.array([0.02, 0.025, 0.03, 0.035, 0.04, 0.04]),
                'asset_values': {'bonds': 1000000},
                'liability_values': {'reserves': 900000}
            },
            'equity': {
                'equity_exposures': [
                    {'market_value': 1000000, 'type': 'type_1'},
                    {'market_value': 500000, 'type': 'type_2'}
                ]
            }
        }
        
    def test_aggregation(self):
        """Test market risk aggregation with correlation."""
        result = self.aggregator.calculate_risk_charge(self.market_data)
        
        # Check diversification benefit
        self.assertGreater(result.diversification_benefit, 0)
        
        # Total charge should be less than sum of individual charges
        self.assertLess(
            result.net_charge,
            sum(r.gross_charge for r in result.sub_risks.values())
        )

if __name__ == '__main__':
    unittest.main()
