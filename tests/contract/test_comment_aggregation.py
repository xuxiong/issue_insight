"""
Contract tests for comment aggregation API.

Tests the contract between IssueAnalyzer and comment aggregation functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from models import Issue, Comment, User, FilterCriteria, GitHubRepository, ActivityMetrics, UserActivity
from services.issue_analyzer import IssueAnalyzer


class TestCommentAggregationContract:
    """Contract tests for comment aggregation API."""

    def test_aggregate_comments_by_user_contract(self):
        """Test the contract of aggregate_comments_by_user method."""
        analyzer = IssueAnalyzer()

        # Test with empty list
        result = analyzer.aggregate_comments_by_user([])
        assert isinstance(result, dict)
        assert result == {}

        # Test with issues that have comments
        users = [
            User(id=1, username="user1", display_name="User 1"),
            User(id=2, username="user2", display_name="User 2"),
        ]

        comments = [
            Comment(id=1, body="Comment 1", author=users[0], created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1), issue_id=1),
            Comment(id=2, body="Comment 2", author=users[1], created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2), issue_id=1),
            Comment(id=3, body="Comment 3", author=users[0], created_at=datetime(2024, 1, 3), updated_at=datetime(2024, 1, 3), issue_id=1),
        ]

        issues = [
            Issue(
                id=1, number=1, title="Test Issue", body="Test body",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=3, comments=comments,
                is_pull_request=False
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)

        # Verify contract: returns dict[str, int]
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())
        assert all(isinstance(v, int) for v in result.values())
        assert all(v >= 0 for v in result.values())

        # Verify correct aggregation
        assert result["user1"] == 2
        assert result["user2"] == 1

    def test_comment_aggregation_integration_contract(self):
        """Test the integration contract between components for comment aggregation."""
        # Create test data
        users = [
            User(id=1, username="alice", display_name="Alice"),
            User(id=2, username="bob", display_name="Bob"),
        ]

        comments = [
            Comment(id=1, body="Comment 1", author=users[0], created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1), issue_id=1),
            Comment(id=2, body="Comment 2", author=users[0], created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2), issue_id=1),
            Comment(id=3, body="Comment 3", author=users[1], created_at=datetime(2024, 1, 3), updated_at=datetime(2024, 1, 3), issue_id=1),
        ]

        issues = [
            Issue(
                id=1, number=1, title="Test Issue", body="Test body",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=3, comments=comments,
                is_pull_request=False
            )
        ]

        # Test the metrics calculation directly
        analyzer = IssueAnalyzer()
        result = analyzer.metrics_analyzer.calculate_metrics(issues, len(issues))

        # Verify metrics contract
        assert isinstance(result, ActivityMetrics)
        assert hasattr(result, 'most_active_users')
        assert isinstance(result.most_active_users, list)

        # Verify most active users contain comment data
        most_active = result.most_active_users
        assert len(most_active) > 0

        for user in most_active:
            assert hasattr(user, 'username')
            assert hasattr(user, 'issues_created')
            assert hasattr(user, 'comments_made')
            assert isinstance(user.username, str)
            assert isinstance(user.issues_created, int)
            assert isinstance(user.comments_made, int)
            assert user.issues_created >= 0
            assert user.comments_made >= 0

    def test_comment_aggregation_error_handling_contract(self):
        """Test error handling contract for comment aggregation."""
        analyzer = IssueAnalyzer()

        # Test with None input
        with pytest.raises(Exception, match="Issues list cannot be None"):
            analyzer.aggregate_comments_by_user(None)

        # Test with issues that have empty comments list (can't test None due to Pydantic validation)
        issues = [
            Issue(
                id=1, number=1, title="Test Issue", body="Test body",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[], labels=[], comment_count=0, comments=[],  # Empty comments
                is_pull_request=False
            )
        ]

        # Should not crash, should return empty dict
        result = analyzer.aggregate_comments_by_user(issues)
        assert isinstance(result, dict)
        assert result == {}

    def test_comment_aggregation_with_deleted_users_contract(self):
        """Test contract for handling deleted users in comment aggregation."""
        analyzer = IssueAnalyzer()

        users = [
            User(id=1, username="valid_user", display_name="Valid User"),
        ]

        comments = [
            Comment(id=1, body="Valid comment", author=users[0], created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1), issue_id=1),
            Comment(id=2, body="Deleted user comment", author=None, created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2), issue_id=1),
        ]

        issues = [
            Issue(
                id=1, number=1, title="Test Issue", body="Test body",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=2, comments=comments,
                is_pull_request=False
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)

        # Contract: deleted user comments should be ignored
        assert result == {"valid_user": 1}  # Only count valid user comment
