"""
Filename generator for automatic output file naming.

This module provides functionality to automatically generate meaningful
and unique filenames for output files when users don't specify them.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from models import GitHubRepository


class FilenameGenerator:
    """Generates meaningful and unique filenames for output files."""

    def __init__(self, base_dir: str = "."):
        """Initialize the filename generator.
        
        Args:
            base_dir: Base directory where files will be created
        """
        self.base_dir = Path(base_dir)
        self.default_template = "{project}_{timestamp}.{ext}"
        
    def generate_filename(
        self,
        repository: GitHubRepository,
        format: str,
        template: Optional[str] = None,
        custom_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a unique filename based on repository and format.
        
        Args:
            repository: The GitHub repository being analyzed
            format: Output format (json, csv, table)
            template: Custom filename template (optional)
            custom_vars: Additional variables for template (optional)
            
        Returns:
            A unique filename that doesn't conflict with existing files
        """
        # Use default template if none provided
        template = template or self.default_template
        
        # Get file extension based on format
        ext = self._get_extension(format)
        
        # Prepare template variables
        variables = self._prepare_variables(repository, ext, custom_vars)
        
        # Generate base filename
        base_filename = self._render_template(template, variables)
        
        # Ensure filename is safe and valid
        safe_filename = self._sanitize_filename(base_filename)
        
        # Handle filename conflicts
        final_filename = self._resolve_conflicts(safe_filename)
        
        return final_filename
    
    def _get_extension(self, format: str) -> str:
        """Get appropriate file extension for the given format.
        
        Args:
            format: Output format name
            
        Returns:
            File extension without dot
        """
        extensions = {
            "json": "json",
            "csv": "csv",
            "table": "txt"  # Table format typically goes to console, but can be captured
        }
        return extensions.get(format.lower(), "txt")
    
    def _prepare_variables(
        self,
        repository: GitHubRepository,
        ext: str,
        custom_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Prepare all variables for template rendering.
        
        Args:
            repository: GitHub repository info
            ext: File extension
            custom_vars: Additional custom variables
            
        Returns:
            Dictionary of template variables
        """
        # Current timestamp in ISO format (safe for filenames)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Repository information
        project_name = f"{repository.owner}_{repository.name}"
        
        # Basic variables
        variables = {
            "timestamp": timestamp,
            "project": project_name,
            "owner": repository.owner,
            "repo": repository.name,
            "ext": ext,
            "format": ext,  # Alias for ext
        }
        
        # Add custom variables if provided
        if custom_vars:
            variables.update(custom_vars)
        
        return variables
    
    def _render_template(self, template: str, variables: Dict[str, str]) -> str:
        """Render a filename template with variables.
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variable values
            
        Returns:
            Rendered filename
            
        Raises:
            ValueError: If template contains invalid placeholders
        """
        try:
            # Simple template rendering using str.format()
            rendered = template.format(**variables)
            return rendered
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Unknown template variable: {{{missing_var}}}")
        except Exception as e:
            raise ValueError(f"Invalid template format: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be safe for all operating systems.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
        safe_filename = re.sub(unsafe_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        safe_filename = safe_filename.strip(' .')
        
        # Ensure filename is not empty
        if not safe_filename:
            safe_filename = "github_analysis_output"
        
        # Limit filename length (255 chars max for most filesystems)
        if len(safe_filename) > 255:
            # Keep extension, truncate basename
            name_part, ext_part = os.path.splitext(safe_filename)
            truncated_name = name_part[:255 - len(ext_part)]
            safe_filename = truncated_name + ext_part
        
        return safe_filename
    
    def _resolve_conflicts(self, filename: str) -> str:
        """Resolve filename conflicts by adding numeric suffixes.
        
        Args:
            filename: Base filename to check
            
        Returns:
            Unique filename that doesn't exist
        """
        path = self.base_dir / filename
        
        # If file doesn't exist, use the original name
        if not path.exists():
            return filename
        
        # Extract name and extension parts
        name_part, ext_part = os.path.splitext(filename)
        
        # Try with increasing numbers until we find an available name
        counter = 1
        while True:
            new_filename = f"{name_part}_{counter}{ext_part}"
            new_path = self.base_dir / new_filename
            
            if not new_path.exists():
                return new_filename
            
            counter += 1
            
            # Safety limit to prevent infinite loops
            if counter > 1000:
                raise RuntimeError("Too many conflicting files. Clean up the directory.")


def create_filename_generator(output_path: Optional[str] = None) -> FilenameGenerator:
    """Create a filename generator instance.
    
    Args:
        output_path: Optional output file path to extract directory from
        
    Returns:
        FilenameGenerator instance
    """
    if output_path:
        # Extract directory from the provided path
        base_dir = os.path.dirname(output_path) or "."
    else:
        base_dir = "."
    
    return FilenameGenerator(base_dir)