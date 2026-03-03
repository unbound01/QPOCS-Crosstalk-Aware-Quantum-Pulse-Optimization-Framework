# Contributing to QPOCS

Thank you for your interest in contributing to the Quantum Pulse Optimization & Crosstalk Simulator!

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker
- Describe the problem clearly
- Include code snippets and error messages
- Specify your Python version and OS

### Suggesting Features

- Open an issue with the "enhancement" label
- Explain the use case
- Describe the expected behavior

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Ensure code follows PEP 8 style
6. Commit with clear messages
7. Push to your fork
8. Open a pull request

### Code Style

- Follow PEP 8 conventions
- Use type hints where appropriate
- Add docstrings to all functions
- Include physics explanations in comments

### Testing

Before submitting:
```bash
# Test all modules
python main.py all

# Test individual components
python -c "from core import *; print('Core OK')"
python -c "from analysis import *; print('Analysis OK')"
python -c "from optimization import *; print('Optimization OK')"
```

### Documentation

- Update README.md if adding features
- Add docstrings to new functions
- Update relevant PHASE*.md files
- Include examples in GETTING_STARTED.md

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/qpocs.git
cd qpocs

# Install dependencies
pip install -r requirements.txt

# Run tests
python main.py all
```

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing!
