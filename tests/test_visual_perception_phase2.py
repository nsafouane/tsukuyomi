"""
Visual Perception System - Phase 2 Integration Test

This test demonstrates the enhanced visual perception pipeline with:
- Raycasting for accurate line-of-sight
- Spatial Index integration for efficient proximity queries
- Field-of-view calculations

Usage:
    python -m pytest tests/test_visual_perception_phase2.py -v
"""

import logging
import pytest
import math

from tsukuyomi.environment.physics.raycasting import Raycaster, Wall
from tsukuyomi.environment.spatial.spatial import SpatialIndex
from tsukuyomi.agents.cognitive.perception_pipeline import (
    PerceptionPipeline,
    SensoryProfile,
    AgentInternalState,
    PerceptionChannel,
    Percept,
)
from tsukuyomi.transport.proto import core_pb2, common_pb2


class TestRaycaster:
    """Tests for the Raycaster line-of-sight calculations."""

    def test_initialization(self):
        """Test raycaster initialization."""
        raycaster = Raycaster()
        assert raycaster.walls == {}

    def test_register_room_walls(self):
        """Test registering walls for a room."""
        raycaster = Raycaster()

        walls = [
            Wall(start=(0, 0), end=(20, 0), thickness=0.5),
            Wall(start=(20, 0), end=(20, 20), thickness=0.5),
            Wall(start=(20, 20), end=(0, 20), thickness=0.5),
            Wall(start=(0, 20), end=(0, 0), thickness=0.5),
        ]

        raycaster.register_room_walls("test_room", walls)

        assert "test_room" in raycaster.walls
        assert len(raycaster.walls["test_room"]) == 4

    def test_unobstructed_ray(self):
        """Test unobstructed line of sight."""
        raycaster = Raycaster()

        walls = [
            Wall(start=(0, 0), end=(20, 0), thickness=0.5),
            Wall(start=(20, 0), end=(20, 20), thickness=0.5),
            Wall(start=(20, 20), end=(0, 20), thickness=0.5),
            Wall(start=(0, 20), end=(0, 0), thickness=0.5),
        ]
        raycaster.register_room_walls("test_room", walls)

        start = (10, 10)
        end = (15, 15)
        blocked, intersection, distance = raycaster.cast_ray(start, end, "test_room")

        assert not blocked
        assert distance > 0
        assert distance == pytest.approx(math.sqrt(50), abs=0.1)

    def test_obstructed_ray(self):
        """Test obstructed line of sight."""
        raycaster = Raycaster()

        walls = [
            Wall(start=(0, 0), end=(20, 0), thickness=0.5),
            Wall(start=(20, 0), end=(20, 20), thickness=0.5),
            Wall(start=(20, 20), end=(0, 20), thickness=0.5),
            Wall(start=(0, 20), end=(0, 0), thickness=0.5),
            Wall(start=(5, 5), end=(5, 15), thickness=0.3),
        ]
        raycaster.register_room_walls("test_room", walls)

        start = (2, 10)
        end = (18, 10)
        blocked, intersection, distance = raycaster.cast_ray(start, end, "test_room")

        assert blocked
        assert intersection is not None
        assert distance < 16

    def test_no_walls(self):
        """Test raycasting when no walls are registered."""
        raycaster = Raycaster()

        start = (0, 0)
        end = (100, 100)
        blocked, intersection, distance = raycaster.cast_ray(start, end, "test_room")

        assert not blocked

    def test_max_distance(self):
        """Test max distance parameter."""
        raycaster = Raycaster()

        walls = [
            Wall(start=(0, 0), end=(100, 0), thickness=0.5),
        ]
        raycaster.register_room_walls("test_room", walls)

        start = (0, 50)
        end = (200, 50)
        blocked, intersection, distance = raycaster.cast_ray(
            start, end, "test_room", max_distance=10.0
        )

        assert distance <= 10.0


class TestSpatialIndexPerception:
    """Tests for SpatialIndex in perception context."""

    def test_query_nearby_for_perception(self):
        """Test querying nearby objects for perception."""
        index = SpatialIndex(width=100, height=100, cell_size=10)

        index.insert("agent1", (10.5, 20.3))
        index.insert("agent2", (15.2, 18.7))
        index.insert("agent3", (50.0, 50.0))
        index.insert("object1", (12.0, 19.5))

        query_pos = (10.5, 20.3)
        nearby = index.query(query_pos, radius=5.0, exclude_self="agent1")

        assert len(nearby) >= 2

        for obj_id, pos in nearby:
            distance = ((pos[0] - query_pos[0]) ** 2 + (pos[1] - query_pos[1]) ** 2) ** 0.5
            assert distance <= 5.0
            assert obj_id != "agent1"

    def test_query_nearest_for_attention(self):
        """Test querying nearest objects for attention."""
        index = SpatialIndex(width=100, height=100, cell_size=10)

        index.insert("agent1", (10.0, 10.0))
        index.insert("object1", (12.0, 10.0))
        index.insert("object2", (20.0, 10.0))
        index.insert("object3", (30.0, 10.0))

        nearest = index.query_nearest((10.0, 10.0), limit=3)

        assert len(nearest) <= 3
        for i in range(1, len(nearest)):
            assert nearest[i][2] >= nearest[i - 1][2]


