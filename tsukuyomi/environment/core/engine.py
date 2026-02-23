"""
TSUKUYOMI Environment Engine - Phase 2 Enhanced
================================================

Implements the Logical Tick Loop with 20 TPS, handling:
- State Broadcast
- Multi-Tick Proposal Window (Phase 2)
- Fate Resolution with Affordance Validation (Phase 2)
- Spatial Index Integration (Phase 2)
- System 1 Reflex Integration

The Environment Engine is the authoritative core of the simulation.

Phase 2 Enhancements:
- Multi-tick proposal windows with conflict resolution
- Affordance-based action validation
- Spatial index for efficient proximity queries
- Enhanced performance for 50+ agents
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
from tsukuyomi.transport.proto import common_pb2
from tsukuyomi.transport.proto import core_pb2

# Import Phase 2 components
from tsukuyomi.environment.spatial.spatial import SpatialIndex
from tsukuyomi.environment.core.proposal import ProposalWindow, ConflictResolution
from tsukuyomi.environment.rules.affordance import AffordanceValidator, ValidationResult

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EnvironmentEngine")

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

from tsukuyomi.shared.utils import to_pb_timestamp, from_pb_timestamp
from tsukuyomi.services.database import DBManager
from tsukuyomi.environment.rules.action_logic import ActionResolver
from tsukuyomi.environment.core.resolution import FateResolvers

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


class EnvironmentEngine(FateResolvers):
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
        medieval_compatibility: bool = True,
        # Phase 2 parameters
        enable_phase2: bool = True,
        multi_tick_window_duration: int = 3,  # Number of ticks for proposal window
        spatial_cell_size: float = 10.0,
        conflict_resolution: ConflictResolution = ConflictResolution.HIGHEST_PRIORITY,
    ):
        # Initialize base class
        super().__init__()

        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate
        self.proposal_window_ms = proposal_window_ms

        # Phase 2 flag
        self.enable_phase2 = enable_phase2

        # Determinism setup
        self.seed = seed if seed is not None else int(time.time())
        self.rng = random.Random(self.seed)

        # Tick state
        self.current_tick = 0
        self.running = False
        self._paused = False
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

            # Hardcoded defaults for medieval scenario if world is still empty (backward compatibility for tests)
            if medieval_compatibility or not self.world_state.locations:
                medieval_locations = {
                    "market_square": (0, 0),
                    "tavern": (10, 10),
                    "inn": (-5, 5),
                    "well": (2, -3),
                }
                for name, pos in medieval_locations.items():
                    if name not in self.world_state.locations:
                        self.world_state.locations[name].CopyFrom(
                            core_pb2.Location(
                                name=name, position=common_pb2.Vector2(x=pos[0], y=pos[1])
                            )
                        )

        # Phase 2: Initialize Spatial Index
        if self.enable_phase2:
            # Calculate world bounds from scenario or use defaults
            max_x = max(loc.position.x for loc in self.world_state.locations.values()) if self.world_state.locations else 100
            max_y = max(loc.position.y for loc in self.world_state.locations.values()) if self.world_state.locations else 100
            min_x = min(loc.position.x for loc in self.world_state.locations.values()) if self.world_state.locations else -100
            min_y = min(loc.position.y for loc in self.world_state.locations.values()) if self.world_state.locations else -100

            world_width = max(abs(max_x), abs(min_x)) * 2 + 100
            world_height = max(abs(max_y), abs(min_y)) * 2 + 100

            self.spatial_index = SpatialIndex(
                width=world_width,
                height=world_height,
                cell_size=spatial_cell_size
            )
            logger.info(f"Phase 2: Spatial Index initialized with {world_width}x{world_height} world, {spatial_cell_size}m cells")
        else:
            self.spatial_index = None

        # Phase 2: Initialize Proposal Window
        if self.enable_phase2:
            self.proposal_window = ProposalWindow(
                duration_ticks=multi_tick_window_duration,
                max_proposals_per_actor=2,
                conflict_resolution=conflict_resolution,
                auto_resolve=True
            )
            logger.info(f"Phase 2: Proposal Window initialized with {multi_tick_window_duration}-tick duration")
        else:
            self.proposal_window = None

        # Phase 2: Initialize Affordance Validator
        if self.enable_phase2:
            self.affordance_validator = AffordanceValidator()
            logger.info("Phase 2: Affordance Validator initialized")
        else:
            self.affordance_validator = None

        # Proposal management (backward compatible)
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

        phase_info = " (Phase 2 Enabled)" if self.enable_phase2 else ""
        logger.info(
            f"Environment Engine initialized with seed={self.seed}, tick_rate={self.tick_rate} TPS{phase_info}"
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
            proposal.timestamp.CopyFrom(to_pb_timestamp(time.time()))
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
        Phase 2: Multi-Tick Proposal Window

        Open a proposal window that can span multiple ticks.
        Proposals are batched and conflicts are resolved when the window closes.

        For Phase 1 compatibility: Falls back to single-tick collection.
        """
        if self.enable_phase2 and self.proposal_window:
            # Phase 2: Use multi-tick proposal window

            # Check if we need to open a new window
            if not self.proposal_window.is_open:
                self.proposal_window.open_window(tick)
                logger.debug(f"  Opened new proposal window at tick {tick}")

            # Collect proposals for this tick
            proposals = await self.flush_proposals()

            # Add collected proposals to the window
            for proposal in proposals:
                self.proposal_window.add_proposal(proposal, priority=0)

            # Generate reflex proposals if reflex layer is attached
            if self.reflex_layer:
                reflex_proposals = await self._generate_reflex_proposals(tick)
                for proposal in reflex_proposals:
                    self.proposal_window.add_proposal(proposal, priority=0)
                logger.debug(f"  Added {len(reflex_proposals)} reflex proposals to window")

            # Check if window has expired
            if self.proposal_window.is_expired(tick):
                # Get ready proposals after conflict resolution
                ready_proposals = self.proposal_window.get_ready_proposals()
                rejected_proposals = self.proposal_window.get_rejected_proposals()

                logger.debug(
                    f"  Proposal window expired: {len(ready_proposals)} ready, "
                    f"{len(rejected_proposals)} rejected"
                )

                self.current_window_proposals = ready_proposals

                # Log conflict results
                conflict_results = self.proposal_window.resolve_conflicts()
                for result in conflict_results:
                    if result.winning_proposal:
                        logger.debug(
                            f"    Conflict resolved: {result.winning_proposal.proposal_id} won "
                            f"using {result.resolution_strategy.value}"
                        )
                    for rejected in result.rejected_proposals:
                        logger.debug(f"    Rejected: {rejected.proposal_id} - {result.reason}")

                # Close window (next window will open on next tick)
                self.proposal_window.close_window()
            else:
                # Window still open, keep proposals for next tick
                self.current_window_proposals = []
                logger.debug(
                    f"  Proposal window still open: "
                    f"{self.proposal_window.get_ticks_remaining(tick)} ticks remaining"
                )

        else:
            # Phase 1 compatibility: Single-tick collection
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
            self.current_window_proposals, key=lambda p: from_pb_timestamp(p.timestamp)
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
        logger.info(f"Starting Environment Engine at {self.tick_rate} TPS")

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
                timestamp=to_pb_timestamp(time.time()),
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
        logger.info(f"Environment Engine stopped at tick {self.current_tick}")

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

        # Phase 2: Add to spatial index
        if self.enable_phase2 and self.spatial_index:
            self.spatial_index.insert(actor_id, position)

        logger.info(f"Actor registered: {name} ({actor_id})")

    def unregister_actor(self, actor_id: str):
        """Remove an actor from the world state."""
        if actor_id in self.world_state.actors:
            name = self.world_state.actors[actor_id].name
            del self.world_state.actors[actor_id]

            # Phase 2: Remove from spatial index
            if self.enable_phase2 and self.spatial_index:
                self.spatial_index.remove(actor_id)

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

    # -------------------------------------------------------------------------
    # Phase 2: Statistics and Monitoring
    # -------------------------------------------------------------------------

    def get_phase2_stats(self) -> Dict:
        """
        Get statistics for Phase 2 components.

        Returns:
            Dictionary with Phase 2 statistics
        """
        stats = {
            "phase2_enabled": self.enable_phase2,
        }

        if self.enable_phase2:
            # Spatial Index stats
            if self.spatial_index:
                stats["spatial_index"] = self.spatial_index.get_stats()

            # Proposal Window stats
            if self.proposal_window:
                stats["proposal_window"] = self.proposal_window.get_stats()

            # Affordance Validator stats
            if self.affordance_validator:
                stats["affordance_validator"] = self.affordance_validator.get_stats()

        return stats


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
        timestamp=to_pb_timestamp(time.time()),
    )


# ============================================================================
# Server Entry Point
# ============================================================================

async def serve():
    """Start the Environment Engine as a gRPC server."""
    engine = EnvironmentEngine(tick_rate=20, seed=42)
    logger.info("Starting Environment Engine Server on port 50051...")

    # Start the engine loop (it starts the gRPC server internally)
    await engine.run()

# Backward compatibility alias
FateEngine = EnvironmentEngine

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
