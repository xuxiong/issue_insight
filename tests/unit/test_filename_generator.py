"""
Unit tests for filename generator functionality.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from models import GitHubRepository
from utils.filename_generator import FilenameGenerator, create_filename_generator


class TestFilenameGenerator:
    """Test cases for FilenameGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = GitHubRepository(
            owner="test-owner",
            name="test-repo",
            url="https://github.com/test-owner/test-repo",
            api_url="https://api.github.com/repos/test-owner/test-repo",
            default_branch="main"
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_base_dir(self):
        """Test initializing with custom base directory."""
        generator = FilenameGenerator(self.temp_dir)
        assert generator.base_dir == Path(self.temp_dir)

    def test_get_extension_valid_formats(self):
        """Test getting extensions for valid formats."""
        generator = FilenameGenerator()
        
        assert generator._get_extension("json") == "json"
        assert generator._get_extension("csv") == "csv"
        assert generator._get_extension("table") == "txt"
        assert generator._get_extension("unknown") == "txt"  # Default fallback

    def test_prepare_variables_basic(self):
        """Test preparing template variables."""
        generator = FilenameGenerator()
        variables = generator._prepare_variables(self.repo, "json")
        
        assert "timestamp" in variables
        assert variables["project"] == "test-owner_test-repo"
        assert variables["owner"] == "test-owner"
        assert variables["repo"] == "test-repo"
        assert variables["ext"] == "json"
        assert variables["format"] == "json"

    def test_prepare_variables_with_custom_vars(self):
        """Test preparing variables with custom additions."""
        generator = FilenameGenerator()
        custom_vars = {"custom_key": "custom_value", "another": "value2"}
        variables = generator._prepare_variables(self.repo, "csv", custom_vars)
        
        assert variables["custom_key"] == "custom_value"
        assert variables["another"] == "value2"
        assert variables["ext"] == "csv"

    def test_render_template_success(self):
        """Test successful template rendering."""
        generator = FilenameGenerator()
        template = "{project}_{timestamp}.{ext}"
        variables = {
            "project": "myproject",
            "timestamp": "20241022_123456",
            "ext": "json"
        }
        
        result = generator._render_template(template, variables)
        assert result == "myproject_20241022_123456.json"

    def test_render_template_missing_variable(self):
        """Test template rendering with missing variable."""
        generator = FilenameGenerator()
        template = "{project}_{missing_var}.{ext}"
        variables = {
            "project": "myproject",
            "ext": "json"
        }
        
        with pytest.raises(ValueError, match="Unknown template variable"):
            generator._render_template(template, variables)

    def test_sanitize_filename_safe_characters(self):
        """Test sanitizing filenames with safe characters."""
        generator = FilenameGenerator()
        
        # Safe filename should remain unchanged
        safe_name = "my_project_2024.json"
        result = generator._sanitize_filename(safe_name)
        assert result == safe_name

    def test_sanitize_filename_unsafe_characters(self):
        """Test sanitizing filenames with unsafe characters."""
        generator = FilenameGenerator()
        
        # Unsafe characters should be replaced
        unsafe_name = 'my/project:with*unsafe"chars?.json'
        result = generator._sanitize_filename(unsafe_name)
        assert result == "my_project_with_unsafe_chars_.json"

    def test_sanitize_filename_empty_result(self):
        """Test sanitizing filename that becomes empty."""
        generator = FilenameGenerator()
        
        # Filename with only unsafe characters
        result = generator._sanitize_filename('<>:"/\\\\|?*')
        # Should be all underscores after sanitization
        assert result == "__________"

    def test_sanitize_filename_long_name(self):
        """Test sanitizing very long filenames."""
        generator = FilenameGenerator()
        
        # Create a very long filename
        long_name = "a" * 300 + ".json"
        result = generator._sanitize_filename(long_name)
        
        # Should be truncated but keep extension
        assert len(result) <= 255
        assert result.endswith(".json")

    def test_resolve_conflicts_no_conflict(self):
        """Test conflict resolution when no file exists."""
        generator = FilenameGenerator(self.temp_dir)
        
        filename = "test_file.json"
        result = generator._resolve_conflicts(filename)
        
        assert result == filename

    def test_resolve_conflicts_with_conflict(self):
        """Test conflict resolution when file exists."""
        generator = FilenameGenerator(self.temp_dir)
        
        # Create a conflicting file
        conflict_file = Path(self.temp_dir) / "test_file.json"
        conflict_file.touch()
        
        result = generator._resolve_conflicts("test_file.json")
        assert result == "test_file_1.json"

    def test_resolve_conflicts_multiple_conflicts(self):
        """Test conflict resolution with multiple existing files."""
        generator = FilenameGenerator(self.temp_dir)
        
        # Create multiple conflicting files
        for i in range(3):
            filename = f"test_file_{i}.json" if i > 0 else "test_file.json"
            conflict_file = Path(self.temp_dir) / filename
            conflict_file.touch()
        
        result = generator._resolve_conflicts("test_file.json")
        assert result == "test_file_3.json"

    @patch('utils.filename_generator.datetime')
    def test_generate_filename_default_template(self, mock_datetime):
        """Test generating filename with default template."""
        # Mock datetime to have consistent timestamp
        mock_datetime.now.return_value.strftime.return_value = "20241022_123456"
        
        generator = FilenameGenerator(self.temp_dir)
        filename = generator.generate_filename(self.repo, "json")
        
        expected = "test-owner_test-repo_20241022_123456.json"
        assert filename == expected

    def test_generate_filename_custom_template(self):
        """Test generating filename with custom template."""
        generator = FilenameGenerator(self.temp_dir)
        custom_template = "analysis_{owner}_{repo}.{ext}"
        
        filename = generator.generate_filename(
            self.repo, 
            "csv", 
            template=custom_template
        )
        
        assert filename.startswith("analysis_test-owner_test-repo")
        assert filename.endswith(".csv")

    def test_generate_filename_with_custom_vars(self):
        """Test generating filename with custom variables."""
        generator = FilenameGenerator(self.temp_dir)
        custom_vars = {"feature": "issue-analysis", "version": "v1.0"}
        
        filename = generator.generate_filename(
            self.repo,
            "json",
            custom_vars=custom_vars
        )
        
        # Custom variables should be available in the template
        # Since we're using default template, they won't be used unless template includes them
        assert "test-owner_test-repo" in filename

    def test_generate_filename_invalid_template(self):
        """Test generating filename with invalid template."""
        generator = FilenameGenerator(self.temp_dir)
        invalid_template = "{invalid_var}.{ext}"
        
        with pytest.raises(ValueError, match="Unknown template variable"):
            generator.generate_filename(
                self.repo,
                "json",
                template=invalid_template
            )

    def test_generate_filename_conflict_resolution(self):
        """Test that filename generation handles conflicts."""
        generator = FilenameGenerator(self.temp_dir)
        
        # Generate first filename
        filename1 = generator.generate_filename(self.repo, "json")
        
        # Create the file to cause a conflict
        (Path(self.temp_dir) / filename1).touch()
        
        # Generate second filename - should be different
        filename2 = generator.generate_filename(self.repo, "json")
        
        assert filename1 != filename2
        assert filename2.endswith("_1.json")


class TestCreateFilenameGenerator:
    """Test cases for create_filename_generator function."""

    def test_create_without_output_path(self):
        """Test creating generator without output path."""
        generator = create_filename_generator()
        assert isinstance(generator, FilenameGenerator)
        assert generator.base_dir == Path(".")

    def test_create_with_output_path(self):
        """Test creating generator with output path."""
        output_path = "/some/path/output.json"
        generator = create_filename_generator(output_path)
        
        assert isinstance(generator, FilenameGenerator)
        assert generator.base_dir == Path("/some/path")

    def test_create_with_directory_only_path(self):
        """Test creating generator with directory-only path."""
        output_path = "/some/path/"
        generator = create_filename_generator(output_path)
        
        assert generator.base_dir == Path("/some/path")

    def test_create_with_relative_path(self):
        """Test creating generator with relative path."""
        output_path = "output/data.json"
        generator = create_filename_generator(output_path)
        
        assert generator.base_dir == Path("output")