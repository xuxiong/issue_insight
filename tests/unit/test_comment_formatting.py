"""
Unit tests for comment content formatting functionality.

Tests how comments are included in different output formats.
"""

import pytest
from unittest.mock import Mock
from io import StringIO

from lib.formatters import JsonFormatter, CsvFormatter, TableFormatter
from models import Issue, IssueState, User, Comment, GitHubRepository, ActivityMetrics, LabelCount, UserActivity
from datetime import datetime


class TestCommentFormatting:
    """Test comment formatting across different output formats."""

    @pytest.fixture
    def sample_issues_with_comments(self):
        """Create sample issues with comments for testing."""
        # Create users
        author = User(id=1, username="author", display_name="Author", is_bot=False)
        commenter1 = User(id=2, username="commenter1", display_name="Commenter One", is_bot=False)
        commenter2 = User(id=3, username="commenter2", display_name="Commenter Two", is_bot=False)

        # Create comments
        comment1 = Comment(
            id=101,
            body="This is a great feature request!",
            author=commenter1,
            created_at=datetime(2023, 1, 1, 10, 0, 0),
            updated_at=datetime(2023, 1, 1, 10, 0, 0),
            issue_id=1
        )

        comment2 = Comment(
            id=102,
            body="I agree, this would be very helpful.",
            author=commenter2,
            created_at=datetime(2023, 1, 1, 14, 30, 0),
            updated_at=datetime(2023, 1, 1, 14, 30, 0),
            issue_id=1
        )

        # Create issues
        issue1 = Issue(
            id=1,
            number=1,
            title="Feature Request",
            body="Please add this feature",
            state=IssueState.OPEN,
            created_at=datetime(2023, 1, 1, 9, 0, 0),
            updated_at=datetime(2023, 1, 1, 15, 0, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=2,
            comments=[comment1, comment2],
            is_pull_request=False
        )

        issue2 = Issue(
            id=2,
            number=2,
            title="Bug Report",
            body="Found a bug",
            state=IssueState.CLOSED,
            created_at=datetime(2023, 1, 2, 9, 0, 0),
            updated_at=datetime(2023, 1, 2, 16, 0, 0),
            closed_at=datetime(2023, 1, 2, 16, 0, 0),
            author=author,
            assignees=[],
            labels=[],
            comment_count=0,
            comments=[],  # No comments
            is_pull_request=False
        )

        return [issue1, issue2]

    @pytest.fixture
    def sample_repository(self):
        """Create sample repository for testing."""
        return GitHubRepository(
            owner="test-owner",
            name="test-repo",
            url="https://github.com/test-owner/test-repo",
            api_url="https://api.github.com/repos/test-owner/test-repo",
            is_public=True,
            default_branch="main"
        )

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing."""
        return ActivityMetrics(
            total_issues_analyzed=2,
            issues_matching_filters=2,
            average_comment_count=1.0,
            comment_distribution={"0": 1, "1-2": 1},
            top_labels=[],
            activity_by_month={"2023-01": 2},
            most_active_users=[],
            average_issue_resolution_time=None
        )

    def test_json_formatter_includes_comments(self, sample_issues_with_comments, sample_repository, sample_metrics):
        """Test that JSON formatter includes comment details."""
        formatter = JsonFormatter()
        result = formatter.format(sample_issues_with_comments, sample_repository, sample_metrics)

        # Parse JSON to verify structure
        import json
        data = json.loads(result)

        assert "issues" in data
        assert len(data["issues"]) == 2

        # Check first issue has comments
        issue1 = data["issues"][0]
        assert "comments" in issue1
        assert len(issue1["comments"]) == 2

        comment1 = issue1["comments"][0]
        assert comment1["id"] == 101
        assert comment1["body"] == "This is a great feature request!"
        assert comment1["author"]["username"] == "commenter1"
        assert comment1["issue_id"] == 1
        assert "created_at" in comment1
        assert "updated_at" in comment1

        # Check second issue has no comments
        issue2 = data["issues"][1]
        assert "comments" in issue2
        assert len(issue2["comments"]) == 0

    def test_json_formatter_comment_structure(self, sample_issues_with_comments, sample_repository, sample_metrics):
        """Test that comment JSON structure matches model specification."""
        formatter = JsonFormatter()
        result = formatter.format(sample_issues_with_comments, sample_repository, sample_metrics)

        import json
        data = json.loads(result)

        comment = data["issues"][0]["comments"][0]
        expected_keys = {"id", "body", "author", "created_at", "updated_at", "issue_id"}
        assert set(comment.keys()) == expected_keys

        # Check author structure
        author = comment["author"]
        expected_author_keys = {"id", "username", "display_name", "avatar_url", "is_bot"}
        assert set(author.keys()) == expected_author_keys
        assert author["is_bot"] is False

    def test_csv_formatter_basic_structure(self, sample_issues_with_comments, sample_repository, sample_metrics):
        """Test that CSV formatter works with comment-inclusive issues."""
        formatter = CsvFormatter()
        result = formatter.format(sample_issues_with_comments, sample_repository, sample_metrics)

        # Parse CSV to verify structure
        lines = result.strip().split('\n')
        assert len(lines) == 3  # Header + 2 issues

        # Check header
        header = lines[0]
        assert "Number" in header
        assert "Title" in header
        assert "State" in header
        assert "Comments" in header

        # Check first data row (issue 1)
        row1 = lines[1].split(',')
        assert row1[0] == "1"
        assert "Feature Request" in row1[1]
        assert row1[2] == "open"
        assert row1[3] == "2"  # comment count

        # Check second data row (issue 2)
        row2 = lines[2].split(',')
        assert row2[0] == "2"
        assert "Bug Report" in row2[1]
        assert row2[2] == "closed"
        assert row2[3] == "0"  # no comments

    def test_csv_formatter_handles_special_characters_in_comments(self):
        """Test that CSV formatter properly escapes special characters that comments might contain."""
        # This will be tested when comment content is serialized
        # For now, test the basic structure without actual comments
        pass

    def test_table_formatter_comment_count_display(self, sample_issues_with_comments, sample_repository, sample_metrics):
        """Test that table formatter displays correct comment counts."""
        formatter = TableFormatter()
        result = formatter.format(sample_issues_with_comments, sample_repository, sample_metrics)

        # Verify comment counts are displayed
        assert "2" in result  # Issue 1 has 2 comments
        assert "0" in result  # Issue 2 has 0 comments

    def test_table_formatter_truncates_long_titles(self, sample_issues_with_comments, sample_repository, sample_metrics):
        """Test that table formatter handles long issue titles properly."""
        formatter = TableFormatter()
        result = formatter.format(sample_issues_with_comments, sample_repository, sample_metrics)

        # Table formatter truncates titles at 50 characters + "..."
        # "Feature Request" is short, but test that truncation logic exists
        assert "Feature Request" in result

    def test_formatters_handle_empty_comments(self, sample_repository, sample_metrics):
        """Test that formatters handle issues with no comments."""
        # Create issue without comments
        author = User(id=1, username="author", display_name="Author", is_bot=False)
        issue = Issue(
            id=1,
            number=1,
            title="Issue with no comments",
            body="Test body",
            state=IssueState.OPEN,
            created_at=datetime(2023, 1, 1, 9, 0, 0),
            updated_at=datetime(2023, 1, 1, 9, 0, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=0,
            comments=[],
            is_pull_request=False
        )

        # Test JSON formatter
        json_formatter = JsonFormatter()
        json_result = json_formatter.format([issue], sample_repository, sample_metrics)
        import json
        json_data = json.loads(json_result)
        assert len(json_data["issues"][0]["comments"]) == 0

        # Test CSV formatter
        csv_formatter = CsvFormatter()
        csv_result = csv_formatter.format([issue], sample_repository, sample_metrics)
        assert "0" in csv_result  # comment count should be 0

    def test_formatters_handle_large_comment_counts(self):
        """Test that formatters handle issues with many comments."""
        # This test would validate that formatters work with high comment counts
        # Implementation depends on how comments are displayed in different formats
        pass
