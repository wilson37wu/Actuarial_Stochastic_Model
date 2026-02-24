import sys
import os

# Ensure src/ is on the path so tests can use 'from src.X import Y' style imports
# while also working when running pytest from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
