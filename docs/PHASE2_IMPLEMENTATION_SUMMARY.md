# Tsukuyomi V2 Phase 2 - Visual Perception Implementation Summary

## Overview

Successfully implemented the Visual Perception pipeline for Tsukuyomi V2 Phase 2 (World Dynamics), providing agents with realistic spatial awareness through raycasting, field-of-view detection, and efficient spatial indexing.

## What Was Implemented

### 1. Enhanced PerceptionPipeline (`/tsukuyomi/brain/PerceptionPipeline.py`)

**New Raycaster Class:**
- `cast_ray()` - Single ray line-of-sight detection with wall intersection
- `cast_cone()` - Multiple rays in FOV cone for visibility polygon
- `get_visible_polygon()` - Returns visible area vertices for visualization
- `is_point_visible()` - Quick check if target is visible from observer
- `_line_intersection()` - Accurate line segment intersection algorithm

**Features:**
- Line-of-sight blocking by walls and obstacles
- Accurate FOV cone calculation using atan2
- Room-aware wall checking
- Configurable ray marching step size
- Integration with SpatialIndex for efficient queries

**Enhanced Perception Methods:**
- `_process_vision_deep()` - Full FOV + occlusion + raycasting
- `_process_vision_proximity()` - Lightweight proximity heartbeat
- Spatial index integration for O(1) proximity queries
- Memory echo tracking with surprise factor

**Key Methods Added:**
```python
set_spatial_index(spatial_index)  # Connect to spatial partitioning
set_spatial_logic(spatial_logic)  # Connect to room/portal system
get_visual_context_summary()      # Export visual context for LLM
```

### 2. Enhanced AgentBrain (`/tsukuyomi/brain/AgentBrain.py`)

**New Spatial Integration:**
- `set_spatial_index(spatial_index)` - Connect agent to spatial index
- `set_spatial_logic(spatial_logic)` - Connect agent to room/portal system
- `_calculate_facing_direction(actor)` - Infer facing direction from state
- `get_visual_context_for_llm()` - Get visual context summary

**Enhanced Tick Processing:**
- Updates agent position in spatial index each tick
- Calculates facing direction from agent state
- Passes visual context to LLM for grounded decision-making

**Integration Points:**
```python
# During agent initialization
brain.set_spatial_index(spatial_index)
brain.set_spatial_logic(spatial_logic)

# Automatic during tick processing
# - Position updated in spatial index
# - Facing direction calculated
# - Visual context passed to LLM
```

### 3. Enhanced LLMService (`/tsukuyomi/brain/LLMService.py`)

**Updated Prompt Templates:**
- Added visual context section to deliberation template
- LLM now receives information about what agent can see
- Visual context includes: nearby actors, visible objects, obstacles

**Template Changes:**
```python
# Before:
TASK: Based on your needs, beliefs... decide your next action.

# After:
VISUAL PERCEPTION:
Nearby: Alice (state: speaking), Bob (state: idle)
Visible objects: food, chair

TASK: Based on your needs, visual perception, beliefs... decide your next action.
```

**Updated Method Signatures:**
```python
async def generate_plan_v2(
    profile, working_memory, beliefs, relationships,
    emotional_modifier, needs_context,
    visual_context,  # NEW: Visual perception data
    reason="scheduled"
) -> Dict
```

### 4. Spatial Index Integration

**Leverages Existing SpatialIndex:**
- Grid-based spatial partitioning (O(1) average queries)
- Efficient proximity detection
- Automatic position tracking for all agents

**Usage Pattern:**
```python
# Create spatial index
index = SpatialIndex(width=100, height=100, cell_size=10)

# Register agents
index.insert("agent1", (10.5, 20.3))

# Query nearby
nearby = index.query((10.5, 20.3), radius=5.0)
```

### 5. Test Suite

**Created Comprehensive Tests:**
- `test_visual_perception_simple.py` - Basic functionality tests
  - Raycasting line-of-sight
  - Field-of-view detection
  - Memory echo tracking

- `test_visual_perception_phase2.py` - Integration tests
  - Full perception pipeline
  - Spatial index integration
  - Visual context generation

**Test Results:**
- ✓ Raycasting - All tests pass
- ✓ Spatial Index - All tests pass
- ✓ Field-of-View - All tests pass
- ✓ Memory Echoes - All tests pass

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentBrain                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  set_spatial_index()  │  set_spatial_logic()        │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PerceptionPipeline                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  Raycaster  │  │SpatialIndex │ │MemoryEchoes │   │   │
│  │  │             │  │Integration  │ │             │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  │                                                             │
│  │  - Vision Deep (raycasting + FOV + occlusion)            │
│  │  - Vision Proximity (lightweight heartbeat)               │
│  │  - Hearing (omnidirectional)                              │
│  │  - Proprioception (self-awareness)                       │
│  │  - Memory Echoes (last-known positions)                  │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│              get_visual_context_summary()                    │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  LLMService                            │   │
│  │  ┌─────────────────────────────────────────────────┐ │   │
│  │  │  Enhanced Prompt Template with Visual Context   │ │   │
│  │  └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Accurate Raycasting
- Line segment intersection algorithm
- Configurable step size for precision vs performance
- Room-aware wall checking
- Support for transparent walls (future)

### 2. Field-of-View (FOV)
- Configurable FOV angle (default: 120°)
- Accurate cone calculation using atan2
- Handles angle wraparound
- Distance-based certainty decay

### 3. Spatial Index Integration
- O(1) average case proximity queries
- Automatic position tracking
- Efficient for large numbers of entities
- Reduces O(A²) complexity

### 4. Staggered Perception Schedule
- Every tick: Proximity heartbeat (lightweight)
- Every N ticks: Deep perception (full FOV + occlusion)
- Configurable interval (default: 3 ticks)
- Reduces CPU usage by ~66%

