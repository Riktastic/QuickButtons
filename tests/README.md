# QuickButtons Test Suite

This directory contains comprehensive tests for the QuickButtons application.

## Test Structure

The test suite is organized into the following modules:

### Core Tests
- **`test_config_manager.py`** - Tests for configuration management
  - Config loading and saving
  - Default value handling
  - Config validation
  - Backup creation

- **`test_button_manager.py`** - Tests for button management
  - Button grid creation
  - Button addition/removal
  - Grid refresh functionality
  - Button configuration updates

- **`test_button_types.py`** - Tests for button type handlers
  - Website handler
  - Shell command handler
  - Music player handler
  - Python script handler
  - POST request handler
  - LLM handler
  - Button handler factory

- **`test_settings_manager.py`** - Tests for settings management
  - Settings dialog functionality
  - Settings validation
  - Theme updates
  - Language changes
  - Dialog cleanup

### Integration Tests
- **`test_app_integration.py`** - Integration tests for the main application
  - Complete app initialization
  - Manager interactions
  - Minimal mode functionality
  - Language initialization
  - App cleanup

### Utility Tests
- **`test_utils.py`** - Tests for utility functions
  - Logging functionality
  - Translation system
  - System theme detection
  - Animation functions
  - Easter egg detection

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Module
```bash
python tests/run_tests.py test_config_manager
python tests/run_tests.py test_button_manager
python tests/run_tests.py test_button_types
python tests/run_tests.py test_settings_manager
python tests/run_tests.py test_app_integration
python tests/run_tests.py test_utils
```

### Run Individual Test Classes
```bash
python -m unittest tests.test_config_manager.TestConfigManager
python -m unittest tests.test_button_manager.TestButtonManager
```

### Run Specific Test Methods
```bash
python -m unittest tests.test_config_manager.TestConfigManager.test_config_loading
```

## Test Coverage

The test suite covers the most important features:

### ✅ Configuration Management
- Config file loading and saving
- Default value handling
- Config validation and error recovery
- Backup file creation

### ✅ Button Management
- Button grid creation and management
- Button addition, editing, and removal
- Grid refresh functionality
- Button configuration updates

### ✅ Button Types
- All supported button types (website, shell, music, python script, POST, LLM)
- Button type validation
- Action execution
- Error handling

### ✅ Settings Management
- Settings dialog functionality
- Settings validation
- Theme switching
- Language changes
- Minimal mode toggling

### ✅ Application Integration
- Complete app initialization
- Manager interactions
- Component communication
- App cleanup and shutdown

### ✅ Utility Functions
- Logging system
- Translation management
- System theme detection
- Animation functions
- Easter egg functionality

## Test Dependencies

The tests use the following Python modules:
- `unittest` - Core testing framework
- `unittest.mock` - Mocking and patching
- `tempfile` - Temporary file creation
- `tkinter` - GUI testing (minimal usage)
- `json` - Config file handling
- `os` and `sys` - System operations

## Mock Strategy

The tests use extensive mocking to:
- Isolate units under test
- Avoid file system dependencies
- Prevent GUI windows from appearing
- Mock external dependencies (web requests, system calls)
- Control test environment

## Test Data

Tests use temporary files and directories that are automatically cleaned up:
- Temporary config files
- Test button configurations
- Mock theme data
- Test translation data

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No GUI dependencies (tests run headless)
- Fast execution (mocked external calls)
- Clear pass/fail reporting
- Proper exit codes for CI systems

## Adding New Tests

When adding new functionality, follow these guidelines:

1. **Create corresponding test file** - `test_<module_name>.py`
2. **Test public interfaces** - Focus on public methods and APIs
3. **Use descriptive test names** - Clear test method names
4. **Mock external dependencies** - Don't rely on external services
5. **Clean up resources** - Use `setUp()` and `tearDown()` methods
6. **Test edge cases** - Include error conditions and boundary cases

## Test Maintenance

- Keep tests up to date with code changes
- Refactor tests when code is refactored
- Add tests for new features
- Remove tests for removed functionality
- Update mocks when interfaces change 