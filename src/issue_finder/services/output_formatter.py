"""
Output formatting service.

This module provides functionality for formatting analysis results in different formats.
"""

from typing import List, Dict, Any
from tabulate import tabulate

from ..models.metrics import ActivityMetrics


class OutputFormatter:
    """Service for formatting output in different formats."""

    def __init__(self, format: str = "table"):
        """
        Initialize the output formatter.

        Args:
            format: Output format ("json", "csv", "table")
        """
        self.format = format

    def format_output(self, issues: List[Any], metrics: ActivityMetrics, repository_info: Dict[str, Any], filters: Any = None) -> str:
        """
        Format analysis results in the specified format.

        Args:
            issues: List of issues to format
            metrics: Activity metrics
            repository_info: Repository information
            filters: Applied filters

        Returns:
            Formatted output string
        """
        if self.format == "table":
            return self._format_table(issues, metrics, repository_info, filters)
        elif self.format == "json":
            return self._format_json(issues, metrics, repository_info, filters)
        elif self.format == "csv":
            return self._format_csv(issues, metrics, repository_info, filters)
        else:
            return "Invalid format"

    def _format_table(self, issues: List[Any], metrics: ActivityMetrics, repository_info: Dict[str, Any], filters: Any) -> str:
        """Format output as a human-readable table."""
        if not issues:
            return "No issues found matching the specified criteria."

        # Prepare table data
        headers = ["ID", "Number", "Title", "State", "Comments", "Author"]
        rows = []

        for issue in issues:
            # Truncate long titles for table display
            title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
            author = issue.author.username if issue.author else "Unknown"

            rows.append([
                issue.id,
                issue.number,
                title,
                issue.state.value,
                issue.comment_count,
                author
            ])

        # Create table using tabulate
        table = tabulate(rows, headers=headers, tablefmt="grid")

        # Add summary information
        summary_lines = []
        summary_lines.append(f"\nRepository: {repository_info.get('owner', 'unknown')}/{repository_info.get('name', 'unknown')}")
        summary_lines.append(f"Total issues analyzed: {metrics.total_issues_analyzed}")
        summary_lines.append(f"Issues matching filters: {metrics.issues_matching_filters}")
        summary_lines.append(f"Average comments per issue: {metrics.average_comment_count:.1f}")

        if filters and not filters.is_empty():
            active_filters = []
            if filters.min_comments is not None:
                active_filters.append(f"Min comments: {filters.min_comments}")
            if filters.max_comments is not None:
                active_filters.append(f"Max comments: {filters.max_comments}")
            if filters.state:
                active_filters.append(f"State: {filters.state}")
            if filters.labels:
                active_filters.append(f"Labels: {', '.join(filters.labels)}")

            summary_lines.append(f"Filters applied: {', '.join(active_filters)}")

        return table + "\n".join(summary_lines)

    def _format_json(self, issues: List[Any], metrics: ActivityMetrics, repository_info: Dict[str, Any], filters: Any) -> str:
        """Format output as JSON."""
        import orjson

        # Convert issues to dictionaries
        issues_data = []
        for issue in issues:
            issue_dict = {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state.value,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "author": {
                    "username": issue.author.username if issue.author else None,
                    "display_name": issue.author.display_name if issue.author else None,
                } if issue.author else None,
                "assignees": [
                    {"username": assignee.username, "display_name": assignee.display_name}
                    for assignee in issue.assignees
                ],
                "labels": issue.labels,
                "comment_count": issue.comment_count,
                "milestone": issue.milestone,
            }

            # Add comments if they exist
            if hasattr(issue, 'comments') and issue.comments:
                issue_dict["comments"] = [
                    {
                        "id": comment.id,
                        "body": comment.body,
                        "author": {
                            "username": comment.author.username if comment.author else None,
                            "display_name": comment.author.display_name if comment.author else None,
                        },
                        "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    }
                    for comment in issue.comments
                ]

            issues_data.append(issue_dict)

        # Create complete JSON output
        output_data = {
            "repository": repository_info,
            "filters": {
                "min_comments": filters.min_comments if filters else None,
                "max_comments": filters.max_comments if filters else None,
                "state": filters.state if filters else None,
                "labels": filters.labels if filters else None,
                "assignees": filters.assignees if filters else None,
                "created_after": filters.created_after.isoformat() if filters and filters.created_after else None,
                "created_before": filters.created_before.isoformat() if filters and filters.created_before else None,
            } if filters else None,
            "issues": issues_data,
            "metrics": {
                "total_issues_analyzed": metrics.total_issues_analyzed,
                "issues_matching_filters": metrics.issues_matching_filters,
                "average_comment_count": metrics.average_comment_count,
                "comment_distribution": metrics.comment_distribution,
                "top_labels": [
                    {"label_name": label.label_name, "count": label.count}
                    for label in metrics.top_labels
                ],
                "activity_by_month": metrics.activity_by_month,
                "most_active_users": [
                    {
                        "username": user.username,
                        "issues_created": user.issues_created,
                        "comments_made": user.comments_made
                    }
                    for user in metrics.most_active_users
                ],
            },
            "generated_at": metrics.generated_at.isoformat() if hasattr(metrics, 'generated_at') else None,
            "processing_time_seconds": metrics.processing_time_seconds if hasattr(metrics, 'processing_time_seconds') else None,
        }

        return orjson.dumps(output_data, option=orjson.OPT_INDENT_2).decode('utf-8')

    def _format_csv(self, issues: List[Any], metrics: ActivityMetrics, repository_info: Dict[str, Any], filters: Any) -> str:
        """Format output as CSV."""
        import csv
        import io

        output = io.StringIO()

        # Define CSV headers
        headers = [
            "id", "number", "title", "state", "author", "created_at",
            "updated_at", "closed_at", "comment_count", "labels", "milestone"
        ]

        writer = csv.writer(output)
        writer.writerow(headers)

        # Write issue data
        for issue in issues:
            writer.writerow([
                issue.id,
                issue.number,
                issue.title,
                issue.state.value,
                issue.author.username if issue.author else "",
                issue.created_at.isoformat() if issue.created_at else "",
                issue.updated_at.isoformat() if issue.updated_at else "",
                issue.closed_at.isoformat() if issue.closed_at else "",
                issue.comment_count,
                ";".join(issue.labels),  # Join multiple labels with semicolon
                issue.milestone or ""
            ])

        return output.getvalue()