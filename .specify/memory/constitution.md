# GitHub Project Activity Analyzer Constitution

## Core Principles

### I. CLI-First Design
Every feature starts as a CLI tool. CLI commands must be discoverable, self-documenting, and follow consistent patterns. Text I/O protocol: stdin/args → stdout, errors → stderr. Support both human-readable and machine-readable formats (JSON, CSV).

### II. Test-First Development (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. All features must have corresponding tests before implementation begins.

### III. Integration Testing Focus
Integration testing required for: GitHub API interactions, CLI command workflows, output format validation, and error handling scenarios. Contract tests for external API dependencies.

### IV. Performance by Design
Tool must handle repositories up to 5000 issues within 30 seconds. Memory usage must stay under 200MB. Streaming-first approach for large datasets. Progress indicators for operations >2 seconds.

### V. Simplicity & Maintainability
Single-responsibility principle applied. No premature optimization. Clear separation between models, services, and CLI interface. Dependencies must be well-maintained and actively supported.

## Quality Standards

### Error Handling
All error messages must be actionable with specific guidance, examples, and resolution steps.

### Security
Only public repositories supported. No storage of user data or API responses. Secure handling of authentication tokens.

### Documentation
CLI help must be comprehensive. Quick start guide must enable 95% of users to succeed without additional documentation.

## Governance

This constitution supersedes all other practices. Amendments require documentation and team approval. All code reviews must verify constitution compliance.

**Version**: 1.0.0 | **Ratified**: 2025-10-14 | **Last Amended**: 2025-10-14