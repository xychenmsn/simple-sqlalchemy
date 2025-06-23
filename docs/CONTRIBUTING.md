# Contributing to Simple SQLAlchemy

Thank you for your interest in contributing to Simple SQLAlchemy! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- PostgreSQL (optional, for PostgreSQL-specific features)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/simple-sqlalchemy.git
   cd simple-sqlalchemy
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .[dev,postgres]
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Verify Setup**
   ```bash
   pytest
   black --check simple_sqlalchemy tests
   mypy simple_sqlalchemy
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=simple_sqlalchemy --cov-report=html

# Run specific test file
pytest tests/test_crud.py

# Run specific test
pytest tests/test_crud.py::test_create_user

# Run PostgreSQL-specific tests (requires PostgreSQL)
pytest -m postgres

# Skip slow tests
pytest -m "not slow"
```

### Test Structure

```
tests/
├── conftest.py              # Test fixtures
├── test_base.py             # Base model tests
├── test_client.py           # DbClient tests
├── test_crud.py             # BaseCrud tests
├── test_helpers/
│   ├── test_m2m.py         # M2M helper tests
│   ├── test_search.py      # Search helper tests
│   └── test_pagination.py  # Pagination tests
├── test_postgres/
│   ├── test_types.py       # PostgreSQL types tests
│   └── test_utils.py       # PostgreSQL utils tests
└── integration/
    └── test_full_workflow.py # End-to-end tests
```

### Writing Tests

```python
import pytest
from simple_sqlalchemy import DbClient, CommonBase, BaseCrud

class TestUser(CommonBase):
    __tablename__ = 'test_users'
    name = Column(String(100), nullable=False)

@pytest.fixture
def test_db():
    db = DbClient("sqlite:///:memory:")
    CommonBase.metadata.create_all(db.engine)
    yield db
    db.close()

def test_user_creation(test_db):
    user_ops = BaseCrud(TestUser, test_db)
    user = user_ops.create({"name": "Test User"})
    assert user.name == "Test User"
    assert user.id is not None
```

## 🎨 Code Style

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format all code
black simple_sqlalchemy tests

# Check formatting
black --check simple_sqlalchemy tests
```

### Import Sorting

We use [isort](https://pycqa.github.io/isort/) for import sorting:

```bash
# Sort imports
isort simple_sqlalchemy tests

# Check import sorting
isort --check-only simple_sqlalchemy tests
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for type checking:

```bash
# Type check
mypy simple_sqlalchemy

# Type check with strict mode
mypy --strict simple_sqlalchemy
```

### Code Quality

```bash
# Run all quality checks
pre-commit run --all-files

# Individual tools
flake8 simple_sqlalchemy tests
pylint simple_sqlalchemy
```

## 📝 Documentation

### Docstring Style

Use Google-style docstrings:

```python
def create_user(self, name: str, email: str) -> User:
    """Create a new user.
    
    Args:
        name: The user's full name
        email: The user's email address
        
    Returns:
        The created user instance
        
    Raises:
        ValueError: If email is already taken
        
    Example:
        >>> user_ops = UserOps(db)
        >>> user = user_ops.create_user("John Doe", "john@example.com")
        >>> print(user.name)
        John Doe
    """
```

### README Updates

When adding new features:

1. Update the main README.md
2. Add examples to the appropriate sections
3. Update the API reference
4. Add to the feature list

### Documentation Files

- `README.md`: Main documentation
- `docs/MIGRATION.md`: Migration guide from common_lib
- `docs/CHANGELOG.md`: Version history
- `docs/CONTRIBUTING.md`: This file
- `examples/`: Usage examples

## 🔧 Development Guidelines

### Code Organization

```
simple_sqlalchemy/
├── __init__.py          # Main exports
├── base.py              # Base models and mixins
├── client.py            # Database client
├── crud.py              # CRUD operations
├── session.py           # Session management
├── helpers/             # Helper modules
│   ├── m2m.py          # Many-to-many helpers
│   ├── search.py       # Search helpers
│   └── pagination.py   # Pagination utilities
└── postgres/            # PostgreSQL-specific features
    ├── types.py        # Custom types
    └── utils.py        # PostgreSQL utilities
```

### Adding New Features

1. **Design First**: Discuss the feature in an issue
2. **Write Tests**: Test-driven development preferred
3. **Implement**: Follow existing patterns
4. **Document**: Update docstrings and README
5. **Test**: Ensure all tests pass

### Backwards Compatibility

- Don't break existing APIs without a major version bump
- Use deprecation warnings for removed features
- Provide migration paths for breaking changes

### Performance Considerations

- Use bulk operations for large datasets
- Implement pagination for large result sets
- Consider database-specific optimizations
- Profile performance-critical code

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Verify with the latest version
3. Create a minimal reproduction case

### Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Create a model with...
2. Call method...
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- Python version:
- simple-sqlalchemy version:
- Database: (SQLite/PostgreSQL/etc.)
- OS:

**Code Sample**
```python
# Minimal code to reproduce the issue
```

**Error Message**
```
Full error traceback
```
```

## 💡 Feature Requests

### Before Requesting

1. Check if the feature already exists
2. Consider if it fits the project scope
3. Think about backwards compatibility

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed API**
```python
# Example of how the feature would be used
```

**Alternatives Considered**
Other ways to achieve the same goal.

**Additional Context**
Any other context about the feature request.
```

## 🔄 Pull Request Process

### Before Submitting

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Ensure all tests pass
7. Run code quality checks

### PR Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why
3. **Tests**: Include tests for new features
4. **Documentation**: Update relevant docs
5. **Backwards Compatibility**: Note any breaking changes

### PR Template

```markdown
**Description**
Brief description of changes.

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing**
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review feedback
4. Squash commits before merge

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

1. Update version in `__init__.py`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release: `git tag v1.0.0`
5. Push tags: `git push --tags`
6. GitHub Actions will build and publish

## 🤝 Community

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: contributors@simple-sqlalchemy.dev

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/):

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## 🙏 Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- GitHub contributors page

Thank you for contributing to Simple SQLAlchemy! 🚀
