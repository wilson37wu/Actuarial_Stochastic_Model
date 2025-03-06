# Development Setup Guide

This guide will help you set up your development environment for the Actuarial Stochastic Model project.

## Prerequisites

- Python 3.11 or higher
- Git
- A code editor (VS Code recommended)

## Initial Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/wilson37wu/Actuarial_Stochastic_Model.git
   cd Actuarial_Stochastic_Model
   ```

2. **Set Up Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv venv_py311

   # Activate virtual environment
   # On Windows:
   .\venv_py311\Scripts\activate
   # On Unix/MacOS:
   source venv_py311/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Install all required packages
   pip install -r requirements.txt

   # For development, install additional tools
   pip install -e ".[dev]"
   ```

## Project Structure

The project follows a modular structure:
```
actuarial_stochastic_model/
├── src/                 # Source code
├── data/               # Data files
├── outputs/            # Generated outputs
├── examples/           # Example scripts
├── tests/             # Test suite
└── docs/              # Documentation
```

## Development Workflow

1. **Activate Virtual Environment**
   ```bash
   # On Windows:
   .\venv_py311\Scripts\activate
   # On Unix/MacOS:
   source venv_py311/bin/activate
   ```

2. **Run Tests**
   ```bash
   # Run all tests
   pytest

   # Run tests with coverage
   pytest --cov=src tests/
   ```

3. **Code Formatting**
   ```bash
   # Format code using black
   black src/ tests/ examples/

   # Check code style
   flake8 src/ tests/ examples/
   ```

4. **Running Examples**
   ```bash
   # Run example scripts
   python examples/product_cashflow_test.py
   ```

5. **Launch Dashboard**
   ```bash
   # Start the Streamlit dashboard
   streamlit run src/dashboard/dashboard.py
   ```

## Development Tools

### 1. Code Quality
- **black**: Code formatter
- **flake8**: Style guide enforcement
- **pytest**: Testing framework
- **pytest-cov**: Test coverage reporting

### 2. Data Analysis
- **numpy**: Numerical computations
- **pandas**: Data manipulation
- **scipy**: Scientific computing

### 3. Visualization
- **matplotlib**: Static plots
- **seaborn**: Statistical visualizations
- **plotly**: Interactive plots
- **streamlit**: Interactive dashboards

## Common Tasks

### Running the Model
1. Configure model parameters in `config/default_config.json`
2. Run example scripts from the `examples/` directory
3. Check outputs in the `outputs/` directory

### Adding New Features
1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Implement your changes
3. Add tests in `tests/` directory
4. Update documentation
5. Submit pull request

### Updating Dependencies
1. Add new packages to `requirements.txt`
2. Update development dependencies in `setup.py`
3. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check if all dependencies are installed
   - Verify Python path includes project root

2. **Configuration Issues**
   - Verify config files exist in correct location
   - Check JSON syntax in config files
   - Ensure all required parameters are present

3. **Data Access Issues**
   - Check file permissions
   - Verify data files exist in correct locations
   - Ensure paths are correctly specified

### Getting Help

1. Check existing documentation in `docs/`
2. Review example scripts in `examples/`
3. Run tests to verify system integrity
4. Check GitHub issues for similar problems

## Best Practices

### 1. Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write descriptive docstrings
- Keep functions focused and small

### 2. Testing
- Write tests for new features
- Maintain high test coverage
- Use meaningful test names
- Test edge cases

### 3. Documentation
- Update docs with new features
- Include docstrings in code
- Document configuration changes
- Add example usage

### 4. Version Control
- Make atomic commits
- Write clear commit messages
- Keep branches focused
- Regularly pull from main

## Deployment

### Local Development
1. Use `venv_py311` environment
2. Run with development config
3. Store outputs in `outputs/` directory

### Production
1. Use stable dependencies
2. Configure production settings
3. Validate all inputs
4. Log all operations

## Security Considerations

1. **Data Protection**
   - Don't commit sensitive data
   - Use environment variables
   - Validate input data
   - Sanitize outputs

2. **Access Control**
   - Manage permissions properly
   - Use secure connections
   - Follow least privilege principle
   - Regular security updates

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow coding standards
4. Add tests and documentation
5. Submit pull request

## Support

For technical support:
1. Check documentation
2. Review example code
3. Run diagnostics
4. Contact project maintainers
