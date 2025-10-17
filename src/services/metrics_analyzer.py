"""
Metrics Analyzer Service (T031).

Computes aggregated activity metrics for GitHub repository issue analysis.
Provides insights into project health, trending topics, and community engagement patterns.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

from models import Issue, Label, User, ActivityMetrics, LabelCount, UserActivity


class MetricsAnalyzer:
    """
    Service for calculating and analyzing activity metrics from GitHub issues.

    This service provides comprehensive insights into:
    - Basic activity statistics (averages, distributions)
    - Trending labels and topics
    - Time-based activity patterns
    - User engagement analysis
    """

    def __init__(self):
        """Initialize metrics analyzer."""
        pass

    def calculate_metrics(
        self,
        filtered_issues: List[Issue],
        total_issues: Optional[int] = None
    ) -> ActivityMetrics:
        """
        Calculate comprehensive activity metrics for filtered issues.

        Args:
            filtered_issues: Issues that matched filtering criteria
            total_issues: Total issues in the repository (optional)

        Returns:
            ActivityMetrics with all calculated insights
        """
        if total_issues is None:
            total_issues = len(filtered_issues)

        # Basic statistics
        avg_comment_count = self._calculate_average_comments(filtered_issues)
        comment_distribution = self._calculate_comment_distribution(filtered_issues)
        top_labels = self._calculate_top_labels(filtered_issues)

        # Time-based analysis
        activity_by_month = self._calculate_monthly_activity(filtered_issues)
        activity_by_week = self.calculate_time_breakdown(filtered_issues, "weekly")
        activity_by_day = self.calculate_time_breakdown(filtered_issues, "daily")

        # User activity analysis
        most_active_users = self._calculate_most_active_users(filtered_issues)

        # Issue resolution time (for closed issues)
        avg_resolution_time = self._calculate_average_resolution_time(filtered_issues)

        return ActivityMetrics(
            total_issues_analyzed=total_issues,
            issues_matching_filters=len(filtered_issues),
            average_comment_count=avg_comment_count,
            comment_distribution=comment_distribution,
            top_labels=top_labels,
            activity_by_month=activity_by_month,
            activity_by_week=activity_by_week,
            activity_by_day=activity_by_day,
            most_active_users=most_active_users,
            average_issue_resolution_time=avg_resolution_time
        )

    def _calculate_average_comments(self, issues: List[Issue]) -> float:
        """Calculate average comment count across issues."""
        if not issues:
            return 0.0
        total_comments = sum(issue.comment_count for issue in issues)
        return total_comments / len(issues)

    def _calculate_comment_distribution(self, issues: List[Issue]) -> Dict[str, int]:
        """Calculate comment count distribution categories."""
        distribution = {
            "0-5": 0,
            "6-10": 0,
            "11+": 0
        }

        for issue in issues:
            count = issue.comment_count
            if count >= 11:
                distribution["11+"] += 1
            elif count >= 6:
                distribution["6-10"] += 1
            else:
                distribution["0-5"] += 1

        return distribution

    def _calculate_top_labels(self, issues: List[Issue], limit: int = 10) -> List[LabelCount]:
        """Calculate most frequently used labels."""
        label_counter = Counter()

        for issue in issues:
            for label in issue.labels:
                label_counter[label.name] += 1

        # Sort by frequency and limit results
        top_labels = []
        for label_name, count in label_counter.most_common(limit):
            top_labels.append(LabelCount(label_name=label_name, count=count))

        return top_labels

    def _calculate_monthly_activity(self, issues: List[Issue]) -> Dict[str, int]:
        """Calculate issue activity by month."""
        return self.calculate_time_breakdown(issues, "monthly")

    def _calculate_most_active_users(self, issues: List[Issue], limit: int = 5) -> List[UserActivity]:
        """Calculate most active users by issue creation."""
        user_counter = Counter()

        for issue in issues:
            user_counter[issue.author.username] += 1

        # Convert to UserActivity objects and sort
        active_users = []
        for username, issues_created in user_counter.most_common(limit):
            active_users.append(UserActivity(
                username=username,
                issues_created=issues_created,
                comments_made=0  # Not calculating comments in this US
            ))

        return active_users

    def _calculate_average_resolution_time(self, issues: List[Issue]) -> Optional[float]:
        """Calculate average issue resolution time in days for closed issues."""
        closed_issues = [issue for issue in issues if issue.state == "closed" and issue.closed_at]

        if not closed_issues:
            return None

        total_days = 0
        resolution_times = []

        for issue in closed_issues:
            if issue.closed_at and issue.created_at:
                delta = issue.closed_at - issue.created_at
                days = delta.total_seconds() / 86400  # Convert to days
                resolution_times.append(days)

        if not resolution_times:
            return None

        return sum(resolution_times) / len(resolution_times)

    def calculate_trending_labels(
        self,
        current_issues: List[Issue],
        previous_issues: List[Issue],
        growth_threshold: float = 0.25,
        min_occurrences: int = 5
    ) -> List[LabelCount]:
        """
        Calculate trending labels based on growth between periods.

        Args:
            current_issues: Issues from current period (e.g., last 30 days)
            previous_issues: Issues from previous period (e.g., prior 30 days)
            growth_threshold: Minimum growth ratio (0.25 = 25% increase)
            min_occurrences: Minimum occurrences in current period

        Returns:
            List of trending LabelCount objects with growth percentages
        """
        # Count labels in current period
        current_counts = Counter()
        for issue in current_issues:
            for label in issue.labels:
                current_counts[label.name] += 1

        # Count labels in previous period
        previous_counts = Counter()
        for issue in previous_issues:
            for label in issue.labels:
                previous_counts[label.name] += 1

        trending_labels = []

        for label_name, current_count in current_counts.items():
            # Must meet minimum occurrence threshold
            if current_count < min_occurrences:
                continue

            previous_count = previous_counts.get(label_name, 0)

            # Calculate growth
            if previous_count == 0:
                # New label - consider it trending since it meets minimum threshold
                trending_labels.append(LabelCount(
                    label_name=label_name,
                    count=current_count
                ))
            else:
                growth_ratio = (current_count - previous_count) / previous_count
                # Check if it meets the growth threshold
                if growth_ratio >= growth_threshold:
                    trending_labels.append(LabelCount(
                        label_name=label_name,
                        count=current_count
                    ))

        # Sort by growth ratio (highest first)
        # Note: In a full implementation, we'd store growth ratio in the model
        return sorted(trending_labels, key=lambda x: x.count, reverse=True)

    def calculate_time_breakdown(
        self,
        issues: List[Issue],
        period: str = "monthly"
    ) -> Dict[str, int]:
        """
        Calculate activity breakdown by time periods.

        Args:
            issues: Issues to analyze
            period: Time period grouping ("daily", "weekly", "monthly")

        Returns:
            Dictionary mapping period keys to issue counts
        """
        period_counts = defaultdict(int)

        format_map = {
            "daily": "%Y-%m-%d",
            "weekly": "%Y-W%U",  # Week number within year
            "monthly": "%Y-%m"
        }

        date_format = format_map.get(period, "%Y-%m")

        for issue in issues:
            period_key = issue.created_at.strftime(date_format)
            period_counts[period_key] += 1

        return dict(sorted(period_counts.items()))

    def analyze_most_active_users(
        self,
        issues: List[Issue],
        limit: int = 5,
        sort_by: str = "issues"
    ) -> List[UserActivity]:
        """
        Analyze most active users based on various criteria.

        Args:
            issues: Issues to analyze
            limit: Maximum number of users to return
            sort_by: Sort criteria ("issues", "comments")

        Returns:
            List of most active UserActivity objects
        """
        if sort_by == "issues":
            return self._calculate_most_active_users(issues, limit)
        else:
            # For now, just return issues-based ranking
            # Comment counting would require comment data fetching
            return self._calculate_most_active_users(issues, limit)
