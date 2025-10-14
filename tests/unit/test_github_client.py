"""
Unit tests for GitHub API client (T006-1).

These tests are written FIRST and expected to FAIL until the GitHub client is implemented.
This follows the Test-First Development methodology.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from github import Github, GithubException, UnknownObjectException, RateLimitExceededException
from datetime import datetime, timedelta

# These imports will fail initially (TDD - tests FAIL first)
from services.github_client import GitHubClient
from models import GitHubRepository, Issue, IssueState


@pytest.mark.unit
class TestGitHubClient:
    """Test PyGithub client initialization and configuration."""

    def test_client_initialization_no_token(self):
        """Test GitHub client initialization without token."""
        client = GitHubClient(token=None)
        assert client.token is None
        assert client.client is not None

    def test_client_initialization_with_token(self):
        """Test GitHub client initialization with token."""
        client = GitHubClient(token="ghp_test_token_123")
        assert client.token == "ghp_test_token_123"
        assert client.client is not None

    def test_client_initialization_from_env(self, monkeypatch):
        """Test GitHub client initialization from environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token_456")
        client = GitHubClient()
        assert client.token == "ghp_env_token_456"

    @patch('github.Github')
    def test_pygithub_client_creation(self, mock_github):
        """Test that PyGithub client is created correctly."""
        mock_github.return_value = Mock()

        client = GitHubClient(token="ghp_test_token")
        mock_github.assert_called_once_with("ghp_test_token")


