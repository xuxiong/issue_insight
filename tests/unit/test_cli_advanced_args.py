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

    @patch('cli.main.IssueAnalyzer')
    def test_cli_accepts_state_argument(self, mock_analyzer):
        """Test CLI accepts --state argument."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--state", "open"
        ])

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch('cli.main.IssueAnalyzer')
    def test_cli_accepts_label_arguments(self, mock_analyzer):
        """Test CLI accepts --label arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "enhancement"
        ])

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch('cli.main.IssueAnalyzer')
    def test_cli_accepts_assignee_arguments(self, mock_analyzer):
        """Test CLI accepts --assignee arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--assignee", "user1",
            "--assignee", "user2"
        ])

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch('cli.main.IssueAnalyzer')
    def test_cli_accepts_date_arguments(self, mock_analyzer):
        """Test CLI accepts date range arguments."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--created-since", "2024-01-01",
            "--created-until", "2024-12-31"
        ])

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error

    @patch('cli.main.IssueAnalyzer')
    def test_cli_accepts_any_all_flags(self, mock_analyzer):
        """Test CLI accepts any/all boolean flags."""
        # Configure mock to prevent actual execution
        mock_analyzer.side_effect = Exception("Should not execute")

        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--any-labels",
            "--any-assignees"
        ])

        # Should not fail during argument parsing
        assert result.exit_code != 2  # 2 = argument parsing error


@pytest.mark.unit
class TestCLIArgumentValidation:
    """Test CLI argument validation and error handling."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    def test_cli_validates_state_values(self):
        """Test CLI validates state parameter values."""
        # Valid states
        valid_states = ["open", "closed", "all"]

        for state in valid_states:
            result = self.runner.invoke(cli, [
                "find-issues",
                "https://github.com/facebook/react",
                "--state", state
            ])
            # This will FAIL initially
            assert result.exit_code != 2  # Should accept valid values

        # Invalid state
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--state", "invalid"
        ])
        # This will FAIL initially - should reject invalid values
        assert result.exit_code == 2  # 2 = argument validation error
        assert "Invalid value for '--state'" in result.output

    def test_cli_validates_date_formats(self):
        """Test CLI validates date format parameters."""
        # Valid date formats
        valid_dates = ["2024-01-15", "2024-12-31", "2023-06-15"]

        for date_str in valid_dates:
            result = self.runner.invoke(cli, [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since", date_str
            ])
            # This will FAIL initially
            assert result.exit_code != 2  # Should accept valid dates

        # Invalid date formats
        invalid_dates = ["2024/01/15", "01-15-2024", "invalid-date"]

        for date_str in invalid_dates:
            result = self.runner.invoke(cli, [
                "find-issues",
                "https://github.com/facebook/react",
                "--created-since", date_str
            ])
            # This will FAIL initially
            assert result.exit_code == 2  # Should reject invalid dates

    def test_cli_validates_date_ranges(self):
        """Test CLI validates logical date ranges."""
        # Valid date range
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--created-since", "2024-01-01",
            "--created-until", "2024-12-31"
        ])
        # This will FAIL initially
        assert result.exit_code != 2  # Should accept valid ranges

        # Invalid date range (end before start)
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--created-since", "2024-12-31",
            "--created-until", "2024-01-01"
        ])
        # This will FAIL initially
        assert result.exit_code == 2  # Should reject invalid ranges

    def test_cli_handles_multiple_labels(self):
        """Test CLI handles multiple label arguments."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "enhancement",
            "--label", "feature"
        ])

        # This will FAIL initially
        assert result.exit_code != 2  # Should handle multiple labels

    def test_cli_handles_multiple_assignees(self):
        """Test CLI handles multiple assignee arguments."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--assignee", "alice",
            "--assignee", "bob",
            "--assignee", "charlie"
        ])

        # This will FAIL initially
        assert result.exit_code != 2  # Should handle multiple assignees


@pytest.mark.unit
class TestCLIFlagLogic:
    """Test CLI flag logic for any/all behavior."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    def test_cli_default_any_behavior(self):
        """Test CLI defaults to ANY behavior when flags not specified."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "enhancement"
        ])

        # This will FAIL initially - should default to any logic
        assert result.exit_code != 2

    def test_cli_explicit_any_labels_flag(self):
        """Test explicit --any-labels flag."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "enhancement",
            "--any-labels"
        ])

        # This will FAIL initially
        assert result.exit_code != 2

    def test_cli_explicit_all_labels_flag(self):
        """Test explicit --all-labels flag."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "enhancement",
            "--all-labels"
        ])

        # This will FAIL initially
        assert result.exit_code != 2

    def test_cli_explicit_any_assignees_flag(self):
        """Test explicit --any-assignees flag."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--assignee", "alice",
            "--assignee", "bob",
            "--any-assignees"
        ])

        # This will FAIL initially
        assert result.exit_code != 2

    def test_cli_explicit_all_assignees_flag(self):
        """Test explicit --all-assignees flag."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--assignee", "alice",
            "--assignee", "bob",
            "--all-assignees"
        ])

        # This will FAIL initially
        assert result.exit_code != 2

    def test_cli_conflicting_any_all_flags(self):
        """Test CLI handles conflicting any/all flags (should this be an error?)."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--any-labels",
            "--all-labels"
        ])

        # This will FAIL initially
        # Decide: should we allow both flags? Probably last one wins, or should error
        assert result.exit_code != 2


