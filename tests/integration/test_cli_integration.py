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
from models import (
    Issue,
    IssueState,
    User,
    Label,
    GitHubRepository,
    ActivityMetrics,
    AnalysisResult,
    FilterCriteria,
    PaginationInfo,
)

# FilterCriteria not needed for this test, removing


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI functionality and end-to-end workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_repo_url = "https://github.com/testowner/testrepo"

    def _create_mock_analysis_result(self, issues=None, min_comments=0):
        """Helper to create a mock analysis result for testing."""
        if issues is None:
            issues = []

        mock_repository = GitHubRepository(
            owner="testowner",
            name="testrepo",
            url=self.sample_repo_url,
            api_url=f"https://api.github.com/repos/testowner/testrepo",
            is_public=True,
            default_branch="main",
        )

        mock_metrics = ActivityMetrics(
            total_issues_analyzed=len(issues),
            issues_matching_filters=len(
                [i for i in issues if i.comment_count >= min_comments]
            ),
            average_comment_count=0.0,
            comment_distribution={},
            top_labels=[],
            activity_by_month={},
            activity_by_week={},
            activity_by_day={},
            most_active_users=[],
            average_issue_resolution_time=None,
        )

        mock_filter_criteria = FilterCriteria(
            min_comments=min_comments,
        )

        mock_pagination_info = PaginationInfo(page_size=100)

        return AnalysisResult(
            repository=mock_repository,
            filter_criteria=mock_filter_criteria,
            issues=issues,
            metrics=mock_metrics,
            generated_at=datetime.now(),
            processing_time_seconds=1.0,
            pagination_info=mock_pagination_info,
            progress_summary={},
            warnings=[],
            errors=[],
        )

    def test_help_command(self):
        """Test that help command works correctly."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Analyze GitHub repository issues" in result.output
        assert "find-issues" in result.output

    def test_version_command(self):
        """Test that version command works correctly."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

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
                author=User(
                    id=1,
                    username="user1",
                    display_name="User 1",
                    avatar_url="http://example.com/1.png",
                ),
                assignees=[],
                labels=[Label(id=1, name="bug", color="red")],
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
                author=User(
                    id=2,
                    username="user2",
                    display_name="User 2",
                    avatar_url="http://example.com/2.png",
                ),
                assignees=[],
                labels=[Label(id=2, name="enhancement", color="blue")],
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
                author=User(
                    id=3,
                    username="user3",
                    display_name="User 3",
                    avatar_url="http://example.com/3.png",
                ),
                assignees=[],
                labels=[Label(id=3, name="question", color="green")],
                comment_count=1,
                comments=[],
                milestone=None,
                is_pull_request=False,
            ),
        ]

        mock_result = self._create_mock_analysis_result(sample_issues, min_comments=5)

        with (
            patch("cli.main.IssueAnalyzer") as mock_analyzer_class,
            patch("utils.formatters.create_formatter") as mock_create_formatter,
        ):

            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_repository.return_value = mock_result

            # Mock formatter for output
            mock_formatter_instance = Mock()
            mock_formatter_instance.format_and_print = Mock()
            mock_create_formatter.return_value = mock_formatter_instance

            result = self.runner.invoke(
                cli, ["find-issues", "--min-comments", "5", self.sample_repo_url]
            )

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify analyzer was called correctly
            mock_analyzer.analyze_repository.assert_called_once()

    def test_invalid_repository_url(self):
        """Test handling of invalid repository URLs."""
        result = self.runner.invoke(
            cli, ["find-issues", "--min-comments", "5", "https://invalid-url"]
        )

        assert result.exit_code == 1
        assert "Invalid repository URL format" in result.output

    def test_negative_comment_count(self):
        """Test handling of negative comment count."""
        result = self.runner.invoke(
            cli, ["find-issues", "--min-comments", "-1", self.sample_repo_url]
        )

        assert result.exit_code == 1
        assert "must be non-negative" in result.output

    def test_verbose_output(self):
        """Test verbose output shows additional information."""
        mock_result = self._create_mock_analysis_result([])

        with (
            patch("cli.main.IssueAnalyzer") as mock_analyzer_class,
            patch("utils.formatters.create_formatter") as mock_create_formatter,
        ):

            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_repository.return_value = mock_result

            mock_formatter_instance = Mock()
            mock_formatter_instance.format_and_print = Mock()
            mock_create_formatter.return_value = mock_formatter_instance

            result = self.runner.invoke(
                cli,
                [
                    "find-issues",
                    "--min-comments",
                    "5",
                    "--verbose",
                    self.sample_repo_url,
                ],
            )

            assert result.exit_code == 0
            assert "🔍 Analyzing repository" in result.output

    def test_different_output_formats(self):
        """Test different output formats (CLI argument parsing)."""
        mock_result = self._create_mock_analysis_result([])

        with (
            patch("cli.main.IssueAnalyzer") as mock_analyzer_class,
            patch("utils.formatters.create_formatter") as mock_create_formatter,
        ):

            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_repository.return_value = mock_result

            mock_formatter_instance = Mock()
            mock_formatter_instance.format = Mock(return_value="JSON output")
            mock_create_formatter.return_value = mock_formatter_instance

            result = self.runner.invoke(
                cli, ["find-issues", "--format", "json", self.sample_repo_url]
            )

            assert result.exit_code == 0
            # In integration test with fully mocked analyzer, we verify CLI argument parsing success
