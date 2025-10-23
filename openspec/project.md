# Project Context

## Purpose
GitHub Project Activity Analyzer is a CLI tool for analyzing GitHub repository issues to understand project activity, identify community hotspots, and assess engagement patterns. The tool helps users evaluate project vitality and community focus through comprehensive issue filtering and activity metrics.

## Tech Stack
- **Language**: Python 3.11+
- **CLI Framework**: Click >= 8.1.0
- **API Client**: PyGithub >= 2.1.0
- **Data Validation**: Pydantic >= 2.0.0
- **UI/Output**: Rich >= 13.0.0
- **Build System**: Hatchling
- **Testing**: pytest >= 7.0.0

## Project Conventions

### Code Style
- **Line Length**: 88 characters (Black-compatible)
- **Formatting**: Black with py311 target version
- **Linting**: Ruff with error/warning focus
- **Type Checking**: MyPy with strict settings
- **Imports**: isort via Ruff
- **Naming**: snake_case for variables/functions, PascalCase for classes

### Architecture Patterns
- **Layered Architecture**: CLI → Services → Models → Utils
- **Dependency Injection**: Explicit service dependencies
- **Data Models**: Pydantic for validation and serialization
- **Error Handling**: Custom exception hierarchy with clear error messages
- **Configuration**: Environment variables and CLI flags

### Testing Strategy
- **Test Types**: Unit, integration, contract tests
- **Test Organization**: Separated by feature/module
- **Coverage**: pytest-cov with comprehensive reporting
- **Markers**: @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.contract
- **Contract Tests**: Validate API and CLI interface stability

### Git Workflow
- **Branch Naming**: {spec-number}-{feature-description} (e.g., 001-github-issue)
- **Commit Messages**: Descriptive, focusing on the "why"
- **Feature Development**: Spec-driven with OpenSpec methodology
- **Review Process**: Automated testing and code quality checks

## Domain Context
- **GitHub API**: REST API with rate limiting considerations
- **Issue Analysis**: Focus on community engagement metrics
- **Comment Aggregation**: User activity tracking across issues
- **Repository Access**: Public repositories only (no private repo support)
- **Rate Limiting**: 60 requests/hour unauthenticated, 5000/hour with token

## Important Constraints
- **Authentication**: GitHub personal access token optional for higher rate limits
- **Repository Scope**: Public repositories only, private repos explicitly unsupported
- **Performance**: Target <10s for 1000 issues, <30s with comment content
- **Output Formats**: JSON, CSV, and human-readable table formats
- **Platform**: Cross-platform compatibility (Linux, macOS, Windows)

## External Dependencies
- **GitHub API**: Primary external service for issue data
- **PyGithub**: GitHub API client library
- **Click**: CLI framework for command-line interface
- **Rich**: Terminal formatting and table output
- **Pydantic**: Data validation and serialization
