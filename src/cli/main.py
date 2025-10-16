#!/usr/bin/env python3
"""
GitHub Project Activity Analyzer CLI

A command-line tool for analyzing GitHub repository issues to understand
project activity and community engagement patterns.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
import pydantic
from rich.console import Console

# Add src root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import FilterCriteria, IssueState
from lib.validators import validate_limit
from lib.formatters import create_formatter
from services.issue_analyzer import IssueAnalyzer

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


def validate_state_param(value: str) -> str:
    """Validate state parameter."""
    valid_states = ["open", "closed", "all"]
    if value not in valid_states:
        raise typer.BadParameter(
            f"Invalid state '{value}'. Valid states: {', '.join(valid_states)}"
        )
    return value


def validate_date_param(value: str) -> str:
    """Validate date parameter format."""
    try:
        from lib.validators import parse_iso_date
        parse_iso_date(value)
        return value
    except Exception:
        raise typer.BadParameter(
            f"Invalid date format: '{value}'. Use YYYY-MM-DD format. Example: 2024-01-15"
        )


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
    ),
    max_comments: Optional[int] = typer.Option(
        None,
        "--max-comments",
        help="Maximum comment count filter (inclusive)",
    ),
    limit: int = typer.Option(
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging for debugging",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    # Advanced filtering options
    state: Optional[str] = typer.Option(
        None,
        "--state",
        help="Filter by issue state: open, closed, all",
    ),
    metrics: bool = typer.Option(
        False,
        "--metrics",
        help="Display detailed activity metrics and trends",
    ),
    label: Optional[list[str]] = typer.Option(
        None,
        "--label",
        help="Filter by labels (can be used multiple times)",
    ),
    assignee: Optional[list[str]] = typer.Option(
        None,
        "--assignee",
        help="Filter by assignees (can be used multiple times)",
    ),
    created_since: Optional[str] = typer.Option(
        None,
        "--created-since",
        help="Filter issues created after this date (YYYY-MM-DD)",
    ),
    created_until: Optional[str] = typer.Option(
        None,
        "--created-until",
        help="Filter issues created before this date (YYYY-MM-DD)",
    ),
    updated_since: Optional[str] = typer.Option(
        None,
        "--updated-since",
        help="Filter issues updated after this date (YYYY-MM-DD)",
    ),
    updated_until: Optional[str] = typer.Option(
        None,
        "--updated-until",
        help="Filter issues updated before this date (YYYY-MM-DD)",
    ),
    any_labels: bool = typer.Option(
        False,
        "--any-labels",
        help="Use ANY logic for labels (default: true, issues with any of the labels)",
    ),
    all_labels: bool = typer.Option(
        False,
        "--all-labels",
        help="Use ALL logic for labels (issues must have all specified labels)",
    ),
    any_assignees: bool = typer.Option(
        False,
        "--any-assignees",
        help="Use ANY logic for assignees (default: true, issues assigned to any of the users)",
    ),
    all_assignees: bool = typer.Option(
        False,
        "--all-assignees",
        help="Use ALL logic for assignees (issues must be assigned to all specified users)",
    ),
    include_comments: bool = typer.Option(
        False,
        "--include-comments",
        help="Include actual comment content in the output (may result in additional API calls)",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="GitHub API token for higher rate limits",
        envvar="GITHUB_TOKEN",
    ),
) -> None:
    """
    Analyze GitHub repository issues and activity patterns.

    This tool helps you understand project activity, identify community hotspots,
    and assess engagement levels through issue filtering and metrics.
    """
    try:
        # Configure logging based on verbose flag
        if verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            logging.basicConfig(level=logging.WARNING)

        # Limit is validated by the callback, so we can use it directly.
        validated_limit = limit

        # Parse state parameter
        state_enum = None
        if state:
            state_enum = IssueState.OPEN if state == "open" else IssueState.CLOSED if state == "closed" else None

        # Determine label logic
        any_labels_flag = any_labels or not all_labels  # Default to ANY if neither specified

        # Determine assignee logic
        any_assignees_flag = any_assignees or not all_assignees  # Default to ANY if neither specified

        # Validate that if all_labels is specified, labels must be provided
        if all_labels and not label:
            raise typer.BadParameter("--all-labels requires --label to be specified")

        # Validate that if all_assignees is specified, assignees must be provided
        if all_assignees and not assignee:
            raise typer.BadParameter("--all-assignees requires --assignee to be specified")

        # Create filter criteria
        filter_criteria = FilterCriteria(
            min_comments=min_comments,
            max_comments=max_comments,
            limit=validated_limit,
            state=state_enum,
            labels=label if label else [],
            assignees=assignee if assignee else [],
            created_since=created_since,
            created_until=created_until,
            updated_since=updated_since,
            updated_until=updated_until,
            any_labels=any_labels_flag,
            any_assignees=any_assignees_flag,
            include_comments=include_comments
        )

        # Initialize analyzer
        analyzer = IssueAnalyzer(github_token=token)

        # Perform analysis
        console.print(f"[dim]🔍 Analyzing repository...[/dim]")
        result = analyzer.analyze_repository(repository_url, filter_criteria)

        # Create formatter and format output
        if format == "table":
            # For table format, print directly to console for proper color rendering
            formatter = create_formatter(format)
            formatter.format_and_print(console, result.issues, result.repository, result.metrics)
        else:
            # For other formats (json, csv), print formatted string
            formatter = create_formatter(format)
            formatted_output = formatter.format(
                result.issues,
                result.repository,
                result.metrics
            )
            console.print(formatted_output)

    except typer.Exit:
        # Typer normal exit (like --help or --version)
        raise
    except pydantic.ValidationError as e:
        # Handle Pydantic validation errors with user-friendly messages
        error_messages = []
        for error in e.errors():
            field = error['loc'][-1] if error['loc'] else 'unknown'
            msg = error['msg']

            # Customize error messages for common cases
            if field == 'limit' and 'at least 1' in msg:
                error_messages.append("Invalid --limit value: must be a positive integer (≥1)")
            elif field in ['min_comments', 'max_comments'] and 'non-negative' in msg:
                error_messages.append(f"Invalid --{field.replace('_', '-')} value: must be non-negative")
            elif 'date' in field and 'Invalid ISO date format' in msg:
                error_messages.append(f"Invalid date format for --{field.replace('_', '-').replace('created', 'created').replace('updated', 'updated')}: use YYYY-MM-DD")
            else:
                error_messages.append(f"Invalid {field}: {msg}")

        for msg in error_messages:
            console.print(f"[red]Error: {msg}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)




if __name__ == "__main__":
    app()
