"""
GitHub Project Activity Analyzer

A CLI tool for analyzing GitHub repository issues to understand project activity,
identify community hotspots, and assess engagement patterns.
"""

__version__ = "1.0.0"
__author__ = "Issue Finder Team"
__email__ = "team@issuefinder.dev"

from .cli import main

__all__ = ["main"]