@pytest.mark.unit
class TestCLIComplexScenarios:
    """Test complex CLI scenarios combining multiple filters."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    def test_cli_complex_filtering_command(self):
        """Test the full complex filtering command from the spec."""
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--min-comments", "3",
            "--label", "bug",
            "--label", "enhancement",
            "--state", "open",
            "--any-labels",
            "--assignee", "user1",
            "--assignee", "user2",
            "--any-assignees",
            "--created-since", "2024-01-01",
            "--limit", "50"
        ])

        # This will FAIL initially - should handle all combined arguments
        assert result.exit_code != 2  # Should not fail parsing

    def test_cli_help_shows_new_options(self):
        """Test that --help shows the new filtering options."""
        result = self.runner.invoke(cli, ["--help"])

        # This will FAIL initially
        assert result.exit_code == 0
        assert "--state" in result.output
        assert "--label" in result.output
        assert "--assignee" in result.output
        assert "--created-since" in result.output
        assert "--created-until" in result.output
        assert "--any-labels" in result.output
        assert "--all-labels" in result.output
        assert "--any-assignees" in result.output
        assert "--all-assignees" in result.output

    def test_cli_version_still_works(self):
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

    @patch('cli.main.IssueAnalyzer')
    def test_cli_passes_state_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes state argument to FilterCriteria."""
        # Configure mock to disable progress display for testing
        mock_analyzer.return_value.disable_progress_display = True
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
        mock_result.filter_criteria.min_comments = None
        mock_analyzer.return_value.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--state", "closed"
        ])

        assert result.exit_code == 0
        # Verify that analyze_repository was called with correct filter criteria
        args, kwargs = mock_analyzer.return_value.analyze_repository.call_args
        filter_criteria = args[1]  # Second argument is filter_criteria
        assert filter_criteria.state == IssueState.CLOSED

    @patch('cli.main.IssueAnalyzer')
    def test_cli_passes_labels_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes label arguments to FilterCriteria."""
        # Configure mock to disable progress display for testing
        mock_analyzer.return_value.disable_progress_display = True
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
        mock_analyzer.return_value.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--label", "bug",
            "--label", "feature",
            "--any-labels"
        ])

        assert result.exit_code == 0
        # Verify filter criteria
        args, kwargs = mock_analyzer.return_value.analyze_repository.call_args
        filter_criteria = args[1]
        assert filter_criteria.labels == ["bug", "feature"]
        assert filter_criteria.any_labels is True

    @patch('cli.main.IssueAnalyzer')
    def test_cli_passes_dates_to_filter_criteria(self, mock_analyzer):
        """Test CLI passes date arguments to FilterCriteria."""
        # Configure mock to disable progress display for testing
        mock_analyzer.return_value.disable_progress_display = True
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
        mock_analyzer.return_value.analyze_repository.return_value = mock_result

        # This will FAIL initially
        result = self.runner.invoke(cli, [
            "find-issues",
            "https://github.com/facebook/react",
            "--created-since", "2024-01-01",
            "--updated-until", "2024-12-31"
        ])

        assert result.exit_code == 0
        # Verify filter criteria
        args, kwargs = mock_analyzer.return_value.analyze_repository.call_args
        filter_criteria = args[1]
        assert filter_criteria.created_since == datetime(2024, 1, 1)
        assert filter_criteria.updated_until == datetime(2024, 12, 31)
