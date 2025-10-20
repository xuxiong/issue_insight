"""
Unit tests for comment retrieval functionality in GitHubClient.

Tests the get_comments_for_issue method and comment fetching logic.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from services.github_client import GitHubClient
from models import Comment, User


class TestCommentRetrieval:
    """Test comment retrieval functionality in GitHubClient."""

    def test_get_comments_for_issue_success(self):
        """Test successful comment retrieval with mock GitHub API."""
        # Create mock GitHub API objects
        mock_github_comment1 = Mock()
        mock_github_comment1.id = 123
        mock_github_comment1.body = "This is a great feature!"
        mock_github_comment1.user.id = 456
        mock_github_comment1.user.login = "dev-user"
        mock_github_comment1.user.type = "User"
        mock_github_comment1.created_at = datetime(2023, 1, 1, 10, 0, 0)
        mock_github_comment1.updated_at = datetime(2023, 1, 1, 10, 0, 0)

        mock_github_comment2 = Mock()
        mock_github_comment2.id = 124
        mock_github_comment2.body = "I agree, this will help many users."
        mock_github_comment2.user.id = 789
        mock_github_comment2.user.login = "tester-user"
        mock_github_comment2.user.type = "User"
        mock_github_comment2.created_at = datetime(2023, 1, 2, 14, 30, 0)
        mock_github_comment2.updated_at = datetime(2023, 1, 2, 14, 30, 0)

        mock_issue = Mock()
        mock_issue.get_comments.return_value = [
            mock_github_comment1,
            mock_github_comment2,
        ]

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        # Create GitHubClient and mock its client attribute
        client = GitHubClient(token=None)
        client.client = Mock()
        client.client.get_repo.return_value = mock_repo
        # Mock rate limit check to avoid mock issues
        client.get_rate_limit_info = Mock(
            return_value={"limit": 5000, "remaining": 4000, "reset": 0}
        )

        # Call the method
        comments = client.get_comments_for_issue("owner", "repo", 1)

        # Verify results
        assert len(comments) == 2

        # Check first comment
        assert comments[0].id == 123
        assert comments[0].body == "This is a great feature!"
        assert comments[0].author.username == "dev-user"
        assert comments[0].author.is_bot == False
        assert comments[0].created_at == datetime(2023, 1, 1, 10, 0, 0)
        assert comments[0].updated_at == datetime(2023, 1, 1, 10, 0, 0)
        assert comments[0].issue_id == 1

        # Check second comment
        assert comments[1].id == 124
        assert comments[1].body == "I agree, this will help many users."
        assert comments[1].author.username == "tester-user"
        assert comments[1].issue_id == 1

    def test_get_comments_for_issue_with_bot(self):
        """Test comment retrieval includes bot users."""
        mock_github_comment = Mock()
        mock_github_comment.id = 125
        mock_github_comment.body = "Build completed successfully!"
        mock_github_comment.user.id = 101
        mock_github_comment.user.login = "build-bot"
        mock_github_comment.user.type = "Bot"
        mock_github_comment.created_at = datetime(2023, 1, 3, 9, 15, 0)
        mock_github_comment.updated_at = datetime(2023, 1, 3, 9, 15, 0)

        mock_issue = Mock()
        mock_issue.get_comments.return_value = [mock_github_comment]

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        client = GitHubClient(token=None)
        client.client = Mock()
        client.client.get_repo.return_value = mock_repo
        client.get_rate_limit_info = Mock(
            return_value={"limit": 5000, "remaining": 4000, "reset": 0}
        )

        comments = client.get_comments_for_issue("owner", "repo", 1)

        assert len(comments) == 1
        assert comments[0].author.is_bot == True
        assert comments[0].author.username == "build-bot"

    def test_get_comments_for_issue_api_failure(self):
        """Test that comment retrieval handles API failures gracefully."""
        mock_repo = Mock()
        mock_repo.get_issue.side_effect = Exception("API Error")

        with patch("github.Github") as mock_gh_class:
            mock_client = Mock()
            mock_gh_class.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo

            client = GitHubClient(token=None)
            comments = client.get_comments_for_issue("owner", "repo", 1)

            # Should return empty list on failure
            assert comments == []

    def test_get_comments_for_issue_empty(self):
        """Test comment retrieval for issues with no comments."""
        mock_issue = Mock()
        mock_issue.get_comments.return_value = []  # No comments

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        with patch("github.Github") as mock_gh_class:
            mock_client = Mock()
            mock_gh_class.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo

            client = GitHubClient(token=None)
            comments = client.get_comments_for_issue("owner", "repo", 1)

            assert comments == []

    def test_get_comments_for_issue_pagination(self):
        """Test comment retrieval handles pagination (multiple pages of comments)."""
        # Create more comments than PyGitHub's page size might handle
        github_comments = []
        for i in range(5):  # Simulate 5 comments across potentially multiple pages
            mock_comment = Mock()
            mock_comment.id = 200 + i
            mock_comment.body = f"Comment {i + 1} content"
            mock_comment.user.id = 100 + i
            mock_comment.user.login = f"user{i}"
            mock_comment.user.type = "User"
            mock_comment.created_at = datetime(2023, 1, 1, 10 + i, 0, 0)
            mock_comment.updated_at = datetime(2023, 1, 1, 10 + i, 0, 0)
            github_comments.append(mock_comment)

        mock_issue = Mock()
        mock_issue.get_comments.return_value = github_comments

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        client = GitHubClient(token=None)
        client.client = Mock()
        client.client.get_repo.return_value = mock_repo
        client.get_rate_limit_info = Mock(
            return_value={"limit": 5000, "remaining": 4000, "reset": 0}
        )

        comments = client.get_comments_for_issue("owner", "repo", 1)

        # Should return all comments regardless of pagination
        assert len(comments) == 5
        assert all(comment.issue_id == 1 for comment in comments)
