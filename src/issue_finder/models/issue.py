"""
GitHub issue and comment models.

This module defines the data structures for representing GitHub issues and comments
in the issue analysis system.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl

from .user import User


class ReactionSummary(BaseModel):
    """Simple reaction summary class to avoid circular import."""
    total_count: int = Field(default=0, description="Total number of reactions")
    plus_one: int = Field(default=0, description="Number of +1 reactions")
    minus_one: int = Field(default=0, description="Number of -1 reactions")
    laugh: int = Field(default=0, description="Number of laugh reactions")
    hooray: int = Field(default=0, description="Number of hooray reactions")
    confused: int = Field(default=0, description="Number of confused reactions")
    heart: int = Field(default=0, description="Number of heart reactions")
    rocket: int = Field(default=0, description="Number of rocket reactions")
    eyes: int = Field(default=0, description="Number of eyes reactions")


class IssueState(str, Enum):
    """Enumeration for issue states."""
    OPEN = "open"
    CLOSED = "closed"


class Comment(BaseModel):
    """
    Represents a comment on a GitHub issue.

    Attributes:
        id: Unique comment ID
        body: Comment content
        author: User who wrote the comment
        created_at: Creation timestamp
        updated_at: Last edit timestamp
        reactions: Reactions on this comment
        issue_id: Reference to parent issue
    """

    id: int = Field(..., description="Unique comment ID")
    body: str = Field(..., description="Comment content")
    author: User = Field(..., description="User who wrote the comment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last edit timestamp")
    reactions: ReactionSummary = Field(default_factory=lambda: ReactionSummary(), description="Reactions on this comment")
    issue_id: int = Field(..., description="Reference to parent issue")

    def __str__(self) -> str:
        """Return truncated comment as string representation."""
        preview = self.body[:50] + "..." if len(self.body) > 50 else self.body
        return f"Comment by {self.author}: {preview}"


class Issue(BaseModel):
    """
    Represents a single GitHub issue with comprehensive metadata.

    Attributes:
        id: Unique GitHub issue ID
        number: Issue number within repository
        title: Issue title
        body: Issue body text (may be None)
        state: Current state (open/closed)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        closed_at: Closure timestamp (if closed)
        author: User who created the issue
        assignees: Users assigned to the issue
        labels: Labels applied to the issue
        comment_count: Number of comments
        comments: Comment content (if requested)
        reactions: Reactions summary
        milestone: Associated milestone
        is_pull_request: Whether this is a pull request (excluded from analysis)
    """

    id: int = Field(..., description="Unique GitHub issue ID")
    number: int = Field(..., description="Issue number within repository")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue body text")
    state: IssueState = Field(..., description="Current issue state")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    author: User = Field(..., description="User who created the issue")
    assignees: List[User] = Field(default_factory=list, description="Users assigned to the issue")
    labels: List[str] = Field(default_factory=list, description="Labels applied to the issue")
    comment_count: int = Field(default=0, description="Number of comments")
    comments: List[Comment] = Field(default_factory=list, description="Comment content (if requested)")
    reactions: ReactionSummary = Field(default_factory=lambda: ReactionSummary(), description="Reactions summary")
    milestone: Optional[str] = Field(None, description="Associated milestone")
    is_pull_request: bool = Field(default=False, description="Whether this is a pull request")

    def __str__(self) -> str:
        """Return issue title and number as string representation."""
        return f"#{self.number}: {self.title}"

    @property
    def url(self) -> str:
        """Generate GitHub URL for this issue."""
        # This would need repository context to generate full URL
        # For now, return a placeholder
        return f"https://github.com/owner/repo/issues/{self.number}"