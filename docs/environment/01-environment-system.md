# Environment System

**Path:** `tsukuyomi/environment/`

**Last Updated:** 2026-02-26

---

## Overview

The Environment System provides the world simulation engine that manages locations, objects, actors, and the tick-based proposal/resolution cycle. It is the authoritative core of any Tsukuyomi simulation.

## Philosophy

Per the MVP v0.1 unified environment architecture:
- **Tick-Based Loop**: 20 TPS (ticks per second) deterministic simulation
- **Proposal Window**: Multi-tick commitment phases for complex decisions
- **Conflict Resolution**: Handle competing proposals intelligently
- **Spatial Indexing**: Efficient proximity queries for 50+ agents
- **Affordance Validation**: Actions validated against world rules

---

## Component Structure

```
environment/
├── core/
│   ├── engine.py         # EnvironmentEngine (FateEngine)
│   ├── world_builder.py  # WorldBuilder API
│   ├── proposal.py       # ProposalWindow system
│   └── resolution.py     # Fate resolution logic
├── physics/
│   ├── raycasting.py     # Visual raycasting
│   └── spatial_logic.py  # Spatial queries
├── rules/
│   ├── action_logic.py   # Action resolution
│   └── affordance.py     # Affordance validation
└── spatial/
    └── spatial.py        # SpatialIndex for queries
```

---

## 1. EnvironmentEngine (`engine.py`)

**Location:** `tsukuyomi/environment/core/engine.py`

The core authority of the simulation running at 20 TPS.

### EnvironmentEngine Class

```python
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
        proposal_window_ms: int = 25,
        seed: Optional[int] = None,
        db_path: Optional[str] = None,
        scenario_config: Optional[str] = None,
        medieval_compatibility: bool = True,
        # Phase 2 parameters
        enable_phase2: bool = True,
        multi_tick_window_duration: int = 3,
        spatial_cell_size: float = 10.0,
        conflict_resolution: ConflictResolution = HIGHEST_PRIORITY,
    )

    # Core state
    world_state: core_pb2.WorldState
    current_tick: int
    running: bool
    tick_history: List[core_pb2.TickState]

    # Phase 2 components
    spatial_index: Optional[SpatialIndex]
    proposal_window: Optional[ProposalWindow]
    affordance_validator: Optional[AffordanceValidator]
```

### Tick Loop Phases

```python
async def run(self):
    """
    Main tick loop running at 20 TPS.

    Each tick executes:
    1. State Broadcast
    2. Proposal Window
    3. Fate Resolution
    """

async def _phase_state_broadcast(self, tick: int):
    """
    Phase 1: State Broadcast

    Broadcast current world state to all observers.
    Includes: tick number, actor states, location data.
    """

async def _phase_proposal_window(self, tick: int):
    """
    Phase 2: Multi-Tick Proposal Window

    Open proposal window that can span multiple ticks.
    Proposals are batched and conflicts resolved when window closes.
    """

async def _phase_fate_resolution(self, tick: int) -> List[core_pb2.Resolution]:
    """
    Phase 3: Fate Resolution

    Resolve all proposals and update world state.
    This is where the "Fate" of each proposal is determined.
    """
```

### Proposal Management

```python
async def submit_proposal(self, proposal: core_pb2.Proposal) -> bool:
    """
    Submit a proposal for current or next tick window.

    Returns True if accepted into current window,
    False if queued for next tick.
    """

async def flush_proposals(self) -> List[core_pb2.Proposal]:
    """Get all pending proposals and clear the queue."""
```

### Actor Management

```python
def register_actor(self, actor_id: str, name: str, position: tuple = (0, 0)):
    """Register an actor in the world state."""

def unregister_actor(self, actor_id: str):
    """Remove an actor from the world state."""
```

### Statistics

```python
def get_phase2_stats(self) -> Dict:
    """Get statistics for Phase 2 components (spatial, proposals, affordances)."""

def get_tick_state(self, tick: int) -> Optional[core_pb2.TickState]:
    """Get the state of a specific tick from history."""

def get_pending_feedback(self, tick: int) -> List[core_pb2.Resolution]:
    """Get feedback (resolutions) available for a given tick."""
```

