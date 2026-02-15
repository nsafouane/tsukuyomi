"""
Tsukuyomi V2 - Proposal Window System (Phase 2)

This module implements multi-tick commitment phases for proposal handling.
The proposal window allows for:
- Batching proposals over multiple ticks
- Conflict resolution between competing proposals
- Priority-based proposal ordering
- Actor commitment tracking

Usage:
    window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)
    window.open_window(tick_number)
    window.add_proposal(proposal)
    if window.is_expired(tick_number):
        ready_proposals = window.get_ready_proposals()
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict
import time

from tsukuyomi.proto import core_pb2, common_pb2

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Strategies for resolving proposal conflicts."""
    FIRST_COME_FIRST_SERVED = "first_come_first_served"
    HIGHEST_PRIORITY = "highest_priority"
    RANDOM = "random"
    MERGE = "merge"


@dataclass
class ProposalMetadata:
    """
    Metadata for tracking proposals in the window.

    Attributes:
        proposal: The actual proposal protobuf message
        priority: Priority level (higher = more important)
        tick_submitted: Tick when proposal was submitted
        actor_commitments: Set of tick indices actor has committed for
    """
    proposal: core_pb2.Proposal
    priority: int = 0
    tick_submitted: int = 0
    actor_commitments: Set[int] = field(default_factory=set)


@dataclass
class ConflictResult:
    """
    Result of conflict resolution.

    Attributes:
        winning_proposal: The proposal that won the conflict
        rejected_proposals: Proposals that were rejected
        resolution_strategy: Strategy used to resolve conflict
        reason: Human-readable explanation
    """
    winning_proposal: Optional[core_pb2.Proposal]
    rejected_proposals: List[core_pb2.Proposal]
    resolution_strategy: ConflictResolution
    reason: str


