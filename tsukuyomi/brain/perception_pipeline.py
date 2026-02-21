import logging
from typing import Dict, List, Optional, Any, Tuple
import math

from tsukuyomi.proto import core_pb2
from tsukuyomi.proto import perception_pb2
from tsukuyomi.proto import common_pb2

from .perception_channels import PerceptionChannelsMixin
from .spatial_utils import SensoryProfile, AgentInternalState, Raycaster, Wall

logger = logging.getLogger("PerceptionPipeline")

class PerceptionPipeline(PerceptionChannelsMixin):
    """
    Transforms raw WorldState into agent-specific Percepts.

    Implements Staggered Perception Schedule:
    - Every tick: Proximity heartbeat (lightweight)
    - Every N ticks: Deep perception (full vision/occlusion)
    - Rotation ensures full perception without O(A^2) per tick

    Enhanced with Raycaster for accurate line-of-sight and FOV calculations.
    """

    # Configuration
    DEEP_PERCEPTION_INTERVAL = 3  # Deep perception every N ticks
    ECHO_DECAY_TICKS = 100  # How long memory echoes last
    ECHO_DECAY_RATE = 0.01  # Per-tick decay for echoes

    # Event type base weights for salience
    SALIENCE_BASE_WEIGHTS = {
        "speech": 0.6,
        "movement": 0.2,
        "violence": 1.0,
        "threat": 0.9,
        "door_opened": 0.3,
        "item_dropped": 0.4,
        "unknown": 0.2,
    }

    def __init__(
        self,
        agent_id: str,
        sensory_profile: SensoryProfile,
        spatial_index=None,
        spatial_logic=None,
    ):
        self.agent_id = agent_id
        self.profile = sensory_profile
        self.spatial_index = spatial_index
        self.spatial_logic = spatial_logic

        # Memory Echo tracking
        self.memory_echoes: Dict[str, perception_pb2.MemoryEcho] = {}

        # Staggered perception state
        self._tick_counter = 0
        self._percept_queue: List[perception_pb2.Percept] = []

        # Raycaster for line-of-sight
        self.raycaster = Raycaster(spatial_index)

        logger.info(
            f"PerceptionPipeline initialized for agent {agent_id} "
            f"with raycasting and spatial integration"
        )

    def set_spatial_index(self, spatial_index):
        """Set the spatial index for proximity queries."""
        self.spatial_index = spatial_index
        self.raycaster.spatial_index = spatial_index
        logger.debug(f"Set spatial index for agent {self.agent_id}")

    def set_spatial_logic(self, spatial_logic):
        """Set the spatial logic for room/portal awareness."""
        self.spatial_logic = spatial_logic
        # Register room walls from spatial logic
        if hasattr(spatial_logic, "rooms"):
            for room_id, room in spatial_logic.rooms.items():
                # Convert room boundaries and occlusions to walls
                walls = self._room_to_walls(room)
                self.raycaster.register_room_walls(room_id, walls)
        logger.debug(f"Set spatial logic and registered walls for agent {self.agent_id}")

    def _room_to_walls(self, room) -> List[Wall]:
        """
        Convert a room definition into a list of Wall objects.

        Args:
            room: Room object from SpatialLogic

        Returns:
            List of Wall objects representing room boundaries and occlusions
        """
        walls = []

        # Room boundaries (walls around the room)
        bounds = room.boundaries
        # Create 4 walls for the room boundaries
        corners = [
            (bounds["x_min"], bounds["y_min"]),
            (bounds["x_max"], bounds["y_min"]),
            (bounds["x_max"], bounds["y_max"]),
            (bounds["x_min"], bounds["y_max"]),
        ]

        for i in range(4):
            start = corners[i]
            end = corners[(i + 1) % 4]
            walls.append(Wall(start=start, end=end, thickness=0.5, transparent=False))

        # Occlusions (internal obstacles)
        for ox, oy, orad in room.occlusions:
            # Create a wall approximation for the occlusion
            # Use 4 walls around the circle
            wall_corners = [
                (ox - orad, oy - orad),
                (ox + orad, oy - orad),
                (ox + orad, oy + orad),
                (ox - orad, oy + orad),
            ]

            for i in range(4):
                start = wall_corners[i]
                end = wall_corners[(i + 1) % 4]
                walls.append(Wall(start=start, end=end, thickness=0.1, transparent=False))

        return walls

    def process(
        self,
        world_state: core_pb2.WorldState,
        agent_internal_state: AgentInternalState,
        current_tick: int,
    ) -> List[perception_pb2.Percept]:
        """
        Main processing method. Returns salience-sorted percepts.

        Implements Staggered Perception Schedule:
        - Tick % interval == 0: Deep perception (full vision + occlusion)
        - Other ticks: Proximity heartbeat (distance check only)
        """
        self._tick_counter = current_tick
        percepts = []

        # Check if this is a deep perception tick
        is_deep_tick = (current_tick % self.DEEP_PERCEPTION_INTERVAL) == 0

        # Get agent's own position and state
        my_actor = world_state.actors.get(self.agent_id)
        if not my_actor:
            logger.warning(f"Agent {self.agent_id} not found in world state")
            return []

        my_pos = (my_actor.position.x, my_actor.position.y)

        # Get facing direction from agent state
        my_facing = self._get_facing_vector(
            my_actor, agent_internal_state
        )  # (dx, dy) normalized

        # Process sensory channels based on schedule
        if is_deep_tick:
            logger.debug(f"Tick {current_tick}: Deep perception for {self.agent_id}")
            percepts.extend(
                self._process_vision_deep(
                    world_state, my_actor, agent_internal_state, my_pos, my_facing
                )
            )
        else:
            logger.debug(
                f"Tick {current_tick}: Proximity heartbeat for {self.agent_id}"
            )
            percepts.extend(
                self._process_vision_proximity(
                    world_state, my_actor, agent_internal_state, my_pos
                )
            )

        # Always process hearing (omnidirectional, less expensive)
        percepts.extend(
            self._process_hearing(world_state, my_pos, agent_internal_state)
        )

        # Process proprioception (self-state awareness)
        percepts.extend(self._process_proprioception(my_actor, current_tick))

        # Update and process memory echoes
        percepts.extend(self._process_memory_echoes(world_state, current_tick))

        # Process gossip channel
        percepts.extend(self._process_gossip_channel(world_state, current_tick))

        # Calculate Surprise Factor for each percept
        percepts = self._apply_surprise_factor(percepts)

        # Sort by salience (descending)
        percepts.sort(key=lambda p: p.salience, reverse=True)

        self._percept_queue = percepts

        logger.debug(f"Agent {self.agent_id} generated {len(percepts)} percepts")
        return percepts

