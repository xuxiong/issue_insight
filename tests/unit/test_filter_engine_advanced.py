"""
Unit tests for advanced filtering logic (T021).

These tests are written FIRST and expected to FAIL until the advanced filtering
engine is implemented. This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

# These imports will FAIL initially (TDD - tests must FAIL first)
from services.filter_engine import FilterEngine, FilterCriteria
from models import Issue, IssueState, User, Label


@pytest.mark.unit
class TestStateFiltering:
    """Test state-based filtering (open/closed)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter_engine = FilterEngine()
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

    def test_state_filter_open_only(self):
        """Test filtering for open issues only."""
        issues = [
            self.create_test_issue(id=1, number=101, state=IssueState.OPEN, title="Open issue 1"),
            self.create_test_issue(id=2, number=102, state=IssueState.CLOSED, title="Closed issue 1"),
            self.create_test_issue(id=3, number=103, state=IssueState.OPEN, title="Open issue 2"),
        ]

        criteria = FilterCriteria(state=IssueState.OPEN)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert all(issue.state == IssueState.OPEN for issue in filtered_issues)
        assert {issue.number for issue in filtered_issues} == {101, 103}

    def test_state_filter_closed_only(self):
        """Test filtering for closed issues only."""
        issues = [
            self.create_test_issue(id=1, number=101, state=IssueState.OPEN, title="Open issue"),
            self.create_test_issue(id=2, number=102, state=IssueState.CLOSED, title="Closed issue 1"),
            self.create_test_issue(id=3, number=103, state=IssueState.CLOSED, title="Closed issue 2"),
        ]

        criteria = FilterCriteria(state=IssueState.CLOSED)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert all(issue.state == IssueState.CLOSED for issue in filtered_issues)
        assert {issue.number for issue in filtered_issues} == {102, 103}

    def test_state_filter_none_returns_all(self):
        """Test that None state filter returns all issues."""
        issues = [
            self.create_test_issue(id=1, number=101, state=IssueState.OPEN),
            self.create_test_issue(id=2, number=102, state=IssueState.CLOSED),
        ]

        criteria = FilterCriteria(state=None)  # No state filter

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2


