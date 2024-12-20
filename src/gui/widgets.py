"""
Common GUI widgets and utilities.
"""
import tkinter as tk
from tkinter import ttk
from typing import Any

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

class StyledWidgetMixin:
    """Mixin class providing styled widget creation methods."""
    
    @staticmethod
    def create_styled_label(parent: ttk.Frame, text: str, row: int, column: int, **kwargs) -> ttk.Label:
        """Create a styled label."""
        label = ttk.Label(
            parent,
            text=text,
            style='Custom.TLabel'
        )
        label.grid(row=row, column=column, padx=5, pady=5, sticky='w', **kwargs)
        return label
    
    @staticmethod
    def create_styled_combobox(parent: ttk.Frame, textvariable: Any, values: list, 
                             row: int, column: int, **kwargs) -> ttk.Combobox:
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
    
    @staticmethod
    def create_styled_entry(parent: ttk.Frame, textvariable: Any, row: int, 
                          column: int, **kwargs) -> ttk.Entry:
        """Create a styled entry."""
        entry = ttk.Entry(
            parent,
            textvariable=textvariable,
            style='Custom.TEntry'
        )
        entry.grid(row=row, column=column, padx=5, pady=5, sticky='ew', **kwargs)
        return entry
    
    @staticmethod
    def create_styled_checkbutton(parent: ttk.Frame, text: str, variable: Any, 
                                row: int, column: int, **kwargs) -> ttk.Checkbutton:
        """Create a styled checkbutton."""
        checkbutton = ttk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            style='Custom.TCheckbutton'
        )
        checkbutton.grid(row=row, column=column, padx=5, pady=5, sticky='w', **kwargs)
        return checkbutton
