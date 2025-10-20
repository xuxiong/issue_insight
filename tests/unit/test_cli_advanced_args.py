"""
Unit tests for CLI argument handling for advanced filters (T023).

These tests are written FIRST and expected to FAIL until CLI enhancements
are implemented. This follows the Test-First Development methodology.
"""

import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
from datetime import datetime

# These imports will FAIL initially (TDD - tests must FAIL first)
from cli.main import cli
from models import FilterCriteria, IssueState


@pytest.mark.unit
class TestCLIBasicArguments:
    """Test CLI argument parsing for advanced filtering options."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    @patch("cli.main.IssueAnalyzer")
    def test_cli_accepts_state_argument(self, mock_analyzer):
        """Test CLI accepts --state argument."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(
            cli, ["find-issues", "https://github.com/facebook/react", "--state", "open"]
        )

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch("cli.main.IssueAnalyzer")
    def test_cli_accepts_label_arguments(self, mock_analyzer):
        """Test CLI accepts --label arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "enhancement",
            ],
        )

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch("cli.main.IssueAnalyzer")
    def test_cli_accepts_assignee_arguments(self, mock_analyzer):
        """Test CLI accepts --assignee arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--assignee",
                "user1",
                "--assignee",
                "user2",
            ],
        )

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch("cli.main.IssueAnalyzer")
    def test_cli_accepts_date_arguments(self, mock_analyzer):
        """Test CLI accepts date range arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since",
                "2024-01-01",
                "--created-until",
                "2024-12-31",
            ],
        )

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch("cli.main.IssueAnalyzer")
    def test_cli_accepts_any_all_flags(self, mock_analyzer):
        """Test CLI accepts any/all boolean flags."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--any-labels",
                "--any-assignees",
            ],
        )

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error


@pytest.mark.unit
class TestCLIArgumentValidation:
    """Test CLI argument validation and error handling."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    @patch("cli.main.IssueAnalyzer")
    def test_cli_validates_state_values(self, mock_analyzer):
        """Test CLI validates state parameter values."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        # Test valid state: open
        result = self.runner.invoke(
            cli, ["find-issues", "https://github.com/facebook/react", "--state", "open"]
        )
        # This will FAIL initially
        assert result.exit_code == 0  # Should accept open

        # Test valid state: closed
        result = self.runner.invoke(
            cli,
            ["find-issues", "https://github.com/facebook/react", "--state", "closed"],
        )
        # This will FAIL initially
        assert result.exit_code == 0  # Should accept closed

        # Test valid state: all
        result = self.runner.invoke(
            cli, ["find-issues", "https://github.com/facebook/react", "--state", "all"]
        )
        # This will FAIL initially
        assert result.exit_code == 0  # Should accept all

        # Test invalid state
        result = self.runner.invoke(
            cli,
            ["find-issues", "https://github.com/facebook/react", "--state", "invalid"],
        )
        # This will FAIL initially - should reject invalid values
        assert (
            result.exit_code == 2
        )  # Click uses exit code 2 for argument parsing errors

    @patch("cli.main.IssueAnalyzer")
    def test_cli_validates_date_formats(self, mock_analyzer):
        """Test CLI validates date format parameters."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        # Valid date formats
        valid_dates = ["2024-01-15", "2024-12-31", "2023-06-15"]

        for date_str in valid_dates:
            result = self.runner.invoke(
                cli,
                [
                    "find-issues",
                    "https://github.com/facebook/react",
                    "--created-since",
                    date_str,
                ],
            )
            # This will FAIL initially
            assert result.exit_code == 0  # Should accept valid dates

        # Invalid date formats
        invalid_dates = ["2024/01/15", "01-15-2024", "invalid-date"]

        for date_str in invalid_dates:
            result = self.runner.invoke(
                cli,
                [
                    "find-issues",
                    "https://github.com/facebook/react",
                    "--created-since",
                    date_str,
                ],
            )
            # This will FAIL initially
            assert result.exit_code == 1  # Should reject invalid dates

    @patch("cli.main.IssueAnalyzer")
    def test_cli_validates_date_ranges(self, mock_analyzer):
        """Test CLI validates logical date ranges."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        # Valid date range
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since",
                "2024-01-01",
                "--created-until",
                "2024-12-31",
            ],
        )
        # This will FAIL initially
        assert result.exit_code == 0  # Should accept valid ranges

        # Invalid date range (end before start)
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since",
                "2024-12-31",
                "--created-until",
                "2024-01-01",
            ],
        )
        # This will FAIL initially
        assert result.exit_code == 1  # Should reject invalid ranges

    @patch("cli.main.IssueAnalyzer")
    def test_cli_handles_multiple_labels(self, mock_analyzer):
        """Test CLI handles multiple label arguments."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "enhancement",
                "--label",
                "feature",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2  # Should handle multiple labels

    @patch("cli.main.IssueAnalyzer")
    def test_cli_handles_multiple_assignees(self, mock_analyzer):
        """Test CLI handles multiple assignee arguments."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--assignee",
                "alice",
                "--assignee",
                "bob",
                "--assignee",
                "charlie",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2  # Should handle multiple assignees


