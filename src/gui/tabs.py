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
            self.variables['expected_return'], 
            3, 1
        )
        ToolTip(return_entry, "Expected annual return (e.g., 0.06 for 6%)")

class LiabilityTab(ttk.Frame, StyledWidgetMixin):
    """Liability projection tab."""
    
    def __init__(self, parent: ttk.Notebook, variables: Dict[str, Any]):
        """Initialize the liability tab."""
        super().__init__(parent)
        self.variables = variables
        self.create_inputs()
    
    def create_inputs(self):
        """Create liability projection input fields."""
        frame = ttk.LabelFrame(self, text="Insurance Contract Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Product type
        self.create_styled_label(frame, "Product Type:", 0, 0)
        product_combo = self.create_styled_combobox(
            frame,
            self.variables['product_type'],
            ['Term', 'WholeLife', 'Universal', 'UnitLinked'],
            0, 1
        )
        ToolTip(product_combo, "Type of insurance product")
        
        # Face amount
        self.create_styled_label(frame, "Face Amount:", 1, 0)
        face_entry = self.create_styled_entry(
            frame,
            self.variables['face_amount'],
            1, 1
        )
        ToolTip(face_entry, "Insurance face amount")
        
        # Premium
        self.create_styled_label(frame, "Premium:", 2, 0)
        premium_entry = self.create_styled_entry(
            frame,
            self.variables['premium'],
            2, 1
        )
        ToolTip(premium_entry, "Annual premium amount")
        
        # Premium mode
        self.create_styled_label(frame, "Premium Mode:", 3, 0)
        mode_combo = self.create_styled_combobox(
            frame,
            self.variables['premium_mode'],
            ['Annual', 'Semi-Annual', 'Quarterly', 'Monthly'],
            3, 1
        )
        ToolTip(mode_combo, "Premium payment frequency")

class AssumptionsTab(ttk.Frame, StyledWidgetMixin):
    """Actuarial assumptions tab."""
    
    def __init__(self, parent: ttk.Notebook, variables: Dict[str, Any]):
        """Initialize the assumptions tab."""
        super().__init__(parent)
        self.variables = variables
        self.create_inputs()
    
    def create_inputs(self):
        """Create actuarial assumptions input fields."""
        frame = ttk.LabelFrame(self, text="Actuarial Assumptions")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Mortality
        self.create_styled_label(frame, "Mortality Multiplier:", 0, 0)
        mort_entry = self.create_styled_entry(
            frame,
            self.variables['mortality_multiplier'],
            0, 1
        )
        ToolTip(mort_entry, "Multiplier for base mortality rates")
        
        # Lapse
        self.create_styled_label(frame, "Base Lapse Rate:", 1, 0)
        lapse_entry = self.create_styled_entry(
            frame,
            self.variables['lapse_rate'],
            1, 1
        )
        ToolTip(lapse_entry, "Base annual lapse rate")
        
        # Inflation
        self.create_styled_label(frame, "Inflation Rate:", 2, 0)
        infl_entry = self.create_styled_entry(
            frame,
            self.variables['inflation_rate'],
            2, 1
        )
        ToolTip(infl_entry, "Annual inflation rate")
