"""
GitHub user and label models.

This module defines the data structures for representing GitHub users
and labels in the issue analysis system.
"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class User(BaseModel):
    """
    Represents a GitHub user with minimal relevant information.

    Attributes:
        id: Unique user ID
        username: GitHub username
        display_name: Display name (may differ from username)
        avatar_url: URL to user's avatar image
        is_bot: Whether this is a bot account
    """

    id: int = Field(..., description="Unique user ID")
    username: str = Field(..., description="GitHub username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: HttpUrl = Field(..., description="Avatar image URL")
    is_bot: bool = Field(default=False, description="Whether this is a bot account")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            HttpUrl: str,
        }

    def __str__(self) -> str:
        """Return username as string representation."""
        return self.username


class Label(BaseModel):
    """
    Represents a GitHub issue label for categorization.

    Attributes:
        id: Unique label ID
        name: Label name (e.g., "bug", "enhancement")
        color: Hex color code (e.g., "#ff0000")
        description: Label description
    """

    id: int = Field(..., description="Unique label ID")
    name: str = Field(..., description="Label name")
    color: str = Field(..., pattern=r"^[0-9a-fA-F]{6}$", description="Hex color code")
    description: Optional[str] = Field(None, description="Label description")

    def __str__(self) -> str:
        """Return label name as string representation."""
        return self.name