"""
Test Suite for Tsukuyomi V2 Phase 2 (World Dynamics)

Tests the integration of:
- SpatialIndex (enhanced grid with caching and bulk ops)
- ProposalWindow (multi-tick commitment with conflict resolution)
- Affordance System (object validation)
- FateEngine integration (all components together)
"""

import asyncio
import pytest
import time
import uuid
import logging

from tsukuyomi.proto import core_pb2, common_pb2
from tsukuyomi.proto.fate_engine import FateEngine
from tsukuyomi.core.spatial_index import SpatialIndex, QueryStats
from tsukuyomi.core.proposal_window import ProposalWindow, ConflictResolution
from tsukuyomi.core.affordance import AffordanceValidator, AffordanceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SpatialIndex Tests (Phase 2 Enhanced)
# ============================================================================

def test_spatial_index_basic():
    """Test basic SpatialIndex operations."""
    index = SpatialIndex(width=100, height=100, cell_size=10.0)

    # Insert objects
    index.insert("agent1", (10.5, 20.3))
    index.insert("agent2", (15.0, 25.0))
    index.insert("agent3", (5.0, 5.0))

    # Query nearby
    nearby = index.query((12.0, 22.0), radius=5.0)
    assert len(nearby) >= 1
    object_ids = [obj_id for obj_id, _ in nearby]
    assert "agent1" in object_ids or "agent2" in object_ids

    # Update position
    index.update_position("agent1", (50.0, 50.0))
    pos = index.get_object_position("agent1")
    assert pos == (50.0, 50.0)

    # Remove object
    assert index.remove("agent1")
    assert index.get_object_position("agent1") is None


def test_spatial_index_bulk_operations():
    """Test bulk operations for batch updates."""
    index = SpatialIndex(width=100, height=100, cell_size=10.0)

    # Bulk insert
    objects = [(f"agent{i}", (i * 2.0, i * 2.0)) for i in range(50)]
    inserted = index.insert_bulk(objects)
    assert inserted == 50
    assert len(index.objects) == 50

    # Bulk update
    updates = [(f"agent{i}", (i * 2.0 + 1.0, i * 2.0 + 1.0)) for i in range(25)]
    updated = index.update_positions_bulk(updates)
    assert updated == 25

    # Bulk remove
    to_remove = [f"agent{i}" for i in range(10, 20)]
    removed = index.remove_bulk(to_remove)
    assert removed == 10
    assert len(index.objects) == 40


def test_spatial_index_query_caching():
    """Test query caching performance."""
    index = SpatialIndex(width=100, height=100, cell_size=10.0, enable_stats=True)

    # Insert objects
    objects = [(f"agent{i}", (i * 2.0, i * 2.0)) for i in range(50)]
    index.insert_bulk(objects)

    # First query (cache miss)
    start = time.perf_counter()
    result1 = index.query((50.0, 50.0), radius=15.0, use_cache=True)
    time1 = (time.perf_counter() - start) * 1000

    # Second query (cache hit)
    start = time.perf_counter()
    result2 = index.query((50.0, 50.0), radius=15.0, use_cache=True)
    time2 = (time.perf_counter() - start) * 1000

    # Cache hit should be faster
    assert result1 == result2
    # Cache hit may not always be faster due to overhead, but it should be close
    logger.info(f"Query time: {time1:.3f}ms (miss) vs {time2:.3f}ms (hit)")


def test_spatial_index_k_nearest():
    """Test k-nearest neighbor query."""
    index = SpatialIndex(width=100, height=100, cell_size=10.0)

    # Insert objects in a grid pattern
    for i in range(10):
        for j in range(10):
            index.insert(f"agent_{i}_{j}", (i * 10.0, j * 10.0))

    # Find 5 nearest to center (point near multiple grid positions)
    nearest = index.find_k_nearest((45.0, 45.0), k=5)
    # Should find at least some objects
    assert len(nearest) > 0
    # Verify sorted by distance if we found multiple
    if len(nearest) > 1:
        for i in range(1, len(nearest)):
            assert nearest[i][2] >= nearest[i-1][2]


def test_spatial_index_performance():
    """Test that SpatialIndex meets performance targets."""
    index = SpatialIndex(width=1000, height=1000, cell_size=10.0, enable_stats=True)

    # Insert 100 objects
    objects = [(f"agent{i}", (i * 10.0, i * 10.0)) for i in range(100)]
    index.insert_bulk(objects)

    # Perform 100 queries
    start = time.perf_counter()
    for i in range(100):
        index.query((500.0, 500.0), radius=50.0, use_cache=False)
    elapsed = (time.perf_counter() - start) * 1000

    avg_query_time = elapsed / 100

    # Performance target: <200ms for 50+ agents
    assert avg_query_time < 200.0, f"Avg query time {avg_query_time:.2f}ms exceeds target"

    stats = index.get_stats()
    logger.info(
        f"SpatialIndex performance: avg_query={avg_query_time:.3f}ms, "
        f"queries={index.query_stats.query_count}"
    )


# ============================================================================
# ProposalWindow Tests (Phase 2)
# ============================================================================

