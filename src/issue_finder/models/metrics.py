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
    Represents filtering criteria for issue analysis with comprehensive options.

    Attributes:
        min_comments: Minimum comment count filter (inclusive)
        max_comments: Maximum comment count filter (inclusive)
        state: Issue state filter (open/closed/all)
        labels: Filter by specific label names (all must match if any_labels=False)
        assignees: Filter by assignee usernames (any if any_assignees=True)
        created_since: Created date lower bound (inclusive)
        created_until: Created date upper bound (inclusive)
        updated_since: Updated date lower bound (inclusive)
        updated_until: Updated date upper bound (inclusive)
        any_labels: If True, match any label; if False, match all labels
        any_assignees: If True, match any assignee; if False, match all assignees
        include_comments: Whether to fetch comment content
        page_size: API pagination batch size for performance tuning
    """

    min_comments: Optional[int] = Field(None, description="Minimum comment count filter (inclusive)")
    max_comments: Optional[int] = Field(None, description="Maximum comment count filter (inclusive)")
    state: Optional[str] = Field(None, description="Issue state filter (open/closed/all)")
    labels: List[str] = Field(default_factory=list, description="Filter by specific label names")
    assignees: List[str] = Field(default_factory=list, description="Filter by assignee usernames")
    created_since: Optional[datetime] = Field(None, description="Created date lower bound (inclusive)")
    created_until: Optional[datetime] = Field(None, description="Created date upper bound (inclusive)")
    updated_since: Optional[datetime] = Field(None, description="Updated date lower bound (inclusive)")
    updated_until: Optional[datetime] = Field(None, description="Updated date upper bound (inclusive)")
    any_labels: bool = Field(default=True, description="If True, match any label; if False, match all labels")
    any_assignees: bool = Field(default=True, description="If True, match any assignee; if False, match all assignees")
    include_comments: bool = Field(default=False, description="Whether to fetch comment content")
    page_size: int = Field(default=100, description="API pagination batch size for performance tuning")

    def is_empty(self) -> bool:
        """Check if any filters are applied."""
        return (
            self.min_comments is None and
            self.max_comments is None and
            self.state is None and
            not self.labels and
            not self.assignees and
            self.created_since is None and
            self.created_until is None and
            self.updated_since is None and
            self.updated_until is None and
            not self.include_comments
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
        pagination_info: Pagination details from API calls
        progress_summary: Summary of progress across all phases
        warnings: Non-fatal warnings during processing
        errors: Fatal errors that may have interrupted processing
    """

    repository: Dict[str, Any] = Field(..., description="Repository information")
    filter_criteria: FilterCriteria = Field(..., description="Applied filters")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Filtered issues")
    metrics: ActivityMetrics = Field(..., description="Aggregated activity metrics")
    generated_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    pagination_info: Dict[str, Any] = Field(default_factory=dict, description="Pagination details from API calls")
    progress_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of progress across all phases")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings during processing")
    errors: List[str] = Field(default_factory=list, description="Fatal errors that may have interrupted processing")


from enum import Enum


class ProgressPhase(str, Enum):
    """
    Represents different phases of the analysis process.
    """
    INITIALIZING = "initializing"
    VALIDATING_REPOSITORY = "validating_repository"
    FETCHING_ISSUES = "fetching_issues"
    FILTERING_ISSUES = "filtering_issues"
    RETRIEVING_COMMENTS = "retrieving_comments"
    CALCULATING_METRICS = "calculating_metrics"
    GENERATING_OUTPUT = "generating_output"
    COMPLETED = "completed"


class ProgressInfo(BaseModel):
    """
    Represents progress tracking information for analysis operations.

    Attributes:
        current_phase: Current processing phase
        total_items: Total items to process in current phase
        processed_items: Number of items processed so far
        phase_description: Human-readable description of current phase
        elapsed_time_seconds: Time elapsed for current phase
        estimated_remaining_seconds: Estimated remaining time
        rate_limit_info: GitHub API rate limit info
        errors encountered: Errors encountered during processing
    """

    current_phase: ProgressPhase = Field(..., description="Current processing phase")
    total_items: int = Field(default=0, description="Total items to process in current phase")
    processed_items: int = Field(default=0, description="Number of items processed so far")
    phase_description: str = Field(default="", description="Human-readable description of current phase")
    elapsed_time_seconds: float = Field(default=0.0, description="Time elapsed for current phase")
    estimated_remaining_seconds: Optional[float] = Field(None, description="Estimated remaining time")
    rate_limit_info: Optional[Dict[str, int]] = Field(None, description="GitHub API rate limit info")
    errors_encountered: List[str] = Field(default_factory=list, description="Errors encountered during processing")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage for current phase."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100.0


class PaginationInfo(BaseModel):
    """
    Represents pagination state for GitHub API operations.

    Attributes:
        page_size: Number of items per page
        current_page: Current page number (1-indexed)
        total_pages: Total estimated pages (None if unknown)
        items_per_page: Actual items returned per page
        has_more: Whether more pages are available
        next_page_url: URL for next page (if available)
    """

    page_size: int = Field(..., description="Number of items per page")
    current_page: int = Field(default=1, description="Current page number (1-indexed)")
    total_pages: Optional[int] = Field(None, description="Total estimated pages (None if unknown)")
    items_per_page: int = Field(default=0, description="Actual items returned per page")
    has_more: bool = Field(default=True, description="Whether more pages are available")
    next_page_url: Optional[str] = Field(None, description="URL for next page (if available)")