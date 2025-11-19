# Lottery Analysis System Documentation

This directory contains the Sphinx documentation for the Lottery Analysis System.

## Building the Documentation

### Requirements

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
```

### Build HTML Documentation

```bash
# Using Makefile
make html

# Or using sphinx-build directly
sphinx-build -b html . _build/html
```

The generated HTML documentation will be in `_build/html/`.

### View Documentation

Open `_build/html/index.html` in your web browser.

## Documentation Structure

- `index.rst` - Main documentation index
- `getting_started.rst` - Getting started guide
- `architecture.rst` - System architecture overview
- `examples.rst` - Code examples
- `changelog.rst` - Version history
- `api/` - API reference documentation
- `modules/` - Module-level documentation
- `conf.py` - Sphinx configuration

## Configuration

The documentation is configured in `conf.py` with:

- **Theme**: Read the Docs (sphinx_rtd_theme)
- **Extensions**: autodoc, viewcode, napoleon, intersphinx
- **Source**: Automatically extracts docstrings from Python code

## Adding Documentation

### Adding a New Page

1. Create a new `.rst` file (e.g., `new_page.rst`)
2. Add it to the toctree in `index.rst`
3. Rebuild with `make html`

### Documenting Code

Use Google-style or NumPy-style docstrings in your Python code:

```python
def example_function(param1, param2):
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Example:
        >>> example_function(1, 2)
        3
    """
    return param1 + param2
```

The docstrings will automatically appear in the API documentation.

## Cleaning Build Artifacts

```bash
make clean
```

## Troubleshooting

**Warning: duplicate object description**

This is expected when using both module-level and function-level documentation. 
The warnings can be safely ignored or fixed by adding `:no-index:` to duplicate entries.

**Module not found errors**

Make sure the parent directory is in the Python path. The `conf.py` includes:

```python
sys.path.insert(0, os.path.abspath('..'))
```

## Documentation Coverage

Current documentation includes:

- ✅ Getting Started Guide
- ✅ Architecture Overview
- ✅ API Reference (all modules)
- ✅ Code Examples
- ✅ Changelog
- ✅ Module Index

## Contributing

When adding new features:

1. Add docstrings to your code
2. Update relevant `.rst` files if needed
3. Rebuild documentation to verify
4. Include documentation updates in your PR
