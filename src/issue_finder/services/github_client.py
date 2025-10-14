"""
GitHub API client service.

This module provides a service for interacting with the GitHub API to fetch
repository and issue data with proper error handling and rate limit management.
"""

import time
from typing import List, Optional, Dict, Any, Iterator
import requests
from github import Github, GithubException, UnknownObjectException, RateLimitExceededException
from rich.console import Console

from ..models.repository import GitHubRepository
from ..models.issue import Issue, IssueState, Comment
from ..models.user import User, Label


class GitHubClient:
    """
    GitHub API client for fetching repository and issue data.

    This client handles authentication, rate limiting, pagination, and error
    handling for GitHub API interactions.
    """

    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the GitHub client.

        Args:
            auth_token: Optional GitHub personal access token for higher rate limits
        """
        self.auth_token = auth_token
        self.console = Console()

        if auth_token:
            self.github = Github(auth_token)
        else:
            self.github = Github()

        self._rate_limit_info = None

    def get_repository(self, owner: str, repo_name: str) -> GitHubRepository:
        """
        Get repository information.

        Args:
            owner: Repository owner username
            repo_name: Repository name

        Returns:
            GitHubRepository object with repository information

        Raises:
            ValueError: If repository not found or not accessible
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            return GitHubRepository(
                owner=repo.owner.login,
                name=repo.name,
                url=repo.html_url,
                api_url=repo.url,
                is_public=not repo.private,
                default_branch=repo.default_branch,
            )
        except UnknownObjectException:
            raise ValueError(f"Repository not found: {owner}/{repo_name}")
        except GithubException as e:
            raise ValueError(f"Error accessing repository: {e}")

    def get_issues(
        self,
        owner: str,
        repo_name: str,
        state: str = "all",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        since: Optional[str] = None,
    ) -> Iterator[Issue]:
        """
        Get issues from the repository with optional filtering.

        Args:
            owner: Repository owner username
            repo_name: Repository name
            state: Issue state filter ("open", "closed", "all")
            labels: Optional list of label names to filter by
            assignee: Optional assignee username to filter by
            since: Optional ISO 8601 timestamp to filter issues updated after

        Yields:
            Issue objects matching the criteria

        Raises:
            ValueError: If repository not found or API error occurs
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Build query parameters
            kwargs = {"state": state}
            if labels:
                kwargs["labels"] = labels
            if assignee:
                kwargs["assignee"] = assignee
            if since:
                kwargs["since"] = since

            # Get issues (exclude pull requests)
            issues = repo.get_issues(**kwargs)

            for issue in issues:
                # Skip pull requests
                if issue.pull_request:
                    continue

                # Convert GitHub issue to our Issue model
                yield self._convert_github_issue(issue)

        except UnknownObjectException:
            raise ValueError(f"Repository not found: {owner}/{repo_name}")
        except RateLimitExceededException as e:
            self._handle_rate_limit(e)
            raise
        except GithubException as e:
            raise ValueError(f"Error fetching issues: {e}")

    def get_comments(self, owner: str, repo_name: str, issue_number: int) -> List[Comment]:
        """
        Get comments for a specific issue.

        Args:
            owner: Repository owner username
            repo_name: Repository name
            issue_number: Issue number

        Returns:
            List of Comment objects

        Raises:
            ValueError: If issue not found or API error occurs
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            issue = repo.get_issue(issue_number)

            comments = []
            for comment in issue.get_comments():
                comments.append(self._convert_github_comment(comment, issue_number))

            return comments

        except UnknownObjectException:
            raise ValueError(f"Issue #{issue_number} not found in {owner}/{repo_name}")
        except RateLimitExceededException as e:
            self._handle_rate_limit(e)
            raise
        except GithubException as e:
            raise ValueError(f"Error fetching comments: {e}")

    def _convert_github_issue(self, github_issue) -> Issue:
        """Convert GitHub issue object to our Issue model."""
        return Issue(
            id=github_issue.id,
            number=github_issue.number,
            title=github_issue.title,
            body=github_issue.body,
            state=IssueState(github_issue.state),
            created_at=github_issue.created_at,
            updated_at=github_issue.updated_at,
            closed_at=github_issue.closed_at,
            author=self._convert_github_user(github_issue.user),
            assignees=[self._convert_github_user(assignee) for assignee in github_issue.assignees],
            labels=[label.name for label in github_issue.labels],
            comment_count=github_issue.comments,
            milestone=github_issue.milestone.title if github_issue.milestone else None,
            is_pull_request=github_issue.pull_request is not None,
        )

    def _convert_github_comment(self, github_comment, issue_id: int) -> Comment:
        """Convert GitHub comment object to our Comment model."""
        return Comment(
            id=github_comment.id,
            body=github_comment.body,
            author=self._convert_github_user(github_comment.user),
            created_at=github_comment.created_at,
            updated_at=github_comment.updated_at,
            issue_id=issue_id,
        )

    def _convert_github_user(self, github_user) -> User:
        """Convert GitHub user object to our User model."""
        return User(
            id=github_user.id,
            username=github_user.login,
            display_name=github_user.name,
            avatar_url=github_user.avatar_url,
            is_bot=github_user.type.lower() == "bot",
        )

    def _handle_rate_limit(self, exception: RateLimitExceededException) -> None:
        """
        Handle GitHub API rate limit exceeded.

        Args:
            exception: The rate limit exception
        """
        reset_time = exception.headers.get('X-RateLimit-Reset')
        if reset_time:
            reset_timestamp = int(reset_time)
            current_time = int(time.time())
            wait_time = max(reset_timestamp - current_time, 1)

            self.console.print(
                f"[yellow]⚠️  Rate limit exceeded. Waiting {wait_time} seconds...[/yellow]"
            )

            # Wait for rate limit to reset
            time.sleep(wait_time)
        else:
            self.console.print(
                "[yellow]⚠️  Rate limit exceeded. Set GITHUB_TOKEN for higher limits.[/yellow]"
            )

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit information.

        Returns:
            Dictionary with rate limit details
        """
        try:
            rate_limit = self.github.get_rate_limit()
            core = rate_limit.core

            return {
                "limit": core.limit,
                "remaining": core.remaining,
                "reset": core.reset,
                "used": core.limit - core.remaining,
            }
        except Exception:
            return {"error": "Unable to fetch rate limit information"}

    def test_connection(self) -> bool:
        """
        Test connection to GitHub API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get rate limit info as a simple test
            self.get_rate_limit_info()
            return True
        except Exception:
            return False