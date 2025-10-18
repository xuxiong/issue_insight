# Quickstart Guide: issue-analyzer

**Version**: 1.0.0
**Date**: 2025-10-14
**Branch**: 001-github-issue

## Overview

issue-analyzer is a command-line tool for analyzing GitHub repository issues and activity. It helps you understand project activity, identify community hotspots, and assess engagement patterns. The tool provides comprehensive issue filtering, detailed activity metrics, and multiple output formats for in-depth repository analysis.

## Installation

### Prerequisites
- Python 3.11 or higher

### Install from PyPI
```bash
pip install issue-analyzer
```

### Install from Source (for development)
```bash
git clone https://github.com/your-org/issue-analyzer.git
cd issue-analyzer
pip install -e .
```

### Install with uv (recommended)
```bash
git clone https://github.com/your-org/issue-analyzer.git
cd issue-analyzer
uv sync
```

## Quick Examples

### Basic Usage
Analyze issues in a repository:
```bash
issue-analyzer find-issues https://github.com/facebook/react
```

### Filter by Comment Count
Find issues with 5+ comments:
```bash
issue-analyzer find-issues https://github.com/facebook/react --min-comments 5
```

### Include Comment Content
Get full comment content for issues with 3+ comments:
```bash
issue-analyzer find-issues https://github.com/facebook/react --min-comments 3 --include-comments --format json
```

### Complex Filtering
Analyze open bug issues with 2-10 comments:
```bash
issue-analyzer find-issues https://github.com/facebook/react --state open --label bug --min-comments 2 --max-comments 10
```

### Enhanced Filtering with Multiple Options
Filter by multiple labels and date ranges:
```bash
issue-analyzer find-issues https://github.com/facebook/react --label bug --label enhancement --created-since 2024-01-01 --updated-until 2024-12-31
```

### Limit Results
Limit the number of issues returned (default: 100):
```bash
issue-analyzer find-issues https://github.com/facebook/react --limit 25 --min-comments 3
```

### Get All Matching Issues
Remove the limit to get all matching issues:
```bash
issue-analyzer find-issues https://github.com/facebook/react --limit 0 --min-comments 1
```

### Multiple Assignee Filtering
Find issues assigned to any of several developers:
```bash
issue-analyzer find-issues https://github.com/facebook/react --assignee developer1 --assignee developer2
```

### Use ALL Logic for Assignee Filtering
Require issues to be assigned to all specified assignees:
```bash
issue-analyzer find-issues https://github.com/facebook/react --assignee developer1 --assignee developer2 --all-assignees
```

### Display Detailed Metrics
Show activity metrics and trends:
```bash
issue-analyzer find-issues https://github.com/facebook/react --metrics --min-comments 5
```

### Verbose Output
Enable detailed logging for debugging:
```bash
issue-analyzer find-issues https://github.com/facebook/react --verbose --min-comments 5
```

## Command Reference

### Basic Syntax
```bash
issue-analyzer find-issues REPOSITORY_URL [OPTIONS]
```

### Required Arguments
- `REPOSITORY_URL`: Full GitHub repository URL (e.g., `https://github.com/owner/repo`)

### Options

#### Filtering Options
- `--min-comments INTEGER`: Minimum comment count filter
- `--max-comments INTEGER`: Maximum comment count filter
- `--state [open|closed|all]`: Filter by issue state (default: all)
- `--label TEXT`: Filter by label (can be used multiple times)
- `--all-labels`: Use ALL logic for labels (issues must have all specified labels, default: ANY)
- `--any-labels`: Use ANY logic for labels (issues with any of the labels, default)
- `--assignee TEXT`: Filter by assignee username (can be used multiple times)
- `--all-assignees`: Use ALL logic for assignees (issues must be assigned to all specified users, default: ANY)
- `--any-assignees`: Use ANY logic for assignees (issues assigned to any of the users, default)
- `--created-since DATE`: Filter issues created after this date (YYYY-MM-DD format)
- `--created-until DATE`: Filter issues created before this date (YYYY-MM-DD format)
- `--updated-since DATE`: Filter issues updated after this date (YYYY-MM-DD format)
- `--updated-until DATE`: Filter issues updated before this date (YYYY-MM-DD format)
- `--limit INTEGER`: Maximum number of issues to return (default: 100, 0 for all)

#### Output Options
- `--format [json|csv|table]`: Output format (default: table)
- `--include-comments`: Include comment content in output
- `--metrics`: Display detailed activity metrics and trends

#### Authentication Options
- `--token TEXT`: GitHub personal access token (env: GITHUB_TOKEN)
- `--verbose/-v`: Enable verbose logging for debugging
- `--version`: Show version and exit
- `--help`: Show help message

## Authentication

### Setting Up GitHub Token
For higher rate limits, create a GitHub personal access token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `public_repo` scope
3. Set environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

### Using Token in Command
```bash
issue-analyzer find-issues https://github.com/facebook/react --token ghp_xxxxxxxxxxxxxxxxxxxx
```

## Output Formats

