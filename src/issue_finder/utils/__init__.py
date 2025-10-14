"""
Utility functions for GitHub issue analysis.

This module contains utilities for input validation, authentication handling,
progress tracking, and other common functionality.
"""

from .validation import validate_repository_url, validate_filters
from .auth import get_auth_token
from .progress import ProgressTracker
from .errors import (
    IssueAnalyzerError,
    RepositoryNotFoundError,
    InvalidURLError,
    ValidationError,
    GitHubAPIError,
    RateLimitError,
    AuthenticationError,
    FilterError,
    OutputFormatError,
    CommentRetrievalError,
    MetricsCalculationError,
)

__all__ = [
    "validate_repository_url",
    "validate_filters",
    "get_auth_token",
    "ProgressTracker",
    "IssueAnalyzerError",
    "RepositoryNotFoundError",
    "InvalidURLError",
    "ValidationError",
    "GitHubAPIError",
    "RateLimitError",
    "AuthenticationError",
    "FilterError",
    "OutputFormatError",
    "CommentRetrievalError",
    "MetricsCalculationError",
]