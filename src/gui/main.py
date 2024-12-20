"""
Main GUI application module.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import json
import os
import pandas as pd
from datetime import date

from .styles import configure_styles
from .tabs import AssetTab, LiabilityTab, AssumptionsTab
from ..enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType, AssetClass, PremiumMode, DividendOption
)
from ..actuarial_assumptions import (
    create_sample_mortality_table,
    create_sample_lapse_assumption,
    create_sample_inflation_assumption
)
from ..investment import TargetDateStrategy, DynamicStrategy
from ..liability import LiabilityModel
from ..products import (
    BaseInsuranceContract, TermInsurance, WholeLifeInsurance,
    ParticipatingWholeLife, UniversalLife, UnitLinkedInsurance
)

class ModelGUI:
    """Main GUI application class."""
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Actuarial Model Input Manager")
        self.root.geometry("800x600")
        
        # Configure styles
        self.style = ttk.Style()
        configure_styles(self.style)
        
        # Initialize variables
        self.variables = self.init_variables()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.asset_tab = AssetTab(self.notebook, self.variables)
        self.liability_tab = LiabilityTab(self.notebook, self.variables)
        self.assumptions_tab = AssumptionsTab(self.notebook, self.variables)
        
        self.notebook.add(self.asset_tab, text='Asset Projection')
        self.notebook.add(self.liability_tab, text='Liability Projection')
        self.notebook.add(self.assumptions_tab, text='Actuarial Assumptions')
        
        # Add control buttons
        self.create_control_buttons()
    
    def init_variables(self) -> Dict[str, Any]:
        """Initialize input variables."""
        return {
            # Asset variables
            'asset_strategy': tk.StringVar(value='TargetDate'),
            'equity_weight': tk.StringVar(value='0.6'),
            'bond_weight': tk.StringVar(value='0.4'),
            
            # Liability variables
            'product_type': tk.StringVar(value='Term'),
            'face_amount': tk.StringVar(value='100000'),
            'premium_mode': tk.StringVar(value='Annual'),
            'dividend_option': tk.StringVar(value='PaidUp'),
            'sex': tk.StringVar(value='Male'),
            'smoking_status': tk.StringVar(value='Non-Smoker'),
            'occupation_class': tk.StringVar(value='Standard'),
            'underwriting_class': tk.StringVar(value='Preferred'),
            
            # Assumption variables
            'mortality_table': tk.StringVar(value='2012 IAM'),
            'mortality_multiplier': tk.StringVar(value='1.0'),
            'lapse_rate': tk.StringVar(value='0.05'),
            'inflation_rate': tk.StringVar(value='0.02'),
            'investment_return': tk.StringVar(value='0.06'),
        }
    
    def create_control_buttons(self):
        """Create control buttons."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Add Run Model button
        run_button = ttk.Button(
            button_frame,
            text="Run Model",
            command=self.run_model,
            style='Custom.TButton'
        )
        run_button.pack(side='right', padx=5)
        
        # Add Export button
        export_button = ttk.Button(
            button_frame,
            text="Export to Excel",
            command=self.export_to_excel,
            style='Custom.TButton'
        )
        export_button.pack(side='right', padx=5)
        
        # Add Reset button
        reset_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self.reset_defaults,
            style='Custom.TButton'
        )
        reset_button.pack(side='right', padx=5)
        
        # Add Save/Load buttons
        save_button = ttk.Button(
            button_frame,
            text="Save",
            command=self.save_inputs,
            style='Custom.TButton'
        )
        save_button.pack(side='right', padx=5)
        
        load_button = ttk.Button(
            button_frame,
            text="Load",
            command=self.load_inputs,
            style='Custom.TButton'
        )
        load_button.pack(side='right', padx=5)
    
    def validate_inputs(self) -> bool:
        """Validate all input fields before running the model."""
        try:
            # Validate numeric inputs
            equity_weight = float(self.variables['equity_weight'].get())
            bond_weight = float(self.variables['bond_weight'].get())
            if not (0 <= equity_weight <= 1 and 0 <= bond_weight <= 1):
                raise ValueError("Asset weights must be between 0 and 1")
            if abs(equity_weight + bond_weight - 1.0) > 0.0001:
                raise ValueError("Asset weights must sum to 1")
            
            face_amount = float(self.variables['face_amount'].get())
            if face_amount <= 0:
                raise ValueError("Face amount must be positive")
            
            mortality_multiplier = float(self.variables['mortality_multiplier'].get())
            if mortality_multiplier <= 0:
                raise ValueError("Mortality multiplier must be positive")
            
            lapse_rate = float(self.variables['lapse_rate'].get())
            if not 0 <= lapse_rate <= 1:
                raise ValueError("Lapse rate must be between 0 and 1")
            
            inflation_rate = float(self.variables['inflation_rate'].get())
            if inflation_rate < 0:
                raise ValueError("Inflation rate cannot be negative")
            
            investment_return = float(self.variables['investment_return'].get())
            if investment_return < -1:
                raise ValueError("Investment return cannot be less than -100%")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False
    
    def reset_defaults(self):
        """Reset all inputs to default values."""
        default_vars = self.init_variables()
        for name, var in self.variables.items():
            var.set(default_vars[name].get())
        messagebox.showinfo("Success", "All inputs have been reset to defaults")
    
    def run_model(self):
        """Run the model with current settings."""
        if not self.validate_inputs():
            return
        
        try:
            # Create mortality table
            mortality_table = create_sample_mortality_table()
            mortality_table.apply_multiplier(
                float(self.variables['mortality_multiplier'].get())
            )
            
            # Create lapse assumption
            lapse_assumption = create_sample_lapse_assumption(
                float(self.variables['lapse_rate'].get())
            )
            
            # Create inflation assumption
            inflation_assumption = create_sample_inflation_assumption(
                float(self.variables['inflation_rate'].get())
            )
            
            # Create investment strategy
            if self.variables['asset_strategy'].get() == 'TargetDate':
                strategy = TargetDateStrategy(
                    equity_weight=float(self.variables['equity_weight'].get()),
                    bond_weight=float(self.variables['bond_weight'].get())
                )
            else:
                strategy = DynamicStrategy(
                    equity_weight=float(self.variables['equity_weight'].get()),
                    bond_weight=float(self.variables['bond_weight'].get())
                )
            
            # Create liability model
            model = LiabilityModel(
                mortality_table=mortality_table,
                lapse_assumption=lapse_assumption,
                inflation_assumption=inflation_assumption
            )
            
            # Create insurance contract
            product_type = self.variables['product_type'].get()
            contract_params = {
                'face_amount': float(self.variables['face_amount'].get()),
                'issue_date': date.today(),
                'sex': Sex[self.variables['sex'].get().upper()],
                'smoking_status': SmokingStatus[self.variables['smoking_status'].get().upper().replace('-', '_')],
                'occupation_class': OccupationClass[self.variables['occupation_class'].get().upper()],
                'underwriting_class': UnderwritingClass[self.variables['underwriting_class'].get().upper()],
                'premium_mode': PremiumMode[self.variables['premium_mode'].get().upper()],
                'dividend_option': DividendOption[self.variables['dividend_option'].get().upper()]
            }
            
            if product_type == 'Term':
                contract = TermInsurance(**contract_params)
            elif product_type == 'Whole Life':
                contract = WholeLifeInsurance(**contract_params)
            elif product_type == 'Universal Life':
                contract = UniversalLife(**contract_params)
            else:  # Unit Linked
                contract = UnitLinkedInsurance(**contract_params)
            
            model.add_contract(contract)
            
            # Run projection
            results = model.project(
                strategy,
                projection_years=30,
                scenarios=100
            )
            
            # Store results for export
            self.last_results = results
            
            messagebox.showinfo("Success", "Model run completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run model: {str(e)}")
    
    def export_to_excel(self):
        """Export model results to Excel."""
        if not hasattr(self, 'last_results'):
            messagebox.showwarning("Warning", "No results to export. Please run the model first.")
            return
        
        try:
            filename = "model_results.xlsx"
            with pd.ExcelWriter(filename) as writer:
                # Export each component of the results
                for sheet_name, df in self.last_results.items():
                    df.to_excel(writer, sheet_name=sheet_name)
            
            messagebox.showinfo("Success", f"Results exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")
    
    def save_inputs(self):
        """Save input values to a JSON file."""
        data = {
            name: var.get()
            for name, var in self.variables.items()
        }
        
        try:
            with open('model_inputs.json', 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", "Inputs saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save inputs: {str(e)}")
    
    def load_inputs(self):
        """Load input values from a JSON file."""
        try:
            with open('model_inputs.json', 'r') as f:
                data = json.load(f)
            
            for name, value in data.items():
                if name in self.variables:
                    self.variables[name].set(value)
            
            messagebox.showinfo("Success", "Inputs loaded successfully!")
        except FileNotFoundError:
            messagebox.showwarning("Warning", "No saved inputs found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inputs: {str(e)}")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
