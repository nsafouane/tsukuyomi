"""
Tests for Tsukuyomi Core Proposal Window Module

Run with: python -m pytest tests/test_proposal_window.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.core.proposal_window import (
    ProposalWindow, ProposalMetadata, ConflictResolution, ConflictResult
)
from tsukuyomi.proto import core_pb2


class TestProposalMetadata:
    def test_create_metadata(self):
        """Test creating proposal metadata."""
        proposal = core_pb2.Proposal(
            proposal_id="test-001",
            actor_id="actor-1",
            action=core_pb2.ActionType.MOVE
        )
        metadata = ProposalMetadata(proposal=proposal)
        assert metadata.proposal is not None
        assert metadata.priority == 0

    def test_metadata_with_priority(self):
        """Test metadata with custom priority."""
        proposal = core_pb2.Proposal(
            proposal_id="test-002",
            actor_id="actor-1",
            action=core_pb2.ActionType.IDLE
        )
        metadata = ProposalMetadata(proposal=proposal, priority=5)
        assert metadata.priority == 5


class TestProposalWindow:
    @pytest.fixture
    def window(self):
        """Create a proposal window for testing."""
        return ProposalWindow(duration_ticks=10)

    @pytest.fixture
    def sample_proposal(self):
        """Create a sample proposal."""
        return core_pb2.Proposal(
            proposal_id="prop-001",
            actor_id="actor-1",
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"}
        )

    def test_create_window(self, window):
        """Test creating a proposal window."""
        assert window is not None

    def test_add_proposal(self, window, sample_proposal):
        """Test adding a proposal."""
        window.open_window(100)  # Need to open window first
        result = window.add_proposal(sample_proposal, priority=1)
        assert result == True

    def test_get_proposals_by_actor(self, window, sample_proposal):
        """Test getting proposals by actor."""
        window.open_window(100)  # Need to open window first
        window.add_proposal(sample_proposal)
        proposals = window.get_proposals_by_actor("actor-1")
        assert len(proposals) == 1

    def test_get_ready_proposals(self, window, sample_proposal):
        """Test getting ready proposals."""
        window.add_proposal(sample_proposal)
        ready = window.get_ready_proposals()
        assert isinstance(ready, list)

    def test_get_stats(self, window, sample_proposal):
        """Test getting window statistics."""
        window.add_proposal(sample_proposal)
        stats = window.get_stats()
        assert stats is not None

    def test_clear(self, window, sample_proposal):
        """Test clearing the window."""
        window.add_proposal(sample_proposal)
        window.clear()
        proposals = window.get_proposals_by_actor("actor-1")
        assert len(proposals) == 0


class TestConflictResolution:
    def test_resolution_values(self):
        """Test conflict resolution values."""
        assert ConflictResolution.HIGHEST_PRIORITY.value == "highest_priority"
        assert ConflictResolution.FIRST_COME_FIRST_SERVED.value == "first_come_first_served"
        assert ConflictResolution.RANDOM.value == "random"
        assert ConflictResolution.MERGE.value == "merge"


class TestConflictResult:
    def test_create_result(self):
        """Test creating a conflict result."""
        proposal = core_pb2.Proposal(
            proposal_id="winner-001",
            actor_id="actor-1",
            action=core_pb2.ActionType.MOVE
        )
        result = ConflictResult(
            winning_proposal=proposal,
            rejected_proposals=[],
            resolution_strategy=ConflictResolution.HIGHEST_PRIORITY,
            reason="Test resolution"
        )
        assert result.winning_proposal is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])