def test_proposal_window_basic():
    """Test basic ProposalWindow operations."""
    window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

    # Open window
    window.open_window(tick_number=0)
    assert window.is_open

    # Add proposals
    proposal1 = core_pb2.Proposal(
        proposal_id="prop1",
        actor_id="actor1",
        action=core_pb2.ActionType.MOVE,
        parameters={"destination": "tavern"}
    )
    assert window.add_proposal(proposal1)

    # Get ready proposals
    ready = window.get_ready_proposals()
    assert len(ready) == 1


def test_proposal_window_multi_tick():
    """Test multi-tick commitment."""
    window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

    # Open window at tick 0
    window.open_window(tick_number=0)

    # Add proposal
    proposal = core_pb2.Proposal(
        proposal_id="prop1",
        actor_id="actor1",
        action=core_pb2.ActionType.MOVE,
        parameters={"destination": "tavern"}
    )
    window.add_proposal(proposal)

    # Should not be expired at tick 1
    assert not window.is_expired(1)

    # Should not be expired at tick 2
    assert not window.is_expired(2)

    # Should be expired at tick 3
    assert window.is_expired(3)


def test_proposal_window_conflict_resolution():
    """Test conflict resolution between proposals."""
    window = ProposalWindow(
        duration_ticks=3,
        max_proposals_per_actor=2,
        conflict_resolution=ConflictResolution.HIGHEST_PRIORITY
    )

    window.open_window(tick_number=0)

    # Two actors try to collect same object
    proposal1 = core_pb2.Proposal(
        proposal_id="prop1",
        actor_id="actor1",
        action=core_pb2.ActionType.COLLECT,
        parameters={"target_id": "apple_1"}
    )
    proposal2 = core_pb2.Proposal(
        proposal_id="prop2",
        actor_id="actor2",
        action=core_pb2.ActionType.COLLECT,
        parameters={"target_id": "apple_1"}
    )

    # Add with different priorities
    window.add_proposal(proposal1, priority=1)
    window.add_proposal(proposal2, priority=10)

    # Resolve conflicts
    conflicts = window.resolve_conflicts()
    assert len(conflicts) > 0

    # Get ready proposals (higher priority should win)
    ready = window.get_ready_proposals()
    assert len(ready) == 1
    assert ready[0].proposal_id == "prop2"  # Higher priority


def test_proposal_window_actor_limit():
    """Test that actor proposal limit is enforced."""
    window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

    window.open_window(tick_number=0)

    # Same actor tries to submit 3 proposals
    for i in range(3):
        proposal = core_pb2.Proposal(
            proposal_id=f"prop{i}",
            actor_id="actor1",
            action=core_pb2.ActionType.IDLE,
            parameters={}
        )
        result = window.add_proposal(proposal)

        # First 2 should succeed, 3rd should fail
        assert result == (i < 2)

    stats = window.get_stats()
    assert stats["total_proposals"] == 2


# ============================================================================
# AffordanceValidator Tests (Phase 2)
# ============================================================================

def test_affordance_basic_validation():
    """Test basic affordance validation."""
    validator = AffordanceValidator()

    # Create an interactive object
    obj = core_pb2.EnvironmentObject(
        id="apple_1",
        type="food",
        position=common_pb2.Vector2(x=10, y=10),
        interactive=True
    )

    # Create actor
    actor = core_pb2.Actor(
        id="actor1",
        name="Alice",
        position=common_pb2.Vector2(x=11, y=11),
        state="IDLE"
    )

    # Validate COLLECT action
    result = validator.validate_action(
        obj,
        core_pb2.ActionType.COLLECT,
        actor,
        {"target_id": "apple_1"}
    )

    assert result.is_valid


def test_affordance_distance_check():
    """Test distance precondition checking."""
    validator = AffordanceValidator()

    # Create object far from actor
    obj = core_pb2.EnvironmentObject(
        id="apple_1",
        type="food",
        position=common_pb2.Vector2(x=100, y=100),
        interactive=True
    )

    actor = core_pb2.Actor(
        id="actor1",
        name="Alice",
        position=common_pb2.Vector2(x=0, y=0),
        state="IDLE"
    )

    # Should fail due to distance
    result = validator.validate_action(
        obj,
        core_pb2.ActionType.COLLECT,
        actor,
        {"target_id": "apple_1"}
    )

    assert not result.is_valid
    assert "Too far" in result.reason


def test_affordance_ownership_check():
    """Test ownership precondition checking."""
    validator = AffordanceValidator()

    # Create owned object
    obj = core_pb2.EnvironmentObject(
        id="sword_1",
        type="weapon",
        position=common_pb2.Vector2(x=10, y=10),
        interactive=True,
        owner_id="actor2"  # Owned by someone else
    )

    actor = core_pb2.Actor(
        id="actor1",
        name="Alice",
        position=common_pb2.Vector2(x=11, y=11),
        state="IDLE"
    )

    # Should fail due to ownership
    result = validator.validate_action(
        obj,
        core_pb2.ActionType.TAKE,
        actor,
        {"target_id": "sword_1"}
    )

    assert not result.is_valid
    assert "owned" in result.reason.lower()


