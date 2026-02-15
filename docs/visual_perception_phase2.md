# Visual Perception System - Phase 2 Implementation

## Overview

The Visual Perception System for Tsukuyomi V2 Phase 2 provides agents with realistic visual awareness through:

1. **Raycasting** - Accurate line-of-sight detection
2. **Field-of-View (FOV)** - Cone-based visual perception
3. **Spatial Index Integration** - Efficient proximity queries (O(1) average)
4. **Memory Echoes** - Tracking last-known positions
5. **Surprise Factor** - Boosted salience for unexpected events

## Architecture

### Core Components

```
PerceptionPipeline
├── Raycaster
│   ├── cast_ray() - Single ray line-of-sight
│   ├── cast_cone() - Multiple rays in FOV
│   └── get_visible_polygon() - Calculate visible shape
├── SpatialIndex (integration)
└── MemoryEcho tracking

AgentBrain
├── set_spatial_index() - Connect to spatial partitioning
├── set_spatial_logic() - Connect to room/portal system
└── get_visual_context_for_llm() - Export visual context

LLMService
└── Enhanced prompt templates with visual context
```

## Key Features

### 1. Raycasting

The `Raycaster` class implements accurate line-of-sight using Bresenham-like ray marching with segment intersection:

```python
from tsukuyomi.brain.PerceptionPipeline import Raycaster, Wall

# Create raycaster
raycaster = Raycaster()

# Register walls for a room
walls = [
    Wall(start=(0, 0), end=(20, 0), thickness=0.5),
    Wall(start=(20, 0), end=(20, 20), thickness=0.5),
    Wall(start=(20, 20), end=(0, 20), thickness=0.5),
    Wall(start=(0, 20), end=(0, 0), thickness=0.5),
]
raycaster.register_room_walls("main_hall", walls)

# Cast a ray
blocked, intersection, distance = raycaster.cast_ray(
    start=(5, 5),
    end=(15, 15),
    room_id="main_hall"
)

print(f"Blocked: {blocked}")
print(f"Intersection: {intersection}")
print(f"Distance: {distance:.2f}m")
```

**Features:**
- Line segment intersection with walls
- Configurable step size for ray marching
- Room-aware wall checking
- Optional max distance capping

### 2. Field-of-View (FOV) Calculation

Agents only see objects within their visual cone:

```python
# Get visible polygon for visualization
polygon = raycaster.get_visible_polygon(
    origin=(10, 10),        # Agent position
    direction=(1, 0),       # Facing direction
    fov_degrees=120,        # Field of view
    max_distance=20,        # Vision range
    room_id="main_hall",
    num_rays=32             # Polygon resolution
)

# Check if point is in FOV
from tsukuyomi.brain.PerceptionPipeline import PerceptionPipeline

perception = PerceptionPipeline(agent_id="agent1", sensory_profile=profile)

in_fov = perception._in_vision_cone(
    my_pos=(10, 10),
    target_pos=(15, 15),
    facing=(1, 0)  # Normalized direction vector
)
```

**Features:**
- Configurable FOV angle (default: 120°)
- Configurable vision range (default: 20m)
- Accurate cone calculation using atan2
- Handles angle wraparound (359° vs 1°)

### 3. Spatial Index Integration

Efficient O(1) proximity queries using grid-based spatial partitioning:

```python
from tsukuyomi.core.spatial_index import SpatialIndex

# Create spatial index
index = SpatialIndex(width=100, height=100, cell_size=10)

# Insert entities
index.insert("agent1", (10.5, 20.3))
index.insert("agent2", (15.2, 18.7))
index.insert("food1", (12.0, 19.5))

# Query nearby objects
nearby = index.query(
    position=(10.5, 20.3),
    radius=5.0,
    exclude_self="agent1"
)

# Query nearest objects
nearest = index.query_nearest(
    position=(10.5, 20.3),
    limit=3
)

# Update position
index.update_position("agent1", (15.0, 25.0))
```

**Performance:**
- Insert: O(1)
- Query: O(k) where k = cells within radius
- Update: O(1)

### 4. Perception Pipeline Integration

The PerceptionPipeline integrates all visual awareness components:

```python
from tsukuyomi.brain.PerceptionPipeline import (
    PerceptionPipeline,
    SensoryProfile,
    AgentInternalState
)

# Create sensory profile
sensory_profile = SensoryProfile(
    vision_range=20.0,
    vision_fov=120.0,
    hearing_range=15.0,
    vision_certainty_decay=0.1,
    hearing_certainty_decay=0.15
)

# Create perception pipeline
perception = PerceptionPipeline(
    agent_id="agent1",
    sensory_profile=sensory_profile,
    spatial_index=spatial_index,  # Optional
    spatial_logic=spatial_logic   # Optional
)

# Process world state
agent_state = AgentInternalState(
    current_concerns=["trial"],
    mood_label="anxious",
    arousal=0.7,
    last_seen_entities={},
    facing_direction=(1.0, 0.5)  # Normalized direction
)

percepts = perception.process(
    world_state=world_state,
    agent_internal_state=agent_state,
    current_tick=100
)

# Filter by channel
vision_percepts = [p for p in percepts if p.channel == perception_pb2.Percept.VISION]
```

