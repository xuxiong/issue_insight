"""
Pytest configuration and fixtures.

This module provides common fixtures and configuration for pytest tests
across unit, integration, and contract test suites.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from typing import Dict, Any

from issue_finder.models.repository import GitHubRepository
from issue_finder.models.issue import Issue, IssueState, Comment
from issue_finder.models.user import User, Label
from issue_finder.models.metrics import FilterCriteria, ActivityMetrics


@pytest.fixture
def sample_user() -> User:
    """Sample user object for testing."""
    return User(
        id=123456789,
        username="testuser",
        display_name="Test User",
        avatar_url="https://avatars.githubusercontent.com/u/123456789?v=4",
        is_bot=False,
    )


@pytest.fixture
def sample_label() -> Label:
    """Sample label object for testing."""
    return Label(
        id=987654321,
        name="bug",
        color="ff0000",
        description="Something isn't working",
    )


@pytest.fixture
def sample_repository() -> GitHubRepository:
    """Sample repository object for testing."""
    return GitHubRepository(
        owner="testowner",
        name="testrepo",
        url="https://github.com/testowner/testrepo",
        api_url="https://api.github.com/repos/testowner/testrepo",
        is_public=True,
        default_branch="main",
    )


@pytest.fixture
def sample_issue(sample_user: User) -> Issue:
    """Sample issue object for testing."""
    return Issue(
        id=123456789,
        number=42,
        title="Test Issue",
        body="This is a test issue for testing purposes",
        state=IssueState.OPEN,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 16, 14, 20, 0),
        closed_at=None,
        author=sample_user,
        assignees=[],
        labels=["bug", "test"],
        comment_count=3,
        comments=[],
        milestone=None,
        is_pull_request=False,
    )


@pytest.fixture
def sample_comment(sample_user: User) -> Comment:
    """Sample comment object for testing."""
    return Comment(
        id=987654321,
        body="This is a test comment",
        author=sample_user,
        created_at=datetime(2024, 1, 15, 11, 0, 0),
        updated_at=datetime(2024, 1, 15, 11, 0, 0),
        issue_id=42,
    )


@pytest.fixture
def sample_filter_criteria() -> FilterCriteria:
    """Sample filter criteria for testing."""
    return FilterCriteria(
        min_comments=1,
        max_comments=10,
        state="open",
        labels=["bug"],
        assignees=["testuser"],
        created_after=datetime(2024, 1, 1),
        created_before=datetime(2024, 12, 31),
    )


@pytest.fixture
def sample_activity_metrics() -> ActivityMetrics:
    """Sample activity metrics for testing."""
    return ActivityMetrics(
        total_issues_analyzed=100,
        issues_matching_filters=25,
        average_comment_count=3.5,
        comment_distribution={"1-5": 60, "6-10": 20, "11+": 5},
        top_labels=[],
        activity_by_month={"2024-01": 45, "2024-02": 67},
        most_active_users=[],
        average_issue_resolution_time=7.2,
    )


@pytest.fixture
def mock_github_repo():
    """Mock GitHub repository object."""
    repo = Mock()
    repo.name = "testrepo"
    repo.owner.login = "testowner"
    repo.owner.name = "Test Owner"
    repo.html_url = "https://github.com/testowner/testrepo"
    repo.url = "https://api.github.com/repos/testowner/testrepo"
    repo.private = False
    repo.default_branch = "main"
    return repo


@pytest.fixture
def mock_github_issue():
    """Mock GitHub issue object."""
    issue = Mock()
    issue.id = 123456789
    issue.number = 42
    issue.title = "Test Issue"
    issue.body = "This is a test issue"
    issue.state = "open"
    issue.created_at = datetime(2024, 1, 15, 10, 30, 0)
    issue.updated_at = datetime(2024, 1, 16, 14, 20, 0)
    issue.closed_at = None
    issue.user.login = "testuser"
    issue.user.name = "Test User"
    issue.user.id = 123456789
    issue.user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
    issue.user.type = "User"
    issue.assignees = []
    issue.labels = []
    issue.comments = 3
    issue.milestone = None
    issue.pull_request = None
    return issue


@pytest.fixture
def mock_github_comment():
    """Mock GitHub comment object."""
    comment = Mock()
    comment.id = 987654321
    comment.body = "This is a test comment"
    comment.user.login = "testuser"
    comment.user.name = "Test User"
    comment.user.id = 123456789
    comment.user.avatar_url = "https://avatars.githubusercontent.com/u/123456789?v=4"
    comment.user.type = "User"
    comment.created_at = datetime(2024, 1, 15, 11, 0, 0)
    comment.updated_at = datetime(2024, 1, 15, 11, 0, 0)
    return comment


@pytest.fixture
def valid_repo_urls():
    """Valid repository URLs for testing."""
    return [
        "https://github.com/facebook/react",
        "https://github.com/python/cpython",
        "https://github.com/microsoft/vscode",
    ]


@pytest.fixture
def invalid_repo_urls():
    """Invalid repository URLs for testing."""
    return [
        "https://gitlab.com/user/repo",
        "github.com/user/repo",  # Missing protocol
        "https://github.com/user",  # Missing repo name
        "https://github.com/user/repo/extra",  # Extra path
        "not-a-url",
    ]


@pytest.fixture
def sample_github_responses():
    """Sample GitHub API responses for testing."""
    return {
        "repository": {
            "id": 123456789,
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "owner": {
                "login": "testowner",
                "id": 987654321,
            },
            "html_url": "https://github.com/testowner/testrepo",
            "url": "https://api.github.com/repos/testowner/testrepo",
            "private": False,
            "default_branch": "main",
        },
        "issue": {
            "id": 123456789,
            "number": 42,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-16T14:20:00Z",
            "user": {
                "login": "testuser",
                "id": 123456789,
                "name": "Test User",
                "avatar_url": "https://avatars.githubusercontent.com/u/123456789?v=4",
                "type": "User",
            },
            "comments": 3,
            "labels": [
                {
                    "id": 987654321,
                    "name": "bug",
                    "color": "ff0000",
                    "description": "Something isn't working",
                }
            ],
            "assignees": [],
            "milestone": None,
            "pull_request": None,
        },
    }


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary directory for configuration files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


# Test markers for categorizing tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external services"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require external services"
    )
    config.addinivalue_line(
        "markers", "contract: Contract tests that verify API contracts"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on file location
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "contract/" in str(item.fspath):
            item.add_marker(pytest.mark.contract)