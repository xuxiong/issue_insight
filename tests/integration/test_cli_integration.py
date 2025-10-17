"""
Integration tests for CLI functionality.

These tests verify end-to-end CLI workflows and ensure the complete
application works as expected.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
from datetime import datetime

from cli.main import cli
from models import Issue, IssueState, User
# FilterCriteria not needed for this test, removing


class TestBasicCommentFiltering:
    """Integration tests for basic comment filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_repo_url = "https://github.com/testowner/testrepo"

    def test_help_command(self):
        """Test that help command works correctly."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Analyze GitHub repository issues' in result.output
        assert 'find-issues' in result.output

    def test_version_command(self):
        """Test that version command works correctly."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_basic_comment_filtering_min_comments(self):
        """Test filtering issues by minimum comment count."""
        # Mock sample issues
        sample_issues = [
            Issue(
                id=1,
                number=1,
                title="Issue with 3 comments",
                body="Test issue 1",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 2),
                closed_at=None,
                author=User(id=1, username="user1", display_name="User 1", avatar_url="http://example.com/1.png"),
                assignees=[],
                labels=["bug"],
                comment_count=3,
                comments=[],
                milestone=None,
                is_pull_request=False,
            ),
            Issue(
                id=2,
                number=2,
                title="Issue with 7 comments",
                body="Test issue 2",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 4),
                closed_at=None,
                author=User(id=2, username="user2", display_name="User 2", avatar_url="http://example.com/2.png"),
                assignees=[],
                labels=["enhancement"],
                comment_count=7,
                comments=[],
                milestone=None,
                is_pull_request=False,
            ),
            Issue(
                id=3,
                number=3,
                title="Issue with 1 comment",
                body="Test issue 3",
                state=IssueState.CLOSED,
                created_at=datetime(2024, 1, 5),
                updated_at=datetime(2024, 1, 6),
                closed_at=datetime(2024, 1, 7),
                author=User(id=3, username="user3", display_name="User 3", avatar_url="http://example.com/3.png"),
                assignees=[],
                labels=["question"],
                comment_count=1,
                comments=[],
                milestone=None,
                is_pull_request=False,
            ),
        ]

        with patch('cli.main.GitHubClient') as mock_client_class, \
             patch('cli.main.OutputFormatter') as mock_formatter:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock repository validation
            mock_client.get_repository.return_value = Mock()

            # Mock issue fetching
            mock_client.get_issues.return_value = iter(sample_issues)

            # Mock output formatter
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_output.return_value = "Mock formatted output"

            result = self.runner.invoke(cli, [
                'find-issues',
                '--min-comments', '5',
                self.sample_repo_url
            ])

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify GitHub client was called correctly
            mock_client.get_issues.assert_called_once()

    def test_invalid_repository_url(self):
        """Test handling of invalid repository URLs."""
        result = self.runner.invoke(cli, [
            'find-issues',
            '--min-comments', '5',
            'https://invalid-url'
        ])

        assert result.exit_code == 1
        assert 'Invalid repository URL format' in result.output

    def test_negative_comment_count(self):
        """Test handling of negative comment count."""
        result = self.runner.invoke(cli, [
            'find-issues',
            '--min-comments', '-1',
            self.sample_repo_url
        ])

        assert result.exit_code == 1
        assert 'must be non-negative' in result.output

    def test_verbose_output(self):
        """Test verbose output shows additional information."""
        with patch('cli.main.GitHubClient') as mock_client_class, \
             patch('cli.main.OutputFormatter') as mock_formatter:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_repository.return_value = Mock()
            mock_client.get_issues.return_value = iter([])

            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_output.return_value = ""

            result = self.runner.invoke(cli, [
                'find-issues',
                '--min-comments', '5',
                '--verbose',
                self.sample_repo_url
            ])

            assert result.exit_code == 0
            assert 'Analyzing repository:' in result.output
            assert 'Using filters:' in result.output

    def test_different_output_formats(self):
        """Test different output formats."""
        with patch('cli.main.GitHubClient') as mock_client_class, \
             patch('cli.main.OutputFormatter') as mock_formatter:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_repository.return_value = Mock()
            mock_client.get_issues.return_value = iter([])

            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_output.return_value = "JSON output"

            result = self.runner.invoke(cli, [
                'find-issues',
                '--format', 'json',
                self.sample_repo_url
            ])

            assert result.exit_code == 0
            # Verify OutputFormatter was called with correct format
            mock_formatter.assert_called_once_with(format='json')
