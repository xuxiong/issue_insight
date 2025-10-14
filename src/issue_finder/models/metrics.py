"""
Activity metrics and filter criteria models.

This module defines the data structures for representing filter criteria,
activity metrics, and reaction summaries in the issue analysis system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReactionSummary(BaseModel):
    """
    Represents a summary of reactions on GitHub content.

    Attributes:
        total_count: Total number of reactions
        plus_one: Number of +1 reactions
        minus_one: Number of -1 reactions
        laugh: Number of laugh reactions
        hooray: Number of hooray reactions
        confused: Number of confused reactions
        heart: Number of heart reactions
        rocket: Number of rocket reactions
        eyes: Number of eyes reactions
    """

    total_count: int = Field(default=0, description="Total number of reactions")
    plus_one: int = Field(default=0, description="Number of +1 reactions")
    minus_one: int = Field(default=0, description="Number of -1 reactions")
    laugh: int = Field(default=0, description="Number of laugh reactions")
    hooray: int = Field(default=0, description="Number of hooray reactions")
    confused: int = Field(default=0, description="Number of confused reactions")
    heart: int = Field(default=0, description="Number of heart reactions")
    rocket: int = Field(default=0, description="Number of rocket reactions")
    eyes: int = Field(default=0, description="Number of eyes reactions")


class FilterCriteria(BaseModel):
    """
    Represents filtering criteria for issue analysis.

    Attributes:
        min_comments: Minimum comment count filter
        max_comments: Maximum comment count filter
        state: Issue state filter
        labels: Filter by specific label names
        assignees: Filter by assignee usernames
        created_after: Created date lower bound
        created_before: Created date upper bound
    """

    min_comments: Optional[int] = Field(None, description="Minimum comment count filter")
    max_comments: Optional[int] = Field(None, description="Maximum comment count filter")
    state: Optional[str] = Field(None, description="Issue state filter")
    labels: List[str] = Field(default_factory=list, description="Filter by specific label names")
    assignees: List[str] = Field(default_factory=list, description="Filter by assignee usernames")
    created_after: Optional[datetime] = Field(None, description="Created date lower bound")
    created_before: Optional[datetime] = Field(None, description="Created date upper bound")

    def is_empty(self) -> bool:
        """Check if any filters are applied."""
        return (
            self.min_comments is None and
            self.max_comments is None and
            self.state is None and
            not self.labels and
            not self.assignees and
            self.created_after is None and
            self.created_before is None
        )


class LabelCount(BaseModel):
    """Represents a label with its usage count."""
    label_name: str = Field(..., description="Label name")
    count: int = Field(..., description="Usage count")


class UserActivity(BaseModel):
    """Represents user activity statistics."""
    username: str = Field(..., description="Username")
    issues_created: int = Field(default=0, description="Number of issues created")
    comments_made: int = Field(default=0, description="Number of comments made")


class ActivityMetrics(BaseModel):
    """
    Represents aggregated activity metrics for a repository.

    Attributes:
        total_issues_analyzed: Total number of issues processed
        issues_matching_filters: Number of issues matching filter criteria
        average_comment_count: Average comments per issue
        comment_distribution: Distribution of comment counts by range
        top_labels: Most frequently used labels
        activity_by_month: Issue activity grouped by month
        most_active_users: Users with most activity
        average_issue_resolution_time: Average time to close issues
    """

    total_issues_analyzed: int = Field(..., description="Total number of issues processed")
    issues_matching_filters: int = Field(..., description="Number of issues matching filter criteria")
    average_comment_count: float = Field(..., description="Average comments per issue")
    comment_distribution: Dict[str, int] = Field(default_factory=dict, description="Comment count distribution")
    top_labels: List[LabelCount] = Field(default_factory=list, description="Most frequently used labels")
    activity_by_month: Dict[str, int] = Field(default_factory=dict, description="Monthly activity breakdown")
    most_active_users: List[UserActivity] = Field(default_factory=list, description="Most active users")
    average_issue_resolution_time: Optional[float] = Field(None, description="Average time to close issues in days")


class AnalysisResult(BaseModel):
    """
    Represents the complete analysis result for output.

    Attributes:
        repository: Repository information
        filter_criteria: Applied filters
        issues: Filtered issues (with comments if requested)
        metrics: Aggregated activity metrics
        generated_at: When analysis was performed
        processing_time_seconds: Total processing time
    """

    repository: Dict[str, Any] = Field(..., description="Repository information")
    filter_criteria: FilterCriteria = Field(..., description="Applied filters")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Filtered issues")
    metrics: ActivityMetrics = Field(..., description="Aggregated activity metrics")
    generated_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")