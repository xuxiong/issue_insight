"""
Output formatters for GitHub issue analysis results.

This module provides formatters for different output formats (table, json, csv)
to display analysis results in a user-friendly way.
"""

import json
import csv
from io import StringIO
from typing import List, Dict, Any
from rich.table import Table
from rich.console import Console
from rich.text import Text

from models import Issue, GitHubRepository, ActivityMetrics


class BaseFormatter:
    """Base class for all formatters."""

    def __init__(self, granularity: str = "auto"):
        """Initialize formatter with optional granularity setting."""
        self.granularity = granularity

    def format(self, issues: List[Issue], repository: GitHubRepository, metrics: ActivityMetrics) -> str:
        """Format the analysis results."""
        raise NotImplementedError("Subclasses must implement format method")


class TableFormatter(BaseFormatter):
    """Formatter that outputs results as a Rich table."""

    def __init__(self, granularity: str = "auto"):
        """Initialize table formatter with granularity setting."""
        super().__init__(granularity)

    def format(self, issues: List[Issue], repository: GitHubRepository, metrics: ActivityMetrics) -> str:
        """Format issues as a Rich table (returns string for compatibility)."""
        return self.format_and_print(None, issues, repository, metrics)

    def format_and_print(self, console: Console, issues: List[Issue], repository: GitHubRepository, metrics: ActivityMetrics) -> str:
        """Format issues as a Rich table."""
        target_console = console if console is not None else Console()

        def render() -> None:
            repo_title = Text(f"Repository: {repository.owner}/{repository.name}", style="bold blue")
            total_issues = Text(f"Total issues analyzed: {metrics.total_issues_analyzed}", style="dim")
            matching_filters = Text(f"Issues matching filters: {metrics.issues_matching_filters}", style="green")
            avg_comments = Text(f"Average comment count: {metrics.average_comment_count:.1f}", style="yellow")

            target_console.print(repo_title)
            target_console.print(total_issues)
            target_console.print(matching_filters)
            target_console.print(avg_comments)

            self._display_metrics(target_console, metrics)

            if not issues:
                empty_message = Text("No issues found matching the specified criteria.", style="red")
                target_console.print(empty_message)
                return

            table = Table(title=f"GitHub Issues ({len(issues)} issues)")
            table.add_column("Number", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("State", style="green")
            table.add_column("Comments", style="yellow", justify="right")
            table.add_column("Created", style="dim")
            table.add_column("Author", style="blue")

            display_issues = issues[:100]
            for issue in display_issues:
                created_date = issue.created_at.strftime("%Y-%m-%d")
                table.add_row(
                    str(issue.number),
                    issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                    issue.state.value.upper(),
                    str(issue.comment_count),
                    created_date,
                    issue.author.username
                )

            target_console.print(table)
            self._display_comments(target_console, issues[:5])

        if console is not None:
            render()
            return ""

        with target_console.capture() as capture:
            render()
        return capture.get()

    def _display_comments(self, console: Console, issues: List[Issue]) -> None:
        """Display comments for issues that have them."""
        issues_with_comments = [issue for issue in issues if issue.comments]

        if not issues_with_comments:
            return

        console.print()
        console.print(Text("💬 Comments", style="bold green"))

        for issue in issues_with_comments:
            console.print(f"[bold cyan]Issue #{issue.number}: {issue.title}[/bold cyan]")
            for comment in issue.comments:
                console.print(f"  {comment.body}")
            console.print()

    def _display_metrics(self, console: Console, metrics: ActivityMetrics) -> None:
        """Display activity metrics in a formatted way."""
        if not metrics.top_labels and not metrics.activity_by_month and not metrics.activity_by_week and not metrics.activity_by_day and not metrics.most_active_users:
            return  # No metrics to display

        console.print()
        console.print(Text("📊 Activity Metrics", style="bold cyan underline"))

        # Comment distribution
        if metrics.comment_distribution:
            console.print(f"💬 Comment Distribution: {metrics.comment_distribution}")
            console.print()

        # Top labels
        if metrics.top_labels:
            console.print("🏷️  Top Labels:")
            for label in metrics.top_labels[:5]:  # Show top 5
                console.print(f"   • {label.label_name}: {label.count} issues")
            console.print()

        # Activity by time period - show the most appropriate granularity
        self._display_time_activity(console, metrics)

        # Most active users
        if metrics.most_active_users:
            console.print("👥 Most Active Comment Users:")
            for user in metrics.most_active_users[:10]:  # Show top 10
                # Get user role if available
                role_info = ""
                if hasattr(metrics, '_user_roles') and metrics._user_roles:
                    user_role = metrics._user_roles.get(user.username)
                    if user_role and user_role != "none":
                        role_info = f" [{user_role}]"

                # Format the user information
                if user.comments_made > 0:
                    console.print(f"   • {user.username}{role_info}: {user.comments_made} comments, {user.issues_created} issues")
                else:
                    console.print(f"   • {user.username}{role_info}: {user.issues_created} issues")
            console.print()

        # Average resolution time
        if metrics.average_issue_resolution_time is not None:
            console.print(f"⏱️  Average issue resolution time: {metrics.average_issue_resolution_time:.1f} days")
            console.print()

        # Add separator
        console.print("─" * 80)

    def _display_time_activity(self, console: Console, metrics: ActivityMetrics) -> None:
        """Display time-based activity in a space-efficient format."""
        all_periods = []
        title = ""
        items_per_line = 4

        if self.granularity == "auto":
            # Determine which granularity to show based on data density
            # Prefer daily if we have recent data, weekly for medium range, monthly for long range

            # Check if we have daily data (last 30 days)
            if metrics.activity_by_day:
                sorted_days = sorted(metrics.activity_by_day.items())
                if len(sorted_days) <= 30:  # Show daily for up to 30 days
                    all_periods = sorted_days[-30:]  # Last 30 days
                    title = "📅 Daily Activity (last 30 days)"
                    items_per_line = 5
                else:
                    all_periods = []

            # If no daily or too much daily data, check weekly
            if not all_periods and metrics.activity_by_week:
                sorted_weeks = sorted(metrics.activity_by_week.items())
                if len(sorted_weeks) <= 26:  # Show weekly for up to 6 months
                    all_periods = sorted_weeks[-26:]  # Last 26 weeks (~6 months)
                    title = "📅 Weekly Activity (last 26 weeks)"
                    items_per_line = 3
                else:
                    all_periods = []

            # Fall back to monthly
            if not all_periods and metrics.activity_by_month:
                sorted_months = sorted(metrics.activity_by_month.items())
                all_periods = sorted_months[-12:]  # Last 12 months
                title = "📅 Monthly Activity (last 12 months)"
                items_per_line = 4

        elif self.granularity == "daily" and metrics.activity_by_day:
            sorted_days = sorted(metrics.activity_by_day.items())
            all_periods = sorted_days[-30:]  # Last 30 days
            title = "📅 Daily Activity (last 30 days)"
            items_per_line = 5

        elif self.granularity == "weekly" and metrics.activity_by_week:
            sorted_weeks = sorted(metrics.activity_by_week.items())
            all_periods = sorted_weeks[-26:]  # Last 26 weeks
            title = "📅 Weekly Activity (last 26 weeks)"
            items_per_line = 3

        elif self.granularity == "monthly" and metrics.activity_by_month:
            sorted_months = sorted(metrics.activity_by_month.items())
            all_periods = sorted_months[-12:]  # Last 12 months
            title = "📅 Monthly Activity (last 12 months)"
            items_per_line = 4

        if not all_periods:
            return

        console.print(title)

        # Format multiple entries per line for better space utilization
        line_items = []
        for i, (period, count) in enumerate(all_periods):
            line_items.append(f"{period}: {count}")
            if (i + 1) % items_per_line == 0 or i == len(all_periods) - 1:
                # Format the line with proper spacing
                formatted_line = "   • " + "   ".join(line_items)
                console.print(formatted_line)
                line_items = []

        console.print()


class JsonFormatter(BaseFormatter):
    """Formatter that outputs results as JSON."""

    def __init__(self, granularity: str = "auto"):
        """Initialize JSON formatter with granularity setting."""
        super().__init__(granularity)

    def format(self, issues: List[Issue], repository: GitHubRepository, metrics: ActivityMetrics) -> str:
        """Format issues as JSON."""
        # Get metrics data and enhance with role information
        metrics_data = metrics.model_dump()

        # Add role information to most_active_users if available
        if metrics.most_active_users and hasattr(metrics, '_user_roles') and metrics._user_roles:
            enhanced_users = []
            for user in metrics.most_active_users:
                user_dict = user.model_dump()
                user_role = metrics._user_roles.get(user.username)
                if user_role:
                    user_dict['role'] = user_role
                enhanced_users.append(user_dict)
            metrics_data['most_active_users'] = enhanced_users

        result = {
            "repository": repository.model_dump(),
            "issues_count": len(issues),
            "issues": [issue.model_dump() for issue in issues],
            "metrics": metrics_data
        }
        return json.dumps(result, indent=2, default=str)


class CsvFormatter(BaseFormatter):
    """Formatter that outputs results as CSV."""

    def __init__(self, granularity: str = "auto"):
        """Initialize CSV formatter with granularity setting."""
        super().__init__(granularity)

    def format(self, issues: List[Issue], repository: GitHubRepository, metrics: ActivityMetrics) -> str:
        """Format issues as CSV."""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Number", "Title", "State", "Comments", "Author", "Created At", "Updated At"])

        # Write issues
        for issue in issues:
            writer.writerow([
                issue.number,
                issue.title.replace(",", ";").replace("\n", " "),  # Simple CSV escaping
                issue.state.value,
                issue.comment_count,
                issue.author.username,
                issue.created_at.isoformat(),
                issue.updated_at.isoformat()
            ])

        return output.getvalue()


def create_formatter(format_name: str, granularity: str = "auto") -> BaseFormatter:
    """
    Create a formatter instance based on the format name.

    Args:
        format_name: The format name (table, json, csv)
        granularity: Time granularity for activity metrics (auto, daily, weekly, monthly)

    Returns:
        A formatter instance

    Raises:
        ValueError: If the format is not supported
    """
    formatters = {
        "table": TableFormatter(granularity),
        "json": JsonFormatter(granularity),
        "csv": CsvFormatter(granularity)
    }

    if format_name not in formatters:
        raise ValueError(f"Unsupported format: {format_name}. Supported formats: {', '.join(formatters.keys())}")

    return formatters[format_name]
