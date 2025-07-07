# Publishing Guide

This guide walks you through publishing the MCP Config Sync package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/)
2. **API Tokens**: Generate API tokens for both PyPI and TestPyPI for secure authentication

## Setup API Tokens

### For TestPyPI:
1. Go to [TestPyPI Account Settings](https://test.pypi.org/manage/account/)
2. Scroll to "API tokens" and click "Add API token"
3. Give it a name like "mcp-config-sync-test"
4. Set scope to "Entire account" (or specific to this project once uploaded)
5. Copy the token (starts with `pypi-`)

### For PyPI:
1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Follow the same steps as TestPyPI

## Configure Authentication

Create a `~/.pypirc` file:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

## Publishing Steps

### 1. Test Locally

```bash
# Install in development mode
pip install -e .

# Test the CLI
mcp-config-sync --help
mcp-config-sync --list-all
```

### 2. Run Tests (when available)

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
black --check mcp_config_sync/
isort --check-only mcp_config_sync/
mypy mcp_config_sync/
```

### 3. Update Version

Update the version in `pyproject.toml` and `mcp_config_sync/__init__.py`:

```toml
version = "0.1.1"  # or whatever the next version should be
```

```python
__version__ = "0.1.1"
```

### 4. Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build
python -m build
```

### 5. Check the Package

```bash
# Verify the package
twine check dist/*
```

### 6. Upload to TestPyPI First

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

### 7. Test Installation from TestPyPI

```bash
# Create a new virtual environment for testing
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-config-sync

# Test the installation
mcp-config-sync --help
```

### 8. Upload to PyPI

If everything works correctly:

```bash
# Upload to PyPI
twine upload dist/*
```

### 9. Verify on PyPI

1. Check your package page: https://pypi.org/project/mcp-config-sync/
2. Test installation from PyPI:

```bash
pip install mcp-config-sync
mcp-config-sync --help
```

## Automation with GitHub Actions

The repository includes GitHub Actions workflows for:
- **CI**: Runs tests, linting, and builds on every push/PR
- **Publishing**: Can be extended to automatically publish on tag creation

To set up automated publishing:

1. Add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`
2. Create a release/tag on GitHub
3. The workflow will automatically build and publish

## Version Management

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `0.1.0` → `0.1.1` (bug fix)
- `0.1.1` → `0.2.0` (new feature)
- `0.2.0` → `1.0.0` (major release)

## Troubleshooting

### Common Issues:

1. **403 Forbidden**: Check your API token and permissions
2. **Package already exists**: You can't overwrite existing versions
3. **Invalid package**: Run `twine check dist/*` to identify issues
4. **Missing dependencies**: Ensure all dependencies are properly specified

### Getting Help:

- [PyPI Help](https://pypi.org/help/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)