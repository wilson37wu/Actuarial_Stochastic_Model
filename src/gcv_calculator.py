"""
Module for calculating Guaranteed Cash Values for insurance products.

This module implements various GCV calculation methodologies:
1. Linear Grading: Simple linear reduction over time
2. S-Curve Grading: Slower initial reduction, faster middle years, slower final years
3. Step-wise Grading: Distinct steps at specific durations
4. Product-specific patterns for different whole life variants
5. Target IRR: Grading pattern to achieve target IRR at specified duration
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple, List, Union
from datetime import date
import numpy as np
from numpy.polynomial import Polynomial

class GradingPattern(Enum):
    """Available GCV grading patterns."""
    LINEAR = "linear"
    S_CURVE = "s_curve"
    STEPWISE = "stepwise"
    CUSTOM = "custom"
    EXPONENTIAL = "exponential"  # Exponential decay
    DUAL_PHASE = "dual_phase"    # Different rates for early/late years
    DYNAMIC = "dynamic"          # Pattern adjusts based on duration
    HYBRID = "hybrid"           # Combination of multiple patterns
    TARGET_IRR = "target_irr"   # Pattern to achieve target IRR

class ProductVariant(Enum):
    """Whole life product variants affecting GCV calculation."""
    STANDARD = "standard"
    LOW_PREMIUM = "low_premium"  # Lower premium, lower early GCV
    HIGH_EARLY_VALUE = "high_early_value"  # Higher early GCV, lower later
    LEVEL_GCV = "level_gcv"  # More level GCV pattern
    EDUCATION = "education"      # Higher values during education years
    RETIREMENT = "retirement"    # Higher values near retirement
    WEALTH_BUILDER = "wealth_builder"  # Aggressive early accumulation
    LEGACY = "legacy"           # Optimized for death benefit

@dataclass
class GCVFactors:
    """Class to hold guaranteed cash value factors."""
    male_factors: Dict[int, float]  # Policy year to factor per 1000 face amount
    female_factors: Dict[int, float]
    
    def validate(self) -> bool:
        """Validate that factors meet minimum requirements."""
        for factors in [self.male_factors, self.female_factors]:
            prev_factor = float('inf')
            for year in sorted(factors.keys()):
                factor = factors[year]
                # Factors should generally decrease over time
                if factor > prev_factor:
                    print(f"Warning: Factor increases at year {year}")
                prev_factor = factor
        return True

@dataclass
class GCVParameters:
    """Parameters for GCV calculation."""
    base_percentage: float = 0.7  # Percentage of PV premium for base
    initial_gcv_percentage: float = 0.5  # Initial percentage of base
    grading_years: int = 10  # Years over which to grade
    minimum_gcv_percentage: float = 0.05  # Minimum as percentage of PV premium
    grading_pattern: GradingPattern = GradingPattern.LINEAR
    product_variant: ProductVariant = ProductVariant.STANDARD
    stepwise_points: Optional[Dict[int, float]] = None  # Year to factor for stepwise
    
    # Target IRR parameters
    target_irr: Optional[float] = None  # Target IRR to achieve
    target_year: Optional[int] = None   # Year by which to achieve target IRR
    
    # External table parameters
    external_table: Optional[Dict[str, Dict[int, float]]] = None  # Product -> Year -> Factor
    interpolation_method: str = "linear"  # linear, cubic, or nearest
    
    # Advanced grading parameters
    pattern_weights: Optional[Dict[GradingPattern, float]] = None  # For hybrid pattern
    custom_function: Optional[callable] = None  # For custom pattern
    dynamic_adjustments: Optional[Dict[str, float]] = None  # For dynamic pattern

class GCVCalculator:
    """Calculator for Guaranteed Cash Values."""
    
    def __init__(self, 
                 valuation_rate: float = 0.035,
                 external_factors: Optional[GCVFactors] = None,
                 parameters: Optional[GCVParameters] = None):
        """Initialize GCV calculator.
        
        Args:
            valuation_rate: Annual rate for present value calculations
            external_factors: Optional external GCV factors by gender and duration
            parameters: Optional parameters for GCV calculation
        """
        self.valuation_rate = valuation_rate
        self.external_factors = external_factors
        self.parameters = parameters or GCVParameters()
        
        if external_factors:
            external_factors.validate()
            
    def calculate_irr(self, premiums: List[float], cash_values: List[float]) -> float:
        """Calculate the Internal Rate of Return (IRR) for a series of cash flows.
        
        Args:
            premiums: List of premium payments (negative cash flows)
            cash_values: List of guaranteed cash values (positive cash flows)
            
        Returns:
            Float: The IRR as a decimal (e.g., 0.05 for 5%)
        """
        cash_flows = [-p for p in premiums]  # Convert premiums to negative cash flows
        cash_flows.extend(cash_values)       # Add positive cash flows from GCV
        
        # Function to calculate NPV given a rate
        def npv(rate):
            return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        
        # Use numerical methods to find IRR (rate where NPV = 0)
        from scipy.optimize import newton
        try:
            irr = newton(npv, x0=0.05)  # Start with 5% guess
            return max(irr, -1)  # IRR cannot be less than -100%
        except:
            return float('-inf')  # Return -infinity if IRR cannot be found
            
    def _solve_for_target_irr(self, 
                             premium: float,
                             face_amount: float,
                             target_irr: float,
                             target_year: int) -> List[float]:
        """Solve for GCV factors that achieve the target IRR by target year.
        
        Uses optimization to find a smooth curve of GCV factors that:
        1. Starts at initial_gcv_percentage
        2. Achieves target IRR by target year
        3. Maintains minimum GCV requirements
        """
        def objective(coeffs):
            # Generate GCV factors using polynomial
            poly = Polynomial(coeffs)
            years = range(target_year + 1)
            factors = [max(self.parameters.minimum_gcv_percentage, 
                         min(self.parameters.initial_gcv_percentage, poly(t)))
                      for t in years]
            
            # Calculate IRR
            premiums = [premium] * target_year
            cash_values = [f * face_amount for f in factors]
            achieved_irr = self.calculate_irr(premiums, cash_values)
            
            # Penalty for deviation from target IRR
            irr_penalty = 100 * (achieved_irr - target_irr) ** 2
            
            # Penalty for non-smoothness
            smoothness_penalty = sum((factors[i+1] - factors[i]) ** 2 
                                   for i in range(len(factors)-1))
            
            return irr_penalty + smoothness_penalty
        
        # Initial guess: linear coefficients
        initial_coeffs = [self.parameters.initial_gcv_percentage,
                         -(self.parameters.initial_gcv_percentage - 
                           self.parameters.minimum_gcv_percentage) / target_year]
        
        # Optimize
        from scipy.optimize import minimize
        result = minimize(objective, initial_coeffs, method='Nelder-Mead')
        
        # Generate final factors
        poly = Polynomial(result.x)
        return [max(self.parameters.minimum_gcv_percentage,
                   min(self.parameters.initial_gcv_percentage, poly(t)))
                for t in range(target_year + 1)]
    
    def _apply_target_irr_grading(self, policy_year: int, premium: float, face_amount: float) -> float:
        """Apply grading pattern to achieve target IRR."""
        if not (self.parameters.target_irr and self.parameters.target_year):
            return self._apply_linear_grading(policy_year)
            
        if not hasattr(self, '_target_irr_factors'):
            self._target_irr_factors = self._solve_for_target_irr(
                premium, face_amount,
                self.parameters.target_irr,
                self.parameters.target_year
            )
            
        if policy_year >= len(self._target_irr_factors):
            return self._target_irr_factors[-1]
        return self._target_irr_factors[policy_year]

    def _apply_s_curve_grading(self, policy_year: int) -> float:
        """Apply S-curve grading pattern.
        
        Uses sigmoid function to create smooth S-curve transition.
        Slower reduction in early and late years, faster in middle years.
        """
        if policy_year >= self.parameters.grading_years:
            return 0.0
            
        x = (policy_year - self.parameters.grading_years/2) / (self.parameters.grading_years/4)
        sigmoid = 1 / (1 + np.exp(x))
        return sigmoid
    
    def _apply_stepwise_grading(self, policy_year: int) -> float:
        """Apply stepwise grading pattern using defined points."""
        if not self.parameters.stepwise_points:
            return self._apply_linear_grading(policy_year)
            
        points = self.parameters.stepwise_points
        if policy_year >= max(points.keys()):
            return 0.0
            
        # Find surrounding points
        years = sorted(points.keys())
        for i, year in enumerate(years):
            if policy_year <= year:
                if i == 0:
                    return points[year]
                prev_year = years[i-1]
                prev_factor = points[prev_year]
                next_factor = points[year]
                # Linear interpolation between steps
                return prev_factor + (next_factor - prev_factor) * (policy_year - prev_year) / (year - prev_year)
        return 0.0
    
    def _apply_linear_grading(self, policy_year: int) -> float:
        """Apply linear grading pattern."""
        return max(0, (self.parameters.grading_years - policy_year) / self.parameters.grading_years)
    
    def _apply_exponential_grading(self, policy_year: int) -> float:
        """Apply exponential decay grading pattern.
        
        Provides smooth, continuous reduction with customizable decay rate.
        """
        decay_rate = -np.log(0.01) / self.parameters.grading_years  # 99% reduction at end
        return np.exp(-decay_rate * policy_year)
    
    def _apply_dual_phase_grading(self, policy_year: int) -> float:
        """Apply dual-phase grading with different rates.
        
        Phase 1: Slower reduction (years 0-5)
        Phase 2: Faster reduction (years 5+)
        """
        if policy_year >= self.parameters.grading_years:
            return 0.0
            
        phase1_years = min(5, self.parameters.grading_years // 2)
        if policy_year <= phase1_years:
            return 1.0 - 0.2 * policy_year / phase1_years
        else:
            remaining_years = self.parameters.grading_years - phase1_years
            remaining_reduction = 0.8  # 20% reduced in phase 1
            years_in_phase2 = policy_year - phase1_years
            return 0.8 * (1.0 - years_in_phase2 / remaining_years)
    
    def _apply_dynamic_grading(self, policy_year: int) -> float:
        """Apply dynamic grading that adjusts based on duration.
        
        - Early years: Linear reduction
        - Middle years: S-curve
        - Later years: Exponential tail
        """
        if policy_year >= self.parameters.grading_years:
            return 0.0
            
        early_years = self.parameters.grading_years * 0.3
        late_years = self.parameters.grading_years * 0.7
        
        if policy_year <= early_years:
            return self._apply_linear_grading(policy_year)
        elif policy_year <= late_years:
            normalized_year = (policy_year - early_years) / (late_years - early_years)
            return self._apply_s_curve_grading(normalized_year * self.parameters.grading_years)
        else:
            normalized_year = (policy_year - late_years) / (self.parameters.grading_years - late_years)
            return self._apply_exponential_grading(normalized_year * self.parameters.grading_years)
    
    def _apply_hybrid_grading(self, policy_year: int) -> float:
        """Apply hybrid grading combining multiple patterns.
        
        Weighted combination of different patterns based on policy year.
        """
        if policy_year >= self.parameters.grading_years:
            return 0.0
            
        linear_weight = max(0, 1 - policy_year / self.parameters.grading_years)
        s_curve_weight = 1 - abs(2 * policy_year / self.parameters.grading_years - 1)
        exp_weight = min(1, policy_year / self.parameters.grading_years)
        
        return (
            linear_weight * self._apply_linear_grading(policy_year) +
            s_curve_weight * self._apply_s_curve_grading(policy_year) +
            exp_weight * self._apply_exponential_grading(policy_year)
        ) / (linear_weight + s_curve_weight + exp_weight)
    
    def _adjust_for_product_variant(self, 
                                  base_gcv: float,
                                  policy_year: int,
                                  pv_premium: float,
                                  issue_age: int = 35) -> float:
        """Adjust GCV based on product variant."""
        variant = self.parameters.product_variant
        
        if variant == ProductVariant.LOW_PREMIUM:
            # Lower early values for low premium variant
            if policy_year <= 5:
                return base_gcv * 0.8
        elif variant == ProductVariant.HIGH_EARLY_VALUE:
            # Higher early values, lower later values
            if policy_year <= 3:
                return base_gcv * 1.2
            elif policy_year > 10:
                return base_gcv * 0.9
        elif variant == ProductVariant.LEVEL_GCV:
            # More level pattern
            avg_gcv = base_gcv * 0.95
            return avg_gcv + (base_gcv - avg_gcv) * np.exp(-policy_year/5)
        elif variant == ProductVariant.EDUCATION:
            # Higher values during typical education years (age 18-22)
            education_start = max(0, 18 - issue_age)
            education_end = max(0, 22 - issue_age)
            if education_start <= policy_year <= education_end:
                return base_gcv * 1.2
                
        elif variant == ProductVariant.RETIREMENT:
            # Higher values near typical retirement (age 65)
            years_to_retirement = max(0, 65 - issue_age)
            if abs(policy_year - years_to_retirement) <= 5:
                boost_factor = 1.2 - 0.04 * abs(policy_year - years_to_retirement)
                return base_gcv * boost_factor
                
        elif variant == ProductVariant.WEALTH_BUILDER:
            # Aggressive early accumulation
            if policy_year <= 7:
                return base_gcv * (1.3 - 0.04 * policy_year)
            else:
                return base_gcv * 0.85
                
        elif variant == ProductVariant.LEGACY:
            # Optimized for death benefit, more conservative CSV
            if policy_year <= 3:
                return base_gcv * 0.9
            else:
                return base_gcv * 0.95
        
        return base_gcv
    
    def calculate_default_factors(self,
                                premium: float,
                                face_amount: float,
                                policy_year: int,
                                pv_premium: float) -> float:
        """Calculate default GCV factors when no external factors provided.
        
        Implements sophisticated GCV calculation with:
        - Multiple grading patterns (linear, S-curve, stepwise)
        - Product variant adjustments
        - Minimum value requirements
        - Base value calculations
        
        Args:
            premium: Annual premium amount
            face_amount: Policy face amount
            policy_year: Current policy year
            pv_premium: Present value of premiums at time 0
        
        Returns:
            GCV factor per 1000 face amount
        """
        if policy_year > self.parameters.grading_years:
            return 0.0
            
        # Calculate base value
        base_value = self.parameters.base_percentage * pv_premium
        initial_gcv = self.parameters.initial_gcv_percentage * base_value
        
        # Apply grading pattern
        if self.parameters.grading_pattern == GradingPattern.S_CURVE:
            grading_factor = self._apply_s_curve_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.STEPWISE:
            grading_factor = self._apply_stepwise_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.EXPONENTIAL:
            grading_factor = self._apply_exponential_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.DUAL_PHASE:
            grading_factor = self._apply_dual_phase_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.DYNAMIC:
            grading_factor = self._apply_dynamic_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.HYBRID:
            grading_factor = self._apply_hybrid_grading(policy_year)
        elif self.parameters.grading_pattern == GradingPattern.TARGET_IRR:
            grading_factor = self._apply_target_irr_grading(policy_year, premium, face_amount)
        else:  # LINEAR
            grading_factor = self._apply_linear_grading(policy_year)
        
        # Calculate initial GCV
        current_gcv = initial_gcv * grading_factor
        
        # Convert to per 1000 face amount factor
        factor = (current_gcv * 1000) / face_amount
        
        # Apply product variant adjustments
        factor = self._adjust_for_product_variant(factor, policy_year, pv_premium)
        
        # Ensure minimum total cash value requirement
        min_gcv = self.parameters.minimum_gcv_percentage * pv_premium
        min_factor = (min_gcv * 1000) / face_amount
        
        return max(factor, min_factor if policy_year <= self.parameters.grading_years else 0)
    
    def get_gcv_factor(self,
                      sex: str,
                      policy_year: int,
                      premium: float,
                      face_amount: float,
                      pv_premium: float) -> float:
        """Get GCV factor based on sex and policy year.
        
        Args:
            sex: 'M' for male, 'F' for female
            policy_year: Current policy year
            premium: Annual premium amount
            face_amount: Policy face amount
            pv_premium: Present value of premiums at time 0
            
        Returns:
            GCV factor per 1000 face amount
        """
        if self.external_factors:
            factors = (self.external_factors.male_factors 
                      if sex == 'M' 
                      else self.external_factors.female_factors)
            return factors.get(policy_year, 0.0)
        
        return self.calculate_default_factors(
            premium=premium,
            face_amount=face_amount,
            policy_year=policy_year,
            pv_premium=pv_premium
        )
    
    def calculate_gcv(self,
                     sex: str,
                     policy_year: int,
                     premium: float,
                     face_amount: float,
                     pv_premium: float) -> float:
        """Calculate Guaranteed Cash Value for a policy.
        
        This method calculates the GCV based on:
        1. External factors if provided
        2. Default calculation using specified grading pattern
        3. Product variant adjustments
        4. Minimum value requirements
        
        The calculation ensures:
        - GCV generally decreases over time
        - Minimum values are maintained
        - Appropriate adjustments for product variants
        - Smooth transitions between policy years
        
        Args:
            sex: 'M' for male, 'F' for female
            policy_year: Current policy year
            premium: Annual premium amount
            face_amount: Policy face amount
            pv_premium: Present value of premiums at time 0
            
        Returns:
            Guaranteed Cash Value amount
        """
        factor = self.get_gcv_factor(
            sex=sex,
            policy_year=policy_year,
            premium=premium,
            face_amount=face_amount,
            pv_premium=pv_premium
        )
        return (factor * face_amount) / 1000
