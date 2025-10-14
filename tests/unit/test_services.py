"""
Unit tests for business logic services.

These tests verify the core business logic and service components.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from issue_finder.services.github_client import GitHubClient
from issue_finder.services.filter_engine import FilterEngine
from issue_finder.services.output_formatter import OutputFormatter
from issue_finder.models.issue import Issue, IssueState
from issue_finder.models.user import User
from issue_finder.models.metrics import FilterCriteria


class TestGitHubClient:
    """Unit tests for GitHub API client service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = GitHubClient()
        self.sample_user = User(
            id=123456789,
            username="testuser",
            display_name="Test User",
            avatar_url="https://avatars.githubusercontent.com/u/123456789?v=4",
            is_bot=False,
        )

    def test_initialization_without_token(self):
        """Test client initialization without auth token."""
        client = GitHubClient()
        assert client.auth_token is None
        assert client.github is not None

    def test_initialization_with_token(self):
        """Test client initialization with auth token."""
        token = "ghp_test_token"
        client = GitHubClient(auth_token=token)
        assert client.auth_token == token
        assert client.github is not None

    @patch('issue_finder.services.github_client.Github')
    def test_get_repository_success(self, mock_github):
        """Test successful repository retrieval."""
        # Setup mock
        mock_repo = Mock()
        mock_repo.owner.login = "testowner"
        mock_repo.name = "testrepo"
        mock_repo.html_url = "https://github.com/testowner/testrepo"
        mock_repo.url = "https://api.github.com/repos/testowner/testrepo"
        mock_repo.private = False
        mock_repo.default_branch = "main"

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        client = GitHubClient()
        result = client.get_repository("testowner", "testrepo")

        # Verify
        assert result.owner == "testowner"
        assert result.name == "testrepo"
        assert result.is_public is True
        assert result.default_branch == "main"

    @patch('issue_finder.services.github_client.Github')
    def test_get_repository_not_found(self, mock_github):
        """Test repository not found error handling."""
        from issue_finder.services.github_client import UnknownObjectException

        mock_github_instance = Mock()
        mock_github_instance.get_repo.side_effect = UnknownObjectException(status=404)
        mock_github.return_value = mock_github_instance

        client = GitHubClient()

        with pytest.raises(ValueError, match="Repository not found"):
            client.get_repository("nonexistent", "repo")

    def test_convert_github_issue(self):
        """Test conversion of GitHub issue to our Issue model."""
        mock_github_issue = Mock()
        mock_github_issue.id = 123456789
        mock_github_issue.number = 42
        mock_github_issue.title = "Test Issue"
        mock_github_issue.body = "Test body"
        mock_github_issue.state = "open"
        mock_github_issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_github_issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
        mock_github_issue.closed_at = None
        mock_github_issue.user = Mock()
        mock_github_issue.user.login = "testuser"
        mock_github_issue.user.name = "Test User"
        mock_github_issue.user.id = 123456789
        mock_github_issue.user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
        mock_github_issue.user.type = "User"
        mock_github_issue.assignees = []
        mock_github_issue.labels = []
        mock_github_issue.comments = 5
        mock_github_issue.milestone = None
        mock_github_issue.pull_request = None

        result = self.client._convert_github_issue(mock_github_issue)

        assert isinstance(result, Issue)
        assert result.id == 123456789
        assert result.number == 42
        assert result.title == "Test Issue"
        assert result.state == IssueState.OPEN
        assert result.comment_count == 5
        assert result.is_pull_request is False

    def test_convert_github_issue_pull_request(self):
        """Test conversion of GitHub pull request (should be marked as PR)."""
        mock_github_issue = Mock()
        mock_github_issue.id = 123456789
        mock_github_issue.number = 42
        mock_github_issue.title = "Test PR"
        mock_github_issue.state = "open"  # Add required state
        mock_github_issue.pull_request = Mock()  # This indicates it's a pull request
        mock_github_issue.body = "Test body"
        mock_github_issue.created_at = datetime.now()
        mock_github_issue.updated_at = datetime.now()
        mock_github_issue.closed_at = None
        mock_github_issue.user = Mock()
        mock_github_issue.user.login = "testuser"
        mock_github_issue.user.name = "Test User"
        mock_github_issue.user.id = 123456789
        mock_github_issue.user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
        mock_github_issue.user.type = "User"
        mock_github_issue.assignees = []
        mock_github_issue.labels = []
        mock_github_issue.comments = 0
        mock_github_issue.milestone = None

        result = self.client._convert_github_issue(mock_github_issue)

        assert result.is_pull_request is True

    def test_convert_github_user(self):
        """Test conversion of GitHub user to our User model."""
        mock_github_user = Mock()
        mock_github_user.login = "testuser"
        mock_github_user.name = "Test User"
        mock_github_user.id = 123456789
        mock_github_user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
        mock_github_user.type = "User"

        result = self.client._convert_github_user(mock_github_user)

        assert isinstance(result, User)
        assert result.username == "testuser"
        assert result.display_name == "Test User"
        assert result.id == 123456789
        assert result.is_bot is False

    def test_convert_github_user_bot(self):
        """Test conversion of GitHub bot user."""
        mock_github_user = Mock()
        mock_github_user.login = "bot-user"
        mock_github_user.name = "Bot User"
        mock_github_user.id = 987654321
        mock_github_user.avatar_url = "https://avatars.githubusercontent.com/u/987654321?v=4"
        mock_github_user.type = "Bot"

        result = self.client._convert_github_user(mock_github_user)

        assert result.is_bot is True


