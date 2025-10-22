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
    ALL = "all"


class OutputFormat(str, Enum):
    """Enum representing supported output formats."""

    JSON = "json"
    CSV = "csv"
    TABLE = "table"


class Granularity(str, Enum):
    """Enum representing time granularity for metrics."""

    AUTO = "auto"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


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


class UserRole(str, Enum):
    """Enum representing user roles in a repository."""

    OWNER = "owner"
    MAINTAINER = "maintainer"
    COLLABORATOR = "collaborator"
    CONTRIBUTOR = "contributor"
    MEMBER = "member"
    NONE = "none"


class User(pydantic.BaseModel):
    """Represents a GitHub user with minimal relevant information."""

    id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.NONE
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
    author: Optional[User]
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

    @field_validator("min_comments", "max_comments", mode="before")
    @classmethod
    def validate_comment_counts(cls, v):
        """Validate that comment counts are non-negative."""
        if v is not None and v < 0:
            raise ValueError(f"Comment count must be non-negative, got: {v}")
        return v

    @field_validator("limit", mode="before")
    @classmethod
    def validate_limit(cls, v, info):
        """Validate limit constraints."""
        if v is not None and v < 1:
            raise ValueError(f"Limit must be at least 1 when specified, got: {v}")

        return v

    @field_validator("max_comments", mode="before")
    @classmethod
    def validate_comment_range(cls, v, info):
        """Validate that min_comments is not greater than max_comments."""
        if info.data and v is not None:
            min_comments = info.data.get("min_comments")
            if min_comments is not None and min_comments > v:
                raise ValueError(f"min_comments cannot be greater than max_comments")
        return v

    @field_validator(
        "created_since",
        "created_until",
        "updated_since",
        "updated_until",
        mode="before",
    )
    @classmethod
    def convert_date_strings(cls, v):
        """Convert date strings to datetime objects."""
        if v is None:
            return v

        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            from utils.validators import parse_iso_date

            try:
                return parse_iso_date(v)
            except Exception:
                # Let Pydantic handle the validation error with its custom message
                raise ValueError(f"Invalid date format: {v}")

        # If it's not a string or datetime, let Pydantic handle the error
        return v

    @field_validator("created_until", mode="before")
    @classmethod
    def validate_created_date_ranges(cls, v, info):
        """Validate that created date ranges are logical."""
        if info.data and v is not None:
            created_since = info.data.get("created_since")

            if (
                created_since is not None
                and isinstance(created_since, datetime)
                and isinstance(v, datetime)
            ):
                if created_since > v:
                    raise ValueError("created_since cannot be after created_until")

        return v

    @field_validator("updated_until", mode="before")
    @classmethod
    def validate_updated_date_ranges(cls, v, info):
        """Validate that updated date ranges are logical."""
        if info.data and v is not None:
            updated_since = info.data.get("updated_since")

            if (
                updated_since is not None
                and isinstance(updated_since, datetime)
                and isinstance(v, datetime)
            ):
                if updated_since > v:
                    raise ValueError("updated_since cannot be after updated_until")

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
    activity_by_week: Dict[str, int]
    activity_by_day: Dict[str, int]
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


