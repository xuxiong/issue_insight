"""
Unit tests for comment count filtering logic (T013).

These tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

# These imports will FAIL initially (TDD - tests must FAIL first)
from services.filter_engine import FilterEngine
from models import Issue, FilterCriteria, IssueState, User, Label


@pytest.mark.unit
class TestCommentCountFiltering:
    """Unit tests for comment count filtering logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # This will FAIL initially - FilterEngine may not be fully implemented
        self.filter_engine = FilterEngine()
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_issue(self, **kwargs):
        """Helper to create test Issue objects."""
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

    def test_min_comments_filter(self):
        """
        Test min-comments filter (>=5).

        This is the primary filtering requirement for User Story 1.
        """
        # Arrange - Create issues with various comment counts
        issues = [
            self.create_test_issue(
                id=1, number=101, comment_count=3
            ),  # Should be filtered out
            self.create_test_issue(
                id=2, number=102, comment_count=5
            ),  # Should pass (minimum)
            self.create_test_issue(id=3, number=103, comment_count=7),  # Should pass
            self.create_test_issue(id=4, number=104, comment_count=10),  # Should pass
            self.create_test_issue(
                id=5, number=105, comment_count=0
            ),  # Should be filtered out
        ]

        filter_criteria = FilterCriteria(min_comments=5)

        # Act - This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert - Should only include issues with >=5 comments
        assert len(filtered_issues) == 3
        assert sorted([issue.number for issue in filtered_issues]) == [102, 103, 104]

        # Verify comment counts
        for issue in filtered_issues:
            assert issue.comment_count >= 5

    def test_max_comments_filter(self):
        """Test max-comments filter (<=10)."""
        # Arrange
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=3),  # Should pass
            self.create_test_issue(id=2, number=102, comment_count=8),  # Should pass
            self.create_test_issue(
                id=3, number=103, comment_count=10
            ),  # Should pass (maximum)
            self.create_test_issue(
                id=4, number=104, comment_count=15
            ),  # Should be filtered out
            self.create_test_issue(
                id=5, number=105, comment_count=20
            ),  # Should be filtered out
        ]

        filter_criteria = FilterCriteria(max_comments=10)

        # Act - This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert
        assert len(filtered_issues) == 3
        assert sorted([issue.number for issue in filtered_issues]) == [101, 102, 103]

        for issue in filtered_issues:
            assert issue.comment_count <= 10

    def test_comment_count_range_filtering(self):
        """Test comment count range filtering (min=3, max=8)."""
        # Arrange
        issues = [
            self.create_test_issue(
                id=1, number=101, comment_count=1
            ),  # Too low - filtered out
            self.create_test_issue(
                id=2, number=102, comment_count=3
            ),  # At minimum - passes
            self.create_test_issue(
                id=3, number=103, comment_count=5
            ),  # In range - passes
            self.create_test_issue(
                id=4, number=104, comment_count=8
            ),  # At maximum - passes
            self.create_test_issue(
                id=5, number=105, comment_count=12
            ),  # Too high - filtered out
            self.create_test_issue(
                id=6, number=106, comment_count=15
            ),  # Too high - filtered out
        ]

        filter_criteria = FilterCriteria(min_comments=3, max_comments=8)

        # Act - This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert
        assert len(filtered_issues) == 3
        assert sorted([issue.number for issue in filtered_issues]) == [102, 103, 104]

        for issue in filtered_issues:
            assert 3 <= issue.comment_count <= 8

    def test_edge_cases_zero_comments(self):
        """Test edge cases with zero comments."""
        # Arrange
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=0),  # Zero comments
            self.create_test_issue(id=2, number=102, comment_count=1),  # One comment
            self.create_test_issue(
                id=3, number=103, comment_count=2
            ),  # Low but non-zero
        ]

        # Test with min-comments=1 (should include those with >=1 comment)
        filter_criteria = FilterCriteria(min_comments=1)

        # Act - This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert
        assert len(filtered_issues) == 2
        assert sorted([issue.number for issue in filtered_issues]) == [102, 103]
        assert all(issue.comment_count >= 1 for issue in filtered_issues)

        # Test with min-comments=0 (should include all)
        filter_criteria = FilterCriteria(min_comments=0)
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        assert len(filtered_issues) == 3  # Should include zero-comment issue

    def test_negative_numbers_invalid(self):
        """Test negative comment counts are invalid."""
        # Arrange
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=5),
        ]

        # Act & Assert - Negative min_comments should be invalid (validated by Pydantic)
        with pytest.raises(
            ValueError
        ) as exc_info:  # Pydantic validation error for negative numbers
            FilterCriteria(min_comments=-1)
        assert "non-negative" in str(exc_info.value).lower()

        # Max comments should also reject negative numbers
        with pytest.raises(ValueError) as exc_info:
            FilterCriteria(max_comments=-5)
        assert "non-negative" in str(exc_info.value).lower()

        # Test that valid criteria work normally
        valid_criteria = FilterCriteria(min_comments=3, max_comments=10)
        filtered_issues = self.filter_engine.filter_issues(issues, valid_criteria)
        assert len(filtered_issues) == 1  # Issue with 5 comments should match

    def test_empty_issues_list_handling(self):
        """Test filtering empty issues list."""
        # Arrange
        empty_issues = []
        filter_criteria = FilterCriteria(min_comments=5)

        # Act - This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(
            empty_issues, filter_criteria
        )

        # Assert
        assert isinstance(filtered_issues, list)
        assert len(filtered_issues) == 0

    def test_all_issues_match_criteria(self):
        """Test when all issues match the criteria."""
        # Arrange - All issues have high comment counts
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=10),
            self.create_test_issue(id=2, number=102, comment_count=15),
            self.create_test_issue(id=3, number=103, comment_count=20),
        ]

        filter_criteria = FilterCriteria(min_comments=5)

        # Act
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert - All should pass
        assert len(filtered_issues) == 3
        assert sorted([issue.number for issue in filtered_issues]) == [101, 102, 103]

    def test_no_issues_match_criteria(self):
        """Test when no issues match the criteria."""
        # Arrange - All issues have low comment counts
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=1),
            self.create_test_issue(id=2, number=102, comment_count=2),
            self.create_test_issue(id=3, number=103, comment_count=3),
        ]

        filter_criteria = FilterCriteria(min_comments=5)

        # Act
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert - None should pass
        assert isinstance(filtered_issues, list)
        assert len(filtered_issues) == 0

    def test_exact_boundary_values(self):
        """Test exact boundary values for comment counts."""
        # Arrange
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=5),  # Exactly at min
            self.create_test_issue(
                id=2, number=102, comment_count=10
            ),  # Exactly at max
            self.create_test_issue(id=3, number=103, comment_count=6),  # In range
            self.create_test_issue(id=4, number=104, comment_count=4),  # Just below min
            self.create_test_issue(
                id=5, number=105, comment_count=11
            ),  # Just above max
        ]

        filter_criteria = FilterCriteria(min_comments=5, max_comments=10)

        # Act
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert
        assert len(filtered_issues) == 3
        assert sorted([issue.number for issue in filtered_issues]) == [101, 102, 103]

    def test_filter_with_limit_combined(self):
        """Test comment filtering combined with limit parameter."""
        # Arrange - Create issues with various comment counts
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=10),
            self.create_test_issue(id=2, number=102, comment_count=8),
            self.create_test_issue(id=3, number=103, comment_count=6),
            self.create_test_issue(id=4, number=104, comment_count=12),
            self.create_test_issue(id=5, number=105, comment_count=15),
        ]

        # Filter for >=6 comments but limit to 3 results
        filter_criteria = FilterCriteria(min_comments=6, limit=3)

        # Act
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert - Should get up to 3 issues (limit applied after filtering)
        assert len(filtered_issues) == 3
        for issue in filtered_issues:
            assert issue.comment_count >= 6

    def test_original_list_not_modified(self):
        """Test that filtering doesn't modify the original issues list."""
        # Arrange
        original_issues = [
            self.create_test_issue(id=1, number=101, comment_count=3),
            self.create_test_issue(id=2, number=102, comment_count=8),
            self.create_test_issue(id=3, number=103, comment_count=12),
        ]
        original_copy = [issue.copy() for issue in original_issues]

        filter_criteria = FilterCriteria(min_comments=5)

        # Act
        filtered_issues = self.filter_engine.filter_issues(
            original_issues, filter_criteria
        )

        # Assert - Original list unchanged
        assert len(original_issues) == 3
        assert original_issues[0].comment_count == original_copy[0].comment_count
        assert original_issues[1].comment_count == original_copy[1].comment_count
        assert original_issues[2].comment_count == original_copy[2].comment_count

        # But filtered result should be different
        assert len(filtered_issues) == 2
        assert all(issue.comment_count >= 5 for issue in filtered_issues)

    def test_large_numbers_performance(self):
        """Test performance with large comment counts (e.g., very active issues)."""
        # Arrange
        issues = [
            self.create_test_issue(id=1, number=101, comment_count=1000),
            self.create_test_issue(id=2, number=102, comment_count=5000),
            self.create_test_issue(id=3, number=103, comment_count=10000),
        ]

        filter_criteria = FilterCriteria(min_comments=1000)

        # Act - Should handle large numbers without overflow
        filtered_issues = self.filter_engine.filter_issues(issues, filter_criteria)

        # Assert
        assert len(filtered_issues) == 3
        assert all(issue.comment_count >= 1000 for issue in filtered_issues)
