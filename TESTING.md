# Testing Guide

## 📋 Overview

This document provides comprehensive testing guidelines for the **GitHub Issue Analyzer** project. We follow **Test-Driven Development (TDD)** methodology as mandated by our project constitution.

## 🧪 Test Structure

```
tests/
├── unit/                   # Unit tests - Fast, isolated tests
│   ├── test_errors.py      # Error handling tests
│   ├── test_formatter_table.py
│   ├── test_github_client_issues.py
│   ├── test_limit_validation.py
│   ├── test_progress.py
│   └── test_validators.py
├── integration/            # Integration tests - Component interaction tests
│   ├── test_cli_integration.py
│   └── test_us1_basic_filtering.py
├── contract/              # Contract tests - API/Interface验证
│   ├── test_api_contracts.py
│   └── test_cli_interface.py
└── conftest.py            # pytest configuration and fixtures
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **uv** package manager
- **GitHub token** (for integration tests)

### Setup

```bash
# Clone and setup
git clone <repository>
cd issue_finder

# Install dependencies with uv
uv sync

# Verify setup
uv run pytest --version
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/contract/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_validators.py -v

# Run specific test method
uv run pytest tests/unit/test_validators.py::TestLimitValidation::test_invalid_limit -v
```

## 📊 Test Categories

### 🏃 Unit Test Guidelines

**Purpose**: Test individual functions and classes in isolation

**Characteristics**:
- ✅ Fast execution (< 1 second)
- ✅ No external dependencies
- ✅ Use mocks/MagicMock for external services
- ✅ Test edge cases and error conditions

**Example**:
```python
@pytest.mark.unit
def test_validate_limit_positive_number():
    """Test that valid positive limits are accepted."""
    result = validate_limit(100)
    assert result == 100
```

### 🔗 Integration Test Guidelines

**Purpose**: Test component interactions and end-to-end flows

**Characteristics**:
- ⏱️ Slower execution (1-30 seconds)
- 🌐 May use external services (GitHub API)
- 📁 Use test fixtures and temporary data
- 🎯 Test realistic user scenarios

**Example**:
```python
@pytest.mark.integration
def test_basic_issue_filtering_workflow():
    """Test complete issue filtering workflow."""
    result = analyzer.analyze_repository(test_repo_url, filter_criteria)
    assert len(result.issues) > 0
```

### 📋 Contract Test Guidelines

**Purpose**: Verify API contracts and interface compliance

**Characteristics**:
- 🔒 Test public interfaces and APIs
- 📝 Validate input/output contracts
- 🛡️ Ensure backward compatibility
- 📊 Verify data model compliance

**Required Testing Patterns**:

**1. Global autouse fixture pattern**:
```python
REAL_ISSUE_ANALYZER = cli_module.IssueAnalyzer
REAL_CREATE_FORMATTER = cli_module.create_formatter

@pytest.fixture(autouse=True)
def mock_cli_dependencies(monkeypatch):
    \"\"\"Automatically mock external dependencies to ensure fast and stable tests\"\"\"

    # Smart conditional replacement: mock only when real classes exist
    if cli_module.IssueAnalyzer is REAL_ISSUE_ANALYZER:
        analyzer_mock = Mock()
        analyzer_mock.analyze_repository.return_value = _build_dummy_analysis_result()
        monkeypatch.setattr(cli_module, "IssueAnalyzer", Mock(return_value=analyzer_mock))

    if cli_module.create_formatter is REAL_CREATE_FORMATTER:
        monkeypatch.setattr(cli_module, "create_formatter",
                          lambda *args, **kwargs: _DummyFormatter())
```

**Core advantages**:
- 🎯 **Automated dependency management**: No manual setup per test, reduces boilerplate code
- 🛡️ **Prevention of oversight**: Automatically applied to all test methods, ensures consistency
- 🚀 **Performance boost**: Mock calls are hundreds of times faster than real API calls, improves CI efficiency
- 🔍 **Debug-friendly**: Preserves original references for easier issue tracking and debugging

**Applicable scenarios**:
- ✅ **Contract tests required**: Must isolate external dependencies for CLI interface contract verification
- ✅ **Fast feedback needed**: Tests requiring <1 second execution in CI/CD pipelines
- ✅ **Idempotency required**: Test results must be completely reproducible without external interference
- ✅ **Network isolation needed**: Avoid GitHub API rate limits and network fluctuations

**3. Shared builders and canonical patch targets**:
- ✅ Provide module-level helpers (e.g., `_build_issue`, `_build_comment`) for re-usable, contract-focused test doubles instead of rebuilding mocks per test
- ✅ Instantiate service clients only after the autouse fixture has patched dependencies to prevent real API construction
- ✅ Patch the canonical import path once (e.g., `services.github_client.Github`) and avoid mixing targets so every code path sees the same mock
- ❌ Do not instantiate real clients or call live constructors inside fixtures/tests once module-level patches are applied

**2. CliRunner.invoke pattern**:
- ✅ **Must use**: All CLI interface tests should use CliRunner.invoke()
- ✅ **Complete flow validation**: Full chain testing from parameter parsing to output formatting
- ✅ **Error handling validation**: Capture and validate error message format and content

**Non-applicable scenarios (avoid usage)**:
- ❌ **Real integration tests**: Scenarios needing verification of actual GitHub API calls
- ❌ **Performance benchmarks**: Tests requiring measurement of actual response times
- ❌ **Network fault tests**: Tests deliberately checking network exception handling

## 🔧 Test Configuration

### pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "contract: Contract tests",
    "slow: Slow tests that may take longer to run",
]
```

