"""
Issue filtering engine service.

This module provides functionality for filtering GitHub issues based on various criteria.
"""

from typing import List, Optional
from datetime import datetime

from ..models.issue import Issue
from ..models.metrics import FilterCriteria


class FilterEngine:
    """Service for filtering GitHub issues based on criteria."""

    def __init__(self):
        """Initialize the filter engine."""
        pass

    def filter_issues(self, issues: List[Issue], criteria: FilterCriteria) -> List[Issue]:
        """
        Filter issues based on the provided criteria.

        Args:
            issues: List of issues to filter
            criteria: Filtering criteria

        Returns:
            List of filtered issues
        """
        filtered_issues = []

        for issue in issues:
            # Skip pull requests
            if issue.is_pull_request:
                continue

            # Apply comment count filters
            if criteria.min_comments is not None and issue.comment_count < criteria.min_comments:
                continue

            if criteria.max_comments is not None and issue.comment_count > criteria.max_comments:
                continue

            # Apply state filter
            if criteria.state and criteria.state != "all":
                if criteria.state == "open" and issue.state.value != "open":
                    continue
                if criteria.state == "closed" and issue.state.value != "closed":
                    continue

            # Apply label filters
            if criteria.labels:
                if not any(label in issue.labels for label in criteria.labels):
                    continue

            # Apply assignee filters
            if criteria.assignees:
                if not any(assignee.username in criteria.assignees for assignee in issue.assignees):
                    continue

            # Apply date filters
            if criteria.created_after and issue.created_at < criteria.created_after:
                continue

            if criteria.created_before and issue.created_at > criteria.created_before:
                continue

            filtered_issues.append(issue)

        return filtered_issues