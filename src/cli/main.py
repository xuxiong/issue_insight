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
from models import validate_limit
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

        # Initialize analyzer
        analyzer = IssueAnalyzer()

        # Perform analysis
        console.print(f"[dim]🔍 Analyzing repository...[/dim]")
        result = analyzer.analyze_repository(repository_url, filter_criteria)

        # Create formatter and format output
        formatter = create_formatter(format)
        formatted_output = formatter.format(
            result.issues,
            result.repository,
            result.metrics
        )

        # Display results
        console.print(formatted_output)

    except typer.Exit:
        # Typer normal exit (like --help or --version)
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)




if __name__ == "__main__":
    app()