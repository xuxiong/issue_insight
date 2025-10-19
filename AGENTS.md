# AGENTS.md
This file provides guidance to Terminal Assistant Agent when working with code in this repository. **All work MUST comply with the principles and standards defined in `.specify/memory/constitution.md`.**

## Project Overview

**GitHub Project Activity Analyzer** - A Python CLI tool for analyzing GitHub repository issues to understand project activity, identify community hotspots, and assess engagement patterns.

## Quick Development Commands

### Setup and Installation
```bash
# Install dependencies with uv (recommended)
uv sync

# Install in development mode
pip install -e .

# Run the CLI tool
issue-analyzer find-issues https://github.com/facebook/react --min-comments 5
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test types
pytest tests/unit/ -v              # Unit tests
pytest tests/integration/ -v        # Integration tests
pytest tests/contract/ -v          # Contract tests

# Run with specific markers
pytest tests/ -m unit              # Only unit tests
pytest tests/ -m integration       # Only integration tests
pytest tests/ -m slow              # Slow tests only

# Run with timeout (useful for GitHub API tests)
python run_tests_with_timeout.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
ruff format src/ tests/

# Run all quality checks
black src/ tests/ && mypy src/ && ruff check src/ tests/
```

### Building and Distribution
```bash
# Build package
python -m build

# Install from built package
pip install dist/issue-analyzer-*.whl
```

## Architecture Overview

### Core Components

**CLI Layer (`src/cli/main.py`)**:
- Click-based command-line interface
- Pydantic validation for all CLI arguments
- Rich console output formatting
- Error handling and user-friendly messages

**Service Layer (`src/services/`)**:
- `github_client.py`: GitHub API client with rate limiting and error handling
- `issue_analyzer.py`: Core analysis orchestrator coordinating GitHub client and filtering
- `filter_engine.py`: Issue filtering based on criteria (comments, labels, dates, etc.)
- `metrics_analyzer.py`: Activity metrics calculation and aggregation

**Data Models (`src/models/`)**:
- Pydantic models for all data structures
- `GitHubRepository`: Repository metadata
- `Issue`: GitHub issue with comprehensive metadata
- `FilterCriteria`: Filtering parameters with validation
- `ActivityMetrics`: Aggregated analysis metrics

**Utilities (`src/lib/`)**:
- `formatters/`: Output formatting (table, JSON, CSV)
- `progress/`: Progress tracking and display
- `validators/`: Input validation and sanitization
- `errors/`: Custom exception types

### Key Design Patterns

1. **Pydantic Validation**: All CLI arguments and data models use Pydantic for validation
2. **Service Composition**: IssueAnalyzer orchestrates GitHubClient, FilterEngine, and MetricsAnalyzer
3. **Progress Tracking**: Real-time progress display with multiple phases
4. **Rate Limiting**: GitHub API rate limit handling with warnings
5. **Error Handling**: Comprehensive error messages for common API issues

## GitHub API Integration

- **Authentication**: Optional GITHUB_TOKEN for higher rate limits
- **Rate Limiting**: Automatic handling with warnings when limits are low
- **Error Handling**: User-friendly messages for common GitHub API errors
- **Private Repositories**: Not supported - only public repositories
- **Pull Requests**: Automatically filtered out (only issues are analyzed)

## Testing Strategy

### Test Structure
- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test GitHub API interactions with mocks
- **Contract Tests** (`tests/contract/`): Test API contracts and data formats

### Test Markers
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests  
- `@pytest.mark.contract`: Contract tests
- `@pytest.mark.slow`: Tests that take longer to run

### Mock Data
- Use `tests/conftest.py` for shared fixtures
- Mock GitHub API responses to avoid hitting real API during tests

## Development Workflow

### Adding New Features
1. Write failing tests for new functionality first (TDD requirement)
2. Add new CLI arguments to `src/cli/main.py` with proper validation
3. Update `FilterCriteria` model in `src/models/__init__.py`
4. Implement filtering logic in `src/services/filter_engine.py` to make tests pass
5. Update documentation in README.md and specs

### Modifying GitHub API Integration
1. Write failing integration tests for new API functionality first (TDD requirement)
2. Update `src/services/github_client.py` for new API endpoints
3. Add corresponding data models in `src/models/__init__.py`
4. Update rate limiting and error handling as needed to make tests pass

### Output Formatting
- Table format: Uses Rich library for console display
- JSON format: Direct JSON serialization of data models
- CSV format: Custom CSV formatting with headers
- Add new formatters in `src/lib/formatters/`

## Important Constraints

- **Python 3.11+**: Only supports Python 3.11, 3.12, and 3.13
- **Public Repositories Only**: Private repositories are not supported
- **GitHub API Limits**: Respect rate limits and implement proper error handling
- **Pull Requests**: Automatically excluded from analysis
- **Memory Usage**: Be mindful of memory when analyzing large repositories

<Additional_info>
**Optionally**, you can retrieve information about the current feature we are working on. Do so **only if it's really necessary**.
For getting more context on feature we are working on:
1. Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.
2. Load and analyze available design documents:
   - IF EXISTS: Read tasks.md for the complete task list and execution plan
   - IF EXISTS: Read plan.md for tech stack, architecture, and file structure
   - IF EXISTS: Read data-model.md for entities
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios
   - IF EXISTS: Read spec.md for user stories and non-technical requirements
</Additional_info>
