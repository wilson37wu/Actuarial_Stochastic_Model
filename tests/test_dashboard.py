"""Test suite for dashboard components."""
import unittest
import numpy as np
from src.dashboard.dashboard import ModelDashboard
from src.gcv_calculator import GradingPattern, GCVParameters
from src.dividend_tracker import DividendTracker

class TestModelDashboard(unittest.TestCase):
    """Test cases for ModelDashboard class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dashboard = ModelDashboard()
    
    def test_grading_patterns(self):
        """Test all grading pattern combinations."""
        years = list(range(30))
        
        for pattern in GradingPattern.__members__.values():
            for year in years:
                try:
                    value = self.dashboard._apply_grading_pattern(year, pattern)
                    self.assertIsInstance(value, float)
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(value, 1)
                except Exception as e:
                    self.fail(f"Pattern {pattern} failed at year {year}: {str(e)}")
    
    def test_plot_gcv_patterns(self):
        """Test GCV pattern plotting."""
        try:
            fig = self.dashboard._plot_gcv_patterns(max_years=30)
            self.assertIsNotNone(fig)
        except Exception as e:
            self.fail(f"GCV pattern plotting failed: {str(e)}")
    
    def test_plot_pattern_derivatives(self):
        """Test pattern derivatives plotting."""
        try:
            years = list(range(30))
            patterns = {}
            
            for name, pattern in GradingPattern.__members__.items():
                values = [
                    self.dashboard._apply_grading_pattern(year, pattern)
                    for year in years
                ]
                
                deriv1 = np.gradient(values)
                deriv2 = np.gradient(deriv1)
                
                patterns[name] = {
                    'values': values,
                    'deriv1': deriv1.tolist(),
                    'deriv2': deriv2.tolist()
                }
            
            fig = self.dashboard.visualizer.plot_pattern_derivatives(patterns, years)
            self.assertIsNotNone(fig)
        except Exception as e:
            self.fail(f"Pattern derivatives plotting failed: {str(e)}")
    
    def test_plot_3d_surface(self):
        """Test 3D surface plotting."""
        try:
            years = np.array(range(30))
            rates = np.linspace(0, 0.1, 20)
            X, Y = np.meshgrid(years, rates)
            Z = np.zeros_like(X)
            
            for i in range(len(years)):
                for j in range(len(rates)):
                    Z[j,i] = self.dashboard._apply_grading_pattern(years[i], GradingPattern.LINEAR)
            
            fig = self.dashboard.visualizer.plot_3d_surface(
                X, Y, Z,
                title='GCV Surface Analysis',
                x_label='Policy Year',
                y_label='Interest Rate',
                z_label='GCV Factor'
            )
            self.assertIsNotNone(fig)
        except Exception as e:
            self.fail(f"3D surface plotting failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
