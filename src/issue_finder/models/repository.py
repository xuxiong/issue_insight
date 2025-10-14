"""
GitHub repository model.

This module defines the data structure for representing GitHub repositories
in the issue analysis system.
"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class GitHubRepository(BaseModel):
    """
    Represents a GitHub repository for issue analysis.

    Attributes:
        owner: Repository owner username
        name: Repository name
        url: Full repository URL
        api_url: GitHub API URL for the repository
        is_public: Whether repository is public (always True for our scope)
        default_branch: Default branch name (e.g., "main", "master")
    """

    owner: str = Field(..., description="Repository owner username")
    name: str = Field(..., description="Repository name")
    url: HttpUrl = Field(..., description="Repository URL")
    api_url: HttpUrl = Field(..., description="GitHub API URL for the repository")
    is_public: bool = Field(default=True, description="Whether repository is public")
    default_branch: str = Field(..., description="Default branch name")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            HttpUrl: str,
        }

    @property
    def full_name(self) -> str:
        """Get the full repository name (owner/repo)."""
        return f"{self.owner}/{self.name}"