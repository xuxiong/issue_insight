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

# Add src root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.github_client import GitHubClient
from services.filter_engine import FilterEngine
from lib.progress import ProgressManager, ProgressInfo, ProgressPhase
from models import Issue, GitHubRepository, FilterCriteria, User, ActivityMetrics
from lib.errors import ValidationError, RepositoryNotFoundError
from lib.validators import apply_limit


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

    def __init__(self, github_token: Optional[str] = None, disable_progress_display: bool = False):
        """Initialize analyzer services."""
        # Only pass token if it's explicitly provided and not None
        if github_token is None:
            self.github_client = GitHubClient()
        else:
            self.github_client = GitHubClient(token=github_token)
        self.filter_engine = FilterEngine()
        self.disable_progress_display = disable_progress_display

    def analyze_repository(
        self,
        repository_url: str,
        filter_criteria: FilterCriteria,
        state: Optional[str] = "all"
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
        progress_manager = ProgressManager(disable_live_display=self.disable_progress_display)
        current_progress = ProgressInfo(
            current_phase=ProgressPhase.INITIALIZING,
            phase_description="Initializing analysis...",
            elapsed_time_seconds=0.0
        )

        # Always use context manager - Rich Progress handles disable internally
        with progress_manager.progress:
            return self._perform_analysis(progress_manager, current_progress, repository_url, filter_criteria, state, start_time)

    def _perform_analysis(
        self,
        progress_manager: ProgressManager,
        current_progress: ProgressInfo,
        repository_url: str,
        filter_criteria: FilterCriteria,
        state: Optional[str],
        start_time: float
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
            # Phase 1: Initialize & Validate repository
            current_progress.current_phase = ProgressPhase.INITIALIZING
            current_progress.phase_description = "Initializing analysis..."

            # Parse and validate repository URL
            repository = self.github_client.get_repository(repository_url)

            current_progress.current_phase = ProgressPhase.VALIDATING_REPOSITORY
            current_progress.phase_description = "Validating repository..."

            # State mapping
            state_mapping = {
                "open": "open",
                "closed": "closed",
                "all": "all",
                None: "all"
            }
            github_state = state_mapping.get(state, "all")

            # Phase 2: Fetch issues
            current_progress.current_phase = ProgressPhase.FETCHING_ISSUES
            current_progress.phase_description = "Fetching issues from repository..."

            # Estimate total items for progress tracking
            if filter_criteria.limit:
                buffer_size = min(filter_criteria.limit + 20, filter_criteria.limit * 1.5, 200)
                buffer_size = int(max(buffer_size, filter_criteria.limit))
                estimated_total = buffer_size
            else:
                estimated_total = 1000  # Conservative estimate for no-limit case

            current_progress.total_items = estimated_total
            progress_manager.start(total_items=estimated_total, description="Fetching issues...")

            # Fetch issues with progress tracking
            issues_fetched = 0
            all_issues = []

            # Define progress callback function
            def issue_progress_callback(current: int, total: int):
                progress_manager.update(advance=1, description=f"Fetched {current}/{total} issues...")

            # Get issues with progress tracking
            raw_issues = self.github_client.get_issues(
                owner=repository.owner,
                repo=repository.name,
                state=github_state,
                limit=filter_criteria.limit,
                progress_callback=issue_progress_callback
            )

            # Add all fetched issues to the list
            all_issues.extend(raw_issues)
            issues_fetched = len(all_issues)

            # Update actual totals
            current_progress.total_items = len(all_issues)
            current_progress.processed_items = current_progress.total_items

            # Complete fetching phase
            progress_manager.finish()

            # Phase 3: Apply filtering
            current_progress.current_phase = ProgressPhase.FILTERING_ISSUES
            current_progress.phase_description = "Applying filters..."
            current_progress.processed_items = 0
            current_progress.total_items = len(all_issues)

            progress_manager.start(total_items=len(all_issues), description="Filtering issues...")
            filtered_issues = self.filter_engine.filter_issues(all_issues, filter_criteria)

            # Update progress
            current_progress.processed_items = len(all_issues)
            current_progress.total_items = len(all_issues)
            progress_manager.finish()

            # Phase 4: Apply limit if specified
            if filter_criteria.limit is not None:
                current_progress.phase_description = f"Applying limit: {filter_criteria.limit}"
                filtered_issues = apply_limit(filtered_issues, filter_criteria.limit)

            # Phase 5: Calculate metrics
            current_progress.current_phase = ProgressPhase.CALCULATING_METRICS
            current_progress.phase_description = "Calculating analysis metrics..."

            metrics = self._calculate_metrics(filtered_issues, all_issues)

            # Phase 6: Generate output
            current_progress.current_phase = ProgressPhase.GENERATING_OUTPUT
            current_progress.phase_description = "Generating output..."

            # Complete analysis
            analysis_time = time.time() - start_time
            current_progress.current_phase = ProgressPhase.COMPLETED
            current_progress.phase_description = f"Analysis completed in {analysis_time:.2f}s"
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
                total_issues_available=len(all_issues),
                analysis_time=analysis_time
            )

        except Exception as e:
            # Record errors in progress
            current_progress.errors_encountered.append(str(e))
            raise

    def quick_analysis(
        self,
        repository_url: str,
        min_comments: Optional[int] = None,
        max_comments: Optional[int] = None,
        limit: Optional[int] = None
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
            include_comments=False
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
                "average_comments": result.metrics.average_comment_count if result.metrics.average_comment_count else 0,
                "has_high_activity": result.metrics.average_comment_count > 5 if result.metrics.average_comment_count else False,
                "analysis_time": result.analysis_time
            }

        except Exception as e:
            return {
                "repository": repository_url,
                "error": str(e),
                "analysis_time": 0
            }

    def _calculate_metrics(
        self,
        filtered_issues: List[Issue],
        all_issues: List[Issue]
    ) -> ActivityMetrics:
        """
        Calculate analysis metrics for issues.

        Args:
            filtered_issues: Issues that passed filters
            all_issues: All issues from repository

        Returns:
            ActivityMetrics with calculated statistics
        """
        if not filtered_issues:
            return ActivityMetrics(
                total_issues_analyzed=len(all_issues),
                issues_matching_filters=0,
                average_comment_count=0.0,
                comment_distribution={},
                top_labels=[],
                activity_by_month={},
                most_active_users=[],
                average_issue_resolution_time=None
            )

        # Calculate comment distribution
        comment_counts = [issue.comment_count for issue in filtered_issues]
        comment_dist = {
            "0-5": sum(1 for c in comment_counts if c <= 5),
            "6-10": sum(1 for c in comment_counts if 6 <= c <= 10),
            "11+": sum(1 for c in comment_counts if c > 10)
        }

        # Calculate label usage
        label_counts = {}
        for issue in filtered_issues:
            for label in issue.labels:
                label_name = getattr(label, 'name', str(label))
                label_counts[label_name] = label_counts.get(label_name, 0) + 1

        top_labels = sorted(
            [{"label_name": name, "count": count} for name, count in label_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Calculate activity by month
        activity_by_month = {}
        for issue in filtered_issues:
            month_key = issue.created_at.strftime("%Y-%m")
            activity_by_month[month_key] = activity_by_month.get(month_key, 0) + 1

        # Find most active users (issue creators)
        user_counts = {}
        for issue in filtered_issues:
            username = issue.author.username
            user_counts[username] = user_counts.get(username, 0) + 1

        most_active_users = sorted(
            [{"username": username, "issues_created": count, "comments_made": 0} for username, count in user_counts.items()],
            key=lambda x: x["issues_created"],
            reverse=True
        )[:5]

        # Calculate average resolution time for closed issues
        closed_issues = [issue for issue in filtered_issues if issue.state.name == "CLOSED"]
        if closed_issues:
            resolution_times = []
            for issue in closed_issues:
                if issue.closed_at:
                    resolution_time = (issue.closed_at - issue.created_at).total_seconds() / 86400  # days
                    resolution_times.append(resolution_time)

            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None
        else:
            avg_resolution_time = None

        return ActivityMetrics(
            total_issues_analyzed=len(all_issues),
            issues_matching_filters=len(filtered_issues),
            average_comment_count=sum(comment_counts) / len(comment_counts) if comment_counts else 0,
            comment_distribution=comment_dist,
            top_labels=top_labels,
            activity_by_month=activity_by_month,
            most_active_users=most_active_users,
            average_issue_resolution_time=avg_resolution_time
        )


def console_print(message: str):
    """Print message using rich console format."""
    try:
        from rich.console import Console
        console = Console()
        console.print(message)
    except ImportError:
        print(message)
