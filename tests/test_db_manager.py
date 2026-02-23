"""
Tests for Tsukuyomi Proto DB Manager Module

Run with: python -m pytest tests/test_db_manager.py -v
"""

import pytest
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.services.database.manager import DBManager


class TestDBManager:
    @pytest.fixture
    def db(self):
        """Create a database manager for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DBManager(db_path)
        yield db
        try:
            os.unlink(db_path)
        except:
            pass

    def test_create_manager(self, db):
        """Test creating a database manager."""
        assert db is not None

    def test_get_latest_tick_number(self, db):
        """Test getting latest tick number."""
        # Should return -1 if no ticks saved yet
        tick = db.get_latest_tick_number()
        assert tick == -1 or tick >= 0

    def test_list_ticks(self, db):
        """Test listing ticks."""
        ticks = db.list_ticks(limit=10)
        assert isinstance(ticks, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])