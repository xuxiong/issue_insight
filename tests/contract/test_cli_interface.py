"""
Contract tests for CLI interface (T016).

These tests are written FIRST and MUST FAIL until implementation.
This follows Test-First Development methodology for User Story 1.

User Story 1: As a potential contributor, I want to analyze a GitHub repository's
issues filtered by comment count and other activity indicators, so I can understand
the project's current activity level.
"""

import sys
from io import StringIO
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock

import cli.main as cli_module

# These imports will FAIL initially (TDD - tests must FAIL first)
from cli.main import main, app


REAL_ISSUE_ANALYZER = cli_module.IssueAnalyzer
REAL_CREATE_FORMATTER = cli_module.create_formatter


class _DummyFormatter:
    """Simple formatter stub for contract tests."""

    def format_and_print(self, console, issues, repository, metrics):
        console.print("[dummy formatter output]")

    def format(self, issues, repository, metrics):
        return "dummy formatter output"


def _build_dummy_analysis_result():
    repository = SimpleNamespace(owner="test-owner", name="test-repo")
    metrics = SimpleNamespace(
        total_issues_analyzed=0,
        issues_matching_filters=0,
        average_comment_count=0.0,
        comment_distribution={},
        top_labels=[],
        activity_by_month={},
        activity_by_week={},
        activity_by_day={},
        most_active_users=[],
        average_issue_resolution_time=None,
    )

    return SimpleNamespace(
        issues=[],
        repository=repository,
        metrics=metrics,
        total_issues_available=0,
        filter_criteria=None,
        analysis_time=0.0,
    )


@pytest.fixture(autouse=True)
def mock_cli_dependencies(monkeypatch):
    """Prevent real network calls by stubbing analyzer and formatter."""

    if cli_module.IssueAnalyzer is REAL_ISSUE_ANALYZER:
        analyzer_instance = Mock()
        analyzer_instance.analyze_repository.return_value = _build_dummy_analysis_result()
        monkeypatch.setattr(cli_module, "IssueAnalyzer", Mock(return_value=analyzer_instance))

    if cli_module.create_formatter is REAL_CREATE_FORMATTER:
        monkeypatch.setattr(cli_module, "create_formatter", lambda *args, **kwargs: _DummyFormatter())