@pytest.mark.unit
class TestLabelFiltering:
    """Test label-based filtering with ANY/ALL logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter_engine = FilterEngine()
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_issue_with_labels(self, number, title, labels):
        """Helper to create test Issue with labels."""
        label_objects = []
        for label_name in labels:
            label = Label(
                id=len(label_objects) + 1,
                name=label_name,
                color="ff0000",
                description=f"Label {label_name}"
            )
            label_objects.append(label)

        return Issue(
            id=number,
            number=number,
            title=title,
            body="Test body",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=self.mock_user,
            assignees=[],
            labels=label_objects,
            comments=[],
            is_pull_request=False,
            comment_count=5
        )

    def test_label_filter_any_logic_single_label(self):
        """Test ANY logic with single target label."""
        issues = [
            self.create_test_issue_with_labels(101, "Bug issue", ["bug"]),
            self.create_test_issue_with_labels(102, "Enhancement issue", ["enhancement"]),
            self.create_test_issue_with_labels(103, "Documentation issue", ["documentation"]),
            self.create_test_issue_with_labels(104, "No labels", []),
        ]

        criteria = FilterCriteria(labels=["bug"], any_labels=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 101

    def test_label_filter_any_logic_multiple_labels(self):
        """Test ANY logic with multiple target labels."""
        issues = [
            self.create_test_issue_with_labels(101, "Bug issue", ["bug"]),
            self.create_test_issue_with_labels(102, "Enhancement issue", ["enhancement"]),
            self.create_test_issue_with_labels(103, "Documentation issue", ["documentation"]),
            self.create_test_issue_with_labels(104, "Both labels", ["bug", "enhancement"]),
        ]

        criteria = FilterCriteria(labels=["bug", "enhancement"], any_labels=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 3
        assert {issue.number for issue in filtered_issues} == {101, 102, 104}

    def test_label_filter_all_logic_multiple_labels(self):
        """Test ALL logic with multiple target labels."""
        issues = [
            self.create_test_issue_with_labels(101, "Bug only", ["bug"]),
            self.create_test_issue_with_labels(102, "Enhancement only", ["enhancement"]),
            self.create_test_issue_with_labels(103, "Documentation issue", ["documentation"]),
            self.create_test_issue_with_labels(104, "Both labels", ["bug", "enhancement"]),
            self.create_test_issue_with_labels(105, "All labels", ["bug", "enhancement", "documentation"]),
        ]

        criteria = FilterCriteria(labels=["bug", "enhancement"], any_labels=False)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2
        assert {issue.number for issue in filtered_issues} == {104, 105}

    def test_label_filter_no_matches(self):
        """Test label filtering when no issues match."""
        issues = [
            self.create_test_issue_with_labels(101, "Documentation issue", ["documentation"]),
            self.create_test_issue_with_labels(102, "Feature request", ["feature"]),
        ]

        criteria = FilterCriteria(labels=["bug"], any_labels=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 0

    def test_label_filter_empty_labels_list(self):
        """Test that empty labels filter returns all issues."""
        issues = [
            self.create_test_issue_with_labels(101, "Issue 1", ["bug"]),
            self.create_test_issue_with_labels(102, "Issue 2", []),
        ]

        criteria = FilterCriteria(labels=[], any_labels=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2


@pytest.mark.unit
class TestAssigneeFiltering:
    """Test assignee-based filtering with ANY/ALL logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter_engine = FilterEngine()
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_test_issue_with_assignees(self, number, title, assignees):
        """Helper to create test Issue with assignees."""
        assignee_objects = []
        for assignee_name in assignees:
            assignee = User(
                id=len(assignee_objects) + 2,
                username=assignee_name,
                display_name=assignee_name.capitalize(),
                avatar_url=f"https://github.com/{assignee_name}.png",
                is_bot=False
            )
            assignee_objects.append(assignee)

        return Issue(
            id=number,
            number=number,
            title=title,
            body="Test body",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=self.mock_user,
            assignees=assignee_objects,
            labels=[],
            comments=[],
            is_pull_request=False,
            comment_count=5
        )

    def test_assignee_filter_any_logic_single_assignee(self):
        """Test ANY logic with single target assignee."""
        issues = [
            self.create_test_issue_with_assignees(101, "Assigned to contributor1", ["contributor1"]),
            self.create_test_issue_with_assignees(102, "Assigned to contributor2", ["contributor2"]),
            self.create_test_issue_with_assignees(103, "Unassigned", []),
        ]

        criteria = FilterCriteria(assignees=["contributor1"], any_assignees=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 101

    def test_assignee_filter_any_logic_multiple_assignees(self):
        """Test ANY logic with multiple target assignees."""
        issues = [
            self.create_test_issue_with_assignees(101, "Assigned to contributor1", ["contributor1"]),
            self.create_test_issue_with_assignees(102, "Assigned to contributor2", ["contributor2"]),
            self.create_test_issue_with_assignees(103, "Assigned to contributor3", ["contributor3"]),
            self.create_test_issue_with_assignees(104, "Both contributors", ["contributor1", "contributor2"]),
        ]

        criteria = FilterCriteria(assignees=["contributor1", "contributor2"], any_assignees=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 3
        assert {issue.number for issue in filtered_issues} == {101, 102, 104}

    def test_assignee_filter_all_logic_multiple_assignees(self):
        """Test ALL logic with multiple target assignees."""
        issues = [
            self.create_test_issue_with_assignees(101, "Only contributor1", ["contributor1"]),
            self.create_test_issue_with_assignees(102, "Only contributor2", ["contributor2"]),
            self.create_test_issue_with_assignees(103, "Both contributors", ["contributor1", "contributor2"]),
            self.create_test_issue_with_assignees(104, "Unassigned", []),
        ]

        criteria = FilterCriteria(assignees=["contributor1", "contributor2"], any_assignees=False)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 103

    def test_assignee_filter_empty_assignees_list(self):
        """Test that empty assignees filter returns all issues."""
        issues = [
            self.create_test_issue_with_assignees(101, "Assigned issue", ["contributor1"]),
            self.create_test_issue_with_assignees(102, "Unassigned", []),
        ]

        criteria = FilterCriteria(assignees=[], any_assignees=True)

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2


@pytest.mark.unit
class TestCombinedFiltering:
    """Test combining multiple filter criteria."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter_engine = FilterEngine()
        self.mock_user = User(
            id=1,
            username="testuser",
            display_name="Test User",
            avatar_url="http://example.com/avatar.png",
            is_bot=False,
        )

    def create_complex_issue(self, number, title, state, labels, assignees, comment_count):
        """Helper to create complex test issues."""
        label_objects = [Label(id=i+1, name=l, color="ff0000", description=l) for i, l in enumerate(labels)]
        assignee_objects = [User(id=i+2, username=a, display_name=a.capitalize(),
                                avatar_url=f"https://github.com/{a}.png", is_bot=False) for i, a in enumerate(assignees)]

        return Issue(
            id=number,
            number=number,
            title=title,
            body="Test body",
            state=state,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=self.mock_user,
            assignees=assignee_objects,
            labels=label_objects,
            comments=[],
            is_pull_request=False,
            comment_count=comment_count
        )

    def test_combined_state_and_labels(self):
        """Test combining state and label filters."""
        issues = [
            self.create_complex_issue(101, "Open bug", IssueState.OPEN, ["bug"], [], 3),
            self.create_complex_issue(102, "Open enhancement", IssueState.OPEN, ["enhancement"], [], 5),
            self.create_complex_issue(103, "Closed bug", IssueState.CLOSED, ["bug"], [], 7),
            self.create_complex_issue(104, "Open doc", IssueState.OPEN, ["documentation"], [], 2),
        ]

        criteria = FilterCriteria(
            state=IssueState.OPEN,
            labels=["bug"],
            any_labels=True,
            min_comments=3
        )

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1  # Only the open bug with >=3 comments
        assert filtered_issues[0].number == 101

    def test_combined_labels_and_assignees(self):
        """Test combining label and assignee filters."""
        issues = [
            self.create_complex_issue(101, "Bug by contributor1", IssueState.OPEN, ["bug"], ["contributor1"], 5),
            self.create_complex_issue(102, "Enhancement by contributor2", IssueState.OPEN, ["enhancement"], ["contributor2"], 7),
            self.create_complex_issue(103, "Bug unassigned", IssueState.OPEN, ["bug"], [], 3),
            self.create_complex_issue(104, "Doc by contributor1", IssueState.OPEN, ["documentation"], ["contributor1"], 2),
        ]

        criteria = FilterCriteria(
            labels=["bug", "enhancement"],
            any_labels=True,
            assignees=["contributor1", "contributor2"],
            any_assignees=True,
            min_comments=4
        )

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 2  # Bug and enhancement with >=4 comments and matching assignees
        assert {issue.number for issue in filtered_issues} == {101, 102}

    def test_all_filters_combined(self):
        """Test all filter types combined."""
        issues = [
            # Should match - open, has enhancement label, assigned to contributor1, >=5 comments
            self.create_complex_issue(101, "Perfect match", IssueState.OPEN, ["enhancement"], ["contributor1"], 7),
            # Doesn't match - closed
            self.create_complex_issue(102, "Wrong state", IssueState.CLOSED, ["enhancement"], ["contributor1"], 6),
            # Doesn't match - wrong label
            self.create_complex_issue(103, "Wrong label", IssueState.OPEN, ["documentation"], ["contributor1"], 8),
            # Doesn't match - unassigned
            self.create_complex_issue(104, "Unassigned", IssueState.OPEN, ["enhancement"], [], 9),
            # Doesn't match - too few comments
            self.create_complex_issue(105, "Low comments", IssueState.OPEN, ["enhancement"], ["contributor1"], 3),
        ]

        criteria = FilterCriteria(
            min_comments=5,
            max_comments=10,
            state=IssueState.OPEN,
            labels=["enhancement"],
            any_labels=True,
            assignees=["contributor1"],
            any_assignees=True
        )

        # This will FAIL initially
        filtered_issues = self.filter_engine.filter_issues(issues, criteria)

        assert len(filtered_issues) == 1
        assert filtered_issues[0].number == 101