@pytest.mark.unit
class TestCLIFlagLogic:
    """Test CLI flag logic for any/all behavior."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    @patch("cli.main.IssueAnalyzer")
    def test_cli_default_any_behavior(self, mock_analyzer):
        """Test CLI defaults to ANY behavior when flags not specified."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "enhancement",
            ],
        )

        # This will FAIL initially - should default to any logic
        assert result.exit_code != 2

    @patch("cli.main.IssueAnalyzer")
    def test_cli_explicit_any_labels_flag(self, mock_analyzer):
        """Test explicit --any-labels flag."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "enhancement",
                "--any-labels",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2

    @patch("cli.main.IssueAnalyzer")
    def test_cli_explicit_all_labels_flag(self, mock_analyzer):
        """Test explicit --all-labels flag."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "enhancement",
                "--all-labels",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2

    @patch("cli.main.IssueAnalyzer")
    def test_cli_explicit_any_assignees_flag(self, mock_analyzer):
        """Test explicit --any-assignees flag."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--assignee",
                "alice",
                "--assignee",
                "bob",
                "--any-assignees",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2

    @patch("cli.main.IssueAnalyzer")
    def test_cli_explicit_all_assignees_flag(self, mock_analyzer):
        """Test explicit --all-assignees flag."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--assignee",
                "alice",
                "--assignee",
                "bob",
                "--all-assignees",
            ],
        )

        # This will FAIL initially
        assert result.exit_code != 2

    @patch("cli.main.IssueAnalyzer")
    def test_cli_conflicting_any_all_flags(self, mock_analyzer):
        """Test CLI handles conflicting any/all flags (should this be an error?)."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--any-labels",
                "--all-labels",
            ],
        )

        # This will FAIL initially
        # Decide: should we allow both flags? Probably last one wins, or should error
        assert result.exit_code != 2


@pytest.mark.unit
class TestCLIComplexScenarios:
    """Test complex CLI scenarios combining multiple filters."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    @patch("cli.main.IssueAnalyzer")
    def test_cli_complex_filtering_command(self, mock_analyzer):
        """Test the full complex filtering command from the spec."""
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--min-comments",
                "3",
                "--label",
                "bug",
                "--label",
                "enhancement",
                "--state",
                "open",
                "--any-labels",
                "--assignee",
                "user1",
                "--assignee",
                "user2",
                "--any-assignees",
                "--created-since",
                "2024-01-01",
                "--limit",
                "50",
            ],
        )

        # This will FAIL initially - should handle all combined arguments
        assert result.exit_code != 2  # Should not fail parsing

    @patch("cli.main.IssueAnalyzer")
    def test_cli_help_shows_new_options(self, mock_analyzer):
        """Test that --help shows the new filtering options."""
        result = self.runner.invoke(cli, ["find-issues", "--help"])

        # This will FAIL initially
        assert result.exit_code == 0
        assert "--state" in result.output
        assert "--label" in result.output
        assert "--assignee" in result.output
        assert "--created-since" in result.output
        assert "--created-until" in result.output
        assert "--updated-since" in result.output
        assert "--updated-until" in result.output
        assert "--any-labels" in result.output
        assert "--all-labels" in result.output
        assert "--any-assignees" in result.output
        assert "--all-assignees" in result.output

    @patch("cli.main.IssueAnalyzer")
    def test_cli_version_still_works(self, mock_analyzer):
        """Test that --version still works with new arguments."""
        result = self.runner.invoke(cli, ["--version"])

        # This will FAIL initially - but should remain working
        assert result.exit_code == 0
        assert "issue-analyzer" in result.output
        assert "version" in result.output


