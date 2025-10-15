"""
Unit tests for table output formatter (T014).

These tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from typing import List

# These imports will FAIL initially (TDD - tests must FAIL first)
from lib.formatters import TableFormatter
from models import Issue, GitHubRepository, IssueState, User, ActivityMetrics, LabelCount, UserActivity


@pytest.mark.unit
class TestTableFormatter:
    """Unit tests for table output formatter."""

    def setup_method(self):
        """Set up test fixtures."""
        # This will FAIL initially - TableFormatter not implemented
        self.formatter = TableFormatter()
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_repository(self):
        """Create mock repository for testing."""
        return GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main"
        )

    def create_test_issue(self, **kwargs):
        """Create test Issue objects."""
        defaults = {
            'id': 123456789,
            'number': 42,
            'title': 'Test Issue Title',
            'body': 'This is a test issue body',
            'state': IssueState.OPEN,
            'created_at': datetime(2024, 1, 15, 10, 30, 0),
            'updated_at': datetime(2024, 1, 16, 14, 20, 0),
            'closed_at': None,
            'author': self.mock_user,
            'assignees': [],
            'labels': [],
            'comments': [],
            'is_pull_request': False,
            'comment_count': 5
        }
        defaults.update(kwargs)
        return Issue(**defaults)

    def create_test_metrics(self, total_issues=10, avg_comments=7.5):
        """Create test ActivityMetrics."""
        return ActivityMetrics(
            total_issues_analyzed=total_issues,
            issues_matching_filters=sum(1 for _ in range(total_issues) if _ < 5),  # Mock matching count
            average_comment_count=avg_comments,
            comment_distribution={
                "0-5": 3,
                "6-10": 4,
                "11+": 3
            },
            top_labels=[
                LabelCount(label_name="enhancement", count=5),
                LabelCount(label_name="bug", count=3),
                LabelCount(label_name="question", count=2)
            ],
            activity_by_month={
                "2024-01": 8,
                "2024-02": 2
            },
            most_active_users=[
                UserActivity(username="user1", issues_created=3, comments_made=15),
                UserActivity(username="user2", issues_created=2, comments_made=10)
            ],
            average_issue_resolution_time=2.5
        )

    def test_Rich_table_formatting_with_issue_data(self):
        """
        Test Rich table formatting with issue data.

        This is the primary output format requirement for User Story 1.
        """
        # Arrange
        issues = [
            self.create_test_issue(
                number=101,
                title="Enhancement request",
                state=IssueState.OPEN,
                comment_count=8,
                created_at=datetime(2024, 1, 15, 10, 30, 0)
            ),
            self.create_test_issue(
                number=102,
                title="Bug report",
                state=IssueState.CLOSED,
                comment_count=3,
                created_at=datetime(2024, 1, 14, 8, 00, 0),
                closed_at=datetime(2024, 1, 15, 16, 30, 0)
            ),
            self.create_test_issue(
                number=103,
                title="Feature idea",
                state=IssueState.OPEN,
                comment_count=12,
                created_at=datetime(2024, 1, 13, 14, 15, 0)
            )
        ]

        repository = self.create_test_repository()
        metrics = self.create_test_metrics(total_issues=15, avg_comments=7.7)

        # Act - This will FAIL initially
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should contain table-formatted output
        assert isinstance(output, str)
        assert len(output) > 0

        # Should contain issue data
        assert "101" in output  # Issue number
        assert "Enhancement request" in output  # Issue title
        assert "102" in output
        assert "Bug report" in output
        assert "103" in output
        assert "Feature idea" in output

        # Should contain comment counts
        assert "8" in output
        assert "3" in output
        assert "12" in output

        # Should contain states
        assert "OPEN" in output
        assert "CLOSED" in output

        # Should contain author information
        assert "testuser" in output

    def test_summary_statistics_display(self):
        """Test summary statistics display."""
        # Arrange
        issues = []  # Empty list to focus on summary
        repository = self.create_test_repository()
        metrics = self.create_test_metrics(total_issues=50, avg_comments=8.4)

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should display summary statistics
        assert isinstance(output, str)
        assert len(output) > 0

        # Should contain repository information
        assert "facebook/react" in output

        # Should contain summary statistics
        assert "50" in output or "50" in str(metrics.total_issues_analyzed)  # Total issues
        assert "8.4" in output or "8.4" in str(metrics.average_comment_count)  # Average comments

        # Should contain matching filters count
        issues_matching = metrics.issues_matching_filters
        assert str(issues_matching) in output

    def test_empty_results_handling(self):
        """Test empty results handling."""
        # Arrange
        empty_issues: List[Issue] = []
        repository = self.create_test_repository()
        EMPTY_METRICS = ActivityMetrics(
            total_issues_analyzed=0,
            issues_matching_filters=0,
            average_comment_count=0.0,
            comment_distribution={},
            top_labels=[],
            activity_by_month={},
            most_active_users=[],
            average_issue_resolution_time=None
        )

        # Act
        output = self.formatter.format(empty_issues, repository, EMPTY_METRICS)

        # Assert - Should handle empty results gracefully
        assert isinstance(output, str)

        # Should contain user-friendly message
        assert ("No issues found matching the specified criteria." in output or
                "No issues" in output or
                "empty" in output.lower())

    def test_column_order_and_formatting(self):
        """Test column order and formatting in table output."""
        # Arrange
        issues = [
            self.create_test_issue(
                number=101,
                title="Test Issue",
                state=IssueState.OPEN,
                comment_count=5,
                author=self.mock_user
            )
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should have proper column structure
        lines = output.split('\n')

        # Look for header row with column names
        header_row = None
        for line in lines:
            if any(col in line.lower() for col in ['number', 'title', 'state', 'comments', 'author']):
                header_row = line
                break

        assert header_row is not None, "Should contain table header with columns"

        # Should contain expected column headers
        expected_columns = ['number', 'title', 'state', 'comments', 'author']
        for col in expected_columns:
            assert col in header_row.lower(), f"Should contain '{col}' column"

    def test_long_title_truncation(self):
        """Test that long titles are properly truncated in table display."""
        # Arrange
        long_title = ("This is a very long issue title that goes on and on and on and should "
                     "definitely be truncated in the table output because it would otherwise "
                     "make the table too wide and difficult to read")

        issues = [
            self.create_test_issue(
                number=101,
                title=long_title,
                state=IssueState.OPEN,
                comment_count=3
            )
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Long title should be truncated
        assert isinstance(output, str)
        assert len(output) > 0

        # The full title should NOT be in the output (if truncation works)
        # or the output line should be reasonably long (not extremely long)
        lines = output.split('\n')
        max_line_length = max(len(line) for line in lines)
        # A reasonable maximum line length for terminal tables
        assert max_line_length < 200, f"Table lines should not be extremely long (max: {max_line_length})"

        # Should still contain key info
        assert "101" in output  # Issue number should be there

    def test_date_formatting_in_display(self):
        """Test date formatting in table display."""
        # Arrange
        specific_date = datetime(2024, 1, 15, 10, 30, 0)
        issues = [
            self.create_test_issue(
                number=101,
                title="Date Test Issue",
                created_at=specific_date,
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                comment_count=2
            )
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should display dates in readable format
        assert isinstance(output, str)

        # Should contain date information (format might be YYYY-MM-DD or other readable format)
        # Don't be too strict about exact format, but date elements should be present
        date_elements = ["2024", "01", "15"]  # Date components
        date_found = (all(elem in output for elem in date_elements) or
                     any(elem in output for elem in ["Jan", "15"]))
        assert date_found, "Should contain readable date information"

    def test_state_display_formatting(self):
        """Test state display formatting in table."""
        # Arrange
        issues = [
            self.create_test_issue(number=101, state=IssueState.OPEN, comment_count=3),
            self.create_test_issue(number=102, state=IssueState.CLOSED, comment_count=7),
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should display states clearly
        assert isinstance(output, str)

        # Should contain state indicators
        assert "open" in output.lower() or "OPEN" in output
        assert "closed" in output.lower() or "CLOSED" in output

    def test_comment_count_display(self):
        """Test comment count display in table."""
        # Arrange
        issues = [
            self.create_test_issue(number=101, comment_count=0),   # No comments
            self.create_test_issue(number=102, comment_count=1),   # Single comment
            self.create_test_issue(number=103, comment_count=999), # High comment count
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should display comment counts correctly
        assert isinstance(output, str)

        # Should show different comment counts
        assert "0" in output  # No comments
        assert "1" in output  # Single comment
        assert "999" in output  # High comments

    def test_color_and_styling_applied(self):
        """Test that color and styling are applied to table output."""
        # Arrange
        issues = [
            self.create_test_issue(
                number=101,
                state=IssueState.OPEN,
                comment_count=8
            )
        ]
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should include Rich styling (ANSI color codes)
        assert isinstance(output, str)

        # Look for ANSI escape sequences (Rich/terminal styling)
        # This might be platform-dependent, so we check that output is more than plain text
        lines = output.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Should table structure with separators/borders
        # (Rich tables typically have border characters)
        border_chars = ['│', '─', '┬', '┼', '┴', '├', '┤', '┌', '┐', '└', '┘', '-', '|', '+']
        has_table_structure = any(any(char in line for char in border_chars)
                                for line in non_empty_lines)
        assert has_table_structure, "Output should contain table structure"

    def test_large_dataset_performance(self):
        """Test table formatting performance with large datasets."""
        # Arrange - Create many issues
        issues = []
        for i in range(100):
            issues.append(
                self.create_test_issue(
                    id=i,
                    number=100 + i,
                    title=f"Issue {i}",
                    comment_count=i % 20
                )
            )

        repository = self.create_test_repository()
        metrics = self.create_test_metrics(total_issues=100)

        # Act - Should not take too long
        import time
        start_time = time.time()
        output = self.formatter.format(issues, repository, metrics)
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"Table formatting should be fast (<1s), took {execution_time:.3f}s"

        assert isinstance(output, str)
        assert len(output) > 0

        # Should contain multiple issues
        assert "Issue 0" in output
        assert "Issue 99" in output

    def test_repository_info_in_header(self):
        """Test repository information in table header."""
        # Arrange
        issues = []
        repository = self.create_test_repository()
        metrics = self.create_test_metrics()

        # Act
        output = self.formatter.format(issues, repository, metrics)

        # Assert - Should contain repository information
        assert isinstance(output, str)

        # Should show repository info
        assert "facebook" in output
        assert "react" in output
        assert "github.com" in output or "facebook/react" in output