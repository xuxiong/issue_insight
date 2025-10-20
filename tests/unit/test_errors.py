"""
Unit tests for error handling (T009-1).

These tests are written FIRST and expected to FAIL until error handling is implemented.
This follows the Test-First Development methodology.
"""

import pytest
from datetime import datetime

# These imports will fail initially (TDD - tests FAIL first)
from lib.errors import (
    GitHubAnalyzerError,
    RepositoryNotFoundError,
    PrivateRepositoryError,
    ValidationError,
    APIError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
)


@pytest.mark.unit
class TestGitHubAnalyzerError:
    """Test custom exception creation and formatting."""

    def test_base_error_creation(self):
        """Test creating base GitHubAnalyzerError."""
        error = GitHubAnalyzerError("Base error message")
        assert str(error) == "Base error message"
        assert error.message == "Base error message"

    def test_base_error_with_context(self):
        """Test base error with additional context."""
        context = {"repository": "facebook/react", "user": "testuser"}
        error = GitHubAnalyzerError("Error with context", context=context)

        assert str(error) == "Error with context"
        assert error.context == context

    def test_base_error_inheritance(self):
        """Test that base error inherits from Exception."""
        error = GitHubAnalyzerError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, GitHubAnalyzerError)


@pytest.mark.unit
class TestRepositoryNotFoundError:
    """Test repository not found error handling."""

    def test_repository_not_found_creation(self):
        """Test creating repository not found error."""
        url = "https://github.com/nonexistent/repo"
        error = RepositoryNotFoundError(url)

        expected_message = "Repository not found or inaccessible. Verify URL and ensure repository is public. Check spelling and try again."
        assert str(error) == expected_message
        assert error.repository_url == url
        assert error.error_code == "REPOSITORY_NOT_FOUND"

    def test_repository_not_found_with_suggestions(self):
        """Test repository not found error with suggestions."""
        url = "https://github.com/facebook/react"
        suggestions = [
            "Check if repository name is spelled correctly",
            "Verify the repository is public",
            "Confirm the repository exists",
        ]

        error = RepositoryNotFoundError(url, suggestions=suggestions)
        assert error.suggestions == suggestions
        assert isinstance(error, GitHubAnalyzerError)

    def test_repository_not_found_from_github_exception(self):
        """Test creating error from GitHub API exception."""
        mock_github_exception = Exception("Not Found")
        url = "https://github.com/owner/repo"

        error = RepositoryNotFoundError.from_github_exception(
            mock_github_exception, url
        )
        assert isinstance(error, RepositoryNotFoundError)
        assert error.repository_url == url


@pytest.mark.unit
class TestPrivateRepositoryError:
    """Test private repository error handling."""

    def test_private_repository_creation(self):
        """Test creating private repository error."""
        url = "https://github.com/owner/private-repo"
        error = PrivateRepositoryError(url)

        expected_message = "Private repositories are not supported. This tool only analyzes public repositories. Use a public repository or consider using GitHub's built-in search for private repositories."
        assert str(error) == expected_message
        assert error.repository_url == url
        assert error.error_code == "PRIVATE_REPOSITORY"

    def test_private_repository_inheritance(self):
        """Test that private repository error inherits correctly."""
        error = PrivateRepositoryError("https://github.com/owner/repo")
        assert isinstance(error, GitHubAnalyzerError)
        assert isinstance(error, ValueError)

    def test_private_repository_with_alternatives(self):
        """Test private repository error with alternatives."""
        url = "https://github.com/company/private-repo"
        alternatives = [
            "Make the repository public",
            "Use GitHub's built-in search for private repositories",
            "Export repository data to a public format",
        ]

        error = PrivateRepositoryError(url, alternatives=alternatives)
        assert error.alternatives == alternatives