**Staggered Perception Schedule:**
- Every tick: Proximity heartbeat (lightweight)
- Every N ticks (default: 3): Deep perception (full FOV + occlusion)
- Prevents O(A²) bottleneck while maintaining awareness

### 5. AgentBrain Integration

AgentBrain integrates with spatial systems for full spatial awareness:

```python
from tsukuyomi.brain.AgentBrain import AgentBrain

# Create agent brain
brain = AgentBrain(
    actor_id="agent1",
    profile=agent_profile,
    server_addr="localhost:50051"
)

# Connect to spatial systems
brain.set_spatial_index(spatial_index)
brain.set_spatial_logic(spatial_logic)

# The brain automatically:
# - Updates agent position in spatial index each tick
# - Calculates facing direction from state
# - Passes visual context to LLM for decisions
```

### 6. LLM Prompt Enhancement

Visual context is integrated into LLM prompt templates:

```python
# Visual context is automatically included in deliberation prompts
# Template includes:
#
# VISUAL PERCEPTION:
# Nearby: Alice (state: speaking) | Bob (state: idle)
# Visible objects: food, chair
#
# The LLM uses this to make spatially-grounded decisions
```

## Configuration

### Sensory Profile

```python
SensoryProfile(
    vision_range=20.0,           # Max vision distance (meters)
    vision_fov=120.0,            # Field of view in degrees
    hearing_range=15.0,          # Max hearing distance (meters)
    vision_certainty_decay=0.1,   # Certainty decay per meter
    hearing_certainty_decay=0.15  # Certainty decay per meter
)
```

### Perception Pipeline Configuration

```python
# In PerceptionPipeline class:
DEEP_PERCEPTION_INTERVAL = 3     # Deep perception every N ticks
ECHO_DECAY_TICKS = 100           # How long memory echoes last
ECHO_DECAY_RATE = 0.01           # Per-tick decay for echoes
```

### Spatial Index Configuration

```python
# Cell size: Smaller = more precision, higher memory
# 10m cells = 100x100 world = 100 cells (good for 50m scale)
# 5m cells = 100x100 world = 400 cells (more precise, 4x memory)

index = SpatialIndex(
    width=100,      # World width (meters)
    height=100,     # World height (meters)
    cell_size=10    # Grid cell size (meters)
)
```

## Usage Examples

### Example 1: Basic Agent with Visual Perception

```python
import asyncio
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.core.spatial_index import SpatialIndex

# Create spatial index
spatial_index = SpatialIndex(width=100, height=100, cell_size=10)

# Create agent
brain = AgentBrain(
    actor_id="agent1",
    profile={
        "name": "Alice",
        "backstory": "A curious explorer",
        "sensory_profile": {
            "vision_range": 25.0,
            "vision_fov": 90.0
        }
    }
)

# Connect spatial systems
brain.set_spatial_index(spatial_index)

# Run agent
asyncio.run(brain.run())
```

### Example 2: Custom Room with Walls

```python
from tsukuyomi.brain.PerceptionPipeline import Wall

# Define room boundaries and occlusions
walls = [
    # Room boundaries
    Wall(start=(0, 0), end=(20, 0), thickness=0.5),
    Wall(start=(20, 0), end=(20, 20), thickness=0.5),
    Wall(start=(20, 20), end=(0, 20), thickness=0.5),
    Wall(start=(0, 20), end=(0, 0), thickness=0.5),

    # Internal obstacles
    Wall(start=(5, 5), end=(5, 15), thickness=0.3),  # Pillar
    Wall(start=(10, 8), end=(15, 8), thickness=0.3),  # Low wall
]

# Register with raycaster
brain.perception.raycaster.register_room_walls("tavern", walls)
```

### Example 3: Testing Line-of-Sight

```python
from tsukuyomi.brain.PerceptionPipeline import Raycaster

raycaster = Raycaster()

# Check if agent can see target
visible = raycaster.is_point_visible(
    observer_pos=(10, 10),
    target_pos=(15, 15),
    room_id="main_hall"
)

if visible:
    print("Target is visible!")
else:
    print("Target is blocked by walls")
```

### Example 4: Getting Visual Context for LLM

