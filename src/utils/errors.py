"""
Custom exceptions for GitHub issue analysis.

This module provides structured error handling with proper error messages,
following the specification from the project documentation.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


class IssueFinderError(Exception):
    """Base class for all GitHub issue analyzer errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        self._message = message
        self.context = context or {}
        self.cause = cause
        self.logging_context: Dict[str, Any] = {}
        super().__init__(message)

    @classmethod
    def _get_default_error_code(cls, instance) -> str:
        """Generate default error code from class name."""
        return instance.__class__.__name__.upper()

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message


class GitHubAnalyzerError(IssueFinderError):
    """Alias for IssueFinderError to match test expectations."""
    pass


class RepositoryNotFoundError(GitHubAnalyzerError):
    """Error when a repository cannot be found or accessed."""

    def __init__(self, repository_url: str, suggestions: Optional[List[str]] = None):
        self.repository_url = repository_url
        self.suggestions = suggestions or []
        self.error_code = "REPOSITORY_NOT_FOUND"

        message = "Repository not found or inaccessible. Verify URL and ensure repository is public. Check spelling and try again."
        super().__init__(message, {"repository_url": repository_url})

    @classmethod
    def from_github_exception(cls, github_exception: Exception, repository_url: str) -> 'RepositoryNotFoundError':
        """Create error from GitHub API exception."""
        return cls(repository_url)


class PrivateRepositoryError(GitHubAnalyzerError, ValueError):
    """Error when trying to access a private repository."""

    def __init__(self, repository_url: str, alternatives: Optional[List[str]] = None):
        self.repository_url = repository_url
        self.alternatives = alternatives or []
        self.error_code = "PRIVATE_REPOSITORY"

        message = "Private repositories are not supported. This tool only analyzes public repositories. Use a public repository or consider using GitHub's built-in search for private repositories."
        super().__init__(message, {"repository_url": repository_url})


class ValidationError(GitHubAnalyzerError):
    """Error for input validation failures."""

    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        self.error_code = "VALIDATION_ERROR"

        message = f"Invalid {field}: {value}. {reason}."
        super().__init__(message, {"field": field, "value": value})

    @classmethod
    def invalid_url(cls, url: str) -> 'ValidationError':
        """Factory method for URL validation errors."""
        return cls(
            "repository_url",
            url,
            "Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react"
        )

    @classmethod
    def invalid_comment_count(cls, count: int) -> 'ValidationError':
        """Factory method for comment count validation errors."""
        return cls(
            "min_comments",
            count,
            f"Invalid comment count: {count}. Comment count must be non-negative integer. Use --min-comments 0 or higher."
        )

    @classmethod
    def invalid_limit(cls, limit: int) -> 'ValidationError':
        """Factory method for limit validation errors."""
        return cls(
            "limit",
            limit,
            f"Invalid limit: {limit}. Limit must be a positive integer. Use --limit 100 or higher."
        )


class GitHubAPIError(GitHubAnalyzerError):
    """Error for GitHub API related issues."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None):
        self._status_code = status_code
        self.response_data = response_data or {}
        self.error_code = "GITHUB_API_ERROR"

        if status_code:
            full_message = f"GitHub API Error ({status_code}): {message}"
        else:
            full_message = f"GitHub API Error: {message}"

        super().__init__(full_message, {"status_code": status_code})

    @classmethod
    def from_github_exception(cls, github_exception: Exception,
                            status_code: int, response_data: Optional[Dict[str, Any]] = None) -> 'GitHubAPIError':
        """Create error from GitHub exception."""
        return cls(str(github_exception), status_code, response_data)

    @property
    def retry_after(self) -> Optional[int]:
        """Get retry-after seconds if available."""
        return self.response_data.get("retry_after")


class APIError(GitHubAPIError):
    """Alias for GitHubAPIError to match test expectations."""

    def __init__(self, status_code: int, message: str, response_data: Optional[Dict[str, Any]] = None,
                 retry_after: Optional[int] = None):
        # Store retry_after in response_data for the parent property to access
        if retry_after is not None:
            response_data = response_data or {}
            response_data = {**response_data, "retry_after": retry_after}

        # Store original values for test access
        self._message = message
        self._status_code = status_code

        # Initialize response_data and other attributes manually
        self.response_data = response_data or {}
        self.error_code = "GITHUB_API_ERROR"
        self.context = {"status_code": status_code}

        # Call Exception.__init__ directly to avoid parent's message prefixing
        Exception.__init__(self, message)

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """Get the original message."""
        return self._message

    @property
    def status_code(self) -> int:
        """Get the status code."""
        return self._status_code

    @classmethod
    def from_github_exception(cls, github_exception: Exception,
                            status_code: int, response_data: Optional[Dict[str, Any]] = None) -> 'APIError':
        """Create error from GitHub exception."""
        return cls(status_code, str(github_exception), response_data)


class AuthenticationError(GitHubAnalyzerError):
    """Error for authentication failures."""

    def __init__(self, token_status: str, reason: str, help_text: Optional[str] = None):
        self.token_status = token_status
        self.reason = reason
        self.help_text = help_text
        self.error_code = "AUTHENTICATION_ERROR"

        message = f"GitHub authentication failed: {reason}. Please check your token or environment variable."
        super().__init__(message, {"token_status": token_status, "reason": reason})


class NetworkError(GitHubAnalyzerError):
    """Error for network-related issues."""

    def __init__(self, original_error: Exception, url: str, timeout: Optional[int] = None,
                 can_retry: bool = False, max_retries: int = 0):
        self.original_error = original_error
        self.url = url
        self.timeout = timeout
        self.can_retry = can_retry
        self.max_retries = max_retries
        self.error_code = "NETWORK_ERROR"

        message = f"Network error accessing GitHub API: {original_error}"
        super().__init__(message, {"url": url, "timeout": timeout}, cause=original_error)


class RateLimitError(GitHubAPIError):
    """Error for GitHub API rate limit exceeded."""

    def __init__(self, remaining: int, reset_time: float, limit: int, suggestions: Optional[List[str]] = None):
        self.remaining = remaining
        self.reset_time = reset_time
        self.limit = limit
        self.suggestions = suggestions or []
        self.error_code = "RATE_LIMIT_EXCEEDED"

        message = "GitHub API rate limit exceeded. Wait 60 seconds or use authentication token for higher limits. Set GITHUB_TOKEN environment variable or use --token flag."
        super().__init__(message, 429, {"remaining": remaining, "reset_time": reset_time, "limit": limit})

    def get_wait_seconds(self) -> int:
        """Calculate wait seconds until reset."""
        current_time = time.time()
        return max(0, int(self.reset_time - current_time))

    def get_wait_minutes(self) -> float:
        """Calculate wait minutes until reset."""
        return self.get_wait_seconds() / 60

    @classmethod
    def from_limits(cls, remaining: int, reset_time: float, limit: int) -> 'RateLimitError':
        """Factory method from rate limit values."""
        return cls(remaining, reset_time, limit)


class ConfigurationError(GitHubAnalyzerError):
    """Error for configuration issues."""
    pass