---

## 2. WorldBuilder (`world_builder.py`)

**Location:** `tsukuyomi/environment/core/world_builder.py`

Programmatic API for building and initializing worlds.

### Core Data Structures

```python
class ObjectType(Enum):
    """Types of objects in the world."""
    DECORATION = "decoration"     # Visual props, no interaction
    INTERACTIVE = "interactive"   # Can be interacted with
    CONTAINER = "container"       # Can hold items
    PORTAL = "portal"            # Connects to other locations
    SPAWN_POINT = "spawn"        # Agent spawn locations

@dataclass
class Affordance:
    """Defines what actions are possible on an object."""
    action_type: str
    precondition: Optional[str]
    effect_description: Optional[str]

@dataclass
class EnvironmentObject:
    """Represents an object in the world."""
    object_id: str
    obj_type: ObjectType
    name: str
    position: tuple  # (x, y)
    properties: Dict[str, Any]
    affordances: List[Affordance]

    def add_affordance(self, action_type: str, precondition: str = None, effect: str = None)

@dataclass
class Location:
    """Represents a location/zone in the world."""
    location_id: str
    name: str
    position: tuple  # Center position
    size: tuple  # (width, height)
    objects: List[EnvironmentObject]
    spawn_points: List[tuple]

    def add_object(self, obj: EnvironmentObject)
    def add_spawn_point(self, x: float, y: float)
```

### WorldBuilder Class

```python
@dataclass
class WorldBuilder:
    """Main API for building and configuring worlds."""

    locations: List[Location]
    global_objects: List[EnvironmentObject]
    metadata: Dict[str, Any]

    def add_location(
        self,
        name: str,
        position: tuple,
        size: tuple,
        spawn_points: Optional[List[tuple]] = None
    ) -> Location:
        """Add a location to the world."""

    def add_object(
        self,
        name: str,
        obj_type: ObjectType,
        position: tuple,
        properties: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
    ) -> EnvironmentObject:
        """Add an object to the world."""

    def add_interactive_object(
        self,
        name: str,
        position: tuple,
        affordances: List[Dict[str, str]],
        properties: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
    ) -> EnvironmentObject:
        """Convenience method to add interactive object with affordances."""

    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID."""

    def set_metadata(self, key: str, value: Any):
        """Set metadata for the world."""

    def serialize(self) -> Dict:
        """Serialize world to dictionary for gRPC transmission."""

    @classmethod
    def deserialize(cls, data: Dict) -> 'WorldBuilder':
        """Create WorldBuilder from serialized dictionary."""

    def validate(self) -> List[str]:
        """Validate world configuration. Returns list of errors (empty if valid)."""
```

### Example Usage

```python
builder = WorldBuilder()

# Add locations
market = builder.add_location(
    name="MarketSquare",
    position=(0, 0),
    size=(20, 20),
    spawn_points=[(0, 0), (5, 5)]
)

# Add objects
builder.add_interactive_object(
    name="fountain",
    position=(5, 5),
    affordances=[
        {"action_type": "COLLECT", "precondition": "has_container"},
        {"action_type": "INTERACT", "effect": "gain_water"}
    ]
)

# Initialize engine
await engine.initialize_world(builder.serialize())
```

---

## 3. Proposal Window (`proposal.py`)

**Location:** `tsukuyomi/environment/core/proposal.py`

Multi-tick commitment phase for proposal handling.

### Core Classes

```python
class ConflictResolution(Enum):
    """Strategies for resolving proposal conflicts."""
    FIRST_COME_FIRST_SERVED = "first_come_first_served"
    HIGHEST_PRIORITY = "highest_priority"
    RANDOM = "random"
    MERGE = "merge"

@dataclass
class ProposalMetadata:
    """Metadata for tracking proposals in the window."""
    proposal: core_pb2.Proposal
    priority: int
    tick_submitted: int
    actor_commitments: Set[int]

@dataclass
class ConflictResult:
    """Result of conflict resolution."""
    winning_proposal: Optional[core_pb2.Proposal]
    rejected_proposals: List[core_pb2.Proposal]
    resolution_strategy: ConflictResolution
    reason: str
```

