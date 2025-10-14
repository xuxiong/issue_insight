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
from ..models.metrics import FilterCriteria


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
        assignees: Optional[List[str]] = None,
        created_since: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_since: Optional[str] = None,
        updated_until: Optional[str] = None,
        page_size: int = 100,
    ) -> Iterator[Issue]:
        """
        Get issues from the repository with optional filtering.

        Args:
            owner: Repository owner username
            repo_name: Repository name
            state: Issue state filter ("open", "closed", "all")
            labels: Optional list of label names to filter by
            assignees: Optional list of assignee usernames to filter by
            created_since: Filter issues created on or after this date (ISO 8601)
            created_until: Filter issues created on or before this date (ISO 8601)
            updated_since: Filter issues updated on or after this date (ISO 8601)
            updated_until: Filter issues updated on or before this date (ISO 8601)
            page_size: Number of issues per page for pagination (default: 100)

        Yields:
            Issue objects matching the criteria

        Raises:
            ValueError: If repository not found or API error occurs
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Build query parameters for GitHub API (server-side filtering)
            kwargs = {"state": state}

            # GitHub API supports labels filtering
            if labels:
                kwargs["labels"] = labels

            # GitHub API only supports single assignee, so we'll handle multiple assignees client-side
            # For now, use the first assignee if provided
            if assignees and len(assignees) > 0:
                kwargs["assignee"] = assignees[0]

            # GitHub API supports 'since' parameter for updated date filtering
            # We'll use updated_since if provided, otherwise created_since
            if updated_since:
                kwargs["since"] = updated_since
            elif created_since:
                kwargs["since"] = created_since

            # Get issues from GitHub API
            issues = repo.get_issues(**kwargs)

            # Apply client-side filtering for parameters not supported by GitHub API
            for issue in issues:
                # Convert GitHub issue to our Issue model
                issue_obj = self._convert_github_issue(issue)

                # Skip pull requests
                if issue_obj.is_pull_request:
                    continue

                # Apply client-side date filtering
                if created_since:
                    # Convert string to datetime for comparison
                    from datetime import datetime
                    created_since_dt = datetime.fromisoformat(created_since.replace('Z', '+00:00'))
                    if issue_obj.created_at < created_since_dt:
                        continue

                if created_until:
                    created_until_dt = datetime.fromisoformat(created_until.replace('Z', '+00:00'))
                    if issue_obj.created_at > created_until_dt:
                        continue

                if updated_since:
                    updated_since_dt = datetime.fromisoformat(updated_since.replace('Z', '+00:00'))
                    if issue_obj.updated_at < updated_since_dt:
                        continue

                if updated_until:
                    updated_until_dt = datetime.fromisoformat(updated_until.replace('Z', '+00:00'))
                    if issue_obj.updated_at > updated_until_dt:
                        continue

                # Handle multiple assignees (GitHub API only supports single assignee)
                if assignees and len(assignees) > 1:
                    assignee_usernames = [assignee.username for assignee in issue_obj.assignees]
                    if not any(assignee in assignee_usernames for assignee in assignees):
                        continue

                yield issue_obj

        except UnknownObjectException:
            raise ValueError(f"Repository not found: {owner}/{repo_name}")
        except RateLimitExceededException as e:
            self._handle_rate_limit(e)
            raise
        except GithubException as e:
            raise ValueError(f"Error fetching issues: {e}")

    def get_issues_by_criteria(self, owner: str, repo_name: str, criteria: 'FilterCriteria') -> Iterator[Issue]:
        """
        Get issues from the repository using FilterCriteria object.

        Args:
            owner: Repository owner username
            repo_name: Repository name
            criteria: FilterCriteria object with all filtering parameters

        Yields:
            Issue objects matching the criteria

        Raises:
            ValueError: If repository not found or API error occurs
        """
        from datetime import datetime

        # Convert datetime objects to ISO format strings for API calls
        created_since_str = criteria.created_since.isoformat() if criteria.created_since else None
        created_until_str = criteria.created_until.isoformat() if criteria.created_until else None
        updated_since_str = criteria.updated_since.isoformat() if criteria.updated_since else None
        updated_until_str = criteria.updated_until.isoformat() if criteria.updated_until else None

        # Call the main get_issues method with converted parameters
        issues = self.get_issues(
            owner=owner,
            repo_name=repo_name,
            state=criteria.state or "all",
            labels=criteria.labels if criteria.labels else None,
            assignees=criteria.assignees if criteria.assignees else None,
            created_since=created_since_str,
            created_until=created_until_str,
            updated_since=updated_since_str,
            updated_until=updated_until_str,
            page_size=criteria.page_size,
        )

        # Apply comment count filtering (client-side only, as GitHub API doesn't support it)
        for issue in issues:
            if criteria.min_comments is not None and issue.comment_count < criteria.min_comments:
                continue
            if criteria.max_comments is not None and issue.comment_count > criteria.max_comments:
                continue
            yield issue

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
        # Use a heuristic to determine if this is a pull request without additional API calls
        # Pull requests typically have a different URL structure and different raw data
        is_pull_request = False

        # Check if the issue URL contains '/pull/' (this is available in the raw data)
        try:
            if hasattr(github_issue, 'raw_data'):
                html_url = github_issue.raw_data.get('html_url', '')
                if '/pull/' in html_url:
                    is_pull_request = True
        except:
            # Fallback - assume it's an issue if we can't check
            pass

        # Use safe attribute access to avoid additional API calls
        try:
            # Try to access raw data directly when possible
            if hasattr(github_issue, 'raw_data'):
                raw_data = github_issue.raw_data
                user_data = raw_data.get('user', {})
                milestone_data = raw_data.get('milestone', {})

                author = User(
                    id=user_data.get('id', 0),
                    username=user_data.get('login', 'unknown'),
                    display_name=user_data.get('name'),
                    avatar_url=user_data.get('avatar_url', ''),
                    is_bot=user_data.get('type', '').lower() == 'bot',
                )

                milestone_title = milestone_data.get('title') if milestone_data else None

                # Handle labels from raw data
                labels = []
                for label_data in raw_data.get('labels', []):
                    if isinstance(label_data, dict):
                        labels.append(label_data.get('name', ''))

                # Handle assignees from raw data
                assignees = []
                for assignee_data in raw_data.get('assignees', []):
                    if isinstance(assignee_data, dict):
                        assignees.append(User(
                            id=assignee_data.get('id', 0),
                            username=assignee_data.get('login', 'unknown'),
                            display_name=assignee_data.get('name'),
                            avatar_url=assignee_data.get('avatar_url', ''),
                            is_bot=assignee_data.get('type', '').lower() == 'bot',
                        ))
            else:
                # Fallback to direct attribute access (may trigger API calls)
                author = self._convert_github_user(github_issue.user)
                assignees = [self._convert_github_user(assignee) for assignee in github_issue.assignees]
                labels=[label.name for label in github_issue.labels]
                milestone=github_issue.milestone.title if github_issue.milestone else None

        except Exception as e:
            # If anything fails, use minimal safe values
            print(f"Warning: Error processing issue {github_issue.number}: {e}")
            author = User(id=0, username='unknown', display_name=None, avatar_url='', is_bot=False)
            assignees = []
            labels = []
            milestone_title = None

        return Issue(
            id=github_issue.id,
            number=github_issue.number,
            title=github_issue.title,
            body=github_issue.body,
            state=IssueState(github_issue.state),
            created_at=github_issue.created_at,
            updated_at=github_issue.updated_at,
            closed_at=github_issue.closed_at,
            author=author,
            assignees=assignees,
            labels=labels,
            comment_count=github_issue.comments,
            milestone=milestone_title,
            is_pull_request=is_pull_request,
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