class TestSensoryProfile:
    """Tests for SensoryProfile."""

    def test_vision_range(self):
        """Test vision range check."""
        profile = SensoryProfile(vision_range=20.0, vision_fov=120.0)

        assert profile.can_see(10.0)
        assert profile.can_see(20.0)
        assert not profile.can_see(25.0)

    def test_vision_fov(self):
        """Test field of view check."""
        profile = SensoryProfile(vision_range=20.0, vision_fov=120.0)

        assert profile.can_see(10.0, angle=0)
        assert profile.can_see(10.0, angle=60)
        assert not profile.can_see(10.0, angle=70)

    def test_hearing_range(self):
        """Test hearing range check."""
        profile = SensoryProfile(hearing_range=15.0)

        assert profile.can_hear(10.0)
        assert profile.can_hear(15.0)
        assert not profile.can_hear(20.0)


class TestAgentInternalState:
    """Tests for AgentInternalState."""

    def test_default_state(self):
        """Test default internal state."""
        state = AgentInternalState()

        assert state.emotional_state["valence"] == 0.0
        assert state.emotional_state["arousal"] == 0.5
        assert state.current_needs == {}
        assert state.active_beliefs == []

    def test_salience_modifier(self):
        """Test salience modifier based on arousal."""
        state = AgentInternalState()

        state.emotional_state["arousal"] = 0.0
        assert state.get_salience_modifier() == pytest.approx(0.5, abs=0.01)

        state.emotional_state["arousal"] = 1.0
        assert state.get_salience_modifier() == pytest.approx(1.0, abs=0.01)


class TestPerceptionPipeline:
    """Tests for PerceptionPipeline."""

    def test_initialization(self):
        """Test pipeline initialization."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        assert pipeline.actor_id == "agent1"
        assert pipeline.profile == profile
        assert pipeline.spatial_index is None

    def test_process_none_world_state(self):
        """Test processing None world state."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        percepts = pipeline.process(None)

        assert percepts == []

    def test_process_basic_world_state(self):
        """Test processing basic world state."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        world_state = core_pb2.WorldState(tick_number=100)
        percepts = pipeline.process(world_state)

        assert len(percepts) > 0
        assert pipeline.get_last_percepts() == percepts

    def test_filter_by_salience(self):
        """Test filtering percepts by salience."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        percepts = [
            Percept("1", PerceptionChannel.VISUAL, {}, salience=0.3),
            Percept("2", PerceptionChannel.VISUAL, {}, salience=0.7),
            Percept("3", PerceptionChannel.AUDITORY, {}, salience=0.5),
        ]

        filtered = pipeline.filter_by_salience(percepts, threshold=0.5)

        assert len(filtered) == 2
        assert all(p.salience >= 0.5 for p in filtered)

    def test_get_visual_percepts(self):
        """Test getting only visual percepts."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        percepts = [
            Percept("1", PerceptionChannel.VISUAL, {}, salience=0.3),
            Percept("2", PerceptionChannel.AUDITORY, {}, salience=0.7),
            Percept("3", PerceptionChannel.VISUAL, {}, salience=0.5),
        ]

        visual = pipeline.get_visual_percepts(percepts)

        assert len(visual) == 2
        assert all(p.channel == PerceptionChannel.VISUAL for p in visual)

    def test_get_auditory_percepts(self):
        """Test getting only auditory percepts."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        percepts = [
            Percept("1", PerceptionChannel.VISUAL, {}, salience=0.3),
            Percept("2", PerceptionChannel.AUDITORY, {}, salience=0.7),
            Percept("3", PerceptionChannel.AUDITORY, {}, salience=0.5),
        ]

        auditory = pipeline.get_auditory_percepts(percepts)

        assert len(auditory) == 2
        assert all(p.channel == PerceptionChannel.AUDITORY for p in auditory)

    def test_with_internal_state(self):
        """Test processing with internal state affecting salience."""
        profile = SensoryProfile()
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)

        internal_state = AgentInternalState()
        internal_state.emotional_state["arousal"] = 1.0

        world_state = core_pb2.WorldState(tick_number=100)
        percepts = pipeline.process(world_state, internal_state)

        assert len(percepts) > 0


class TestIntegration:
    """Integration tests for visual perception system."""

    def test_spatial_index_with_pipeline(self):
        """Test spatial index integration with perception pipeline."""
        index = SpatialIndex(width=100, height=100, cell_size=10)

        index.insert("agent1", (10.0, 10.0))
        index.insert("agent2", (15.0, 15.0))
        index.insert("object1", (12.0, 12.0))

        profile = SensoryProfile(vision_range=20.0)
        pipeline = PerceptionPipeline(actor_id="agent1", profile=profile)
        pipeline.set_spatial_index(index)

        nearby = index.query((10.0, 10.0), radius=20.0, exclude_self="agent1")

        assert len(nearby) >= 2

    def test_raycasting_blocks_view(self):
        """Test that walls block line of sight."""
        raycaster = Raycaster()

        walls = [
            Wall(start=(0, 0), end=(20, 0), thickness=0.5),
            Wall(start=(20, 0), end=(20, 20), thickness=0.5),
            Wall(start=(20, 20), end=(0, 20), thickness=0.5),
            Wall(start=(0, 20), end=(0, 0), thickness=0.5),
            Wall(start=(5, 5), end=(5, 15), thickness=0.3),
        ]
        raycaster.register_room_walls("room", walls)

        blocked1, _, _ = raycaster.cast_ray((10, 10), (15, 15), "room")
        blocked2, _, _ = raycaster.cast_ray((2, 10), (18, 10), "room")

        assert not blocked1
        assert blocked2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
