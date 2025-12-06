"""
Pytest configuration and fixtures for e2e tests.

This module provides:
- Test server management (FastAPI and Streamlit)
- Test database setup/teardown
- API client fixtures
- Browser fixtures for Playwright
- Test data helpers

SECURITY NOTE: All test data is synthetic and used only in isolated test
environments. Test databases are temporary and cleaned up after tests.
No production data or real user data is used in these tests.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator

import httpx
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

# Test configuration
API_BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
DASHBOARD_URL = os.getenv("TEST_DASHBOARD_URL", "http://localhost:8501")
TEST_DB_PATH = tempfile.mktemp(suffix=".db", dir=tempfile.gettempdir())


@pytest.fixture(scope="session")
def test_database() -> Generator[str, None, None]:
    """
    Create a temporary test database.
    
    Returns the path to the test database file.
    The database is cleaned up after all tests complete.
    """
    # Ensure the directory exists
    db_path = Path(TEST_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    yield TEST_DB_PATH
    
    # Cleanup: remove test database
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="session")
def api_server(test_database: str) -> Generator[str, None, None]:
    """
    Start the FastAPI server for testing.
    
    Sets up environment variables for test database and starts the server.
    Waits for the server to be ready before yielding.
    """
    # Set test database URL
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{test_database}"
    os.environ["APP_ENV"] = "local"
    
    # Ensure database directory exists
    db_path = Path(test_database)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Start server in background
    # Use DEVNULL to avoid deadlock from unread pipe buffer
    # Server logs aren't needed for tests - errors are caught via health checks
    process = subprocess.Popen(
        ["poetry", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )
    
    # Wait for server to be ready
    max_attempts = 30
    server_ready = False
    for attempt in range(max_attempts):
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
        
        # Check if process has died
        if process.poll() is not None:
            # Process has terminated
            error_msg = f"API server process exited with code {process.returncode}"
            raise RuntimeError(error_msg)
    
    if not server_ready:
        process.terminate()
        error_msg = "API server failed to start within timeout"
        raise RuntimeError(error_msg)
    
    yield API_BASE_URL
    
    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except Exception:
        pass  # Process may already be terminated
    
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def dashboard_server(api_server: str) -> Generator[str, None, None]:
    """
    Start the Streamlit dashboard for testing.
    
    Requires the API server to be running.
    Waits for the dashboard to be ready before yielding.
    """
    # Set API base URL for dashboard
    original_api_url = os.environ.get("REVIEW_API_BASE_URL")
    os.environ["REVIEW_API_BASE_URL"] = API_BASE_URL
    
    # Start Streamlit in background
    # Use DEVNULL to avoid deadlock from unread pipe buffer
    # Dashboard logs aren't needed for tests - errors are caught via health checks
    process = subprocess.Popen(
        ["poetry", "run", "streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )
    
    # Wait for dashboard to be ready
    max_attempts = 30
    dashboard_ready = False
    for attempt in range(max_attempts):
        try:
            response = httpx.get(f"{DASHBOARD_URL}", timeout=2)
            if response.status_code == 200:
                dashboard_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
        
        # Check if process has died
        if process.poll() is not None:
            # Process has terminated
            error_msg = f"Dashboard server process exited with code {process.returncode}"
            raise RuntimeError(error_msg)
    
    if not dashboard_ready:
        process.terminate()
        error_msg = "Dashboard server failed to start within timeout"
        raise RuntimeError(error_msg)
    
    yield DASHBOARD_URL
    
    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except Exception:
        pass  # Process may already be terminated
    
    if original_api_url:
        os.environ["REVIEW_API_BASE_URL"] = original_api_url
    else:
        os.environ.pop("REVIEW_API_BASE_URL", None)


@pytest.fixture
def api_client(api_server: str) -> Generator[httpx.Client, None, None]:
    """
    Create an HTTP client for API testing.
    
    Provides a configured httpx client pointing to the test API server.
    """
    with httpx.Client(base_url=api_server, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """
    Initialize Playwright for browser testing.
    
    This fixture manages the Playwright instance lifecycle.
    """
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Generator[Browser, None, None]:
    """
    Launch a browser instance for testing.
    
    Uses Chromium browser in headless mode for CI compatibility.
    """
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def browser_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create a new browser context for each test.
    
    Provides isolation between tests by creating a fresh context.
    """
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture
def page(browser_context: BrowserContext, dashboard_server: str) -> Generator[Page, None, None]:
    """
    Create a new page for each test.
    
    Navigates to the dashboard URL and provides a clean page for testing.
    """
    page = browser_context.new_page()
    page.goto(dashboard_server)
    yield page
    page.close()


@pytest.fixture
def sample_csv_data() -> bytes:
    """
    Generate sample CSV data for testing dataset uploads.
    
    Returns bytes of a valid CSV file with review data.
    """
    csv_content = """product_id,product_name,platform,rating,title,body,created_at
SKU-1000,Orbit Smartwatch,amazon,5,Love the battery,"Battery lasts me three days even with GPS on.",2024-09-01
SKU-1000,Orbit Smartwatch,amazon,2,Charger broke,"Wish the charger cable was sturdier. Broke after a month.",2024-09-05
SKU-1000,Orbit Smartwatch,shopify,4,Sleek design,"Looks amazing and fits under shirt cuffs.",2024-09-10
SKU-2000,Aero Buds,amazon,1,Uncomfortable,"These hurt after 20 minutes. Need softer tips.",2024-08-20
SKU-2000,Aero Buds,amazon,5,Great sound,"Bass is punchy and calls are crystal clear.",2024-08-22
SKU-2000,Aero Buds,shopify,3,Battery meh,"Battery life could be longer; lasts about 3 hours.",2024-08-25
SKU-3000,Comfy Sneakers,amazon,4,So comfy,"Feels like walking on clouds. Would love more colors.",2024-07-15
SKU-3000,Comfy Sneakers,amazon,2,Sizing off,"Runs small and returns process was clunky.",2024-07-20
"""
    return csv_content.encode("utf-8")


@pytest.fixture
def sample_json_data() -> bytes:
    """
    Generate sample JSON data for testing dataset uploads.
    
    Returns bytes of a valid JSON file with review data.
    """
    import json
    
    json_content = [
        {
            "product_id": "SKU-4000",
            "product_name": "Wireless Mouse",
            "platform": "amazon",
            "rating": 5,
            "title": "Perfect tracking",
            "body": "Works flawlessly on any surface. Great battery life.",
            "created_at": "2024-10-01",
        },
        {
            "product_id": "SKU-4000",
            "product_name": "Wireless Mouse",
            "platform": "amazon",
            "rating": 3,
            "title": "Okay but not great",
            "body": "Does the job but feels cheap. Scroll wheel is noisy.",
            "created_at": "2024-10-05",
        },
    ]
    return json.dumps(json_content).encode("utf-8")
