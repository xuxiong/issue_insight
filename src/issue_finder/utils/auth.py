"""
Authentication handling utilities.

This module provides functions for handling GitHub authentication tokens
from environment variables and command-line arguments.
"""

import os
from typing import Optional


def get_auth_token() -> Optional[str]:
    """
    Get GitHub authentication token from environment variable.

    Returns:
        GitHub personal access token if available, None otherwise
    """
    return os.getenv("GITHUB_TOKEN")


def validate_token_format(token: str) -> bool:
    """
    Validate that a token appears to be in the correct format.

    Args:
        token: GitHub token to validate

    Returns:
        True if token format looks valid, False otherwise
    """
    # GitHub tokens start with "ghp_" or "github_pat_"
    return (
        token.startswith("ghp_") and len(token) == 40
    ) or (
        token.startswith("github_pat_") and len(token) > 40
    )


def mask_token(token: str) -> str:
    """
    Mask a token for safe logging/display.

    Args:
        token: Token to mask

    Returns:
        Masked token showing only first and last few characters
    """
    if len(token) <= 8:
        return "*" * len(token)

    return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"