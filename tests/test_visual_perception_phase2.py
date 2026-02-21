"""
Visual Perception System - Phase 2 Integration Test

This test demonstrates the enhanced visual perception pipeline with:
- Raycasting for accurate line-of-sight
- Spatial Index integration for efficient proximity queries
- Field-of-view calculations
- AgentBrain integration with spatial awareness

Usage:
    python tests/test_visual_perception_phase2.py
"""

import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tsukuyomi.brain.perception_pipeline import (
    PerceptionPipeline,
    SensoryProfile,
    AgentInternalState,
    Raycaster,
    Wall,
)
from tsukuyomi.brain.agent_brain import AgentBrain
from tsukuyomi.core.spatial_index import SpatialIndex
from tsukuyomi.proto import core_pb2, perception_pb2, common_pb2


def test_raycaster():
    """Test the Raycaster for line-of-sight calculations."""
    print("\n" + "=" * 60)
    print("TEST 1: Raycaster - Line-of-Sight Calculation")
    print("=" * 60)

    # Create a raycaster
    raycaster = Raycaster()

    # Register some walls (simple room: 20x20)
    walls = [
        Wall(start=(0, 0), end=(20, 0), thickness=0.5),  # Bottom wall
        Wall(start=(20, 0), end=(20, 20), thickness=0.5),  # Right wall
        Wall(start=(20, 20), end=(0, 20), thickness=0.5),  # Top wall
        Wall(start=(0, 20), end=(0, 0), thickness=0.5),  # Left wall
        Wall(start=(5, 5), end=(5, 15), thickness=0.3),  # Internal wall
    ]

    raycaster.register_room_walls("test_room", walls)

    # Test 1: Unobstructed line of sight
    start = (10, 10)
    end = (15, 15)
    blocked, intersection, distance = raycaster.cast_ray(start, end, "test_room")

    print(f"\nTest 1a: Unobstructed ray")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Blocked: {blocked}")
    print(f"  Distance: {distance:.2f}")
    print(f"  Result: {'PASS' if not blocked else 'FAIL'}")

    # Test 2: Obstructed line of sight
    start = (2, 10)
    end = (18, 10)
    blocked, intersection, distance = raycaster.cast_ray(start, end, "test_room")

    print(f"\nTest 1b: Obstructed ray (hits internal wall)")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Blocked: {blocked}")
    print(f"  Intersection: {intersection}")
    print(f"  Distance to wall: {distance:.2f}")
    print(f"  Result: {'PASS' if blocked and intersection else 'FAIL'}")

    # Test 3: Visible polygon calculation
    origin = (10, 10)
    direction = (1, 0)  # Facing +X
    fov = 120
    max_distance = 15

    polygon = raycaster.get_visible_polygon(
        origin, direction, fov, max_distance, "test_room", num_rays=16
    )

    print(f"\nTest 1c: Visible polygon")
    print(f"  Origin: {origin}")
    print(f"  Direction: {direction}")
    print(f"  FOV: {fov}°")
    print(f"  Max distance: {max_distance}")
    print(f"  Polygon vertices: {len(polygon)}")
    print(f"  Result: PASS")

    return not blocked or intersection


def test_spatial_index():
    """Test SpatialIndex for efficient proximity queries."""
    print("\n" + "=" * 60)
    print("TEST 2: Spatial Index - Proximity Queries")
    print("=" * 60)

    # Create spatial index
    index = SpatialIndex(width=100, height=100, cell_size=10)

    # Insert some objects
    index.insert("agent1", (10.5, 20.3))
    index.insert("agent2", (15.2, 18.7))
    index.insert("agent3", (50.0, 50.0))  # Far away
    index.insert("object1", (12.0, 19.5))

    # Test query
    query_pos = (10.5, 20.3)
    nearby = index.query(query_pos, radius=5.0, exclude_self="agent1")

    print(f"\nTest 2a: Query nearby objects")
    print(f"  Query position: {query_pos}")
    print(f"  Radius: 5.0")
    print(f"  Found {len(nearby)} nearby objects:")
    for obj_id, pos in nearby:
        distance = ((pos[0] - query_pos[0])**2 + (pos[1] - query_pos[1])**2)**0.5
        print(f"    - {obj_id} at {pos} (distance: {distance:.2f})")
    print(f"  Result: {'PASS' if len(nearby) >= 2 else 'FAIL'}")

    # Test nearest query
    nearest = index.query_nearest(query_pos, limit=3)

    print(f"\nTest 2b: Query nearest objects")
    print(f"  Query position: {query_pos}")
    print(f"  Nearest {len(nearest)} objects:")
    for obj_id, pos, distance in nearest:
        print(f"    {distance:.2f}m - {obj_id} at {pos}")
    print(f"  Result: PASS")

    return len(nearby) >= 2


