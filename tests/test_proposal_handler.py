"""
Unit Tests for Proposal Handler
==============================

Tests for Proposal, ProposalHandler.
"""

import pytest
from tsukuyomi.agents.runtime.proposal_handler import (
    ProposalType, ProposalStatus, Proposal, ProposalHandler,
    create_verdict_proposal, tally_votes
)


class TestProposal:
    """Tests for Proposal."""
    
    def test_create_proposal(self):
        """Test creating a proposal."""
        proposal = Proposal(
            title="Vote guilty",
            description="The evidence proves guilt",
            proposal_type=ProposalType.VOTE,
            proposer_id="juror_01"
        )
        
        assert proposal.title == "Vote guilty"
        assert proposal.proposal_type == ProposalType.VOTE
    
    def test_vote_counts(self):
        """Test vote counting."""
        proposal = Proposal(
            title="Test",
            required_votes=3
        )
        proposal.votes = {
            "v1": "yes",
            "v2": "yes",
            "v3": "no"
        }
        
        assert proposal.yes_count == 2
        assert proposal.no_count == 1
        assert abs(proposal.yes_percentage - (2/3)) < 0.001
    
    def test_has_reached_threshold(self):
        """Test threshold check."""
        proposal = Proposal(required_votes=3)
        
        assert not proposal.has_reached_threshold
        
        proposal.votes = {"v1": "yes"}
        assert not proposal.has_reached_threshold
        
        proposal.votes = {"v1": "yes", "v2": "yes", "v3": "yes"}
        assert proposal.has_reached_threshold
    
    def test_would_pass(self):
        """Test pass check."""
        proposal = Proposal(
            required_votes=2,
            min_agreement=0.5
        )
        
        # Not enough votes
        assert not proposal.would_pass
        
        # Enough votes, but not enough yes
        proposal.votes = {"v1": "no", "v2": "no"}
        assert not proposal.would_pass
        
        # Enough votes, enough yes
        proposal.votes = {"v1": "yes", "v2": "yes"}
        assert proposal.would_pass
    
    def test_proposal_serialization(self):
        """Test proposal serialization."""
        proposal = Proposal(
            title="Test",
            description="Desc",
            votes={"v1": "yes"},
            tick=100
        )
        
        data = proposal.to_dict()
        restored = Proposal.from_dict(data)
        
        assert restored.title == proposal.title
        assert restored.votes == proposal.votes


