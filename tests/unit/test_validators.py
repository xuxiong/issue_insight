"""
Unit tests for limit validation (T010-1).

These tests are written FIRST and expected to FAIL until validators are implemented.
This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime

# These imports will fail initially (TDD - tests FAIL first)
from lib.validators import validate_limit, apply_limit, ValidationError
from models import Issue, IssueState, User


@pytest.mark.unit
class TestValidateLimit:
    """Test limit validation (≥1 when specified)."""

    def test_valid_limits(self):
        """Test that valid limits pass validation."""
        valid_limits = [1, 10, 100, 1000, 9999]

        for limit in valid_limits:
            # Should not raise any exception
            result = validate_limit(limit)
            assert result == limit

    def test_none_limit(self):
        """Test that None limit (unlimited) passes validation."""
        result = validate_limit(None)
        assert result is None

    def test_invalid_limits(self):
        """Test that invalid limits raise validation errors."""
        invalid_limits = [0, -1, -10, -999]

        for limit in invalid_limits:
            with pytest.raises(ValidationError, match="Limit must be at least 1 when specified"):
                validate_limit(limit)

    def test_limit_zero_specific_error(self):
        """Test specific error for limit = 0."""
        try:
            validate_limit(0)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "Limit must be at least 1 when specified" in str(e)
            assert e.field == "limit"
            assert e.value == 0

    def test_limit_negative_specific_error(self):
        """Test specific error for negative limits."""
        try:
            validate_limit(-5)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "Limit must be at least 1 when specified" in str(e)
            assert e.field == "limit"
            assert e.value == -5

    def test_limit_validation_with_context(self):
        """Test limit validation with additional context."""
        limit = 0

        try:
            validate_limit(limit)
        except ValidationError as e:
            assert e.field == "limit"
            assert e.value == 0
            assert "Limit must be at least 1" in e.reason


@pytest.mark.unit
class TestApplyLimit:
    """Test apply_limit function with various inputs."""

    def test_apply_limit_with_valid_number(self):
        """Test applying a valid limit to a list."""
        items = list(range(10))  # [0, 1, 2, ..., 9]

        result = apply_limit(items, 5)

        assert result == [0, 1, 2, 3, 4]
        assert len(result) == 5

    def test_apply_limit_larger_than_list(self):
        """Test applying limit larger than list size."""
        items = [1, 2, 3]  # Only 3 items

        result = apply_limit(items, 10)

        assert result == [1, 2, 3]  # Should return all items
        assert len(result) == 3

    def test_apply_limit_equal_to_list_size(self):
        """Test applying limit equal to list size."""
        items = [1, 2, 3, 4, 5]

        result = apply_limit(items, 5)

        assert result == [1, 2, 3, 4, 5]
        assert len(result) == 5

    def test_apply_limit_none_no_limit(self):
        """Test applying None limit (unlimited)."""
        items = [1, 2, 3, 4, 5]

        result = apply_limit(items, None)

        assert result == [1, 2, 3, 4, 5]  # Should return all items
        assert len(result) == 5

    def test_apply_limit_zero_error(self):
        """Test applying limit = 0 should raise error."""
        items = [1, 2, 3]

        with pytest.raises(ValueError, match="Limit must be at least 1 when specified"):
            apply_limit(items, 0)

    def test_apply_limit_negative_error(self):
        """Test applying negative limit should raise error."""
        items = [1, 2, 3]

        with pytest.raises(ValueError, match="Limit must be at least 1 when specified"):
            apply_limit(items, -1)

    def test_apply_limit_to_empty_list(self):
        """Test applying limit to empty list."""
        items = []

        result = apply_limit(items, 10)

        assert result == []
        assert len(result) == 0

    def test_apply_limit_with_single_item(self):
        """Test applying limit to single item list."""
        items = [42]

        result = apply_limit(items, 1)

        assert result == [42]
        assert len(result) == 1

    def test_apply_limit_preserves_order(self):
        """Test that apply_limit preserves original order."""
        items = ["zebra", "apple", "banana", "cherry"]

        result = apply_limit(items, 3)

        assert result == ["zebra", "apple", "banana"]  # First 3 items in original order

    def test_apply_limit_does_not_modify_original(self):
        """Test that apply_limit doesn't modify the original list."""
        items = [1, 2, 3, 4, 5]
        original_copy = items.copy()

        result = apply_limit(items, 3)

        # Original list should be unchanged
        assert items == original_copy
        # Result should be limited
        assert len(result) == 3