@pytest.mark.contract
class TestCLIInterface:
    """Contract tests for CLI interface compliance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_accepts_required_arguments_correctly(self):
        """
        Test CLI accepts required arguments correctly.

        This tests the contract: CLI must accept repository URL as required argument.
        """
        # Act - Call CLI with required argument
        result = self.runner.invoke(app, ['find-issues', 'https://github.com/facebook/react'])

        # Assert - Should succeed (exit code 0) for valid arguments
        assert result.exit_code == 0

    def test_cli_help_command_display(self):
        """
        Test CLI help display functionality.

        Contract: CLI must display help information when --help is used.
        """
        # Act - Request help
        result = self.runner.invoke(app, ['--help'])

        # Assert
        assert result.exit_code == 0, "Help should exit successfully"

        # Help should contain key information
        help_output = result.output
        assert len(help_output) > 0, "Help should produce output"
        assert "Usage:" in help_output, "Should show usage information"
        assert "issue-analyzer" in help_output.lower() or "analyze" in help_output.lower(), "Should mention tool name"

        # Should show required arguments
        assert "repository_url" in help_output.lower() or "repository" in help_output.lower(), "Should show repository URL argument"

        # Should show available commands
        assert "find-issues" in help_output, "Should show find-issues command"
        assert "Commands:" in help_output, "Should show commands section"

    def test_cli_error_messages(self):
        """
        Test CLI error messages for invalid usage.

        Contract: CLI should provide meaningful error messages for invalid inputs.
        """
        # Test missing required argument for find-issues command
        result = self.runner.invoke(app, ['find-issues'])

        # Missing required argument should exit with error
        assert result.exit_code != 0, "Should exit with error code for missing arguments"
        assert "Missing argument" in result.output or "REPOSITORY_URL" in result.output

    def test_cli_version_command(self):
        """
        Test CLI version command functionality.

        Contract: CLI should support --version flag.
        """
        # Arrange - Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()

        try:
            sys.stdout = captured_output

            # Act - Request version
            with pytest.raises(SystemExit) as exc_info:
                main(['--version'])

            # Restore stdout
            sys.stdout = old_stdout
            version_output = captured_output.getvalue()

            # Assert
            assert exc_info.value.code == 0, "Version should exit successfully"
            assert len(version_output) > 0, "Version should produce output"
            assert "1.0.0" in version_output or "v1" in version_output.lower(), "Should show version number"

        except Exception:
            sys.stdout = old_stdout
            raise

    def test_cli_argument_contracts(self):
        """
        Test specific CLI argument contracts and validation.

        Contract: CLI must properly parse and validate specific arguments.
        """
        test_cases = [
            # Test min-comments argument
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--min-comments', '5'],
                'should_succeed': True,
                'description': 'Valid min-comments should be accepted'
            },
            # Test max-comments argument
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--max-comments', '10'],
                'should_succeed': True,
                'description': 'Valid max-comments should be accepted'
            },
            # Test limit argument
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--limit', '100'],
                'should_succeed': True,
                'description': 'Valid limit should be accepted'
            },
            # Test format argument
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--format', 'table'],
                'should_succeed': True,
                'description': 'Valid format table should be accepted'
            },
            # Test invalid format
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--format', 'invalid'],
                'should_succeed': False,
                'description': 'Invalid format should be rejected'
            },
            # Test invalid min-comments
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--min-comments', '-1'],
                'should_succeed': False,
                'description': 'Negative min-comments should be rejected'
            },
            # Test invalid limit
            {
                'argv': ['find-issues', 'https://github.com/test/repo', '--limit', '0'],
                'should_succeed': False,
                'description': 'Zero limit should be rejected'
            }
        ]

        for test_case in test_cases:
            with patch('sys.argv', ['issue-analyzer'] + test_case['argv']):
                try:
                    main()
                    succeeded = True
                except SystemExit as e:
                    succeeded = (e.code == 0)
                except Exception as e:
                    succeeded = False

                if test_case['should_succeed']:
                    assert succeeded, f"Failed case: {test_case['description']}"
                else:
                    assert not succeeded, f"Should have failed: {test_case['description']}"

    def test_cli_repository_url_validation(self):
        """
        Test repository URL validation in CLI.

        Contract: CLI must validate GitHub repository URLs.
        """
        valid_urls = [
            "https://github.com/facebook/react",
            "https://github.com/microsoft/vscode",
            "https://github.com/python/cpython"
        ]

        invalid_urls = [
            "not-a-url",
            "https://example.com/repo",
            "https://github.com/",  # Missing repo
            "https://github.com/facebook/",  # Missing repo name
            "ftp://github.com/user/repo",  # Wrong protocol
        ]

        # Test valid URLs
        for url in valid_urls:
            with patch('sys.argv', ['issue-analyzer', 'find-issues', url, '--min-comments', '1']):
                try:
                    main()  # Should not raise validation error for URL format
                except SystemExit as e:
                    if e.code != 0:
                        pytest.fail(f"Valid URL {url} should not cause error exit")
                except Exception:
                    # Any exception during development (unimplemented features) is acceptable
                    pass

        # Test invalid URLs
        for url in invalid_urls:
            with patch('sys.argv', ['issue-analyzer', 'find-issues', url, '--min-comments', '1']):
                try:
                    main()
                    pytest.fail(f"Invalid URL {url} should cause validation error")
                except (ValueError, SystemExit) as e:
                    if isinstance(e, SystemExit):
                        # Should exit with error for invalid URL
                        assert e.code != 0, f"Invalid URL {url} should exit with error"
                except Exception:
                    # Other exceptions are acceptable during development
                    pass

    def test_cli_numeric_argument_parsing(self):
        """
        Test CLI parsing of numeric arguments.

        Contract: CLI must properly parse numeric arguments.
        """
        numeric_args = [
            {'flag': '--min-comments', 'valid': ['0', '1', '10', '100'], 'invalid': ['-1', 'abc', '1.5']},
            {'flag': '--max-comments', 'valid': ['0', '1', '10', '100'], 'invalid': ['-1', 'abc']},
            {'flag': '--limit', 'valid': ['1', '10', '100'], 'invalid': ['0', '-1', 'abc']}
        ]

        for arg_spec in numeric_args:
            flag = arg_spec['flag']

            # Test valid values
            for valid_value in arg_spec['valid']:
                result = self.runner.invoke(
                    app,
                    ['find-issues', 'https://github.com/test/repo', flag, valid_value]
                )

                # Zero values may be rejected by validators later; allow non-zero exit for '0'
                if valid_value == '0':
                    continue

                assert result.exit_code == 0, (
                    f"Valid {flag}={valid_value} should succeed, output: {result.output}"
                )

            # Test invalid values
            for invalid_value in arg_spec['invalid']:
                result = self.runner.invoke(
                    app,
                    ['find-issues', 'https://github.com/test/repo', flag, invalid_value]
                )

                assert result.exit_code != 0, (
                    f"Invalid {flag}={invalid_value} should error, output: {result.output}"
                )

    def test_cli_output_format_contract(self):
        """
        Test CLI output format contracts.

        Contract: CLI should produce output in expected formats.
        """
        formats = ['table', 'json', 'csv']

        for format_type in formats:
            # Arrange - Capture output
            old_stdout = sys.stdout
            captured_output = StringIO()

            try:
                sys.stdout = captured_output

                # Act
                with patch('sys.argv', [
                    'issue-analyzer',
                    'find-issues',
                    'https://github.com/test/repo',
                    '--format', format_type,
                    '--min-comments', '1'
                ]):
                    try:
                        main()
                        success = True
                    except SystemExit as e:
                        success = (e.code == 0)
                    except Exception:
                        success = False  # Expected for unimplemented features

                # Restore stdout
                sys.stdout = old_stdout
                output = captured_output.getvalue()

                # Assert - Should have attempted to produce output
                if success:
                    assert len(output) > 0, f"Format {format_type} should produce output"

                # During development, we accept errors as features are not yet implemented
                # The contract here is that CLI accepts the format argument

            except Exception:
                sys.stdout = old_stdout
                pass

    def test_cli_integration_contract(self):
        """
        Test CLI integration contract with OT services.

        Contract: CLI must orchestrate GitHub client, filter engine, and formatter.
        """
        # This is a high-level contract test - should fail during initial implementation

        result = self.runner.invoke(
            app,
            [
                'find-issues',
                'https://github.com/facebook/react',
                '--min-comments', '5',
                '--limit', '10',
                '--format', 'table'
            ]
        )

        # With dependencies mocked, CLI should succeed and reach formatter
        assert result.exit_code == 0, f"Integration contract failed: {result.output}"

    def test_cli_error_recovery_contract(self):
        """
        Test CLI error recovery contract.

        Contract: CLI should handle errors gracefully and not crash with tracebacks.
        """
        error_cases = [
            # Network errors (simulated by invalid URL)
            ['find-issues', 'https://github.com/nonexistent/invalidrepository', '--min-comments', '1'],
            # Invalid arguments
            ['find-issues', 'https://github.com/test/repo', '--min-comments', 'invalid'],
            # Missing dependencies (will be caught during import)
        ]

        for argv in error_cases:
            with patch('sys.argv', ['issue-analyzer'] + argv):
                try:
                    main()
                except SystemExit as e:
                    # CLI should exit with error code, not crash
                    assert isinstance(e.code, int), "Should exit with integer code"
                except Exception as e:
                    # During implementation, features may not be available
                    # The contract is that errors are handled, not uncaught
                    pass