class TestFilterEngine:
    """Unit tests for issue filtering engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter_engine = FilterEngine()
        self.sample_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def test_filter_issues_empty_criteria(self):
        """Test filtering with empty criteria returns all issues."""
        issues = [
            Issue(id=1, number=1, title="Issue 1", body="Body 1", state=IssueState.OPEN,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=None,
                   author=self.sample_user, assignees=[], labels=[], comment_count=5,
                   comments=[], milestone=None, is_pull_request=False),
            Issue(id=2, number=2, title="Issue 2", body="Body 2", state=IssueState.CLOSED,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=datetime.now(),
                   author=self.sample_user, assignees=[], labels=[], comment_count=2,
                   comments=[], milestone=None, is_pull_request=False),
        ]

        criteria = FilterCriteria()  # Empty criteria
        result = self.filter_engine.filter_issues(issues, criteria)

        assert len(result) == 2  # Should return all issues

    def test_filter_issues_by_min_comments(self):
        """Test filtering by minimum comment count."""
        issues = [
            Issue(id=1, number=1, title="Issue 1", body="Body 1", state=IssueState.OPEN,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=None,
                   author=self.sample_user, assignees=[], labels=[], comment_count=3,
                   comments=[], milestone=None, is_pull_request=False),
            Issue(id=2, number=2, title="Issue 2", body="Body 2", state=IssueState.CLOSED,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=datetime.now(),
                   author=self.sample_user, assignees=[], labels=[], comment_count=7,
                   comments=[], milestone=None, is_pull_request=False),
            Issue(id=3, number=3, title="Issue 3", body="Body 3", state=IssueState.OPEN,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=None,
                   author=self.sample_user, assignees=[], labels=[], comment_count=1,
                   comments=[], milestone=None, is_pull_request=False),
        ]

        criteria = FilterCriteria(min_comments=5)
        result = self.filter_engine.filter_issues(issues, criteria)

        assert len(result) == 1
        assert result[0].comment_count == 7

    def test_filter_issues_by_max_comments(self):
        """Test filtering by maximum comment count."""
        issues = [
            Issue(id=1, number=1, title="Issue 1", body="Body 1", state=IssueState.OPEN,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=None,
                   author=self.sample_user, assignees=[], labels=[], comment_count=3,
                   comments=[], milestone=None, is_pull_request=False),
            Issue(id=2, number=2, title="Issue 2", body="Body 2", state=IssueState.CLOSED,
                   created_at=datetime.now(), updated_at=datetime.now(), closed_at=datetime.now(),
                   author=self.sample_user, assignees=[], labels=[], comment_count=7,
                   comments=[], milestone=None, is_pull_request=False),
        ]

        criteria = FilterCriteria(max_comments=5)
        result = self.filter_engine.filter_issues(issues, criteria)

        assert len(result) == 1
        assert result[0].comment_count == 3


class TestOutputFormatter:
    """Unit tests for output formatting service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = OutputFormatter(format="table")

    def test_initialization(self):
        """Test formatter initialization."""
        formatter = OutputFormatter(format="json")
        assert formatter.format == "json"

    def test_format_output_table(self):
        """Test table format output."""
        issues = []
        metrics = Mock()
        metrics.total_issues_analyzed = 0
        metrics.issues_matching_filters = 0
        metrics.average_comment_count = 0
        repository_info = {"owner": "testowner", "name": "testrepo"}

        result = self.formatter.format_output(issues, metrics, repository_info)

        assert isinstance(result, str)
        assert "No issues found matching the specified criteria." in result

    def test_format_output_json(self):
        """Test JSON format output."""
        # Test that JSON format produces output without error
        # We'll test the full functionality in integration tests
        formatter = OutputFormatter(format="json")
        issues = []

        # Create a real metrics object to avoid serialization issues
        from issue_finder.models.metrics import ActivityMetrics
        metrics = ActivityMetrics(
            total_issues_analyzed=0,
            issues_matching_filters=0,
            average_comment_count=0,
            comment_distribution={},
            top_labels=[],
            activity_by_month={},
            most_active_users=[]
        )
        repository_info = {"owner": "testowner", "name": "testrepo"}

        result = formatter.format_output(issues, metrics, repository_info)

        assert isinstance(result, str)
        # Check that it's valid JSON
        import json
        parsed = json.loads(result)
        assert "repository" in parsed
        assert "issues" in parsed
        assert "metrics" in parsed

    def test_format_output_csv(self):
        """Test CSV format output."""
        formatter = OutputFormatter(format="csv")
        issues = []
        metrics = Mock()
        repository_info = {"owner": "testowner", "name": "testrepo"}

        result = formatter.format_output(issues, metrics, repository_info)

        assert isinstance(result, str)
        assert result.startswith("id,number,title,state,author")

    def test_format_output_invalid_format(self):
        """Test handling of invalid format."""
        formatter = OutputFormatter(format="invalid")
        issues = []
        metrics = Mock()
        repository_info = {"owner": "testowner", "name": "testrepo"}

        result = formatter.format_output(issues, metrics, repository_info)

        assert result == "Invalid format"