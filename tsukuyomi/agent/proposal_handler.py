"""
Proposal Handler
================

Handles proposal generation, evaluation, and integration with FateEngine.

Key Features:
- Proposal generation from decisions
- Proposal validation
- FateEngine integration
- Proposal voting/acceptance tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
import json
import random


class ProposalType(Enum):
    """Types of proposals."""
    VOTE = "vote"                    # Vote on verdict
    ACTION = "action"                # Take an action
    INVESTIGATION = "investigation"  # Investigate something
    DELAY = "delay"                  # Delay decision
    RECONSIDER = "reconsider"         # Reconsider previous decision
    RECESS = "recess"                # Take a break


class ProposalStatus(Enum):
    """Status of a proposal."""
    PENDING = "pending"      # Not yet voted
    ACCEPTED = "accepted"    # Passed
    REJECTED = "rejected"   # Failed
    WITHDRAWN = "withdrawn"  # Withdrawn by proposer
    EXPIRED = "expired"      # Timed out


@dataclass
class Proposal:
    """
    A formal proposal for group decision.
    """
    id: str = field(default_factory=lambda: f"prop_{random.randint(100000, 999999)}")
    proposal_type: ProposalType = ProposalType.VOTE
    
    # Content
    title: str = ""
    description: str = ""
    proposer_id: str = ""
    
    # Target
    target_id: Optional[str] = None  # What this affects
    
    # Timing
    tick: int = 0
    deadline_tick: Optional[int] = None
    
    # Voting
    votes: Dict[str, str] = field(default_factory=dict)  # voter_id -> vote
    required_votes: int = 1
    min_agreement: float = 0.5  # % needed to pass
    
    # Status
    status: ProposalStatus = ProposalStatus.PENDING
    
    # Linked decision
    decision_id: Optional[str] = None
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def vote_count(self) -> int:
        """Total votes cast."""
        return len(self.votes)
    
    @property
    def yes_count(self) -> int:
        """Yes votes."""
        return sum(1 for v in self.votes.values() if v.lower() in ["yes", "y", "aye", "guilty"])
    
    @property
    def no_count(self) -> int:
        """No votes."""
        return sum(1 for v in self.votes.values() if v.lower() in ["no", "n", "nay", "not guilty"])
    
    @property
    def yes_percentage(self) -> float:
        """Yes vote percentage."""
        if self.vote_count == 0:
            return 0.0
        return self.yes_count / self.vote_count
    
    @property
    def has_reached_threshold(self) -> bool:
        """Check if minimum votes reached."""
        return self.vote_count >= self.required_votes
    
    @property
    def would_pass(self) -> bool:
        """Check if proposal would pass with current votes."""
        if not self.has_reached_threshold:
            return False
        return self.yes_percentage >= self.min_agreement
    
    @property
    def is_decided(self) -> bool:
        """Check if proposal is decided."""
        return self.status in [
            ProposalStatus.ACCEPTED,
            ProposalStatus.REJECTED,
            ProposalStatus.WITHDRAWN,
            ProposalStatus.EXPIRED
        ]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "proposal_type": self.proposal_type.value,
            "title": self.title,
            "description": self.description,
            "proposer_id": self.proposer_id,
            "target_id": self.target_id,
            "tick": self.tick,
            "deadline_tick": self.deadline_tick,
            "votes": self.votes,
            "required_votes": self.required_votes,
            "min_agreement": self.min_agreement,
            "status": self.status.value,
            "decision_id": self.decision_id,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Proposal":
        proposal = cls(
            id=data["id"],
            proposal_type=ProposalType(data["proposal_type"]),
            title=data["title"],
            description=data["description"],
            proposer_id=data["proposer_id"],
            target_id=data.get("target_id"),
            tick=data["tick"],
            deadline_tick=data.get("deadline_tick"),
            votes=data.get("votes", {}),
            required_votes=data.get("required_votes", 1),
            min_agreement=data.get("min_agreement", 0.5),
            status=ProposalStatus(data.get("status", "pending")),
            decision_id=data.get("decision_id"),
            context=data.get("context", {})
        )
        return proposal


@dataclass
class ProposalHandler:
    """
    Handles proposal lifecycle.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Storage
        self.proposals: Dict[str, Proposal] = {}
        self.active_proposals: List[str] = []
        self.decided_proposals: List[str] = []
        
        # History
        self.proposals_proposed: List[str] = []  # IDs proposed by this agent
        self.proposals_voted: List[str] = []     # IDs this agent voted on
        
        # Configuration
        self.max_active_proposals = 10
        self.default_deadline = 100  # ticks
    
    # ==================== PROPOSAL CREATION ====================
    
    def create_proposal(
        self,
        title: str,
        description: str,
        proposal_type: ProposalType = ProposalType.VOTE,
        proposer_id: Optional[str] = None,
        target_id: Optional[str] = None,
        required_votes: int = 1,
        min_agreement: float = 0.5,
        deadline_tick: Optional[int] = None,
        decision_id: Optional[str] = None,
        context: Optional[Dict] = None,
        tick: int = 0
    ) -> Proposal:
        """
        Create a new proposal.
        """
        # Check max active proposals
        if len(self.active_proposals) >= self.max_active_proposals:
            self._cleanup_expired()
        
        proposal = Proposal(
            proposal_type=proposal_type,
            title=title,
            description=description,
            proposer_id=proposer_id or self.agent_id,
            target_id=target_id,
            required_votes=required_votes,
            min_agreement=min_agreement,
            deadline_tick=deadline_tick or (tick + self.default_deadline),
            decision_id=decision_id,
            context=context or {},
            tick=tick
        )
        
        self.proposals[proposal.id] = proposal
        self.active_proposals.append(proposal.id)
        
        if proposal.proposer_id == self.agent_id:
            self.proposals_proposed.append(proposal.id)
        
        return proposal
    
    def create_vote_proposal(
        self,
        verdict: str,
        justification: str,
        proposer_id: Optional[str] = None,
        required_votes: int = 1,
        tick: int = 0
    ) -> Proposal:
        """
        Create a vote proposal (e.g., guilty/not guilty).
        """
        return self.create_proposal(
            title=f"Vote: {verdict}",
            description=justification,
            proposal_type=ProposalType.VOTE,
            proposer_id=proposer_id,
            required_votes=required_votes,
            min_agreement=0.5,
            tick=tick
        )
    
    def create_investigation_proposal(
        self,
        target: str,
        reason: str,
        proposer_id: Optional[str] = None,
        tick: int = 0
    ) -> Proposal:
        """
        Create an investigation proposal.
        """
        return self.create_proposal(
            title=f"Investigate: {target}",
            description=reason,
            proposal_type=ProposalType.INVESTIGATION,
            proposer_id=proposer_id,
            required_votes=1,
            target_id=target,
            tick=tick
        )
    
    # ==================== VOTING ====================
    
    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote: str,
        tick: int = 0
    ) -> bool:
        """
        Cast a vote on a proposal.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if proposal.is_decided:
            return False
        
        proposal.votes[voter_id] = vote
        
        if voter_id == self.agent_id:
            self.proposals_voted.append(proposal_id)
        
        # Check if should be decided
        self._check_decision(proposal_id, tick)
        
        return True
    
    def vote_yes(
        self,
        proposal_id: str,
        voter_id: Optional[str] = None,
        tick: int = 0
    ) -> bool:
        """Vote yes on a proposal."""
        return self.cast_vote(proposal_id, voter_id or self.agent_id, "yes", tick)
    
    def vote_no(
        self,
        proposal_id: str,
        voter_id: Optional[str] = None,
        tick: int = 0
    ) -> bool:
        """Vote no on a proposal."""
        return self.cast_vote(proposal_id, voter_id or self.agent_id, "no", tick)
    
    def withdraw_proposal(self, proposal_id: str) -> bool:
        """Withdraw a proposal (only proposer can)."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if proposal.proposer_id != self.agent_id:
            return False
        
        if proposal.is_decided:
            return False
        
        proposal.status = ProposalStatus.WITHDRAWN
        self._move_to_decided(proposal_id)
        
        return True
    
    # ==================== DECISION ====================
    
    def _check_decision(self, proposal_id: str, tick: int = 0):
        """Check if proposal should be decided."""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.is_decided:
            return
        
        # Check deadline
        if proposal.deadline_tick and tick >= proposal.deadline_tick:
            self._decide_proposal(proposal_id, tick)
            return
        
        # Check if threshold reached
        if proposal.has_reached_threshold:
            self._decide_proposal(proposal_id, tick)
    
    def _decide_proposal(self, proposal_id: str, tick: int = 0):
        """Decide a proposal based on votes."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return
        
        if proposal.would_pass:
            proposal.status = ProposalStatus.ACCEPTED
        else:
            proposal.status = ProposalStatus.REJECTED
        
        self._move_to_decided(proposal_id)
    
    def _move_to_decided(self, proposal_id: str):
        """Move proposal from active to decided."""
        if proposal_id in self.active_proposals:
            self.active_proposals.remove(proposal_id)
        if proposal_id not in self.decided_proposals:
            self.decided_proposals.append(proposal_id)
    
    # ==================== QUERIES ====================
    
    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals."""
        return [self.proposals[pid] for pid in self.active_proposals]
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a specific proposal."""
        return self.proposals.get(proposal_id)
    
    def get_proposals_by_type(
        self,
        proposal_type: ProposalType,
        active_only: bool = False
    ) -> List[Proposal]:
        """Get proposals by type."""
        proposals = self.proposals.values()
        
        if active_only:
            proposals = [p for p in proposals if p.id in self.active_proposals]
        
        return [p for p in proposals if p.proposal_type == proposal_type]
    
    def get_proposals_for_voter(
        self,
        voter_id: str,
        exclude_voted: bool = True
    ) -> List[Proposal]:
        """Get proposals available for a voter."""
        proposals = self.get_active_proposals()
        
        if exclude_voted:
            proposals = [p for p in proposals if voter_id not in p.votes]
        
        return proposals
    
    def get_proposal_results(self, proposal_id: str) -> Dict[str, Any]:
        """Get detailed results for a proposal."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {}
        
        return {
            "id": proposal.id,
            "title": proposal.title,
            "status": proposal.status.value,
            "votes": dict(proposal.votes),
            "vote_count": proposal.vote_count,
            "yes_count": proposal.yes_count,
            "no_count": proposal.no_count,
            "yes_percentage": proposal.yes_percentage,
            "would_pass": proposal.would_pass,
            "required_votes": proposal.required_votes,
            "min_agreement": proposal.min_agreement
        }
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get proposal statistics."""
        all_proposals = list(self.proposals.values())
        
        accepted = [p for p in all_proposals if p.status == ProposalStatus.ACCEPTED]
        rejected = [p for p in all_proposals if p.status == ProposalStatus.REJECTED]
        
        return {
            "total_proposals": len(all_proposals),
            "active": len(self.active_proposals),
            "decided": len(self.decided_proposals),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "acceptance_rate": len(accepted) / len(all_proposals) if all_proposals else 0,
            "proposed_by_me": len(self.proposals_proposed),
            "voted_by_me": len(self.proposals_voted)
        }
    
    # ==================== INTERNAL ====================
    
    def _cleanup_expired(self):
        """Remove expired proposals."""
        for pid in list(self.active_proposals):
            proposal = self.proposals.get(pid)
            if proposal and proposal.status == ProposalStatus.EXPIRED:
                self._move_to_decided(pid)
    
    def expire_proposals(self, tick: int):
        """Expire proposals past deadline."""
        for pid in list(self.active_proposals):
            proposal = self.proposals.get(pid)
            if proposal and proposal.deadline_tick and tick >= proposal.deadline_tick:
                proposal.status = ProposalStatus.EXPIRED
                self._move_to_decided(pid)
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "proposals": {pid: p.to_dict() for pid, p in self.proposals.items()},
            "active_proposals": self.active_proposals,
            "decided_proposals": self.decided_proposals,
            "proposals_proposed": self.proposals_proposed,
            "proposals_voted": self.proposals_voted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ProposalHandler":
        handler = cls(agent_id=data["agent_id"])
        handler.proposals = {
            pid: Proposal.from_dict(p) for pid, p in data.get("proposals", {}).items()
        }
        handler.active_proposals = data.get("active_proposals", [])
        handler.decided_proposals = data.get("decided_proposals", [])
        handler.proposals_proposed = data.get("proposals_proposed", [])
        handler.proposals_voted = data.get("proposals_voted", [])
        return handler


# ==================== HELPER FUNCTIONS ====================

def create_verdict_proposal(
    handler: ProposalHandler,
    verdict: str,
    justification: str,
    voters: List[str],
    tick: int = 0
) -> Proposal:
    """
    Create a verdict proposal with multiple voters.
    """
    return handler.create_proposal(
        title=f"Verdict: {verdict}",
        description=justification,
        proposal_type=ProposalType.VOTE,
        required_votes=len(voters),
        min_agreement=0.5,  # Majority
        tick=tick
    )


def tally_votes(proposals: List[Proposal]) -> Dict[str, int]:
    """
    Tally votes across multiple proposals.
    
    Returns dict of vote -> count
    """
    tally = {}
    
    for proposal in proposals:
        for vote in proposal.votes.values():
            vote_lower = vote.lower()
            tally[vote_lower] = tally.get(vote_lower, 0) + 1
    
    return tally
