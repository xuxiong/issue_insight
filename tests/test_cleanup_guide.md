# Test Cleanup Best Practices

This guide outlines the cleanup patterns and fixtures available for pytest tests in this project.

## Available Cleanup Fixtures

### 1. `temporary_directory`
- Creates a temporary directory for file operations
- Automatically cleans up after tests
- Useful for tests that create files or directories

```python
def test_file_operations(temporary_directory):
    # Create files in the temporary directory
    test_file = temporary_directory / "test.txt"
    test_file.write_text("Hello, World!")
    
    # File will be automatically deleted after test
    assert test_file.exists()
```

### 2. `temporary_file`
- Creates a temporary file
- Automatically deletes it after tests
- Useful for testing file I/O operations

```python
def test_file_reading(temporary_file):
    temporary_file.write_text("Test content")
    
    # File will be automatically deleted after test
    content = temporary_file.read_text()
    assert content == "Test content"
```

### 3. `mock_cleanup`
- Manages mock objects and resets them after tests
- Prevents mock state leakage between tests

```python
def test_with_mocks(mock_cleanup):
    mock_obj = mock_cleanup(Mock())
    # Mock will be reset after test
```

### 4. `cleanup_registry`
- Register custom cleanup functions
- Useful for complex cleanup scenarios

```python
def test_complex_cleanup(cleanup_registry):
    # Create resources that need custom cleanup
    resource = create_complex_resource()
    
    def cleanup_resource():
        resource.cleanup()
        
    cleanup_registry(cleanup_resource)
    # cleanup_resource will be called after test
```

### 5. `test_class_cleanup`
- Provides class-level cleanup functionality
- Useful for test classes that need shared cleanup

```python
class TestMyClass:
    def test_something(self, test_class_cleanup):
        # Add cleanup that should run after all tests in class
        test_class_cleanup.add_cleanup(lambda: print("Class cleanup"))
```

## Test Method Cleanup Patterns

### Using `yield` fixtures
```python
@pytest.fixture
def database_connection():
    conn = create_database_connection()
    yield conn
    conn.close()  # Cleanup runs after test
```

### Using `request.addfinalizer`
```python
@pytest.fixture
def resource_with_finalizer(request):
    resource = create_resource()
    
    def cleanup():
        resource.cleanup()
    
    request.addfinalizer(cleanup)
    return resource
```

### Using `try/finally` in tests
```python
def test_with_manual_cleanup():
    resource = create_resource()
    try:
        # Test code here
        assert resource.is_valid()
    finally:
        # Cleanup runs even if test fails
        resource.cleanup()
```

## Best Practices

1. **Always use cleanup fixtures** when creating external resources
2. **Test cleanup should be idempotent** - safe to run multiple times
3. **Cleanup should handle failures gracefully** - don't let cleanup failures mask test failures
4. **Use appropriate fixture scopes** (`function`, `class`, `module`, `session`)
5. **Document cleanup requirements** in test docstrings

## Common Cleanup Scenarios

### File Operations
```python
def test_file_operations(temporary_directory):
    test_file = temporary_directory / "test.txt"
    test_file.write_text("data")
    # Automatic cleanup: file and directory removed
```

### Database Connections
```python
@pytest.fixture
def db_connection():
    conn = create_db_connection()
    yield conn
    conn.close()  # Ensure connection is closed
```

### Mock Objects
```python
def test_with_mocks(mock_cleanup):
    mock_api = mock_cleanup(Mock())
    # Mock state reset after test
```

### Network Resources
```python
def test_network_operations(cleanup_registry):
    server = start_test_server()
    cleanup_registry(lambda: server.stop())
```

## Testing Cleanup Logic

Test that your cleanup works correctly:

```python
def test_cleanup_works():
    # Create resource
    resource = create_resource()
    
    # Test that cleanup removes the resource
    resource.cleanup()
    assert not resource.exists()
```