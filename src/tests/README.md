# Test Suite for d4-snap

This directory contains unit tests for the d4-snap Git snapshot manager.

## Test Structure

### Files
- `conftest.py` - Pytest configuration and shared fixtures
- `test_simple.py` - Basic functionality tests (19 tests passing)
- `test_main.py` - Main CLI module tests
- `test_cli.py` - CLI function tests  
- `test_menu.py` - Menu manager tests
- `test_ui.py` - User interface tests
- `test_tools.py` - Tools and utilities tests
- `test_git_operations.py` - Git operations tests
- `test_snapshot_manager.py` - Snapshot manager tests
- `pytest.ini` - Pytest configuration

### Test Categories

#### BasicFunctionality Tests (9 tests)
- Module imports
- Help system
- CLI argument parsing
- Error handling

#### ConfigLoading Tests (3 tests)  
- Valid YAML loading
- Non-existent file handling
- Empty file handling

#### MenuManager Tests (3 tests)
- Initialization with config
- Message retrieval
- User input prompts

## Running Tests

### Run all tests
```bash
cd src
python -m pytest tests/ -v
```

### Run specific test file
```bash
python -m pytest tests/test_simple.py -v
```

### Run with coverage
```bash
python -m pytest tests/ --cov=d4_snap --cov-report=html
```

## Test Fixtures

### temp_dir
Creates a temporary directory for test files.

### mock_git_repo  
Creates a mock Git repository with initial commit.

### mock_config_file
Creates a mock YAML configuration file.

## Current Status

✅ **19 tests passing** in `test_simple.py`
⏳ **Additional test files** created but need refinement based on actual module structure

## Notes

- Tests use mocking to avoid affecting user's actual environment
- Git operations are mocked to prevent actual Git commands
- Configuration files are created in temp directories
- Tests cover both happy path and error scenarios

## Future Improvements

- Add integration tests with real Git repositories
- Add performance tests for large snapshot sets
- Add tests for edge cases in Git operations
- Add tests for concurrent access scenarios