### ProposalWindow Class

```python
class ProposalWindow:
    """
    Manages proposal windows for multi-tick commitment phases.

    Features:
    - Window duration (in ticks)
    - Maximum proposals per actor per window
    - Conflict detection and resolution
    - Priority-based ordering
    - Actor commitment tracking

    Complexity:
    - Add proposal: O(1) amortized
    - Conflict detection: O(n)
    - Conflict resolution: O(n)
    - Tick update: O(n)
    """

    def __init__(
        self,
        duration_ticks: int = 3,
        max_proposals_per_actor: int = 2,
        conflict_resolution: ConflictResolution = HIGHEST_PRIORITY,
        auto_resolve: bool = True
    )

    # Window Management
    def open_window(self, tick_number: int)
    def close_window(self)
    def is_expired(self, tick_number: int) -> bool
    def get_ticks_remaining(self, tick_number: int) -> int

    # Proposal Management
    def add_proposal(self, proposal: core_pb2.Proposal, priority: int = 0) -> bool
    def remove_proposal(self, proposal_id: str) -> bool
    def add_actor_commitment(self, proposal_id: str, tick_index: int) -> bool

    # Conflict Resolution
    def resolve_conflicts(self) -> List[ConflictResult]
    def get_ready_proposals(self) -> List[core_pb2.Proposal]
    def get_rejected_proposals(self) -> List[core_pb2.Proposal]

    # Queries
    def get_proposals_by_actor(self, actor_id: str) -> List[core_pb2.Proposal]
    def get_stats(self) -> Dict
```

---

## 4. Spatial System (`spatial/spatial.py`)

**Location:** `tsukuyomi/environment/spatial/spatial.py`

Spatial indexing for efficient proximity queries.

### SpatialIndex Class

```python
class SpatialIndex:
    """
    Grid-based spatial index for efficient proximity queries.

    Features:
    - O(1) insert/remove
    - O(k) range queries where k = cells in range
    - Supports 50+ agents efficiently
    """

    def __init__(self, width: float, height: float, cell_size: float = 10.0)

    def insert(self, entity_id: str, position: tuple):
        """Insert an entity at position."""

    def remove(self, entity_id: str):
        """Remove an entity."""

    def update(self, entity_id: str, new_position: tuple):
        """Update entity position."""

    def query_range(
        self,
        center: tuple,
        radius: float
    ) -> List[str]:
        """Get all entities within radius of center."""

    def query_nearby(
        self,
        entity_id: str,
        radius: float
    ) -> List[str]:
        """Get all entities within radius of given entity."""

    def get_stats(self) -> Dict:
        """Get spatial index statistics."""
```

---

## 5. Physics Components

### Raycasting (`physics/raycasting.py`)

```python
def cast_ray(
    origin: tuple,
    direction: tuple,
    max_distance: float,
    world_state: WorldState
) -> RaycastResult:
    """
    Cast a ray from origin in direction.

    Returns:
        RaycastResult with hit information
    """

def get_visible_objects(
    actor_position: tuple,
    view_distance: float,
    view_angle: float,
    world_state: WorldState
) -> List[str]:
    """Get all objects visible from position."""
```

### Spatial Logic (`physics/spatial_logic.py`)

**Location:** `tsukuyomi/environment/physics/spatial_logic.py`

**PHASE 11: Multi-Room Spatial Logic**

Manages spatial partitioning of the world into rooms, portal connections, and basic collision/occlusion logic for agent movement.

#### Core Data Structures

```python
@dataclass
class Portal:
    """A connection between two rooms (doorway, archway, gate)."""
    portal_id: str
    source_room_id: str
    target_room_id: str
    position: Tuple[float, float]  # x, y in source room
    size: float = 1.0              # Width of the doorway (collision radius)
    locked: bool = False

@dataclass
class Room:
    """A defined physical space with boundaries and potential occlusions."""
    room_id: str
    name: str
    description: str
    # Simple bounding box for MVP: x_min, x_max, y_min, y_max
    boundaries: Dict[str, float] = field(default_factory=lambda: {
        'x_min': 0.0, 'x_max': 20.0, 'y_min': 0.0, 'y_max': 20.0
    })
    portals: List[Portal] = field(default_factory=list)
    occlusions: List[Tuple[float, float, float]] = field(default_factory=list)  # x, y, radius
```