### 5. Memory Echoes & Surprise Factor
- Track last-known positions
- Decay over time
- Boost salience for unexpected events
- Teleportation detection

### 6. LLM Integration
- Visual context in prompts
- Grounded spatial decision-making
- Awareness of nearby entities
- Obstacle information

## Performance Characteristics

### Raycasting
- **Complexity:** O(distance / step_size * num_walls)
- **Optimization:** Room filtering limits walls checked
- **Configurable:** Step size balances speed vs accuracy

### Spatial Index
- **Insert:** O(1)
- **Query:** O(k) where k = cells within radius
- **Update:** O(1)
- **Memory:** O(grid_width * grid_height)

### Perception Pipeline
- **Proximity Tick:** O(query_complexity)
- **Deep Tick:** O(rays_in_cone * raycast_complexity)
- **Staggered:** Deep every 3 ticks = ~33% of ticks

## Usage Guide

### Basic Setup

```python
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
            "vision_range": 20.0,
            "vision_fov": 120.0
        }
    }
)

# Connect spatial systems
brain.set_spatial_index(spatial_index)
brain.set_spatial_logic(spatial_logic)

# Run
asyncio.run(brain.run())
```

### Custom Room with Walls

```python
from tsukuyomi.brain.PerceptionPipeline import Wall

# Define walls
walls = [
    Wall(start=(0, 0), end=(20, 0), thickness=0.5),
    Wall(start=(20, 0), end=(20, 20), thickness=0.5),
    Wall(start=(20, 20), end=(0, 20), thickness=0.5),
    Wall(start=(0, 20), end=(0, 0), thickness=0.5),
    Wall(start=(5, 5), end=(5, 15), thickness=0.3),  # Pillar
]

# Register with agent's raycaster
brain.perception.raycaster.register_room_walls("tavern", walls)
```

### Testing Line-of-Sight

```python
# Check visibility
visible = brain.perception.raycaster.is_point_visible(
    observer_pos=(10, 10),
    target_pos=(15, 15),
    room_id="tavern"
)
```

## Testing

### Run Tests

```bash
cd /root/.openclaw/workspace/tsukuyomi
source venv/bin/activate

# Basic tests
python tests/test_visual_perception_simple.py

# Integration tests
python tests/test_visual_perception_phase2.py
```

### Test Coverage

- ✓ Raycasting line-of-sight
- ✓ Field-of-view detection
- ✓ Spatial index queries
- ✓ Memory echo tracking
- ✓ Surprise factor calculation
- ✓ Visual context generation

## Files Modified

1. `/tsukuyomi/brain/PerceptionPipeline.py` - Enhanced with Raycaster and spatial integration
2. `/tsukuyomi/brain/AgentBrain.py` - Added spatial index/logic integration
3. `/tsukuyomi/brain/LLMService.py` - Updated prompt templates with visual context
4. `/tsukuyomi/tests/test_visual_perception_simple.py` - New test file (basic)
5. `/tsukuyomi/tests/test_visual_perception_phase2.py` - New test file (integration)
6. `/tsukuyomi/docs/visual_perception_phase2.md` - Comprehensive documentation

## Configuration Options

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

### Perception Pipeline
```python
PerceptionPipeline.DEEP_PERCEPTION_INTERVAL = 3  # Deep every N ticks
PerceptionPipeline.ECHO_DECAY_TICKS = 100          # Echo lifetime
PerceptionPipeline.ECHO_DECAY_RATE = 0.01          # Per-tick decay
```

### Spatial Index
```python
SpatialIndex(
    width=100,      # World width (meters)
    height=100,     # World height (meters)
    cell_size=10    # Grid cell size (meters)
)
```

## Design Decisions

1. **Raycasting over Bounding Boxes:** More accurate line-of-sight, supports transparency
2. **Staggered Perception:** Reduces CPU usage while maintaining awareness
3. **Grid-Based Spatial Index:** Simple, fast O(1), upgradeable to Quadtree
4. **Separate Raycaster Class:** Reusable across different systems
5. **Visual Context in LLM:** Grounds decisions in spatial reality

## Future Enhancements

1. Partial transparency for walls
2. Dynamic lighting system
3. Peripheral vision effects
4. Vision persistence (afterimages)
5. Quadtree upgrade for larger worlds
6. 3D raycasting support

## Troubleshooting

**Issue:** Agents see through walls
**Solution:** Ensure walls are registered:
```python
perception.raycaster.register_room_walls(room_id, walls)
```

**Issue:** Poor performance
**Solution:** Increase staggered interval:
```python
PerceptionPipeline.DEEP_PERCEPTION_INTERVAL = 5
```

**Issue:** Queries are slow
**Solution:** Increase cell size:
```python
index = SpatialIndex(width=100, height=100, cell_size=20)
```

## Compliance with Requirements

✅ **Raycasting:** Agents can only see objects in their field of view
✅ **Line-of-Sight:** Walls and obstacles block vision
✅ **Performance:** Perception does not block the main tick loop (staggered schedule)
✅ **Spatial Awareness:** Enhanced AgentBrain to use spatial awareness
✅ **LLM Integration:** Updated prompt templates for visual context
✅ **SpatialIndex:** Integrated for proximity detection

## Conclusion

The Visual Perception pipeline is now fully implemented and tested. Agents have realistic spatial awareness through accurate raycasting, efficient proximity queries, and memory-based tracking of last-known positions. The system is performant, extensible, and well-integrated with the existing Tsukuyomi architecture.

---

**Implementation Date:** 2026-02-15
**Phase:** Tsukuyomi V2 Phase 2 (World Dynamics)
**Implemented By:** Agent Brain Engineer
**Status:** ✓ Complete and Tested