class TestProposalHandler:
    """Tests for ProposalHandler."""
    
    def test_create_handler(self):
        """Test creating a handler."""
        handler = ProposalHandler(agent_id="test")
        
        assert handler.agent_id == "test"
        assert len(handler.proposals) == 0
    
    def test_create_proposal(self):
        """Test creating a proposal."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test Proposal",
            description="Description",
            tick=100
        )
        
        assert proposal.id in handler.proposals
        assert proposal.id in handler.active_proposals
    
    def test_create_vote_proposal(self):
        """Test creating a vote proposal."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_vote_proposal(
            verdict="guilty",
            justification="Evidence shows he's guilty",
            tick=100
        )
        
        assert proposal.proposal_type == ProposalType.VOTE
        assert "guilty" in proposal.title
    
    def test_cast_vote(self):
        """Test casting a vote."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            tick=100
        )
        
        result = handler.cast_vote(
            proposal_id=proposal.id,
            voter_id="juror_01",
            vote="yes",
            tick=100
        )
        
        assert result is True
        assert "juror_01" in proposal.votes
    
    def test_vote_yes_no(self):
        """Test convenience vote methods."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            required_votes=2,
            tick=100
        )
        
        handler.vote_yes(proposal.id, "voter1", 100)
        handler.vote_no(proposal.id, "voter2", 100)
        
        assert proposal.votes.get("voter1") == "yes"
        assert proposal.votes.get("voter2") == "no"
    
    def test_proposal_decides_on_threshold(self):
        """Test proposal decides when threshold reached."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            required_votes=2,
            min_agreement=0.5,
            tick=100
        )
        
        handler.cast_vote(proposal.id, "v1", "yes", 100)
        assert proposal.status == ProposalStatus.PENDING
        
        handler.cast_vote(proposal.id, "v2", "yes", 100)
        assert proposal.status == ProposalStatus.ACCEPTED
    
    def test_proposal_decides_on_deadline(self):
        """Test proposal decides on deadline."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            required_votes=3,
            deadline_tick=200,
            tick=100
        )
        
        handler.cast_vote(proposal.id, "v1", "yes", 150)
        
        # Manually expire
        handler.expire_proposals(250)
        
        assert proposal.status == ProposalStatus.EXPIRED
    
    def test_withdraw_proposal(self):
        """Test withdrawing a proposal."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            proposer_id="test",
            tick=100
        )
        
        result = handler.withdraw_proposal(proposal.id)
        
        assert result is True
        assert proposal.status == ProposalStatus.WITHDRAWN
    
    def test_withdraw_non_proposer_fails(self):
        """Test non-proposer cannot withdraw."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = handler.create_proposal(
            title="Test",
            description="Desc",
            proposer_id="other",
            tick=100
        )
        
        result = handler.withdraw_proposal(proposal.id)
        
        assert result is False
    
    def test_get_active_proposals(self):
        """Test getting active proposals."""
        handler = ProposalHandler(agent_id="test")
        
        p1 = handler.create_proposal(title="Test1", description="D1", tick=100)
        p2 = handler.create_proposal(title="Test2", description="D2", tick=100)
        
        active = handler.get_active_proposals()
        
        assert len(active) == 2
    
    def test_get_proposals_by_type(self):
        """Test filtering by type."""
        handler = ProposalHandler(agent_id="test")
        
        handler.create_proposal(title="Vote", description="D", proposal_type=ProposalType.VOTE, tick=100)
        handler.create_proposal(title="Action", description="D", proposal_type=ProposalType.ACTION, tick=100)
        
        votes = handler.get_proposals_by_type(ProposalType.VOTE)
        
        assert len(votes) == 1
    
    def test_get_proposals_for_voter(self):
        """Test getting proposals for voter."""
        handler = ProposalHandler(agent_id="test")
        
        p1 = handler.create_proposal(title="Test1", description="D", tick=100)
        
        # Hasn't voted
        proposals = handler.get_proposals_for_voter("voter1")
        assert len(proposals) == 1
        
        # Already voted
        handler.cast_vote(p1.id, "voter1", "yes", 100)
        proposals = handler.get_proposals_for_voter("voter1")
        assert len(proposals) == 0
    
    def test_get_statistics(self):
        """Test getting statistics."""
        handler = ProposalHandler(agent_id="test")
        
        p1 = handler.create_proposal(title="Test", description="Desc", tick=100)
        handler.cast_vote(p1.id, "v1", "yes", 100)
        handler.cast_vote(p1.id, "v2", "yes", 100)
        
        stats = handler.get_statistics()
        
        assert stats["total_proposals"] == 1
        assert stats["accepted"] == 1
    
    def test_serialization(self):
        """Test handler serialization."""
        handler = ProposalHandler(agent_id="test")
        
        p1 = handler.create_proposal(title="Test", description="Desc", tick=100)
        handler.cast_vote(p1.id, "v1", "yes", 100)
        
        data = handler.to_dict()
        restored = ProposalHandler.from_dict(data)
        
        assert restored.agent_id == handler.agent_id
        assert len(restored.proposals) == len(handler.proposals)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_verdict_proposal(self):
        """Test creating verdict proposal."""
        handler = ProposalHandler(agent_id="test")
        
        proposal = create_verdict_proposal(
            handler=handler,
            verdict="guilty",
            justification="Beyond reasonable doubt",
            voters=["j1", "j2", "j3"],
            tick=100
        )
        
        assert proposal.proposal_type == ProposalType.VOTE
        assert proposal.required_votes == 3
    
    def test_tally_votes(self):
        """Test vote tallying."""
        proposals = [
            Proposal(title="A", description="D", votes={"v1": "yes", "v2": "yes"}),
            Proposal(title="B", description="D", votes={"v3": "no", "v4": "no"})
        ]
        
        tally = tally_votes(proposals)
        
        assert tally["yes"] == 2
        assert tally["no"] == 2