@pytest.mark.unit
class TestApplyLimitWithIssues:
    """Test apply_limit function specifically with Issue objects."""

    def test_apply_limit_to_issues(self):
        """Test applying limit to list of Issue objects."""
        # Create mock issue objects
        issues = []
        for i in range(5):
            author = User(
                id=1,
                username=f"user{i}",
                display_name=f"User {i}",
                avatar_url=f"https://github.com/user{i}.png"
            )
            issue = Issue(
                id=i + 1,
                number=i + 1,
                title=f"Issue {i + 1}",
                body=f"Body {i + 1}",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=[],
                labels=[],
                comment_count=i + 1,
                comments=[],
                is_pull_request=False
            )
            issues.append(issue)

        # Apply limit of 3
        result = apply_limit(issues, 3)

        assert len(result) == 3
        assert result[0].number == 1
        assert result[1].number == 2
        assert result[2].number == 3

    def test_apply_limit_issues_preserves_type(self):
        """Test that apply_limit preserves Issue object types."""
        author = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="https://github.com/testuser.png"
        )

        issue = Issue(
            id=123,
            number=42,
            title="Test Issue",
            body="Test body",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=5,
            comments=[],
            is_pull_request=False
        )

        issues = [issue]
        result = apply_limit(issues, 1)

        assert len(result) == 1
        assert isinstance(result[0], Issue)
        assert result[0].id == 123
        assert result[0].number == 42


@pytest.mark.unit
class TestLimitValidationEdgeCases:
    """Test limit validation edge cases and error handling."""

    def test_apply_limit_none_list_error(self):
        """Test applying limit to None list should raise error."""
        with pytest.raises(ValueError, match="Issues list cannot be None"):
            apply_limit(None, 10)

    def test_apply_limit_non_integer_limit_error(self):
        """Test applying non-integer limit should raise error."""
        items = [1, 2, 3]

        # Note: None is handled as no limit, so excluded from invalid list
        # Note: True/False are rejected as type errors since booleans are not allowed
        invalid_limits = [3.14, "10"]

        for invalid_limit in invalid_limits:
            with pytest.raises((TypeError, ValueError)):
                apply_limit(items, invalid_limit)

        # Test None separately - should not raise
        result = apply_limit(items, None)
        assert result == [1, 2, 3]  # Should return all items

        # Test boolean values - should raise TypeError since booleans are not allowed
        with pytest.raises(TypeError, match="got boolean"):
            apply_limit(items, True)

        with pytest.raises(TypeError, match="got boolean"):
            apply_limit(items, False)

    def test_validate_limit_with_large_numbers(self):
        """Test limit validation with very large numbers."""
        # Test with maximum reasonable values
        large_valid_limit = 1000000
        result = validate_limit(large_valid_limit)
        assert result == large_valid_limit

        # Test with very large numbers that might cause memory issues
        very_large_limit = 10**18
        result = validate_limit(very_large_limit)
        assert result == very_large_limit

    def test_apply_limit_performance_with_large_lists(self):
        """Test that apply_limit performs well with large lists."""
        import time

        # Create a large list (simulating many issues)
        large_list = list(range(10000))  # 10,000 items

        start_time = time.time()
        result = apply_limit(large_list, 100)
        end_time = time.time()

        # Should complete quickly (< 0.1 second for this operation)
        execution_time = end_time - start_time
        assert execution_time < 0.1, f"Too slow: {execution_time:.3f}s"
        assert len(result) == 100
        assert result == list(range(100))

    def test_apply_limit_with_memory_efficiency(self):
        """Test that apply_limit doesn't create unnecessary copies."""
        import sys

        # Create a list of objects (not just integers)
        objects = [{"id": i, "data": f"item_{i}"} for i in range(100)]

        # Apply limit should return new list but not copy unnecessary objects
        result = apply_limit(objects, 50)

        # Objects in result should be the same instances (no deep copy)
        for i, item in enumerate(result):
            assert objects[i] is item  # Same object instance

    def test_limit_in_filter_criteria_context(self):
        """Test limit validation in the context of filter criteria."""
        # This simulates how limit validation would work in the filtering system
        def filter_issues_with_limit(issues, filter_criteria):
            # Validate limit first
            validated_limit = validate_limit(filter_criteria.get('limit', None))

            # Apply filter logic here (simplified for test)
            filtered_issues = issues  # Assume all issues passed filters

            # Apply limit
            return apply_limit(filtered_issues, validated_limit)

        issues = list(range(20))
        criteria = {"min_comments": 5, "limit": 5}

        result = filter_issues_with_limit(issues, criteria)
        assert result == [0, 1, 2, 3, 4]

        # Test with invalid limit in criteria
        invalid_criteria = {"min_comments": 5, "limit": 0}

        with pytest.raises(ValidationError):
            filter_issues_with_limit(issues, invalid_criteria)


