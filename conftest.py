"""
Pytest configuration and fixtures for Tsukuyomi tests.
"""

import pytest
import asyncio
import sys

# Configure asyncio mode
pytest_plugins = ('pytest_asyncio',)


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark (deselect with '-m \"not benchmark\"')"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "postgresql: mark test as requiring PostgreSQL"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    # Skip postgresql tests by default unless --run-postgresql is passed
    if not config.getoption("--run-postgresql", default=False):
        skip_postgresql = pytest.mark.skip(reason="need --run-postgresql option to run")
        for item in items:
            if "postgresql" in item.keywords:
                item.add_marker(skip_postgresql)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-postgresql",
        action="store_true",
        default=False,
        help="Run tests that require PostgreSQL"
    )


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()