"""
Test Suite for Tsukuyomi V2 Phase 2 (World Dynamics)

Tests the integration of:
- SpatialIndex (enhanced grid with caching and bulk ops)
- ProposalWindow (multi-tick commitment with conflict resolution)
- Affordance System (object validation)
"""

import pytest
import time
import logging

from tsukuyomi.environment.spatial.spatial import SpatialIndex, SpatialObject
from tsukuyomi.environment.core.proposal import ProposalWindow, ConflictResolution
from tsukuyomi.environment.rules.affordance import AffordanceValidator
from tsukuyomi.transport.proto import core_pb2, common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSpatialIndex:
    """Tests for SpatialIndex (Phase 2 Enhanced)."""

    def test_basic_operations(self):
        """Test basic SpatialIndex operations."""
        index = SpatialIndex(width=100, height=100, cell_size=10.0)

        index.insert("agent1", (10.5, 20.3))
        index.insert("agent2", (15.0, 25.0))
        index.insert("agent3", (5.0, 5.0))

        nearby = index.query((12.0, 22.0), radius=5.0)
        assert len(nearby) >= 1
        object_ids = [obj_id for obj_id, _ in nearby]
        assert "agent1" in object_ids or "agent2" in object_ids

        index.update_position("agent1", (50.0, 50.0))
        pos = index.get_object_position("agent1")
        assert pos == (50.0, 50.0)

        assert index.remove("agent1")
        assert index.get_object_position("agent1") is None

    def test_bulk_operations(self):
        """Test bulk operations for batch updates."""
        index = SpatialIndex(width=100, height=100, cell_size=10.0)

        objects = [(f"agent{i}", (i * 2.0, i * 2.0)) for i in range(50)]
        inserted = index.insert_bulk(objects)
        assert inserted == 50
        assert len(index.objects) == 50

        updates = [(f"agent{i}", (i * 2.0 + 1.0, i * 2.0 + 1.0)) for i in range(25)]
        updated = index.update_positions_bulk(updates)
        assert updated == 25

        to_remove = [f"agent{i}" for i in range(10, 20)]
        removed = index.remove_bulk(to_remove)
        assert removed == 10
        assert len(index.objects) == 40

    def test_query_caching(self):
        """Test query caching performance."""
        index = SpatialIndex(width=100, height=100, cell_size=10.0, enable_stats=True)

        objects = [(f"agent{i}", (i * 2.0, i * 2.0)) for i in range(50)]
        index.insert_bulk(objects)

        start = time.perf_counter()
        result1 = index.query((50.0, 50.0), radius=15.0, use_cache=True)
        time1 = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        result2 = index.query((50.0, 50.0), radius=15.0, use_cache=True)
        time2 = (time.perf_counter() - start) * 1000

        assert result1 == result2
        logger.info(f"Query time: {time1:.3f}ms (miss) vs {time2:.3f}ms (hit)")

    def test_k_nearest(self):
        """Test k-nearest neighbor query."""
        index = SpatialIndex(width=100, height=100, cell_size=10.0)

        for i in range(10):
            for j in range(10):
                index.insert(f"agent_{i}_{j}", (i * 10.0, j * 10.0))

        nearest = index.find_k_nearest((45.0, 45.0), k=5)
        assert len(nearest) > 0
        if len(nearest) > 1:
            for i in range(1, len(nearest)):
                assert nearest[i][2] >= nearest[i - 1][2]

    def test_performance(self):
        """Test that SpatialIndex meets performance targets."""
        index = SpatialIndex(width=1000, height=1000, cell_size=10.0, enable_stats=True)

        objects = [(f"agent{i}", (i * 10.0, i * 10.0)) for i in range(100)]
        index.insert_bulk(objects)

        start = time.perf_counter()
        for i in range(100):
            index.query((500.0, 500.0), radius=50.0, use_cache=False)
        elapsed = (time.perf_counter() - start) * 1000

        avg_query_time = elapsed / 100
        assert avg_query_time < 200.0, f"Avg query time {avg_query_time:.2f}ms exceeds target"

        stats = index.get_stats()
        logger.info(
            f"SpatialIndex performance: avg_query={avg_query_time:.3f}ms, "
            f"queries={index.query_stats.query_count}"
        )


