"""
Unit tests for filter engine (T007-1).

These tests are written FIRST and expected to FAIL until the filter engine is implemented.
This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

# These imports will fail initially (TDD - tests FAIL first)
from services.filter_engine import FilterEngine, FilterCriteria
from models import Issue, IssueState, User, Label


@pytest.mark.unit
class TestFilterCriteria:
    """Test FilterCriteria model validation."""

    def test_valid_filter_criteria(self):
        """Test creating valid filter criteria."""
        criteria = FilterCriteria(
            min_comments=5,
            max_comments=20,
            state=IssueState.OPEN,
            labels=["enhancement", "bug"],
            assignees=["contributor1"],
            limit=100,
            any_labels=True,
            any_assignees=False,
        )

        assert criteria.min_comments == 5
        assert criteria.max_comments == 20
        assert criteria.state == IssueState.OPEN
        assert criteria.labels == ["enhancement", "bug"]
        assert criteria.assignees == ["contributor1"]
        assert criteria.limit == 100
        assert criteria.any_labels is True
        assert criteria.any_assignees is False

    def test_filter_criteria_defaults(self):
        """Test filter criteria default values."""
        criteria = FilterCriteria()

        assert criteria.min_comments is None
        assert criteria.max_comments is None
        assert criteria.state is None
        assert criteria.labels == []
        assert criteria.assignees == []
        assert criteria.limit is None  # Should be None for unlimited
        assert criteria.any_labels is True
        assert criteria.any_assignees is True
        assert criteria.include_comments is False
        assert criteria.page_size == 100

    def test_invalid_limit_value(self):
        """Test validation of invalid limit values."""
        with pytest.raises(ValueError, match="Limit must be at least 1 when specified"):
            FilterCriteria(limit=0)

        with pytest.raises(ValueError, match="Limit must be at least 1 when specified"):
            FilterCriteria(limit=-5)

    def test_valid_limit_values(self):
        """Test validation of valid limit values."""
        for limit in [1, 10, 100, 1000]:
            criteria = FilterCriteria(limit=limit)
            assert criteria.limit == limit

    def test_invalid_comment_filters(self):
        """Test validation of invalid comment count filters."""
        with pytest.raises(ValueError, match="Comment count must be non-negative"):
            FilterCriteria(min_comments=-1)

        with pytest.raises(ValueError, match="Comment count must be non-negative"):
            FilterCriteria(max_comments=-10)

        with pytest.raises(
            ValueError, match="min_comments cannot be greater than max_comments"
        ):
            FilterCriteria(min_comments=10, max_comments=5)

    def test_date_range_validation(self):
        """Test date range validation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        # Valid date range
        criteria = FilterCriteria(created_since=start_date, created_until=end_date)
        assert criteria.created_since == start_date
        assert criteria.created_until == end_date

        # Invalid date range (end before start)
        with pytest.raises(
            ValueError, match="created_since cannot be after created_until"
        ):
            FilterCriteria(created_since=end_date, created_until=start_date)


