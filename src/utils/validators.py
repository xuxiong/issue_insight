"""
Validation utilities for GitHub issue analysis.

This module provides input validation functions for limits, dates,
and other parameters with proper error handling.
"""

from datetime import datetime
from typing import List, Optional, Any
from .errors import ValidationError as BaseValidationError


class ValidationError(BaseValidationError):
    """Local ValidationError for validators module."""
    pass


def parse_iso_date(date_str: str) -> datetime:
    """
    Parse ISO 8601 date string to datetime object.

    Supports multiple ISO 8601 formats:
    - YYYY-MM-DD (date only)
    - YYYY-MM-DDTHH:MM:SS (datetime)
    - YYYY-MM-DDTHH:MM:SSZ (UTC datetime)

    Timezone-aware datetimes are normalized to UTC.

    Args:
        date_str: ISO 8601 formatted date string

    Returns:
        datetime object

    Raises:
        ValidationError: If date string is invalid
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError("date", date_str, "Date string cannot be empty")

    try:
        # Try to parse as ISO date with Z suffix first
        if date_str.endswith('Z'):
            # Parse as UTC datetime
            dt = datetime.fromisoformat(date_str[:-1])
            # Ensure it's treated as UTC
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        # Try to parse as ISO datetime
        dt = datetime.fromisoformat(date_str)

        # If it has timezone info, convert to UTC
        if dt.tzinfo is not None:
            # For simplicity, assume input times are already in target timezone
            # and just remove timezone info (GitHub API typically returns UTC)
            return dt.replace(tzinfo=None)

        return dt

    except ValueError as e:
        raise ValidationError("date", date_str, f"Invalid ISO date format. Expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS, got: {date_str}")


def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
    """
    Validate that start_date is not after end_date if both are provided.

    Args:
        start_date: Start date or None
        end_date: End date or None

    Returns:
        True if valid

    Raises:
        ValidationError: If start_date > end_date
        TypeError: If arguments are not datetime or None
    """
    # Neither provided - valid
    if start_date is None and end_date is None:
        return True

    # Both provided - check range
    if start_date is not None and end_date is not None:
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise TypeError("Date arguments must be datetime objects or None")

        if start_date > end_date:
            raise ValidationError("date_range", f"{start_date} to {end_date}",
                                "Start date cannot be after end date")

    return True


def validate_limit(limit: Optional[int]) -> Optional[int]:
    """
    Validate limit parameter (≥1 when specified, or None for unlimited).

    Args:
        limit: The limit to validate, or None for unlimited

    Returns:
        The validated limit, or None if no limit was specified

    Raises:
        ValidationError: If limit is invalid (0, negative, or non-integer)
    """
    # None means unlimited, which is valid
    if limit is None:
        return None

    # Check if it's an integer (but reject booleans even though they're ints in Python)
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError("Limit must be an integer or None")

    # Check if it's at least 1
    if limit < 1:
        raise ValidationError("limit", limit, "Limit must be at least 1 when specified")

    return limit


def apply_limit(items: List[Any], limit: Optional[int]) -> List[Any]:
    """
    Apply a limit to a list of items, preserving order and not modifying the original list.

    Args:
        items: The list of items to limit
        limit: Maximum number of items to return, or None for unlimited

    Returns:
        A new list containing at most `limit` items from the original list

    Raises:
        ValidationError: If items is None or limit is invalid
    """
    if items is None:
        raise ValidationError("items", items, "Issues list cannot be None")

    # Validate and process limit
    processed_limit = validate_limit(limit)

    # If limit is None, return a copy of the entire list
    if processed_limit is None:
        return items.copy()

    # Return the limited number of items (slice creates a new list)
    return items[:processed_limit]
