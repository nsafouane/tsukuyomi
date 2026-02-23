"""
Tests for Tsukuyomi Core Proposal Window Module

Run with: python -m pytest tests/test_proposal_window.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.environment.core.proposal import (
    ProposalWindow, ProposalMetadata, ConflictResolution, ConflictResult
)
from tsukuyomi.transport.proto import core_pb2


class TestProposalMetadata:
    def test_create_metadata(self):
        """Test creating proposal metadata."""
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "test-001"
        proposal.actor_id = "actor-1"
        proposal.action = 0  # IDLE
        
        metadata = ProposalMetadata(proposal=proposal)
        assert metadata.proposal is not None
        assert metadata.priority == 0
        assert metadata.tick_submitted == 0
        assert len(metadata.actor_commitments) == 0
    
    def test_metadata_with_priority(self):
        """Test metadata with custom priority."""
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "test-002"
        proposal.actor_id = "actor-2"
        proposal.action = 0
        
        metadata = ProposalMetadata(
            proposal=proposal,
            priority=10,
            tick_submitted=100
        )
        assert metadata.priority == 10
        assert metadata.tick_submitted == 100


class TestConflictResolution:
    def test_conflict_resolution_enum(self):
        """Test conflict resolution enum values."""
        assert ConflictResolution.FIRST_COME_FIRST_SERVED.value == "first_come_first_served"
        assert ConflictResolution.HIGHEST_PRIORITY.value == "highest_priority"
        assert ConflictResolution.RANDOM.value == "random"
        assert ConflictResolution.MERGE.value == "merge"


class TestConflictResult:
    def test_conflict_result_creation(self):
        """Test creating a conflict result."""
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "winner"
        
        result = ConflictResult(
            winning_proposal=proposal,
            rejected_proposals=[],
            resolution_strategy=ConflictResolution.HIGHEST_PRIORITY,
            reason="Test resolution"
        )
        
        assert result.winning_proposal.proposal_id == "winner"
        assert result.resolution_strategy == ConflictResolution.HIGHEST_PRIORITY
        assert result.reason == "Test resolution"


class TestProposalWindow:
    def test_window_initialization(self):
        """Test proposal window initialization."""
        window = ProposalWindow(
            duration_ticks=3,
            max_proposals_per_actor=2
        )
        
        assert window.duration_ticks == 3
        assert window.max_proposals_per_actor == 2
        assert window.is_open == False
        assert len(window.proposals) == 0
    
    def test_open_window(self):
        """Test opening a proposal window."""
        window = ProposalWindow()
        window.open_window(tick_number=100)
        
        assert window.is_open == True
        assert window.window_start_tick == 100
    
    def test_add_proposal(self):
        """Test adding a proposal to the window."""
        window = ProposalWindow()
        window.open_window(tick_number=0)
        
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "prop-1"
        proposal.actor_id = "actor-1"
        proposal.action = 0
        
        result = window.add_proposal(proposal)
        assert result == True
        assert len(window.proposals) == 1
    
    def test_add_proposal_when_closed(self):
        """Test that proposals cannot be added when window is closed."""
        window = ProposalWindow()
        
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "prop-1"
        proposal.actor_id = "actor-1"
        
        result = window.add_proposal(proposal)
        assert result == False
    
    def test_max_proposals_per_actor(self):
        """Test max proposals limit per actor."""
        window = ProposalWindow(max_proposals_per_actor=2)
        window.open_window(tick_number=0)
        
        for i in range(3):
            proposal = core_pb2.Proposal()
            proposal.proposal_id = f"prop-{i}"
            proposal.actor_id = "actor-1"
            proposal.action = 0
            
            if i < 2:
                assert window.add_proposal(proposal) == True
            else:
                assert window.add_proposal(proposal) == False
    
    def test_is_expired(self):
        """Test window expiration check."""
        window = ProposalWindow(duration_ticks=3)
        window.open_window(tick_number=0)
        
        assert window.is_expired(0) == False
        assert window.is_expired(2) == False
        assert window.is_expired(3) == True
    
    def test_get_ticks_remaining(self):
        """Test getting remaining ticks."""
        window = ProposalWindow(duration_ticks=5)
        window.open_window(tick_number=100)
        
        assert window.get_ticks_remaining(100) == 5
        assert window.get_ticks_remaining(102) == 3
        assert window.get_ticks_remaining(105) == 0
    
    def test_remove_proposal(self):
        """Test removing a proposal."""
        window = ProposalWindow()
        window.open_window(tick_number=0)
        
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "prop-1"
        proposal.actor_id = "actor-1"
        
        window.add_proposal(proposal)
        assert len(window.proposals) == 1
        
        result = window.remove_proposal("prop-1")
        assert result == True
        assert len(window.proposals) == 0
    
    def test_get_stats(self):
        """Test getting window statistics."""
        window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)
        window.open_window(tick_number=0)
        
        stats = window.get_stats()
        
        assert stats["is_open"] == True
        assert stats["duration_ticks"] == 3
        assert stats["total_proposals"] == 0
        assert stats["max_per_actor"] == 2
    
    def test_get_ready_proposals_empty(self):
        """Test getting ready proposals when window is empty."""
        window = ProposalWindow()
        window.open_window(tick_number=0)
        
        ready = window.get_ready_proposals()
        assert len(ready) == 0
    
    def test_close_window(self):
        """Test closing a proposal window."""
        window = ProposalWindow()
        window.open_window(tick_number=0)
        assert window.is_open == True
        
        window.close_window()
        assert window.is_open == False
    
    def test_clear_window(self):
        """Test clearing a proposal window."""
        window = ProposalWindow()
        window.open_window(tick_number=0)
        
        proposal = core_pb2.Proposal()
        proposal.proposal_id = "prop-1"
        proposal.actor_id = "actor-1"
        window.add_proposal(proposal)
        
        window.clear()
        assert window.is_open == False
        assert len(window.proposals) == 0