### Table Format (Default)
Human-readable table output:
```bash
issue-analyzer find-issues https://github.com/facebook/react --min-comments 5

┌──────┬─────────┬─────────────────────────────┬────────┬─────────────┬─────────────┐
│ ID   │ Number  │ Title                       │ State   │ Comments    │ Author      │
├──────┼─────────┼─────────────────────────────┼────────┼─────────────┼─────────────┤
│ 42   │ 12345   │ Bug: Component not rendering │ open    │ 8           │ contributor1│
│ 43   │ 12346   │ Enhancement: Add new feature │ closed  │ 12          │ developer2  │
└──────┴─────────┴─────────────────────────────┴────────┴─────────────┴─────────────┘

Total issues: 2 | Average comments: 10.0 | Processing time: 2.3s
```

### JSON Format
Machine-readable JSON output:
```bash
issue-analyzer find-issues https://github.com/facebook/react --format json --min-comments 5

{
  "repository": {
    "owner": "facebook",
    "name": "react",
    "url": "https://github.com/facebook/react"
  },
  "filters": {
    "min_comments": 5
  },
  "issues": [
    {
      "id": 123456789,
      "number": 42,
      "title": "Bug: Component not rendering correctly",
      "state": "open",
      "comment_count": 8,
      "author": "contributor1",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T14:20:00Z"
    }
  ],
  "metrics": {
    "total_issues_analyzed": 1250,
    "issues_matching_filters": 2,
    "average_comment_count": 10.0
  }
}
```

### CSV Format
Spreadsheet-compatible output:
```bash
issue-analyzer find-issues https://github.com/facebook/react --format csv --min-comments 5

id,number,title,state,comments,author,created_at,updated_at
123456789,42,Bug: Component not rendering correctly,open,8,contributor1,2024-01-15T10:30:00Z,2024-01-16T14:20:00Z
```

## Common Use Cases

### 1. Assess Project Activity
Find the most discussed issues:
```bash
issue-analyzer find-issues https://github.com/owner/repo --min-comments 10 --format table
```

### 2. Identify Community Hotspots
Find trending bug reports:
```bash
issue-analyzer find-issues https://github.com/owner/repo --label bug --state open --min-comments 5
```

### 3. Research Feature Requests
Analyze enhancement discussions:
```bash
issue-analyzer find-issues https://github.com/owner/repo --label enhancement --include-comments --format json > features.json
```

### 4. Track Recent Activity
Find issues from the last month:
```bash
issue-analyzer find-issues https://github.com/owner/repo --created-since 2024-10-01
```

### 5. Analyze Specific User Activity
Check issues assigned to a developer:
```bash
issue-analyzer find-issues https://github.com/owner/repo --assignee developer123 --min-comments 3
```

## Performance Tips

### For Large Repositories
- Use specific filters to reduce processing time
- Avoid `--include-comments` unless necessary
- Use authentication token for higher rate limits

### Example for Large Analysis:
```bash
issue-analyzer --min-comments 5 --state open --token $GITHUB_TOKEN https://github.com/large-repo/project
```

## Troubleshooting

### Common Issues

#### Repository Not Found
```
Error: Repository not found
```
**Solution**: Verify the repository URL format and ensure it's a public repository.

#### Rate Limit Exceeded
```
Error: Rate limit exceeded. Try again later or use authentication token.
```
**Solution**: Set up a GitHub token as shown in Authentication section.

#### Invalid Date Format
```
Error: Invalid date format. Use YYYY-MM-DD format.
```
**Solution**: Ensure dates are in the correct format (e.g., `2024-01-15`).

#### No Issues Match Criteria
```
No issues found matching the specified criteria.
```
**Solution**: Try relaxing filters or verify repository has issues.

### Debug Mode
Use `--verbose` flag for detailed information:
```bash
issue-analyzer find-issues https://github.com/facebook/react --verbose --min-comments 5
```

## Advanced Usage

### Combining Multiple Filters
```bash
issue-analyzer \
  --state open \
  --label bug \
  --label high-priority \
  --min-comments 3 \
  --max-comments 20 \
  --created-since 2024-01-01 \
  --assignee developer123 \
  https://github.com/facebook/react
```

### Output to File
```bash
# Save JSON output to file
issue-analyzer --format json --include-comments https://github.com/facebook/react > analysis.json

# Save CSV for spreadsheet analysis
issue-analyzer --format csv --min-comments 5 https://github.com/facebook/react > issues.csv
```

### Batch Analysis
Create a script to analyze multiple repositories:
```bash
#!/bin/bash
repos=(
  "https://github.com/facebook/react"
  "https://github.com/vuejs/vue"
  "https://github.com/angular/angular"
)

for repo in "${repos[@]}"; do
  echo "Analyzing $repo..."
  issue-analyzer --min-comments 5 --format json "$repo" > "$(basename $repo).json"
done
```

## Getting Help

### Command Line Help
```bash
issue-analyzer --help
```

### Version Information
```bash
issue-analyzer --version
```

### Example Repository
Try with this sample repository:
```bash
issue-analyzer --min-comments 1 --format table https://github.com/octocat/Hello-World
```

## Limitations

- Only public repositories are supported
- Rate limits apply for GitHub API usage
- Comment retrieval can be slow for issues with many comments
- Processing time scales with repository size and filter complexity

## Next Steps

1. **Set up authentication** for better rate limits
2. **Experiment with filters** to find relevant insights
3. **Use different output formats** based on your needs
4. **Automate analysis** by incorporating into scripts
5. **Share results** with your team using the JSON/CSV formats

## Support

For issues, feature requests, or contributions:
- Repository: https://github.com/your-org/issue-analyzer
- Documentation: See `/docs` directory
- Issues: Create an issue on the GitHub repository
