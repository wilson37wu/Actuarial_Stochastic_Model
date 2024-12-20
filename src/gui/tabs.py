"""
Tab components for the model GUI.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from .widgets import StyledWidgetMixin, ToolTip

class AssetTab(ttk.Frame, StyledWidgetMixin):
    """Asset projection tab."""
    
    def __init__(self, parent: ttk.Notebook, variables: Dict[str, Any]):
        """Initialize the asset tab."""
        super().__init__(parent)
        self.variables = variables
        self.create_inputs()
    
    def create_inputs(self):
        """Create asset projection input fields."""
        frame = ttk.LabelFrame(self, text="Asset Strategy Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Strategy selection
        self.create_styled_label(frame, "Investment Strategy:", 0, 0)
        strategy_combo = self.create_styled_combobox(
            frame, 
            self.variables['asset_strategy'], 
            ['TargetDate', 'Dynamic'], 
            0, 1
        )
        ToolTip(strategy_combo, "Choose between Target Date or Dynamic investment strategy")
        
        # Asset weights
        self.create_styled_label(frame, "Equity Weight:", 1, 0)
        equity_entry = self.create_styled_entry(
            frame, 
            self.variables['equity_weight'], 
            1, 1
        )
        ToolTip(equity_entry, "Weight of equity in the portfolio (0-1)")
        
        self.create_styled_label(frame, "Bond Weight:", 2, 0)
        bond_entry = self.create_styled_entry(
            frame, 
            self.variables['bond_weight'], 
            2, 1
        )
        ToolTip(bond_entry, "Weight of bonds in the portfolio (0-1)")
        
        # Investment return
        self.create_styled_label(frame, "Expected Return:", 3, 0)
        return_entry = self.create_styled_entry(
            frame,
            self.variables['investment_return'],
            3, 1
        )
        ToolTip(return_entry, "Expected annual investment return (e.g., 0.06 for 6%)")

class LiabilityTab(ttk.Frame, StyledWidgetMixin):
    """Liability projection tab."""
    
    def __init__(self, parent: ttk.Notebook, variables: Dict[str, Any]):
        """Initialize the liability tab."""
        super().__init__(parent)
        self.variables = variables
        self.create_inputs()
    
    def create_inputs(self):
        """Create liability projection input fields."""
        # Product details frame
        product_frame = ttk.LabelFrame(self, text="Product Details")
        product_frame.pack(fill='x', padx=10, pady=5)
        
        # Product type
        self.create_styled_label(product_frame, "Product Type:", 0, 0)
        product_combo = self.create_styled_combobox(
            product_frame,
            self.variables['product_type'],
            ['Term', 'Whole Life', 'Universal Life', 'Unit Linked'],
            0, 1
        )
        ToolTip(product_combo, "Type of insurance product")
        
        # Face amount
        self.create_styled_label(product_frame, "Face Amount:", 1, 0)
        face_amount_entry = self.create_styled_entry(
            product_frame,
            self.variables['face_amount'],
            1, 1
        )
        ToolTip(face_amount_entry, "Face amount of the insurance policy")
        
        # Premium mode
        self.create_styled_label(product_frame, "Premium Mode:", 2, 0)
        mode_combo = self.create_styled_combobox(
            product_frame,
            self.variables['premium_mode'],
            ['Annual', 'Semi-Annual', 'Quarterly', 'Monthly'],
            2, 1
        )
        ToolTip(mode_combo, "Frequency of premium payments")
        
        # Dividend option
        self.create_styled_label(product_frame, "Dividend Option:", 3, 0)
        div_combo = self.create_styled_combobox(
            product_frame,
            self.variables['dividend_option'],
            ['PaidUp', 'Cash', 'Premium Reduction'],
            3, 1
        )
        ToolTip(div_combo, "How dividends should be handled")
        
        # Policyholder details frame
        holder_frame = ttk.LabelFrame(self, text="Policyholder Details")
        holder_frame.pack(fill='x', padx=10, pady=5)
        
        # Sex
        self.create_styled_label(holder_frame, "Sex:", 0, 0)
        sex_combo = self.create_styled_combobox(
            holder_frame,
            self.variables['sex'],
            ['Male', 'Female'],
            0, 1
        )
        
        # Smoking status
        self.create_styled_label(holder_frame, "Smoking Status:", 1, 0)
        smoking_combo = self.create_styled_combobox(
            holder_frame,
            self.variables['smoking_status'],
            ['Non-Smoker', 'Smoker'],
            1, 1
        )
        
        # Occupation class
        self.create_styled_label(holder_frame, "Occupation Class:", 2, 0)
        occ_combo = self.create_styled_combobox(
            holder_frame,
            self.variables['occupation_class'],
            ['Standard', 'Professional', 'Manual'],
            2, 1
        )
        
        # Underwriting class
        self.create_styled_label(holder_frame, "Underwriting Class:", 3, 0)
        uw_combo = self.create_styled_combobox(
            holder_frame,
            self.variables['underwriting_class'],
            ['Preferred', 'Standard', 'Substandard'],
            3, 1
        )

class AssumptionsTab(ttk.Frame, StyledWidgetMixin):
    """Actuarial assumptions tab."""
    
    def __init__(self, parent: ttk.Notebook, variables: Dict[str, Any]):
        """Initialize the assumptions tab."""
        super().__init__(parent)
        self.variables = variables
        self.create_inputs()
    
    def create_inputs(self):
        """Create actuarial assumptions input fields."""
        # Mortality frame
        mort_frame = ttk.LabelFrame(self, text="Mortality Assumptions")
        mort_frame.pack(fill='x', padx=10, pady=5)
        
        # Mortality table
        self.create_styled_label(mort_frame, "Mortality Table:", 0, 0)
        table_combo = self.create_styled_combobox(
            mort_frame,
            self.variables['mortality_table'],
            ['2012 IAM', '2017 CSO'],
            0, 1
        )
        ToolTip(table_combo, "Base mortality table to use")
        
        # Mortality multiplier
        self.create_styled_label(mort_frame, "Mortality Multiplier:", 1, 0)
        mult_entry = self.create_styled_entry(
            mort_frame,
            self.variables['mortality_multiplier'],
            1, 1
        )
        ToolTip(mult_entry, "Multiplier applied to base mortality rates")
        
        # Other assumptions frame
        other_frame = ttk.LabelFrame(self, text="Other Assumptions")
        other_frame.pack(fill='x', padx=10, pady=5)
        
        # Lapse rate
        self.create_styled_label(other_frame, "Lapse Rate:", 0, 0)
        lapse_entry = self.create_styled_entry(
            other_frame,
            self.variables['lapse_rate'],
            0, 1
        )
        ToolTip(lapse_entry, "Annual lapse rate (e.g., 0.05 for 5%)")
        
        # Inflation rate
        self.create_styled_label(other_frame, "Inflation Rate:", 1, 0)
        infl_entry = self.create_styled_entry(
            other_frame,
            self.variables['inflation_rate'],
            1, 1
        )
        ToolTip(infl_entry, "Annual inflation rate (e.g., 0.02 for 2%)")
