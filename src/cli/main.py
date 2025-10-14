#!/usr/bin/env python3
"""
GitHub Project Activity Analyzer CLI

A command-line tool for analyzing GitHub repository issues to understand
project activity and community engagement patterns.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Add src root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import FilterCriteria, IssueState
from lib.validators import validate_limit
from services.github_client import GitHubClient
from services.filter_engine import FilterEngine

app = typer.Typer(
    name="issue-analyzer",
    help="Analyze GitHub repository issues and activity patterns",
    no_args_is_help=True,
)
console = Console()

__version__ = "1.0.0"


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"issue-analyzer version {__version__}")
        raise typer.Exit()


def validate_repository_url(url: str) -> str:
    """Validate GitHub repository URL format."""
    import re
    pattern = r'^https?://github\.com/([^/]+)/([^/]+)(?:/?|/.*)$'
    if not re.match(pattern, url):
        raise typer.BadParameter(
            "Invalid repository URL format. Expected: https://github.com/owner/repo. "
            f"Example: https://github.com/facebook/react"
        )
    return url

def validate_comment_count(value: Optional[int]) -> Optional[int]:
    """Validate comment count parameters."""
    if value is not None:
        if value < 0:
            raise typer.BadParameter(
                "Comment count must be non-negative. Use positive numbers or omit the flag."
            )
    return value

def validate_format_param(value: str) -> str:
    """Validate output format parameter."""
    valid_formats = ["table", "json", "csv"]
    if value not in valid_formats:
        raise typer.BadParameter(
            f"Invalid format '{value}'. Valid formats: {', '.join(valid_formats)}"
        )
    return value


@app.command()
def main(
    repository_url: str = typer.Argument(
        ...,
        help="GitHub repository URL (e.g., https://github.com/facebook/react)",
        callback=validate_repository_url,
    ),
    min_comments: Optional[int] = typer.Option(
        None,
        "--min-comments",
        help="Minimum comment count filter (inclusive)",
        callback=validate_comment_count,
    ),
    max_comments: Optional[int] = typer.Option(
        None,
        "--max-comments",
        help="Maximum comment count filter (inclusive)",
        callback=validate_comment_count,
    ),
    limit: Optional[int] = typer.Option(
        100,
        "--limit",
        help="Maximum number of issues to return (default: 100)",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        help="Output format: table, json, csv",
        callback=validate_format_param,
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    Analyze GitHub repository issues and activity patterns.

    This tool helps you understand project activity, identify community hotspots,
    and assess engagement levels through issue filtering and metrics.
    """
    try:
        # Validate limit parameter
        validated_limit = validate_limit(limit)

        # Create filter criteria
        filter_criteria = FilterCriteria(
            min_comments=min_comments,
            max_comments=max_comments,
            limit=validated_limit,
            state=None,  # Include all states
            include_comments=False
        )

        # Initialize services
        github_client = GitHubClient()
        filter_engine = FilterEngine()

        # Get repository information
        repository = github_client.get_repository(repository_url)

        # Fetch all issues (excluding pull requests)
        console.print(f"[dim]Fetching issues from {repository.owner}/{repository.name}...[/dim]")
        all_issues = github_client.get_issues(repository.owner, repository.name, state="all")

        # Apply filters
        console.print(f"[dim]Applying filters...[/dim]")
        filtered_issues = filter_engine.filter_issues(all_issues, filter_criteria)

        # Format and display output
        if format == "table":
            _display_table_output(filtered_issues, repository)
        elif format == "json":
            _display_json_output(filtered_issues, repository, filter_criteria)
        elif format == "csv":
            _display_csv_output(filtered_issues, repository, filter_criteria)

        # Display summary
        total_issues = len(all_issues)
        matching_issues = len(filtered_issues)

        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Repository: {repository.owner}/{repository.name}")
        console.print(f"Total issues analyzed: {total_issues}")
        console.print(f"Issues matching filters: {matching_issues}")

        if matching_issues == 0:
            console.print("[yellow]No issues found matching the specified criteria.[/yellow]")
        else:
            avg_comments = sum(issue.comment_count for issue in filtered_issues) / matching_issues
            console.print(f"Average comment count: {avg_comments:.1f}")

    except typer.Exit:
        # Typer normal exit (like --help or --version)
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _display_table_output(issues, repository):
    """Display output in table format."""
    from rich.table import Table

    table = Table(title=f"Issues Analysis: {repository.owner}/{repository.name}")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("State", style="green")
    table.add_column("Comments", justify="right", style="yellow")
    table.add_column("Author", style="blue")
    table.add_column("Created", style="dim")

    for issue in issues:
        state_style = "green" if issue.state == IssueState.OPEN else "red"
        table.add_row(
            str(issue.number),
            issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
            f"[{state_style}]{issue.state.value}[/{state_style}]",
            str(issue.comment_count),
            issue.author.username,
            issue.created_at.strftime("%Y-%m-%d")
        )

    console.print(table)


def _display_json_output(issues, repository, criteria):
    """Display output in JSON format."""
    import json

    result = {
        "repository": {
            "owner": repository.owner,
            "name": repository.name,
            "url": repository.url
        },
        "filter_criteria": {
            "min_comments": criteria.min_comments,
            "max_comments": criteria.max_comments,
            "limit": criteria.limit
        },
        "issues": [
            {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "state": issue.state.value,
                "comment_count": issue.comment_count,
                "author": issue.author.username,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": f"{repository.url}/issues/{issue.number}"
            }
            for issue in issues
        ],
        "summary": {
            "total_issues": len(issues),
            "average_comments": sum(issue.comment_count for issue in issues) / len(issues) if issues else 0
        }
    }

    console.print(json.dumps(result, indent=2))


def _display_csv_output(issues, repository, criteria):
    """Display output in CSV format."""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "id", "number", "title", "state", "comment_count",
        "author", "created_at", "updated_at", "url"
    ])

    # Write data
    for issue in issues:
        writer.writerow([
            issue.id,
            issue.number,
            issue.title,
            issue.state.value,
            issue.comment_count,
            issue.author.username,
            issue.created_at.isoformat(),
            issue.updated_at.isoformat(),
            f"{repository.url}/issues/{issue.number}"
        ])

    console.print(output.getvalue().strip())


if __name__ == "__main__":
    app()