class ProposalWindow:
    """
    Manages proposal windows for multi-tick commitment phases.

    A proposal window allows actors to commit to actions over multiple ticks,
    enabling more complex decision-making while maintaining simulation determinism.

    Features:
    - Window duration (in ticks)
    - Maximum proposals per actor per window
    - Conflict detection and resolution
    - Priority-based ordering
    - Actor commitment tracking

    Complexity:
        - Add proposal: O(1) amortized
        - Conflict detection: O(n) where n = proposals in window
        - Conflict resolution: O(n)
        - Tick update: O(n) for expiration checks
    """

    def __init__(
        self,
        duration_ticks: int = 3,
        max_proposals_per_actor: int = 2,
        conflict_resolution: ConflictResolution = ConflictResolution.HIGHEST_PRIORITY,
        auto_resolve: bool = True
    ):
        """
        Initialize the proposal window.

        Args:
            duration_ticks: How many ticks a window remains open
            max_proposals_per_actor: Max proposals an actor can submit per window
            conflict_resolution: Strategy for resolving conflicts
            auto_resolve: Whether to automatically resolve conflicts on expiry
        """
        self.duration_ticks = duration_ticks
        self.max_proposals_per_actor = max_proposals_per_actor
        self.conflict_resolution = conflict_resolution
        self.auto_resolve = auto_resolve

        # Window state
        self.current_tick: int = 0
        self.window_start_tick: int = 0
        self.is_open: bool = False

        # Proposals in current window
        self.proposals: Dict[str, ProposalMetadata] = {}  # proposal_id -> metadata

        # Actor tracking
        self.actor_proposal_count: Dict[str, int] = defaultdict(int)

        # Conflict cache
        self._conflict_cache: Optional[List[ConflictResult]] = None
        self._cache_tick: int = -1

        logger.info(
            f"ProposalWindow initialized: duration={duration_ticks} ticks, "
            f"max_per_actor={max_proposals_per_actor}, "
            f"conflict_resolution={conflict_resolution.value}"
        )

    def open_window(self, tick_number: int) -> None:
        """
        Open a new proposal window.

        Args:
            tick_number: Current tick number
        """
        self.current_tick = tick_number
        self.window_start_tick = tick_number
        self.is_open = True

        # Clear previous window state
        self.proposals.clear()
        self.actor_proposal_count.clear()
        self._conflict_cache = None
        self._cache_tick = -1

        logger.debug(f"Opened proposal window at tick {tick_number}")

    def close_window(self) -> None:
        """Close the current proposal window."""
        self.is_open = False
        logger.debug(f"Closed proposal window at tick {self.current_tick}")

    def add_proposal(
        self,
        proposal: core_pb2.Proposal,
        priority: int = 0
    ) -> bool:
        """
        Add a proposal to the current window.

        Args:
            proposal: The proposal to add
            priority: Priority level (higher = more important)

        Returns:
            True if proposal was accepted, False otherwise
        """
        if not self.is_open:
            logger.warning(f"Cannot add proposal: window is closed")
            return False

        if proposal.proposal_id in self.proposals:
            logger.warning(f"Proposal {proposal.proposal_id} already exists")
            return False

        # Check actor limit
        actor_id = proposal.actor_id
        if self.actor_proposal_count[actor_id] >= self.max_proposals_per_actor:
            logger.debug(
                f"Actor {actor_id} has reached max proposals "
                f"({self.max_proposals_per_actor}) for this window"
            )
            return False

        # Add proposal with metadata
        self.proposals[proposal.proposal_id] = ProposalMetadata(
            proposal=proposal,
            priority=priority,
            tick_submitted=self.current_tick,
            actor_commitments=set()
        )

        # Update actor count
        self.actor_proposal_count[actor_id] += 1

        # Invalidate conflict cache
        self._conflict_cache = None

        logger.debug(
            f"Added proposal {proposal.proposal_id} from {actor_id} "
            f"with priority {priority}"
        )
        return True

    def remove_proposal(self, proposal_id: str) -> bool:
        """
        Remove a proposal from the window.

        Args:
            proposal_id: ID of proposal to remove

        Returns:
            True if removed, False if not found
        """
        if proposal_id not in self.proposals:
            return False

        metadata = self.proposals[proposal_id]
        actor_id = metadata.proposal.actor_id

        # Update actor count
        self.actor_proposal_count[actor_id] -= 1

        # Remove proposal
        del self.proposals[proposal_id]

        # Invalidate conflict cache
        self._conflict_cache = None

        logger.debug(f"Removed proposal {proposal_id}")
        return True

    def add_actor_commitment(
        self,
        proposal_id: str,
        tick_index: int
    ) -> bool:
        """
        Record an actor's commitment to a proposal for a specific tick.

        This allows tracking multi-tick commitments where actors reaffirm
        their intent across multiple ticks.

        Args:
            proposal_id: The proposal being committed to
            tick_index: Tick index within the window (0 to duration_ticks-1)

        Returns:
            True if commitment recorded, False if proposal not found
        """
        if proposal_id not in self.proposals:
            return False

        if not (0 <= tick_index < self.duration_ticks):
            return False

        self.proposals[proposal_id].actor_commitments.add(tick_index)
        logger.debug(f"Actor commitment added for {proposal_id} at tick {tick_index}")
        return True

    def is_expired(self, tick_number: int) -> bool:
        """
        Check if the current window has expired.

        Args:
            tick_number: Current tick number

        Returns:
            True if window has expired
        """
        if not self.is_open:
            return True

        ticks_elapsed = tick_number - self.window_start_tick
        return ticks_elapsed >= self.duration_ticks

    def get_ticks_remaining(self, tick_number: int) -> int:
        """
        Get number of ticks remaining in the window.

        Args:
            tick_number: Current tick number

        Returns:
            Number of ticks remaining (0 if expired)
        """
        if not self.is_open:
            return 0

        ticks_elapsed = tick_number - self.window_start_tick
        remaining = self.duration_ticks - ticks_elapsed
        return max(0, remaining)

    def _detect_conflicts(self) -> List[List[str]]:
        """
        Detect conflicts between proposals in the window.

        Returns:
            List of lists, where each inner list contains proposal_ids in conflict
        """
        if not self.proposals:
            return []

        # Group proposals by actor and target to detect conflicts
        # Conflict types:
        # 1. Same actor, overlapping time windows
        # 2. Different actors, same exclusive resource
        # 3. Mutually exclusive actions

        conflicts = []

        # Group by actor
        by_actor: Dict[str, List[ProposalMetadata]] = defaultdict(list)
        for metadata in self.proposals.values():
            by_actor[metadata.proposal.actor_id].append(metadata)

        # Check for actor self-conflicts
        for actor_id, proposals in by_actor.items():
            if len(proposals) > 1:
                # Actor has multiple proposals - check if they conflict
                action_types = [p.proposal.action for p in proposals]

                # MOVING and INTERACTING typically conflict
                if core_pb2.ActionType.MOVE in action_types and core_pb2.ActionType.INTERACT in action_types:
                    conflict_ids = [p.proposal.proposal_id for p in proposals]
                    conflicts.append(conflict_ids)

        # Group by target for object/actor conflicts
        by_target: Dict[str, List[ProposalMetadata]] = defaultdict(list)
        for metadata in self.proposals.values():
            proposal = metadata.proposal
            # Extract target from parameters
            target_id = proposal.parameters.get("target_id") or proposal.parameters.get("destination")
            if target_id:
                by_target[target_id].append(metadata)

        # Check for target conflicts (e.g., two actors trying to TAKE same object)
        for target_id, proposals in by_target.items():
            if len(proposals) > 1:
                # Check if actions are mutually exclusive
                actions = [p.proposal.action for p in proposals]
                exclusive_actions = {
                    core_pb2.ActionType.TAKE,
                    core_pb2.ActionType.COLLECT,
                    core_pb2.ActionType.INTERACT
                }

                # If multiple actors are trying exclusive actions on same target
                if any(action in exclusive_actions for action in actions):
                    conflict_ids = [p.proposal.proposal_id for p in proposals]
                    conflicts.append(conflict_ids)

        return conflicts

    def _resolve_conflict(
        self,
        conflicting_proposals: List[ProposalMetadata]
    ) -> ConflictResult:
        """
        Resolve a conflict using the configured strategy.

        Args:
            conflicting_proposals: List of proposals in conflict

        Returns:
            ConflictResult with winner and rejected proposals
        """
        if not conflicting_proposals:
            return ConflictResult(
                winning_proposal=None,
                rejected_proposals=[],
                resolution_strategy=self.conflict_resolution,
                reason="No proposals to resolve"
            )

        if self.conflict_resolution == ConflictResolution.FIRST_COME_FIRST_SERVED:
            # First submitted wins
            winner = min(conflicting_proposals, key=lambda p: p.tick_submitted)
            reason = "First-come-first-served: earliest submission selected"

        elif self.conflict_resolution == ConflictResolution.HIGHEST_PRIORITY:
            # Highest priority wins, break ties with submission time
            winner = min(
                conflicting_proposals,
                key=lambda p: (-p.priority, p.tick_submitted)
            )
            reason = f"Highest priority: priority {winner.priority}"

        elif self.conflict_resolution == ConflictResolution.RANDOM:
            # Random selection (deterministic if seeded)
            import random
            winner = random.choice(conflicting_proposals)
            reason = "Random selection"

        elif self.conflict_resolution == ConflictResolution.MERGE:
            # Try to merge compatible proposals
            # For now, fall back to highest priority
            winner = min(
                conflicting_proposals,
                key=lambda p: (-p.priority, p.tick_submitted)
            )
            reason = "Merge attempted, falling back to highest priority"

        else:
            winner = conflicting_proposals[0]
            reason = "Default resolution"

        rejected = [p.proposal for p in conflicting_proposals if p.proposal.proposal_id != winner.proposal.proposal_id]

        return ConflictResult(
            winning_proposal=winner.proposal,
            rejected_proposals=rejected,
            resolution_strategy=self.conflict_resolution,
            reason=reason
        )

    def resolve_conflicts(self) -> List[ConflictResult]:
        """
        Detect and resolve all conflicts in the current window.

        Returns:
            List of ConflictResult objects
        """
        # Check cache
        if self._conflict_cache is not None and self._cache_tick == self.current_tick:
            return self._conflict_cache

        conflicts = self._detect_conflicts()
        results = []

        for conflict_group in conflicts:
            conflicting_metadata = [self.proposals[pid] for pid in conflict_group]
            result = self._resolve_conflict(conflicting_metadata)
            results.append(result)

        # Cache results
        self._conflict_cache = results
        self._cache_tick = self.current_tick

        logger.info(f"Resolved {len(results)} conflicts")
        return results

    def get_ready_proposals(self) -> List[core_pb2.Proposal]:
        """
        Get proposals ready for execution after conflict resolution.

        Returns:
            List of proposals that should be executed
        """
        if not self.proposals:
            return []

        # Auto-resolve conflicts if enabled
        if self.auto_resolve:
            conflict_results = self.resolve_conflicts()

            # Build set of rejected proposal IDs
            rejected_ids = set()
            for result in conflict_results:
                for rejected in result.rejected_proposals:
                    rejected_ids.add(rejected.proposal_id)

            # Filter out rejected proposals
            ready = [
                metadata.proposal
                for metadata in self.proposals.values()
                if metadata.proposal.proposal_id not in rejected_ids
            ]
        else:
            # No auto-resolve, return all proposals
            ready = [metadata.proposal for metadata in self.proposals.values()]

        # Sort by priority (highest first) then submission time
        ready.sort(
            key=lambda p: (
                -self.proposals[p.proposal_id].priority,
                self.proposals[p.proposal_id].tick_submitted
            )
        )

        return ready

    def get_rejected_proposals(self) -> List[core_pb2.Proposal]:
        """
        Get proposals that were rejected during conflict resolution.

        Returns:
            List of rejected proposals
        """
        if not self.auto_resolve:
            return []

        conflict_results = self.resolve_conflicts()
        rejected = []

        for result in conflict_results:
            rejected.extend(result.rejected_proposals)

        return rejected

    def get_proposals_by_actor(self, actor_id: str) -> List[core_pb2.Proposal]:
        """
        Get all proposals from a specific actor.

        Args:
            actor_id: Actor ID to filter by

        Returns:
            List of proposals from the actor
        """
        return [
            metadata.proposal
            for metadata in self.proposals.values()
            if metadata.proposal.actor_id == actor_id
        ]

    def get_stats(self) -> Dict:
        """
        Get statistics about the current proposal window.

        Returns:
            Dictionary with statistics
        """
        conflict_results = self.resolve_conflicts()

        return {
            "is_open": self.is_open,
            "window_start_tick": self.window_start_tick,
            "current_tick": self.current_tick,
            "duration_ticks": self.duration_ticks,
            "total_proposals": len(self.proposals),
            "actors_with_proposals": len(self.actor_proposal_count),
            "conflicts_detected": len(conflict_results),
            "proposals_rejected": sum(len(r.rejected_proposals) for r in conflict_results),
            "max_per_actor": self.max_proposals_per_actor
        }

    def clear(self) -> None:
        """Clear all proposals and close the window."""
        self.proposals.clear()
        self.actor_proposal_count.clear()
        self._conflict_cache = None
        self._cache_tick = -1
        self.is_open = False
        logger.debug("Proposal window cleared")

    def to_dict(self) -> Dict:
        """Serialize proposal window to dictionary."""
        return {
            "is_open": self.is_open,
            "window_start_tick": self.window_start_tick,
            "duration_ticks": self.duration_ticks,
            "max_proposals_per_actor": self.max_proposals_per_actor,
            "conflict_resolution": self.conflict_resolution.value,
            "auto_resolve": self.auto_resolve,
            "stats": self.get_stats()
        }