@pytest.mark.unit
class TestLimitValidationIntegration:
    """Test limit validation in realistic integration scenarios."""

    def test_limit_validation_in_cli_context(self):
        """Test limit validation as it would be used in CLI argument parsing."""
        # Simulate CLI input validation
        def validate_cli_limit(limit_str):
            try:
                limit = int(limit_str) if limit_str else None
                return validate_limit(limit)
            except ValueError as e:
                raise ValidationError("limit", limit_str, f"Invalid integer: {limit_str}")

        # Test valid CLI inputs
        assert validate_cli_limit("100") == 100
        assert validate_cli_limit("") is None  # Empty string means no limit

        # Test invalid CLI inputs
        with pytest.raises(ValidationError):
            validate_cli_limit("0")

        with pytest.raises(ValidationError):
            validate_cli_limit("-5")

    def test_limit_validation_with_user_feedback(self):
        """Test limit validation with helpful user feedback."""
        def validate_and_suggest(limit):
            try:
                return validate_limit(limit)
            except ValidationError as e:
                # Add helpful suggestion
                if e.value == 0:
                    e.reason += " Use a positive number like 10 or 100."
                elif e.value < 0:
                    e.reason += " Limits must be positive, not negative."
                raise

        # Test with helpful suggestions
        try:
            validate_and_suggest(0)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "positive number like 10 or 100" in e.reason

    def test_limit_in_pagination_context(self):
        """Test limit validation in pagination context."""
        # In pagination, limit often interacts with page_size
        def calculate_pagination(total_items, limit, page_size=100):
            validated_limit = validate_limit(limit)
            validated_page_size = validate_limit(page_size)

            if validated_limit and validated_limit < validated_page_size:
                # If limit is smaller than page_size, adjust page_size
                validated_page_size = validated_limit

            return {
                "total_pages": (total_items + validated_page_size - 1) // validated_page_size,
                "limit": validated_limit,
                "page_size": validated_page_size
            }

        # Test valid pagination scenarios
        result = calculate_pagination(1000, 150, 100)
        assert result["limit"] == 150
        assert result["page_size"] == 100  # Unchanged
        assert result["total_pages"] == 10

        # Test limit smaller than page_size
        result = calculate_pagination(1000, 50, 100)
        assert result["limit"] == 50
        assert result["page_size"] == 50  # Adjusted
        assert result["total_pages"] == 20

    def test_limit_with_complex_objects(self):
        """Test limit validation with complex nested objects."""
        class ComplexItem:
            def __init__(self, id, data):
                self.id = id
                self.data = data
                self.metadata = {"created": datetime.now(), "size": len(data)}

        items = [
            ComplexItem(i, f"data_{i}" * 10)  # Create items with substantial data
            for i in range(10)
        ]

        # Apply limit should work with complex objects
        result = apply_limit(items, 3)

        assert len(result) == 3
        assert all(isinstance(item, ComplexItem) for item in result)
        assert result[0].id == 0
        assert result[1].id == 1
        assert result[2].id == 2
