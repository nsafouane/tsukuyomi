"""
TSUKUYOMI Fate Engine - Phase 1 Prototype
==========================================

Implements the Logical Tick Loop with 20 TPS, handling:
- State Broadcast
- Proposal Window
- Fate Resolution
- System 1 Reflex Integration

The Fate Engine is the authoritative core of the simulation.
"""

import asyncio
import json
import os
import random
import time
import uuid
from typing import List, Optional, Callable, Awaitable, Dict
import logging
from collections import defaultdict

# Import generated protobuf classes
from tsukuyomi.proto import common_pb2
from tsukuyomi.proto import core_pb2

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FateEngine")

# ============================================================================
# Data Structures (now using Protobuf)
# ============================================================================

# These are now directly imported from core_pb2
ActionType = core_pb2.ActionType
Proposal = core_pb2.Proposal
Resolution = core_pb2.Resolution
TickState = core_pb2.TickState
Actor = core_pb2.Actor
Location = core_pb2.Location
WorldState = core_pb2.WorldState

# ============================================================================
# Utility Functions for Protobuf Timestamps
# ============================================================================


def _to_pb_timestamp(t: float) -> common_pb2.Timestamp:
    seconds = int(t)
    nanos = int((t - seconds) * 1e9)
    return common_pb2.Timestamp(seconds=seconds, nanos=nanos)


def _from_pb_timestamp(pb_timestamp: common_pb2.Timestamp) -> float:
    return pb_timestamp.seconds + pb_timestamp.nanos / 1e9


from tsukuyomi.proto.db_manager import DBManager
from tsukuyomi.proto.action_logic import ActionResolver

# ============================================================================
# Scenario Config Loader
# ============================================================================


def _load_scenario_config(config_path: Optional[str] = None) -> Dict:
    """
    Load scenario configuration from JSON file.

    Args:
        config_path: Path to JSON config file. If None, uses default_scenario.json

    Returns:
        Dictionary with locations and objects configuration
    """
    if config_path is None:
        # Default path relative to this file
        module_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(module_dir, "default_scenario.json")

    if not os.path.exists(config_path):
        logger.warning(f"Scenario config not found at {config_path}, using empty config")
        return {"locations": {}, "objects": {}}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded scenario configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load scenario config from {config_path}: {e}")
        return {"locations": {}, "objects": {}}


# ============================================================================
# Fate Engine Core
# ============================================================================


