# Tests Directory

This directory contains all test suites for the ArXiv MCP project, organized by test type and scope.

## 📁 Test Organization

```
tests/
├── unit/                  # Unit tests - fast, isolated component tests
├── integration/           # Integration tests - multi-component interactions  
├── legacy/                # Legacy and disabled tests for reference
├── fixtures/              # Test data, mocks, and shared test resources
├── conftest.py           # Pytest configuration and shared fixtures
└── README.md             # This file
```

## 🧪 Test Categories

### Unit Tests (`unit/`)

- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1s per test)
- **Scope**: Single functions, classes, or modules
- **Files**: `test_pydantic_models.py`, `test_document_processor.py`

### Integration Tests (`integration/`)  

- **Purpose**: Test component interactions and workflows
- **Speed**: Medium (1-10s per test)
- **Scope**: Multiple components, external dependencies
- **Files**: `test_modular_integration.py`, `test_mcp_integration.py`

### Legacy Tests (`legacy/`)

- **Purpose**: Archived tests for reference and backward compatibility
- **Status**: Not run in CI, kept for historical context
- **Files**: `legacy_*.py`, disabled test files

## 🚀 Running Tests

### Quick Test Suite

```bash
# Run fast unit tests only
uv run python -m pytest tests/unit/ -v

# Run all tests with coverage
uv run python -m pytest tests/ -v --cov=src
```

### Test Development Workflow

```bash
# Run specific test file
uv run python -m pytest tests/unit/test_document_processor.py -v

# Run tests matching pattern
uv run python -m pytest -k "test_processor" -v

# Run with debugging
uv run python -m pytest tests/unit/ -v -s --pdb
```

## 📋 Test Standards

### Naming Conventions

- **Test files**: `test_*.py`
- **Test functions**: `test_*`
- **Test classes**: `Test*`
- **Fixtures**: Descriptive names in `conftest.py`

### Test Structure

```python
def test_feature_with_valid_input():
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.is_valid()
    assert result.data == expected_data
```

### Coverage Goals

- **Unit tests**: 90%+ coverage
- **Integration tests**: Critical paths covered
- **Overall**: 85%+ total coverage

## 🔧 Development Guidelines

### Adding New Tests

1. **Unit tests**: Add to `tests/unit/test_{module}.py`
2. **Integration tests**: Add to `tests/integration/test_{feature}_integration.py`
3. **Fixtures**: Add shared data to `tests/fixtures/`

### Test Data Management  

- Use `tests/fixtures/` for sample data
- Mock external dependencies in unit tests
- Use real (but lightweight) data in integration tests

---

*Follow the test pyramid: Many unit tests, some integration tests, few end-to-end tests.*
