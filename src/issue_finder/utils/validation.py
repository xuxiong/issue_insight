"""
Input validation utilities.

This module provides functions for validating user input including repository URLs,
filter parameters, and other command-line arguments.
"""

import re
from datetime import datetime
from typing import Optional, List

from ..models.metrics import FilterCriteria


def validate_repository_url(url: str) -> None:
    """
    Validate GitHub repository URL format.

    Args:
        url: Repository URL to validate

    Raises:
        ValueError: If URL format is invalid
    """
    # GitHub URL pattern: https://github.com/owner/repo
    pattern = r'^https://github\.com/[^/]+/[^/]+$'

    if not re.match(pattern, url):
        raise ValueError(
            f"Invalid repository URL format: {url}\n"
            "Expected format: https://github.com/owner/repo\n"
            "Example: https://github.com/facebook/react"
        )


def validate_filters(
    min_comments: Optional[int] = None,
    max_comments: Optional[int] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
) -> FilterCriteria:
    """
    Validate and normalize filter parameters.

    Args:
        min_comments: Minimum comment count filter
        max_comments: Maximum comment count filter
        state: Issue state filter
        labels: List of label names
        assignees: List of assignee usernames
        created_after: Created date lower bound (YYYY-MM-DD)
        created_before: Created date upper bound (YYYY-MM-DD)

    Returns:
        Validated FilterCriteria object

    Raises:
        ValueError: If any filter parameter is invalid
    """
    # Validate comment count filters
    if min_comments is not None:
        if min_comments < 0:
            raise ValueError(
                f"Invalid minimum comment count: {min_comments}. "
                "Comment count must be non-negative. Use --min-comments 0 or higher."
            )

    if max_comments is not None:
        if max_comments < 0:
            raise ValueError(
                f"Invalid maximum comment count: {max_comments}. "
                "Comment count must be non-negative. Use --max-comments 0 or higher."
            )

    if min_comments is not None and max_comments is not None:
        if min_comments > max_comments:
            raise ValueError(
                f"Minimum comment count ({min_comments}) cannot be greater than "
                f"maximum comment count ({max_comments})."
            )

    # Validate state filter
    valid_states = ["open", "closed", "all"]
    if state is not None and state not in valid_states:
        raise ValueError(
            f"Invalid state: {state}. Must be one of: {', '.join(valid_states)}"
        )

    # Validate dates
    created_after_date = None
    if created_after is not None:
        created_after_date = validate_date(created_after, "created-after")

    created_before_date = None
    if created_before is not None:
        created_before_date = validate_date(created_before, "created-before")

    # Validate date range
    if created_after_date and created_before_date:
        if created_after_date > created_before_date:
            raise ValueError(
                f"Created after date ({created_after}) cannot be later than "
                f"created before date ({created_before})."
            )

    # Validate labels and assignees (basic validation)
    labels = labels or []
    assignees = assignees or []

    for label in labels:
        if not label.strip():
            raise ValueError("Label names cannot be empty")

    for assignee in assignees:
        if not assignee.strip():
            raise ValueError("Assignee usernames cannot be empty")

    return FilterCriteria(
        min_comments=min_comments,
        max_comments=max_comments,
        state=state,
        labels=labels,
        assignees=assignees,
        created_after=created_after_date,
        created_before=created_before_date,
    )


def validate_date(date_str: str, field_name: str) -> datetime:
    """
    Validate date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date format for --{field_name}: '{date_str}'. "
            "Use YYYY-MM-DD format. Example: 2024-01-15"
        )


def validate_output_format(format_str: str) -> str:
    """
    Validate output format.

    Args:
        format_str: Output format string to validate

    Returns:
        Validated format string

    Raises:
        ValueError: If format is invalid
    """
    valid_formats = ["json", "csv", "table"]

    if format_str not in valid_formats:
        raise ValueError(
            f"Invalid output format: {format_str}. "
            f"Must be one of: {', '.join(valid_formats)}"
        )

    return format_str.lower()


def parse_repository_url(url: str) -> tuple[str, str]:
    """
    Parse owner and repository name from GitHub URL.

    Args:
        url: GitHub repository URL

    Returns:
        Tuple of (owner, repository_name)

    Raises:
        ValueError: If URL format is invalid
    """
    validate_repository_url(url)

    # Extract owner and repo from URL
    # https://github.com/owner/repo -> ["", "owner", "repo"]
    parts = url.split("/")

    if len(parts) < 5:
        raise ValueError(f"Invalid repository URL: {url}")

    owner = parts[3]
    repo = parts[4]

    if not owner or not repo:
        raise ValueError(f"Unable to extract owner and repository from URL: {url}")

    return owner, repo


def validate_comment_count_range(min_val: Optional[int], max_val: Optional[int]) -> None:
    """
    Validate comment count range parameters.

    Args:
        min_val: Minimum comment count
        max_val: Maximum comment count

    Raises:
        ValueError: If range is invalid
    """
    if min_val is not None and min_val < 0:
        raise ValueError("Minimum comment count cannot be negative")

    if max_val is not None and max_val < 0:
        raise ValueError("Maximum comment count cannot be negative")

    if min_val is not None and max_val is not None and min_val > max_val:
        raise ValueError(
            f"Minimum comment count ({min_val}) cannot be greater than "
            f"maximum comment count ({max_val})"
        )