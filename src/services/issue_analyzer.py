"""
Issue Analyzer Service (T018).

Orchestrates the complete issue analysis workflow for User Story 1.
This service integrates GitHub client, filter engine, and output formatting.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from services.github_client import GitHubClient
from services.filter_engine import FilterEngine
from services.metrics_analyzer import MetricsAnalyzer
from utils.progress import ProgressManager, ProgressInfo, ProgressPhase
from models import Issue, GitHubRepository, FilterCriteria, User, ActivityMetrics, UserRole, UserActivity
from utils.errors import ValidationError, RepositoryNotFoundError
from utils.validators import apply_limit


@dataclass
class AnalysisResult:
    """Result of issue analysis with metadata."""

    issues: List[Issue]
    repository: GitHubRepository
    filter_criteria: FilterCriteria
    metrics: ActivityMetrics
    total_issues_available: int
    analysis_time: float


class IssueAnalyzer:
    """
    Orchestrates GitHub repository issue analysis.

    This service provides high-level analysis functionality by integrating:
    - GitHub API client for data retrieval
    - Filter engine for criteria-based filtering
    - Metrics calculation for insights
    """

    def __init__(
        self, github_token: Optional[str] = None, disable_progress_display: bool = False
    ):
        """Initialize analyzer services."""
        # Only pass token if it's explicitly provided and not None
        if github_token is None:
            self.github_client = GitHubClient()
        else:
            self.github_client = GitHubClient(token=github_token)
        self.filter_engine = FilterEngine()
        self.metrics_analyzer = MetricsAnalyzer()
        self.disable_progress_display = disable_progress_display

    def analyze_repository(
        self,
        repository_url: str,
        filter_criteria: FilterCriteria,
        state: Optional[str] = "all",
    ) -> AnalysisResult:
        """
        Analyze a GitHub repository with specified filters.

        Args:
            repository_url: GitHub repository URL
            filter_criteria: Filtering criteria for issues
            state: Issue state filter (open/closed/all)

        Returns:
            AnalysisResult with filtered issues and metrics

        Raises:
            ValidationError: If parameters are invalid
            RepositoryNotFoundError: If repository doesn't exist
        """

        start_time = time.time()

        # Initialize progress manager for real-time display
        progress_manager = ProgressManager(
            disable_live_display=self.disable_progress_display
        )
        current_progress = ProgressInfo(
            current_phase=ProgressPhase.INITIALIZING,
            phase_description="Initializing analysis...",
            elapsed_time_seconds=0.0,
        )

        # Always use context manager - Rich Progress handles disable internally
        with progress_manager.progress:
            return self._perform_analysis(
                progress_manager,
                current_progress,
                repository_url,
                filter_criteria,
                state,
                start_time,
            )

    def _perform_analysis(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        repository_url: str,
        filter_criteria: FilterCriteria,
        state: Optional[str],
        start_time: float,
    ) -> AnalysisResult:
        """
        Perform the actual analysis logic.

        Args:
            progress_manager: Progress manager instance
            current_progress: Current progress info
            repository_url: Repository URL
            filter_criteria: Filter criteria
            state: Issue state
            start_time: Analysis start time

        Returns:
            AnalysisResult with analysis results
        """
        try:
            # Initialize analysis
            repository = self._initialize_analysis(progress_manager, current_progress, repository_url)
            
            # Map state for GitHub API
            github_state = self._map_github_state(state)
            
            # Fetch issues
            all_issues = self._fetch_issues_with_progress(
                progress_manager, current_progress, repository, github_state, filter_criteria
            )
            
            # Apply filtering
            filtered_issues = self._apply_filters_with_progress(
                progress_manager, current_progress, all_issues, filter_criteria
            )
            
            # Apply limit if specified
            filtered_issues = self._apply_limit_if_needed(filtered_issues, filter_criteria, current_progress)
            
            # Retrieve comments if requested
            if filter_criteria.include_comments:
                filtered_issues = self._retrieve_comments_with_progress(
                    progress_manager, current_progress, filtered_issues, repository
                )
            
            # Calculate metrics
            metrics = self._calculate_metrics_with_enhancements(
                current_progress, filtered_issues, all_issues, filter_criteria, repository
            )
            
            # Complete analysis
            return self._complete_analysis(
                current_progress, start_time, filtered_issues, repository, 
                filter_criteria, metrics, len(all_issues)
            )

        except Exception as e:
            # Record errors in progress
            current_progress.errors_encountered.append(str(e))
            raise

    def _initialize_analysis(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        repository_url: str
    ) -> GitHubRepository:
        """Initialize analysis and validate repository."""
        current_progress.current_phase = ProgressPhase.INITIALIZING
        current_progress.phase_description = "Initializing analysis..."

        # Parse and validate repository URL
        repository = self.github_client.get_repository(repository_url)

        current_progress.current_phase = ProgressPhase.VALIDATING_REPOSITORY
        current_progress.phase_description = "Validating repository..."
        
        return repository

    def _map_github_state(self, state: Optional[str]) -> str:
        """Map CLI state parameter to GitHub API state."""
        state_mapping = {
            "open": "open",
            "closed": "closed",
            "all": "all",
            None: "all",
        }
        return state_mapping.get(state, "all")

    def _fetch_issues_with_progress(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        repository: GitHubRepository,
        github_state: str,
        filter_criteria: FilterCriteria
    ) -> List[Issue]:
        """Fetch issues from GitHub with progress tracking."""
        current_progress.current_phase = ProgressPhase.FETCHING_ISSUES
        current_progress.phase_description = "Fetching issues from repository..."

        # Estimate total items for progress tracking
        estimated_total = self._estimate_total_items(filter_criteria)
        current_progress.total_items = estimated_total
        
        progress_manager.start(
            total_items=estimated_total, description="Fetching issues..."
        )

        # Define progress callback function
        def issue_progress_callback(current: int, total: int):
            progress_manager.update(
                advance=1, description=f"Fetched {current}/{total} issues..."
            )

        # Get issues with progress tracking
        raw_issues = self.github_client.get_issues(
            owner=repository.owner,
            repo=repository.name,
            state=github_state,
            limit=filter_criteria.limit,
            progress_callback=issue_progress_callback,
        )

        # Update actual totals
        current_progress.total_items = len(raw_issues)
        current_progress.processed_items = current_progress.total_items

        # Complete fetching phase
        progress_manager.finish()
        
        return raw_issues

    def _estimate_total_items(self, filter_criteria: FilterCriteria) -> int:
        """Estimate total items for progress tracking."""
        if filter_criteria.limit:
            buffer_size = min(
                filter_criteria.limit + 20, filter_criteria.limit * 1.5, 200
            )
            buffer_size = int(max(buffer_size, filter_criteria.limit))
            return buffer_size
        else:
            return 1000  # Conservative estimate for no-limit case

    def _apply_filters_with_progress(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        all_issues: List[Issue],
        filter_criteria: FilterCriteria
    ) -> List[Issue]:
        """Apply filters to issues with progress tracking."""
        current_progress.current_phase = ProgressPhase.FILTERING_ISSUES
        current_progress.phase_description = "Applying filters..."
        current_progress.processed_items = 0
        current_progress.total_items = len(all_issues)

        progress_manager.start(
            total_items=len(all_issues), description="Filtering issues..."
        )
        
        filtered_issues = self.filter_engine.filter_issues(all_issues, filter_criteria)

        # Update progress
        current_progress.processed_items = len(all_issues)
        current_progress.total_items = len(all_issues)
        progress_manager.finish()
        
        return filtered_issues

    def _apply_limit_if_needed(
        self,
        filtered_issues: List[Issue],
        filter_criteria: FilterCriteria,
        current_progress: ProgressInfo
    ) -> List[Issue]:
        """Apply limit to filtered issues if specified."""
        if filter_criteria.limit is not None:
            current_progress.phase_description = (
                f"Applying limit: {filter_criteria.limit}"
            )
            return apply_limit(filtered_issues, filter_criteria.limit)
        return filtered_issues

    def _retrieve_comments_with_progress(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        filtered_issues: List[Issue],
        repository: GitHubRepository
    ) -> List[Issue]:
        """Retrieve comments for issues with progress tracking."""
        current_progress.current_phase = ProgressPhase.RETRIEVING_COMMENTS
        current_progress.phase_description = "Retrieving comment content..."
        current_progress.processed_items = 0
        current_progress.total_items = len(filtered_issues)

        progress_manager.start(
            total_items=len(filtered_issues),
            description="Retrieving comments...",
        )

        for i, issue in enumerate(filtered_issues):
            # Retrieve comments for this issue
            comments = self.github_client.get_comments_for_issue(
                owner=repository.owner,
                repo=repository.name,
                issue_number=issue.number,
            )
            # Update issue with retrieved comments
            filtered_issues[i].comments = comments

            progress_manager.update(
                advance=1,
                description=f"Retrieved comments for issue #{issue.number}",
            )

        progress_manager.finish()
        
        return filtered_issues

    def _calculate_metrics_with_enhancements(
        self,
        current_progress: ProgressInfo,
        filtered_issues: List[Issue],
        all_issues: List[Issue],
        filter_criteria: FilterCriteria,
        repository: GitHubRepository
    ) -> ActivityMetrics:
        """Calculate metrics and enhance with role information if needed."""
        current_progress.current_phase = ProgressPhase.CALCULATING_METRICS
        current_progress.phase_description = "Calculating analysis metrics..."

        metrics = self._calculate_metrics(filtered_issues, all_issues)

        # Enhance metrics with role information for most active users if comments were retrieved
        if filter_criteria.include_comments and metrics.most_active_users:
            metrics = self._enhance_metrics_with_roles(
                current_progress, metrics, repository
            )
        
        return metrics

    def _enhance_metrics_with_roles(
        self,
        current_progress: ProgressInfo,
        metrics: ActivityMetrics,
        repository: GitHubRepository
    ) -> ActivityMetrics:
        """Enhance metrics with user role information."""
        try:
            # Get roles for the most active users
            user_roles = self.github_client.get_user_roles_for_active_users(
                owner=repository.owner,
                repo=repository.name,
                usernames=[user.username for user in metrics.most_active_users]
            )

            current_progress.phase_description = "Enhancing metrics with user roles..."
        except Exception as e:
            # If role retrieval fails, continue without roles
            user_roles = {}
            current_progress.phase_description = "Role information unavailable, continuing..."

        # Store role information for later use in formatter
        # We store it as a private attribute on the metrics object
        metrics._user_roles = user_roles
        
        return metrics

    def _complete_analysis(
        self,
        current_progress: ProgressInfo,
        start_time: float,
        filtered_issues: List[Issue],
        repository: GitHubRepository,
        filter_criteria: FilterCriteria,
        metrics: ActivityMetrics,
        total_issues_count: int
    ) -> AnalysisResult:
        """Complete the analysis and prepare the final result."""
        current_progress.current_phase = ProgressPhase.GENERATING_OUTPUT
        current_progress.phase_description = "Generating output..."

        # Complete analysis
        analysis_time = time.time() - start_time
        current_progress.current_phase = ProgressPhase.COMPLETED
        current_progress.phase_description = (
            f"Analysis completed in {analysis_time:.2f}s"
        )
        current_progress.elapsed_time_seconds = analysis_time

        # Update rate limit info if available
        rate_limit_info = self.github_client.get_rate_limit_info()
        if rate_limit_info:
            current_progress.rate_limit_info = rate_limit_info

        return AnalysisResult(
            issues=filtered_issues,
            repository=repository,
            filter_criteria=filter_criteria,
            metrics=metrics,
            total_issues_available=total_issues_count,
            analysis_time=analysis_time,
        )

    def quick_analysis(
        self,
        repository_url: str,
        min_comments: Optional[int] = None,
        max_comments: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> AnalysisResult:
        """
        Quick analysis with common comment count filters.

        Args:
            repository_url: GitHub repository URL
            min_comments: Minimum comment count filter
            max_comments: Maximum comment count filter
            limit: Maximum number of issues to return

        Returns:
            AnalysisResult with filtered issues and metrics
        """
        filter_criteria = FilterCriteria(
            min_comments=min_comments,
            max_comments=max_comments,
            limit=limit,
            include_comments=False,
        )

        return self.analyze_repository(repository_url, filter_criteria)

    def get_activity_summary(self, repository_url: str) -> Dict[str, Any]:
        """
        Quick activity summary for a repository.

        Args:
            repository_url: GitHub repository URL

        Returns:
            Dictionary with activity summary statistics
        """
        try:
            # Quick analysis without filters
            filter_criteria = FilterCriteria(limit=10)
            result = self.analyze_repository(repository_url, filter_criteria)

            return {
                "repository": f"{result.repository.owner}/{result.repository.name}",
                "total_issues_available": result.total_issues_available,
                "recent_activity": len(result.issues),
                "average_comments": (
                    result.metrics.average_comment_count
                    if result.metrics.average_comment_count
                    else 0
                ),
                "has_high_activity": (
                    result.metrics.average_comment_count > 5
                    if result.metrics.average_comment_count
                    else False
                ),
                "analysis_time": result.analysis_time,
            }

        except Exception as e:
            return {"repository": repository_url, "error": str(e), "analysis_time": 0}

    def _calculate_metrics(
        self, filtered_issues: List[Issue], all_issues: List[Issue]
    ) -> ActivityMetrics:
        """
        Calculate analysis metrics for issues.

        Args:
            filtered_issues: Issues that passed filters
            all_issues: All issues from repository

        Returns:
            ActivityMetrics with calculated statistics
        """
        return self.metrics_analyzer.calculate_metrics(filtered_issues, len(all_issues))

    def aggregate_comments_by_user(self, issues: List[Issue]) -> Dict[str, int]:
        """
        Aggregate comment counts by user across all issues.

        Args:
            issues: List of issues with comments loaded

        Returns:
            Dictionary mapping username to total comment count
        """
        if issues is None:
            from utils.errors import ValidationError
            raise ValidationError("issues", issues, "Issues list cannot be None")

        user_comments = {}

        for issue in issues:
            if issue.comments:  # Only process if comments are loaded
                for comment in issue.comments:
                    # Skip comments from deleted users (user is None)
                    if comment.author is None:
                        continue

                    username = comment.author.username
                    user_comments[username] = user_comments.get(username, 0) + 1

        return user_comments

    def get_most_active_users_with_roles(
        self, issues: List[Issue], repository: GitHubRepository, limit: int = 10
    ) -> List[UserActivity]:
        """
        Get most active users with their roles included.

        Args:
            issues: Issues to analyze
            repository: Repository information
            limit: Maximum number of users to return

        Returns:
            List of UserActivity objects with role information
        """
        # Get user activity from metrics analyzer
        active_users = self.metrics_analyzer._calculate_most_active_users(issues, limit)

        # If no users or not using include_comments, return as-is
        if not active_users:
            return active_users

        # Get usernames for role checking
        usernames = [user.username for user in active_users]

        # Get user roles for these active users
        user_roles = {}
        try:
            user_roles = self.github_client.get_user_roles_for_active_users(
                owner=repository.owner,
                repo=repository.name,
                usernames=usernames
            )
        except Exception:
            # If we can't get roles, continue without them
            pass

        # Create a copy of UserActivity list to avoid modifying the original
        from models import User, UserActivity

        # Create User objects with role information for each active user
        users_with_roles = []
        for user_activity in active_users:
            # Get the role or default to CONTRIBUTOR
            user_role = user_roles.get(user_activity.username, UserRole.CONTRIBUTOR)

            # Create a User object with role
            user = User(
                id=0,  # We don't have ID for comment-only users
                username=user_activity.username,
                role=user_role
            )

            # Note: UserActivity model doesn't include role field currently
            # We'll handle role display in the formatter
            users_with_roles.append(user_activity)

        return active_users


def console_print(message: str):
    """Print message using rich console format."""
    try:
        from rich.console import Console

        console = Console()
        console.print(message)
    except ImportError:
        print(message)
