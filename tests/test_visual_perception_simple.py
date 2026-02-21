"""
Simple Visual Perception Test - Phase 2

Basic test to verify raycasting and spatial integration works.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tsukuyomi.brain.perception_pipeline import (
    PerceptionPipeline,
    SensoryProfile,
    AgentInternalState,
    Raycaster,
    Wall,
)
from tsukuyomi.proto import core_pb2, perception_pb2, common_pb2


def test_basic_raycasting():
    """Test basic raycasting functionality."""
    print("\n" + "=" * 60)
    print("TEST: Basic Raycasting")
    print("=" * 60)

    raycaster = Raycaster()

    # Add a wall
    walls = [
        Wall(start=(5, 0), end=(5, 20), thickness=0.5),
    ]
    raycaster.register_room_walls("room1", walls)

    # Test 1: Unobstructed
    blocked, _, _ = raycaster.cast_ray((0, 10), (4, 10), "room1")
    print(f"Unobstructed ray (0,10) -> (4,10): Blocked={blocked}")
    assert not blocked, "Unobstructed ray should not be blocked"

    # Test 2: Obstructed
    blocked, intersection, _ = raycaster.cast_ray((0, 10), (10, 10), "room1")
    print(f"Obstructed ray (0,10) -> (10,10): Blocked={blocked}, Intersection={intersection}")
    assert blocked, "Ray hitting wall should be blocked"
    assert intersection is not None, "Should have intersection point"

    print("✓ All raycasting tests passed")
    return True


def test_fov_detection():
    """Test field-of-view detection."""
    print("\n" + "=" * 60)
    print("TEST: Field-of-View Detection")
    print("=" * 60)

    # Create perception pipeline
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=90.0,  # 90 degree FOV
        hearing_range=15.0
    )

    perception = PerceptionPipeline(
        agent_id="agent1",
        sensory_profile=sensory_profile,
        spatial_index=None
    )

    # Test FOV calculation
    my_pos = (10.0, 10.0)
    facing = (1.0, 0.0)  # Facing +X

    # Test positions
    positions = {
        "front": (15.0, 10.0),    # In FOV
        "front_left": (15.0, 5.0),  # In FOV
        "behind": (5.0, 10.0),    # Behind
        "side": (10.0, 15.0),     # Outside FOV
    }

    for name, pos in positions.items():
        in_fov = perception._in_vision_cone(my_pos, pos, facing)
        distance = perception._distance(my_pos, pos)
        print(f"  {name:12s} at ({pos[0]:5.1f}, {pos[1]:5.1f}) distance={distance:5.1f}m FOV={in_fov}")

    # Check that front positions are in FOV
    front_in_fov = perception._in_vision_cone(my_pos, positions["front"], facing)
    assert front_in_fov, "Front position should be in FOV"

    # Check that behind position is not in FOV
    behind_in_fov = perception._in_vision_cone(my_pos, positions["behind"], facing)
    assert not behind_in_fov, "Behind position should not be in FOV"

    print("✓ All FOV tests passed")
    return True


def test_memory_echoes():
    """Test memory echo tracking."""
    print("\n" + "=" * 60)
    print("TEST: Memory Echo Tracking")
    print("=" * 60)

    sensory_profile = SensoryProfile()
    perception = PerceptionPipeline(
        agent_id="agent1",
        sensory_profile=sensory_profile
    )

    # Simulate seeing an actor
    tick = 100
    entity_id = "actor_bob"
    position = common_pb2.Vector2(x=10.0, y=15.0)

    perception._update_memory_echo(entity_id, "actor", position, tick)

    # Check echo exists
    assert entity_id in perception.memory_echoes, "Memory echo should be created"
    echo = perception.memory_echoes[entity_id]
    assert echo.last_position.x == 10.0, "Position should be recorded"
    assert echo.current_certainty == 1.0, "Certainty should start at 1.0"

    print(f"  Created memory echo for {entity_id}")
    print(f"  Position: ({echo.last_position.x}, {echo.last_position.y})")
    print(f"  Certainty: {echo.current_certainty}")

    # Simulate surprise factor
    world_state = core_pb2.WorldState(
        tick_number=110,
        actors={}
    )
    world_state.actors[entity_id].CopyFrom(
        core_pb2.Actor(
            id=entity_id,
            name="Bob",
            position=common_pb2.Vector2(x=20.0, y=15.0),  # Moved 10m
            state="idle"
        )
    )

    # Create a percept for the new position
    percept = perception_pb2.Percept(
        percept_id="test_percept",
        tick_observed=110,
        channel=perception_pb2.Percept.VISION,
        actor=perception_pb2.ActorPercept(
            actor_id=entity_id,
            name="Bob",
            approximate_position=common_pb2.Vector2(x=20.0, y=15.0),
            visible_action_state="idle",
            visible_emotional_cue="neutral"
        ),
        salience=0.5,
        certainty=0.8
    )

    # Apply surprise factor
    perception._tick_counter = 110
    percepts = perception._apply_surprise_factor([percept])

    assert percepts[0].salience > 0.5, "Surprise should boost salience"
    print(f"  Original salience: 0.5")
    print(f"  Boosted salience: {percepts[0].salience:.2f} (surprise!)")

    print("✓ All memory echo tests passed")
    return True


def run_tests():
    """Run all simple tests."""
    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("SIMPLE VISUAL PERCEPTION TESTS - PHASE 2")
    print("=" * 60)

    tests = [
        test_basic_raycasting,
        test_fov_detection,
        test_memory_echoes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
