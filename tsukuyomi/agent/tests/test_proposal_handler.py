"""
Unit Tests for Proposal Handler
==============================

Tests for Proposal, ProposalHandler.
"""

import pytest
from tsukuyomi.agent.proposal_handler import (
    ProposalType, ProposalStatus, Proposal, ProposalHandler,
    create_verdict_proposal, tally_votes
)


class TestProposal:
    """Tests for Proposal."""
    
    def test_create_proposal(self):
        proposal = Proposal(
            title="Vote guilty",
            description="The evidence proves guilt",
            proposal_type=ProposalType.VOTE,
            proposer_id="juror_01"
        )
        assert proposal.title == "Vote guilty"
        assert proposal.proposal_type == ProposalType.VOTE
    
    def test_vote_counts(self):
        proposal = Proposal(title="Test", required_votes=3)
        proposal.votes = {"v1": "yes", "v2": "yes", "v3": "no"}
        assert proposal.yes_count == 2
        assert proposal.no_count == 1
    
    def test_would_pass(self):
        proposal = Proposal(required_votes=2, min_agreement=0.5)
        assert not proposal.would_pass
        proposal.votes = {"v1": "yes", "v2": "yes"}
        assert proposal.would_pass
    
    def test_proposal_serialization(self):
        proposal = Proposal(title="Test", description="Desc", votes={"v1": "yes"}, tick=100)
        data = proposal.to_dict()
        restored = Proposal.from_dict(data)
        assert restored.title == proposal.title


class TestProposalHandler:
    """Tests for ProposalHandler."""
    
    def test_create_handler(self):
        handler = ProposalHandler(agent_id="test")
        assert handler.agent_id == "test"
    
    def test_create_proposal(self):
        handler = ProposalHandler(agent_id="test")
        proposal = handler.create_proposal(title="Test", description="Desc", tick=100)
        assert proposal.id in handler.proposals
    
    def test_cast_vote(self):
        handler = ProposalHandler(agent_id="test")
        proposal = handler.create_proposal(title="Test", description="Desc", tick=100)
        result = handler.cast_vote(proposal.id, "voter1", "yes", 100)
        assert result is True
        assert "voter1" in proposal.votes
    
    def test_proposal_decides_on_threshold(self):
        handler = ProposalHandler(agent_id="test")
        proposal = handler.create_proposal(
            title="Test", description="Desc",
            required_votes=2, min_agreement=0.5, tick=100
        )
        handler.cast_vote(proposal.id, "v1", "yes", 100)
        assert proposal.status == ProposalStatus.PENDING
        handler.cast_vote(proposal.id, "v2", "yes", 100)
        assert proposal.status == ProposalStatus.ACCEPTED
    
    def test_withdraw_proposal(self):
        handler = ProposalHandler(agent_id="test")
        proposal = handler.create_proposal(
            title="Test", description="Desc", proposer_id="test", tick=100
        )
        result = handler.withdraw_proposal(proposal.id)
        assert result is True
        assert proposal.status == ProposalStatus.WITHDRAWN
    
    def test_get_statistics(self):
        handler = ProposalHandler(agent_id="test")
        p1 = handler.create_proposal(title="Test", description="Desc", tick=100)
        handler.cast_vote(p1.id, "v1", "yes", 100)
        handler.cast_vote(p1.id, "v2", "yes", 100)
        stats = handler.get_statistics()
        assert stats["total_proposals"] == 1
        assert stats["accepted"] == 1
    
    def test_serialization(self):
        handler = ProposalHandler(agent_id="test")
        p1 = handler.create_proposal(title="Test", description="Desc", tick=100)
        data = handler.to_dict()
        restored = ProposalHandler.from_dict(data)
        assert restored.agent_id == handler.agent_id


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_verdict_proposal(self):
        handler = ProposalHandler(agent_id="test")
        proposal = create_verdict_proposal(
            handler=handler, verdict="guilty",
            justification="Beyond reasonable doubt",
            voters=["j1", "j2", "j3"], tick=100
        )
        assert proposal.proposal_type == ProposalType.VOTE
        assert proposal.required_votes == 3
    
    def test_tally_votes(self):
        proposals = [
            Proposal(title="A", description="D", votes={"v1": "yes", "v2": "yes"}),
            Proposal(title="B", description="D", votes={"v3": "no", "v4": "no"})
        ]
        tally = tally_votes(proposals)
        assert tally["yes"] == 2
        assert tally["no"] == 2
