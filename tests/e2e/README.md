# End-to-End Test Suite

This directory contains comprehensive end-to-end (e2e) tests for the Prema Review Intelligence application using Playwright and pytest.

## Overview

The e2e test suite covers all use cases and features of the application:

### Test Coverage

1. **API Endpoint Tests** (`test_api_endpoints.py`)
   - Health check endpoint
   - Dataset management (create, list, summary)
   - Review listing and filtering
   - Theme extraction
   - All endpoints with descriptive test cases

2. **Dashboard UI Tests** (`test_dashboard_ui.py`)
   - Page loading and initial state
   - Dataset selection and navigation
   - Dataset upload workflow
   - Summary display and metrics
   - Theme visualization
   - User interactions

3. **Error Handling Tests** (`test_error_handling.py`)
   - Invalid file uploads (wrong type, too large, malformed)
   - Missing or invalid parameters
   - Non-existent resources
   - Edge cases and boundary conditions

## Test Structure

```
tests/e2e/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_api_endpoints.py    # API endpoint tests
├── test_dashboard_ui.py     # Streamlit dashboard UI tests
├── test_error_handling.py   # Error scenarios and edge cases
└── README.md               # This file
```

## Prerequisites

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Install Playwright browsers:
   ```bash
   poetry run playwright install chromium
   ```

## Running Tests

### Run All E2E Tests

```bash
poetry run pytest tests/e2e/ -v
```

### Run Specific Test Categories

```bash
# API tests only
poetry run pytest tests/e2e/test_api_endpoints.py -v

# UI tests only
poetry run pytest tests/e2e/test_dashboard_ui.py -v

# Error handling tests only
poetry run pytest tests/e2e/test_error_handling.py -v
```

### Run with Markers

```bash
# Run all e2e tests
poetry run pytest -m e2e -v

# Run API tests
poetry run pytest -m api -v

# Run UI tests
poetry run pytest -m ui -v
```

### Run Specific Test

```bash
poetry run pytest tests/e2e/test_api_endpoints.py::TestHealthEndpoint::test_health_check_returns_ok -v
```

## Test Fixtures

The `conftest.py` file provides several fixtures:

- `test_database`: Creates a temporary test database
- `api_server`: Starts the FastAPI server for testing
- `dashboard_server`: Starts the Streamlit dashboard for testing
- `api_client`: HTTP client for API testing
- `browser`: Playwright browser instance
- `page`: Browser page for UI testing
- `sample_csv_data`: Sample CSV file data for testing
- `sample_json_data`: Sample JSON file data for testing

## Test Descriptions

Each test includes a descriptive docstring explaining:
- What the test verifies
- Expected behavior
- Why it's important

Example:
```python
def test_create_dataset_with_csv_file(self, api_client, sample_csv_data):
    """
    Test creating a dataset by uploading a CSV file.
    
    This is the primary ingestion workflow. Verifies:
    - File upload handling
    - CSV parsing
    - Review import count
    - Dataset creation with metadata
    Expected: 200 with imported review count
    """
```

## Configuration

Test servers are automatically started and stopped by pytest fixtures:
- API server runs on `http://localhost:8000`
- Dashboard server runs on `http://localhost:8501`

You can override these via environment variables:
- `TEST_API_URL`: Override API base URL
- `TEST_DASHBOARD_URL`: Override dashboard URL

## Troubleshooting

### Tests Fail to Start Servers

If tests fail to start servers, ensure:
1. Ports 8000 and 8501 are not in use
2. All dependencies are installed
3. Database directory is writable

### Playwright Browser Issues

If Playwright tests fail:
1. Ensure browsers are installed: `poetry run playwright install chromium`
2. Check that headless mode is working (tests use headless by default)
3. Increase timeouts if tests are slow

### Flaky Tests

Some UI tests may be flaky due to timing. If tests fail intermittently:
1. Check if Streamlit needs more time to render
2. Increase wait times in test fixtures
3. Use explicit waits instead of fixed sleeps

## Best Practices

1. **Descriptive Test Names**: Each test has a clear, descriptive name
2. **Documentation**: All tests include docstrings explaining their purpose
3. **Isolation**: Each test is independent and can run in any order
4. **Cleanup**: Fixtures handle cleanup automatically
5. **Error Messages**: Tests include clear assertions with helpful messages

## Continuous Integration

These tests are designed to run in CI environments:
- Headless browser mode (no display required)
- Automatic server management
- Isolated test database
- Cleanup after test completion

## Adding New Tests

When adding new tests:

1. Follow the existing test structure
2. Add descriptive docstrings
3. Use appropriate fixtures
4. Include both success and error cases
5. Update this README if adding new test categories

## Test Coverage Goals

- ✅ All API endpoints covered
- ✅ All UI workflows covered
- ✅ Error scenarios covered
- ✅ Edge cases covered
- ✅ Security validations covered
