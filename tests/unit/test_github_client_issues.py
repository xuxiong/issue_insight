"""
Unit tests for GitHub client issue fetching (T012).

These tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# These imports will FAIL initially (TDD - tests must FAIL first)
from services.github_client import GitHubClient
from models import Issue, User, GitHubRepository, IssueState


@pytest.mark.unit
class TestGitHubClientIssueFetching:
    """Unit tests for GitHub client issue fetching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # This will FAIL initially - GitHubClient not fully implemented
        self.client = GitHubClient()

    def create_mock_github_issue(self, **kwargs):
        """Helper to create mock GitHub issue objects."""
        defaults = {
            'id': 123456789,
            'number': 42,
            'title': 'Test Issue',
            'body': 'Test body content',
            'state': 'open',
            'created_at': datetime(2024, 1, 15, 10, 30, 0),
            'updated_at': datetime(2024, 1, 16, 14, 20, 0),
            'closed_at': None,
            'comments': 5,
            'pull_request': None,  # Not a pull request
        }
        defaults.update(kwargs)

        mock_issue = Mock()
        for key, value in defaults.items():
            setattr(mock_issue, key, value)

        # Mock user
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_user.name = "Test User"
        mock_user.id = 123456
        mock_user.avatar_url = "https://github.com/testuser.png"
        mock_user.type = "User"
        mock_issue.user = mock_user

        # Mock empty collections
        mock_issue.assignees = []
        mock_issue.labels = []

        return mock_issue

    def test_successful_issue_retrieval_with_comment_counts(self):
        """
        Test successful issue retrieval with comment counts.

        This is a primary requirement for User Story 1 - comment count filtering.
        """
        # Arrange - Mock GitHub API
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo

            # Create mock issues with different comment counts
            mock_issues = [
                self.create_mock_github_issue(number=101, comments=10),
                self.create_mock_github_issue(number=102, comments=2),
                self.create_mock_github_issue(number=103, comments=15),
            ]

            mock_repo.get_issues.return_value = mock_issues

            # Act - This will FAIL initially
            issues = self.client.get_issues("facebook", "react", state="all")

            # Assert - Should convert GitHub issues to our Issue model
            assert len(issues) == 3

            # Check comment counts are preserved
            assert issues[0].comment_count == 10
            assert issues[1].comment_count == 2
            assert issues[2].comment_count == 15

            # Check other fields are properly converted
            for i, issue in enumerate(issues):
                assert isinstance(issue, Issue)
                assert issue.number in [101, 102, 103]
                assert isinstance(issue.author, User)
                assert issue.author.username == "testuser"
                assert issue.state == IssueState.OPEN

    def test_issue_retrieval_excludes_pull_requests(self):
        """
        Test that pull requests are excluded from issue results.

        Critical for User Story 1 - we only want issues, not PRs.
        """
        # Arrange
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo

            # Create mix of issues and pull requests
            mock_items = [
                self.create_mock_github_issue(number=101, comments=10, pull_request=None),  # Regular issue
                self.create_mock_github_issue(number=102, comments=5, pull_request=Mock()),   # Pull request
                self.create_mock_github_issue(number=103, comments=8, pull_request=None),  # Regular issue
                self.create_mock_github_issue(number=104, comments=12, pull_request=Mock()),  # Pull request
            ]

            mock_repo.get_issues.return_value = mock_items

            # Act - This will FAIL initially
            issues = self.client.get_issues("facebook", "react", state="all")

            # Assert - Should only return issues, not pull requests
            assert len(issues) == 2
            assert all(issue.number in [101, 103] for issue in issues)
            assert all(not issue.is_pull_request for issue in issues)

    def test_issue_retrieval_with_state_filtering(self):
        """Test issue retrieval with state filtering (open/closed/all)."""
        # Arrange
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo

            # Create issues with different states
            mock_issues = [
                self.create_mock_github_issue(number=101, state="open"),
                self.create_mock_github_issue(number=102, state="closed"),
                self.create_mock_github_issue(number=103, state="open"),
            ]

            mock_repo.get_issues.return_value = mock_issues

            # Act & Assert - Test different states
            # This will FAIL initially until implementation supports state filtering

            # Test "open" state
            open_issues = self.client.get_issues("facebook", "react", state="open")
            open_numbers = [issue.number for issue in open_issues]
            assert open_numbers == [101, 103]

            # Test "closed" state
            closed_issues = self.client.get_issues("facebook", "react", state="closed")
            closed_numbers = [issue.number for issue in closed_issues]
            assert closed_numbers == [102]

            # Test "all" state
            all_issues = self.client.get_issues("facebook", "react", state="all")
            all_numbers = [issue.number for issue in all_issues]
            assert sorted(all_numbers) == [101, 102, 103]

    def test_issue_model_conversion_comprehensive(self):
        """Test comprehensive Issue model conversion from GitHub objects."""
        # Arrange
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo

            # Create detailed mock issue
            mock_github_issue = Mock()
            mock_github_issue.id = 987654321
            mock_github_issue.number = 42
            mock_github_issue.title = "Comprehensive Test Issue"
            mock_github_issue.body = "This is a comprehensive test of issue conversion"
            mock_github_issue.state = "open"
            mock_github_issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
            mock_github_issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
            mock_github_issue.closed_at = None
            mock_github_issue.comments = 7
            mock_github_issue.pull_request = None
            mock_github_issue.assignees = []
            mock_github_issue.labels = []

            # Mock author
            mock_author = Mock()
            mock_author.login = "comprehensive_user"
            mock_author.name = "Comprehensive User"
            mock_author.id = 456789
            mock_author.avatar_url = "https://github.com/comprehensive_user.png"
            mock_author.type = "User"
            mock_github_issue.user = mock_author

            mock_repo.get_issues.return_value = [mock_github_issue]

            # Act - This will FAIL initially
            issues = self.client.get_issues("owner", "repo", state="all")

            # Assert - Comprehensive field mapping
            assert len(issues) == 1
            issue = issues[0]

            # Basic fields
            assert issue.id == 987654321
            assert issue.number == 42
            assert issue.title == "Comprehensive Test Issue"
            assert issue.body == "This is a comprehensive test of issue conversion"
            assert issue.state == IssueState.OPEN

            # Comment count (critical for User Story 1)
            assert issue.comment_count == 7

            # Author fields
            assert isinstance(issue.author, User)
            assert issue.author.username == "comprehensive_user"
            assert issue.author.display_name == "Comprehensive User"
            assert issue.author.id == 456789
            assert issue.author.avatar_url == "https://github.com/comprehensive_user.png"
            assert not issue.author.is_bot

            # Collections should be properly initialized
            assert isinstance(issue.assignees, list)
            assert isinstance(issue.labels, list)
            assert isinstance(issue.comments, list)

            # Pull request flag
            assert not issue.is_pull_request

            # DateTime fields should be datetime objects
            assert isinstance(issue.created_at, datetime)
            assert isinstance(issue.updated_at, datetime)
            assert issue.closed_at is None

    def test Repository_Validation_Logic(self):
        """Test repository validation logic."""
        # This test may pass as it might already be implemented
        # Testing repository validation in context of issue retrieval

        #Arrange - Mock valid repository
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.owner.login = "valid_owner"
            mock_repo.name = "valid_repo"
            mock_repo.html_url = "https://github.com/valid_owner/valid_repo"
            mock_repo.url = "https://api.github.com/repos/valid_owner/valid_repo"
            mock_repo.private = False
            mock_repo.default_branch = "main"
            mock_get_repo.return_value = mock_repo

            # Act - Should succeed
            repo = self.client.get_repository("https://github.com/valid_owner/valid_repo")

            # Assert
            assert repo.owner == "valid_owner"
            assert repo.name == "valid_repo"
            assert repo.is_public is True

    def test_API_Error_Handling(self):
        """Test GitHub API error handling during issue retrieval."""
        # Arrange - Mock API error
        from github import GithubException

        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_get_repo.side_effect = GithubException(status=403, data={"message": "API rate limit exceeded"})

            # Act & Assert - Should handle API errors gracefully
            with pytest.raises(GithubException) as exc_info:
                self.client.get_issues("owner", "repo")

            assert exc_info.value.status == 403

    def test_Rate_Limit_Error_Specifically(self):
        """Test specific rate limit error handling."""
        # Arrange - Mock rate limit exceeded
        from github import RateLimitExceededException

        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo
            mock_repo.get_issues.side_effect = RateLimitExceededException(status=403, data={"message": "Rate limit exceeded"})

            # Act & Assert - Should handle rate limit errors specifically
            with pytest.raises(RateLimitExceededException):
                self.client.get_issues("owner", "repo")

    def test_empty_issue_list_handling(self):
        """Test handling of repository with no issues."""
        # Arrange - Mock repository with no issues
        with patch.object(self.client.client, 'get_repo') as mock_get_repo:
            mock_repo = Mock()
            mock_get_repo.return_value = mock_repo
            mock_repo.get_issues.return_value = []

            # Act - Should return empty list
            issues = self.client.get_issues("owner", "repo")

            # Assert - Should return empty list without error
            assert isinstance(issues, list)
            assert len(issues) == 0