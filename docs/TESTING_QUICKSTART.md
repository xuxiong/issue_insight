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

## ⚙️ Configuration & Setup Fixes

### 🔧 Src Layout Import Configuration (2025-01-18)

**Problem:** Tests failed with src prefix imports and hatchling build errors.

**Root Cause:**
- Test files used `from src.cli.main import main` hardcoded imports
- pyproject.toml missing proper `packages` configuration for hatchling src layout
- pytest missing `--import-mode=importlib` for proper package importing

**Solution Applied:**

1. **Updated pyproject.toml build configuration:**
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["cli", "models", "services", "lib"]
   sources = ["src"]
   ```

2. **Added pytest import-mode:**
   ```toml
   [tool.pytest.ini_options]
   addopts = "-ra -q --strict-markers --strict-config --import-mode=importlib"
   ```

3. **Removed src prefix from test imports:**
   ```python
   # Before (broken)
   from src.cli.main import main, app

   # After (working)
   from cli.main import main, app
   ```

4. **Reinstalled in editable mode:**
   ```bash
   uv sync  # Installs package correctly for development
   ```

**Verification:**
- ✅ Direct imports work: `from cli.main import main`
- ✅ Tests run without import errors
- ✅ Contract tests execute (expected to fail - TDD design)

**Key Insights:**
- With `sources = ["src"]`, hatchling maps src/ → package root
- `packages = ["cli", ...]` tells hatchling which subdirectories contain packages
- `--import-mode=importlib` forces pytest to use installed package imports
- No src prefix needed in test imports when package is properly installed

### 🏗️ General Principles to Avoid Import Issues

**1. Src Layout Best Practices:**
- **Always specify packages explicitly** in pyproject.toml for hatchling
- **Use sources = ["src"]** maps src/ to package root for imports
- **Test imports should NOT include src prefix** when using editable installs

**2. Pytest Configuration:**
- **Always use --import-mode=importlib** for consistent with production imports
- **Never rely on PYTHONPATH hacks** in development - fix the package configuration
- **Install in editable mode** for development with proper import resolution

**3. Import Strategy:**
- **Tests import installed packages** (like production code)
- **Avoid relative imports** unless within the same package
- **Consistent import paths** between development and production

**4. Configuration Validation:**
- **Test direct imports** after any pyproject.toml changes
- **Run build/install** before committing configuration changes
- **Verify setuptools entry points** work correctly

**5. Troubleshooting Checklist:**
- Package installed in editable mode? `uv sync`
- Hatchling packages config correct? Check `packages = [...]`
- Pytest using import-mode? `--import-mode=importlib`
- Test imports without src prefix? `from cli.main import main`
- Direct import works? `python -c "from cli.main import main"`

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
