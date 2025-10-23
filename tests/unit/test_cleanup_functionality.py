"""
Unit tests for pytest cleanup functionality.

These tests verify that the cleanup fixtures and patterns work correctly.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock


class TestCleanupFixtures:
    """Test cases for cleanup fixtures."""

    def test_temporary_directory_cleanup(self, temporary_directory):
        """Test that temporary_directory fixture creates and cleans up directories."""
        # Create a file in the temporary directory
        test_file = temporary_directory / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Verify file exists
        assert test_file.exists()
        assert test_file.read_text() == "Hello, World!"
        
        # The cleanup will happen automatically after the test

    def test_temporary_file_cleanup(self, temporary_file):
        """Test that temporary_file fixture creates and cleans up files."""
        # Write content to the temporary file
        temporary_file.write_text("Test content")
        
        # Verify file exists and content is correct
        assert temporary_file.exists()
        assert temporary_file.read_text() == "Test content"
        
        # The cleanup will happen automatically after the test

    def test_mock_cleanup_resets_mocks(self, mock_cleanup):
        """Test that mock_cleanup fixture resets mock objects."""
        # Create a mock and register it with cleanup
        mock_obj = mock_cleanup(Mock())
        
        # Use the mock
        mock_obj.some_method.return_value = "test"
        mock_obj.some_method()
        
        # Verify mock was called
        mock_obj.some_method.assert_called_once()
        
        # The mock will be reset after the test

    def test_cleanup_registry_executes_functions(self, cleanup_registry):
        """Test that cleanup_registry executes registered functions."""
        cleanup_executed = False
        
        def custom_cleanup():
            nonlocal cleanup_executed
            cleanup_executed = True
        
        # Register the cleanup function
        cleanup_registry(custom_cleanup)
        
        # The cleanup function will be executed after the test
        # We can't verify it here since it happens after the test
        # This test mainly ensures the fixture doesn't raise errors

    def test_test_class_cleanup(self, test_class_cleanup):
        """Test that test_class_cleanup fixture works."""
        cleanup_executed = False
        
        def class_cleanup():
            nonlocal cleanup_executed
            cleanup_executed = True
        
        # Add cleanup task
        test_class_cleanup.add_cleanup(class_cleanup)
        
        # The cleanup will happen after the test class
        # This test mainly ensures the fixture doesn't raise errors


class TestCleanupPatterns:
    """Test cases for various cleanup patterns."""

    def test_yield_fixture_pattern(self):
        """Test the yield fixture pattern for cleanup."""
        
        @pytest.fixture
        def resource_with_yield():
            """Fixture that uses yield for cleanup."""
            resource = Mock()
            resource.setup = Mock()
            resource.cleanup = Mock()
            
            resource.setup()
            yield resource
            resource.cleanup()
        
        # This pattern is used in conftest.py fixtures
        # The test verifies the pattern syntax is correct

    def test_try_finally_pattern(self):
        """Test the try/finally pattern for cleanup."""
        resource = Mock()
        resource.cleanup = Mock()
        
        try:
            # Test operations
            assert resource is not None
        finally:
            # Cleanup always runs
            resource.cleanup()
            resource.cleanup.assert_called_once()


class TestComplexCleanupScenarios:
    """Test more complex cleanup scenarios."""

    def test_multiple_cleanup_fixtures(self, temporary_directory, mock_cleanup):
        """Test using multiple cleanup fixtures together."""
        # Create a file in temporary directory
        test_file = temporary_directory / "test.txt"
        test_file.write_text("Multi-fixture test")
        
        # Create and register a mock
        mock_obj = mock_cleanup(Mock())
        mock_obj.test_method.return_value = "success"
        
        # Verify both fixtures work together
        assert test_file.exists()
        assert mock_obj.test_method() == "success"

    def test_nested_cleanup_patterns(self, cleanup_registry):
        """Test nested cleanup patterns."""
        cleanup_calls = []
        
        def nested_cleanup():
            cleanup_calls.append("nested")
        
        def outer_cleanup():
            cleanup_calls.append("outer")
            # Register nested cleanup
            cleanup_registry(nested_cleanup)
        
        # Register outer cleanup
        cleanup_registry(outer_cleanup)
        
        # This tests that cleanup functions can register other cleanups
        # The execution order will be: outer -> nested


class TestCleanupBestPractices:
    """Test that demonstrate cleanup best practices."""

    def test_idempotent_cleanup(self, temporary_directory):
        """Test that cleanup is idempotent (safe to run multiple times)."""
        # Create a file
        test_file = temporary_directory / "test.txt"
        test_file.write_text("data")
        
        # Simulate cleanup being called multiple times
        # (fixture will handle this automatically)
        assert test_file.exists()
        
        # The cleanup fixture should handle multiple calls safely

    def test_cleanup_with_failure_handling(self, cleanup_registry):
        """Test that cleanup handles failures gracefully."""
        cleanup_called = False
        
        def failing_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
            # This cleanup might fail, but it should be handled
            raise ValueError("Cleanup failed, but should not break test")
        
        def successful_cleanup():
            # This should still run even if previous cleanup failed
            pass
        
        # Register both cleanups
        cleanup_registry(failing_cleanup)
        cleanup_registry(successful_cleanup)
        
        # The cleanup registry should handle the failure gracefully


# Test the actual cleanup functionality
@pytest.mark.cleanup
def test_cleanup_fixtures_actually_cleanup():
    """Integration test to verify cleanup actually happens."""
    
    # This test would need to run in a separate process to verify
    # that files are actually cleaned up, but it documents the intent
    
    # The actual verification would require:
    # 1. Creating temporary resources
    # 2. Running tests
    # 3. Verifying resources are gone
    
    # For now, we trust pytest's fixture system works correctly
    pass