from setuptools import setup, find_packages

setup(
    name="actuarial_stochastic_model",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn"
    ]
)
