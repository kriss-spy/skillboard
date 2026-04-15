# Contributing to Skillboard

Thank you for your interest in contributing to Skillboard! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/skillboard.git
   cd skillboard
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation:**
   ```bash
   skillboard --version
   ```

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run these before committing:

```bash
# Format code
black skillboard/ tests/

# Lint
ruff check --fix skillboard/ tests/

# Type check
mypy skillboard/

# Run tests
pytest
```

## Testing

Write tests for new features and bug fixes:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=skillboard

# Run specific test file
pytest tests/test_manager.py

# Run with verbose output
pytest -v
```

## Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   # or
   git checkout -b fix/my-bugfix
   ```

2. **Make your changes** with clear, focused commits

3. **Add tests** for your changes

4. **Update documentation** if needed

5. **Run the test suite** to ensure everything passes

6. **Submit a pull request**

## Commit Messages

Use clear, descriptive commit messages:

- ✨ `feat: add new feature`
- 🐛 `fix: resolve issue with X`
- 📚 `docs: update README`
- ✅ `test: add tests for Y`
- 🔧 `refactor: improve Z`

## Pull Request Process

1. Ensure your PR description clearly describes the problem and solution
2. Reference any relevant issues
3. Ensure all CI checks pass
4. Wait for review from maintainers

## Code Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for public APIs
- Keep functions focused and small
- Write clear, readable code

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Skillboard version
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for questions or join discussions.

Thank you for contributing! 🎉
