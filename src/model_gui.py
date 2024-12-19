"""
GUI interface for managing asset and liability projection inputs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Tuple
import json
import os
from datetime import date
import pandas as pd

from src.enums import (
    Sex, SmokingStatus, OccupationClass,
    UnderwritingClass, ProductType, AssetClass, PremiumMode, DividendOption
)
from src.actuarial_assumptions import (
    create_sample_mortality_table,
    create_sample_lapse_assumption,
    create_sample_inflation_assumption
)
from src.investment import TargetDateStrategy, DynamicStrategy
from src.liability import LiabilityModel
from src.products import (
    BaseInsuranceContract, TermInsurance, WholeLifeInsurance,
    ParticipatingWholeLife, UniversalLife, UnitLinkedInsurance
)

class ToolTip:
    """Create a tooltip for a given widget."""
    
    def __init__(self, widget: tk.Widget, text: str):
        """Initialize the tooltip."""
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Display the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Create top-level window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip, text=self.text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            font=("Arial", "10", "normal")
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ModelInputGUI:
    """GUI for managing model inputs."""
    print("Importing PremiumMode in class")  # Debug print
    from src.enums import PremiumMode  # Try importing here
    print("PremiumMode imported in class:", PremiumMode)  # Verify import

    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Actuarial Model Input Manager")
        self.root.geometry("800x600")
        
        # Configure styles
        self.style = ttk.Style()
        
        # Configure label style
        self.style.configure(
            'Custom.TLabel',
            foreground='black',
            background='#d3d3d3',
            padding=5
        )
        
        # Configure combobox style
        self.style.configure(
            'Custom.TCombobox',
            fieldbackground='#d3d3d3',
            foreground='black',
            selectbackground='#d3d3d3',
            selectforeground='black'
        )
        
        # Configure button style
        self.style.configure(
            'Custom.TButton',
            background='#d3d3d3',
            foreground='black',
            borderwidth=1,
            relief='raised'
        )
        
        # Configure entry style
        self.style.configure(
            'Custom.TEntry',
            fieldbackground='#d3d3d3',
            foreground='black'
        )
        
        # Configure checkbutton style
        self.style.configure(
            'Custom.TCheckbutton',
            foreground='black',
            background='#d3d3d3'
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
    
    def create_styled_label(self, parent, text, row, column, **kwargs):
        """Create a styled label."""
        label = ttk.Label(
            parent,
            text=text,
            style='Custom.TLabel'
        )
        label.grid(row=row, column=column, padx=5, pady=5, sticky='w', **kwargs)
        return label
    
    def create_styled_combobox(self, parent, textvariable, values, row, column, **kwargs):
        """Create a styled combobox."""
        combo = ttk.Combobox(
            parent,
            textvariable=textvariable,
            style='Custom.TCombobox',
            state='readonly'
        )
        combo['values'] = values
        combo.grid(row=row, column=column, padx=5, pady=5, sticky='ew', **kwargs)
        return combo
    
    def create_styled_entry(self, parent, textvariable, row, column, **kwargs):
        """Create a styled entry."""
        entry = ttk.Entry(
            parent,
            textvariable=textvariable,
            style='Custom.TEntry'
        )
        entry.grid(row=row, column=column, padx=5, pady=5, sticky='ew', **kwargs)
        return entry
    
    def create_styled_checkbutton(self, parent, text, variable, row, column, **kwargs):
        """Create a styled checkbutton."""
        checkbutton = ttk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            style='Custom.TCheckbutton'
        )
        checkbutton.grid(row=row, column=column, padx=5, pady=5, sticky='w', **kwargs)
        return checkbutton

    def create_asset_inputs(self):
        """Create asset projection input fields."""
        frame = ttk.LabelFrame(self.asset_tab, text="Asset Strategy Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Strategy selection
        self.create_styled_label(frame, "Investment Strategy:", 0, 0)
        self.create_styled_combobox(frame, self.asset_strategy, ['TargetDate', 'Dynamic'], 0, 1)
        
        # Asset weights
        self.create_styled_label(frame, "Equity Weight:", 1, 0)
        equity_entry = self.create_styled_entry(frame, self.equity_weight, 1, 1)
        ToolTip(equity_entry, "Weight of equity in the portfolio (0-1)")
        
        self.create_styled_label(frame, "Bond Weight:", 2, 0)
        bond_entry = self.create_styled_entry(frame, self.bond_weight, 2, 1)
        ToolTip(bond_entry, "Weight of bonds in the portfolio (0-1)")
        
        # Target year
        self.create_styled_label(frame, "Target Year:", 3, 0)
        target_year_entry = self.create_styled_entry(frame, self.target_year, 3, 1)
        ToolTip(target_year_entry, "Target year for the investment strategy")
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)

        # Projection years
        self.create_styled_label(frame, "Projection Years:", 4, 0)
        proj_years_entry = self.create_styled_entry(frame, self.projection_years_asset, 4, 1)
        ToolTip(proj_years_entry, "Number of years to project asset returns")
    
    def create_liability_inputs(self):
        """Create liability projection input fields."""
        import sys
        print("Python path:", sys.path)  # Show Python's import path
        from src.enums import PremiumMode  # Try importing here
        print("PremiumMode imported:", PremiumMode)  # Verify import
        print("PremiumMode values:", [p.name for p in PremiumMode])  # Show values

        print("PremiumMode values:", [p.name for p in PremiumMode])  # Debug print
        frame = ttk.LabelFrame(self.liability_tab, text="Liability Settings")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Product type selection
        self.create_styled_label(frame, "Product Type:", 0, 0)
        self.create_styled_combobox(frame, self.product_type, [p.name for p in ProductType], 0, 1)
        
        # Face amount
        self.create_styled_label(frame, "Face Amount:", 1, 0)
        face_amount_entry = self.create_styled_entry(frame, self.face_amount, 1, 1)
        ToolTip(face_amount_entry, "Face amount of the insurance policy")

        # Premium
        self.create_styled_label(frame, "Premium:", 2, 0)
        premium_entry = self.create_styled_entry(frame, self.premium, 2, 1)
        ToolTip(premium_entry, "Premium amount")

        # Projection years
        self.create_styled_label(frame, "Projection Years:", 1, 0)
        projection_years_entry = self.create_styled_entry(frame, self.projection_years, 1, 1)
        ToolTip(projection_years_entry, "Number of years to project liability cash flows")
        
        # Premium mode
        self.create_styled_label(frame, "Premium Mode:", 2, 0)
        self.create_styled_combobox(frame, self.premium_mode, [p.name for p in PremiumMode], 2, 1)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
    
    def create_assumption_inputs(self):
        """Create actuarial assumption input fields."""
        frame = ttk.LabelFrame(self.assumptions_tab, text="Actuarial Assumptions")
        frame.pack(fill='x', padx=10, pady=5)
        
        # Mortality improvement checkbox
        self.create_styled_checkbutton(frame, "Apply Mortality Improvement", self.mortality_improvement, 0, 0, columnspan=2)
        
        # Lapse study start date
        self.create_styled_label(frame, "Lapse Study Start:", 1, 0)
        lapse_study_start_entry = self.create_styled_entry(frame, self.lapse_study_start, 1, 1)
        ToolTip(lapse_study_start_entry, "Start date of the lapse study (YYYY-MM-DD)")
                
        # Mortality multiplier
        self.create_styled_label(frame, "Mortality Multiplier:", 1, 0)
        mort_mult_entry = self.create_styled_entry(frame, self.mortality_multiplier, 1, 1)
        ToolTip(mort_mult_entry, "Multiplier applied to base mortality rates")

        # Base lapse rate
        self.create_styled_label(frame, "Base Lapse Rate:", 2, 0)
        base_lapse_entry = self.create_styled_entry(frame, self.base_lapse_rate, 2, 1)
        ToolTip(base_lapse_entry, "Base annual lapse rate")

        # Shock lapse
        self.create_styled_label(frame, "Shock Lapse Rate:", 3, 0)
        shock_lapse_entry = self.create_styled_entry(frame, self.shock_lapse, 3, 1)
        ToolTip(shock_lapse_entry, "Shock lapse rate at end of surrender charge period")

        # Inflation base rate
        self.create_styled_label(frame, "Base Inflation Rate:", 2, 0)
        inflation_base_rate_entry = self.create_styled_entry(frame, self.inflation_base_rate, 2, 1)
        ToolTip(inflation_base_rate_entry, "Base inflation rate for the projection")
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)

    def create_control_buttons(self):
        """Create control buttons."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Create custom button style
        self.style.configure('Export.TButton', font=('Helvetica', 10, 'bold'), foreground='green')
        
        button_style = {
            'style': 'Custom.TButton',
            'width': 15
        }
        
        export_style = {
            'style': 'Export.TButton',
            'width': 20
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
        
        ttk.Button(
            button_frame, 
            text="📊 Export Results to Excel",
            command=self.export_to_excel,
            **export_style
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
                'premium_mode': self.premium_mode.get()  # Renamed key to match its purpose
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
            self.premium_mode.set(settings['liability']['premium_mode'])  # Renamed key to match its purpose
            
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
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validate all input fields before running the model."""
        try:
            # Validate projection years
            try:
                proj_years = int(self.projection_years.get())
                if proj_years <= 0:
                    return False, "Projection years must be a positive integer"
            except ValueError:
                return False, "Projection years must be a valid number"
            
            # Validate asset weights
            try:
                equity = float(self.equity_weight.get())
                bond = float(self.bond_weight.get())
                if not (0 <= equity <= 1 and 0 <= bond <= 1):
                    return False, "Asset weights must be between 0 and 1"
                if equity + bond > 1:
                    return False, "Sum of asset weights cannot exceed 100%"
            except ValueError:
                return False, "Asset weights must be valid numbers"
            
            # Validate target year
            if self.asset_strategy.get() == 'TargetDate':
                try:
                    target_year = int(self.target_year.get())
                    current_year = pd.Timestamp.today().year
                    if target_year < current_year:
                        return False, f"Target year must be greater than or equal to {current_year}"
                except ValueError:
                    return False, "Target year must be a valid number"
            
            # Validate inflation rate
            try:
                inflation = float(self.inflation_base_rate.get())
                if not (-0.1 <= inflation <= 0.2):  # Allow deflation up to -10% and inflation up to 20%
                    return False, "Inflation rate must be between -10% and 20%"
            except ValueError:
                return False, "Inflation rate must be a valid number"
            
            # Validate lapse study start date
            try:
                pd.Timestamp(self.lapse_study_start.get())
            except ValueError:
                return False, "Lapse study start date must be in YYYY-MM-DD format"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def run_model(self):
        """Run the model with current settings."""
        try:
            # First validate all inputs
            is_valid, error_message = self.validate_inputs()
            if not is_valid:
                messagebox.showerror("Input Error", error_message)
                return
            
            settings = self.get_settings()
            
            # Create investment strategy
            try:
                if settings['asset']['strategy'] == 'TargetDate':
                    investment_strategy = TargetDateStrategy(
                        target_year=int(settings['asset']['target_year']),
                        initial_equity=float(settings['asset']['equity_weight'])
                    )
                else:
                    # Create base allocation for dynamic strategy
                    equity_weight = float(settings['asset']['equity_weight'])
                    bond_weight = float(settings['asset']['bond_weight'])
                    cash_weight = max(0, 1 - equity_weight - bond_weight)
                    
                    base_allocation = {
                        AssetClass.LARGE_CAP_EQUITY: equity_weight,
                        AssetClass.GOVERNMENT_BOND: bond_weight,
                        AssetClass.CASH: cash_weight
                    }
                    investment_strategy = DynamicStrategy(
                        base_allocation=base_allocation,
                        max_deviation=0.2  # 20% maximum deviation from base allocation
                    )
            except Exception as e:
                messagebox.showerror("Strategy Error", f"Failed to create investment strategy: {str(e)}")
                return
            
            # Create sample contract based on product type
            try:
                contract_class = {
                    'TERM': TermInsurance,
                    'WHOLE_LIFE': WholeLifeInsurance,
                    'PAR_WHOLE_LIFE': ParticipatingWholeLife,
                    'UNIVERSAL_LIFE': UniversalLife,
                    'UNIT_LINKED': UnitLinkedInsurance
                }[settings['liability']['product_type']]
            except KeyError:
                messagebox.showerror("Product Error", f"Invalid product type: {settings['liability']['product_type']}")
                return
            
            # Parse the valuation date (today's date)
            try:
                valuation_date = pd.Timestamp.today().date()
            except Exception as e:
                messagebox.showerror("Date Error", f"Failed to create valuation date: {str(e)}")
                return
            
            # Create contract with appropriate parameters
            try:
                base_params = {
                    'policy_number': "SAMPLE001",
                    'issue_date': valuation_date,
                    'term_length': int(settings['liability']['projection_years']),
                    'premium': 1000,  # Fixed annual premium for simplicity
                    'issue_age': 35,  # Sample age
                    'sex': Sex.MALE,  # Sample sex
                    'smoking_status': SmokingStatus.NON_SMOKER,
                    'occupation_class': OccupationClass.PROFESSIONAL,
                    'underwriting_class': UnderwritingClass.STANDARD,
                    'premium_mode': getattr(PremiumMode, settings['liability']['premium_mode'])
                }
            except Exception as e:
                messagebox.showerror("Contract Error", f"Failed to create contract parameters: {str(e)}")
                return

            # Create the specific contract type
            try:
                if settings['liability']['product_type'] == 'TERM':
                    sample_contract = contract_class(
                        face_amount=100000,
                        **base_params
                    )
                elif settings['liability']['product_type'] == 'WHOLE_LIFE':
                    sample_contract = contract_class(
                        face_amount=100000,
                        guaranteed_rate=float(settings['assumptions']['inflation_base_rate']),
                        **base_params
                    )
                elif settings['liability']['product_type'] == 'PAR_WHOLE_LIFE':
                    sample_contract = contract_class(
                        face_amount=100000,
                        guaranteed_rate=float(settings['assumptions']['inflation_base_rate']),
                        dividend_option=DividendOption.CASH,
                        dividend_scale=float(settings['assumptions']['inflation_base_rate']) + 0.02,  # 2% above guaranteed rate
                        **base_params
                    )
                elif settings['liability']['product_type'] == 'UNIVERSAL_LIFE':
                    sample_contract = contract_class(
                        initial_face_amount=100000,
                        min_guaranteed_rate=float(settings['assumptions']['inflation_base_rate']) - 0.01,  # 1% below inflation
                        current_credited_rate=float(settings['assumptions']['inflation_base_rate']) + 0.01,  # 1% above inflation
                        cost_of_insurance={i: 0.001 * (1.05 ** i) for i in range(int(settings['liability']['projection_years']))},
                        **base_params
                    )
                else:  # UNIT_LINKED
                    equity_weight = float(settings['asset']['equity_weight'])
                    bond_weight = float(settings['asset']['bond_weight'])
                    
                    sample_contract = contract_class(
                        initial_face_amount=100000,
                        investment_strategy='BALANCED',
                        fund_allocation={
                            'equity': equity_weight,
                            'bond': bond_weight
                        },
                        fund_charges={'equity': 0.015, 'bond': 0.01},
                        **base_params
                    )
            except Exception as e:
                messagebox.showerror("Contract Error", f"Failed to create specific contract type: {str(e)}")
                return
            
            # Create and initialize liability model
            try:
                mortality_table = create_sample_mortality_table()
                lapse_assumption = create_sample_lapse_assumption()
                inflation_assumption = create_sample_inflation_assumption()
                
                liability_model = LiabilityModel(
                    mortality_table=mortality_table,
                    lapse_assumption=lapse_assumption,
                    inflation_assumption=inflation_assumption,
                    investment_returns=None  # We'll set this based on the investment strategy later
                )
            except Exception as e:
                messagebox.showerror("Model Error", f"Failed to initialize liability model: {str(e)}")
                return
            
            # Add the sample contract to the model and project cash flows
            try:
                liability_model.add_contract(sample_contract)
                projection = liability_model.project_cashflows(
                    valuation_date=valuation_date,
                    projection_years=int(settings['liability']['projection_years'])
                )
                
                # Show success message with some basic projection results
                total_premium = sum(projection.premiums)
                total_benefit = sum(projection.death_benefits)
                total_surrender = sum(projection.surrenders)
                
                messagebox.showinfo(
                    "Success",
                    f"Model executed successfully!\n\n"
                    f"Total Premium: ${total_premium:,.2f}\n"
                    f"Total Death Benefits: ${total_benefit:,.2f}\n"
                    f"Total Surrender Value: ${total_surrender:,.2f}"
                )
                
            except Exception as e:
                messagebox.showerror("Projection Error", f"Failed to project cash flows: {str(e)}")
                return
            
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
    
    def export_to_excel(self):
        """Export model results to Excel."""
        try:
            # First try to import openpyxl
            try:
                import openpyxl
            except ImportError:
                messagebox.showerror(
                    "Missing Dependency",
                    "The openpyxl package is required for Excel export.\n"
                    "Please install it using:\n"
                    "pip install openpyxl"
                )
                return
                
            # First validate all inputs
            is_valid, error_message = self.validate_inputs()
            if not is_valid:
                messagebox.showerror("Input Error", error_message)
                return
            
            settings = self.get_settings()
            
            # Run the model to get projections
            valuation_date = pd.Timestamp.today().date()
            
            # Create investment strategy
            if settings['asset']['strategy'] == 'TargetDate':
                investment_strategy = TargetDateStrategy(
                    target_year=int(settings['asset']['target_year']),
                    initial_equity=float(settings['asset']['equity_weight'])
                )
            else:
                equity_weight = float(settings['asset']['equity_weight'])
                bond_weight = float(settings['asset']['bond_weight'])
                cash_weight = max(0, 1 - equity_weight - bond_weight)
                
                base_allocation = {
                    AssetClass.LARGE_CAP_EQUITY: equity_weight,
                    AssetClass.GOVERNMENT_BOND: bond_weight,
                    AssetClass.CASH: cash_weight
                }
                investment_strategy = DynamicStrategy(
                    base_allocation=base_allocation,
                    max_deviation=0.2
                )
            
            # Create contract
            contract_class = {
                'TERM': TermInsurance,
                'WHOLE_LIFE': WholeLifeInsurance,
                'PAR_WHOLE_LIFE': ParticipatingWholeLife,
                'UNIVERSAL_LIFE': UniversalLife,
                'UNIT_LINKED': UnitLinkedInsurance
            }[settings['liability']['product_type']]
            
            base_params = {
                'policy_number': "SAMPLE001",
                'issue_date': valuation_date,
                'term_length': int(settings['liability']['projection_years']),
                'premium': 1000,
                'issue_age': 35,
                'sex': Sex.MALE,
                'smoking_status': SmokingStatus.NON_SMOKER,
                'occupation_class': OccupationClass.PROFESSIONAL,
                'underwriting_class': UnderwritingClass.STANDARD,
                'premium_mode': getattr(PremiumMode, settings['liability']['premium_mode'])
            }
            
            # Create specific contract type
            if settings['liability']['product_type'] == 'TERM':
                sample_contract = contract_class(
                    face_amount=100000,
                    **base_params
                )
            elif settings['liability']['product_type'] == 'WHOLE_LIFE':
                sample_contract = contract_class(
                    face_amount=100000,
                    guaranteed_rate=float(settings['assumptions']['inflation_base_rate']),
                    **base_params
                )
            elif settings['liability']['product_type'] == 'PAR_WHOLE_LIFE':
                sample_contract = contract_class(
                    face_amount=100000,
                    guaranteed_rate=float(settings['assumptions']['inflation_base_rate']),
                    dividend_option=DividendOption.CASH,
                    dividend_scale=float(settings['assumptions']['inflation_base_rate']) + 0.02,
                    **base_params
                )
            elif settings['liability']['product_type'] == 'UNIVERSAL_LIFE':
                sample_contract = contract_class(
                    initial_face_amount=100000,
                    min_guaranteed_rate=float(settings['assumptions']['inflation_base_rate']) - 0.01,
                    current_credited_rate=float(settings['assumptions']['inflation_base_rate']) + 0.01,
                    cost_of_insurance={i: 0.001 * (1.05 ** i) for i in range(int(settings['liability']['projection_years']))},
                    **base_params
                )
            else:  # UNIT_LINKED
                sample_contract = contract_class(
                    initial_face_amount=100000,
                    investment_strategy='BALANCED',
                    fund_allocation={
                        'equity': equity_weight,
                        'bond': bond_weight
                    },
                    fund_charges={'equity': 0.015, 'bond': 0.01},
                    **base_params
                )
            
            # Create and initialize liability model
            mortality_table = create_sample_mortality_table()
            lapse_assumption = create_sample_lapse_assumption()
            inflation_assumption = create_sample_inflation_assumption()
            
            liability_model = LiabilityModel(
                mortality_table=mortality_table,
                lapse_assumption=lapse_assumption,
                inflation_assumption=inflation_assumption,
                investment_returns=None
            )
            
            # Add contract and project cash flows
            liability_model.add_contract(sample_contract)
            projection = liability_model.project_cashflows(
                valuation_date=valuation_date,
                projection_years=int(settings['liability']['projection_years'])
            )
            
            # Convert projection to DataFrame
            df = projection.to_dataframe()
            
            # Add summary statistics
            summary_df = pd.DataFrame({
                'Metric': [
                    'Total Premium',
                    'Total Death Benefits',
                    'Total Surrender Value',
                    'Total Expenses',
                    'Total Dividends',
                    'Total Policy Loans',
                    'Total Loan Repayments',
                    'Total Withdrawals'
                ],
                'Value': [
                    df['Premium'].sum(),
                    df['Death_Benefit'].sum(),
                    df['Surrender'].sum(),
                    df['Expenses'].sum(),
                    df['Dividends'].sum(),
                    df['Policy_Loans'].sum(),
                    df['Loan_Repayments'].sum(),
                    df['Withdrawals'].sum()
                ]
            })
            
            # Create Excel writer
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f'model_results_{timestamp}.xlsx'
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Write settings to first sheet
                pd.DataFrame([
                    ['Asset Settings', ''],
                    ['Strategy', settings['asset']['strategy']],
                    ['Equity Weight', settings['asset']['equity_weight']],
                    ['Bond Weight', settings['asset']['bond_weight']],
                    ['Target Year', settings['asset']['target_year']],
                    ['', ''],
                    ['Liability Settings', ''],
                    ['Product Type', settings['liability']['product_type']],
                    ['Projection Years', settings['liability']['projection_years']],
                    ['Premium Mode', settings['liability']['premium_mode']],
                    ['', ''],
                    ['Assumption Settings', ''],
                    ['Mortality Improvement', settings['assumptions']['mortality_improvement']],
                    ['Lapse Study Start', settings['assumptions']['lapse_study_start']],
                    ['Inflation Base Rate', settings['assumptions']['inflation_base_rate']]
                ], columns=['Setting', 'Value']).to_excel(writer, sheet_name='Settings', index=False)
                
                # Write summary to second sheet
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Write detailed projections to third sheet
                df.to_excel(writer, sheet_name='Projections', index=False)
            
            messagebox.showinfo("Success", f"Results exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
    
    def init_variables(self):
        """Initialize all input variables with default values."""
        # Asset strategy variables
        self.projection_years_asset = tk.StringVar(value='30')
        self.asset_strategy = tk.StringVar(value='Dynamic')
        self.equity_weight = tk.StringVar(value='0.6')
        self.bond_weight = tk.StringVar(value='0.4')
        self.target_year = tk.StringVar(value='2050')
        
        # Liability variables
        self.product_type = tk.StringVar(value='PAR_WHOLE_LIFE')
        self.projection_years = tk.StringVar(value='50')
        self.premium_mode = tk.StringVar(value='ANNUAL')
        self.face_amount = tk.StringVar(value='1000000')
        self.premium = tk.StringVar(value='10000')
        
        # Assumption variables
        self.mortality_improvement = tk.BooleanVar(value=True)
        self.mortality_multiplier = tk.StringVar(value='1.0')
        self.base_lapse_rate = tk.StringVar(value='0.05')
        self.shock_lapse = tk.StringVar(value='0.15')
        self.lapse_study_start = tk.StringVar(value=pd.Timestamp.today().strftime('%Y-%m-%d'))  # Use today's date as default
        self.inflation_base_rate = tk.StringVar(value='0.02')       
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()

def launch_gui():
    """Launch the model input GUI."""
    gui = ModelInputGUI()
    gui.run()

if __name__ == '__main__':
    launch_gui()
