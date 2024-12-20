"""
GUI styles and theme configuration.
"""
from tkinter import ttk

def configure_styles(style: ttk.Style) -> None:
    """Configure the application styles."""
    # Configure label style
    style.configure(
        'Custom.TLabel',
        foreground='black',
        background='#d3d3d3',
        padding=5
    )
    
    # Configure combobox style
    style.configure(
        'Custom.TCombobox',
        fieldbackground='#d3d3d3',
        foreground='black',
        selectbackground='#d3d3d3',
        selectforeground='black'
    )
    
    # Configure button style
    style.configure(
        'Custom.TButton',
        background='#d3d3d3',
        foreground='black',
        borderwidth=1,
        relief='raised'
    )
    
    # Configure entry style
    style.configure(
        'Custom.TEntry',
        fieldbackground='#d3d3d3',
        foreground='black'
    )
    
    # Configure checkbutton style
    style.configure(
        'Custom.TCheckbutton',
        foreground='black',
        background='#d3d3d3'
    )
