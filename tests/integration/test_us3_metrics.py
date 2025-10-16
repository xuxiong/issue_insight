"""
Integration tests for User Story 3 - Activity Metrics and Trends (T026).

These tests are written FIRST and expected to FAIL until the metrics calculation
and analysis functionality is implemented. This follows the Test-First Development methodology.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# These imports will FAIL initially (TDD - tests must FAIL first)
from services.metrics_analyzer import MetricsAnalyzer
from models import Issue, User, Label, ActivityMetrics


@pytest.mark.integration
class TestMetricsCalculationIntegration:
    """Integration tests for metrics calculation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # This will FAIL initially - MetricsAnalyzer doesn't exist yet
        self.metrics_analyzer = MetricsAnalyzer()

        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_issue(self, **kwargs):
        """Helper to create test Issue objects."""
        defaults = {
            'id': 1,
            'number': 101,
            'title': 'Test Issue',
            'body': 'Test body',
            'state': 'open',
            'created_at': datetime(2024, 1, 15, 10, 30, 0),
            'updated_at': datetime(2024, 1, 16, 14, 20, 0),
            'closed_at': None,
            'author': self.mock_user,
            'assignees': [],
            'labels': [],
            'comment_count': 5,
            'is_pull_request': False
        }
        defaults.update(kwargs)
        return Issue(**defaults)

    def test_calculate_basic_metrics(self):
        """Test basic metrics calculation with a set of filtered issues."""
        # Create sample issues with varying comment counts and labels
        issues = [
            self.create_test_issue(id=101, number=101, comment_count=2, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=102, number=102, comment_count=5, labels=[Label(id=2, name="enhancement", color="00ff00", description="Enhancement")]),
            self.create_test_issue(id=103, number=103, comment_count=8, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report"), Label(id=2, name="enhancement", color="00ff00", description="Enhancement")]),
            self.create_test_issue(id=104, number=104, comment_count=1, labels=[]),
            self.create_test_issue(id=105, number=105, comment_count=12, labels=[Label(id=3, name="documentation", color="0000ff", description="Documentation")]),
        ]

        # This will FAIL initially - MetricsAnalyzer not implemented
        metrics = self.metrics_analyzer.calculate_metrics(issues)

        # Verify basic metrics
        assert isinstance(metrics, ActivityMetrics)
        assert metrics.total_issues_analyzed == 5
        assert metrics.issues_matching_filters == 5

        # Verify average calculation (2+5+8+1+12)/5 = 5.6
        assert abs(metrics.average_comment_count - 5.6) < 0.01

    def test_trending_labels_calculation(self):
        """Test trending labels algorithm calculation."""
        # Create issues with labels showing growth trend
        # Current period (recent issues)
        current_issues = [
            self.create_test_issue(id=101, number=101, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=102, number=102, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=103, number=103, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=104, number=104, labels=[Label(id=2, name="enhancement", color="00ff00", description="Enhancement")]),
            self.create_test_issue(id=105, number=105, labels=[Label(id=2, name="enhancement", color="00ff00", description="Enhancement")]),
        ]

        # Previous period (baseline)
        previous_issues = [
            self.create_test_issue(id=201, number=201, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=202, number=202, labels=[Label(id=1, name="bug", color="ff0000", description="Bug report")]),
            self.create_test_issue(id=203, number=203, labels=[Label(id=3, name="documentation", color="0000ff", description="Documentation")]),
        ]

        # This will FAIL initially - trending algorithm not implemented
        trending_labels = self.metrics_analyzer.calculate_trending_labels(current_issues, previous_issues)

        # Bug label should show 150% increase (3 vs 2, meets threshold)
        # Enhancement should be new (2 occurrences, meets minimum)
        # Documentation should show decline but may not qualify as trending

        assert isinstance(trending_labels, list)
        # Should find at least the new enhancement label and growing bug label
        assert len(trending_labels) >= 1

        # Find bug label in trending results
        bug_trend = None
        enhancement_trend = None

        for trend in trending_labels:
            if trend.label_name == "bug":
                bug_trend = trend
            elif trend.label_name == "enhancement":
                enhancement_trend = trend

        # Bug should show positive trend
        if bug_trend:
            assert bug_trend.count >= 3  # Current period count

        if enhancement_trend:
            assert enhancement_trend.count >= 2  # Current period count

    def test_time_based_activity_breakdowns(self):
        """Test time-based activity breakdown calculations."""
        # Create issues spanning different months
        base_date = datetime(2024, 1, 1)

        issues = [
            self.create_test_issue(id=101, number=101, created_at=base_date.replace(month=1), comment_count=5),
            self.create_test_issue(id=102, number=102, created_at=base_date.replace(month=1), comment_count=3),
            self.create_test_issue(id=103, number=103, created_at=base_date.replace(month=2), comment_count=8),
            self.create_test_issue(id=104, number=104, created_at=base_date.replace(month=2), comment_count=2),
            self.create_test_issue(id=105, number=105, created_at=base_date.replace(month=3), comment_count=1),
        ]

        # This will FAIL initially - time breakdown not implemented
        monthly_breakdown = self.metrics_analyzer.calculate_time_breakdown(issues, "monthly")

        assert isinstance(monthly_breakdown, dict)
        assert "2024-01" in monthly_breakdown
        assert "2024-02" in monthly_breakdown
        assert "2024-03" in monthly_breakdown

        # January: 2 issues, average ~4 comments
        assert monthly_breakdown["2024-01"] >= 2

        # February: 2 issues, average ~5 comments
        assert monthly_breakdown["2024-02"] >= 2

        # March: 1 issue, 1 comment
        assert monthly_breakdown["2024-03"] >= 1

    def test_most_active_users_analysis(self):
        """Test most active users analysis."""
        # Different users authoring issues
        users = [
            User(id=1, username="alice", display_name="Alice Developer", avatar_url="http://example.com/alice.png", is_bot=False),
            User(id=2, username="bob", display_name="Bob Tester", avatar_url="http://example.com/bob.png", is_bot=False),
            User(id=3, username="charlie", display_name="Charlie Manager", avatar_url="http://example.com/charlie.png", is_bot=False),
        ]

        issues = [
            self.create_test_issue(id=101, number=101, author=users[0]),  # alice: 3 issues
            self.create_test_issue(id=102, number=102, author=users[0]),
            self.create_test_issue(id=103, number=103, author=users[0]),
            self.create_test_issue(id=104, number=104, author=users[1]),  # bob: 2 issues
            self.create_test_issue(id=105, number=105, author=users[1]),
            self.create_test_issue(id=106, number=106, author=users[2]),  # charlie: 1 issue
        ]

        # This will FAIL initially - user activity analysis not implemented
        top_users = self.metrics_analyzer.analyze_most_active_users(issues)

        assert isinstance(top_users, list)
        assert len(top_users) == 3

        # alice should be first (3 issues)
        assert top_users[0].username == "alice"
        assert top_users[0].issues_created == 3

        # bob should be second (2 issues)
        assert top_users[1].username == "bob"
        assert top_users[1].issues_created == 2

        # charlie should be third (1 issue)
        assert top_users[2].username == "charlie"
        assert top_users[2].issues_created == 1

    def test_metrics_with_empty_issues(self):
        """Test metrics calculation with empty issues list."""
        # This will FAIL initially - MetricsAnalyzer not implemented
        metrics = self.metrics_analyzer.calculate_metrics([])

        assert isinstance(metrics, ActivityMetrics)
        assert metrics.total_issues_analyzed == 0
        assert metrics.issues_matching_filters == 0
        assert metrics.average_comment_count == 0.0
        assert metrics.top_labels == []

    def test_trending_algorithm_edge_cases(self):
        """Test trending algorithm with edge cases."""
        # New repository - no previous issues
        current_issues = [
            self.create_test_issue(id=101, number=101, labels=[Label(id=1, name="first-label", color="ff0000", description="First label")]),
        ]

        previous_issues = []  # No previous activity

        # This will FAIL initially - trending algorithm not implemented
        trending_labels = self.metrics_analyzer.calculate_trending_labels(current_issues, previous_issues)

        # Should handle new labels gracefully
        assert isinstance(trending_labels, list)

        # First label should appear as new/trending
        new_labels = [t for t in trending_labels if t.label_name == "first-label"]
        assert len(new_labels) > 0

    def test_large_repository_performance(self):
        """Test metrics calculation with large number of issues."""
        # Simulate a repository with many issues
        issues = []
        for i in range(500):  # 500 issues
            issue = self.create_test_issue(
                id=i+1,
                number=i+1,
                comment_count=i % 20,  # Varying comment counts
                created_at=datetime(2024, (i % 12) + 1, ((i % 27) + 1), 0, 0, 0),  # Spread across months
                labels=[Label(id=1, name=f"label_{i%5}", color="ff0000", description=f"Test label {i%5}")]
            )
            issues.append(issue)

        # This will FAIL initially - MetricsAnalyzer not implemented
        # But should handle large datasets efficiently
        import time
        start_time = time.time()

        metrics = self.metrics_analyzer.calculate_metrics(issues)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 1 second for 500 issues)
        assert duration < 1.0

        assert metrics.total_issues_analyzed == 500
        assert len(metrics.top_labels) <= 10  # Limited to top 10
