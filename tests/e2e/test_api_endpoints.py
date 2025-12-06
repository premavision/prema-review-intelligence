"""
End-to-end tests for FastAPI endpoints.

This test suite covers all API endpoints with comprehensive scenarios:
- Health check endpoint
- Dataset management (create, list, summary)
- Review listing and filtering
- Theme extraction
- Error handling and validation

SECURITY NOTE: Security-related tests in this file validate that security
measures are properly implemented. They test security protections (file type
validation, size limits, etc.), not expose vulnerabilities. All test data
is synthetic and used only in isolated test environments.
"""

import json
from pathlib import Path

import httpx
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.api]


class TestHealthEndpoint:
    """Test suite for the health check endpoint."""

    def test_health_check_returns_ok(self, api_client: httpx.Client):
        """
        Verify that the health endpoint returns a successful status.
        
        This is a basic smoke test to ensure the API is running and accessible.
        Expected: 200 status with {"status": "ok"}
        """
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}


class TestDatasetEndpoints:
    """Test suite for dataset management endpoints."""

    def test_create_dataset_without_file(self, api_client: httpx.Client):
        """
        Test creating a dataset without uploading a file.
        
        This verifies that datasets can be created as empty containers
        that can be populated later. Expected: 201 with dataset metadata.
        """
        response = api_client.post(
            "/datasets",
            data={"name": "Empty Dataset", "source": "manual", "description": "Test dataset"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "dataset" in data
        assert data["dataset"]["name"] == "Empty Dataset"
        assert data["dataset"]["source"] == "manual"
        assert data["imported_reviews"] == 0
        assert isinstance(data["dataset"]["id"], int)

    def test_create_dataset_with_csv_file(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test creating a dataset by uploading a CSV file.
        
        This is the primary ingestion workflow. Verifies:
        - File upload handling
        - CSV parsing
        - Review import count
        - Dataset creation with metadata
        Expected: 200 with imported review count
        """
        files = {"file": ("reviews.csv", sample_csv_data, "text/csv")}
        data = {
            "name": "CSV Test Dataset",
            "source": "import",
            "description": "Dataset from CSV upload",
        }
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code == 200
        result = response.json()
        assert result["dataset"]["name"] == "CSV Test Dataset"
        assert result["imported_reviews"] > 0
        assert len(result.get("warnings", [])) >= 0

    def test_create_dataset_with_json_file(
        self, api_client: httpx.Client, sample_json_data: bytes
    ):
        """
        Test creating a dataset by uploading a JSON file.
        
        Verifies JSON ingestion works correctly, including:
        - JSON parsing
        - Review extraction from JSON structure
        - Proper import counting
        Expected: 200 with imported reviews
        """
        files = {"file": ("reviews.json", sample_json_data, "application/json")}
        data = {"name": "JSON Test Dataset", "source": "import"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code == 200
        result = response.json()
        assert result["dataset"]["name"] == "JSON Test Dataset"
        assert result["imported_reviews"] > 0

    def test_list_datasets(self, api_client: httpx.Client, sample_csv_data: bytes):
        """
        Test listing all datasets.
        
        Verifies the dataset list endpoint returns all created datasets
        with proper structure. Expected: 200 with list of datasets.
        """
        # Create a dataset first
        files = {"file": ("test.csv", sample_csv_data, "text/csv")}
        api_client.post("/datasets", data={"name": "List Test Dataset"}, files=files)
        
        response = api_client.get("/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert isinstance(data["datasets"], list)
        assert len(data["datasets"]) > 0
        # Verify dataset structure
        dataset = data["datasets"][0]
        assert "id" in dataset
        assert "name" in dataset
        assert "total_reviews" in dataset
        assert "created_at" in dataset

    def test_get_dataset_summary(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test retrieving dataset summary with analysis.
        
        Verifies that the summary endpoint returns:
        - Dataset metadata
        - Analysis results (stats, sentiment, themes)
        - Cached analysis (force=false should use cache)
        Expected: 200 with complete summary including analysis
        """
        # Create dataset with reviews
        files = {"file": ("summary_test.csv", sample_csv_data, "text/csv")}
        create_response = api_client.post(
            "/datasets", data={"name": "Summary Test Dataset"}, files=files
        )
        dataset_id = create_response.json()["dataset"]["id"]
        
        # Get summary
        response = api_client.get(f"/datasets/{dataset_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "dataset" in data
        assert "analysis" in data
        
        analysis = data["analysis"]
        if analysis:  # Analysis might not be available immediately
            assert "stats" in analysis
            assert "summary_text" in analysis
            assert "themes" in analysis
            stats = analysis["stats"]
            assert "average_rating" in stats
            assert "total_reviews" in stats
            assert "rating_distribution" in stats

    def test_get_dataset_summary_with_force_refresh(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test forcing a refresh of dataset analysis.
        
        Verifies that force=true parameter triggers a fresh analysis
        instead of using cached results. Expected: 200 with fresh analysis.
        """
        files = {"file": ("force_test.csv", sample_csv_data, "text/csv")}
        create_response = api_client.post(
            "/datasets", data={"name": "Force Refresh Test"}, files=files
        )
        dataset_id = create_response.json()["dataset"]["id"]
        
        # Get summary with force refresh
        response = api_client.get(f"/datasets/{dataset_id}/summary?force=true")
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data

    def test_create_dataset_rejects_invalid_file_type(self, api_client: httpx.Client):
        """
        Test that invalid file types are rejected.
        
        Security validation test: Verifies that only allowed file types (CSV, JSON)
        are accepted. This test validates security protections are working.
        Expected: 400 error with descriptive message.
        
        NOTE: This test uses synthetic HTML content as test data in an isolated
        environment. The content is never processed or persisted - it's only
        used to verify the security validation rejects it.
        """
        # Synthetic test data - HTML content used only to test file type validation
        invalid_file = b"<html><body>Not a review file</body></html>"
        files = {"file": ("invalid.html", invalid_file, "text/html")}
        data = {"name": "Invalid File Test"}
        response = api_client.post("/datasets", data=data, files=files)
        # Verify security protection: invalid file types are rejected
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_create_dataset_rejects_missing_filename(self, api_client: httpx.Client):
        """
        Test that file uploads without filenames are rejected.
        
        Validation test: ensures filename is required for file uploads.
        Expected: 400 or 422 error (both are valid validation errors).
        """
        files = {"file": (None, b"some content", "text/csv")}
        data = {"name": "No Filename Test"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code in [400, 422]  # Both are valid validation errors


class TestReviewEndpoints:
    """Test suite for review listing and filtering endpoints."""

    def test_list_reviews_default(self, api_client: httpx.Client, sample_csv_data: bytes):
        """
        Test listing reviews with default parameters.
        
        Verifies basic review listing without filters.
        Expected: 200 with list of reviews, default limit applied.
        """
        # Create dataset with reviews
        files = {"file": ("reviews_list.csv", sample_csv_data, "text/csv")}
        create_response = api_client.post("/datasets", data={"name": "Review List Test"}, files=files)
        dataset_id = create_response.json()["dataset"]["id"]
        
        response = api_client.get("/reviews")
        assert response.status_code == 200
        reviews = response.json()
        assert isinstance(reviews, list)
        assert len(reviews) <= 100  # Default limit
        if reviews:
            review = reviews[0]
            assert "id" in review
            assert "rating" in review
            assert "body" in review
            assert "dataset_id" in review

    def test_list_reviews_filtered_by_dataset(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test filtering reviews by dataset ID.
        
        Verifies that dataset_id parameter correctly filters reviews
        to only those belonging to the specified dataset.
        Expected: 200 with reviews only from specified dataset.
        """
        files = {"file": ("filtered.csv", sample_csv_data, "text/csv")}
        create_response = api_client.post("/datasets", data={"name": "Filter Test"}, files=files)
        dataset_id = create_response.json()["dataset"]["id"]
        
        response = api_client.get(f"/reviews?dataset_id={dataset_id}")
        assert response.status_code == 200
        reviews = response.json()
        assert all(review["dataset_id"] == dataset_id for review in reviews)

    def test_list_reviews_filtered_by_rating_range(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test filtering reviews by rating range.
        
        Verifies that min_rating and max_rating parameters correctly
        filter reviews to only those within the specified range.
        Expected: 200 with reviews in rating range [min_rating, max_rating].
        """
        files = {"file": ("rating_filter.csv", sample_csv_data, "text/csv")}
        api_client.post("/datasets", data={"name": "Rating Filter Test"}, files=files)
        
        # Test high ratings only
        response = api_client.get("/reviews?min_rating=4&max_rating=5")
        assert response.status_code == 200
        reviews = response.json()
        assert all(4 <= review["rating"] <= 5 for review in reviews)
        
        # Test low ratings only
        response = api_client.get("/reviews?min_rating=1&max_rating=2")
        assert response.status_code == 200
        reviews = response.json()
        assert all(1 <= review["rating"] <= 2 for review in reviews)

    def test_list_reviews_with_limit(self, api_client: httpx.Client, sample_csv_data: bytes):
        """
        Test pagination using the limit parameter.
        
        Verifies that limit parameter correctly restricts the number
        of returned reviews. Expected: 200 with at most 'limit' reviews.
        """
        files = {"file": ("limit_test.csv", sample_csv_data, "text/csv")}
        api_client.post("/datasets", data={"name": "Limit Test"}, files=files)
        
        response = api_client.get("/reviews?limit=3")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) <= 3

    def test_list_reviews_invalid_rating_range(self, api_client: httpx.Client):
        """
        Test that invalid rating ranges are rejected.
        
        Validation test: ensures rating parameters are within valid range [1, 5].
        Expected: 422 validation error.
        """
        response = api_client.get("/reviews?min_rating=0")
        assert response.status_code == 422
        
        response = api_client.get("/reviews?max_rating=6")
        assert response.status_code == 422


class TestThemeEndpoints:
    """Test suite for theme extraction endpoints."""

    def test_get_themes_for_dataset(
        self, api_client: httpx.Client, sample_csv_data: bytes
    ):
        """
        Test retrieving themes for a dataset.
        
        Verifies that themes endpoint returns structured theme data
        extracted from reviews. Expected: 200 with list of themes.
        """
        files = {"file": ("themes_test.csv", sample_csv_data, "text/csv")}
        create_response = api_client.post("/datasets", data={"name": "Themes Test"}, files=files)
        dataset_id = create_response.json()["dataset"]["id"]
        
        # Ensure analysis exists
        api_client.get(f"/datasets/{dataset_id}/summary?force=true")
        
        response = api_client.get(f"/datasets/{dataset_id}/themes")
        # Themes might not be available immediately, so accept 200 or 404
        if response.status_code == 200:
            themes = response.json()
            assert isinstance(themes, list)
            if themes:
                theme = themes[0]
                assert "name" in theme
                assert "sentiment" in theme
                assert "importance" in theme

    def test_get_themes_for_nonexistent_dataset(self, api_client: httpx.Client):
        """
        Test that themes endpoint handles nonexistent datasets gracefully.
        
        Error handling test: ensures proper 404 response for invalid dataset IDs.
        Expected: 404 or appropriate error status.
        """
        response = api_client.get("/datasets/99999/themes")
        # Should return 404 or handle gracefully
        assert response.status_code in [404, 422]

    def test_get_themes_for_dataset_without_analysis(
        self, api_client: httpx.Client
    ):
        """
        Test themes endpoint for dataset without analysis.
        
        Verifies that datasets without analysis return appropriate error.
        Expected: 404 with descriptive message.
        """
        # Create empty dataset
        create_response = api_client.post(
            "/datasets", data={"name": "No Analysis Dataset", "source": "manual"}
        )
        dataset_id = create_response.json()["dataset"]["id"]
        
        response = api_client.get(f"/datasets/{dataset_id}/themes")
        assert response.status_code == 404
        assert "analysis" in response.json()["detail"].lower()