#### SpatialLogic Class

```python
class SpatialLogic:
    """
    Manages multi-room spatial partitioning and movement validation.

    Responsibilities:
    - Room registry and boundary enforcement
    - Portal traversal logic
    - Basic collision checks (wall avoidance)
    - Line-of-sight occlusion (MVP: simple distance/object check)

    Complexity:
        - Room registry: O(1) add/remove
        - Collision detection: O(n) where n = occlusions per room
        - Portal lookup: O(p) where p = portals per room
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.portals_by_room: Dict[str, List[Portal]] = {}

    # Room Management
    def add_room(self, room: Room) -> None:
        """Register a new room in the world."""

    def add_portal(self, portal: Portal) -> None:
        """Add a portal to a specific room."""

    # Movement Validation
    def can_move_to(
        self,
        room_id: str,
        target_pos: Tuple[float, float],
        radius: float = 0.5
    ) -> bool:
        """
        Check if a position is within the bounds of the current room
        and not colliding with occlusions.

        Process:
        1. Boundary check (with margin for agent radius)
        2. Occlusion/collision check (circle-circle collision)
        """

    def get_portal_at(
        self,
        room_id: str,
        position: Tuple[float, float]
    ) -> Optional[Portal]:
        """
        Check if a position intersects with a portal.
        Returns the Portal object if found, None otherwise.
        """

    def attempt_move_through_portal(
        self,
        room_id: str,
        position: Tuple[float, float]
    ) -> Optional[str]:
        """
        Attempt to move through a portal.
        Returns the new room_id if successful, None otherwise.
        """

    def get_initial_position(self, room_id: str) -> Tuple[float, float]:
        """Get a default spawn position for a room (center)."""

    # Visibility
    def is_visible(
        self,
        room_id: str,
        pos_a: Tuple[float, float],
        pos_b: Tuple[float, float]
    ) -> bool:
        """
        MVP Visibility Check:
        Returns False if an occlusion exists directly between points.
        (Simplified implementation for Phase 11 MVP)
        """
```

#### Usage Example

```python
from tsukuyomi.environment.physics.spatial_logic import SpatialLogic, Room, Portal

# Initialize spatial logic
logic = SpatialLogic()

# Create rooms
jury_room = Room(
    room_id="jury_room",
    name="Jury Deliberation Room",
    description="A formal room for jury discussions",
    boundaries={'x_min': 0.0, 'x_max': 20.0, 'y_min': 0.0, 'y_max': 20.0},
    occlusions=[(10.0, 10.0, 2.0)]  # Central table
)

hallway = Room(
    room_id="hallway",
    name="Courthouse Hallway",
    boundaries={'x_min': 20.0, 'x_max': 40.0, 'y_min': 0.0, 'y_max': 10.0}
)

# Add rooms
logic.add_room(jury_room)
logic.add_room(hallway)

# Create portal connecting rooms
door = Portal(
    portal_id="jury_door",
    source_room_id="jury_room",
    target_room_id="hallway",
    position=(20.0, 10.0),  # East wall of jury room
    size=2.0
)
logic.add_portal(door)

# Check movement
can_move = logic.can_move_to("jury_room", (5.0, 5.0), radius=0.5)

# Try to move through portal
new_room = logic.attempt_move_through_portal("jury_room", (20.0, 10.0))
# Returns: "hallway"

# Get spawn position
spawn_pos = logic.get_initial_position("jury_room")
# Returns: (10.0, 10.0) - center of room
```

### Raycasting (`physics/raycasting.py`)

**Location:** `tsukuyomi/environment/physics/raycasting.py`

Implements raycasting for line-of-sight and field-of-view calculations.

#### Core Classes

