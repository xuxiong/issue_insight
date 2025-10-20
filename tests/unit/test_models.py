"""
Unit tests for core data models (T005-1).

These tests are written FIRST and expected to FAIL until the models are implemented.
This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

# These imports will fail initially (TDD - tests FAIL first)
from models import GitHubRepository, Issue, User, Label, Comment, IssueState


@pytest.mark.unit
class TestGitHubRepository:
    """Test GitHubRepository model validation and serialization."""

    def test_valid_repository_creation(self):
        """Test creating a valid GitHub repository model."""
        repo = GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main",
        )

        assert repo.owner == "facebook"
        assert repo.name == "react"
        assert repo.url == "https://github.com/facebook/react"
        assert repo.api_url == "https://api.github.com/repos/facebook/react"
        assert repo.is_public is True
        assert repo.default_branch == "main"

    def test_repository_serialization(self):
        """Test repository model serialization to dict."""
        repo = GitHubRepository(
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            api_url="https://api.github.com/repos/facebook/react",
            is_public=True,
            default_branch="main",
        )

        data = repo.model_dump()
        assert data["owner"] == "facebook"
        assert data["name"] == "react"
        assert data["is_public"] is True

    def test_repository_validation(self):
        """Test repository model validation for required fields."""
        # Missing required fields should fail
        with pytest.raises(ValidationError):
            GitHubRepository(owner="", name="react")

        with pytest.raises(ValidationError):
            GitHubRepository(owner="facebook", name="")


@pytest.mark.unit
class TestIssue:
    """Test Issue model with comment count validation."""

    def test_valid_issue_creation(self):
        """Test creating a valid issue model."""
        author = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        issue = Issue(
            id=987654321,
            number=42,
            title="Test Issue",
            body="This is a test issue",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=5,
            comments=[],
            is_pull_request=False,
        )

        assert issue.id == 987654321
        assert issue.number == 42
        assert issue.title == "Test Issue"
        assert issue.state == IssueState.OPEN
        assert issue.comment_count == 5
        assert issue.is_pull_request is False

    def test_issue_comment_count_validation(self):
        """Test comment count validation."""
        author = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        # Valid comment counts
        for count in [0, 1, 5, 10, 100]:
            issue = Issue(
                id=987654321,
                number=42,
                title="Test Issue",
                body="This is a test issue",
                state=IssueState.OPEN,
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                updated_at=datetime(2024, 1, 16, 14, 20, 0),
                closed_at=None,
                author=author,
                assignees=[],
                labels=[],
                comment_count=count,
                comments=[],
                is_pull_request=False,
            )
            assert issue.comment_count == count

    def test_issue_state_enum(self):
        """Test IssueState enum values."""
        assert IssueState.OPEN == "open"
        assert IssueState.CLOSED == "closed"


@pytest.mark.unit
class TestUser:
    """Test User model validation."""

    def test_valid_user_creation(self):
        """Test creating a valid user model."""
        user = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        assert user.id == 123456
        assert user.username == "contributor1"
        assert user.display_name == "Contributor One"
        assert user.avatar_url == "https://github.com/contributor1.png"
        assert user.is_bot is False

    def test_user_defaults(self):
        """Test user model default values."""
        user = User(
            id=123456,
            username="contributor1",
            display_name=None,
            avatar_url="https://github.com/contributor1.png",
        )

        assert user.is_bot is False  # Default should be False

    def test_bot_user(self):
        """Test creating a bot user."""
        user = User(
            id=123456,
            username="github-actions[bot]",
            display_name="GitHub Actions",
            avatar_url="https://github.com/bot.png",
            is_bot=True,
        )

        assert user.is_bot is True


@pytest.mark.unit
class TestLabel:
    """Test Label model validation."""

    def test_valid_label_creation(self):
        """Test creating a valid label model."""
        label = Label(
            id=123,
            name="enhancement",
            color="a2eeef",
            description="New feature or request",
        )

        assert label.id == 123
        assert label.name == "enhancement"
        assert label.color == "a2eeef"
        assert label.description == "New feature or request"

    def test_label_optional_description(self):
        """Test label with optional description."""
        label = Label(id=123, name="bug", color="ff0000", description=None)

        assert label.description is None


@pytest.mark.unit
class TestComment:
    """Test Comment model validation."""

    def test_valid_comment_creation(self):
        """Test creating a valid comment model."""
        author = User(
            id=123456,
            username="commenter1",
            display_name="Commenter One",
            avatar_url="https://github.com/commenter1.png",
            is_bot=False,
        )

        comment = Comment(
            id=987654321,
            body="This is a test comment",
            author=author,
            created_at=datetime(2024, 1, 15, 11, 0, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
            issue_id=42,
        )

        assert comment.id == 987654321
        assert comment.body == "This is a test comment"
        assert comment.author.username == "commenter1"
        assert comment.issue_id == 42

    def test_comment_with_empty_body(self):
        """Test comment with empty body (edge case)."""
        author = User(
            id=123456,
            username="commenter1",
            display_name="Commenter One",
            avatar_url="https://github.com/commenter1.png",
            is_bot=False,
        )

        comment = Comment(
            id=987654321,
            body="",
            author=author,
            created_at=datetime(2024, 1, 15, 11, 0, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
            issue_id=42,
        )

        assert comment.body == ""


@pytest.mark.unit
class TestModelRelationships:
    """Test relationships between models."""

    def test_issue_author_relationship(self):
        """Test issue-author relationship."""
        author = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        issue = Issue(
            id=987654321,
            number=42,
            title="Test Issue",
            body="This is a test issue",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=3,
            comments=[],
            is_pull_request=False,
        )

        assert issue.author.username == "contributor1"
        assert issue.author.id == 123456

    def test_issue_label_relationship(self):
        """Test issue-label relationship."""
        label = Label(
            id=123,
            name="enhancement",
            color="a2eeef",
            description="New feature or request",
        )

        author = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        issue = Issue(
            id=987654321,
            number=42,
            title="Test Issue",
            body="This is a test issue",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[label],
            comment_count=3,
            comments=[],
            is_pull_request=False,
        )

        assert len(issue.labels) == 1
        assert issue.labels[0].name == "enhancement"
        assert issue.labels[0].color == "a2eeef"

    def test_issue_comment_relationship(self):
        """Test issue-comment relationship."""
        author = User(
            id=123456,
            username="contributor1",
            display_name="Contributor One",
            avatar_url="https://github.com/contributor1.png",
            is_bot=False,
        )

        commenter = User(
            id=654321,
            username="commenter1",
            display_name="Commenter One",
            avatar_url="https://github.com/commenter1.png",
            is_bot=False,
        )

        comment = Comment(
            id=987654321,
            body="This is a test comment",
            author=commenter,
            created_at=datetime(2024, 1, 15, 11, 0, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
            issue_id=42,
        )

        issue = Issue(
            id=987654321,
            number=42,
            title="Test Issue",
            body="This is a test issue",
            state=IssueState.OPEN,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 16, 14, 20, 0),
            closed_at=None,
            author=author,
            assignees=[],
            labels=[],
            comment_count=1,
            comments=[comment],
            is_pull_request=False,
        )

        assert len(issue.comments) == 1
        assert issue.comments[0].author.username == "commenter1"
        assert issue.comments[0].issue_id == 42
