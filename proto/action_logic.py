"""
PHASE 6: Action Logic & Reflex Expansion Specification
=====================================================

This phase implements the internal logic for the new actions:
- COLLECT: Move an EnvironmentObject to an Actor's inventory.
- USE: Trigger an effect using an item in inventory on a target.

It also updates the reflex layer to handle basic 'gathering' behavior.
"""

from typing import Dict, Optional
import logging
from tsukuyomi.proto import core_pb2, common_pb2

logger = logging.getLogger("Phase6Logic")

class ActionResolver:
    """
    Logic for resolving new Phase 6 actions.
    Integrated into FateEngine._resolve_proposal.
    """
    
    @staticmethod
    async def resolve_collect(proposal: core_pb2.Proposal, actor: core_pb2.Actor, world_state: core_pb2.WorldState) -> core_pb2.Resolution:
        """
        Logic for COLLECT action.
        Requirements:
        1. target_id (EnvironmentObject) must exist.
        2. target_id must be interactive.
        3. Actor must be close to target (dist < 2.0).
        """
        target_id = proposal.parameters.get("target_id")
        if not target_id or target_id not in world_state.objects:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor.id,
                success=False,
                reason=f"Object {target_id} not found"
            )
        
        obj = world_state.objects[target_id]
        if not obj.interactive:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor.id,
                success=False,
                reason=f"Object {target_id} is not collectible"
            )

        # Distance check
        dist = ((actor.position.x - obj.position.x)**2 + (actor.position.y - obj.position.y)**2)**0.5
        if dist > 2.0:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor.id,
                success=False,
                reason=f"Too far from object (dist={dist:.2f})"
            )

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=actor.id,
            success=True,
            outcome={
                "action": "collect",
                "object_id": target_id,
                "object_type": obj.type
            }
        )

    @staticmethod
    async def resolve_use(proposal: core_pb2.Proposal, actor: core_pb2.Actor, world_state: core_pb2.WorldState) -> core_pb2.Resolution:
        """
        Logic for USE action.
        Requirements:
        1. item_id must be in actor's inventory.
        2. target_id (Actor or Object) must exist (optional).
        """
        item_id = proposal.parameters.get("item_id")
        target_id = proposal.parameters.get("target_id")
        
        if item_id not in actor.inventory:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor.id,
                success=False,
                reason=f"Item {item_id} not in inventory"
            )

        # Basic usage logic: if it's an apple, it might restore health (meta property)
        # For Phase 6, we just succeed and report the use.
        
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=actor.id,
            success=True,
            outcome={
                "action": "use",
                "item_id": item_id,
                "target_id": target_id or "self"
            }
        )
