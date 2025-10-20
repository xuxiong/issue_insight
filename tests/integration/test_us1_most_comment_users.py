"""
Integration tests for User Story 1 - Display Most Active Comment Users.

Tests the complete workflow of fetching issues with comments and displaying
most active comment users.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from models import Issue, Comment, User, FilterCriteria, GitHubRepository, ActivityMetrics
from services.issue_analyzer import IssueAnalyzer


class TestMostCommentUsersIntegration:
    """Integration tests for most active comment users feature."""

    def test_most_active_comment_users_workflow(self):
        """Test the complete workflow for displaying most active comment users."""
        # Create analyzer without mocking GitHub client to avoid API calls
        analyzer = IssueAnalyzer()

        # Create test data with comments
        users = [
            User(id=1, username="alice", display_name="Alice"),
            User(id=2, username="bob", display_name="Bob"),
            User(id=3, username="charlie", display_name="Charlie"),
            User(id=4, username="diana", display_name="Diana"),
        ]

        # Create comments - Alice has most comments, then Bob, etc.
        comments = [
            # Issue 1 - Alice comments 3 times
            Comment(id=1, body="Comment 1", author=users[0], created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1), issue_id=1),
            Comment(id=2, body="Comment 2", author=users[0], created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2), issue_id=1),
            Comment(id=3, body="Comment 3", author=users[1], created_at=datetime(2024, 1, 3), updated_at=datetime(2024, 1, 3), issue_id=1),

            # Issue 2 - Bob comments 2 times, Diana comments 1 time
            Comment(id=4, body="Comment 4", author=users[1], created_at=datetime(2024, 1, 4), updated_at=datetime(2024, 1, 4), issue_id=2),
            Comment(id=5, body="Comment 5", author=users[1], created_at=datetime(2024, 1, 5), updated_at=datetime(2024, 1, 5), issue_id=2),
            Comment(id=6, body="Comment 6", author=users[3], created_at=datetime(2024, 1, 6), updated_at=datetime(2024, 1, 6), issue_id=2),

            # Issue 3 - Charlie comments 1 time, Alice comments 1 time
            Comment(id=7, body="Comment 7", author=users[2], created_at=datetime(2024, 1, 7), updated_at=datetime(2024, 1, 7), issue_id=3),
            Comment(id=8, body="Comment 8", author=users[0], created_at=datetime(2024, 1, 8), updated_at=datetime(2024, 1, 8), issue_id=3),
        ]

        # Create issues with different comment distributions
        issues = [
            Issue(
                id=1, number=1, title="Issue 1", body="Body 1",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=3, comments=comments[0:3],
                is_pull_request=False
            ),
            Issue(
                id=2, number=2, title="Issue 2", body="Body 2",
                state="open", created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2),
                author=users[1], assignees=[], labels=[], comment_count=2, comments=comments[3:6],
                is_pull_request=False
            ),
            Issue(
                id=3, number=3, title="Issue 3", body="Body 3",
                state="open", created_at=datetime(2024, 1, 3), updated_at=datetime(2024, 1, 3),
                author=users[2], assignees=[], labels=[], comment_count=2, comments=comments[6:8],
                is_pull_request=False
            ),
        ]

        # Test metrics analyzer directly
        metrics_analyzer = analyzer.metrics_analyzer
        metrics = metrics_analyzer.calculate_metrics(issues, len(issues))

        # Check most active users ranking (by comments: alice=3, bob=3, diana=1, charlie=1)
        # Bob has 3 comments total: 1 in issue 1 + 2 in issue 2 = 3 total
        # Since bob and charlie have same comment count (3 and 1), should be sorted by comment count desc, then issues created
        most_active = metrics.most_active_users
        assert len(most_active) > 0

        # Alice should be first (3 comments from issue 1 and issue 3)
        alice_user = next((u for u in most_active if u.username == "alice"), None)
        assert alice_user is not None
        assert alice_user.comments_made == 3  # 2 in issue 1 + 1 in issue 3
        assert alice_user.issues_created == 1  # She created issue 1

        # Bob should be second (3 comments: 1 in issue 1 + 2 in issue 2, 1 issue created)
        bob_user = next((u for u in most_active if u.username == "bob"), None)
        assert bob_user is not None
        assert bob_user.comments_made == 3  # 1 in issue 1 + 2 in issue 2
        assert bob_user.issues_created == 1  # He created issue 2

        # Diana and Charlie both have 1 comment each
        diana_user = next((u for u in most_active if u.username == "diana"), None)
        charlie_user = next((u for u in most_active if u.username == "charlie"), None)

        assert diana_user is not None
        assert diana_user.comments_made == 1
        assert diana_user.issues_created == 0  # She created no issues

        assert charlie_user is not None
        assert charlie_user.comments_made == 1
        assert charlie_user.issues_created == 1  # He created issue 3

        # Charlie should come before Diana in ranking due to more issues created (tiebreaker)
        diana_idx = next(i for i, u in enumerate(most_active) if u.username == "diana")
        charlie_idx = next(i for i, u in enumerate(most_active) if u.username == "charlie")
        assert charlie_idx < diana_idx  # Charlie ranks higher due to more issues created

    def test_comment_users_include_issue_creators_with_zero_comments(self):
        """Test that users who only create issues (no comments) are included with 0 comments."""
        users = [
            User(id=1, username="creator_only", display_name="Creator Only"),
            User(id=2, username="commenter", display_name="Commenter"),
        ]

        # Create comments - only commenter has comments
        comments = [
            Comment(id=1, body="Comment 1", author=users[1], created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1), issue_id=1),
        ]

        # Create issues - creator_only created an issue but made no comments
        issues = [
            Issue(
                id=1, number=1, title="Issue by creator_only", body="Body 1",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=1, comments=comments,
                is_pull_request=False
            ),
        ]

        # Create analyzer and test metrics calculation directly
        analyzer = IssueAnalyzer()
        metrics = analyzer.metrics_analyzer.calculate_metrics(issues, len(issues))

        # Check most active users
        most_active = metrics.most_active_users

        # Both users should be included
        creator_user = next((u for u in most_active if u.username == "creator_only"), None)
        commenter_user = next((u for u in most_active if u.username == "commenter"), None)

        assert creator_user is not None
        assert creator_user.comments_made == 0  # No comments made
        assert creator_user.issues_created == 1  # Created 1 issue

        assert commenter_user is not None
        assert commenter_user.comments_made == 1  # Made 1 comment
        assert commenter_user.issues_created == 0  # Created no issues

    def test_comment_aggregation_handles_missing_comments(self):
        """Test that comment aggregation works when some issues have no comments loaded."""
        users = [
            User(id=1, username="alice", display_name="Alice"),
        ]

        # Create issues - some with comments, some without comments loaded
        issues = [
            Issue(
                id=1, number=1, title="Issue with comments", body="Body 1",
                state="open", created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
                author=users[0], assignees=[], labels=[], comment_count=1,
                comments=[Comment(id=1, body="Comment", author=users[0], created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2), issue_id=1)],
                is_pull_request=False
            ),
            Issue(
                id=2, number=2, title="Issue without comments loaded", body="Body 2",
                state="open", created_at=datetime(2024, 1, 2), updated_at=datetime(2024, 1, 2),
                author=users[0], assignees=[], labels=[], comment_count=0, comments=[],  # Empty comments list
                is_pull_request=False
            ),
        ]

        # Create analyzer and test metrics calculation directly
        analyzer = IssueAnalyzer()
        metrics = analyzer.metrics_analyzer.calculate_metrics(issues, len(issues))

        # Check most active users
        most_active = metrics.most_active_users

        # Alice should be included with 1 comment and 2 issues created
        alice_user = next((u for u in most_active if u.username == "alice"), None)
        assert alice_user is not None
        assert alice_user.comments_made == 1
        assert alice_user.issues_created == 2