@pytest.mark.unit
class TestCLIFilterCriteriaIntegration:
    """Test that CLI arguments are correctly passed to FilterCriteria."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    @patch("cli.main.IssueAnalyzer")
    def test_cli_passes_state_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes state argument to FilterCriteria."""
        # Mock the analyzer to return a valid result
        mock_result = Mock()
        mock_result.issues = []
        mock_result.repository = Mock()
        mock_result.repository.owner = "facebook"
        mock_result.repository.name = "react"
        mock_result.metrics = Mock()
        mock_result.metrics.total_issues_analyzed = 0
        mock_result.metrics.issues_matching_filters = 0
        mock_result.metrics.average_comment_count = 0.0
        mock_result.metrics.comment_distribution = {}
        mock_result.metrics.top_labels = []
        mock_result.metrics.activity_by_month = {}
        mock_result.metrics.activity_by_week = {}
        mock_result.metrics.activity_by_day = {}
        mock_result.metrics.most_active_users = []
        mock_result.metrics.average_issue_resolution_time = 0.0
        mock_result.filter_criteria = Mock()
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(
            cli,
            ["find-issues", "https://github.com/facebook/react", "--state", "closed"],
        )

        assert result.exit_code == 0
        # Verify that IssueAnalyzer was called with correct state
        mock_analyzer_instance.analyze_repository.assert_called_once()
        call_args, call_kwargs = mock_analyzer_instance.analyze_repository.call_args
        passed_filter_criteria = call_args[
            1
        ]  # The second positional argument should be filter_criteria
        assert passed_filter_criteria.state == IssueState.CLOSED

    @patch("cli.main.IssueAnalyzer")
    def test_cli_passes_labels_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes label arguments to FilterCriteria."""
        # Mock the analyzer
        mock_result = Mock()
        mock_result.issues = []
        mock_result.repository = Mock()
        mock_result.repository.owner = "facebook"
        mock_result.repository.name = "react"
        mock_result.metrics = Mock()
        mock_result.metrics.total_issues_analyzed = 0
        mock_result.metrics.issues_matching_filters = 0
        mock_result.metrics.average_comment_count = 0.0
        mock_result.metrics.comment_distribution = {}
        mock_result.metrics.top_labels = []
        mock_result.metrics.activity_by_month = {}
        mock_result.metrics.activity_by_week = {}
        mock_result.metrics.activity_by_day = {}
        mock_result.metrics.most_active_users = []
        mock_result.metrics.average_issue_resolution_time = 0.0
        mock_result.filter_criteria = Mock()
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--label",
                "bug",
                "--label",
                "feature",
                "--any-labels",
            ],
        )

        assert result.exit_code == 0
        # Verify that IssueAnalyzer was called
        mock_analyzer_instance.analyze_repository.assert_called_once()
        # Extract the filter_criteria from the call arguments
        call_args, call_kwargs = mock_analyzer_instance.analyze_repository.call_args
        passed_filter_criteria = call_args[
            1
        ]  # The second positional argument should be filter_criteria
        assert passed_filter_criteria.labels == ["bug", "feature"]
        assert passed_filter_criteria.any_labels is True

    @patch("cli.main.IssueAnalyzer")
    def test_cli_passes_dates_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes date arguments to FilterCriteria."""
        # Mock the analyzer
        mock_result = Mock()
        mock_result.issues = []
        mock_result.repository = Mock()
        mock_result.repository.owner = "facebook"
        mock_result.repository.name = "react"
        mock_result.metrics = Mock()
        mock_result.metrics.total_issues_analyzed = 0
        mock_result.metrics.issues_matching_filters = 0
        mock_result.metrics.average_comment_count = 0.0
        mock_result.metrics.comment_distribution = {}
        mock_result.metrics.top_labels = []
        mock_result.metrics.activity_by_month = {}
        mock_result.metrics.activity_by_week = {}
        mock_result.metrics.activity_by_day = {}
        mock_result.metrics.most_active_users = []
        mock_result.metrics.average_issue_resolution_time = 0.0
        mock_result.filter_criteria = Mock()
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(
            cli,
            [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since",
                "2024-01-01",
                "--updated-until",
                "2024-12-31",
            ],
        )

        assert result.exit_code == 0
        # Verify that IssueAnalyzer was called
        mock_analyzer_instance.analyze_repository.assert_called_once()