```python
# In AgentBrain or directly from PerceptionPipeline
visual_context = brain.perception.get_visual_context_summary()

# Returns something like:
# "Nearby: Alice (state: speaking), Bob (state: idle) |
#  Visible objects: food, chair, table"

# This is automatically included in LLM prompts
```

## Performance Considerations

### Raycasting Performance

- **Step size:** Larger steps = faster but less accurate (default: 0.5m)
- **Max distance:** Limits ray length for early termination
- **Room filtering:** Only checks walls in specific room

```python
# Faster, less accurate
blocked, _, _ = raycaster.cast_ray(start, end, step_size=1.0)

# Slower, more accurate
blocked, _, _ = raycaster.cast_ray(start, end, step_size=0.1)
```

### Spatial Index Performance

- **Cell size:** Balance precision vs memory
- **Grid utilization:** Monitor with `index.get_stats()`

```python
stats = index.get_stats()
print(f"Utilization: {stats['utilization']*100:.1f}%")
print(f"Avg cell load: {stats['avg_cell_load']:.1f}")
```

### Staggered Perception

- Reduces CPU usage by ~66% (deep every 3 ticks)
- Maintains situational awareness via proximity heartbeat
- Configurable via `DEEP_PERCEPTION_INTERVAL`

## Testing

Run the test suite:

```bash
cd /root/.openclaw/workspace/tsukuyomi
source venv/bin/activate

# Run simple tests
python tests/test_visual_perception_simple.py

# Run integration tests
python tests/test_visual_perception_phase2.py
```

## API Reference

### Raycaster

```python
class Raycaster:
    def __init__(self, spatial_index=None)
    def register_room_walls(self, room_id: str, walls: List[Wall]) -> None
    def cast_ray(self, start, end, room_id=None, max_distance=None, step_size=0.5)
        -> Tuple[bool, Optional[Tuple[float, float]], float]
    def cast_cone(self, origin, direction, fov_degrees, max_distance, room_id=None, num_rays=16)
        -> List[Tuple[float, float, float]]
    def get_visible_polygon(self, origin, direction, fov_degrees, max_distance, room_id=None, num_rays=32)
        -> List[Tuple[float, float]]
    def is_point_visible(self, observer_pos, target_pos, room_id=None, step_size=0.5) -> bool
```

### PerceptionPipeline

```python
class PerceptionPipeline:
    def __init__(self, agent_id, sensory_profile, spatial_index=None, spatial_logic=None)
    def set_spatial_index(self, spatial_index) -> None
    def set_spatial_logic(self, spatial_logic) -> None
    def process(self, world_state, agent_internal_state, current_tick)
        -> List[perception_pb2.Percept]
    def get_visual_context_summary(self) -> str
```

### AgentBrain

```python
class AgentBrain:
    def set_spatial_index(self, spatial_index) -> None
    def set_spatial_logic(self, spatial_logic) -> None
    def get_visual_context_for_llm(self) -> str
```

## Design Decisions

### Why Raycasting Instead of Bounding Boxes?

- **Accuracy:** Exact line-of-sight rather than approximation
- **Transparency:** Can support partial transparency later
- **Flexibility:** Works with arbitrary wall shapes

### Why Staggered Perception?

- **Performance:** Reduces O(A²) complexity
- **Consistency:** Predictable tick pattern
- **Balance:** Deep perception without CPU overload

### Why Grid-Based Spatial Index?

- **Simplicity:** Easy to implement and debug
- **Performance:** O(1) average case
- **Scalability:** Can upgrade to Quadtree if needed

## Future Enhancements

1. **Partial Transparency:** Walls with transparency percentages
2. **Dynamic Lighting:** Vision affected by light sources
3. **Peripheral Vision:** Different precision in FOV edges
4. **Vision Persistence:** Brief "afterimage" of vanished entities
5. **Quadtree Upgrade:** For larger worlds (>1000x1000)

## Troubleshooting

### Issue: Agents see through walls

**Solution:** Ensure walls are registered with the raycaster:

```python
perception.raycaster.register_room_walls(room_id, walls)
```

### Issue: Poor performance with many agents

**Solution:** Increase staggered perception interval:

```python
PerceptionPipeline.DEEP_PERCEPTION_INTERVAL = 5  # Instead of 3
```

### Issue: Spatial index queries are slow

**Solution:** Increase cell size for coarser partitioning:

```python
index = SpatialIndex(width=100, height=100, cell_size=20)  # Instead of 10
```

## Credits

- **Phase 2 Implementation:** Agent Brain Engineer
- **Design Philosophy:** "General Engine" - Generic, reusable perception system
- **Inspiration:** Game AI techniques (raycasting, spatial partitioning)
