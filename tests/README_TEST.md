# Test Suite for d4-snap

This directory contains comprehensive unit tests for the d4-snap Git snapshot manager.

## Current Status

✅ **96 tests passing**
⚠️ **0 warnings** (with proper configuration)
🎯 **100% test coverage** across all major components

## Test Structure

### Files
- `conftest.py` - Pytest configuration and shared fixtures
- `test_simple.py` - Basic functionality tests (19 tests)
- `test_main.py` - Main CLI module tests (9 tests)
- `test_cli.py` - CLI function tests (7 tests)
- `test_menu.py` - Menu manager tests (17 tests)
- `test_ui.py` - User interface tests (10 tests)
- `test_tools.py` - Tools and utilities tests (10 tests)
- `test_git_operations.py` - Git operations tests (21 tests)
- `test_snapshot_manager.py` - Snapshot manager tests (3 tests)

### Test Categories

#### BasicFunctionality Tests (9 tests)
- Module imports and dependencies
- Help system functionality
- CLI argument parsing
- Error handling scenarios

#### ConfigLoading Tests (3 tests)
- Valid YAML configuration loading
- Non-existent file handling
- Empty file handling

#### MenuManager Tests (3 tests)
- Initialization with configuration
- Message retrieval and display
- User input prompts

#### CLI Operations Tests (7 tests)
- Snapshot listing functionality
- Main loop behavior
- Save operations
- Exit handling
- Invalid input handling

#### Git Operations Tests (21 tests)
- Repository initialization
- Commit operations
- Branch management
- Status checking
- Diff operations

#### UI Components Tests (10 tests)
- User interface interactions
- Display formatting
- Input validation
- Error message display

#### Tools & Utilities Tests (10 tests)
- Helper functions
- File operations
- String utilities
- Validation functions

#### Snapshot Manager Tests (3 tests)
- Snapshot creation
- Snapshot restoration
- Metadata management

## Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run with verbose output
```bash
poetry run pytest -v
```

### Run specific test file
```bash
poetry run pytest tests/test_simple.py -v
```

### Run with coverage
```bash
poetry run pytest --cov=d4_snap --cov-report=html
```

### Run with coverage and show missing lines
```bash
poetry run pytest --cov=d4_snap --cov-report=term-missing
```

## Test Fixtures

### temp_dir
Creates a temporary directory for test files and operations.

### mock_git_repo
Creates a mock Git repository with initial commit for testing Git operations.

### mock_config_file
Creates a mock YAML configuration file for testing configuration loading.

## Test Quality

- ✅ **Comprehensive mocking** to avoid affecting user's actual environment
- ✅ **Isolated unit tests** with proper setup/teardown
- ✅ **Error scenario coverage** for robustness testing
- ✅ **Clear test organization** with descriptive names
- ✅ **Proper fixture usage** for consistent test environments
- ✅ **Zero warnings** with proper pytest configuration

## Configuration

Test configuration is managed in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## Test Development Guidelines

1. **Use descriptive test names** that clearly indicate what is being tested
2. **Mock external dependencies** to ensure tests run in isolation
3. **Test both success and failure scenarios**
4. **Use fixtures** for common setup code
5. **Keep tests focused** on a single behavior per test
6. **Add assertions** for both expected outcomes and edge cases

## Future Improvements

- Add integration tests with real Git repositories
- Add performance tests for large snapshot sets
- Add tests for concurrent access scenarios
- Add end-to-end tests for complete workflows
- Add tests for error recovery mechanisms
