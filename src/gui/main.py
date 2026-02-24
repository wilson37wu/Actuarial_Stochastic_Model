"""
Main GUI application module.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any
import json
import os
import logging
import traceback
import pandas as pd
from datetime import date, datetime, timedelta

from .styles import configure_styles
from .tabs import AssetTab, LiabilityTab, AssumptionsTab
from ..enums import (
    Sex, SmokingStatus, OccupationClass, UnderwritingClass,
    ProductType, DividendOption, AssetClass, PremiumMode
)
from ..liability import LiabilityModel
from ..products import (
    BaseInsuranceContract, TermInsurance, WholeLifeInsurance,
    ParticipatingWholeLife, UniversalLife, UnitLinkedInsurance
)
from ..fixed_income import Bond
from ..public_equity import Equity
from ..asset_model import AssetModel
from ..investment import DynamicStrategy, TargetDateStrategy
from ..actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption
)

# Configure logging
logger = logging.getLogger(__name__)

def create_sample_assumptions():
    """Create sample actuarial assumptions for testing."""
    # Create sample mortality table
    mortality_table = MortalityTable({
        35: 0.001, 36: 0.00102, 37: 0.00104, 38: 0.00106, 39: 0.00108,
        40: 0.0011, 41: 0.00112, 42: 0.00114, 43: 0.00116, 44: 0.00118,
        45: 0.0012, 46: 0.00123, 47: 0.00126, 48: 0.00129, 49: 0.00132,
        50: 0.00135, 51: 0.00139, 52: 0.00143, 53: 0.00147, 54: 0.00151
    })
    
    # Create sample lapse assumption with numeric keys only
    lapse_rates = {
        1: 0.15,  # Higher lapse in first year
        2: 0.10,
        3: 0.08,
        4: 0.07,
        5: 0.06,
        6: 0.05,  # Ultimate lapse rate
        7: 0.05,
        8: 0.05,
        9: 0.05,
        10: 0.05
    }
    lapse_assumption = LapseAssumption(lapse_rates)
    
    # Create sample inflation assumption
    inflation_assumption = InflationAssumption(
        base_rate=0.025,  # Base inflation rate
        wage_inflation=0.035,  # Wage inflation rate
        medical_inflation=0.045  # Medical inflation rate
    )
    
    return mortality_table, lapse_assumption, inflation_assumption

class ModelGUI:
    """Main GUI application class."""
    
    def __init__(self):
        """Initialize the GUI application."""
        try:
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
            
            logger.info("GUI initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GUI: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def init_variables(self):
        """Initialize input variables."""
        try:
            variables = {
                # Asset variables
                'asset_strategy': tk.StringVar(value='TargetDate'),
                'equity_weight': tk.StringVar(value='0.6'),
                'bond_weight': tk.StringVar(value='0.4'),
                'expected_return': tk.StringVar(value='0.06'),
                
                # Liability variables
                'product_type': tk.StringVar(value='Term'),
                'face_amount': tk.StringVar(value='100000'),
                'premium': tk.StringVar(value='1000'),
                'premium_mode': tk.StringVar(value='Annual'),
                
                # Assumption variables
                'mortality_multiplier': tk.StringVar(value='1.0'),
                'lapse_rate': tk.StringVar(value='0.05'),
                'inflation_rate': tk.StringVar(value='0.02')
            }
            return variables
        except Exception as e:
            logger.error(f"Failed to initialize variables: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def create_control_buttons(self):
        """Create control buttons."""
        try:
            # Create frame for buttons
            button_frame = ttk.Frame(self.root)
            button_frame.pack(side='bottom', fill='x', padx=10, pady=5)
            
            # Run model button
            run_button = ttk.Button(
                button_frame,
                text="Run Model",
                command=self.run_model,
                style='Primary.TButton'
            )
            run_button.pack(side='left', padx=5)
            
            # Reset button
            reset_button = ttk.Button(
                button_frame,
                text="Reset",
                command=self.reset_defaults,
                style='Secondary.TButton'
            )
            reset_button.pack(side='left', padx=5)
            
            # Save inputs button
            save_button = ttk.Button(
                button_frame,
                text="Save Inputs",
                command=self.save_inputs,
                style='Secondary.TButton'
            )
            save_button.pack(side='left', padx=5)
            
            # Load inputs button
            load_button = ttk.Button(
                button_frame,
                text="Load Inputs",
                command=self.load_inputs,
                style='Secondary.TButton'
            )
            load_button.pack(side='left', padx=5)
            
        except Exception as e:
            logger.error(f"Error creating control buttons: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def run_model(self):
        """Run the model with current settings."""
        try:
            if not self.validate_inputs():
                return
            
            # Create sample assumptions
            mortality_table, lapse_assumption, inflation_assumption = create_sample_assumptions()
            
            # Create investment strategy
            if self.variables['asset_strategy'].get() == 'Dynamic':
                strategy = DynamicStrategy(
                    float(self.variables['equity_weight'].get()),
                    float(self.variables['bond_weight'].get())
                )
            else:
                strategy = TargetDateStrategy(2045)  # Example target year
            
            # Create sample investment portfolio
            today = date.today()
            bonds = [
                Bond(
                    id='GOVT_1',
                    par_value=1000000,
                    coupon_rate=0.03,
                    maturity_date=today + timedelta(days=3650),  # 10-year bond
                    credit_rating='AA',
                    payment_frequency=2,  # Semi-annual
                    issue_date=today - timedelta(days=365),  # Issued 1 year ago
                    purchase_price=1020000  # Purchased at a premium
                ),
                Bond(
                    id='CORP_1',
                    par_value=500000,
                    coupon_rate=0.045,
                    maturity_date=today + timedelta(days=1825),  # 5-year bond
                    credit_rating='A',
                    payment_frequency=2,
                    issue_date=today - timedelta(days=180),  # Issued 6 months ago
                    purchase_price=495000  # Purchased at a discount
                )
            ]
            
            equities = [
                Equity(
                    id='STOCK_1',
                    quantity=10000,
                    initial_price=50.0,
                    dividend_yield=0.02,
                    beta=1.1,
                    sector='Technology',
                    purchase_date=date.today()
                ),
                Equity(
                    id='STOCK_2',
                    quantity=5000,
                    initial_price=75.0,
                    dividend_yield=0.03,
                    beta=0.9,
                    sector='Healthcare',
                    purchase_date=date.today()
                )
            ]
            
            # Create asset model
            asset_model = AssetModel({
                'fixed_income': {'default_spread': 0.01},
                'equity': {'market_volatility': 0.15}
            })
            
            # Set economic scenarios
            today = date.today()
            dates = pd.date_range(start=today, end=today + timedelta(days=3650), freq='M')
            scenarios = pd.DataFrame({
                'risk_free_rate': [0.02] * len(dates),  # 2% risk-free rate
                'equity_return': [0.08] * len(dates),    # 8% equity return
                'credit_spread': [0.01] * len(dates),    # 1% credit spread
                'inflation_rate': [0.025] * len(dates)   # 2.5% inflation
            }, index=dates)
            asset_model.set_economic_scenarios(scenarios)
            
            # Create sample contract based on inputs
            contract = WholeLifeInsurance(
                face_amount=float(self.variables['face_amount'].get()),
                guaranteed_rate=0.03,  # 3% guaranteed rate
                issue_date=date.today(),
                issue_age=35,
                sex=Sex.MALE,
                smoking_status=SmokingStatus.NON_SMOKER,
                underwriting_class=UnderwritingClass.STANDARD,
                occupation_class=OccupationClass.PROFESSIONAL,
                premium=float(self.variables['premium'].get()),
                premium_mode=PremiumMode.ANNUAL,
                policy_number='WL' + datetime.now().strftime('%Y%m%d%H%M'),
                term_length=None  # Whole life has no term
            )
            
            # Create liability model
            liability_model = LiabilityModel(
                mortality_table=mortality_table,
                lapse_assumption=lapse_assumption,
                inflation_assumption=inflation_assumption
            )
            
            # Add contract to liability model
            liability_model.add_contract(contract)
            
            liability_results = liability_model.project_cashflows(
                valuation_date=date.today(),
                projection_years=30
            )
            
            # Project investment portfolio
            investment_results = asset_model.project_portfolio(
                bonds=bonds,
                equities=equities,
                valuation_date=date.today(),
                scenario_idx=0,  # Use base scenario
                projection_years=30,
                frequency='monthly'
            )
            
            # Export results
            self.export_to_excel(liability_results, investment_results)
            
            messagebox.showinfo("Success", "Model run completed successfully!")
            
        except Exception as e:
            logger.error(f"Error running model: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to run model: {str(e)}")
    
    def validate_inputs(self) -> bool:
        """Validate all input fields before running the model."""
        try:
            # Validate face amount
            face_amount = float(self.variables['face_amount'].get())
            if face_amount <= 0:
                messagebox.showerror("Validation Error", "Face amount must be greater than 0")
                return False
            
            # Validate premium
            premium = float(self.variables['premium'].get())
            if premium <= 0:
                messagebox.showerror("Validation Error", "Premium must be greater than 0")
                return False
            
            # Validate premium vs face amount
            if premium > face_amount:
                messagebox.showerror("Validation Error", "Premium cannot be greater than face amount")
                return False
            
            # Validate asset allocation if dynamic strategy
            if self.variables['asset_strategy'].get() == 'Dynamic':
                equity_weight = float(self.variables['equity_weight'].get())
                bond_weight = float(self.variables['bond_weight'].get())
                
                if not (0 <= equity_weight <= 1 and 0 <= bond_weight <= 1):
                    messagebox.showerror("Validation Error", "Asset weights must be between 0 and 1")
                    return False
                    
                if abs(equity_weight + bond_weight - 1.0) > 0.0001:
                    messagebox.showerror("Validation Error", "Asset weights must sum to 1")
                    return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", "Please enter valid numeric values")
            return False
    
    def reset_defaults(self):
        """Reset all inputs to default values."""
        try:
            self.variables = self.init_variables()
            messagebox.showinfo("Success", "All inputs reset to defaults!")
        except Exception as e:
            logger.error(f"Error resetting defaults: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to reset defaults: {str(e)}")
    
    def export_to_excel(self, liability_results, investment_results):
        """Export model results to Excel."""
        try:
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"model_results_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Export liability cashflow projections
                df_liability = pd.DataFrame({
                    'Date': liability_results.time_points,
                    'Premium': liability_results.premiums,
                    'Death_Benefit': liability_results.death_benefits,
                    'Surrender': liability_results.surrenders,
                    'Expenses': liability_results.expenses,
                    'Dividends': liability_results.dividends,
                    'Policy_Loans': liability_results.policy_loans,
                    'Loan_Repayments': liability_results.loan_repayments,
                    'Withdrawals': liability_results.withdrawals
                })
                df_liability.to_excel(writer, sheet_name='Liability_Cashflows', index=False)
                
                # Export fixed income projections if available
                if 'fixed_income_cf' in investment_results:
                    investment_results['fixed_income_cf'].to_excel(
                        writer, sheet_name='Fixed_Income_Cashflows', index=True
                    )
                
                # Export equity projections if available
                if 'equity_cf' in investment_results:
                    investment_results['equity_cf'].to_excel(
                        writer, sheet_name='Equity_Cashflows', index=True
                    )
                
                # Export combined portfolio projections if available
                if 'combined_cf' in investment_results:
                    investment_results['combined_cf'].to_excel(
                        writer, sheet_name='Portfolio_Cashflows', index=True
                    )
                
                # Export input parameters
                input_data = {
                    'Parameter': [
                        'Product Type',
                        'Face Amount',
                        'Premium',
                        'Issue Age',
                        'Sex',
                        'Smoking Status',
                        'Occupation Class',
                        'Underwriting Class',
                        'Asset Strategy',
                        'Equity Weight',
                        'Bond Weight'
                    ],
                    'Value': [
                        self.variables['product_type'].get(),
                        self.variables['face_amount'].get(),
                        self.variables['premium'].get(),
                        '35',  # Example value
                        'Male',  # Example value
                        'Non-Smoker',  # Example value
                        'Professional',  # Example value
                        'Standard',  # Example value
                        self.variables['asset_strategy'].get(),
                        self.variables['equity_weight'].get(),
                        self.variables['bond_weight'].get()
                    ]
                }
                pd.DataFrame(input_data).to_excel(writer, sheet_name='Inputs', index=False)
                
                # Format the sheets
                workbook = writer.book
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    # Adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except (TypeError, AttributeError):
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            messagebox.showinfo("Success", f"Results exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")
    
    def save_inputs(self):
        """Save input values to a JSON file."""
        try:
            # Get all variable values
            input_data = {
                name: var.get() for name, var in self.variables.items()
            }
            
            # Create a unique filename with timestamp
            timestamp = date.today().strftime("%Y%m%d")
            filename = f"model_inputs_{timestamp}.json"
            
            # Save to JSON
            with open(filename, 'w') as f:
                json.dump(input_data, f, indent=4)
            
            messagebox.showinfo("Success", f"Input parameters saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving inputs: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to save inputs: {str(e)}")
    
    def load_inputs(self):
        """Load input values from a JSON file."""
        try:
            # Ask user to select input file
            filename = filedialog.askopenfilename(
                title="Select Input File",
                filetypes=[("JSON files", "*.json")]
            )
            
            if not filename:  # User cancelled
                return
            
            # Load from JSON
            with open(filename, 'r') as f:
                input_data = json.load(f)
            
            # Update variables
            for name, value in input_data.items():
                if name in self.variables:
                    self.variables[name].set(value)
            
            messagebox.showinfo("Success", "Input parameters loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading inputs: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to load inputs: {str(e)}")
    
    def run(self):
        """Start the GUI application."""
        try:
            logger.info("Starting GUI main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in GUI main loop: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
