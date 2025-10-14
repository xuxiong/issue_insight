"""
CLI interface for GitHub Project Activity Analyzer.

This module provides the main CLI commands and options for analyzing
GitHub repository issues.
"""

import click
from typing import Optional
import sys

from .services.github_client import GitHubClient
from .services.filter_engine import FilterEngine
from .services.output_formatter import OutputFormatter
from .models.metrics import ActivityMetrics
from .utils.validation import validate_repository_url, validate_filters
from .utils.auth import get_auth_token
from .utils.progress import ProgressTracker


@click.command()
@click.argument("repository_url", type=str)
@click.option(
    "--min-comments",
    type=int,
    help="Minimum number of comments an issue must have",
)
@click.option(
    "--max-comments",
    type=int,
    help="Maximum number of comments an issue can have",
)
@click.option(
    "--state",
    type=click.Choice(["open", "closed", "all"]),
    default="all",
    help="Filter issues by state (default: all)",
)
@click.option(
    "--label",
    multiple=True,
    help="Filter by label (can be used multiple times)",
)
@click.option(
    "--assignee",
    help="Filter by assignee username",
)
@click.option(
    "--created-after",
    help="Filter issues created after this date (YYYY-MM-DD format)",
)
@click.option(
    "--created-before",
    help="Filter issues created before this date (YYYY-MM-DD format)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "table"]),
    default="table",
    help="Output format (default: table)",
)
@click.option(
    "--include-comments",
    is_flag=True,
    help="Include comment content in output",
)
@click.option(
    "--token",
    help="GitHub personal access token for higher rate limits",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output with additional details",
)
@click.version_option(version="1.0.0", prog_name="issue-analyzer")
def main(
    repository_url: str,
    min_comments: Optional[int],
    max_comments: Optional[int],
    state: str,
    label: tuple,
    assignee: Optional[str],
    created_after: Optional[str],
    created_before: Optional[str],
    format: str,
    include_comments: bool,
    token: Optional[str],
    verbose: bool,
) -> None:
    """
    Analyze GitHub repository issues to understand project activity.

    REPOSITORY_URL: Full GitHub repository URL (e.g., https://github.com/owner/repo)

    Examples:

    \b
    # Basic analysis with comment filter
    issue-analyzer --min-comments 5 https://github.com/facebook/react

    \b
    # Filter by labels and state
    issue-analyzer --label bug --state open https://github.com/owner/repo

    \b
    # Include comment content in JSON format
    issue-analyzer --include-comments --format json https://github.com/owner/repo
    """
    try:
        # Validate repository URL
        validate_repository_url(repository_url)

        # Get authentication token
        auth_token = token or get_auth_token()

        # Validate filter parameters
        filters = validate_filters(
            min_comments=min_comments,
            max_comments=max_comments,
            state=state,
            labels=list(label),
            assignees=[assignee] if assignee else None,
            created_after=created_after,
            created_before=created_before,
        )

        if verbose:
            click.echo(f"Analyzing repository: {repository_url}")
            click.echo(f"Using filters: {filters}")

        # Parse repository URL to get owner and repo name
        from .utils.validation import parse_repository_url
        owner, repo_name = parse_repository_url(repository_url)

        # Initialize services
        client = GitHubClient(auth_token=auth_token)
        filter_engine = FilterEngine()
        formatter = OutputFormatter(format=format)
        progress = ProgressTracker(verbose=verbose)

        # Get repository information
        progress.start_operation("Fetching repository information")
        repo = client.get_repository(owner, repo_name)
        progress.finish_operation("Repository information retrieved")

        # Show repository info
        progress.show_repository_info(owner, repo_name, 0)  # Will be updated after filtering

        # Get issues
        progress.start_operation("Fetching issues", total=None)
        all_issues = list(client.get_issues(owner, repo_name))
        progress.finish_operation(f"Fetched {len(all_issues)} issues")

        # Apply filters
        progress.start_operation("Applying filters")
        filtered_issues = filter_engine.filter_issues(all_issues, filters)
        progress.finish_operation(f"Filtered to {len(filtered_issues)} issues")

        # Calculate metrics
        progress.start_operation("Calculating metrics")
        # Simple metrics for now - will be enhanced in user story 3
        metrics = ActivityMetrics(
            total_issues_analyzed=len(all_issues),
            issues_matching_filters=len(filtered_issues),
            average_comment_count=sum(issue.comment_count for issue in filtered_issues) / len(filtered_issues) if filtered_issues else 0,
        )
        progress.finish_operation("Metrics calculated")

        # Format and display results
        repo_info = {
            "owner": owner,
            "name": repo_name,
            "url": str(repo.url)
        }

        output = formatter.format_output(filtered_issues, metrics, repo_info, filters)
        click.echo(output)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()