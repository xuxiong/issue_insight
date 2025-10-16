# Testing Quickstart Guide

## 🚀 5-Minute Testing Setup

### 1. Prerequisites Check

```bash
# Verify uv is installed
uv --version

# Verify Python version
python --version  # Should be 3.11+

# Check project structure
ls -la src/ tests/
```

### 2. Quick Setup

```bash
# Install dependencies
uv sync

# Verify pytest works
uv run pytest --version
```

### 3. Run Your First Test

```bash
# Run all tests (most will fail initially - this is expected!)
uv run pytest tests/ -v

# Run only working tests (models)
uv run pytest tests/ -k "not (test_git or test_error or test_formatter or test_limit or test_progress or test_validators)" -v
```

## 🎯 Common Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run only unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term

# Run specific test file
uv run pytest tests/unit/test_validators.py -v

# Run in watch mode (requires pytest-watch)
uv add --dev pytest-watch
uv run ptw tests/
```

## 🐛 Common Issues & Fixes

### Issue: `ModuleNotFoundError: No module named 'lib'`

```bash
# This is EXPECTED - lib module not implemented yet
# Focus on tests that do work:

uv run pytest tests/ -k "not (lib errors formatters)" -v
```

### Issue: GitHub API Rate Limits

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_personal_access_token

# Or skip integration tests
uv run pytest tests/ -m "not integration"
```

### Issue: Python Path Issues

```bash
# Add src to Python path explicitly
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run pytest tests/ -v
```

## 📊 Current Test Status Matrix

| Test Category | Status | Command |
|--------------|--------|---------|
| Models ✅ | Working | `uv run pytest tests/ -k model -v` |
| Unit Tests ❌ | Missing lib/* | `uv run pytest tests/unit/ -v` (10 errors) |
| Integration ❌ | Missing lib/* | `uv run pytest tests/integration/ -v` (2 errors) |
| Contract ❌ | Missing issue_finder | `uv run pytest tests/contract/ -v` |

## 🎯 Your First Contribution

1. **Pick a failing test**
2. **Create the missing implementation**
3. **Make the test pass**
4. **Run the test suite again**

Example workflow:
```bash
# 1. See what's failing
uv run pytest tests/unit/test_validators.py -v

# 2. Create missing src/lib/validators.py

# 3. Run test again
uv run pytest tests/unit/test_validators.py -v

# 4. Celebrate green test! 🎉
```

## 🔧 Development Tools

```bash
# Code formatting
uv run black src/ tests/

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/ tests/

# All quality checks
uv run black src/ tests/ && uv run mypy src/ && uv run ruff check src/ tests/
```

---

**🎉 Happy Testing! Remember: Red → Green → Refactor**