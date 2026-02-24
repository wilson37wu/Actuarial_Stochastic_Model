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
        "seaborn>=0.11.0",
        "streamlit>=1.24.0",
        "plotly>=5.15.0",
        "openpyxl>=3.1.0",
        "xlsxwriter>=3.1.9",
        "reportlab>=4.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.3.0",
            "flake8>=4.0.0",
        ]
    },
)
