"""
GitHub API client for fetching repository and issue data.

This module provides a high-level interface to the GitHub API using PyGithub,
with specific functionality for the GitHub Project Activity Analyzer.
"""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from github import Github, GithubException, UnknownObjectException, RateLimitExceededException
from github.Repository import Repository as GithubRepository
from github.Issue import Issue as GithubIssue
from github.NamedUser import NamedUser

from models import GitHubRepository, Issue, User, Label, Comment, IssueState

# Set up logger
logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub client for repository and issue data retrieval."""

    # Sentinel to distinguish between "no argument provided" and "explicitly None"
    _NO_TOKEN_PROVIDED = object()

    def __init__(self, token=_NO_TOKEN_PROVIDED, use_env_if_none: bool = True):
        """
        Initialize GitHub client with optional authentication token.

        Args:
            token: GitHub personal access token for higher rate limits
            use_env_if_none: Whether to use environment variable if token is not explicitly provided (default: True)
        """
        # Handle token logic using sentinel to distinguish cases
        if token is self._NO_TOKEN_PROVIDED:
            # No token argument provided at all - use environment if allowed
            self.token = os.getenv("GITHUB_TOKEN") if use_env_if_none else None
        elif token is None:
            # Explicitly None provided - don't use environment
            self.token = None
        else:
            # Explicit token provided (even if empty string)
            self.token = token if token else None

        # Create client with proper authentication
        if self.token:
            import github
            self.client = Github(auth=github.Auth.Token(self.token))
        else:
            self.client = Github()

    def get_repository(self, repository_url: str) -> GitHubRepository:
        """
        Get repository information from GitHub URL.

        Args:
            repository_url: Full GitHub repository URL

        Returns:
            GitHubRepository object with repository metadata

        Raises:
            ValueError: If URL format is invalid or repository not found
            GithubException: For API errors
        """
        logger.debug(f"Parsing repository URL: {repository_url}")
        # Validate URL format
        parsed = self._parse_github_url(repository_url)
        repo_full_name = f"{parsed['owner']}/{parsed['repo']}"
        logger.info(f"Fetching repository info for: {repo_full_name}")

        try:
            repo = self.client.get_repo(repo_full_name)
            logger.info(f"Successfully fetched repository: {repo_full_name}")
        except UnknownObjectException as e:
            logger.error(f"Repository not found: {repo_full_name}")
            raise ValueError("Repository not found or inaccessible. Verify URL and ensure repository is public. Check spelling and try again.") from e
        except GithubException as e:
            logger.error(f"GitHub API error fetching repository {repo_full_name}: {e}")
            raise e

        # Check if repository is private (not supported)
        if repo.private:
            logger.warning(f"Attempted to access private repository: {repo_full_name}")
            raise ValueError("Private repositories are not supported. This tool only analyzes public repositories. Use a public repository or consider using GitHub's built-in search for private repositories.")

        logger.debug(f"Repository metadata - owner: {repo.owner.login}, name: {repo.name}, public: {not repo.private}")
        return GitHubRepository(
            owner=repo.owner.login,
            name=repo.name,
            url=repo.html_url,
            api_url=repo.url,
            is_public=not repo.private,
            default_branch=repo.default_branch
        )

    def get_issues(self, owner: str, repo: str, state: str = "all", limit: Optional[int] = None) -> List[Issue]:
        """
        Get issues for a repository (excluding pull requests).

        Args:
            owner: Repository owner username
            repo: Repository name
            state: Issue state filter ('open', 'closed', 'all')
            limit: Maximum number of issues to fetch (default: None for all)

        Returns:
            List of Issue objects

        Raises:
            GithubException: For API errors
            RateLimitExceededException: If rate limit is exceeded
        """
        # Check rate limits before making API calls
        self.check_and_handle_rate_limit()

        try:
            github_repo = self.client.get_repo(f"{owner}/{repo}")

            # Use iterator approach to avoid loading everything into memory at once
            issue_iterator = github_repo.get_issues(state=state, sort="created", direction="desc")

            if limit is None:
                # No limit specified: this will potentially fetch ALL issues.
                # Be careful - this could result in many API calls and high rate limit usage.
                logger.warning("Fetching all issues without limit - this may consume significant API quota")
                issues = []
                for github_issue in issue_iterator:
                    # Skip pull requests (early filtering to potentially save API calls)
                    if github_issue.pull_request is not None:
                        continue
                    issues.append(self._convert_issue(github_issue))
            else:
                # With limit: collect enough items to satisfy the limit after PR filtering
                # Use a more conservative approach with iterator
                buffer_size = min(limit + 20, limit * 1.5, 200)  # More generous buffer for PR filtering
                buffer_size = int(max(buffer_size, limit))

                # Collect issues until we have enough buffer
                raw_issues = []
                for github_issue in issue_iterator:
                    raw_issues.append(github_issue)
                    if len(raw_issues) >= buffer_size:
                        break

                # Filter PRs and apply final limit
                github_issues_filtered = [gi for gi in raw_issues if gi.pull_request is None][:limit]
                issues = [self._convert_issue(gi) for gi in github_issues_filtered]

        except GithubException as e:
            raise e

        return issues

    def get_rate_limit_info(self) -> Optional[Dict[str, int]]:
        """
        Get current GitHub API rate limit information.

        Returns:
            Dictionary with rate limit info or None if unavailable
        """
        try:
            rate_limit = self.client.get_rate_limit()
            return {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset,
            }
        except Exception:
            return None

    def _parse_github_url(self, url: str) -> Dict[str, str]:
        """
        Parse GitHub repository URL to extract owner and repo name.

        Args:
            url: GitHub repository URL

        Returns:
            Dictionary with 'owner' and 'repo' keys

        Raises:
            ValueError: If URL format is invalid
        """
        # Regex pattern for GitHub URLs
        pattern = r'^https?://github\.com/([^/]+)/([^/]+)(?:/?|/.*)$'
        match = re.match(pattern, url)

        if not match:
            raise ValueError("Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react")

        owner, repo = match.groups()
        return {"owner": owner, "repo": repo}

    def _convert_user(self, github_user: NamedUser) -> User:
        """Convert GitHub user to our User model."""
        return User(
            id=github_user.id,
            username=github_user.login,
            display_name=github_user.login,  # 使用 username 作为 display_name
            avatar_url=None,    # 避免触发额外 API 调用
            is_bot=github_user.type.lower() == "bot"
        )

    def _convert_label(self, github_label) -> Label:
        """Convert GitHub label to our Label model."""
        return Label(
            id=github_label.id,
            name=github_label.name,
            color=github_label.color,
            description=github_label.description
        )

    def _convert_issue(self, github_issue: GithubIssue) -> Issue:
        """Convert GitHub issue to our Issue model."""
        # Convert author (avoid additional API calls - use available data only)
        author = User(
            id=github_issue.user.id,
            username=github_issue.user.login,
            display_name=github_issue.user.login,  # 使用 username 作为 display_name
            avatar_url=None,    # 避免触发额外 API 调用
            is_bot=github_issue.user.type.lower() == "bot"
        )

        # Convert assignees (avoid additional API calls - use available data only)
        assignees = [
            User(
                id=assignee.id,
                username=assignee.login,
                display_name=assignee.login,  # 使用 username 作为 display_name
                avatar_url=None,    # 避免触发额外 API 调用
                is_bot=assignee.type.lower() == "bot"
            )
            for assignee in github_issue.assignees
        ]

        # Convert labels
        labels = [self._convert_label(label) for label in github_issue.labels]

        # Get comment count (GitHub API provides this)
        comment_count = github_issue.comments

        # Parse dates
        created_at = github_issue.created_at
        updated_at = github_issue.updated_at
        closed_at = github_issue.closed_at

        # Create issue object
        issue = Issue(
            id=github_issue.id,
            number=github_issue.number,
            title=github_issue.title,
            body=github_issue.body,
            state=IssueState(github_issue.state),
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
            author=author,
            assignees=assignees,
            labels=labels,
            comment_count=comment_count,
            comments=[],
            is_pull_request=github_issue.pull_request is not None
        )

        return issue

    def check_and_handle_rate_limit(self) -> None:
        """
        Check rate limits and provide warnings if needed.

        Raises:
            RateLimitExceededException: If rate limit is exceeded
        """
        rate_limit_info = self.get_rate_limit_info()
        if not rate_limit_info:
            return

        remaining = rate_limit_info["remaining"]
        limit = rate_limit_info["limit"]

        # Warn if rate limit is getting low
        if remaining < limit * 0.1:  # Less than 10% remaining
            import warnings
            reset_time = datetime.fromtimestamp(rate_limit_info["reset"])
            wait_time = max(0, (reset_time - datetime.now()).total_seconds() / 60)
            warnings.warn(
                f"GitHub API rate limit warning: {remaining}/{limit} requests remaining. "
                f"Resets in {wait_time:.1f} minutes."
            )

        # Error if rate limit is exceeded
        if remaining == 0:
            raise RateLimitExceededException(
                status=403,
                data={
                    "message": "GitHub API rate limit exceeded",
                    "retry_after": int(max(0, (datetime.fromtimestamp(rate_limit_info["reset"]) - datetime.now()).total_seconds()))
                }
            )

    def get_comments_for_issue(self, owner: str, repo: str, issue_number: int) -> List[Comment]:
        """
        Get all comments for a specific issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            List of Comment objects

        Raises:
            RateLimitExceededException: If rate limit is exceeded
        """
        # Check rate limits before making API calls
        self.check_and_handle_rate_limit()

        try:
            github_repo = self.client.get_repo(f"{owner}/{repo}")
            github_issue = github_repo.get_issue(issue_number)
            github_comments = github_issue.get_comments()

            comments = []
            for github_comment in github_comments:
                # Convert author (avoid additional API calls - use available data only)
                author = User(
                    id=github_comment.user.id,
                    username=github_comment.user.login,
                    display_name=github_comment.user.login,  # 使用 username 作为 display_name
                    avatar_url=None,    # 避免触发额外 API 调用
                    is_bot=github_comment.user.type.lower() == "bot"
                )
                comment = Comment(
                    id=github_comment.id,
                    body=github_comment.body,
                    author=author,
                    created_at=github_comment.created_at,
                    updated_at=github_comment.updated_at,
                    issue_id=github_issue.number
                )
                comments.append(comment)

        except GithubException as e:
            # Return empty list if comments can't be retrieved, don't fail the whole analysis
            return []

        return comments
