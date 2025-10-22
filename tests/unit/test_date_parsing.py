"""
Unit tests for date parsing and validation (T022).

These tests are written FIRST and expected to FAIL until date parsing
utilities are implemented. This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime, date

# These imports will FAIL initially (TDD - tests must FAIL first)
from utils.validators import validate_date_range, parse_iso_date


@pytest.mark.unit
class TestISODatesParsing:
    """Test ISO 8601 date format parsing."""

    def test_parse_valid_iso_date_string(self):
        """Test parsing valid ISO 8601 date strings."""
        valid_dates = [
            ("2024-01-15", datetime(2024, 1, 15)),
            ("2023-12-31", datetime(2023, 12, 31)),
            ("2025-02-28", datetime(2025, 2, 28)),
            ("2024-02-29", datetime(2024, 2, 29)),  # Leap year
        ]

        for date_str, expected in valid_dates:
            # This will FAIL initially
            result = parse_iso_date(date_str)
            assert result == expected
            assert isinstance(result, datetime)

    def test_parse_iso_datetime_string(self):
        """Test parsing ISO datetime strings."""
        valid_datetimes = [
            ("2024-01-15T10:30:00", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024-01-15T14:20:30Z", datetime(2024, 1, 15, 14, 20, 30)),
            ("2023-12-31T23:59:59", datetime(2023, 12, 31, 23, 59, 59)),
        ]

        for datetime_str, expected in valid_datetimes:
            # This will FAIL initially
            result = parse_iso_date(datetime_str)
            assert result == expected
            assert isinstance(result, datetime)

    def test_parse_invalid_date_formats(self):
        """Test handling of invalid date formats."""
        invalid_dates = [
            "2024/01/15",  # Wrong separator
            "01-15-2024",  # MM-DD-YYYY format
            "15/01/2024",  # DD/MM/YYYY format
            "2024-1-15",  # Missing zero padding
            "2024-13-45",  # Invalid month/day
            "not-a-date",  # Non-date string
            "",  # Empty string
            "2024-02-30",  # Invalid day for February
            "2023-02-29",  # Not a leap year
        ]

        for invalid_date in invalid_dates:
            # This will FAIL initially - should raise ValidationError
            with pytest.raises(Exception):  # Accept any exception for now
                parse_iso_date(invalid_date)

    def test_parse_edge_dates(self):
        """Test parsing edge date cases."""
        edge_cases = [
            ("1900-01-01", datetime(1900, 1, 1)),  # Early date
            ("2100-12-31", datetime(2100, 12, 31)),  # Future date
            ("2024-03-01", datetime(2024, 3, 1)),  # March 1st
            ("2024-12-31", datetime(2024, 12, 31)),  # Year end
        ]

        for date_str, expected in edge_cases:
            # This will FAIL initially
            result = parse_iso_date(date_str)
            assert result == expected

    def test_parse_date_with_timezones(self):
        """Test parsing dates with timezone information."""
        # Note: GitHub API typically returns UTC, so we should normalize
        timezone_dates = [
            ("2024-01-15T10:30:00Z", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024-01-15T10:30:00+00:00", datetime(2024, 1, 15, 10, 30, 0)),
            (
                "2024-01-15T12:30:00+02:00",
                datetime(2024, 1, 15, 12, 30, 0),
            ),  # Should normalize to UTC
        ]

        for date_str, expected in timezone_dates:
            # This will FAIL initially
            result = parse_iso_date(date_str)
            assert result == expected


@pytest.mark.unit
class TestDateRangeValidation:
    """Test date range validation logic."""

    def test_valid_date_ranges(self):
        """Test validation of valid date ranges."""
        valid_ranges = [
            # Same date
            (datetime(2024, 1, 15), datetime(2024, 1, 15)),
            # Start before end
            (datetime(2024, 1, 1), datetime(2024, 12, 31)),
            (datetime(2023, 12, 31), datetime(2024, 1, 1)),
            # Different years
            (datetime(2023, 6, 15), datetime(2024, 3, 20)),
        ]

        for start_date, end_date in valid_ranges:
            # This will FAIL initially
            result = validate_date_range(start_date, end_date)
            assert result is True  # Should return True for valid ranges

    def test_invalid_date_ranges(self):
        """Test validation of invalid date ranges."""
        invalid_ranges = [
            # End before start
            (datetime(2024, 12, 31), datetime(2024, 1, 1)),
            (datetime(2024, 1, 15), datetime(2024, 1, 14)),
            # Cross-year invalid
            (datetime(2024, 6, 15), datetime(2023, 3, 20)),
        ]

        for start_date, end_date in invalid_ranges:
            # This will FAIL initially - should raise any exception
            with pytest.raises(Exception):
                validate_date_range(start_date, end_date)

    def test_date_range_with_none_values(self):
        """Test date range validation with None values."""
        # Both None should be valid (no date filtering)
        # This will FAIL initially
        result = validate_date_range(None, None)
        assert result is True

        # One None should be valid
        test_date = datetime(2024, 1, 15)

        result = validate_date_range(None, test_date)
        assert result is True

        result = validate_date_range(test_date, None)
        assert result is True

    def test_date_range_boundary_cases(self):
        """Test date range validation at boundaries."""
        # Very close dates
        close_dates = [
            (datetime(2024, 1, 15, 10, 30, 0), datetime(2024, 1, 15, 10, 30, 1)),
            (datetime(2024, 1, 15, 23, 59, 59), datetime(2024, 1, 16, 0, 0, 0)),
        ]

        for start_date, end_date in close_dates:
            # This will FAIL initially
            result = validate_date_range(start_date, end_date)
            assert result is True

    def test_invalid_arguments(self):
        """Test validation with invalid argument types."""
        valid_datetime = datetime(2024, 1, 15)

        # Non-datetime arguments
        invalid_args = [
            ("2024-01-15", valid_datetime),
            (valid_datetime, "2024-01-16"),
            (123, valid_datetime),
            (valid_datetime, 456),
        ]

        for start, end in invalid_args:
            # This will FAIL initially
            with pytest.raises(TypeError, match="must be datetime objects or None"):
                validate_date_range(start, end)


@pytest.mark.unit
class TestDateFilterIntegration:
    """Test date parsing integration with filter engine."""

    def test_date_parsing_in_filter_criteria(self):
        """Test that date strings can be used in FilterCriteria."""
        from models import FilterCriteria

        # Test with date strings (should be parsed to datetime)
        criteria = FilterCriteria(
            created_since="2024-01-01",
            created_until="2024-12-31",
            updated_since="2024-06-01",
        )

        # This will FAIL initially - FilterCriteria should accept and parse date strings
        assert isinstance(criteria.created_since, datetime)
        assert isinstance(criteria.created_until, datetime)
        assert isinstance(criteria.updated_since, datetime)

        assert criteria.created_since == datetime(2024, 1, 1)
        assert criteria.created_until == datetime(2024, 12, 31)
        assert criteria.updated_since == datetime(2024, 6, 1)

    def test_invalid_date_strings_in_filters(self):
        """Test handling of invalid date strings in FilterCriteria."""
        from models import FilterCriteria
        from pydantic import ValidationError

        invalid_dates = ["invalid-date", "2024/01/01", "2024-13-45"]

        for invalid_date in invalid_dates:
            # This will FAIL initially - should raise ValidationError
            with pytest.raises((ValueError, ValidationError)):
                FilterCriteria(created_since=invalid_date)

    def test_date_range_validation_in_filters(self):
        """Test date range validation in FilterCriteria construction."""
        from models import FilterCriteria

        # Valid range
        criteria = FilterCriteria(
            created_since=datetime(2024, 1, 1), created_until=datetime(2024, 12, 31)
        )
        assert criteria.created_since == datetime(2024, 1, 1)
        assert criteria.created_until == datetime(2024, 12, 31)

        # Invalid range - end before start
        with pytest.raises(
            ValueError, match="created_since cannot be after created_until"
        ):
            FilterCriteria(
                created_since=datetime(2024, 12, 31), created_until=datetime(2024, 1, 1)
            )
