"""
Unit tests for comment aggregation functionality.

Tests the comment counting logic in the IssueAnalyzer service.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from models import Issue, Comment, User
from services.issue_analyzer import IssueAnalyzer


class TestCommentAggregation:
    """Test cases for comment aggregation logic."""

    def test_aggregate_comments_by_user_empty_issues(self):
        """Test comment aggregation with no issues."""
        analyzer = IssueAnalyzer()
        result = analyzer.aggregate_comments_by_user([])
        assert result == {}

    def test_aggregate_comments_by_user_no_comments(self):
        """Test comment aggregation when issues have no comments."""
        analyzer = IssueAnalyzer()

        # Create issues without comments
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=0,
                comments=[],
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {}

    def test_aggregate_comments_by_user_single_comment(self):
        """Test comment aggregation with a single comment."""
        analyzer = IssueAnalyzer()

        # Create a comment
        comment = Comment(
            id=1,
            body="Test comment",
            author=User(id=2, username="commenter", display_name="Commenter"),
            created_at=datetime(2024, 1, 2),
            updated_at=datetime(2024, 1, 2),
            issue_id=1,
        )

        # Create issue with comment
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=1,
                comments=[comment],
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {"commenter": 1}

    def test_aggregate_comments_by_user_multiple_comments_same_user(self):
        """Test comment aggregation with multiple comments from the same user."""
        analyzer = IssueAnalyzer()

        # Create comments from same user
        comments = [
            Comment(
                id=1,
                body="Comment 1",
                author=User(id=2, username="commenter", display_name="Commenter"),
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
                issue_id=1,
            ),
            Comment(
                id=2,
                body="Comment 2",
                author=User(id=2, username="commenter", display_name="Commenter"),
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 3),
                issue_id=1,
            ),
        ]

        # Create issue with comments
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=2,
                comments=comments,
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {"commenter": 2}

    def test_aggregate_comments_by_user_multiple_users(self):
        """Test comment aggregation with comments from multiple users."""
        analyzer = IssueAnalyzer()

        # Create comments from different users
        comments = [
            Comment(
                id=1,
                body="Comment 1",
                author=User(id=2, username="commenter1", display_name="Commenter 1"),
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
                issue_id=1,
            ),
            Comment(
                id=2,
                body="Comment 2",
                author=User(id=3, username="commenter2", display_name="Commenter 2"),
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 3),
                issue_id=1,
            ),
            Comment(
                id=3,
                body="Comment 3",
                author=User(id=2, username="commenter1", display_name="Commenter 1"),
                created_at=datetime(2024, 1, 4),
                updated_at=datetime(2024, 1, 4),
                issue_id=1,
            ),
        ]

        # Create issue with comments
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=3,
                comments=comments,
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {"commenter1": 2, "commenter2": 1}

    def test_aggregate_comments_by_user_multiple_issues(self):
        """Test comment aggregation across multiple issues."""
        analyzer = IssueAnalyzer()

        # Comments for issue 1
        comments1 = [
            Comment(
                id=1,
                body="Comment 1",
                author=User(id=2, username="commenter1", display_name="Commenter 1"),
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
                issue_id=1,
            ),
        ]

        # Comments for issue 2
        comments2 = [
            Comment(
                id=2,
                body="Comment 2",
                author=User(id=2, username="commenter1", display_name="Commenter 1"),
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 3),
                issue_id=2,
            ),
            Comment(
                id=3,
                body="Comment 3",
                author=User(id=3, username="commenter2", display_name="Commenter 2"),
                created_at=datetime(2024, 1, 4),
                updated_at=datetime(2024, 1, 4),
                issue_id=2,
            ),
        ]

        # Create issues
        issues = [
            Issue(
                id=1,
                number=1,
                title="Issue 1",
                body="Body 1",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=1,
                comments=comments1,
                is_pull_request=False,
            ),
            Issue(
                id=2,
                number=2,
                title="Issue 2",
                body="Body 2",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=2,
                comments=comments2,
                is_pull_request=False,
            ),
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {"commenter1": 2, "commenter2": 1}

    def test_aggregate_comments_by_user_deleted_user(self):
        """Test comment aggregation handles deleted users gracefully."""
        analyzer = IssueAnalyzer()

        # Create comments, one with None author (deleted user)
        comments = [
            Comment(
                id=1,
                body="Comment 1",
                author=User(id=2, username="commenter1", display_name="Commenter 1"),
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
                issue_id=1,
            ),
            Comment(
                id=2,
                body="Comment 2",
                author=None,  # Deleted user
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 3),
                issue_id=1,
            ),
        ]

        # Create issue with comments
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=2,
                comments=comments,
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        # Should only count the comment with valid author
        assert result == {"commenter1": 1}

    def test_aggregate_comments_by_user_empty_comments_list(self):
        """Test comment aggregation when comments list is empty."""
        analyzer = IssueAnalyzer()

        # Create issue with empty comments list
        issues = [
            Issue(
                id=1,
                number=1,
                title="Test Issue",
                body="Test body",
                state="open",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                author=User(id=1, username="testuser", display_name="Test User"),
                assignees=[],
                labels=[],
                comment_count=0,
                comments=[],  # Empty comments list
                is_pull_request=False,
            )
        ]

        result = analyzer.aggregate_comments_by_user(issues)
        assert result == {}