@pytest.mark.unit
class TestValidationError:
    """Test input validation error handling."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        field = "min_comments"
        value = -5
        reason = "Comment count must be non-negative"

        error = ValidationError(field, value, reason)

        expected_message = f"Invalid {field}: {value}. {reason}."
        assert str(error) == expected_message
        assert error.field == field
        assert error.value == value
        assert error.reason == reason

    def test_validation_error_for_urls(self):
        """Test validation error specifically for URLs."""
        url = "https://gitlab.com/user/repo"
        expected_reason = "Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react"

        error = ValidationError("repository_url", url, expected_reason)

        assert "Invalid repository URL format" in str(error)
        assert error.field == "repository_url"
        assert error.value == url

    def test_validation_error_for_dates(self):
        """Test validation error for date inputs."""
        date_str = "2024-13-45"  # Invalid date
        expected_reason = "Invalid date format: '2024-13-45'. Use YYYY-MM-DD format. Example: 2024-01-15"

        error = ValidationError("created_since", date_str, expected_reason)

        assert "Invalid date format" in str(error)
        assert "YYYY-MM-DD" in str(error)

    def test_validation_error_for_limits(self):
        """Test validation error for limit values."""
        limit = -10
        expected_reason = "Invalid limit: -10. Limit must be a positive integer. Use --limit 100 or higher."

        error = ValidationError("limit", limit, expected_reason)

        assert "Invalid limit" in str(error)
        assert "positive integer" in str(error)

    def test_validation_error_collection(self):
        """Test creating multiple validation errors."""
        errors = [
            ValidationError("min_comments", -1, "Comment count must be non-negative"),
            ValidationError("limit", 0, "Limit must be at least 1"),
            ValidationError("repository_url", "invalid", "Invalid URL format"),
        ]

        # Test that we can collect multiple errors
        messages = [str(error) for error in errors]
        assert len(messages) == 3
        assert all("Invalid" in msg for msg in messages)


@pytest.mark.unit
class TestAPIError:
    """Test API error handling."""

    def test_api_error_creation(self):
        """Test creating API error."""
        status_code = 500
        message = "Internal Server Error"
        response_data = {"error": "Something went wrong"}

        error = APIError(status_code, message, response_data)

        assert str(error) == message  # APIError.__str__ returns the original message
        assert error.status_code == status_code
        assert error.message == message
        assert error.response_data == response_data

    def test_api_error_from_github_exception(self):
        """Test creating API error from GitHub exception."""
        mock_github_exception = Exception("API Error")
        status_code = 403
        response_data = {"message": "Rate limit exceeded"}

        error = APIError.from_github_exception(
            mock_github_exception, status_code, response_data
        )

        assert isinstance(error, APIError)
        assert error.status_code == status_code
        assert error.response_data == response_data

    def test_api_error_with_retry_info(self):
        """Test API error with retry information."""
        error = APIError(
            status_code=429,
            message="Too Many Requests",
            response_data={"retry_after": 60},
            retry_after=60,
        )

        assert error.retry_after == 60
        assert "429" in str(error)


@pytest.mark.unit
class TestRateLimitError:
    """Test rate limit error handling."""

    def test_rate_limit_error_creation(self):
        """Test creating rate limit error."""
        remaining = 0
        reset_time = datetime.now().timestamp() + 3600  # 1 hour from now
        limit = 5000

        error = RateLimitError(remaining, reset_time, limit)

        expected_message = "GitHub API rate limit exceeded. Wait 60 seconds or use authentication token for higher limits. Set GITHUB_TOKEN environment variable or use --token flag."
        assert error.remaining == remaining
        assert error.reset_time == reset_time
        assert error.limit == limit
        assert error.error_code == "RATE_LIMIT_EXCEEDED"

    def test_rate_limit_error_time_calculation(self):
        """Test rate limit error time calculations."""
        from datetime import datetime, timedelta

        reset_time = (datetime.now() + timedelta(seconds=30)).timestamp()
        error = RateLimitError(0, reset_time, 5000)

        # Should calculate wait time
        import time

        current_time = time.time()
        expected_wait = max(0, int(reset_time - current_time))

        assert error.get_wait_seconds() >= 0
        assert error.get_wait_minutes() == expected_wait / 60

    def test_rate_limit_with_suggestions(self):
        """Test rate limit error with suggestions."""
        error = RateLimitError(50, 0, 5000)

        suggestions = [
            "Wait and retry",
            "Use authentication token for higher limits",
            "Reduce number of requests",
        ]

        error.suggestions = suggestions
        assert error.suggestions == suggestions


@pytest.mark.unit
class TestAuthenticationError:
    """Test authentication error handling."""

    def test_authentication_error_creation(self):
        """Test creating authentication error."""
        token_status = "invalid"
        reason = "Bad credentials"

        error = AuthenticationError(token_status, reason)

        expected_message = f"GitHub authentication failed: {reason}. Please check your token or environment variable."
        assert str(error) == expected_message
        assert error.token_status == token_status
        assert error.reason == reason

    def test_authentication_error_with_help(self):
        """Test authentication error with helpful hints."""
        error = AuthenticationError("missing", "No token provided")
        help_text = "Create a GitHub personal access token at https://github.com/settings/tokens"

        error.help_text = help_text
        assert error.help_text == help_text
        assert "personal access token" in error.help_text

    def test_authentication_error_various_statuses(self):
        """Test different authentication error statuses."""
        test_cases = [
            ("invalid", "Bad credentials"),
            ("expired", "Token has expired"),
            ("missing", "No token provided"),
            ("revoked", "Token has been revoked"),
        ]

        for status, reason in test_cases:
            error = AuthenticationError(status, reason)
            assert error.token_status == status
            assert error.reason == reason


@pytest.mark.unit
class TestNetworkError:
    """Test network error handling."""

    def test_network_error_creation(self):
        """Test creating network error."""
        original_error = ConnectionError("Connection timed out")
        url = "https://api.github.com/repos/owner/repo"
        timeout = 30

        error = NetworkError(original_error, url, timeout)

        expected_message = f"Network error accessing GitHub API: {original_error}"
        assert str(error) == expected_message
        assert error.original_error == original_error
        assert error.url == url
        assert error.timeout == timeout

    def test_network_error_retry_logic(self):
        """Test network error retry suggestions."""
        original_error = TimeoutError("Request timeout")

        error = NetworkError(
            original_error=original_error,
            url="https://api.github.com/repos/owner/repo",
            timeout=30,
            can_retry=True,
            max_retries=3,
        )

        assert error.can_retry is True
        assert error.max_retries == 3
        assert "retry" in str(error).lower()

    def test_network_error_different_types(self):
        """Test different types of network errors."""
        errors = [
            ConnectionError("Connection refused"),
            TimeoutError("Request timeout"),
            OSError("Network unreachable"),
        ]

        for original_error in errors:
            error = NetworkError(original_error, "https://api.github.com/test", 30)
            assert error.original_error == original_error
            assert isinstance(error, GitHubAnalyzerError)


@pytest.mark.unit
class TestErrorMessageStandards:
    """Test that error messages follow spec.md standards exactly."""

    def test_repository_url_errors_match_spec(self):
        """Test repository URL errors match spec.md requirements."""
        # Invalid format
        format_error = ValidationError(
            "repository_url",
            "not-a-url",
            "Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react",
        )
        assert "Expected: https://github.com/owner/repo" in str(format_error)
        assert "Example: https://github.com/facebook/react" in str(format_error)

        # Not found
        not_found_error = RepositoryNotFoundError("https://github.com/owner/repo")
        assert "Repository not found or inaccessible" in str(not_found_error)
        assert "Verify URL and ensure repository is public" in str(not_found_error)

        # Private repository
        private_error = PrivateRepositoryError("https://github.com/owner/private-repo")
        assert "Private repositories are not supported" in str(private_error)
        assert "This tool only analyzes public repositories" in str(private_error)

    def test_filter_value_errors_match_spec(self):
        """Test filter value errors match spec.md requirements."""
        # Negative comments
        comment_error = ValidationError(
            "min_comments",
            -5,
            "Invalid comment count: -5. Comment count must be non-negative integer. Use --min-comments 0 or higher.",
        )
        assert "Comment count must be non-negative integer" in str(comment_error)
        assert "Use --min-comments 0 or higher" in str(comment_error)

        # Invalid date
        date_error = ValidationError(
            "created_since",
            "2024-13-45",
            "Invalid date format: '2024-13-45'. Use YYYY-MM-DD format. Example: 2024-01-15",
        )
        assert "Use YYYY-MM-DD format" in str(date_error)
        assert "Example: 2024-01-15" in str(date_error)

        # Invalid limit
        limit_error = ValidationError(
            "limit",
            -10,
            "Invalid limit: -10. Limit must be a positive integer. Use --limit 100 or higher.",
        )
        assert "Limit must be a positive integer" in str(limit_error)
        assert "Use --limit 100 or higher" in str(limit_error)

    def test_rate_limit_errors_match_spec(self):
        """Test rate limit errors match spec.md requirements."""
        rate_limit_error = RateLimitError(0, 0, 5000)
        expected_message = "GitHub API rate limit exceeded. Wait 60 seconds or use authentication token for higher limits. Set GITHUB_TOKEN environment variable or use --token flag."
        assert str(rate_limit_error) == expected_message
        assert "Wait 60 seconds" in str(rate_limit_error)
        assert "GITHUB_TOKEN environment variable" in str(rate_limit_error)
        assert "--token flag" in str(rate_limit_error)

    def test_error_structure_consistency(self):
        """Test that all errors have consistent structure."""
        errors = [
            GitHubAnalyzerError("Test error"),
            RepositoryNotFoundError("https://github.com/owner/repo"),
            PrivateRepositoryError("https://github.com/owner/repo"),
            ValidationError("field", "value", "reason"),
            APIError(500, "Server error", {}),
            RateLimitError(0, 0, 5000),
            AuthenticationError("invalid", "Bad credentials"),
            NetworkError(ConnectionError("Timeout"), "https://api.github.com", 30),
        ]

        for error in errors:
            # All errors should have a string representation
            assert str(error) is not None
            assert len(str(error)) > 0

            # All errors should inherit from GitHubAnalyzerError
            assert isinstance(error, GitHubAnalyzerError)

            # All errors should have an error_code attribute (or default)
            if hasattr(error, "error_code"):
                assert error.error_code is not None
            else:
                # Default error code should be derived from class name
                expected_code = error.__class__.__name__.upper().replace(
                    "ERROR", "_ERROR"
                )
                assert GitHubAnalyzerError._get_default_error_code(error) is not None


@pytest.mark.unit
class TestErrorPropagationAndLogging:
    """Test error propagation and logging."""

    def test_error_chaining(self):
        """Test that errors can chain underlying causes."""
        original_error = ValueError("Original error")
        wrapped_error = GitHubAnalyzerError("Wrapped error", cause=original_error)

        assert wrapped_error.cause == original_error
        assert "Original error" in str(wrapped_error.cause)

    def test_error_with_logging_context(self):
        """Test error with logging context."""
        context = {
            "timestamp": datetime.now(),
            "user": "testuser",
            "repository": "facebook/react",
            "command": "--min-comments 5",
        }

        error = ValidationError("min_comments", -1, "Must be non-negative")
        error.logging_context = context

        assert error.logging_context == context
        assert "user" in error.logging_context

    def test_error_serialization(self):
        """Test that errors can be serialized for logging."""
        error = RepositoryNotFoundError("https://github.com/owner/repo")

        # Should be able to convert to dict for logging
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
            "repository_url": error.repository_url,
            "error_code": error.error_code,
        }

        assert error_dict["type"] == "RepositoryNotFoundError"
        assert "Repository not found" in error_dict["message"]
        assert error_dict["error_code"] == "REPOSITORY_NOT_FOUND"

    def test_error_handling_in_try_catch(self):
        """Test that errors work properly in try/catch blocks."""
        try:
            raise RepositoryNotFoundError("https://github.com/owner/repo")
        except GitHubAnalyzerError as e:
            assert isinstance(e, RepositoryNotFoundError)
            assert "Repository not found" in str(e)
        except Exception as e:
            pytest.fail(f"Expected GitHubAnalyzerError but got {type(e)}")

    def test_error_factory_methods(self):
        """Test error factory methods for common scenarios."""
        # Test URL validation error factory
        url_error = ValidationError.invalid_url("invalid-url")
        assert url_error.field == "repository_url"
        assert "invalid-url" in str(url_error)

        # Test comment validation error factory
        comment_error = ValidationError.invalid_comment_count(-5)
        assert comment_error.field == "min_comments"
        assert comment_error.value == -5

        # Test rate limit error factory
        rate_error = RateLimitError.from_limits(0, 3600, 5000)
        assert rate_error.remaining == 0
        assert rate_error.limit == 5000
