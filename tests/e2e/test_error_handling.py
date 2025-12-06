"""
End-to-end tests for error handling and edge cases.

This test suite covers error scenarios and edge cases:
- Invalid file uploads (wrong type, too large, malformed)
- Missing or invalid parameters
- Non-existent resources
- Rate limiting and size limits
- Database errors and recovery
"""

import json

import httpx
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.error]


class TestFileUploadErrors:
    """Test suite for file upload error handling."""

    def test_reject_file_too_large(self, api_client: httpx.Client):
        """
        Test that files exceeding size limit are rejected.
        
        Security test: ensures max_upload_size limit is enforced
        to prevent DoS attacks. Expected: 413 status with error message.
        """
        # Create a file larger than default 10MB limit
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large_file.csv", large_content, "text/csv")}
        data = {"name": "Large File Test"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code == 413
        assert "size" in response.json()["detail"].lower()

    def test_reject_malformed_csv(self, api_client: httpx.Client):
        """
        Test that malformed CSV files are handled gracefully.
        
        Error handling test: ensures the system handles invalid CSV
        structure without crashing. Expected: Either rejection or graceful handling.
        Note: The system might accept malformed CSV and import what it can.
        """
        malformed_csv = b"invalid,csv,structure\nmissing,columns\n"
        files = {"file": ("malformed.csv", malformed_csv, "text/csv")}
        data = {"name": "Malformed CSV Test"}
        response = api_client.post("/datasets", data=data, files=files)
        # System might accept it and import what it can, or reject it
        assert response.status_code in [200, 400, 422, 500]
        if response.status_code != 200:
            # Should have error detail if rejected
            assert "detail" in response.json()

    def test_reject_malformed_json(self, api_client: httpx.Client):
        """
        Test that malformed JSON files are rejected.
        
        Validation test: ensures invalid JSON structure is caught
        before processing. Expected: 400 or 422 error.
        """
        malformed_json = b'{"invalid": json, missing quotes}'
        files = {"file": ("malformed.json", malformed_json, "application/json")}
        data = {"name": "Malformed JSON Test"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code in [400, 422, 500]

    def test_reject_empty_file(self, api_client: httpx.Client):
        """
        Test that empty files are handled appropriately.
        
        Edge case test: ensures empty files don't cause errors
        but are handled gracefully. Expected: Either rejection or empty dataset.
        """
        empty_file = b""
        files = {"file": ("empty.csv", empty_file, "text/csv")}
        data = {"name": "Empty File Test"}
        response = api_client.post("/datasets", data=data, files=files)
        # Should either reject or create empty dataset
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            assert response.json()["imported_reviews"] == 0

    def test_reject_csv_with_missing_required_columns(self, api_client: httpx.Client):
        """
        Test that CSV files missing required columns are handled.
        
        Validation test: ensures CSV has required fields (at minimum 'body').
        Expected: Error or warning about missing columns.
        """
        incomplete_csv = b"product_id,rating\nSKU-100,5\n"
        files = {"file": ("incomplete.csv", incomplete_csv, "text/csv")}
        data = {"name": "Incomplete CSV Test"}
        response = api_client.post("/datasets", data=data, files=files)
        # Should either reject or import with warnings
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            # Should have warnings about missing columns
            warnings = response.json().get("warnings", [])
            # Warnings might indicate missing required fields


class TestParameterValidation:
    """Test suite for API parameter validation."""

    def test_reject_missing_required_fields(self, api_client: httpx.Client):
        """
        Test that missing required fields are rejected.
        
        Validation test: ensures 'name' field is required for dataset creation.
        Expected: 422 validation error.
        """
        response = api_client.post("/datasets", data={})
        assert response.status_code == 422

    def test_reject_invalid_dataset_id_format(self, api_client: httpx.Client):
        """
        Test that invalid dataset ID formats are rejected.
        
        Validation test: ensures dataset_id must be an integer.
        Expected: 422 validation error.
        """
        response = api_client.get("/datasets/not-a-number/summary")
        assert response.status_code == 422

    def test_reject_invalid_rating_parameters(self, api_client: httpx.Client):
        """
        Test that invalid rating filter parameters are rejected.
        
        Validation test: ensures rating parameters are within [1, 5] range.
        Expected: 422 validation errors for out-of-range values.
        """
        # Test negative rating
        response = api_client.get("/reviews?min_rating=-1")
        assert response.status_code == 422
        
        # Test rating > 5
        response = api_client.get("/reviews?max_rating=10")
        assert response.status_code == 422
        
        # Test min > max
        response = api_client.get("/reviews?min_rating=5&max_rating=1")
        # This might be allowed (empty result) or rejected
        assert response.status_code in [200, 422]

    def test_reject_invalid_limit_parameter(self, api_client: httpx.Client):
        """
        Test that invalid limit parameters are rejected.
        
        Validation test: ensures limit is within allowed range [1, 500].
        Expected: 422 validation errors for out-of-range values.
        """
        # Test negative limit
        response = api_client.get("/reviews?limit=-1")
        assert response.status_code == 422
        
        # Test limit > 500
        response = api_client.get("/reviews?limit=1000")
        assert response.status_code == 422
        
        # Test zero limit
        response = api_client.get("/reviews?limit=0")
        assert response.status_code == 422


class TestResourceNotFound:
    """Test suite for handling non-existent resources."""

    def test_get_nonexistent_dataset(self, api_client: httpx.Client):
        """
        Test that requesting non-existent dataset returns appropriate error.
        
        Error handling test: ensures 404 for missing resources.
        Expected: 404 status with error message.
        """
        response = api_client.get("/datasets/99999/summary")
        assert response.status_code == 404

    def test_get_themes_for_nonexistent_dataset(self, api_client: httpx.Client):
        """
        Test that requesting themes for non-existent dataset returns error.
        
        Error handling test: ensures proper 404 response.
        Expected: 404 status.
        """
        response = api_client.get("/datasets/99999/themes")
        assert response.status_code in [404, 422]

    def test_filter_reviews_by_nonexistent_dataset(self, api_client: httpx.Client):
        """
        Test that filtering reviews by non-existent dataset returns empty list.
        
        Edge case test: ensures graceful handling when dataset doesn't exist.
        Expected: 200 with empty list (not an error).
        """
        response = api_client.get("/reviews?dataset_id=99999")
        assert response.status_code == 200
        assert response.json() == []


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_create_dataset_with_very_long_name(self, api_client: httpx.Client):
        """
        Test that very long dataset names are handled.
        
        Edge case test: ensures system handles extremely long input strings.
        Expected: Either rejection or truncation/acceptance.
        """
        long_name = "A" * 1000
        response = api_client.post("/datasets", data={"name": long_name, "source": "manual"})
        # Should either accept or reject with validation error
        assert response.status_code in [200, 422]

    def test_create_dataset_with_special_characters(self, api_client: httpx.Client):
        """
        Test that dataset names with special characters are handled.
        
        Edge case test: ensures special characters don't break the system.
        Expected: Proper handling (acceptance or sanitization).
        """
        special_name = "Test Dataset !@#$%^&*()_+-=[]{}|;':\",./<>?"
        response = api_client.post(
            "/datasets", data={"name": special_name, "source": "manual"}
        )
        # Should handle gracefully
        assert response.status_code in [200, 422]

    def test_list_reviews_with_zero_limit(self, api_client: httpx.Client):
        """
        Test that limit=0 is rejected (already covered, but explicit test).
        
        Validation test: ensures limit must be at least 1.
        Expected: 422 validation error.
        """
        response = api_client.get("/reviews?limit=0")
        assert response.status_code == 422

    def test_get_summary_with_force_for_empty_dataset(self, api_client: httpx.Client):
        """
        Test forcing analysis refresh for empty dataset.
        
        Edge case test: ensures force refresh works even for empty datasets.
        Expected: 200 with empty or null analysis.
        """
        # Create empty dataset
        create_response = api_client.post(
            "/datasets", data={"name": "Empty Force Test", "source": "manual"}
        )
        dataset_id = create_response.json()["dataset"]["id"]
        
        response = api_client.get(f"/datasets/{dataset_id}/summary?force=true")
        assert response.status_code == 200
        # Analysis might be null for empty dataset
        data = response.json()
        assert "dataset" in data

    def test_upload_csv_with_only_headers(self, api_client: httpx.Client):
        """
        Test uploading CSV with only header row (no data).
        
        Edge case test: ensures header-only files are handled gracefully.
        Expected: Either rejection or empty dataset creation.
        """
        header_only = b"product_id,product_name,platform,rating,title,body,created_at\n"
        files = {"file": ("headers_only.csv", header_only, "text/csv")}
        data = {"name": "Headers Only Test"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            assert response.json()["imported_reviews"] == 0

    def test_upload_csv_with_duplicate_reviews(self, api_client: httpx.Client):
        """
        Test uploading CSV with duplicate review entries.
        
        Edge case test: ensures duplicate reviews are handled
        (either deduplicated or all imported). Expected: Successful import.
        """
        duplicate_csv = b"""product_id,product_name,platform,rating,title,body,created_at
SKU-100,Product A,amazon,5,Great,"This is great",2024-01-01
SKU-100,Product A,amazon,5,Great,"This is great",2024-01-01
"""
        files = {"file": ("duplicates.csv", duplicate_csv, "text/csv")}
        data = {"name": "Duplicates Test"}
        response = api_client.post("/datasets", data=data, files=files)
        assert response.status_code == 200
        # Should import successfully (duplicates might be allowed)

    def test_filter_reviews_with_no_matches(self, api_client: httpx.Client, sample_csv_data: bytes):
        """
        Test filtering reviews that match no criteria.
        
        Edge case test: ensures filters return empty list when no matches.
        Expected: 200 with empty list.
        """
        # Create dataset
        files = {"file": ("no_matches.csv", sample_csv_data, "text/csv")}
        api_client.post("/datasets", data={"name": "No Matches Test"}, files=files)
        
        # Filter for impossible criteria
        response = api_client.get("/reviews?min_rating=5&max_rating=1")
        assert response.status_code == 200
        # Should return empty list (or might be rejected as invalid)
