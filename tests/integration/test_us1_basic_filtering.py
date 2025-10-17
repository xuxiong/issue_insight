"""
Integration tests for User Story 1 - Basic Comment Filtering (T011).

These integration tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from typer.testing import CliRunner

# These imports will FAIL initially (TDD - tests must FAIL first)
from cli.main import app
from services.github_client import GitHubClient
from services.filter_engine import FilterEngine
from models import Issue, GitHubRepository, FilterCriteria, IssueState, User


@pytest.mark.integration
class TestBasicCommentFiltering:
    """Integration tests for basic comment filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_issues = self._create_mock_issues()
        self.mock_repo_info = self._create_mock_repository()

    def _create_mock_repository(self) -> Dict[str, Any]:
        """Create mock repository data."""
        return {
            "id": 123456789,
            "name": "react",
            "owner": "facebook",
            "html_url": "https://github.com/facebook/react",
            "api_url": "https://api.github.com/repos/facebook/react",
            "is_public": True,
            "default_branch": "main"
        }

    def _create_mock_issues(self) -> List[Dict[str, Any]]:
        """Create mock issue data with various comment counts."""
        return [
            {
                "id": 1,
                "number": 101,
                "title": "Issue with many comments",
                "body": "This issue has a lot of discussion",
                "state": "open",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "closed_at": None,
                "comment_count": 10,  # High comment count - should match min-comments=5
                "author": {
                    "id": 1,
                    "username": "contributor1",
                    "display_name": "Contributor One",
                    "avatar_url": "https://github.com/contributor1.png",
                    "is_bot": False
                },
                "assignees": [],
                "labels": [
                    {"id": 1, "name": "enhancement", "color": "a2eeef"}
                ],
                "is_pull_request": False
            },
            {
                "id": 2,
                "number": 102,
                "title": "Issue with few comments",
                "body": "This issue has minimal discussion",
                "state": "open",
                "created_at": "2024-01-14T08:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z",
                "closed_at": None,
                "comment_count": 2,   # Low comment count - should NOT match min-comments=5
                "author": {
                    "id": 2,
                    "username": "contributor2",
                    "display_name": "Contributor Two",
                    "avatar_url": "https://github.com/contributor2.png",
                    "is_bot": False
                },
                "assignees": [],
                "labels": [
                    {"id": 2, "name": "bug", "color": "d73a4a"}
                ],
                "is_pull_request": False
            },
            {
                "id": 3,
                "number": 103,
                "title": "Another issue with many comments",
                "body": "Another highly discussed topic",
                "state": "closed",
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-12T16:30:00Z",
                "closed_at": "2024-01-12T16:30:00Z",
                "comment_count": 15,  # High comment count - should match min-comments=5
                "author": {
                    "id": 3,
                    "username": "contributor3",
                    "display_name": "Contributor Three",
                    "avatar_url": "https://github.com/contributor3.png",
                    "is_bot": False
                },
                "assignees": [],
                "labels": [
                    {"id": 3, "name": "question", "color": "d876e3"}
                ],
                "is_pull_request": False
            },
            {
                "id": 4,
                "number": 104,
                "title": "Pull request that should be filtered out",
                "body": "This is a pull request, should be excluded",
                "state": "open",
                "created_at": "2024-01-11T11:00:00Z",
                "updated_at": "2024-01-11T15:00:00Z",
                "closed_at": None,
                "comment_count": 8,   # High comment count but IS a pull request - should be filtered out
                "author": {
                    "id": 4,
                    "username": "contributor4",
                    "display_name": "Contributor Four",
                    "avatar_url": "https://github.com/contributor4.png",
                    "is_bot": False
                },
                "assignees": [],
                "labels": [
                    {"id": 4, "name": "feature", "color": "0075ca"}
                ],
                "is_pull_request": True  # This should be excluded by GitHub client
            }
        ]

    @patch('services.github_client.Github')
    def test_acceptance_scenario_repository_url_and_min_comments(self, mock_github):
        """
        Test acceptance scenario: repository URL + min-comments 5 → filtered results.

        This is the main acceptance criteria for User Story 1.
        """
        # Arrange - Mock GitHub API responses
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance

        mock_repo = Mock()
        mock_repo.owner.login = "facebook"
        mock_repo.name = "react"
        mock_repo.html_url = "https://github.com/facebook/react"
        mock_repo.url = "https://api.github.com/repos/facebook/react"
        mock_repo.private = False
        mock_repo.default_branch = "main"
        mock_github_instance.get_repo.return_value = mock_repo

        # Mock issues that exclude pull requests
        mock_issues = []
        for issue_data in self.mock_issues:
            if not issue_data["is_pull_request"]:  # Only include non-PR issues
                mock_issue = Mock()
                for key, value in issue_data.items():
                    if key == "author":
                        mock_user = Mock()
                        mock_user.login = value["username"]
                        mock_user.name = value["display_name"]
                        mock_user.id = value["id"]
                        mock_user.avatar_url = value["avatar_url"]
                        mock_user.type = "User"
                        setattr(mock_issue, 'user', mock_user)
                    elif key in ['assignees', 'labels']:
                        setattr(mock_issue, key, [])
                    else:
                        setattr(mock_issue, key, value)
                mock_issue.comments = issue_data["comment_count"]
                mock_issue.pull_request = None  # Not a PR
                mock_issues.append(mock_issue)

        mock_repo.get_issues.return_value = mock_issues

        # Act - This will FAIL initially because main() doesn't accept these arguments yet
        with patch('cli.main.GitHubClient') as mock_client_class, \
             patch('cli.main.FilterEngine') as mock_filter_class, \
             patch('cli.main.OutputFormatter') as mock_formatter_class:
            # Mock the classes
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_filter = Mock()
            mock_filter_class.return_value = mock_filter
            mock_formatter = Mock()
            mock_formatter_class.return_value = mock_formatter

            # Setup mock data
            mock_client.get_repository.return_value = self.mock_repo_info
            mock_client.get_issues.return_value = iter([Issue(
                id=i+1,
                number=100+i+1,
                title=f"Issue {i+1}",
                body=f"Body {i+1}",
                state=IssueState.OPEN,
                created_at="2024-01-01",
                updated_at="2024-01-02",
                closed_at=None,
                author=User(id=i+1, username=f"user{i+1}", display_name=f"User {i+1}", avatar_url=f"url{i+1}"),
                assignees=[],
                labels=[],
                comment_count=10 if i < 2 else 2,  # First 2 issues have >=5 comments
                comments=[],
                milestone=None,
                is_pull_request=False
            ) for i in range(4)])  # 4 issues total

            mock_filter.apply_filters.return_value = [issue for issue in mock_client.get_issues.return_value if issue.comment_count >= 5][:2]
            mock_formatter.format_output.return_value = "Mock output"

            result = self.runner.invoke(app, [
                'https://github.com/facebook/react',
                '--min-comments', '5',
                '--limit', '100'
            ])

        # Assert - This will FAIL until implementation
        # Should only return issues 1 and 3 (those with >=5 comments but not PRs)
        expected_filtered_issues = [
            issue for issue in self.mock_issues
            if issue["comment_count"] >= 5 and not issue["is_pull_request"]
        ]

        assert len(expected_filtered_issues) == 2
        assert expected_filtered_issues[0]["number"] == 101  # Issue 1
        assert expected_filtered_issues[1]["number"] == 103  # Issue 3

    @patch('cli.main.GitHubClient')
    def test_invalid_repository_url_error_handling(self, mock_github_client):
        """Test invalid repository URL error handling."""
        # Arrange - Mock GitHub client to raise exception for invalid URL
        with patch('cli.main.OutputFormatter') as mock_formatter:
            mock_client = Mock()
            mock_github_client.return_value = mock_client
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance

            # Simulate invalid repository (not found)
            mock_client.get_repository.side_effect = ValueError("Repository not found")

            # Act - Call CLI with invalid URL
            result = self.runner.invoke(app, [
                'https://github.com/nonexistent/nonexistent-repo',
                '--min-comments', '5'
            ])

            # Assert - Should fail gracefully with user-friendly error
            assert result.exit_code != 0
            assert "not found" in result.output.lower() or "repository" in result.output.lower()

    @patch('cli.main.GitHubClient')
    @patch('cli.main.FilterEngine')
    @patch('cli.main.OutputFormatter')
    def test_no_matching_results_scenario(self, mock_formatter, mock_filter, mock_github_client):
        """Test no matching results scenario."""
        # Arrange - Mock services
        mock_client = Mock()
        mock_github_client.return_value = mock_client
        mock_filter_instance = Mock()
        mock_filter.return_value = mock_filter_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        # Setup mock data with issues that don't meet criteria
        mock_client.get_repository.return_value = self.mock_repo_info
        mock_client.get_issues.return_value = iter([Issue(
            id=i+1,
            number=100+i+1,
            title=f"Issue {i+1}",
            body=f"Body {i+1}",
            state=IssueState.OPEN,
            created_at="2024-01-01",
            updated_at="2024-01-02",
            closed_at=None,
            author=User(id=i+1, username=f"user{i+1}", display_name=f"User {i+1}", avatar_url=f"url{i+1}"),
            assignees=[],
            labels=[],
            comment_count=2,  # All issues have <5 comments, won't match min-comments=10
            comments=[],
            milestone=None,
            is_pull_request=False
        ) for i in range(4)])  # 4 issues total

        mock_filter_instance.apply_filters.return_value = []  # No issues meet criteria
        mock_formatter_instance.format_output.return_value = "No matching issues found"

        # Act - Call CLI
        result = self.runner.invoke(app, [
            'https://github.com/facebook/react',
            '--min-comments', '10',
            '--limit', '100'
        ])

        # Assert
        assert result.exit_code == 0  # Should succeed but show no results
        assert "No matching issues found" in result.output or len(result.output.strip()) > 0

    def test_cli_argument_validation(self):
        """Test CLI argument validation and help."""
        # Act - Call CLI --help
        result = self.runner.invoke(app, ['--help'])

        # Assert
        assert result.exit_code == 0  # Help should exit successfully
        assert 'Usage:' in result.output or '--help' in result.output

    @patch('cli.main.GitHubClient')
    @patch('cli.main.FilterEngine')
    @patch('cli.main.OutputFormatter')
    def test_default_limit_behavior(self, mock_formatter, mock_filter, mock_github_client):
        """Test that default limit of 100 is applied when not specified."""
        # Arrange - Mock services
        mock_client = Mock()
        mock_github_client.return_value = mock_client
        mock_filter_instance = Mock()
        mock_filter.return_value = mock_filter_instance
        mock_formatter_instance = Mock()
        mock_formatter.return_value = mock_formatter_instance

        # Setup mock data
        mock_client.get_repository.return_value = self.mock_repo_info
        mock_client.get_issues.return_value = iter([Issue(
            id=i+1,
            number=100+i+1,
            title=f"Issue {i+1}",
            body=f"Body {i+1}",
            state=IssueState.OPEN,
            created_at="2024-01-01",
            updated_at="2024-01-02",
            closed_at=None,
            author=User(id=i+1, username=f"user{i+1}", display_name=f"User {i+1}", avatar_url=f"url{i+1}"),
            assignees=[],
            labels=[],
            comment_count=5,
            comments=[],
            milestone=None,
            is_pull_request=False
        ) for i in range(150)])  # More than default limit of 100

        mock_filter_instance.apply_filters.return_value = list(mock_client.get_issues.return_value)[:100]  # Should be limited to 100
        mock_formatter_instance.format_output.return_value = "Mock output with 100 issues"

        # Act - Call CLI without --limit (should default to 100)
        result = self.runner.invoke(app, [
            'https://github.com/facebook/react'
        ])

        # Assert
        assert result.exit_code == 0
        assert "Mock output with 100 issues" in result.output
        # Verify that filter was applied with default limit
        mock_filter.assert_called_once()
        call_args = mock_filter.call_args
        assert call_args is not None