### Test Markers

```python
# Mark tests appropriately
@pytest.mark.unit
def test_fast_function():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_github_api_integration():
    pass

@pytest.mark.contract
def test_api_contract():
    pass
```

## 🏗️ TDD Workflow

### 1. Red Phase - Write Failing Test

```python
def test_validate_limit_edge_case():
    """Test limit validation with edge case."""
    # This should FAIL initially
    result = validate_limit(0)
    assert result == 0
```

### 2. Green Phase - Make Test Pass

```python
def validate_limit(limit: int) -> int:
    """Make the test pass with minimal implementation."""
    if limit <= 0:
        return 100  # Default fallback
    return limit
```

### 3. Refactor Phase - Improve Code

```python
def validate_limit(limit: int) -> int:
    """Improved implementation with proper validation."""
    if not isinstance(limit, int):
        raise ValidationError("Limit must be an integer")
    if limit <= 0:
        return 100
    return limit
```

## 🎯 Current Test Status

### ✅ Working Tests
- Basic model validation tests
- Simple utility function tests

### 🚧 Need Implementation
- GitHub client integration tests (missing lib/modules)
- CLI interface tests (missing lib/validators)
- Error handling tests (missing lib/errors)
- Progress tracking tests (missing lib/progress)

### 📝 Known Issues

1. **Missing Module Structure**
   - lib/ directory and submodules not implemented
   - Blocks 8/10 test files from running

2. **Syntax Errors**
   - `test_github_client_issues.py:238` - method name with spaces
   - Prevents collection of GitHub client tests

3. **Import Path Inconsistency**
   - Mixed import paths: `from issue_finder.cli` vs `from cli.main`

