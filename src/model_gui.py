"""
GUI interface for managing asset and liability projection inputs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
import json
import os
from datetime import date

from .enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType, AssetClass, PremiumMode
)
from .actuarial_assumptions import (
    create_sample_mortality_table,
    create_sample_lapse_assumption,
    create_sample_inflation_assumption
)
from .investment import TargetDateStrategy, DynamicStrategy
from .liability import LiabilityModel
from .products import BaseInsuranceContract

class ModelInputGUI:
    """GUI for managing model inputs."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Actuarial Model Input Manager")
        self.root.geometry("800x600")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure(
            'Custom.TButton',
            background='#d3d3d3',  # Light grey
            foreground='black',
            borderwidth=1,
            relief='raised'
        )
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.asset_tab = ttk.Frame(self.notebook)
        self.liability_tab = ttk.Frame(self.notebook)
        self.assumptions_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.asset_tab, text='Asset Projection')
        self.notebook.add(self.liability_tab, text='Liability Projection')
        self.notebook.add(self.assumptions_tab, text='Actuarial Assumptions')
        
        # Initialize input variables
        self.init_variables()
        
        # Create input forms
        self.create_asset_inputs()
        self.create_liability_inputs()
        self.create_assumption_inputs()
        
        # Add buttons
        self.create_control_buttons()
    
    def init_variables(self):
        """Initialize input variables with default values."""
        # Asset projection variables
        self.asset_strategy = tk.StringVar(value="TargetDate")
        self.equity_weight = tk.DoubleVar(value=0.6)
        self.bond_weight = tk.DoubleVar(value=0.4)
        self.target_year = tk.IntVar(value=2050)
        
        # Liability projection variables
        self.product_type = tk.StringVar(value="WHOLE_LIFE")
        self.projection_years = tk.IntVar(value=50)
        self.premium_pattern = tk.StringVar(value="LEVEL")
        
        # Actuarial assumption variables
        self.mortality_improvement = tk.BooleanVar(value=True)
        self.lapse_study_start = tk.StringVar(value="2020-01-01")
        self.inflation_base_rate = tk.DoubleVar(value=0.02)
    
    def create_asset_inputs(self):
        """Create asset projection input fields."""
        frame = ttk.LabelFrame(self.asset_tab, text="Asset Strategy Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Strategy selection
        ttk.Label(frame, text="Investment Strategy:").grid(row=0, column=0, padx=5, pady=5)
        strategy_combo = ttk.Combobox(frame, textvariable=self.asset_strategy)
        strategy_combo['values'] = ('TargetDate', 'Dynamic')
        strategy_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Asset weights
        ttk.Label(frame, text="Equity Weight:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.equity_weight).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Bond Weight:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.bond_weight).grid(row=2, column=1, padx=5, pady=5)
        
        # Target year for target date strategy
        ttk.Label(frame, text="Target Year:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.target_year).grid(row=3, column=1, padx=5, pady=5)
    
    def create_liability_inputs(self):
        """Create liability projection input fields."""
        frame = ttk.LabelFrame(self.liability_tab, text="Liability Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Product type selection
        ttk.Label(frame, text="Product Type:").grid(row=0, column=0, padx=5, pady=5)
        product_combo = ttk.Combobox(frame, textvariable=self.product_type)
        product_combo['values'] = [p.name for p in ProductType]
        product_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Projection years
        ttk.Label(frame, text="Projection Years:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.projection_years).grid(row=1, column=1, padx=5, pady=5)
        
        # Premium pattern
        ttk.Label(frame, text="Premium Pattern:").grid(row=2, column=0, padx=5, pady=5)
        pattern_combo = ttk.Combobox(frame, textvariable=self.premium_pattern)
        pattern_combo['values'] = ('LEVEL', 'INCREASING', 'DECREASING')
        pattern_combo.grid(row=2, column=1, padx=5, pady=5)
    
    def create_assumption_inputs(self):
        """Create actuarial assumption input fields."""
        frame = ttk.LabelFrame(self.assumptions_tab, text="Actuarial Assumptions")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Mortality improvement checkbox
        ttk.Checkbutton(
            frame, text="Apply Mortality Improvement",
            variable=self.mortality_improvement
        ).grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        
        # Lapse study start date
        ttk.Label(frame, text="Lapse Study Start:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.lapse_study_start).grid(row=1, column=1, padx=5, pady=5)
        
        # Inflation base rate
        ttk.Label(frame, text="Base Inflation Rate:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.inflation_base_rate).grid(row=2, column=1, padx=5, pady=5)
    
    def create_control_buttons(self):
        """Create control buttons."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Create custom button style
        button_style = {
            'style': 'Custom.TButton',
            'width': 15
        }
        
        ttk.Button(
            button_frame, text="Save Settings",
            command=self.save_settings,
            **button_style
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, text="Load Settings",
            command=self.load_settings,
            **button_style
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, text="Reset to Defaults",
            command=self.reset_defaults,
            **button_style
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, text="Run Model",
            command=self.run_model,
            **button_style
        ).pack(side='right', padx=5)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get all current settings as a dictionary."""
        return {
            'asset': {
                'strategy': self.asset_strategy.get(),
                'equity_weight': self.equity_weight.get(),
                'bond_weight': self.bond_weight.get(),
                'target_year': self.target_year.get()
            },
            'liability': {
                'product_type': self.product_type.get(),
                'projection_years': self.projection_years.get(),
                'premium_pattern': self.premium_pattern.get()
            },
            'assumptions': {
                'mortality_improvement': self.mortality_improvement.get(),
                'lapse_study_start': self.lapse_study_start.get(),
                'inflation_base_rate': self.inflation_base_rate.get()
            }
        }
    
    def save_settings(self):
        """Save current settings to a JSON file."""
        settings = self.get_settings()
        file_path = 'model_settings.json'
        
        try:
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self):
        """Load settings from a JSON file."""
        file_path = 'model_settings.json'
        
        try:
            with open(file_path, 'r') as f:
                settings = json.load(f)
            
            # Update asset settings
            self.asset_strategy.set(settings['asset']['strategy'])
            self.equity_weight.set(settings['asset']['equity_weight'])
            self.bond_weight.set(settings['asset']['bond_weight'])
            self.target_year.set(settings['asset']['target_year'])
            
            # Update liability settings
            self.product_type.set(settings['liability']['product_type'])
            self.projection_years.set(settings['liability']['projection_years'])
            self.premium_pattern.set(settings['liability']['premium_pattern'])
            
            # Update assumption settings
            self.mortality_improvement.set(settings['assumptions']['mortality_improvement'])
            self.lapse_study_start.set(settings['assumptions']['lapse_study_start'])
            self.inflation_base_rate.set(settings['assumptions']['inflation_base_rate'])
            
            messagebox.showinfo("Success", "Settings loaded successfully!")
        except FileNotFoundError:
            messagebox.showwarning("Warning", "No saved settings found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def reset_defaults(self):
        """Reset all inputs to default values."""
        self.init_variables()
        messagebox.showinfo("Success", "Settings reset to defaults!")
    
    def run_model(self):
        """Run the model with current settings."""
        try:
            settings = self.get_settings()
            
            # Create investment strategy
            if settings['asset']['strategy'] == 'TargetDate':
                investment_strategy = TargetDateStrategy(
                    target_year=settings['asset']['target_year'],
                    initial_equity=settings['asset']['equity_weight']
                )
            else:
                # Create base allocation for dynamic strategy
                base_allocation = {
                    AssetClass.LARGE_CAP_EQUITY: settings['asset']['equity_weight'],
                    AssetClass.GOVERNMENT_BOND: settings['asset']['bond_weight'],
                    AssetClass.CASH: max(0, 1 - settings['asset']['equity_weight'] - settings['asset']['bond_weight'])
                }
                investment_strategy = DynamicStrategy(
                    base_allocation=base_allocation,
                    max_deviation=0.2  # 20% maximum deviation from base allocation
                )
            
            # Create sample contract
            sample_contract = BaseInsuranceContract(
                policy_number="SAMPLE001",
                issue_date=date.today(),
                product_type=ProductType[settings['liability']['product_type']],
                face_amount=100000,  # Sample face amount
                premium=1000,  # Sample annual premium
                premium_mode=PremiumMode.ANNUAL,
                age_at_issue=35,  # Sample age
                sex=Sex.MALE,  # Sample sex
                smoking_status=SmokingStatus.NON_SMOKER,
                underwriting_class=UnderwritingClass.STANDARD
            )
            
            # Create and initialize liability model
            mortality_table = create_sample_mortality_table()
            lapse_assumption = create_sample_lapse_assumption()
            inflation_assumption = create_sample_inflation_assumption()
            
            liability_model = LiabilityModel(
                mortality_table=mortality_table,
                lapse_assumption=lapse_assumption,
                inflation_assumption=inflation_assumption
            )
            
            # Add the sample contract to the model
            liability_model.add_contract(sample_contract)
            
            # Project cash flows
            projection = liability_model.project_cashflows(
                valuation_date=date.today(),
                projection_years=settings['liability']['projection_years']
            )
            
            messagebox.showinfo("Success", "Model executed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run model: {str(e)}")
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()

def launch_gui():
    """Launch the model input GUI."""
    gui = ModelInputGUI()
    gui.run()

if __name__ == '__main__':
    launch_gui()