```python
@dataclass
class SensoryProfile:
    """Configuration for an agent's sensory capabilities."""
    vision_range: float = 20.0       # Max vision distance (meters)
    vision_fov: float = 120.0         # Field of view in degrees
    hearing_range: float = 15.0       # Max hearing distance (meters)
    vision_certainty_decay: float = 0.1    # Visual certainty decay per meter
    hearing_certainty_decay: float = 0.15  # Auditory certainty decay per meter

@dataclass
class Wall:
    """Represents a wall or occluding obstacle for raycasting."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    thickness: float = 0.5
    transparent: bool = False
```

#### Raycaster Class

```python
class Raycaster:
    """
    Implements raycasting for line-of-sight and field-of-view calculations.

    Uses Bresenham-like line sampling combined with segment intersection
    for efficient and accurate line-of-sight determination.
    """

    def __init__(self, spatial_index=None)

    def register_room_walls(self, room_id: str, walls: List[Wall]) -> None:
        """Register walls for a specific room."""

    def cast_ray(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        room_id: Optional[str] = None,
        max_distance: Optional[float] = None,
        step_size: float = 0.5,
    ) -> Tuple[bool, Optional[Tuple[float, float]], float]:
        """
        Cast a ray from start to end and check for wall intersections.

        Returns:
            (is_blocked, intersection_point, distance_traveled)
        """

    def cast_cone(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 16,
    ) -> List[Tuple[float, float, float]]:
        """Cast multiple rays in a cone (field of view)."""

    def get_visible_polygon(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 32,
    ) -> List[Tuple[float, float]]:
        """
        Get the visible polygon (shape) of the agent's field of view.
        Returns list of (x, y) vertices forming the visible polygon.
        """

    def is_point_visible(
        self,
        observer_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        room_id: Optional[str] = None,
        step_size: float = 0.5,
    ) -> bool:
        """Check if a target point is visible from observer position."""
```

---

## 6. Rules System

### Affordance Validator (`rules/affordance.py`)

```python
class AffordanceValidator:
    """
    Validates proposals against affordance rules.

    Checks:
    - Preconditions are met
    - Target is valid
    - Actor has required capabilities
    """

    def validate_proposal(
        self,
        proposal: Proposal,
        world_state: WorldState
    ) -> ValidationResult:
        """Validate a proposal against affordance rules."""

    def get_stats(self) -> Dict:
        """Get validation statistics."""
```

### Action Resolver (`rules/action_logic.py`)

```python
class ActionResolver:
    """
    Resolves action proposals into outcomes.

    Handles:
    - Movement actions
    - Interaction actions
    - Collection actions
    - State transitions
    """

    async def resolve_action(
        self,
        proposal: Proposal,
        world_state: WorldState
    ) -> Resolution:
        """Resolve a proposal into an outcome."""
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_engine.py` | EnvironmentEngine tick loop |
| `test_world_builder.py` | WorldBuilder API |
| `test_proposal_window.py` | ProposalWindow, conflict resolution |
| `test_spatial_index.py` | SpatialIndex queries |
| `test_affordance.py` | Affordance validation |

---

## Dependencies

**Internal:**
- `tsukuyomi.transport.proto.core_pb2` - Protocol buffers (TickState, Proposal, etc.)
- `tsukuyomi.transport.proto.common_pb2` - Common types (Vector2, etc.)
- `tsukuyomi.services.database` - Tick persistence
- `tsukuyomi.shared.utils` - Timestamp utilities

**External:**
- `asyncio` - Async operations
- `dataclasses` - Data structures
- `enum` - Enumerations
- `json` - Configuration loading
- `logging` - Logging
- `random` - Deterministic RNG
- `time` - Timing
- `uuid` - ID generation
- `typing` - Type hints

---

## Design Principles

1. **Deterministic**: Seeded RNG ensures reproducible simulations
2. **Phase-Based**: Clear tick phases (Broadcast → Window → Resolution)
3. **Conflict Resolution**: Multiple strategies for handling competing proposals
4. **Spatial Efficiency**: Grid-based indexing for 50+ agents
5. **Affordance-Based**: Actions validated against world rules
6. **Scenario Agnostic**: WorldBuilder API for flexible world definition
