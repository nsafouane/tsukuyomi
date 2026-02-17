"""
Tests for Tsukuyomi Proto Action Logic Module

Run with: python -m pytest tests/test_action_logic.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.proto.action_logic import ActionResolver
from tsukuyomi.proto import core_pb2


class TestActionResolver:
    @pytest.fixture
    def resolver(self):
        """Create an action resolver for testing."""
        return ActionResolver()

    def test_create_resolver(self, resolver):
        """Test creating an action resolver."""
        assert resolver is not None

    def test_resolve_collect(self, resolver):
        """Test resolve_collect method exists."""
        assert hasattr(resolver, 'resolve_collect')

    def test_resolve_use(self, resolver):
        """Test resolve_use method exists."""
        assert hasattr(resolver, 'resolve_use')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])