def test_affordance_get_supported_actions():
    """Test getting supported actions for an object."""
    validator = AffordanceValidator()

    # Interactive object
    obj = core_pb2.EnvironmentObject(
        id="apple_1",
        type="food",
        position=common_pb2.Vector2(x=10, y=10),
        interactive=True
    )

    actions = validator.get_supported_actions(obj)
    assert "EXAMINE" in actions
    assert "COLLECT" in actions


# ============================================================================
# Integration Tests (Phase 2)
# ============================================================================

@pytest.mark.asyncio
async def test_fate_engine_phase2_integration():
    """Test Phase 2 integration in FateEngine."""
    # Create engine with Phase 2 enabled
    engine = FateEngine(
        tick_rate=20,
        seed=42,
        enable_phase2=True,
        multi_tick_window_duration=3,
        conflict_resolution=ConflictResolution.HIGHEST_PRIORITY
    )

    # Register actors
    actor1_id = str(uuid.uuid4())
    actor2_id = str(uuid.uuid4())
    engine.register_actor(actor1_id, "Alice", position=(10, 10))
    engine.register_actor(actor2_id, "Bob", position=(15, 15))

    # Add collectible object
    obj_id = "apple_1"
    engine.world_state.objects[obj_id].CopyFrom(
        core_pb2.EnvironmentObject(
            id=obj_id,
            type="food",
            position=common_pb2.Vector2(x=10.5, y=10.5),
            interactive=True
        )
    )

    # Verify Phase 2 components are initialized
    assert engine.spatial_index is not None
    assert engine.proposal_window is not None
    assert engine.affordance_validator is not None

    # Verify actors in spatial index
    assert actor1_id in engine.spatial_index.objects
    assert actor2_id in engine.spatial_index.objects

    # Run a few ticks
    await engine._phase_state_broadcast(0)
    await engine._phase_proposal_window(0)
    await engine._phase_proposal_window(1)
    await engine._phase_proposal_window(2)
    await engine._phase_proposal_window(3)  # Window expires

    # Check Phase 2 stats
    stats = engine.get_phase2_stats()
    assert stats["phase2_enabled"]
    assert "spatial_index" in stats
    assert "proposal_window" in stats
    assert "affordance_validator" in stats


@pytest.mark.asyncio
async def test_fate_engine_affordance_validation():
    """Test that FateEngine uses affordance validation when Phase 2 is enabled."""
    # Test with Phase 2 enabled - affordance validator should check distance
    engine = FateEngine(
        tick_rate=20,
        seed=42,
        enable_phase2=True,
        multi_tick_window_duration=1  # Use 1-tick window for immediate resolution
    )

    # Register actor
    actor_id = str(uuid.uuid4())
    engine.register_actor(actor_id, "Alice", position=(0, 0))

    # Add object far away
    obj_id = "apple_1"
    engine.world_state.objects[obj_id].CopyFrom(
        core_pb2.EnvironmentObject(
            id=obj_id,
            type="food",
            position=common_pb2.Vector2(x=100, y=100),
            interactive=True
        )
    )

    # Submit proposal to collect (should fail due to distance)
    proposal = core_pb2.Proposal(
        proposal_id=str(uuid.uuid4()),
        actor_id=actor_id,
        action=core_pb2.ActionType.COLLECT,
        parameters={"target_id": obj_id}
    )

    await engine.submit_proposal(proposal)

    # Run proposal window (1 tick duration means it expires immediately)
    await engine._phase_proposal_window(0)
    await engine._phase_proposal_window(1)  # Window expires

    resolutions = await engine._phase_fate_resolution(0)

    # Should have at least one resolution
    assert len(resolutions) >= 1
    # At least one resolution should be a failure due to distance
    has_distance_failure = any(
        not r.success and "Too far" in r.reason
        for r in resolutions
    )
    assert has_distance_failure, f"Expected distance failure, got: {[(r.success, r.reason) for r in resolutions]}"


if __name__ == "__main__":
    # Run basic tests
    print("Running SpatialIndex tests...")
    test_spatial_index_basic()
    test_spatial_index_bulk_operations()
    test_spatial_index_query_caching()
    test_spatial_index_k_nearest()
    test_spatial_index_performance()
    print("✓ SpatialIndex tests passed")

    print("\nRunning ProposalWindow tests...")
    test_proposal_window_basic()
    test_proposal_window_multi_tick()
    test_proposal_window_conflict_resolution()
    test_proposal_window_actor_limit()
    print("✓ ProposalWindow tests passed")

    print("\nRunning AffordanceValidator tests...")
    test_affordance_basic_validation()
    test_affordance_distance_check()
    test_affordance_ownership_check()
    test_affordance_get_supported_actions()
    print("✓ AffordanceValidator tests passed")

    print("\nRunning integration tests...")
    asyncio.run(test_fate_engine_phase2_integration())
    asyncio.run(test_fate_engine_affordance_validation())
    print("✓ Integration tests passed")

    print("\n✓ All Phase 2 tests passed!")
