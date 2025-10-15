"""
Contract tests for GitHub API endpoints.

These tests verify that our integration with the GitHub API conforms to the
expected contracts and handles API responses correctly.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from lib.progress import ProgressPhase
from lib.errors import ValidationError
from models import Issue, IssueState
from services.github_client import GitHubClient


class TestGitHubAPIContracts:
    """Contract tests for GitHub API integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = GitHubClient()

    @patch('services.github_client.Github')
    def test_repository_info_contract(self, mock_github):
        """Test that repository info API contract is followed."""
        # Setup mock GitHub repository response according to contract
        mock_repo = Mock()
        mock_repo.owner.login = "testowner"
        mock_repo.owner.name = "Test Owner"
        mock_repo.name = "testrepo"
        mock_repo.html_url = "https://github.com/testowner/testrepo"
        mock_repo.url = "https://api.github.com/repos/testowner/testrepo"
        mock_repo.private = False
        mock_repo.default_branch = "main"

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        result = self.client.get_repository("testowner", "testrepo")

        # Verify contract compliance
        assert result.owner == "testowner"  # Required field
        assert result.name == "testrepo"  # Required field
        assert result.url is not None  # Required field
        assert result.api_url is not None  # Required field
        assert result.default_branch is not None  # Required field

    @patch('services.github_client.Github')
    def test_issue_list_contract(self, mock_github):
        """Test that issue list API contract is followed."""
        # Create mock GitHub issue according to contract
        mock_github_issue = Mock()
        mock_github_issue.id = 123456789
        mock_github_issue.number = 42
        mock_github_issue.title = "Test Issue Title"
        mock_github_issue.body = "Test issue body content"
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

        mock_repo = Mock()
        mock_repo.get_issues.return_value = [mock_github_issue]

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        issues = list(self.client.get_issues("testowner", "testrepo"))

        # Verify contract compliance
        assert len(issues) == 1
        issue = issues[0]
        assert isinstance(issue, Issue)
        assert issue.id == 123456789  # Required field
        assert issue.number == 42  # Required field
        assert issue.title == "Test Issue Title"  # Required field
        assert issue.state == IssueState.OPEN  # Required field
        assert issue.created_at is not None  # Required field
        assert issue.updated_at is not None  # Required field
        assert issue.author is not None  # Required field
        assert issue.comment_count == 5  # Required field

    @patch('issue_finder.services.github_client.Github')
    def test_comment_list_contract(self, mock_github):
        """Test that comment list API contract is followed."""
        # Create mock GitHub comment according to contract
        mock_github_comment = Mock()
        mock_github_comment.id = 987654321
        mock_github_comment.body = "This is a test comment"
        mock_github_comment.user = Mock()
        mock_github_comment.user.login = "commenter"
        mock_github_comment.user.name = "Commenter"
        mock_github_comment.user.id = 987654321
        mock_github_comment.user.avatar_url = "https://avatars.githubusercontent.com/u/987654321?v=4"
        mock_github_comment.user.type = "User"
        mock_github_comment.created_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_github_comment.updated_at = datetime(2024, 1, 15, 11, 0, 0)

        mock_issue = Mock()
        mock_issue.get_comments.return_value = [mock_github_comment]

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        comments = self.client.get_comments("testowner", "testrepo", 42)

        # Verify contract compliance
        assert len(comments) == 1
        comment = comments[0]
        assert comment.id == 987654321  # Required field
        assert comment.body == "This is a test comment"  # Required field
        assert comment.author is not None  # Required field
        assert comment.created_at is not None  # Required field
        assert comment.issue_id == 42  # Required field

    @patch('issue_finder.services.github_client.Github')
    def test_rate_limit_contract(self, mock_github):
        """Test that rate limit handling follows contract."""
        from issue_finder.services.github_client import RateLimitExceededException

        # Setup rate limit exception with required headers
        rate_limit_exception = RateLimitExceededException()
        rate_limit_exception.headers = {
            'X-RateLimit-Limit': '5000',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(datetime.now().timestamp()) + 60)
        }

        mock_github_instance = Mock()
        mock_github_instance.get_repo.side_effect = rate_limit_exception
        mock_github.return_value = mock_github_instance

        # Test
        with pytest.raises(ValueError, match="Error fetching issues"):
            self.client.get_repository("testowner", "testrepo")

        # Note: Rate limit handling is tested through the exception mechanism
        # The actual waiting behavior would be tested in integration tests

    @patch('issue_finder.services.github_client.Github')
    def test_pull_request_exclusion_contract(self, mock_github):
        """Test that pull requests are excluded from issue analysis."""
        # Create mock GitHub issue (regular issue)
        mock_issue = Mock()
        mock_issue.id = 123456789
        mock_issue.number = 1
        mock_issue.title = "Regular Issue"
        mock_issue.pull_request = None  # Not a pull request

        # Create mock GitHub pull request
        mock_pr = Mock()
        mock_pr.id = 987654321
        mock_pr.number = 2
        mock_pr.title = "Pull Request"
        mock_pr.pull_request = Mock()  # This indicates it's a pull request

        mock_repo = Mock()
        mock_repo.get_issues.return_value = [mock_issue, mock_pr]

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        issues = list(self.client.get_issues("testowner", "testrepo"))

        # Verify contract compliance: Only issues should be returned, not PRs
        assert len(issues) == 1
        assert issues[0].title == "Regular Issue"
        assert issues[0].is_pull_request is False

    @patch('issue_finder.services.github_client.Github')
    def test_user_contract(self, mock_github):
        """Test that user information follows contract."""
        # Create mock GitHub user
        mock_github_user = Mock()
        mock_github_user.login = "testuser"
        mock_github_user.name = "Test User Display Name"
        mock_github_user.id = 123456789
        mock_github_user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
        mock_github_user.type = "User"

        # Mock issue to trigger user conversion
        mock_issue = Mock()
        mock_issue.user = mock_github_user
        mock_issue.id = 1
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.state = "open"
        mock_issue.created_at = datetime.now()
        mock_issue.updated_at = datetime.now()
        mock_issue.closed_at = None
        mock_issue.assignees = []
        mock_issue.labels = []
        mock_issue.comments = 0
        mock_issue.milestone = None
        mock_issue.pull_request = None

        mock_repo = Mock()
        mock_repo.get_issues.return_value = [mock_issue]

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        issues = list(self.client.get_issues("testowner", "testrepo"))
        user = issues[0].author

        # Verify contract compliance for user fields
        assert user.username == "testuser"  # Required field
        assert user.display_name == "Test User Display Name"  # Optional field
        assert user.id == 123456789  # Required field
        assert user.avatar_url is not None  # Required field
        assert user.is_bot is False  # Required field

    @patch('issue_finder.services.github_client.Github')
    def test_label_contract(self, mock_github):
        """Test that label information follows contract."""
        # Create mock GitHub label
        mock_label = Mock()
        mock_label.id = 987654321
        mock_label.name = "bug"
        mock_label.color = "ff0000"
        mock_label.description = "Something isn't working"

        # Mock issue with labels
        mock_issue = Mock()
        mock_issue.id = 1
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.state = "open"
        mock_issue.created_at = datetime.now()
        mock_issue.updated_at = datetime.now()
        mock_issue.closed_at = None
        mock_issue.user = Mock()
        mock_issue.user.login = "testuser"
        mock_issue.user.id = 123456789
        mock_issue.user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
        mock_issue.user.type = "User"
        mock_issue.assignees = []
        mock_issue.labels = [mock_label]
        mock_issue.comments = 0
        mock_issue.milestone = None
        mock_issue.pull_request = None

        mock_repo = Mock()
        mock_repo.get_issues.return_value = [mock_issue]

        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Test
        issues = list(self.client.get_issues("testowner", "testrepo"))
        labels = issues[0].labels

        # Verify contract compliance for label fields
        assert len(labels) == 1
        assert labels[0] == "bug"  # We store just the label name as per our model design