@pytest.mark.unit
class TestFilterEngine:
    """Test issue filtering logic."""

    def test_filter_by_comment_count_min(self):
        """Test filtering by minimum comment count."""
        engine = FilterEngine()
        criteria = FilterCriteria(min_comments=5)

        # Create test issues
        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 3, "title": "Few comments"},
                {"number": 2, "comment_count": 7, "title": "Many comments"},
                {"number": 3, "comment_count": 5, "title": "Exactly 5 comments"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 2  # 7 comments
        assert filtered_issues[1].number == 3  # 5 comments

    def test_filter_by_comment_count_max(self):
        """Test filtering by maximum comment count."""
        engine = FilterEngine()
        criteria = FilterCriteria(max_comments=10)

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 5, "title": "Few comments"},
                {"number": 2, "comment_count": 15, "title": "Too many comments"},
                {"number": 3, "comment_count": 10, "title": "Exactly 10 comments"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 1  # 5 comments
        assert filtered_issues[1].number == 3  # 10 comments

    def test_filter_by_comment_count_range(self):
        """Test filtering by comment count range."""
        engine = FilterEngine()
        criteria = FilterCriteria(min_comments=3, max_comments=8)

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 2, "title": "Too few"},
                {"number": 2, "comment_count": 5, "title": "Just right"},
                {"number": 3, "comment_count": 9, "title": "Too many"},
                {"number": 4, "comment_count": 8, "title": "At max"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 2  # 5 comments
        assert filtered_issues[1].number == 4  # 8 comments

    def test_filter_by_issue_state(self):
        """Test filtering by issue state."""
        engine = FilterEngine()
        criteria = FilterCriteria(state=IssueState.OPEN)

        issues = self._create_test_issues(
            [
                {"number": 1, "state": IssueState.OPEN, "title": "Open issue"},
                {"number": 2, "state": IssueState.CLOSED, "title": "Closed issue"},
                {"number": 3, "state": IssueState.OPEN, "title": "Another open"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 1
        assert filtered_issues[1].number == 3

    def test_filter_by_labels_any(self):
        """Test filtering by labels with ANY logic."""
        engine = FilterEngine()
        criteria = FilterCriteria(labels=["enhancement", "bug"], any_labels=True)

        issues = self._create_test_issues_with_labels(
            [
                {"number": 1, "labels": ["enhancement"], "title": "Enhancement issue"},
                {"number": 2, "labels": ["bug"], "title": "Bug issue"},
                {
                    "number": 3,
                    "labels": ["documentation"],
                    "title": "Documentation issue",
                },
                {"number": 4, "labels": ["enhancement", "bug"], "title": "Both labels"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 3
        assert filtered_issues[0].number == 1  # has "enhancement"
        assert filtered_issues[1].number == 2  # has "bug"
        assert filtered_issues[2].number == 4  # has both

    def test_filter_by_labels_all(self):
        """Test filtering by labels with ALL logic."""
        engine = FilterEngine()
        criteria = FilterCriteria(labels=["enhancement", "bug"], any_labels=False)

        issues = self._create_test_issues_with_labels(
            [
                {"number": 1, "labels": ["enhancement"], "title": "Enhancement only"},
                {"number": 2, "labels": ["bug"], "title": "Bug only"},
                {"number": 3, "labels": ["documentation"], "title": "Wrong label"},
                {"number": 4, "labels": ["enhancement", "bug"], "title": "Both labels"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 4  # Only has both labels

    def test_filter_by_assignees_any(self):
        """Test filtering by assignees with ANY logic."""
        engine = FilterEngine()
        criteria = FilterCriteria(
            assignees=["contributor1", "contributor2"], any_assignees=True
        )

        issues = self._create_test_issues_with_assignees(
            [
                {
                    "number": 1,
                    "assignees": ["contributor1"],
                    "title": "Assigned to contributor1",
                },
                {
                    "number": 2,
                    "assignees": ["contributor2"],
                    "title": "Assigned to contributor2",
                },
                {"number": 3, "assignees": ["contributor3"], "title": "Wrong assignee"},
                {"number": 4, "assignees": [], "title": "Unassigned"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 1
        assert filtered_issues[1].number == 2

    def test_filter_by_assignees_all(self):
        """Test filtering by assignees with ALL logic."""
        engine = FilterEngine()
        criteria = FilterCriteria(
            assignees=["contributor1", "contributor2"], any_assignees=False
        )

        issues = self._create_test_issues_with_assignees(
            [
                {
                    "number": 1,
                    "assignees": ["contributor1"],
                    "title": "Only contributor1",
                },
                {
                    "number": 2,
                    "assignees": ["contributor1", "contributor2"],
                    "title": "Both assignees",
                },
                {
                    "number": 3,
                    "assignees": ["contributor2", "contributor3"],
                    "title": "Wrong combination",
                },
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 2  # Has both required assignees

    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        engine = FilterEngine()
        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 20)
        criteria = FilterCriteria(created_since=start_date, created_until=end_date)

        issues = self._create_test_issues_with_dates(
            [
                {"number": 1, "created": datetime(2024, 1, 5), "title": "Too early"},
                {"number": 2, "created": datetime(2024, 1, 15), "title": "Just right"},
                {"number": 3, "created": datetime(2024, 1, 25), "title": "Too late"},
                {
                    "number": 4,
                    "created": datetime(2024, 1, 10),
                    "title": "Exactly at start",
                },
                {
                    "number": 5,
                    "created": datetime(2024, 1, 20),
                    "title": "Exactly at end",
                },
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 3
        assert filtered_issues[0].number == 2
        assert filtered_issues[1].number == 4
        assert filtered_issues[2].number == 5

    def test_apply_limit_functionality(self):
        """Test limit application and validation."""
        engine = FilterEngine()
        criteria = FilterCriteria(limit=2)

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 5, "title": "Issue 1"},
                {"number": 2, "comment_count": 3, "title": "Issue 2"},
                {"number": 3, "comment_count": 7, "title": "Issue 3"},
                {"number": 4, "comment_count": 1, "title": "Issue 4"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 1
        assert filtered_issues[1].number == 2

    def test_unlimited_limit(self):
        """Test behavior when limit is None (unlimited)."""
        engine = FilterEngine()
        criteria = FilterCriteria(limit=None)

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 5, "title": "Issue 1"},
                {"number": 2, "comment_count": 3, "title": "Issue 2"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2  # Should return all issues

    def test_complex_filtering(self):
        """Test multiple filters combined."""
        engine = FilterEngine()
        criteria = FilterCriteria(
            min_comments=2, state=IssueState.OPEN, labels=["enhancement"], limit=3
        )

        issues = self._create_test_issues_with_complex_data(
            [
                {
                    "number": 1,
                    "comment_count": 1,
                    "state": IssueState.OPEN,
                    "labels": ["enhancement"],
                    "title": "Too few comments",
                },
                {
                    "number": 2,
                    "comment_count": 3,
                    "state": IssueState.OPEN,
                    "labels": ["enhancement"],
                    "title": "Perfect match",
                },
                {
                    "number": 3,
                    "comment_count": 5,
                    "state": IssueState.CLOSED,
                    "labels": ["enhancement"],
                    "title": "Wrong state",
                },
                {
                    "number": 4,
                    "comment_count": 4,
                    "state": IssueState.OPEN,
                    "labels": ["bug"],
                    "title": "Wrong label",
                },
                {
                    "number": 5,
                    "comment_count": 6,
                    "state": IssueState.OPEN,
                    "labels": ["enhancement"],
                    "title": "Another match",
                },
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert filtered_issues[0].number == 2
        assert filtered_issues[1].number == 5

    def test_empty_filter_criteria(self):
        """Test filtering with empty criteria (should return all)."""
        engine = FilterEngine()
        criteria = FilterCriteria()

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 5, "title": "Issue 1"},
                {"number": 2, "comment_count": 3, "title": "Issue 2"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2  # Should return all issues

    def test_no_matching_results(self):
        """Test filtering when no issues match criteria."""
        engine = FilterEngine()
        criteria = FilterCriteria(min_comments=100)  # Very high threshold

        issues = self._create_test_issues(
            [
                {"number": 1, "comment_count": 5, "title": "Issue 1"},
                {"number": 2, "comment_count": 3, "title": "Issue 2"},
            ]
        )

        filtered_issues = engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 0

    # Helper methods for creating test data
    def _create_test_issues(self, issue_data_list):
        """Helper to create test issues with basic data."""
        issues = []
        for data in issue_data_list:
            author = User(
                id=1,
                username="testuser",
                display_name="Test User",
                avatar_url="https://github.com/testuser.png",
            )
            issue = Issue(
                id=data["number"],
                number=data["number"],
                title=data["title"],
                body="Test body",
                state=data.get("state", IssueState.OPEN),
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=[],
                labels=[],
                comment_count=data.get("comment_count", 0),
                comments=[],
                is_pull_request=False,
            )
            issues.append(issue)
        return issues

    def _create_test_issues_with_labels(self, issue_data_list):
        """Helper to create test issues with labels."""
        issues = []
        for data in issue_data_list:
            author = User(
                id=1,
                username="testuser",
                display_name="Test User",
                avatar_url="https://github.com/testuser.png",
            )

            # Create Label objects
            labels = []
            for label_name in data["labels"]:
                label = Label(
                    id=len(labels) + 1,
                    name=label_name,
                    color="ff0000",
                    description=f"Label {label_name}",
                )
                labels.append(label)

            issue = Issue(
                id=data["number"],
                number=data["number"],
                title=data["title"],
                body="Test body",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=[],
                labels=labels,
                comment_count=3,
                comments=[],
                is_pull_request=False,
            )
            issues.append(issue)
        return issues

    def _create_test_issues_with_assignees(self, issue_data_list):
        """Helper to create test issues with assignees."""
        issues = []
        for data in issue_data_list:
            author = User(
                id=1,
                username="testuser",
                display_name="Test User",
                avatar_url="https://github.com/testuser.png",
            )

            # Create assignee User objects
            assignees = []
            for assignee_name in data["assignees"]:
                assignee = User(
                    id=len(assignees) + 2,
                    username=assignee_name,
                    display_name=assignee_name.capitalize(),
                    avatar_url=f"https://github.com/{assignee_name}.png",
                )
                assignees.append(assignee)

            issue = Issue(
                id=data["number"],
                number=data["number"],
                title=data["title"],
                body="Test body",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=assignees,
                labels=[],
                comment_count=3,
                comments=[],
                is_pull_request=False,
            )
            issues.append(issue)
        return issues

    def _create_test_issues_with_dates(self, issue_data_list):
        """Helper to create test issues with specific dates."""
        issues = []
        for data in issue_data_list:
            author = User(
                id=1,
                username="testuser",
                display_name="Test User",
                avatar_url="https://github.com/testuser.png",
            )
            issue = Issue(
                id=data["number"],
                number=data["number"],
                title=data["title"],
                body="Test body",
                state=IssueState.OPEN,
                created_at=data["created"],
                updated_at=data["created"],
                closed_at=None,
                author=author,
                assignees=[],
                labels=[],
                comment_count=3,
                comments=[],
                is_pull_request=False,
            )
            issues.append(issue)
        return issues

    def _create_test_issues_with_complex_data(self, issue_data_list):
        """Helper to create test issues with complex data."""
        issues = []
        for data in issue_data_list:
            author = User(
                id=1,
                username="testuser",
                display_name="Test User",
                avatar_url="https://github.com/testuser.png",
            )

            # Create labels
            labels = []
            for label_name in data["labels"]:
                label = Label(
                    id=len(labels) + 1,
                    name=label_name,
                    color="ff0000",
                    description=f"Label {label_name}",
                )
                labels.append(label)

            issue = Issue(
                id=data["number"],
                number=data["number"],
                title=data["title"],
                body="Test body",
                state=data["state"],
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=[],
                labels=labels,
                comment_count=data["comment_count"],
                comments=[],
                is_pull_request=False,
            )
            issues.append(issue)
        return issues


@pytest.mark.unit
class TestFilterEngineErrorHandling:
    """Test error handling for invalid filters."""

    def test_invalid_filter_criteria_type(self):
        """Test error handling for invalid filter criteria types."""
        engine = FilterEngine()

        # This should handle cases where filter criteria is not properly structured
        issues = []  # Empty issues list

        with pytest.raises(ValueError):
            engine.filter_issues(issues, None)  # None criteria should error

    def test_filter_with_empty_issues_list(self):
        """Test filtering with empty issues list."""
        engine = FilterEngine()
        criteria = FilterCriteria(min_comments=5)

        filtered_issues = engine.filter_issues([], criteria)

        assert filtered_issues == []

    def test_filter_with_none_issues_list(self):
        """Test filtering with None issues list."""
        engine = FilterEngine()
        criteria = FilterCriteria(min_comments=5)

        with pytest.raises(ValueError, match="Issues list cannot be None"):
            engine.filter_issues(None, criteria)
