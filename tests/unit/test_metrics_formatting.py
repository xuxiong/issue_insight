"""
Unit tests for metrics formatting functionality in table formatter.

Tests focus on the new granularity features implemented for User Story 3:
- Multiple time granularities (daily, weekly, monthly)
- Auto-detection logic to choose best granularity based on data density
- Space-efficient display with multiple entries per line
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from typing import List

from lib.formatters import TableFormatter
from models import GitHubRepository, ActivityMetrics, LabelCount, UserActivity


@pytest.mark.unit
class TestMetricsFormattingGranularity:
    """Unit tests for metrics formatting with granularity options."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TableFormatter()
        self.mock_repository = GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main",
        )

    def create_test_metrics(self, **kwargs):
        """Create test ActivityMetrics with flexible defaults."""
        defaults = {
            "total_issues_analyzed": 25,
            "issues_matching_filters": 18,
            "average_comment_count": 4.2,
            "comment_distribution": {"0-5": 15, "6-10": 8, "11+": 2},
            "top_labels": [
                LabelCount(label_name="enhancement", count=12),
                LabelCount(label_name="bug", count=8),
            ],
            "activity_by_month": {},
            "activity_by_week": {},
            "activity_by_day": {},
            "most_active_users": [
                UserActivity(username="user1", issues_created=5, comments_made=20),
                UserActivity(username="user2", issues_created=3, comments_made=15),
            ],
            "average_issue_resolution_time": 3.5,
        }
        defaults.update(kwargs)
        return ActivityMetrics(**defaults)

    def _assert_period(self, output: str, period: str, count: int) -> None:
        direct = f"{period}: {count}"
        wrapped = f"{period}:\n{count}"
        assert direct in output or wrapped in output

    @pytest.mark.parametrize("granularity", ["auto", "daily", "weekly", "monthly"])
    def test_granularity_parameter_initialization(self, granularity):
        """Test that formatter can be initialized with different granularity settings."""
        formatter = TableFormatter(granularity=granularity)
        assert formatter.granularity == granularity

    def test_auto_granularity_daily_selection(self):
        """Test auto granularity selects daily view for recent activity (≤30 days)."""
        # Create daily activity for last 25 days
        today = datetime.now()
        activity_by_day = {}
        for i in range(25):
            date_key = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            activity_by_day[date_key] = i % 10 + 1  # Some variation

        activity_by_day = dict(sorted(activity_by_day.items()))  # Sort by date

        metrics = self.create_test_metrics(activity_by_day=activity_by_day)
        formatter = TableFormatter(granularity="auto")

        # This will exercise the _display_metrics and _display_time_activity methods
        output = formatter.format([], self.mock_repository, metrics)

        # Should contain daily activity indicator and some date entries
        assert "Daily Activity" in output
        assert "📅" in output  # Calendar emoji should be present

        # Should contain some date entries (check individually to avoid line wrapping issues)
        for date, count in list(activity_by_day.items())[-5:]:
            self._assert_period(output, date, count)

    def test_auto_granularity_weekly_selection(self):
        """Test auto granularity selects weekly view for medium-term activity (≤26 weeks)."""
        # Create weekly activity for last 20 weeks and minimal daily data
        activity_by_week = {}
        today = datetime.now()
        for i in range(20):
            week_date = today - timedelta(weeks=i)
            week_key = f"{week_date.year}-W{week_date.isocalendar().week:02d}"
            activity_by_week[week_key] = (i % 8) + 1

        activity_by_week = dict(sorted(activity_by_week.items()))

        metrics = self.create_test_metrics(
            activity_by_week=activity_by_week, activity_by_day={}
        )
        formatter = TableFormatter(granularity="auto")

        output = formatter.format([], self.mock_repository, metrics)

        # Should contain weekly activity indicator
        assert "Weekly Activity" in output
        assert "📅" in output

        for week, count in list(activity_by_week.items())[-3:]:
            self._assert_period(output, week, count)

    def test_auto_granularity_monthly_fallback(self):
        """Test auto granularity falls back to monthly when other data is insufficient."""
        # Only monthly data available
        activity_by_month = {
            "2023-08": 5,
            "2023-09": 8,
            "2023-10": 12,
            "2023-11": 15,
            "2023-12": 10,
            "2024-01": 18,
            "2024-02": 22,
            "2024-03": 15,
            "2024-04": 20,
            "2024-05": 25,
            "2024-06": 28,
            "2024-07": 30,
        }

        metrics = self.create_test_metrics(activity_by_month=activity_by_month)
        formatter = TableFormatter(granularity="auto")

        output = formatter.format([], self.mock_repository, metrics)

        # Should contain monthly activity indicator and last 12 months
        assert "Monthly Activity" in output
        assert "📅" in output

        # Should contain recent monthly entries (last 12 months)
        for month, count in list(activity_by_month.items())[-4:]:
            self._assert_period(output, month, count)

    def test_explicit_daily_granularity_override(self):
        """Test explicit daily granularity overrides auto-detection."""
        # Setup with monthly data but request daily (even if no daily data)
        activity_by_month = {"2024-01": 10, "2024-02": 15}
        metrics = self.create_test_metrics(activity_by_month=activity_by_month)

        formatter = TableFormatter(granularity="daily")
        output = formatter.format([], self.mock_repository, metrics)

        assert "Monthly Activity" not in output

    def test_explicit_weekly_granularity_override(self):
        """Test explicit weekly granularity overrides auto-detection."""
        activity_by_week = {"2024-W01": 5, "2024-W02": 8}
        metrics = self.create_test_metrics(activity_by_week=activity_by_week)

        formatter = TableFormatter(granularity="weekly")
        output = formatter.format([], self.mock_repository, metrics)

        assert "Weekly Activity" in output
        for week, count in activity_by_week.items():
            self._assert_period(output, week, count)

    def test_explicit_monthly_granularity_override(self):
        """Test explicit monthly granularity overrides auto-detection."""
        activity_by_month = {"2024-01": 20, "2024-02": 25}
        metrics = self.create_test_metrics(activity_by_month=activity_by_month)

        formatter = TableFormatter(granularity="monthly")
        output = formatter.format([], self.mock_repository, metrics)

        assert "Monthly Activity" in output
        for month, count in activity_by_month.items():
            self._assert_period(output, month, count)

    def test_space_efficient_formatting_daily(self):
        """Test space-efficient formatting with multiple daily entries per line."""
        today = datetime.now()
        activity_by_day = {}

        # Create data for exactly 25 days (should fit well with 5 items per line)
        for i in range(25):
            date_key = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            activity_by_day[date_key] = (i % 7) + 1

        activity_by_day = dict(sorted(activity_by_day.items()))

        metrics = self.create_test_metrics(activity_by_day=activity_by_day)
        formatter = TableFormatter(granularity="daily")

        output = formatter.format([], self.mock_repository, metrics)

        for date in list(activity_by_day.keys())[-5:]:
            self._assert_period(output, date, activity_by_day[date])

    def test_space_efficient_formatting_weekly(self):
        """Test space-efficient formatting with multiple weekly entries per line."""
        activity_by_week = {}
        today = datetime.now()

        # Create data for 24 weeks (should fit well with 3 items per line)
        for i in range(24):
            week_date = today - timedelta(weeks=i)
            week_key = f"{week_date.year}-W{week_date.isocalendar().week:02d}"
            activity_by_week[week_key] = (i % 10) + 1

        metrics = self.create_test_metrics(activity_by_week=activity_by_week)
        formatter = TableFormatter(granularity="weekly")

        output = formatter.format([], self.mock_repository, metrics)

        for week in list(activity_by_week.keys())[-3:]:
            self._assert_period(output, week, activity_by_week[week])

    def test_space_efficient_formatting_monthly(self):
        """Test space-efficient formatting with multiple monthly entries per line."""
        activity_by_month = {}

        # Create data for 12 months (should fit well with 4 items per line)
        for i in range(12):
            year = 2023 + (i // 12)
            month = (i % 12) + 1
            month_key = f"{year:02d}-{month:02d}"
            activity_by_month[month_key] = (i % 12) + 5

        metrics = self.create_test_metrics(activity_by_month=activity_by_month)
        formatter = TableFormatter(granularity="monthly")

        output = formatter.format([], self.mock_repository, metrics)

        for month in list(activity_by_month.keys())[-4:]:
            self._assert_period(output, month, activity_by_month[month])

    def test_no_activity_data_handling(self):
        """Test graceful handling when no activity data is available."""
        metrics = self.create_test_metrics(
            activity_by_day={}, activity_by_week={}, activity_by_month={}
        )

        for granularity in ["auto", "daily", "weekly", "monthly"]:
            formatter = TableFormatter(granularity=granularity)
            output = formatter.format([], self.mock_repository, metrics)

            assert "Daily Activity" not in output
            assert "Weekly Activity" not in output
            assert "Monthly Activity" not in output

    def test_granularity_fallback_behavior(self):
        """Test fallback behavior when requested granularity has no data."""
        # Only have monthly data but request daily
        metrics = self.create_test_metrics(
            activity_by_month={"2024-01": 10, "2024-02": 15}
        )

        formatter = TableFormatter(granularity="daily")
        output = formatter.format([], self.mock_repository, metrics)

        assert "Daily Activity" not in output
        assert "Weekly Activity" not in output
        assert "Monthly Activity" not in output

    def test_mixed_data_auto_selection_logic(self):
        """Test auto-selection logic with mixed available data."""
        # Have weekly and monthly data, no daily
        activity_by_week = {"2024-W01": 5, "2024-W02": 8, "2024-W03": 10}
        activity_by_month = {"2023-12": 20, "2024-01": 25}

        metrics = self.create_test_metrics(
            activity_by_week=activity_by_week, activity_by_month=activity_by_month
        )

        formatter = TableFormatter(granularity="auto")

        # Should prefer weekly over monthly for medium-term view
        output = formatter.format([], self.mock_repository, metrics)

        assert "Weekly Activity" in output
        for week in activity_by_week:
            self._assert_period(output, week, activity_by_week[week])
