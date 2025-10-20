"""Contract tests for GitHub API endpoints."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from models import Issue, IssueState
from services.github_client import GitHubClient, RateLimitExceededException


@pytest.fixture(autouse=True)
def mock_github_dependencies(monkeypatch):
    github_instance = Mock(name="GithubInstance")
    rate_limit = Mock()
    rate_limit.core.limit = 5000
    rate_limit.core.remaining = 5000
    rate_limit.core.reset = datetime.now().replace(microsecond=0)
    github_instance.get_rate_limit.return_value = rate_limit

    github_constructor = Mock(return_value=github_instance)
    monkeypatch.setattr("services.github_client.Github", github_constructor)

    return github_instance


def _build_repository(owner_login="testowner", owner_name="Test Owner", name="testrepo"):
    owner = Mock()
    owner.login = owner_login
    owner.name = owner_name

    repository = Mock()
    repository.owner = owner
    repository.name = name
    repository.html_url = f"https://github.com/{owner_login}/{name}"
    repository.url = f"https://api.github.com/repos/{owner_login}/{name}"
    repository.private = False
    repository.default_branch = "main"
    return repository


def _build_user(login="testuser", user_id=123456789, type_="User"):
    user = Mock()
    user.login = login
    user.name = login
    user.id = user_id
    user.avatar_url = f"https://avatars.githubusercontent.com/u/{user_id}?v=4"
    user.type = type_
    return user


def _build_issue(
    *,
    issue_id=123456789,
    number=42,
    title="Test Issue Title",
    state="open",
    comment_count=5,
    created_at=datetime(2024, 1, 15, 10, 30, 0),
    updated_at=datetime(2024, 1, 16, 14, 20, 0),
    closed_at=None,
    user=None,
    assignees=None,
    labels=None,
    pull_request=None,
):
    issue = Mock()
    issue.id = issue_id
    issue.number = number
    issue.title = title
    issue.body = "Test issue body content"
    issue.state = state
    issue.created_at = created_at
    issue.updated_at = updated_at
    issue.closed_at = closed_at
    issue.user = user or _build_user()
    issue.assignees = assignees or []
    issue.labels = labels or []
    issue.comments = comment_count
    issue.milestone = None
    issue.pull_request = pull_request
    return issue


def _build_comment(
    *,
    comment_id=987654321,
    body="This is a test comment",
    created_at=datetime(2024, 1, 15, 11, 0, 0),
    updated_at=datetime(2024, 1, 15, 11, 0, 0),
    user=None,
):
    comment = Mock()
    comment.id = comment_id
    comment.body = body
    comment.created_at = created_at
    comment.updated_at = updated_at
    comment.user = user or _build_user(login="commenter", user_id=987654321)
    return comment


def test_repository_info_contract(mock_github_dependencies):
    repository_url = "https://github.com/testowner/testrepo"
    mock_github_dependencies.get_repo.return_value = _build_repository()

    client = GitHubClient(token=None, use_env_if_none=False)
    result = client.get_repository(repository_url)

    assert result.owner == "testowner"
    assert result.name == "testrepo"
    assert result.url == "https://github.com/testowner/testrepo"
    assert result.api_url == "https://api.github.com/repos/testowner/testrepo"
    assert result.default_branch == "main"


def test_issue_list_contract(mock_github_dependencies):
    mock_repo = _build_repository()
    mock_issue = _build_issue()
    mock_repo.get_issues.return_value = [mock_issue]
    mock_github_dependencies.get_repo.return_value = mock_repo

    client = GitHubClient(token=None, use_env_if_none=False)
    issues = list(client.get_issues("testowner", "testrepo", limit=1))

    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, Issue)
    assert issue.id == 123456789
    assert issue.number == 42
    assert issue.title == "Test Issue Title"
    assert issue.state == IssueState.OPEN
    assert issue.author.username == "testuser"
    assert issue.comment_count == 5


def test_comment_list_contract(mock_github_dependencies):
    mock_repo = _build_repository()
    mock_issue = Mock()
    mock_issue.get_comments.return_value = [_build_comment()]
    mock_repo.get_issue.return_value = mock_issue
    mock_github_dependencies.get_repo.return_value = mock_repo

    client = GitHubClient(token=None, use_env_if_none=False)
    comments = client.get_comments_for_issue("testowner", "testrepo", 42)

    assert len(comments) == 1
    comment = comments[0]
    assert comment.id == 987654321
    assert comment.body == "This is a test comment"
    assert comment.author.username == "commenter"
    assert comment.issue_id == 42


def test_rate_limit_contract(monkeypatch, mock_github_dependencies):
    client = GitHubClient(token=None, use_env_if_none=False)
    mock_github_dependencies.get_repo.side_effect = RateLimitExceededException(
        status=403,
        data={"message": "API rate limit exceeded"},
    )

    with pytest.raises(RateLimitExceededException):
        client.get_issues("testowner", "testrepo")


def test_pull_request_exclusion_contract(mock_github_dependencies):
    mock_repo = _build_repository()
    regular_issue = _build_issue(issue_id=1, number=1, title="Regular Issue", pull_request=None)
    pull_request = _build_issue(issue_id=2, number=2, title="Pull Request", pull_request=Mock())
    mock_repo.get_issues.return_value = [regular_issue, pull_request]
    mock_github_dependencies.get_repo.return_value = mock_repo

    client = GitHubClient(token=None, use_env_if_none=False)
    issues = list(client.get_issues("testowner", "testrepo"))

    assert len(issues) == 1
    assert issues[0].title == "Regular Issue"
    assert issues[0].is_pull_request is False


def test_user_contract(mock_github_dependencies):
    mock_repo = _build_repository()
    mock_issue = _build_issue(user=_build_user(login="testuser", user_id=123456789))
    mock_repo.get_issues.return_value = [mock_issue]
    mock_github_dependencies.get_repo.return_value = mock_repo

    client = GitHubClient(token=None, use_env_if_none=False)
    user = client.get_issues("testowner", "testrepo")[0].author

    assert user.username == "testuser"
    assert user.display_name == "testuser"
    assert user.id == 123456789
    assert user.avatar_url is None
    assert user.is_bot is False


def test_label_contract(mock_github_dependencies):
    mock_repo = _build_repository()
    label = Mock()
    label.id = 987654321
    label.name = "bug"
    label.color = "ff0000"
    label.description = "Something isn't working"
    mock_issue = _build_issue(labels=[label])
    mock_repo.get_issues.return_value = [mock_issue]
    mock_github_dependencies.get_repo.return_value = mock_repo

    client = GitHubClient(token=None, use_env_if_none=False)
    labels = client.get_issues("testowner", "testrepo")[0].labels

    assert len(labels) == 1
    assert labels[0].name == "bug"
