"""
Entry point for the actuarial model GUI application.
Provides backward compatibility for existing imports.
"""
from src.gui.main import ModelGUI as ModelInputGUI  # Backward compatibility

def launch_gui():
    """Launch the model input GUI."""
    app = ModelInputGUI()
    app.run()

if __name__ == '__main__':
    launch_gui()
