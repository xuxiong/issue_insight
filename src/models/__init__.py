"""
Core data models for GitHub Project Activity Analyzer.

This module contains Pydantic models for GitHub entities including:
- GitHubRepository: Repository information
- Issue: GitHub issue with metadata
- Comment: Issue comment content
- User: GitHub user information
- Label: GitHub issue labels
- FilterCriteria: Filtering parameters
- ActivityMetrics: Aggregated metrics
- Progress tracking models
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import pydantic
from pydantic import field_validator


class IssueState(str, Enum):
    """Enum representing GitHub issue states."""
    OPEN = "open"
    CLOSED = "closed"


class OutputFormat(str, Enum):
    """Enum representing supported output formats."""
    JSON = "json"
    CSV = "csv"
    TABLE = "table"


class ProgressPhase(str, Enum):
    """Enum representing different phases of the analysis process."""
    INITIALIZING = "initializing"
    VALIDATING_REPOSITORY = "validating_repository"
    FETCHING_ISSUES = "fetching_issues"
    FILTERING_ISSUES = "filtering_issues"
    RETRIEVING_COMMENTS = "retrieving_comments"
    CALCULATING_METRICS = "calculating_metrics"
    GENERATING_OUTPUT = "generating_output"
    COMPLETED = "completed"


class User(pydantic.BaseModel):
    """Represents a GitHub user with minimal relevant information."""

    id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: str
    is_bot: bool = False


class Label(pydantic.BaseModel):
    """Represents a GitHub issue label."""

    id: int
    name: str
    color: str
    description: Optional[str] = None


class Comment(pydantic.BaseModel):
    """Represents a comment on a GitHub issue."""

    id: int
    body: str
    author: User
    created_at: datetime
    updated_at: datetime
    issue_id: int


# For backward compatibility with tests that import old model names
class ReactionSummary(pydantic.BaseModel):
    """Placeholder for reaction summary (future implementation)."""
    total_count: int = 0
    plus_one: int = 0
    minus_one: int = 0
    laugh: int = 0
    hooray: int = 0
    confused: int = 0
    heart: int = 0
    rocket: int = 0
    eyes: int = 0


class Milestone(pydantic.BaseModel):
    """Placeholder for milestone model (future implementation)."""
    id: Optional[int] = None
    title: Optional[str] = None
    state: Optional[str] = None


class Issue(pydantic.BaseModel):
    """Represents a single GitHub issue with comprehensive metadata."""

    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: IssueState
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    author: User
    assignees: List[User] = []
    labels: List[Label] = []
    comment_count: int
    comments: List[Comment] = []
    reactions: ReactionSummary = ReactionSummary()
    milestone: Optional[Milestone] = None
    is_pull_request: bool = False


class GitHubRepository(pydantic.BaseModel):
    """Represents a GitHub repository for issue analysis."""

    owner: str
    name: str
    url: str
    api_url: str
    is_public: bool = True
    default_branch: str


class FilterCriteria(pydantic.BaseModel):
    """Represents filtering criteria for issue analysis."""

    min_comments: Optional[int] = None
    max_comments: Optional[int] = None
    state: Optional[IssueState] = None
    labels: List[str] = []
    assignees: List[str] = []
    created_since: Optional[datetime] = None
    created_until: Optional[datetime] = None
    updated_since: Optional[datetime] = None
    updated_until: Optional[datetime] = None
    limit: Optional[int] = None
    any_labels: bool = True
    any_assignees: bool = True
    include_comments: bool = False
    page_size: int = 100

    @field_validator('min_comments', 'max_comments', mode='before')
    @classmethod
    def validate_comment_counts(cls, v):
        """Validate that comment counts are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Comment count must be non-negative")
        return v

    @field_validator('limit', mode='before')
    @classmethod
    def validate_limit(cls, v, info):
        """Validate limit constraints."""
        if v is not None and v < 1:
            raise ValueError("Limit must be at least 1 when specified")

        return v

    @field_validator('max_comments', mode='before')
    @classmethod
    def validate_comment_range(cls, v, info):
        """Validate that min_comments is not greater than max_comments."""
        if info.data and v is not None:
            min_comments = info.data.get('min_comments')
            if min_comments is not None and min_comments > v:
                raise ValueError("min_comments cannot be greater than max_comments")
        return v

    @field_validator('created_until', mode='before')
    @classmethod
    def validate_date_ranges(cls, v, info):
        """Validate that date ranges are logical."""
        if info.data and v:
            created_since = info.data.get('created_since')
            created_until = v

            if created_since is not None and created_until is not None:
                if created_since > created_until:
                    raise ValueError("created_since cannot be after created_until")

        return v


class LabelCount(pydantic.BaseModel):
    """Represents label usage statistics."""

    label_name: str
    count: int


class UserActivity(pydantic.BaseModel):
    """Represents user activity statistics."""

    username: str
    issues_created: int
    comments_made: int


class ActivityMetrics(pydantic.BaseModel):
    """Represents aggregated activity metrics for a repository."""

    total_issues_analyzed: int
    issues_matching_filters: int
    average_comment_count: float
    comment_distribution: Dict[str, int]
    top_labels: List[LabelCount]
    activity_by_month: Dict[str, int]
    most_active_users: List[UserActivity]
    average_issue_resolution_time: Optional[float]


class PaginationInfo(pydantic.BaseModel):
    """Represents pagination state for GitHub API operations."""

    page_size: int
    current_page: int = 1
    total_pages: Optional[int] = None
    items_per_page: int = 0
    has_more: bool = True
    next_page_url: Optional[str] = None


class AnalysisResult(pydantic.BaseModel):
    """Represents the complete analysis result for output."""

    repository: GitHubRepository
    filter_criteria: FilterCriteria
    issues: List[Issue]
    metrics: ActivityMetrics
    generated_at: datetime
    processing_time_seconds: float
    pagination_info: PaginationInfo
    progress_summary: Dict[str, Any]
    warnings: List[str] = []
    errors: List[str] = []