class FateEngine:
    """
    The core authority of the simulation.

    Implements a deterministic tick loop at 20 TPS that:
    1. Broadcasts current state
    2. Opens a proposal window
    3. Resolves proposals and updates state
    4. Integrates with System 1 reflexes
    """

    def __init__(
        self,
        tick_rate: int = 20,
        proposal_window_ms: int = 25,  # Time window to accept proposals per tick
        seed: Optional[int] = None,
        db_path: Optional[str] = None,
        scenario_config: Optional[str] = None,  # Path to scenario JSON config
    ):
        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate
        self.proposal_window_ms = proposal_window_ms

        # Determinism setup
        self.seed = seed if seed is not None else int(time.time())
        self.rng = random.Random(self.seed)

        # Tick state
        self.current_tick = 0
        self.running = False
        self.tick_history: List[core_pb2.TickState] = []

        # Persistence
        self.db = DBManager(db_path) if db_path else None
        if self.db:
            latest = self.db.get_latest_tick_number()
            if latest >= 0:
                last_state = self.db.get_tick(latest)
                if last_state:
                    self.current_tick = latest + 1
                    self.world_state = last_state.world_state
                    logger.info(f"Resumed from DB at tick {self.current_tick}")

        # World state (now loaded from config instead of hardcoded)
        if not hasattr(self, "world_state") or not self.world_state.locations:
            if not hasattr(self, "world_state"):
                self.world_state = core_pb2.WorldState()

            # FIX: Load scenario configuration from JSON file instead of hardcoding
            self._load_scenario(scenario_config)

        # Proposal management
        self.proposal_queue: List[core_pb2.Proposal] = []
        self.current_window_proposals: List[core_pb2.Proposal] = []
        self.proposal_buffer_lock = asyncio.Lock()

        self.world_state.global_events.extend([])  # Empty list for now

        # Resolution history for feedback (2-tick delay)
        self.resolution_buffer: Dict[int, List[core_pb2.Resolution]] = defaultdict(list)

        # Phase hooks
        self.pre_broadcast_hooks: List[Callable[[int], Awaitable[None]]] = []
        self.post_resolution_hooks: List[
            Callable[[int, List[core_pb2.Resolution]], Awaitable[None]]
        ] = []

        # System 1 reflex layer (to be attached)
        self.reflex_layer: Optional[object] = None

        logger.info(
            f"Fate Engine initialized with seed={self.seed}, tick_rate={self.tick_rate} TPS"
        )

    def _load_scenario(self, scenario_config: Optional[str] = None):
        """
        Load world state from scenario configuration file.

        This replaces the hardcoded medieval data with a flexible configuration system.
        """
        config = _load_scenario_config(scenario_config)

        # Load locations from config
        for loc_name, loc_data in config.get("locations", {}).items():
            self.world_state.locations[loc_name].CopyFrom(
                core_pb2.Location(
                    name=loc_data.get("name", loc_name),
                    position=common_pb2.Vector2(
                        x=loc_data.get("position", {}).get("x", 0),
                        y=loc_data.get("position", {}).get("y", 0)
                    )
                )
            )
            logger.debug(f"Loaded location: {loc_name}")

        # Load objects from config
        for obj_id, obj_data in config.get("objects", {}).items():
            self.world_state.objects[obj_id].CopyFrom(
                core_pb2.EnvironmentObject(
                    id=obj_id,
                    type=obj_data.get("type", "unknown"),
                    position=common_pb2.Vector2(
                        x=obj_data.get("position", {}).get("x", 0),
                        y=obj_data.get("position", {}).get("y", 0)
                    ),
                    interactive=obj_data.get("interactive", False),
                    properties=obj_data.get("properties", {})
                )
            )
            logger.debug(f"Loaded object: {obj_id}")

        logger.info(f"Loaded {len(self.world_state.locations)} locations and {len(self.world_state.objects)} objects from scenario config")

    # -------------------------------------------------------------------------
    # Proposal Management
    # -------------------------------------------------------------------------

    async def submit_proposal(self, proposal: core_pb2.Proposal) -> bool:
        """
        Submit a proposal to be considered in the current or next tick window.

        Returns True if proposal was accepted into current window,
        False if queued for next tick.
        """
        async with self.proposal_buffer_lock:
            proposal.timestamp.CopyFrom(_to_pb_timestamp(time.time()))
            self.proposal_queue.append(proposal)

            logger.debug(
                f"Proposal received: {proposal.proposal_id} from {proposal.actor_id}"
            )
            return True

    async def flush_proposals(self) -> List[core_pb2.Proposal]:
        """Get all pending proposals and clear the queue."""
        async with self.proposal_buffer_lock:
            proposals = self.proposal_queue.copy()
            self.proposal_queue.clear()
            return proposals

    # -------------------------------------------------------------------------
    # Core Tick Phases
    # -------------------------------------------------------------------------

    async def _phase_state_broadcast(self, tick: int):
        """
        Phase 1: State Broadcast

        Broadcast the current world state to all observers.
        This includes: tick number, actor states, location data.
        """
        # Execute pre-broadcast hooks
        for hook in self.pre_broadcast_hooks:
            try:
                await hook(tick)
            except Exception as e:
                logger.error(
                    f"Pre-broadcast hook error at tick {tick}: {e}", exc_info=True
                )

        # Broadcast tick info
        logger.info(f"=== Tick [{tick}] ===")

        # Broadcast actor states (sample for demo)
        active_actors = list(self.world_state.actors.values())[:5]
        for actor in active_actors:
            logger.debug(
                f"  Actor {actor.name}: pos=({actor.position.x}, {actor.position.y}), state={actor.state}"
            )

        # Broadcast pending proposal count
        pending = len(self.proposal_queue)
        logger.debug(f"  Pending proposals: {pending}")

    async def _phase_proposal_window(self, tick: int):
        """
        Phase 2: Proposal Window

        Open a small time window to receive actor proposals.
        For Phase 1, we simply collect proposals that have accumulated.
        """
        # Collect proposals for this tick
        proposals = await self.flush_proposals()
        self.current_window_proposals = proposals

        logger.debug(f"  Proposal window collected {len(proposals)} proposals")

        # Generate reflex proposals if reflex layer is attached
        if self.reflex_layer:
            reflex_proposals = await self._generate_reflex_proposals(tick)
            self.current_window_proposals.extend(reflex_proposals)
            logger.debug(f"  Generated {len(reflex_proposals)} reflex proposals")

    async def _phase_fate_resolution(self, tick: int) -> List[core_pb2.Resolution]:
        """
        Phase 3: Fate Resolution

        Resolve all proposals and update world state.
        This is where the "Fate" of each proposal is determined.

        Returns list of resolutions for feedback.
        """
        resolutions = []

        # Sort proposals by timestamp for deterministic processing
        sorted_proposals = sorted(
            self.current_window_proposals, key=lambda p: _from_pb_timestamp(p.timestamp)
        )

        for proposal in sorted_proposals:
            resolution = await self._resolve_proposal(proposal)
            resolutions.append(resolution)

            # If successful, apply the state change
            if resolution.success:
                await self._apply_outcome(resolution)

            logger.debug(
                f"  Resolved {ActionType.Name(proposal.action)} for {proposal.actor_id}: "
                f"{'SUCCESS' if resolution.success else 'FAILED'}"
            )

        # Store resolutions for 2-tick feedback delay
        feedback_tick = tick + 2
        self.resolution_buffer[feedback_tick] = resolutions

        return resolutions

    # -------------------------------------------------------------------------
    # Resolution Logic
    # -------------------------------------------------------------------------

    async def _resolve_proposal(
        self, proposal: core_pb2.Proposal
    ) -> core_pb2.Resolution:
        """
        Determine the fate of a proposal.

        For Phase 1, we implement basic movement and interaction resolution.
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
                reason=f"Unknown action type: {ActionType.Name(proposal.action)}",
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
            actor.position.x = float(outcome.get("to_x", actor.position.x))
            actor.position.y = float(outcome.get("to_y", actor.position.y))
            actor.current_location = outcome.get("destination", actor.current_location)
            actor.state = "IDLE"

        elif outcome.get("action") == "collect":
            obj_id = outcome.get("object_id")
            if obj_id in self.world_state.objects:
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
                tick_timestamp=_to_pb_timestamp(time.time()),
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
                            timestamp=_to_pb_timestamp(time.time()),
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
                                            timestamp=_to_pb_timestamp(time.time()),
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

    # -------------------------------------------------------------------------
    # Tick Loop
    # -------------------------------------------------------------------------

    async def run(self):
        """
        Main tick loop running at 20 TPS.

        Each tick executes:
        1. State Broadcast
        2. Proposal Window
        3. Fate Resolution
        """
        self.running = True
        logger.info(f"Starting Fate Engine at {self.tick_rate} TPS")

        while self.running:
            start_time = time.perf_counter()

            # Phase 1: State Broadcast
            await self._phase_state_broadcast(self.current_tick)

            # Phase 2: Proposal Window
            await self._phase_proposal_window(self.current_tick)

            # Phase 3: Fate Resolution
            resolutions = await self._phase_fate_resolution(self.current_tick)
            logger.debug(
                f"Tick {self.current_tick}: _phase_fate_resolution returned {len(resolutions)} resolutions."
            )

            # Store tick state for debugging/history
            tick_state = core_pb2.TickState(
                tick_number=self.current_tick,
                timestamp=_to_pb_timestamp(time.time()),
                world_state=self._get_world_snapshot(),
                pending_proposals=self.current_window_proposals,
                resolutions=resolutions,
            )
            self.tick_history.append(tick_state)

            # Execute post-resolution hooks (now that history is updated)
            for hook in self.post_resolution_hooks:
                try:
                    await hook(self.current_tick, resolutions)
                except Exception as e:
                    logger.error(
                        f"Post-resolution hook error at tick {self.current_tick}: {e}",
                        exc_info=True,
                    )

            # Persist to database
            if self.db:
                self.db.save_tick(tick_state)

            # Keep history manageable
            if len(self.tick_history) > 1000:
                self.tick_history.pop(0)

            # Advance tick
            self.current_tick += 1

            # Maintain tick rate
            elapsed = time.perf_counter() - start_time
            sleep_time = self.tick_duration - elapsed

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                if self.current_tick % 100 == 0:
                    logger.warning(
                        f"Tick {self.current_tick - 1} lagged by {abs(sleep_time):.4f}s"
                    )

    def stop(self):
        """Stop the tick loop."""
        self.running = False
        logger.info(f"Fate Engine stopped at tick {self.current_tick}")

    # -------------------------------------------------------------------------
    # Actor Management
    # -------------------------------------------------------------------------

    def register_actor(self, actor_id: str, name: str, position: tuple = (0, 0)):
        """Register an actor in the world state."""
        actor = core_pb2.Actor(
            id=actor_id,
            name=name,
            position=common_pb2.Vector2(x=position[0], y=position[1]),
            state="IDLE",
            current_location="",  # default empty string
        )
        self.world_state.actors[actor_id].CopyFrom(actor)
        logger.info(f"Actor registered: {name} ({actor_id})")

    def unregister_actor(self, actor_id: str):
        """Remove an actor from the world state."""
        if actor_id in self.world_state.actors:
            name = self.world_state.actors[actor_id].name
            del self.world_state.actors[actor_id]
            logger.info(f"Actor unregistered: {name} ({actor_id})")

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _get_world_snapshot(self) -> core_pb2.WorldState:
        """Get a snapshot of the current world state."""
        # A deep copy is implicitly created when assigning to a new protobuf message
        # or when passing it for serialization.
        # For an explicit copy, use world_state_copy = core_pb2.WorldState()
        # world_state_copy.CopyFrom(self.world_state)
        # However, for snapshotting, it's often sufficient to return the current state
        # as subsequent modifications won't affect the already-processed TickState's snapshot.
        return self.world_state

    def get_pending_feedback(self, tick: int) -> List[core_pb2.Resolution]:
        """Get feedback (resolutions) available for a given tick."""
        return self.resolution_buffer.get(tick, [])

    def get_tick_state(self, tick: int) -> Optional[core_pb2.TickState]:
        """Get the state of a specific tick from history."""
        for state in self.tick_history:
            if state.tick_number == tick:
                return state
        return None


# ============================================================================
# Convenience Functions
# ============================================================================


async def create_proposal(
    actor_id: str,  # Now accepts string UUID
    action: str,
    parameters: Dict[str, str],  # Parameters map to string
) -> core_pb2.Proposal:
    """Create a proposal with automatic timestamp."""
    return core_pb2.Proposal(
        proposal_id=str(uuid.uuid4()),  # Generate UUID string
        actor_id=actor_id,
        action=core_pb2.ActionType.Value(
            action.upper()
        ),  # Convert string to enum value
        parameters=parameters,
        timestamp=_to_pb_timestamp(time.time()),
    )


# ============================================================================
# Demo / Test Runner
# ============================================================================


async def demo_fate_engine():
    """Run a quick demonstration of the Fate Engine."""
    # Initialize fate engine with deterministic seed
    engine = FateEngine(tick_rate=20, seed=42)

    # Register some actors (actor_id is now string)
    alice_id = str(uuid.uuid4())
    bob_id = str(uuid.uuid4())

    engine.register_actor(alice_id, "Alice", position=(0, 0))
    engine.register_actor(bob_id, "Bob", position=(5, 5))

    # Submit some initial proposals
    await engine.submit_proposal(
        await create_proposal(
            actor_id=alice_id, action="MOVE", parameters={"destination": "tavern"}
        )
    )

    await engine.submit_proposal(
        await create_proposal(
            actor_id=bob_id, action="EMOTE", parameters={"type": "wave"}
        )
    )

    # Run for a limited time
    async def limited_run():
        await asyncio.sleep(2)  # Run for 2 seconds (~40 ticks)
        engine.stop()

    # Start both the engine and the limiter
    await asyncio.gather(engine.run(), limited_run())

    # Print summary
    print(f"\nDemo completed: {engine.current_tick} ticks executed")
    print(f"Total proposals processed: {len(engine.tick_history)}")

    # Show final state
    final_world_state = engine._get_world_snapshot()
    print("\nFinal World State:")
    for aid, actor in final_world_state.actors.items():
        print(
            f"  {actor.name}: pos=({actor.position.x}, {actor.position.y}), loc={actor.current_location}"
        )


if __name__ == "__main__":
    asyncio.run(demo_fate_engine())