## 🧪 Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestYourClass:
    """Unit tests for YourClass."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_obj = YourClass()

    def test_method_success_case(self):
        """Test successful execution."""
        # Arrange
        expected = "result"

        # Act
        result = self.test_obj.method()

        # Assert
        assert result == expected

    def test_method_error_case(self):
        """Test error handling."""
        # Arrange & Act & Assert
        with pytest.raises(ExpectedError):
            self.test_obj.method_with_error()
```

### Integration Test Template

```python
import pytest
from pathlib import Path

@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def test_config(self):
        """Provide test configuration."""
        return {
            "repository": "https://github.com/owner/repo",
            "limit": 50
        }

    def test_complete_workflow(self, test_config):
        """Test end-to-end workflow."""
        # This should test the complete user story
        result = complete_workflow(test_config)
        assert result.issues
        assert result.metrics is not None
```

## 📊 Test Coverage

### Coverage Goals
- **Unit Tests**: ≥ 80% line coverage
- **Integration Tests**: Main user journeys
- **Contract Tests**: All public interfaces

### Coverage Commands

```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Check coverage threshold
uv run pytest tests/ --cov=src --cov-fail-under=80

# View coverage in browser
open htmlcov/index.html
```

## 🔄 Continuous Integration

### GitHub Actions Workflow

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: astral-sh/setup-uv@v2
    - run: uv sync
    - run: uv run pytest tests/ --cov=src
    - run: uv run black --check src/ tests/
    - run: uv run mypy src/
    - run: uv run ruff check src/ tests/
```

## 🛠️ Debugging Tests

### Common Issues

1. **ImportError: No module named 'lib'**
   ```bash
   # Check Python path
   uv run python -c "import sys; print(sys.path)"

   # Add src to path
   uv run python -m pytest tests/ --import-mode=append
   ```

2. **GitHub API Rate Limits**
   ```bash
   # Set token for tests
   export GITHUB_TOKEN=your_token_here

   # Skip integration tests
   uv run pytest tests/ -m "not integration"
   ```

3. **Async Test Issues**
   ```python
   # Use pytest-asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       await async_function()
   ```

### Debug Commands

```bash
# Enter pdb on failure
uv run pytest tests/ --pdb

# Stop on first failure
uv run pytest tests/ -x

# Run with verbose output
uv run pytest tests/ -v -s

# Show local variables on failure
uv run pytest tests/ --tb=short
```

## 📚 Best Practices

### ✅ Do's
- **Write Tests First** - Follow TDD methodology
- **Use Descriptive Names** - `test_validate_rejects_negative_limit`
- **Test One Thing** - Each test should have one responsibility
- **Use Fixtures** - For common test data
- **Mock External Services** - Keep tests isolated and fast
- **Test Edge Cases** - Empty inputs, null values, error conditions

### ❌ Don'ts
- **Don't Test Implementation Details** - Test behavior, not code
- **Don't Use Real APIs** in unit tests - Use mocks
- **Don't Ignore Edge Cases** - They often reveal bugs
- **Don't Write Long Tests** - Keep them focused and readable
- **Don't Skip Tests** - All code must have corresponding tests

## 🎯 Quality Gates

### Pre-commit Requirements
- [ ] All tests pass (`uv run pytest`)
- [ ] Code coverage ≥ 80%
- [ ] Code formatted (`uv run black`)
- [ ] Type checking passes (`uv run mypy`)
- [ ] Linting passes (`uv run ruff`)

### Release Requirements
- [ ] Integration tests pass
- [ ] Contract tests pass
- [ ] Performance benchmarks pass
- [ ] Security tests pass

## 🔗 Related Documents

- [Project Constitution](./specs/001-github-issue/constitution.md) - Quality standards
- [Development Guide](./DEVELOPMENT.md) - Development workflows
- [User Stories](./specs/001-github-issue/spec.md) - Feature requirements

## ⚙️ Configuration Best Practices

### 🏗️ Import Configuration Principles

**1. Package Structure Standards:**
- **Always use explicit package declarations** in pyproject.toml
- **Never assume implicit package discovery** - be explicit about what's included
- **Use src layout consistently** for cleaner imports and testing

**2. Hatchling Build Configuration:**
```toml
[tool.hatch.build.targets.wheel]
packages = ["cli", "models", "services", "lib"]  # Explicit package list
sources = ["src"]                                 # Src layout mapping
```

**3. Pytest Import Mode:**
- **Always use `--import-mode=importlib`** for production-consistent imports
- **Never rely on PYTHONPATH modifications** - fix package configuration instead
- **Install in editable mode** (`uv sync`) for development testing

**4. Test Import Strategy:**
- **Tests should NOT use src prefix** - use installed package imports
- **Import like production code** - `from cli.main import main`, not `from src.cli.main`
- **Avoid relative imports** except within the same package submodules

**5. Configuration Validation:**
```bash
# Test imports work correctly
python -c "from cli.main import main"

# Verify build configuration
uv sync  # Rebuilds if needed

# Check pytest discovers tests properly
uv run pytest tests/ --collect-only | head -20
```

### 🐛 Troubleshooting Import Issues

**Checklist for Import Problems:**
- [ ] Package installed in editable mode? `uv sync`
- [ ] pyproject.toml has correct `packages = [...]` list?
- [ ] `sources = ["src"]` configured for src layout?
- [ ] pytest using `--import-mode=importlib`?
- [ ] Test files import without `src.` prefix?
- [ ] `__init__.py` files present in all package directories?

**Common Import Error Patterns:**
```bash
# Problem: src prefix in tests (breaks with importlib mode)
from src.cli.main import main  # ❌ FAILS

# Solution: Use installed package imports
from cli.main import main      # ✅ WORKS

# Problem: Missing packages in pyproject.toml (build fails)
[tool.hatch.build.targets.wheel]
sources = ["src"]  # Missing packages = [...]

# Solution: Explicit package list
[tool.hatch.build.targets.wheel]
packages = ["cli", "models", "services", "lib"]
sources = ["src"]
```

### 📚 Testing Configuration Resources
- [Python Packaging Guide - Src Layout](https://packaging.python.org/en/latest/tutorials/packaging-projects/#choosing-a-build-backend)
- [Hatchling Configuration](https://hatch.pypa.io/latest/config/build/)
- [Pytest Import Modes](https://docs.pytest.org/en/stable/explanation/pythonpath.html)

## 📞 Getting Help

- **Test failures**: Check this guide first
- **Setup issues**: Verify uv and Python installation
- **CI failures**: Check environment variables and GitHub token
- **Coverage issues**: Use `--cov-report=html` for detailed analysis
- **Import issues**: See Configuration Best Practices section above

---

*Last updated: 2025-10-18*
