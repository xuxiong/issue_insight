"""
pytest configuration and fixtures for GitHub Project Activity Analyzer tests.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Generator, Dict, Any

# Mock GitHub API responses for testing
MOCK_REPOSITORY_DATA = {
    "id": 123456789,
    "name": "react",
    "full_name": "facebook/react",
    "owner": {
        "login": "facebook",
        "id": 69631,
        "avatar_url": "https://github.com/facebook.png",
    },
    "html_url": "https://github.com/facebook/react",
    "description": "A declarative, efficient, and flexible JavaScript library for building user interfaces.",
    "default_branch": "main",
    "private": False,
}

MOCK_ISSUE_DATA = {
    "id": 987654321,
    "number": 42,
    "title": "Feature: Add new component library",
    "body": "We should add a comprehensive component library...",
    "state": "open",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:20:00Z",
    "closed_at": None,
    "comments": 5,
    "user": {
        "login": "contributor1",
        "id": 123456,
        "avatar_url": "https://github.com/contributor1.png",
    },
    "assignees": [],
    "labels": [
        {
            "id": 123,
            "name": "enhancement",
            "color": "a2eeef",
            "description": "New feature or request",
        }
    ],
    "pull_request": None,  # Not a pull request
}

MOCK_ISSUES_LIST = [MOCK_ISSUE_DATA]


@pytest.fixture
def mock_repository() -> Dict[str, Any]:
    """Fixture providing mock repository data."""
    return MOCK_REPOSITORY_DATA.copy()


@pytest.fixture
def mock_issue() -> Dict[str, Any]:
    """Fixture providing mock issue data."""
    return MOCK_ISSUE_DATA.copy()


@pytest.fixture
def mock_issues_list() -> list[Dict[str, Any]]:
    """Fixture providing a list of mock issue data."""
    return [issue.copy() for issue in MOCK_ISSUES_LIST]


@pytest.fixture
def mock_github_client():
    """Fixture providing a mock GitHub client."""
    mock_client = Mock()
    mock_repo = Mock()
    mock_repo.get_repo.return_value = mock_repo
    mock_repo.name = "react"
    mock_repo.owner.login = "facebook"
    mock_repo.html_url = "https://github.com/facebook/react"
    mock_repo.private = False
    mock_repo.default_branch = "main"

    # Mock issues
    mock_issues = []
    for issue_data in MOCK_ISSUES_LIST:
        mock_issue = Mock()
        for key, value in issue_data.items():
            if key == "user":
                user_mock = Mock()
                user_mock.login = value["login"]
                user_mock.id = value["id"]
                user_mock.avatar_url = value["avatar_url"]
                setattr(mock_issue, key, user_mock)
            elif key == "assignees":
                setattr(mock_issue, key, [])
            elif key == "labels":
                mock_labels = []
                for label_data in value:
                    mock_label = Mock()
                    for lk, lv in label_data.items():
                        setattr(mock_label, lk, lv)
                    mock_labels.append(mock_label)
                setattr(mock_issue, key, mock_labels)
            else:
                setattr(mock_issue, key, value)
        mock_issues.append(mock_issue)

    mock_repo.get_issues.return_value = mock_issues
    mock_client.get_repo.return_value = mock_repo

    return mock_client


@pytest.fixture
def valid_github_url():
    """Fixture providing a valid GitHub repository URL."""
    return "https://github.com/facebook/react"


@pytest.fixture
def invalid_github_url():
    """Fixture providing an invalid GitHub repository URL."""
    return "https://example.com/not-github/repo"


@pytest.fixture
def sample_filter_criteria():
    """Fixture providing sample filter criteria."""
    return {
        "min_comments": 5,
        "max_comments": None,
        "limit": 100,
        "state": None,
        "labels": [],
        "assignees": [],
    }


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Cleanup fixtures
@pytest.fixture
def temporary_directory():
    """Fixture that creates a temporary directory and cleans it up after tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup: Remove the temporary directory and all its contents
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def temporary_file():
    """Fixture that creates a temporary file and deletes it after tests."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        temp_file_path = Path(temp_file.name)
    yield temp_file_path
    # Cleanup: Remove the temporary file
    if temp_file_path.exists():
        temp_file_path.unlink()


@pytest.fixture
def mock_cleanup():
    """Fixture that provides mock cleanup helpers."""
    mocks = []
    
    def add_mock(mock_obj):
        mocks.append(mock_obj)
        return mock_obj
    
    yield add_mock
    
    # Cleanup: Reset all mocks
    for mock_obj in mocks:
        if hasattr(mock_obj, 'reset_mock'):
            mock_obj.reset_mock()


@pytest.fixture
def cleanup_registry():
    """Fixture that provides a registry for cleanup functions."""
    cleanup_functions = []
    
    def register_cleanup(func):
        """Register a function to be called during cleanup."""
        cleanup_functions.append(func)
        
    def cleanup():
        """Execute all registered cleanup functions."""
        for func in cleanup_functions:
            try:
                func()
            except Exception as e:
                print(f"Warning: Cleanup function failed: {e}")
    
    yield register_cleanup
    
    # Execute cleanup
    cleanup()


# Class-level cleanup support
@pytest.fixture
def test_class_cleanup():
    """Fixture that provides class-level cleanup functionality."""
    class TestClassCleanup:
        def __init__(self):
            self.cleanup_tasks = []
            
        def add_cleanup(self, func):
            """Add a cleanup function to be called at the end of the test class."""
            self.cleanup_tasks.append(func)
            
        def cleanup(self):
            """Execute all cleanup tasks."""
            for task in self.cleanup_tasks:
                try:
                    task()
                except Exception as e:
                    print(f"Warning: Class cleanup task failed: {e}")
    
    cleanup_manager = TestClassCleanup()
    yield cleanup_manager
    cleanup_manager.cleanup()


# pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers", "contract: Contract tests (API interface compliance)"
    )
    config.addinivalue_line(
        "markers", "cleanup: Tests that require specific cleanup procedures"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker for tests in unit directory
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker for tests in integration directory
        elif "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add contract marker for tests in contract directory
        elif "tests/contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
