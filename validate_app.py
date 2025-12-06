#!/usr/bin/env python3
"""Quick validation script to check app structure and imports."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def validate_imports():
    """Validate that all modules can be imported."""
    print("Validating imports...")

    try:
        from app.core.config import Settings, get_settings  # noqa: F401

        print("✓ Config module imports successfully")

        # Test settings
        settings = get_settings()
        print(f"✓ Settings loaded: APP_ENV={settings.app_env}")
        print(
            f"✓ Security settings: MAX_UPLOAD_SIZE={settings.max_upload_size}, MAX_INGESTION_ROWS={settings.max_ingestion_rows}"
        )
        print("✓ CORS settings: cors_allowed_origins configured")
        print(f"✓ LLM rate limit: {settings.llm_rate_limit_rpm} RPM")

    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

    try:
        from app.db.base import engine, get_session  # noqa: F401

        print("✓ Database module imports successfully")
        print(f"✓ Engine configured: {engine.url}")
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False

    try:
        from app.ingestion.service import IngestionService  # noqa: F401

        print("✓ Ingestion service imports successfully")
    except Exception as e:
        print(f"✗ Ingestion service import failed: {e}")
        return False

    try:
        from app.analysis.llm.client import RateLimiter, create_llm_client  # noqa: F401

        print("✓ LLM client imports successfully")
    except Exception as e:
        print(f"✗ LLM client import failed: {e}")
        return False

    try:
        from app.services.dataset_service import DatasetService  # noqa: F401

        print("✓ Dataset service imports successfully")
    except Exception as e:
        print(f"✗ Dataset service import failed: {e}")
        return False

    try:
        from app.api.routers import datasets, health, reviews, themes  # noqa: F401

        print("✓ API routers import successfully")
    except Exception as e:
        print(f"✗ API routers import failed: {e}")
        return False

    return True


def validate_security_features():
    """Validate security features are in place."""
    print("\nValidating security features...")

    try:
        from app.api.routers.datasets import ALLOWED_EXTENSIONS, validate_file_upload  # noqa: F401

        print(f"✓ File upload validation: {ALLOWED_EXTENSIONS}")

        from app.core.config import settings

        assert settings.max_upload_size > 0, "MAX_UPLOAD_SIZE not set"
        print(f"✓ File size limit: {settings.max_upload_size} bytes")

        assert settings.max_ingestion_rows > 0, "MAX_INGESTION_ROWS not set"
        print(f"✓ Row limit protection: {settings.max_ingestion_rows}")

        assert hasattr(settings, "cors_allowed_origins"), "CORS settings missing"
        print("✓ CORS configuration present")

        assert settings.llm_rate_limit_rpm > 0, "LLM rate limit not set"
        print(f"✓ LLM rate limiting: {settings.llm_rate_limit_rpm} RPM")

    except Exception as e:
        print(f"✗ Security validation failed: {e}")
        return False

    return True


def validate_cache_invalidation():
    """Validate cache invalidation is implemented."""
    print("\nValidating cache invalidation...")

    try:
        import inspect

        from app.services.dataset_service import DatasetService

        # Check methods exist
        assert hasattr(
            DatasetService, "_invalidate_analysis_cache"
        ), "Cache invalidation method missing"
        assert hasattr(DatasetService, "_is_cache_stale"), "Cache staleness check missing"

        # Check ingest_reviews calls invalidation
        ingest_source = inspect.getsource(DatasetService.ingest_reviews)
        assert (
            "_invalidate_analysis_cache" in ingest_source
        ), "ingest_reviews doesn't call cache invalidation"

        # Check get_dataset_analysis checks staleness
        analysis_source = inspect.getsource(DatasetService.get_dataset_analysis)
        assert (
            "_is_cache_stale" in analysis_source
        ), "get_dataset_analysis doesn't check cache staleness"

        print("✓ Cache invalidation method exists")
        print("✓ Cache staleness check implemented")
        print("✓ ingest_reviews invalidates cache")
        print("✓ get_dataset_analysis checks cache staleness")

    except Exception as e:
        print(f"✗ Cache invalidation validation failed: {e}")
        return False

    return True


def main():
    """Run all validations."""
    print("=" * 60)
    print("App Validation Check")
    print("=" * 60)

    results = []
    results.append(("Imports", validate_imports()))
    results.append(("Security Features", validate_security_features()))
    results.append(("Cache Invalidation", validate_cache_invalidation()))

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:30} {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n✓ All validations passed!")
        return 0
    else:
        print("\n✗ Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