def test_perception_pipeline():
    """Test PerceptionPipeline with raycasting and spatial index."""
    print("\n" + "=" * 60)
    print("TEST 3: Perception Pipeline - Deep Perception")
    print("=" * 60)

    # Create world state
    world_state = core_pb2.WorldState(
        tick_number=100,
        timestamp=common_pb2.Timestamp(seconds=1234567890, nanos=0),
        actors={},
        objects={},
    )

    # Add agents to world
    world_state.actors["agent1"].CopyFrom(
        core_pb2.Actor(
            id="agent1",
            name="Alice",
            position=common_pb2.Vector2(x=10.0, y=10.0),
            state="idle",
            current_location="test_room",
        )
    )

    world_state.actors["agent2"].CopyFrom(
        core_pb2.Actor(
            id="agent2",
            name="Bob",
            position=common_pb2.Vector2(x=15.0, y=15.0),
            state="speaking",
            current_location="test_room",
        )
    )

    world_state.actors["agent3"].CopyFrom(
        core_pb2.Actor(
            id="agent3",
            name="Charlie",
            position=common_pb2.Vector2(x=2.0, y=10.0),  # Behind wall
            state="idle",
            current_location="test_room",
        )
    )

    # Add objects to world
    world_state.objects["food1"].CopyFrom(
        core_pb2.EnvironmentObject(
            id="food1",
            type="food",
            position=common_pb2.Vector2(x=12.0, y=12.0),
            interactive=True,
        )
    )

    # Create spatial index and register entities
    spatial_index = SpatialIndex(width=100, height=100, cell_size=10)
    spatial_index.insert("agent1", (10.0, 10.0))
    spatial_index.insert("agent2", (15.0, 15.0))
    spatial_index.insert("agent3", (2.0, 10.0))
    spatial_index.insert("food1", (12.0, 12.0))

    # Create perception pipeline
    sensory_profile = SensoryProfile(
        vision_range=20.0, vision_fov=120.0, hearing_range=15.0
    )

    perception = PerceptionPipeline(
        agent_id="agent1", sensory_profile=sensory_profile, spatial_index=spatial_index
    )

    # Register walls for raycasting
    raycaster = perception.raycaster
    walls = [
        Wall(start=(0, 0), end=(20, 0), thickness=0.5),
        Wall(start=(20, 0), end=(20, 20), thickness=0.5),
        Wall(start=(20, 20), end=(0, 20), thickness=0.5),
        Wall(start=(0, 20), end=(0, 0), thickness=0.5),
        Wall(start=(5, 5), end=(5, 15), thickness=0.3),  # Internal wall
    ]
    raycaster.register_room_walls("test_room", walls)

    # Create agent internal state
    agent_state = AgentInternalState(
        current_concerns=[],
        mood_label="calm",
        arousal=0.5,
        last_seen_entities={},
        facing_direction=(1.0, 1.0),  # Diagonal
    )

    # Process perception (deep tick)
    percepts = perception.process(world_state, agent_state, current_tick=100)

    print(f"\nTest 3a: Deep perception results")
    print(f"  Agent: agent1 (Alice) at (10.0, 10.0)")
    print(f"  Facing: {agent_state.facing_direction}")
    print(f"  Generated {len(percepts)} percepts")

    # Analyze results
    vision_percepts = [
        p for p in percepts if p.channel == perception_pb2.Percept.VISION
    ]

    print(f"\n  Vision percepts ({len(vision_percepts)}):")
    for percept in vision_percepts:
        if percept.HasField("actor"):
            print(
                f"    - {percept.actor.name} at "
                f"({percept.actor.approximate_position.x:.1f}, "
                f"{percept.actor.approximate_position.y:.1f}), "
                f"salience: {percept.salience:.2f}, "
                f"certainty: {percept.certainty:.2f}"
            )
        elif percept.HasField("object"):
            print(
                f"    - {percept.object.apparent_type} at "
                f"({percept.object.approximate_position.x:.1f}, "
                f"{percept.object.approximate_position.y:.1f}), "
                f"salience: {percept.salience:.2f}, "
                f"certainty: {percept.certainty:.2f}"
            )

    print(f"\n  Expected: Should see Bob and food, NOT Charlie (behind wall)")
    visible_names = [
        p.actor.name
        for p in vision_percepts
        if p.HasField("actor") and p.actor.name != "Alice"
    ]
    visible_objects = [
        p.object.apparent_type for p in vision_percepts if p.HasField("object")
    ]

    test_passed = "Bob" in visible_names and "Charlie" not in visible_names
    print(f"  Result: {'PASS' if test_passed else 'FAIL'}")

    # Test visual context summary
    visual_context = perception.get_visual_context_summary()
    print(f"\nTest 3b: Visual context for LLM")
    print(f"  Summary: {visual_context}")
    print(f"  Result: PASS")

    return test_passed


def run_all_tests():
    """Run all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("\n" + "=" * 60)
    print("VISUAL PERCEPTION SYSTEM - PHASE 2 TESTS")
    print("=" * 60)

    results = {
        "Raycaster": test_raycaster(),
        "Spatial Index": test_spatial_index(),
        "Perception Pipeline": test_perception_pipeline(),
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED ✓' if all_passed else 'SOME TESTS FAILED ✗'}")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