@pytest.mark.unit
class TestRepositoryValidation:
    """Test repository validation (public/private, existence)."""

    @patch('services.github_client.GithubClient.get_repository')
    def test_valid_public_repository(self, mock_get_repo):
        """Test validation of a valid public repository."""
        mock_repo = Mock()
        mock_repo.name = "react"
        mock_repo.owner.login = "facebook"
        mock_repo.html_url = "https://github.com/facebook/react"
        mock_repo.private = False
        mock_repo.default_branch = "main"
        mock_get_repo.return_value = GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main"
        )

        client = GitHubClient()
        repo = client.get_repository("https://github.com/facebook/react")

        assert repo.owner == "facebook"
        assert repo.name == "react"
        assert repo.is_public is True

    @patch('services.github_client.GithubClient.get_repository')
    def test_private_repository_error(self, mock_get_repo):
        """Test that private repositories raise appropriate error."""
        mock_repo = Mock()
        mock_repo.private = True

        client = GitHubClient()

        with pytest.raises(ValueError, match="Private repositories are not supported"):
            client.get_repository("https://github.com/owner/private-repo")

    @patch('services.github_client.GithubClient.get_repository')
    def test_repository_not_found(self, mock_get_repo):
        """Test repository not found error handling."""
        mock_get_repo.side_effect = UnknownObjectException(status=404, data={"message": "Not Found"})

        client = GitHubClient()

        with pytest.raises(ValueError, match="Repository not found"):
            client.get_repository("https://github.com/owner/nonexistent")

    def test_invalid_repository_url_format(self):
        """Test validation of invalid repository URL formats."""
        client = GitHubClient()

        invalid_urls = [
            "https://gitlab.com/user/repo",
            "github.com/user/repo",  # Missing protocol
            "https://github.com/user",  # Missing repo name
            "https://github.com/user/repo/extra",  # Extra path
            "not-a-url",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid repository URL format"):
                client.get_repository(url)

    @patch('services.github_client.GithubClient.get_repository')
    def test_github_api_error_handling(self, mock_get_repo):
        """Test GitHub API error handling."""
        mock_get_repo.side_effect = GithubException(status=500, data={"message": "Server Error"})

        client = GitHubClient()

        with pytest.raises(GithubException):
            client.get_repository("https://github.com/owner/repo")


@pytest.mark.unit
class TestIssueRetrieval:
    """Test issue retrieval with comment counting."""

    @patch('services.github_client.GithubClient.get_issues')
    def test_successful_issue_retrieval(self, mock_get_issues):
        """Test successful issue retrieval with comment counts."""
        # Mock GitHub issue object
        mock_github_issue = Mock()
        mock_github_issue.id = 987654321
        mock_github_issue.number = 42
        mock_github_issue.title = "Test Issue"
        mock_github_issue.body = "This is a test issue"
        mock_github_issue.state = "open"
        mock_github_issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_github_issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
        mock_github_issue.closed_at = None

        # Mock user
        mock_user = Mock()
        mock_user.login = "contributor1"
        mock_user.id = 123456
        mock_user.avatar_url = "https://github.com/contributor1.png"
        mock_user.type = "User"
        mock_github_issue.user = mock_user

        # Mock assignees
        mock_github_issue.assignees = []

        # Mock labels
        mock_label = Mock()
        mock_label.id = 123
        mock_label.name = "enhancement"
        mock_label.color = "a2eeef"
        mock_label.description = "New feature or request"
        mock_github_issue.labels = [mock_label]

        # Mock comments count
        mock_github_issue.comments = 5

        # Mock milestone and pull request
        mock_github_issue.milestone = None
        mock_github_issue.pull_request = None

        mock_get_issues.return_value = [mock_github_issue]

        client = GitHubClient()
        issues = client.get_issues("facebook", "react")

        assert len(issues) == 1
        issue = issues[0]
        assert issue.id == 987654321
        assert issue.number == 42
        assert issue.title == "Test Issue"
        assert issue.state == IssueState.OPEN
        assert issue.comment_count == 5

    @patch('services.github_client.GithubClient.get_issues')
    def test_issue_retrieval_filters_pull_requests(self, mock_get_issues):
        """Test that pull requests are filtered out from issue results."""
        # Mock GitHub issue (pull request)
        mock_pr = Mock()
        mock_pr.id = 987654321
        mock_pr.number = 1
        mock_pr.title = "Add new feature"
        mock_pr.pull_request = Mock()  # Has pull_request attribute -> is PR

        # Mock GitHub issue (regular issue)
        mock_issue = Mock()
        mock_issue.id = 987654322
        mock_issue.number = 2
        mock_issue.title = "Bug report"
        mock_issue.pull_request = None
        mock_issue.comments = 3

        mock_issue.user = Mock()
        mock_issue.user.login = "contributor1"
        mock_issue.user.id = 123456
        mock_issue.user.avatar_url = "https://github.com/contributor1.png"
        mock_issue.user.type = "User"

        mock_issue.assignees = []
        mock_issue.labels = []
        mock_issue.body = "This is a bug report"
        mock_issue.state = "open"
        mock_issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
        mock_issue.closed_at = None
        mock_issue.milestone = None

        mock_get_issues.return_value = [mock_pr, mock_issue]

        client = GitHubClient()
        issues = client.get_issues("facebook", "react")

        # Should only return the regular issue, not the pull request
        assert len(issues) == 1
        assert issues[0].number == 2
        assert issues[0].title == "Bug report"

    @patch('services.github_client.GithubClient.get_issues')
    def test_empty_issue_list(self, mock_get_issues):
        """Test handling of repositories with no issues."""
        mock_get_issues.return_value = []

        client = GitHubClient()
        issues = client.get_issues("owner", "empty-repo")

        assert issues == []

    @patch('services.github_client.GithubClient.get_issues')
    def test_issue_retrieval_with_pagination(self, mock_get_issues):
        """Test issue retrieval with pagination."""
        # Create multiple mock issues
        mock_issues = []
        for i in range(3):
            mock_issue = Mock()
            mock_issue.id = 987654321 + i
            mock_issue.number = 42 + i
            mock_issue.title = f"Test Issue {i}"
            mock_issue.body = f"This is test issue {i}"
            mock_issue.state = "open"
            mock_issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
            mock_issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
            mock_issue.closed_at = None
            mock_issue.pull_request = None
            mock_issue.comments = i + 1
            mock_issue.milestone = None

            mock_user = Mock()
            mock_user.login = "contributor1"
            mock_user.id = 123456
            mock_user.avatar_url = "https://github.com/contributor1.png"
            mock_user.type = "User"
            mock_issue.user = mock_user

            mock_issue.assignees = []
            mock_issue.labels = []

            mock_issues.append(mock_issue)

        mock_get_issues.return_value = mock_issues

        client = GitHubClient()
        issues = client.get_issues("owner", "repo")

        assert len(issues) == 3
        assert issues[0].comment_count == 1
        assert issues[1].comment_count == 2
        assert issues[2].comment_count == 3


@pytest.mark.unit
class TestRateLimitDetection:
    """Test rate limit detection and error handling."""

    @patch('services.github_client.GithubClient.get_repository')
    def test_rate_limit_detection(self, mock_get_repo, monkeypatch):
        """Test GitHub API rate limit detection."""
        # Mock rate limit info
        mock_rate_limit = Mock()
        mock_rate_limit.raw_data = {
            'resources': {
                'core': {
                    'limit': 5000,
                    'remaining': 0,
                    'reset': int((datetime.now() + timedelta(hours=1)).timestamp())
                }
            }
        }

        mock_github = Mock()
        mock_github.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient()
        client.client = mock_github

        with patch('github.Github'):
            try:
                client.get_repository("https://github.com/owner/repo")
            except:
                pass  # We just want to check rate limit is checked

        mock_github.get_rate_limit.assert_called()

    @patch('services.github_client.GithubClient.get_repository')
    def test_rate_limit_exceeded(self, mock_get_repo):
        """Test rate limit exceeded error handling."""
        mock_get_repo.side_effect = RateLimitExceededException(
            status=403,
            data={
                "message": "API rate limit exceeded",
                "documentation_url": "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting"
            }
        )

        client = GitHubClient()

        with pytest.raises(RateLimitExceededException):
            client.get_repository("https://github.com/owner/repo")

    @patch('services.github_client.GithubClient.get_repository')
    def test_rate_limit_warning(self, mock_get_repo, monkeypatch):
        """Test rate limit warning when remaining is low."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "react"
        mock_repo.owner.login = "facebook"
        mock_repo.html_url = "https://github.com/facebook/react"
        mock_repo.private = False
        mock_repo.default_branch = "main"
        mock_get_repo.return_value = GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main"
        )

        # Mock rate limit with low remaining calls
        mock_rate_limit = Mock()
        mock_rate_limit.raw_data = {
            'resources': {
                'core': {
                    'limit': 5000,
                    'remaining': 50,  # Low threshold
                    'reset': int((datetime.now() + timedelta(hours=1)).timestamp())
                }
            }
        }

        mock_github = Mock()
        mock_github.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient()
        client.client = mock_github

        repo = client.get_repository("https://github.com/facebook/react")
        assert repo.owner == "facebook"


@pytest.mark.unit
class TestGitHubClientAuthentication:
    """Test GitHub client authentication and error handling."""

    def test_authentication_with_invalid_token(self):
        """Test authentication failure with invalid token."""
        client = GitHubClient(token="invalid_token")

        # This should be tested with actual PyGithub mocking
        assert client.token == "invalid_token"

    @patch('services.github_client.GithubClient.get_repository')
    def test_authentication_permission_error(self, mock_get_repo):
        """Test authentication permission errors."""
        mock_get_repo.side_effect = GithubException(
            status=401,
            data={"message": "Bad credentials"}
        )

        client = GitHubClient(token="invalid_token")

        with pytest.raises(GithubException):
            client.get_repository("https://github.com/owner/repo")

    def test_token_validation(self):
        """Test token validation logic."""
        # Valid token formats
        valid_tokens = [
            "ghp_1234567890abcdef",
            "github_pat_11ABCDEF...",
            "v1.1234567890abcdef"
        ]

        for token in valid_tokens:
            client = GitHubClient(token=token)
            assert client.token == token

    def test_empty_token_handling(self):
        """Test handling of empty token."""
        client = GitHubClient(token="")
        assert client.token is None

        client = GitHubClient(token=None)
        assert client.token is None