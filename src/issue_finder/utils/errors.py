"""
Custom error classes for the issue analyzer.

This module defines custom exception classes for different types of errors
that can occur during issue analysis operations.
"""


class IssueAnalyzerError(Exception):
    """Base exception for all issue analyzer errors."""
    pass


class RepositoryNotFoundError(IssueAnalyzerError):
    """Raised when a GitHub repository is not found or not accessible."""
    pass


class InvalidURLError(IssueAnalyzerError):
    """Raised when a repository URL format is invalid."""
    pass


class ValidationError(IssueAnalyzerError):
    """Raised when input validation fails."""
    pass


class GitHubAPIError(IssueAnalyzerError):
    """Raised when GitHub API operations fail."""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class AuthenticationError(GitHubAPIError):
    """Raised when GitHub authentication fails."""
    pass


class FilterError(ValidationError):
    """Raised when filter parameters are invalid."""
    pass


class OutputFormatError(ValidationError):
    """Raised when output format is invalid."""
    pass


class CommentRetrievalError(IssueAnalyzerError):
    """Raised when comment retrieval fails for specific issues."""
    pass


class MetricsCalculationError(IssueAnalyzerError):
    """Raised when metrics calculation fails."""
    pass