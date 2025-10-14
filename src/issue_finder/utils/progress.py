"""
Progress tracking utilities.

This module provides progress indicators and status tracking for long-running
operations using the Rich library.
"""

from typing import Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class ProgressTracker:
    """
    Progress tracker for long-running operations.

    This class provides progress indicators and status updates for operations
    like fetching issues, processing data, and generating reports.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize progress tracker.

        Args:
            verbose: Whether to show detailed progress information
        """
        self.verbose = verbose
        self.console = Console()
        self._progress = None

    def start_operation(self, description: str, total: Optional[int] = None) -> None:
        """
        Start tracking a new operation.

        Args:
            description: Description of the operation
            total: Total number of items to process (if known)
        """
        if self.verbose:
            self.console.print(f"[blue]🚀 Starting: {description}[/blue]")

        if total and total > 1:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
            )
            self._progress.start()
            self._task_id = self._progress.add_task(description, total=total)

    def update_progress(self, advance: int = 1, description: Optional[str] = None) -> None:
        """
        Update progress for the current operation.

        Args:
            advance: Number of items to advance the progress by
            description: Optional new description
        """
        if self._progress:
            self._progress.advance(self._task_id, advance)
            if description:
                self._progress.update(self._task_id, description=description)

    def finish_operation(self, description: Optional[str] = None) -> None:
        """
        Finish the current operation.

        Args:
            description: Optional completion message
        """
        if self._progress:
            self._progress.stop()
            self._progress = None

        if self.verbose:
            message = description or "Operation completed"
            self.console.print(f"[green]✅ {message}[/green]")

    def show_status(self, message: str, style: str = "info") -> None:
        """
        Show a status message.

        Args:
            message: Status message to display
            style: Message style ("info", "warning", "error", "success")
        """
        styles = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        }

        color = styles.get(style, "blue")
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }

        icon = icons.get(style, "ℹ️")
        self.console.print(f"[{color}]{icon} {message}[/{color}]")

    def show_rate_limit_warning(self, wait_time: int) -> None:
        """
        Show rate limit warning.

        Args:
            wait_time: Time to wait in seconds
        """
        panel = Panel(
            f"[yellow]GitHub API rate limit exceeded.\n"
            f"Waiting {wait_time} seconds for limit to reset...\n"
            f"Set GITHUB_TOKEN environment variable for higher limits.[/yellow]",
            title="[bold red]Rate Limited[/bold red]",
            border_style="red",
        )
        self.console.print(panel)

    def show_error(self, error: Exception, context: str = "") -> None:
        """
        Show error information.

        Args:
            error: Exception that occurred
            context: Context where the error occurred
        """
        title = f"Error{f' in {context}' if context else ''}"
        panel = Panel(
            f"[red]{str(error)}[/red]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
        )
        self.console.print(panel)

    def show_summary_table(self, data: dict[str, Any], title: str = "Summary") -> None:
        """
        Show a summary table with data.

        Args:
            data: Dictionary of data to display
            title: Table title
        """
        table = Table(title=title, show_header=True, header_style="bold magenta")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for key, value in data.items():
            # Format key for display
            display_key = key.replace("_", " ").title()
            table.add_row(display_key, str(value))

        self.console.print(table)

    def show_repository_info(self, owner: str, repo: str, total_issues: int) -> None:
        """
        Show repository information.

        Args:
            owner: Repository owner
            repo: Repository name
            total_issues: Total number of issues
        """
        panel = Panel(
            f"[bold cyan]Repository:[/bold cyan] {owner}/{repo}\n"
            f"[bold cyan]Total Issues:[/bold cyan] {total_issues:,}",
            title="[bold blue]Repository Information[/bold blue]",
            border_style="blue",
        )
        self.console.print(panel)

    def show_filter_summary(self, filters: dict) -> None:
        """
        Show applied filters summary.

        Args:
            filters: Dictionary of applied filters
        """
        if not filters:
            return

        filter_items = []
        for key, value in filters.items():
            if value is not None and value != [] and value != "":
                # Format key for display
                display_key = key.replace("_", " ").title()
                if isinstance(value, list):
                    filter_items.append(f"{display_key}: {', '.join(map(str, value))}")
                else:
                    filter_items.append(f"{display_key}: {value}")

        if filter_items:
            panel = Panel(
                "\n".join(filter_items),
                title="[bold blue]Applied Filters[/bold blue]",
                border_style="blue",
            )
            self.console.print(panel)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._progress:
            self._progress.stop()