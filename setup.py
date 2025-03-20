from setuptools import setup, find_packages

setup(
    name="actuarial_stochastic_model",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.23.0",
        "pandas>=1.5.0",
        "scipy>=1.9.0",
        "matplotlib>=3.6.0",
        "streamlit>=1.24.0",
        "plotly>=5.15.0",
        "openpyxl>=3.1.0"  # For Excel support
    ]
)