class TestProposalWindow:
    """Tests for ProposalWindow (Phase 2)."""

    def test_basic_operations(self):
        """Test basic ProposalWindow operations."""
        window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

        window.open_window(tick_number=0)
        assert window.is_open

        proposal1 = core_pb2.Proposal(
            proposal_id="prop1",
            actor_id="actor1",
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"}
        )
        assert window.add_proposal(proposal1)

        ready = window.get_ready_proposals()
        assert len(ready) == 1

    def test_multi_tick(self):
        """Test multi-tick commitment."""
        window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

        window.open_window(tick_number=0)

        proposal = core_pb2.Proposal(
            proposal_id="prop1",
            actor_id="actor1",
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"}
        )
        window.add_proposal(proposal)

        assert not window.is_expired(1)
        assert not window.is_expired(2)
        assert window.is_expired(3)

    def test_conflict_resolution(self):
        """Test conflict resolution between proposals."""
        window = ProposalWindow(
            duration_ticks=3,
            max_proposals_per_actor=2,
            conflict_resolution=ConflictResolution.HIGHEST_PRIORITY
        )

        window.open_window(tick_number=0)

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

        window.add_proposal(proposal1, priority=1)
        window.add_proposal(proposal2, priority=10)

        conflicts = window.resolve_conflicts()
        assert len(conflicts) > 0

        ready = window.get_ready_proposals()
        assert len(ready) == 1
        assert ready[0].proposal_id == "prop2"

    def test_actor_limit(self):
        """Test that actor proposal limit is enforced."""
        window = ProposalWindow(duration_ticks=3, max_proposals_per_actor=2)

        window.open_window(tick_number=0)

        for i in range(3):
            proposal = core_pb2.Proposal(
                proposal_id=f"prop{i}",
                actor_id="actor1",
                action=core_pb2.ActionType.IDLE,
                parameters={}
            )
            result = window.add_proposal(proposal)
            assert result == (i < 2)

        stats = window.get_stats()
        assert stats["total_proposals"] == 2


class TestAffordanceValidator:
    """Tests for AffordanceValidator (Phase 2)."""

    def test_basic_validation(self):
        """Test basic affordance validation."""
        validator = AffordanceValidator()

        obj = core_pb2.EnvironmentObject(
            id="apple_1",
            type="food",
            position=common_pb2.Vector2(x=10, y=10),
            interactive=True
        )

        actor = core_pb2.Actor(
            id="actor1",
            name="Alice",
            position=common_pb2.Vector2(x=11, y=11),
            state="IDLE"
        )

        result = validator.validate_action(
            obj,
            core_pb2.ActionType.COLLECT,
            actor,
            {"target_id": "apple_1"}
        )

        assert result.is_valid

    def test_distance_check(self):
        """Test distance precondition checking."""
        validator = AffordanceValidator()

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

        result = validator.validate_action(
            obj,
            core_pb2.ActionType.COLLECT,
            actor,
            {"target_id": "apple_1"}
        )

        assert not result.is_valid
        assert "Too far" in result.reason

    def test_ownership_check(self):
        """Test ownership precondition checking."""
        validator = AffordanceValidator()

        obj = core_pb2.EnvironmentObject(
            id="sword_1",
            type="weapon",
            position=common_pb2.Vector2(x=10, y=10),
            interactive=True,
            owner_id="actor2"
        )

        actor = core_pb2.Actor(
            id="actor1",
            name="Alice",
            position=common_pb2.Vector2(x=11, y=11),
            state="IDLE"
        )

        result = validator.validate_action(
            obj,
            core_pb2.ActionType.TAKE,
            actor,
            {"target_id": "sword_1"}
        )

        assert not result.is_valid
        assert "owned" in result.reason.lower()

    def test_get_supported_actions(self):
        """Test getting supported actions for an object."""
        validator = AffordanceValidator()

        obj = core_pb2.EnvironmentObject(
            id="apple_1",
            type="food",
            position=common_pb2.Vector2(x=10, y=10),
            interactive=True
        )

        actions = validator.get_supported_actions(obj)
        assert "EXAMINE" in actions
        assert "COLLECT" in actions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
