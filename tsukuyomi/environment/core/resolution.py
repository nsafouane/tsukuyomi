"""
Fate Resolution Logic

This module contains the core resolution logic for determining the fate
of proposals submitted to the Fate Engine.
"""

import logging
import uuid
import time
import asyncio
from typing import List, Dict, Optional, Any
from tsukuyomi.transport.proto import core_pb2, common_pb2
from tsukuyomi.environment.rules.action_logic import ActionResolver
from tsukuyomi.shared.utils import to_pb_timestamp

logger = logging.getLogger("FateResolvers")

class FateResolvers:
    """Base class for fate resolution logic."""

    async def _resolve_proposal(
        self, proposal: core_pb2.Proposal
    ) -> core_pb2.Resolution:
        """
        Determine the fate of a proposal.

        For Phase 1, we implement basic movement and interaction resolution.
        Phase 2 adds affordance validation for object interactions.

        Future phases will include physics checks, conflict resolution, and
        skill-based outcomes.
        """
        actor_id = proposal.actor_id

        # Check if actor exists
        if actor_id not in self.world_state.actors:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=False,
                reason="Actor not found in world state",
            )

        actor = self.world_state.actors[actor_id]

        # Phase 2: Affordance validation for object interactions
        if self.enable_phase2 and self.affordance_validator:
            # Check if action involves an object
            target_id = proposal.parameters.get("target_id")
            if target_id and target_id in self.world_state.objects:
                obj = self.world_state.objects[target_id]

                # Validate action against affordances
                validation = self.affordance_validator.validate_action(
                    obj, proposal.action, actor, proposal.parameters
                )

                if not validation.is_valid:
                    logger.debug(
                        f"Affordance validation failed for {proposal.proposal_id}: "
                        f"{validation.reason}"
                    )
                    return core_pb2.Resolution(
                        proposal_id=proposal.proposal_id,
                        actor_id=actor_id,
                        success=False,
                        reason=f"Affordance validation failed: {validation.reason}",
                    )

        # Resolve based on action type
        if proposal.action == core_pb2.ActionType.MOVE:
            return await self._resolve_move(proposal, actor)
        elif proposal.action == core_pb2.ActionType.INTERACT:
            return await self._resolve_interact(proposal, actor)
        elif proposal.action == core_pb2.ActionType.IDLE:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=True,
                outcome={
                    "action": "idle",
                    "duration": proposal.parameters.get("duration", "1"),
                },
            )
        elif proposal.action == core_pb2.ActionType.EMOTE:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=True,
                outcome={
                    "action": "emote",
                    "emote_type": proposal.parameters.get("type", "wave"),
                },
            )
        elif proposal.action == core_pb2.ActionType.COLLECT:
            return await ActionResolver.resolve_collect(
                proposal, actor, self.world_state
            )
        elif proposal.action == core_pb2.ActionType.USE:
            return await ActionResolver.resolve_use(proposal, actor, self.world_state)
        elif proposal.action == core_pb2.ActionType.EXAMINE:
            return await self._resolve_examine(proposal, actor)
        elif proposal.action == core_pb2.ActionType.TAKE:
            return await self._resolve_take(proposal, actor)
        elif proposal.action == core_pb2.ActionType.DROP:
            return await self._resolve_drop(proposal, actor)
        elif proposal.action == core_pb2.ActionType.REFLECT:
            return await self._resolve_reflect(proposal, actor)
        else:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=False,
                reason=f"Unknown action type: {core_pb2.ActionType.Name(proposal.action)}",
            )

    async def _resolve_move(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve a movement proposal."""
        destination_name = proposal.parameters.get("destination")

        # Check if destination exists
        if not destination_name or destination_name not in self.world_state.locations:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=False,
                reason="Invalid or unknown destination",
            )

        dest_loc = self.world_state.locations[destination_name]
        current_pos = actor.position

        # Calculate distance (for Phase 1, movement is instant)
        distance = (
            (dest_loc.position.x - current_pos.x) ** 2
            + (dest_loc.position.y - current_pos.y) ** 2
        ) ** 0.5

        # For Phase 1, we allow unlimited movement
        # Future: check stamina, path obstacles, etc.

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={
                "action": "move",
                "from_x": str(current_pos.x),
                "from_y": str(current_pos.y),
                "to_x": str(dest_loc.position.x),
                "to_y": str(dest_loc.position.y),
                "destination": destination_name,
                "distance": str(distance),
            },
        )

    async def _resolve_interact(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve an interaction proposal."""
        target_id = proposal.parameters.get("target_id")
        interaction_type = proposal.parameters.get("type", "generic")

        # For Phase 1, interactions always succeed
        # Future: check relationship, skills, cooldowns, etc.

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={
                "action": "interact",
                "type": interaction_type,
                "target_id": target_id,
            },
        )

    async def _resolve_examine(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve an EXAMINE proposal."""
        target_id = proposal.parameters.get("target_id")

        if target_id in self.world_state.objects:
            obj = self.world_state.objects[target_id]
            distance = (
                (actor.position.x - obj.position.x) ** 2
                + (actor.position.y - obj.position.y) ** 2
            ) ** 0.5

            if distance > 10.0:
                return core_pb2.Resolution(
                    proposal_id=proposal.proposal_id,
                    actor_id=proposal.actor_id,
                    success=False,
                    reason="Target object is too far away (beyond 10m)",
                )

            revealed = {}
            if hasattr(obj, "hidden_properties"):
                for key, value in obj.hidden_properties.items():
                    revealed[key] = value

            # FIX: Include revealed_properties in the outcome
            outcome = {
                "action": "examine",
                "object_id": target_id,
                "object_type": obj.type,
                "distance": str(distance),
            }
            if revealed:
                outcome["revealed_properties"] = revealed

            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=True,
                outcome=outcome,
            )

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=False,
            reason=f"Target object not found: {target_id}",
        )

    async def _resolve_take(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve a TAKE proposal."""
        target_id = proposal.parameters.get("target_id")

        if target_id in self.world_state.objects:
            obj = self.world_state.objects[target_id]

            if obj.owner_id and obj.owner_id != proposal.actor_id:
                return core_pb2.Resolution(
                    proposal_id=proposal.proposal_id,
                    actor_id=proposal.actor_id,
                    success=False,
                    reason=f"Object is owned by another actor: {obj.owner_id}",
                )

            distance = (
                (actor.position.x - obj.position.x) ** 2
                + (actor.position.y - obj.position.y) ** 2
            ) ** 0.5
            if distance > 5.0:
                return core_pb2.Resolution(
                    proposal_id=proposal.proposal_id,
                    actor_id=proposal.actor_id,
                    success=False,
                    reason="Object is too far to pick up",
                )

            obj.owner_id = proposal.actor_id
            if hasattr(obj, "state"):
                obj.state = "in_inventory"

            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=True,
                outcome={
                    "action": "take",
                    "object_id": target_id,
                    "object_type": obj.type,
                },
            )

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=False,
            reason=f"Target object not found: {target_id}",
        )

    async def _resolve_drop(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve a DROP proposal."""
        target_id = proposal.parameters.get("target_id")

        if target_id in actor.inventory:
            actor.inventory.remove(target_id)
            obj = self.world_state.objects.get(target_id)

            if obj:
                obj.position.CopyFrom(actor.position)
                obj.owner_id = ""
                if hasattr(obj, "state"):
                    obj.state = "on_ground"

                return core_pb2.Resolution(
                    proposal_id=proposal.proposal_id,
                    actor_id=proposal.actor_id,
                    success=True,
                    outcome={
                        "action": "drop",
                        "object_id": target_id,
                        "position": f"({actor.position.x}, {actor.position.y})",
                    },
                )

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=False,
            reason=f"Object not in inventory: {target_id}",
        )

    async def _resolve_reflect(
        self, proposal: core_pb2.Proposal, actor: core_pb2.Actor
    ) -> core_pb2.Resolution:
        """Resolve a REFLECT proposal (internal action)."""
        params = proposal.parameters
        topic = params.get("topic", "general")
        position = params.get("position", "neutral")
        weight = params.get("weight", 0.5)
        reasoning = params.get("reasoning", "")

        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={
                "action": "reflect",
                "topic": topic,
                "position": position,
                "weight": str(weight),
                "reasoning": reasoning,
            },
        )

    async def _apply_outcome(self, resolution: core_pb2.Resolution):
        """Apply a successful resolution outcome to world state."""
        actor_id = resolution.actor_id

        if actor_id not in self.world_state.actors:
            return

        actor = self.world_state.actors[actor_id]
        outcome = resolution.outcome

        if outcome.get("action") == "move":
            old_position = (actor.position.x, actor.position.y)
            actor.position.x = float(outcome.get("to_x", actor.position.x))
            actor.position.y = float(outcome.get("to_y", actor.position.y))
            actor.current_location = outcome.get("destination", actor.current_location)
            actor.state = "IDLE"

            # Phase 2: Update spatial index
            if self.enable_phase2 and self.spatial_index:
                new_position = (actor.position.x, actor.position.y)
                self.spatial_index.update_position(actor_id, new_position)
                logger.debug(
                    f"Updated spatial index for {actor.name}: {old_position} -> {new_position}"
                )

        elif outcome.get("action") == "collect":
            obj_id = outcome.get("object_id")
            if obj_id in self.world_state.objects:
                # Phase 2: Remove from spatial index
                if self.enable_phase2 and self.spatial_index:
                    obj = self.world_state.objects[obj_id]
                    obj_pos = (obj.position.x, obj.position.y)
                    # Try to remove object from spatial index
                    try:
                        self.spatial_index.remove(obj_id)
                    except:
                        pass

                actor.inventory.append(obj_id)
                del self.world_state.objects[obj_id]
                logger.info(f"Actor {actor.name} collected {obj_id}")

        elif outcome.get("action") == "use":
            item_id = outcome.get("item_id")
            if item_id in actor.inventory:
                actor.inventory.remove(item_id)
                logger.info(f"Actor {actor.name} used {item_id}")

        elif outcome.get("action") == "take":
            obj_id = outcome.get("object_id")
            if obj_id in self.world_state.objects:
                obj = self.world_state.objects[obj_id]

                # Phase 2: Remove from spatial index
                if self.enable_phase2 and self.spatial_index:
                    obj_pos = (obj.position.x, obj.position.y)
                    try:
                        self.spatial_index.remove(obj_id)
                    except:
                        pass

                obj.owner_id = actor_id
                if hasattr(obj, "state"):
                    obj.state = "in_inventory"
                actor.inventory.append(obj_id)
                del self.world_state.objects[obj_id]
                logger.info(f"Actor {actor.name} took {obj_id}")

        elif outcome.get("action") == "drop":
            obj_id = outcome.get("object_id")
            if obj_id in actor.inventory:
                actor.inventory.remove(obj_id)
                obj = self.world_state.objects.get(obj_id)
                if obj:
                    obj.position.CopyFrom(actor.position)
                    obj.owner_id = ""
                    if hasattr(obj, "state"):
                        obj.state = "on_ground"
                    self.world_state.objects[obj_id] = obj

                    # Phase 2: Add to spatial index
                    if self.enable_phase2 and self.spatial_index:
                        obj_pos = (obj.position.x, obj.position.y)
                        self.spatial_index.insert(obj_id, obj_pos)

                logger.info(f"Actor {actor.name} dropped {obj_id}")

        elif outcome.get("action") == "examine":
            obj_id = outcome.get("object_id")
            if obj_id in self.world_state.objects:
                obj = self.world_state.objects[obj_id]
                if hasattr(obj, "hidden_properties") and outcome.get(
                    "revealed_properties"
                ):
                    for key, value in outcome["revealed_properties"].items():
                        obj.properties[key] = value
                logger.info(f"Actor {actor.name} examined {obj_id}")

        elif outcome.get("action") == "reflect":
            topic = outcome.get("topic", "general")
            position = outcome.get("position", "neutral")
            logger.info(f"Actor {actor.name} reflected on {topic}: {position}")

        elif outcome.get("action") == "interact":
            interaction = core_pb2.Interaction(
                type=outcome.get("type", "generic"),
                target_id=outcome.get("target_id", ""),
                tick_timestamp=to_pb_timestamp(time.time()),
            )
            actor.interactions.append(interaction)

    # -------------------------------------------------------------------------
    # Reflex Integration
    # -------------------------------------------------------------------------

    async def _generate_reflex_proposals(self, tick: int) -> List[core_pb2.Proposal]:
        """
        Generate proposals from the System 1 reflex layer.

        This allows NPCs to automatically propose actions based on
        their needs and environmental stimuli.
        """
        if not self.reflex_layer:
            return []

        # Get world from reflex layer if it has agents
        try:
            world = getattr(self.reflex_layer, "world", None)
            if not world:
                return []

            proposals = []

            # Generate proposals for each agent based on their reflex state
            for agent_id_str, agent in world.agents.items():  # agent.id is uuid.UUID
                # MOVEMENT REFLEX
                if agent.state.name == "WALKING" and agent.target_destination:
                    # Propose movement to target
                    proposals.append(
                        core_pb2.Proposal(
                            proposal_id=str(uuid.uuid4()),
                            actor_id=agent_id_str,  # Use string representation
                            action=core_pb2.ActionType.MOVE,
                            parameters={
                                "destination": self._find_location_name(
                                    agent.target_destination
                                )
                                or ""
                            },
                            timestamp=to_pb_timestamp(time.time()),
                        )
                    )

                # COLLECTION REFLEX: Check for nearby collectible objects
                actor = self.world_state.actors.get(agent_id_str)
                if actor:
                    # Find nearby interactive objects within 2.0 distance
                    for obj_id, obj in self.world_state.objects.items():
                        if obj.interactive:
                            dist = (
                                (actor.position.x - obj.position.x) ** 2
                                + (actor.position.y - obj.position.y) ** 2
                            ) ** 0.5

                            # Simple rule: Collect food or tools if nearby
                            if dist < 2.0 and obj.type in ("food", "tool"):
                                # Only collect if not already in inventory
                                if obj_id not in actor.inventory:
                                    proposals.append(
                                        core_pb2.Proposal(
                                            proposal_id=str(uuid.uuid4()),
                                            actor_id=agent_id_str,
                                            action=core_pb2.ActionType.COLLECT,
                                            parameters={"target_id": obj_id},
                                            timestamp=to_pb_timestamp(time.time()),
                                        )
                                    )

            return proposals
        except Exception as e:
            logger.error(f"Error generating reflex proposals: {e}", exc_info=True)
            return []

    def _find_location_name(self, position: common_pb2.Vector2) -> Optional[str]:
        """Find the location name closest to a position."""
        for name, loc in self.world_state.locations.items():
            if loc.position.x == position.x and loc.position.y == position.y:
                return name
        return None

    def attach_reflex_layer(self, reflex_layer):
        """Attach a System 1 reflex layer to the fate engine."""
        self.reflex_layer = reflex_layer
        logger.info("Reflex layer attached to Fate Engine")
