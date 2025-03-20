"""
Tests for insurance risk calculations.
References Cap 41R test scenarios and DTT implementation examples.
"""

import unittest
import numpy as np
from src.hkrbc.capital_calculator.insurance_risk.mortality import MortalityRiskModule
from src.hkrbc.capital_calculator.insurance_risk.longevity import LongevityRiskModule
from src.hkrbc.capital_calculator.insurance_risk.lapse import LapseRiskModule
from src.hkrbc.capital_calculator.insurance_risk.aggregator import InsuranceRiskAggregator

class TestMortalityRisk(unittest.TestCase):
    """Test mortality risk calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.module = MortalityRiskModule()
        
        # Test data
        self.mortality_data = {
            'mortality_rates': np.array([
                [0.001, 0.002, 0.003],  # Age 30
                [0.002, 0.003, 0.004],  # Age 40
                [0.003, 0.004, 0.005]   # Age 50
            ]),
            'sum_assured': np.array([
                [1000000, 800000, 600000],
                [900000, 700000, 500000],
                [800000, 600000, 400000]
            ]),
            'discount_factors': np.array([0.98, 0.96, 0.94])
        }
        
    def test_level_stress(self):
        """Test permanent increase in mortality rates."""
        impact = self.module.calculate_level_stress_impact(
            self.mortality_data['mortality_rates'],
            self.mortality_data['sum_assured'],
            self.mortality_data['discount_factors']
        )
        
        self.assertGreater(impact, 0)
        
    def test_catastrophe_stress(self):
        """Test mortality catastrophe scenario."""
        impact = self.module.calculate_catastrophe_stress_impact(
            self.mortality_data['sum_assured'],
            self.mortality_data['discount_factors']
        )
        
        self.assertGreater(impact, 0)
        
    def test_risk_charge(self):
        """Test total mortality risk charge."""
        result = self.module.calculate_risk_charge(self.mortality_data)
        
        self.assertGreater(result.gross_charge, 0)
        self.assertGreater(result.diversification_benefit, 0)
        self.assertEqual(len(result.sub_risks), 2)

class TestLapseRisk(unittest.TestCase):
    """Test lapse risk calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.module = LapseRiskModule()
        
        # Test data
        self.lapse_data = {
            'lapse_rates': np.array([0.1, 0.08, 0.06, 0.05, 0.04]),
            'policy_values': np.array([100000, 90000, 80000]),
            'surrender_values': np.array([90000, 82000, 74000]),
            'policy_cashflows': np.array([
                [10000, 9000, 8000],
                [9500, 8500, 7500],
                [9000, 8000, 7000]
            ]),
            'discount_factors': np.array([0.98, 0.96, 0.94])
        }
        
    def test_mass_lapse(self):
        """Test mass lapse scenario."""
        impact = self.module.calculate_mass_lapse_impact(
            self.lapse_data['policy_values'],
            self.lapse_data['surrender_values']
        )
        
        self.assertGreater(impact, 0)
        
    def test_trend_stress(self):
        """Test lapse trend stress scenarios."""
        # Test up stress
        up_impact = self.module.calculate_trend_stress_impact(
            self.lapse_data['lapse_rates'],
            self.lapse_data['policy_cashflows'],
            self.lapse_data['discount_factors'],
            'up'
        )
        
        # Test down stress
        down_impact = self.module.calculate_trend_stress_impact(
            self.lapse_data['lapse_rates'],
            self.lapse_data['policy_cashflows'],
            self.lapse_data['discount_factors'],
            'down'
        )
        
        self.assertNotEqual(up_impact, 0)
        self.assertNotEqual(down_impact, 0)

class TestInsuranceRiskAggregation(unittest.TestCase):
    """Test insurance risk aggregation."""
    
    def setUp(self):
        """Set up test data."""
        self.aggregator = InsuranceRiskAggregator()
        
        # Common test data
        self.mortality_rates = np.array([
            [0.001, 0.002],
            [0.002, 0.003]
        ])
        self.discount_factors = np.array([0.98, 0.96])
        
        # Test data for all risks
        self.insurance_data = {
            'mortality': {
                'mortality_rates': self.mortality_rates,
                'sum_assured': np.array([[1000000, 800000], [900000, 700000]]),
                'discount_factors': self.discount_factors
            },
            'longevity': {
                'mortality_rates': self.mortality_rates,
                'annuity_payments': np.array([[50000, 45000], [48000, 43000]]),
                'discount_factors': self.discount_factors
            },
            'lapse': {
                'lapse_rates': np.array([0.1, 0.08]),
                'policy_values': np.array([100000, 90000]),
                'surrender_values': np.array([90000, 82000]),
                'policy_cashflows': np.array([[10000, 9000], [9500, 8500]]),
                'discount_factors': self.discount_factors
            }
        }
        
    def test_aggregation(self):
        """Test insurance risk aggregation with correlation."""
        result = self.aggregator.calculate_risk_charge(self.insurance_data)
        
        # Check diversification benefit
        self.assertGreater(result.diversification_benefit, 0)
        
        # Check negative correlation effect
        self.assertLess(
            result.net_charge,
            sum(r.gross_charge for r in result.sub_risks.values())
        )

if __name__ == '__main__':
    unittest.main()
