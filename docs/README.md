# Simple SQLAlchemy Documentation

This directory contains the Sphinx documentation for Simple SQLAlchemy.

## Building Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -e .[docs]
```

Or install manually:

```bash
pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
```

### Build HTML Documentation

```bash
cd docs
make html
```

The built documentation will be available in `docs/_build/html/`.

### Build and Serve Locally

Use the provided build script:

```bash
python scripts/build_docs.py --serve
```

This will:
1. Install dependencies
2. Build the documentation
3. Serve it locally at http://localhost:8000

### Clean Build

To clean previous builds:

```bash
cd docs
make clean
make html
```

Or with the script:

```bash
python scripts/build_docs.py --clean --serve
```

## Documentation Structure

- `index.rst` - Main documentation index
- `quickstart.rst` - Quick start guide
- `string_schema.rst` - String-schema operations guide
- `examples.rst` - Examples documentation
- `api/` - API reference documentation
- `_static/` - Static files (CSS, images)
- `_templates/` - Custom templates

## Writing Documentation

### reStructuredText (RST)

Most documentation is written in reStructuredText format. Key syntax:

```rst
Section Title
=============

Subsection
----------

**Bold text**
*Italic text*

Code blocks:

.. code-block:: python

   def example():
       return "Hello, World!"

Links:
- :doc:`quickstart` - Link to another document
- :class:`~simple_sqlalchemy.BaseCrud` - Link to API class
- :meth:`~simple_sqlalchemy.BaseCrud.query_with_schema` - Link to method
```

### API Documentation

API documentation is auto-generated from docstrings using Sphinx autodoc:

```rst
.. autoclass:: simple_sqlalchemy.BaseCrud
   :members:
   :undoc-members:
   :show-inheritance:
```

### Examples

Include examples in documentation:

```rst
**Example:**

.. code-block:: python

   from simple_sqlalchemy import DbClient, BaseCrud
   
   db = DbClient("sqlite:///app.db")
   user_crud = BaseCrud(User, db)
   
   users = user_crud.query_with_schema(
       "id:int, name:string, email:email"
   )
```

## Deployment

### GitHub Pages

Documentation is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the main branch.

The workflow is defined in `.github/workflows/docs.yml`.

### Manual Deployment

To deploy manually:

1. Build documentation: `make html`
2. Push `docs/_build/html/` contents to `gh-pages` branch

### Read the Docs

For Read the Docs deployment:

1. Connect your GitHub repository to Read the Docs
2. Configure build settings:
   - Python version: 3.9+
   - Requirements file: `docs/requirements.txt`
   - Documentation type: Sphinx

## Configuration

Documentation configuration is in `conf.py`:

- Theme: `sphinx_rtd_theme`
- Extensions: autodoc, napoleon, myst_parser
- API documentation settings
- HTML theme options

## Troubleshooting

### Common Issues

**Import errors during build:**
```bash
# Make sure the package is installed
pip install -e .
```

**Missing dependencies:**
```bash
# Install documentation dependencies
pip install -e .[docs]
```

**Autodoc not finding modules:**
- Check `sys.path` configuration in `conf.py`
- Ensure package is properly installed

**Theme not loading:**
```bash
# Install theme
pip install sphinx-rtd-theme
```

### Build Warnings

Address common warnings:

- **Undefined references:** Check cross-references and links
- **Missing docstrings:** Add docstrings to public methods
- **Duplicate labels:** Ensure section titles are unique

## Contributing

When contributing to documentation:

1. Follow existing structure and style
2. Test builds locally before submitting
3. Include examples for new features
4. Update API documentation for code changes
5. Check for broken links and references

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs](https://docs.readthedocs.io/)
- [Sphinx RTD Theme](https://sphinx-rtd-theme.readthedocs.io/)