class CLIArguments(pydantic.BaseModel):
    """Represents validated CLI arguments for issue analysis."""

    repository_url: str
    min_comments: Optional[int] = None
    max_comments: Optional[int] = None
    limit: int = 100
    format: OutputFormat = OutputFormat.TABLE
    verbose: bool = False
    state: Optional[str] = None
    metrics: bool = False
    granularity: Granularity = Granularity.AUTO
    labels: List[str] = []
    assignees: List[str] = []
    created_since: Optional[str] = None
    created_until: Optional[str] = None
    updated_since: Optional[str] = None
    updated_until: Optional[str] = None
    any_labels: bool = True
    all_labels: bool = False
    any_assignees: bool = True
    all_assignees: bool = False
    include_comments: bool = False
    token: Optional[str] = None

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_repository_url(cls, v):
        """Validate GitHub repository URL format."""
        import re

        pattern = r"^https?://github\.com/([^/]+)/([^/]+)(?:/?|/.*)$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react"
            )
        return v

    @field_validator("min_comments", "max_comments", mode="before")
    @classmethod
    def validate_comment_counts(cls, v):
        """Validate that comment counts are non-negative."""
        if v is not None and v < 0:
            raise ValueError(
                "Comment count must be non-negative. Use positive numbers or omit the flag."
            )
        return v

    @field_validator("limit", mode="before")
    @classmethod
    def validate_limit(cls, v, info):
        """Validate limit constraints."""
        if v is not None and v < 1:
            raise ValueError("Limit must be at least 1 when specified")
        return v

    @field_validator("max_comments", mode="before")
    @classmethod
    def validate_comment_range(cls, v, info):
        """Validate that min_comments is not greater than max_comments."""
        if info.data and v is not None:
            min_comments = info.data.get("min_comments")
            if min_comments is not None and min_comments > v:
                raise ValueError(f"min_comments cannot be greater than max_comments")
        return v

    @field_validator("state", mode="before")
    @classmethod
    def validate_state(cls, v):
        """Validate state parameter."""
        if v is not None:
            valid_states = ["open", "closed", "all"]
            if v not in valid_states:
                raise ValueError(
                    f"Invalid state '{v}'. Valid states: {', '.join(valid_states)}"
                )
        return v

    @field_validator(
        "created_since",
        "created_until",
        "updated_since",
        "updated_until",
        mode="before",
    )
    @classmethod
    def validate_date_params(cls, v):
        """Validate date parameter format."""
        if v is not None:
            from utils.validators import parse_iso_date

            try:
                parse_iso_date(v)
            except Exception:
                raise ValueError(
                    f"Invalid date format: '{v}'. Use YYYY-MM-DD format. Example: 2024-01-15"
                )
        return v

    @field_validator("created_until", mode="before")
    @classmethod
    def validate_created_date_ranges(cls, v, info):
        """Validate that created date ranges are logical."""
        if info.data and v is not None:
            created_since = info.data.get("created_since")
            if created_since is not None:
                try:
                    created_since_dt = info.data.get("created_since")
                    v_dt = (
                        info.data.get("created_until")
                        if info.field_name == "created_until"
                        else v
                    )
                    if created_since_dt and v_dt:
                        # Simple check if both are present and order
                        pass  # Let FilterCriteria handle the full conversion
                except:
                    pass  # Defer to runtime
        return v

    @field_validator("updated_until", mode="before")
    @classmethod
    def validate_updated_date_ranges(cls, v, info):
        """Validate that updated date ranges are logical."""
        if info.data and v is not None:
            updated_since = info.data.get("updated_since")
            if updated_since is not None:
                try:
                    updated_since_dt = info.data.get("updated_since")
                    v_dt = (
                        info.data.get("updated_until")
                        if info.field_name == "updated_until"
                        else v
                    )
                    if updated_since_dt and v_dt:
                        pass
                except:
                    pass
        return v

    @field_validator("all_labels", mode="before")
    @classmethod
    def validate_all_labels(cls, v, info):
        """Validate that if all_labels is specified, labels must be provided."""
        if info.data and v and not info.data.get("labels"):
            raise ValueError("--all-labels requires --labels to be specified")
        return v

    @field_validator("all_assignees", mode="before")
    @classmethod
    def validate_all_assignees(cls, v, info):
        """Validate that if all_assignees is specified, assignees must be provided."""
        if info.data and v and not info.data.get("assignees"):
            raise ValueError("--all-assignees requires --assignees to be specified")
        return v

    def to_filter_criteria(self) -> FilterCriteria:
        """Convert CLI arguments to FilterCriteria."""
        # Convert dates
        dates = {}
        for date_field in [
            "created_since",
            "created_until",
            "updated_since",
            "updated_until",
        ]:
            val = getattr(self, date_field)
            if val:
                from utils.validators import parse_iso_date

                dates[date_field] = parse_iso_date(val)

        # Convert state to IssueState or None
        state_enum = None
        if self.state:
            if self.state == "open":
                state_enum = IssueState.OPEN
            elif self.state == "closed":
                state_enum = IssueState.CLOSED
            elif self.state == "all":
                state_enum = IssueState.ALL

        # Determine label/assignee logic - default to ANY if neither specified
        any_labels_flag = self.any_labels or not self.all_labels
        any_assignees_flag = self.any_assignees or not self.all_assignees

        return FilterCriteria(
            min_comments=self.min_comments,
            max_comments=self.max_comments,
            limit=self.limit,
            state=state_enum,
            labels=self.labels,
            assignees=self.assignees,
            created_since=dates.get("created_since"),
            created_until=dates.get("created_until"),
            updated_since=dates.get("updated_since"),
            updated_until=dates.get("updated_until"),
            any_labels=any_labels_flag,
            any_assignees=any_assignees_flag,
            include_comments=self.include_comments,
        )
