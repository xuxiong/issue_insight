# GitHub Project Activity Analyzer

A powerful CLI tool for analyzing GitHub repository issues to understand project activity, identify community hotspots, and assess engagement patterns.

## Features

- **Issue Filtering**: Filter issues by comment count, labels, state, assignees, and dates
- **Activity Metrics**: Get insights into project health with aggregated statistics
- **Comment Analysis**: Access comment content to understand community discussions
- **Multiple Formats**: Export results in JSON, CSV, or human-readable table format
- **Performance Optimized**: Handle repositories with thousands of issues efficiently

## Quick Start

### Installation

```bash
pip install issue-finder
```

### Basic Usage

```bash
# Analyze issues with 5+ comments
issue-analyzer --min-comments 5 https://github.com/facebook/react

# Filter by labels and state
issue-analyzer --label bug --state open https://github.com/owner/repo

# Include comment content
issue-analyzer --include-comments --format json https://github.com/owner/repo
```

### Authentication

For higher rate limits, set a GitHub personal access token:

```bash
export GITHUB_TOKEN=your_token_here
```

## Requirements

- Python 3.11+
- GitHub personal access token (optional, for higher rate limits)

## Documentation

See the [Quickstart Guide](specs/001-github-issue/quickstart.md) for detailed usage examples and advanced features.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to our repository.