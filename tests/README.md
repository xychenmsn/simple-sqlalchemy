# Simple-SQLAlchemy Test Suite

This directory contains comprehensive tests for simple-sqlalchemy, including the new string-schema integration.

## 🧪 Test Structure

### Core Tests

- **`test_base.py`** - Tests for base models and mixins
- **`test_client.py`** - Tests for database client functionality
- **`test_crud.py`** - Tests for CRUD operations
- **`test_session.py`** - Tests for session management
- **`test_helpers.py`** - Tests for helper classes (M2M, Search, Pagination)
- **`test_integration.py`** - Integration and end-to-end tests

### String-Schema Integration Tests

- **`test_string_schema.py`** - Core string-schema integration tests
- **`test_string_schema_advanced.py`** - Advanced features and edge cases
- **`test_news_integration.py`** - News project integration patterns

### Test Utilities

- **`conftest.py`** - Test configuration and fixtures
- **`test_runner.py`** - Advanced test runner with options
- **`requirements.txt`** - Test dependencies

## 🚀 Running Tests

### Quick Validation

```bash
# Quick smoke test
python validate_integration.py

# Run all tests with comprehensive report
python run_all_tests.py
```

### Individual Test Suites

```bash
# Core functionality tests
python -m pytest tests/test_base.py tests/test_client.py tests/test_crud.py -v

# String-schema integration tests
python -m pytest tests/test_string_schema.py -v

# Run specific test file
pytest tests/test_crud.py -v
```

### With Coverage

```bash
# Run tests with coverage report
pytest tests/ --cov=simple_sqlalchemy --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=simple_sqlalchemy --cov-report=html
# View report at htmlcov/index.html
```

### Using the Makefile

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run fast tests (excluding slow ones)
make test-fast

# Run only integration tests
make test-integration
```

### Using the Test Runner Script

```bash
# Basic run
python run_tests.py

# With coverage
python run_tests.py --coverage

# Verbose mode
python run_tests.py --verbose

# Parallel execution
python run_tests.py --parallel 4

# Run specific test file
python run_tests.py tests/test_crud.py
```

## Test Database

All tests use SQLite in-memory databases (`sqlite:///:memory:`) for:

- **Speed**: In-memory databases are extremely fast
- **Isolation**: Each test gets a fresh database
- **No Dependencies**: No need to set up external databases
- **Consistency**: Same behavior across different environments

## Test Models

The tests use simple test models defined in `conftest.py`:

- **User**: Basic user model with name, email, and active status
- **Post**: Blog post model with soft delete capability
- **Category**: Simple category model
- **Role**: Role model for M2M relationship testing

## Test Coverage

The test suite aims for comprehensive coverage of:

- ✅ **Core CRUD Operations**: Create, read, update, delete
- ✅ **Soft Delete**: Soft delete and restore functionality
- ✅ **Session Management**: Session scoping and transaction handling
- ✅ **Helper Modules**: M2M relationships, search, pagination
- ✅ **Base Models**: CommonBase, mixins, and inheritance
- ✅ **Client Operations**: Database client functionality
- ✅ **Integration**: Components working together
- ✅ **Error Handling**: Exception scenarios and rollbacks

## Test Markers

Tests can be marked with the following markers:

- `slow`: Tests that take longer to run
- `integration`: Integration tests
- `postgres`: Tests requiring PostgreSQL (not used in current suite)

Filter tests using markers:

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

## Adding New Tests

When adding new tests:

1. **Use appropriate fixtures** from `conftest.py`
2. **Follow naming conventions** (`test_*` functions in `Test*` classes)
3. **Use SQLite in-memory** for database testing
4. **Add docstrings** explaining what the test does
5. **Test both success and failure cases**
6. **Use appropriate assertions** with clear error messages

Example test structure:

```python
class TestNewFeature:
    """Test new feature functionality"""

    def test_feature_success_case(self, db_client):
        """Test that feature works correctly"""
        # Arrange
        # Act
        # Assert

    def test_feature_error_case(self, db_client):
        """Test that feature handles errors correctly"""
        # Test error scenarios
```

## Continuous Integration

The test suite is designed to run in CI environments with:

- No external dependencies
- Fast execution (< 2 minutes)
- Comprehensive coverage reporting
- Clear failure messages

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure the package is installed in development mode:

   ```bash
   pip install -e .
   ```

2. **SQLAlchemy Version Issues**: Ensure compatible SQLAlchemy version:

   ```bash
   pip install "sqlalchemy>=1.4.0,<3.0.0"
   ```

3. **Test Dependencies**: Install test requirements:
   ```bash
   pip install -r tests/requirements.txt
   ```

### Debug Mode

Run tests with more verbose output:

```bash
pytest tests/ -v -s --tb=long
```

### Performance

If tests are slow:

```bash
# Run tests in parallel
pytest tests/ -n auto

# Profile test execution
pytest tests/ --durations=10
```
