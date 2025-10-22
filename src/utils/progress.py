"""
Progress tracking utilities for GitHub issue analysis.

This module provides classes and enums for tracking progress through various
phases of the analysis process, with Rich integration for display.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from rich.console import Console
from rich.progress import Progress, TaskID


class ProgressPhase(Enum):
    """Phase of the analysis process."""

    def __str__(self):
        """String representation that replaces underscores with spaces and capitalizes words."""
        return self.value.replace('_', ' ').replace(' ', '_').lower()

    INITIALIZING = "initializing"
    VALIDATING_REPOSITORY = "validating_repository"
    FETCHING_ISSUES = "fetching_issues"
    FILTERING_ISSUES = "filtering_issues"
    RETRIEVING_COMMENTS = "retrieving_comments"
    CALCULATING_METRICS = "calculating_metrics"
    GENERATING_OUTPUT = "generating_output"
    COMPLETED = "completed"


@dataclass
class ProgressInfo:
    """Progress information for current analysis phase."""

    current_phase: ProgressPhase
    total_items: int = 0
    processed_items: int = 0
    phase_description: str = ""
    elapsed_time_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    errors_encountered: List[str] = field(default_factory=list)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100.0


class ProgressManager:
    """Rich-based progress manager for displaying progress."""

    def __init__(self, disable_live_display: bool = False):
        """
        Initialize progress manager.

        Args:
            disable_live_display: If True, disables live progress display for testing
        """
        self.console = Console()
        self.disable_live_display = disable_live_display
        self.progress = Progress(disable=disable_live_display)
        self.current_task: Optional[TaskID] = None
        self.start_time: Optional[datetime] = None

    def start(self, total_items: int, description: str = "Processing...") -> TaskID:
        """Start progress tracking."""
        self.start_time = datetime.now()
        self.current_task = self.progress.add_task(description, total=total_items)
        return self.current_task

    def update(self, advance: int = 1, description: Optional[str] = None, total: Optional[int] = None) -> None:
        """Update progress by advancing items."""
        if self.current_task is not None:
            if total is not None:
                self.progress.update(self.current_task, total=total)
            self.progress.advance(self.current_task, advance)
            if description:
                self.progress.update(self.current_task, description=description)

    def finish(self) -> None:
        """Mark progress as complete."""
        if self.current_task is not None:
            self.progress.update(self.current_task, completed=self.progress.tasks[self.current_task].total)

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
