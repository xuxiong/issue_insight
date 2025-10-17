"""Unit tests for time period breakdown calculations."""

from datetime import datetime

import pytest

from models import Issue, IssueState, User
from services.metrics_analyzer import MetricsAnalyzer


class TestTimeBreakdowns:
    """Test time-based activity breakdowns with different granularities."""

    @pytest.fixture
    def metrics_analyzer(self):
        """Create a metrics analyzer instance for testing."""
        return MetricsAnalyzer()

    @pytest.fixture
    def sample_issues(self):
        """Create sample issues with different creation dates."""
        issues = []

        # Create issues for different time periods
        dates = [
            "2025-10-01T10:00:00",
            "2025-10-01T15:30:00",
            "2025-10-02T09:15:00",
            "2025-10-08T14:20:00",  # Same week as above (week 40)
            "2025-10-15T11:45:00",  # Different week (week 41)
            "2025-11-01T16:30:00",  # Different month
        ]

        for i, date_str in enumerate(dates):
            issues.append(
                Issue(
                    id=i + 1,
                    number=i + 1,
                    title=f"Test Issue {i + 1}",
                    body="Test body",
                    state=IssueState.OPEN,
                    created_at=datetime.fromisoformat(date_str),
                    updated_at=datetime.fromisoformat(date_str),
                    author=User(id=1, username="testuser"),
                    assignees=[],
                    labels=[],
                    comment_count=0,
                    comments=[],
                )
            )

        return issues

    def test_daily_breakdown(self, metrics_analyzer, sample_issues):
        """Test daily time breakdown functionality."""
        result = metrics_analyzer.calculate_time_breakdown(sample_issues, "daily")

        expected = {
            "2025-10-01": 2,
            "2025-10-02": 1,
            "2025-10-08": 1,
            "2025-10-15": 1,
            "2025-11-01": 1,
        }

        assert result == expected

    def test_weekly_breakdown(self, metrics_analyzer, sample_issues):
        """Test weekly time breakdown functionality."""
        result = metrics_analyzer.calculate_time_breakdown(sample_issues, "weekly")

        expected = {
            "2025-W39": 3,
            "2025-W40": 1,
            "2025-W41": 1,
            "2025-W43": 1,
        }

        assert result == expected

    def test_monthly_breakdown(self, metrics_analyzer, sample_issues):
        """Test monthly time breakdown functionality."""
        result = metrics_analyzer.calculate_time_breakdown(sample_issues, "monthly")

        expected = {
            "2025-10": 5,
            "2025-11": 1,
        }

        assert result == expected

    def test_invalid_period_defaults_to_monthly(self, metrics_analyzer, sample_issues):
        """Test that invalid period defaults to monthly."""
        result = metrics_analyzer.calculate_time_breakdown(sample_issues, "invalid")

        expected = {
            "2025-10": 5,
            "2025-11": 1,
        }

        assert result == expected

    def test_empty_issues_list(self, metrics_analyzer):
        """Test time breakdown with empty issues list."""
        result = metrics_analyzer.calculate_time_breakdown([], "daily")
        assert result == {}

    def test_calculate_metrics_includes_all_granularities(self, metrics_analyzer, sample_issues):
        """Test that calculate_metrics includes all time granularities."""
        metrics = metrics_analyzer.calculate_metrics(sample_issues)

        # Should have all three granularity fields
        assert hasattr(metrics, 'activity_by_day')
        assert hasattr(metrics, 'activity_by_week')
        assert hasattr(metrics, 'activity_by_month')

        # All should be populated
        assert len(metrics.activity_by_day) == 5
        assert len(metrics.activity_by_week) == 4
        assert len(metrics.activity_by_month) == 2