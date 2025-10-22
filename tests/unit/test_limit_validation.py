"""
Unit tests for limit validation and application (T015).

These tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import pytest
import pydantic
from unittest.mock import Mock
from datetime import datetime

# These imports will FAIL initially (TDD - tests must FAIL first)
from utils.validators import validate_limit, apply_limit, ValidationError
from models import Issue, IssueState, FilterCriteria, User


@pytest.mark.unit
class TestLimitValidation:
    """Unit tests for limit validation in CLI context."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_issue(self, **kwargs):
        """Create test Issue objects."""
        defaults = {
            "id": 1,
            "number": 101,
            "title": "Test Issue",
            "body": "Test body",
            "state": IssueState.OPEN,
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
            "updated_at": datetime(2024, 1, 16, 14, 20, 0),
            "closed_at": None,
            "author": self.mock_user,
            "assignees": [],
            "labels": [],
            "comments": [],
            "is_pull_request": False,
            "comment_count": 5,
        }
        defaults.update(kwargs)
        return Issue(**defaults)

    def test_default_limit_100_behavior(self):
        """
        Test default limit = 100 behavior.

        This is critical for User Story 1 - CLI should have sensible defaults.
        """
        # Arrange - Create more than 100 issues to test default limit
        issues = []
        for i in range(150):
            issues.append(
                self.create_test_issue(
                    id=i, number=100 + i, title=f"Issue {i}", comment_count=5
                )
            )

        # Act - This should use default limit of 100
        result = apply_limit(issues, 100)  # Simulating default limit

        # Assert - Should limit to 100 results
        assert len(result) == 100
        # Should contain first 100 issues (in order)
        assert result[0].number == 100
        assert result[-1].number == 199

    def test_custom_limit_specification(self):
        """Test custom limit specification from CLI."""
        # Arrange
        issues = []
        for i in range(20):
            issues.append(
                self.create_test_issue(
                    id=i, number=200 + i, title=f"Issue {i}", comment_count=3
                )
            )

        # Act - Test custom limit of 5
        result = apply_limit(issues, 5)

        # Assert - Should limit to specified amount
        assert len(result) == 5
        assert result[0].number == 200
        assert result[-1].number == 204

    def test_limit_validation_errors(self):
        """
        Test limit validation errors (< 1).

        CLI should reject invalid limit values with helpful error messages.
        """
        # Arrange - Create test data
        issues = [self.create_test_issue(number=101, comment_count=5)]

        # Act & Assert - Test invalid limits in FilterCriteria model
        # This tests the Pydantic validation layer

        # Limit of 0 should raise Pydantic.ValidationError
        with pytest.raises(pydantic.ValidationError) as exc_info:
            FilterCriteria(limit=0)
        error_str = str(exc_info.value)
        assert "at least 1" in error_str.lower()

        # Negative limit should raise Pydantic.ValidationError
        with pytest.raises(pydantic.ValidationError) as exc_info:
            FilterCriteria(limit=-5)
        error_str = str(exc_info.value)
        assert "at least 1" in error_str.lower()

        # Zero validation directly in validator
        with pytest.raises(ValidationError) as exc_info:
            validate_limit(0)
        assert "must be at least 1" in str(exc_info.value).lower()

    def test_limit_greater_than_available(self):
        """Test limit greater than available issues."""
        # Arrange - Only 5 issues available
        issues = []
        for i in range(5):
            issues.append(
                self.create_test_issue(
                    id=i, number=300 + i, title=f"Issue {i}", comment_count=4
                )
            )

        # Act - Request more issues than available
        result = apply_limit(issues, 10)

        # Assert - Should return all available issues
        assert len(result) == 5
        assert result == issues  # Should preserve all issues

    def test_limit_exactly_matches_available(self):
        """Test limit exactly matches available issues."""
        # Arrange - Exactly 10 issues
        issues = []
        for i in range(10):
            issues.append(
                self.create_test_issue(
                    id=i, number=400 + i, title=f"Issue {i}", comment_count=6
                )
            )

        # Act - Request exactly 10 issues
        result = apply_limit(issues, 10)

        # Assert - Should return all issues
        assert len(result) == 10
        assert result == issues

    def test_limit_in_filter_criteria_context(self):
        """Test limit in FilterCriteria context."""
        # Arrange - Create filter criteria with limit
        filter_criteria = FilterCriteria(min_comments=3, max_comments=10, limit=5)

        # Create matching issues (all have >=3 and <=10 comments)
        issues = []
        for i in range(8):  # Create 8 matching issues
            issues.append(
                self.create_test_issue(
                    id=i,
                    number=500 + i,
                    title=f"Issue {i}",
                    comment_count=5 + i % 3,  # 5, 6, 7, 8, 5, 6, 7, 8
                )
            )

        # Apply as would happen in real filtering logic
        # 1. Apply comment filter (all should pass)
        filtered_by_comments = [
            issue for issue in issues if 3 <= issue.comment_count <= 10
        ]
        assert len(filtered_by_comments) == 8

        # 2. Apply limit
        result = apply_limit(filtered_by_comments, filter_criteria.limit)

        # Assert - Should limit to 5
        assert len(result) == 5
        assert result[0].number == 500
        assert result[-1].number == 504

    def test_limit_preserves_order(self):
        """Test that limit preserves original issue order."""
        # Arrange - Create issues in specific order
        issues = [
            self.create_test_issue(
                number=301,
                comment_count=10,
                title="First",
                created_at=datetime(2024, 1, 10),
            ),
            self.create_test_issue(
                number=302,
                comment_count=8,
                title="Second",
                created_at=datetime(2024, 1, 11),
            ),
            self.create_test_issue(
                number=303,
                comment_count=12,
                title="Third",
                created_at=datetime(2024, 1, 12),
            ),
            self.create_test_issue(
                number=304,
                comment_count=6,
                title="Fourth",
                created_at=datetime(2024, 1, 13),
            ),
            self.create_test_issue(
                number=305,
                comment_count=9,
                title="Fifth",
                created_at=datetime(2024, 1, 14),
            ),
            self.create_test_issue(
                number=306,
                comment_count=11,
                title="Sixth",
                created_at=datetime(2024, 1, 15),
            ),
        ]

        # Act - Limit to 4
        result = apply_limit(issues, 4)

        # Assert - Should preserve original order
        assert len(result) == 4
        assert result[0].number == 301 and result[0].title == "First"
        assert result[1].number == 302 and result[1].title == "Second"
        assert result[2].number == 303 and result[2].title == "Third"
        assert result[3].number == 304 and result[3].title == "Fourth"

    def test_limit_none_unlimited(self):
        """Test that limit=None means unlimited."""
        # Arrange - Create many issues
        issues = []
        for i in range(50):
            issues.append(
                self.create_test_issue(
                    id=i, number=600 + i, title=f"Issue {i}", comment_count=i % 5 + 1
                )
            )

        # Act - Apply unlimited limit
        result = apply_limit(issues, None)

        # Assert - Should return all issues
        assert len(result) == 50
        assert result == issues

    def test_limit_zero_with_user_feedback(self):
        """Test limit=0 with helpful user feedback."""
        # Arrange
        issues = [self.create_test_issue(number=101, comment_count=5)]

        # Act & Assert - Should provide helpful error message from Pydantic
        try:
            FilterCriteria(limit=0)
            assert False, "Should have raised Pydantic ValidationError"
        except pydantic.ValidationError as e:
            error_str = str(e)
            assert "at least 1" in error_str.lower()

        # Also test the validator function directly
        try:
            validate_limit(0)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "must be at least 1" in str(e).lower()
            assert e.field == "limit"
            assert e.value == 0

    def test_limit_in_cli_parsing_context(self):
        """Test limit validation in CLI argument parsing context."""
        # Simulate CLI argument parsing scenarios

        # Valid CLI inputs
        valid_inputs = [("10", 10), ("100", 100), ("1", 1), ("999", 999)]

        for cli_str, expected in valid_inputs:
            # Simulate CLI parsing
            try:
                parsed_int = int(cli_str)
                result = validate_limit(parsed_int)
                assert result == expected
            except ValueError:
                pytest.fail(f"Valid CLI input '{cli_str}' should not raise error")

        # Invalid CLI inputs should raise helpful errors
        invalid_inputs = ["0", "-1", "-10", "0.5", "abc", ""]

        for cli_str in invalid_inputs:
            try:
                parsed_int = int(cli_str) if cli_str else 0
                try:
                    validate_limit(parsed_int)
                    pytest.fail(
                        f"Invalid CLI input '{cli_str}' should raise ValidationError"
                    )
                except ValidationError as e:
                    assert "must be at least 1" in str(e).lower()
            except ValueError:
                # Non-numeric input should be caught by CLI parser
                pass

    def test_limit_limits_performance(self):
        """Test that limit application is performant with large datasets."""
        # Arrange - Create large dataset
        large_issues = []
        for i in range(10000):
            large_issues.append(
                self.create_test_issue(
                    id=i,
                    number=1000 + i,
                    title=f"Large Issue {i}",
                    comment_count=i % 50,
                )
            )

        # Act - Should complete quickly
        import time

        start_time = time.time()
        result = apply_limit(large_issues, 1000)
        end_time = time.time()

        # Assert - Performance check
        execution_time = end_time - start_time
        assert (
            execution_time < 0.1
        ), f"Limit application should be fast (<0.1s), took {execution_time:.3f}s"

        assert len(result) == 1000
        assert result[0].number == 1000
        assert result[-1].number == 1999

    def test_limit_with_complex_filters_combined(self):
        """Test limit applied after complex filtering chain."""
        # Arrange - Start with many issues
        all_issues = []
        for i in range(100):
            all_issues.append(
                self.create_test_issue(
                    id=i,
                    number=700 + i,
                    title=f"Complex Issue {i}",
                    comment_count=i,  # Varying comment counts
                )
            )

        # Simulate filtering chain:
        # 1. Filter by min_comments >= 10 (should leave 90 issues: 10-99)
        comment_filtered = [issue for issue in all_issues if issue.comment_count >= 10]
        assert len(comment_filtered) == 90

        # 2. Apply limit of 20
        final_result = apply_limit(comment_filtered, 20)

        # Assert - Should get 20 issues from the comment-filtered set
        assert len(final_result) == 20
        # Should start from the first comment-filtered issue (comment_count=10)
        assert final_result[0].comment_count == 10
        assert final_result[-1].comment_count == 29

    def test_limit_validation_edge_cases(self):
        """Test limit validation edge cases."""
        # Edge: Very large numbers
        large_valid_limit = 1000000
        result = validate_limit(large_valid_limit)
        assert result == large_valid_limit

        # Edge: Minimum valid limit
        min_valid_limit = 1
        result = validate_limit(min_valid_limit)
        assert result == min_valid_limit

        # Edge: Just below minimum
        just_below_min = 0
        with pytest.raises(ValidationError):
            validate_limit(just_below_min)

        # Edge: Negative number very small
        very_small_negative = -1
        with pytest.raises(ValidationError):
            validate_limit(very_small_negative)
