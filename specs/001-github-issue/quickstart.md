# Quickstart Guide: GitHub Project Activity Analyzer

**Version**: 1.0.0
**Date**: 2025-10-14
**Branch**: 001-github-issue

## Overview

The GitHub Project Activity Analyzer is a command-line tool that helps you analyze repository issues to understand project activity, identify community hotspots, and assess engagement patterns. It provides filtering capabilities, activity metrics, and multiple output formats for comprehensive repository analysis.

## Installation

### Prerequisites
- Python 3.11 or higher
- Git (for cloning if needed)

### Install from Source
```bash
git clone https://github.com/your-org/issue-finder.git
cd issue-finder
pip install -e .
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Quick Examples

### Basic Usage
Analyze issues in a repository:
```bash
issue-analyzer https://github.com/facebook/react
```

### Filter by Comment Count
Find issues with 5+ comments:
```bash
issue-analyzer --min-comments 5 https://github.com/facebook/react
```

### Include Comment Content
Get full comment content for issues with 3+ comments:
```bash
issue-analyzer --min-comments 3 --include-comments --format json https://github.com/facebook/react
```

### Complex Filtering
Analyze open bug issues with 2-10 comments:
```bash
issue-analyzer --state open --label bug --min-comments 2 --max-comments 10 https://github.com/facebook/react
```

## Command Reference

### Basic Syntax
```bash
issue-analyzer [OPTIONS] REPOSITORY_URL
```

### Required Arguments
- `REPOSITORY_URL`: Full GitHub repository URL (e.g., `https://github.com/owner/repo`)

### Options

#### Filtering Options
- `--min-comments INTEGER`: Minimum comment count filter
- `--max-comments INTEGER`: Maximum comment count filter
- `--state [open|closed|all]`: Filter by issue state (default: all)
- `--label TEXT`: Filter by label (can be used multiple times)
- `--assignee TEXT`: Filter by assignee username
- `--created-after DATE`: Filter by creation date (YYYY-MM-DD format)
- `--created-before DATE`: Filter by creation date (YYYY-MM-DD format)

#### Output Options
- `--format [json|csv|table]`: Output format (default: table)
- `--include-comments`: Include comment content in output
- `--verbose`: Enable verbose output with additional details

#### Authentication Options
- `--token TEXT`: GitHub personal access token
- `--help`: Show help message
- `--version`: Show version information

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
issue-analyzer --token ghp_xxxxxxxxxxxxxxxxxxxx https://github.com/facebook/react
```

## Output Formats

### Table Format (Default)
Human-readable table output:
```bash
issue-analyzer --min-comments 5 https://github.com/facebook/react

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
issue-analyzer --format json --min-comments 5 https://github.com/facebook/react

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
issue-analyzer --format csv --min-comments 5 https://github.com/facebook/react

id,number,title,state,comments,author,created_at,updated_at
123456789,42,Bug: Component not rendering correctly,open,8,contributor1,2024-01-15T10:30:00Z,2024-01-16T14:20:00Z
```

## Common Use Cases

### 1. Assess Project Activity
Find the most discussed issues:
```bash
issue-analyzer --min-comments 10 --format table https://github.com/owner/repo
```

### 2. Identify Community Hotspots
Find trending bug reports:
```bash
issue-analyzer --label bug --state open --min-comments 5 https://github.com/owner/repo
```

### 3. Research Feature Requests
Analyze enhancement discussions:
```bash
issue-analyzer --label enhancement --include-comments --format json https://github.com/owner/repo > features.json
```

### 4. Track Recent Activity
Find issues from the last month:
```bash
issue-analyzer --created-after 2024-01-01 https://github.com/owner/repo
```

### 5. Analyze Specific User Activity
Check issues assigned to a developer:
```bash
issue-analyzer --assignee developer123 --min-comments 3 https://github.com/owner/repo
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
issue-analyzer --verbose --min-comments 5 https://github.com/facebook/react
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
  --created-after 2024-01-01 \
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
- Repository: https://github.com/your-org/issue-finder
- Documentation: See `/docs` directory
- Issues: Create an issue on the GitHub repository