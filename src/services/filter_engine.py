"""
Issue filtering engine for GitHub Project Activity Analyzer.

This module provides comprehensive filtering capabilities for GitHub issues,
including comment count filters, state filters, label filters, assignee filters,
and date range filters.
"""

from datetime import datetime
from typing import List, Optional

from models import FilterCriteria, Issue, IssueState, Label
from utils.errors import ValidationError


class FilterEngine:
    """Engine for filtering GitHub issues based on various criteria."""

    def filter_issues(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """
        Filter issues based on the provided criteria.

        Args:
            issues: List of issues to filter
            criteria: Filtering criteria

        Returns:
            List of filtered issues

        Raises:
            ValueError: If issues list is None or criteria is invalid
        """
        if issues is None:
            raise ValidationError("issues", issues, "Issues list cannot be None")

        if criteria is None:
            raise ValidationError("criteria", criteria, "Filter criteria cannot be None")

        if len(issues) == 0:
            return []

        # Start with all issues and apply filters progressively
        filtered_issues = issues.copy()

        # Apply each filter
        filtered_issues = self._filter_by_comment_count(filtered_issues, criteria)
        filtered_issues = self._filter_by_state(filtered_issues, criteria)
        filtered_issues = self._filter_by_labels(filtered_issues, criteria)
        filtered_issues = self._filter_by_assignees(filtered_issues, criteria)
        filtered_issues = self._filter_by_date_range(filtered_issues, criteria)

        # Apply limit last
        if criteria.limit is not None:
            filtered_issues = filtered_issues[: criteria.limit]

        return filtered_issues

    def _filter_by_comment_count(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """Filter issues by comment count (min and max)."""
        filtered = []

        for issue in issues:
            # Check minimum comment count
            if (
                criteria.min_comments is not None
                and issue.comment_count < criteria.min_comments
            ):
                continue

            # Check maximum comment count
            if (
                criteria.max_comments is not None
                and issue.comment_count > criteria.max_comments
            ):
                continue

            filtered.append(issue)

        return filtered

    def _filter_by_state(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """Filter issues by state (open/closed)."""
        if criteria.state is None:
            return issues

        filtered = []
        target_state = criteria.state

        for issue in issues:
            if issue.state == target_state:
                filtered.append(issue)

        return filtered

    def _filter_by_labels(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """Filter issues by labels."""
        if not criteria.labels:
            return issues

        filtered = []
        target_labels = set(criteria.labels)

        for issue in issues:
            # Get issue label names
            issue_label_names = {label.name for label in issue.labels}

            # Skip if no match
            if not issue_label_names:
                continue

            # Apply ANY or ALL logic
            if criteria.any_labels:
                # ANY logic: match if any target label is present
                if issue_label_names & target_labels:
                    filtered.append(issue)
            else:
                # ALL logic: match if all target labels are present
                if target_labels.issubset(issue_label_names):
                    filtered.append(issue)

        return filtered

    def _filter_by_assignees(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """Filter issues by assignees."""
        if not criteria.assignees:
            return issues

        filtered = []
        target_assignees = set(criteria.assignees)

        for issue in issues:
            # Get issue assignee usernames
            issue_assignees = {assignee.username for assignee in issue.assignees}

            # Skip if no assignees
            if not issue_assignees:
                continue

            # Apply ANY or ALL logic
            if criteria.any_assignees:
                # ANY logic: match if any target assignee is assigned
                if issue_assignees & target_assignees:
                    filtered.append(issue)
            else:
                # ALL logic: match if all target assignees are assigned
                if target_assignees.issubset(issue_assignees):
                    filtered.append(issue)

        return filtered

    def _filter_by_date_range(
        self, issues: List[Issue], criteria: FilterCriteria
    ) -> List[Issue]:
        """Filter issues by creation date range."""
        filtered = []

        for issue in issues:
            # Check created_since filter
            if criteria.created_since is not None:
                if issue.created_at < criteria.created_since:
                    continue

            # Check created_until filter
            if criteria.created_until is not None:
                if issue.created_at > criteria.created_until:
                    continue

            # Check updated_since filter
            if criteria.updated_since is not None:
                if issue.updated_at < criteria.updated_since:
                    continue

            # Check updated_until filter
            if criteria.updated_until is not None:
                if issue.updated_at > criteria.updated_until:
                    continue

            filtered.append(issue)

        return filtered

    def get_filter_summary(self, criteria: FilterCriteria) -> str:
        """
        Get a human-readable summary of the active filters.

        Args:
            criteria: Filtering criteria

        Returns:
            String description of active filters
        """
        summary_parts = []

        if criteria.min_comments is not None:
            summary_parts.append(f"min_comments={criteria.min_comments}")

        if criteria.max_comments is not None:
            summary_parts.append(f"max_comments={criteria.max_comments}")

        if criteria.state is not None:
            summary_parts.append(f"state={criteria.state.value}")

        if criteria.labels:
            join_str = " OR " if criteria.any_labels else " AND "
            labels_str = join_str.join(criteria.labels)
            summary_parts.append(f"labels=[{labels_str}]")

        if criteria.assignees:
            join_str = " OR " if criteria.any_assignees else " AND "
            assignees_str = join_str.join(criteria.assignees)
            summary_parts.append(f"assignees=[{assignees_str}]")

        if criteria.created_since is not None:
            summary_parts.append(
                f"created_since={criteria.created_since.strftime('%Y-%m-%d')}"
            )

        if criteria.created_until is not None:
            summary_parts.append(
                f"created_until={criteria.created_until.strftime('%Y-%m-%d')}"
            )

        if criteria.updated_since is not None:
            summary_parts.append(
                f"updated_since={criteria.updated_since.strftime('%Y-%m-%d')}"
            )

        if criteria.updated_until is not None:
            summary_parts.append(
                f"updated_until={criteria.updated_until.strftime('%Y-%m-%d')}"
            )

        if criteria.limit is not None:
            summary_parts.append(f"limit={criteria.limit}")

        if summary_parts:
            return f"Filters: {', '.join(summary_parts)}"
        else:
            return "No filters applied"

    def validate_criteria(self, criteria: FilterCriteria) -> List[str]:
        """
        Validate filtering criteria and return any errors found.

        Args:
            criteria: Filtering criteria to validate

        Returns:
            List of error messages (empty if criteria is valid)
        """
        errors = []

        # Validate comment count ranges
        if criteria.min_comments is not None and criteria.max_comments is not None:
            if criteria.min_comments > criteria.max_comments:
                errors.append("min_comments cannot be greater than max_comments")

        # Validate date ranges
        if criteria.created_since and criteria.created_until:
            if criteria.created_since > criteria.created_until:
                errors.append("created_since cannot be after created_until")

        if criteria.updated_since and criteria.updated_until:
            if criteria.updated_since > criteria.updated_until:
                errors.append("updated_since cannot be after updated_until")

        # Validate that labels and assignees are non-empty if specified
        if criteria.labels:
            for label in criteria.labels:
                if not label.strip():
                    errors.append("Label names cannot be empty")
                    break

        if criteria.assignees:
            for assignee in criteria.assignees:
                if not assignee.strip():
                    errors.append("Assignee names cannot be empty")
                    break

        return errors
