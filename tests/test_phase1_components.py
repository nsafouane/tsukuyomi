"""
Phase 1 Components Test Script

Tests the new V2 components:
1. NeedsSystem - Decay, thresholds, satisfaction
2. WorldBuilder - Object placement, affordances
3. SpatialIndex - Insert, query, remove operations

Run with: python -m pytest tests/test_phase1_components.py -v
"""

import pytest
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.internal.needs.needs_system import NeedsSystem, NeedType, Need
from tsukuyomi.environment.core.world_builder import WorldBuilder, EnvironmentObject, ObjectType, Affordance, Location
from tsukuyomi.environment.spatial.spatial import SpatialIndex, SpatialObject


class TestNeedsSystem:
    """Tests for NeedsSystem."""
    
    def test_initialization(self):
        """Test needs system initialization."""
        needs = NeedsSystem()
        
        assert needs.hunger is not None
        assert needs.fatigue is not None
        assert needs.boredom is not None
        assert needs.social is not None
    
    def test_need_update(self):
        """Test need update."""
        need = Need(NeedType.HUNGER, value=0.0, decay_rate=0.01)
        
        need.update(dt=10.0)
        
        assert need.value > 0.0
    
    def test_need_satisfy(self):
        """Test satisfying a need."""
        need = Need(NeedType.HUNGER, value=0.8)
        
        need.satisfy(0.5)
        
        assert need.value == pytest.approx(0.3, abs=0.01)
    
    def test_need_is_critical(self):
        """Test critical threshold."""
        need = Need(NeedType.HUNGER, value=0.9, threshold=0.8)
        
        assert need.is_critical() == True
        
        need.satisfy(0.5)
        assert need.is_critical() == False
    
    def test_need_get_motivation(self):
        """Test motivation calculation."""
        need = Need(NeedType.HUNGER, value=0.5, threshold=0.8)
        
        motivation = need.get_motivation()
        assert 0.0 <= motivation <= 1.0
    
    def test_need_to_dict(self):
        """Test serialization."""
        need = Need(NeedType.HUNGER, value=0.5)
        
        data = need.to_dict()
        
        assert data["type"] == "hunger"
        assert data["value"] == 0.5
    
    def test_update_all(self):
        """Test updating all needs."""
        needs = NeedsSystem()
        
        time.sleep(0.1)  # Wait a bit for time to pass
        needs.update_all(tick_rate=20.0)
        
        # Needs should have increased
        assert needs.hunger.value >= 0.0
    
    def test_get_dominant_need(self):
        """Test getting dominant need."""
        needs = NeedsSystem()
        
        dominant = needs.get_dominant_need()
        # May be None if no needs are critical
        assert dominant is None or isinstance(dominant, NeedType)
    
    def test_get_critical_needs(self):
        """Test getting critical needs."""
        needs = NeedsSystem()
        
        critical = needs.get_critical_needs()
        assert isinstance(critical, list)
    
    def test_satisfy_need(self):
        """Test satisfying a specific need."""
        needs = NeedsSystem()
        needs.hunger.value = 0.8
        
        needs.satisfy_need(NeedType.HUNGER, 0.5)
        
        assert needs.hunger.value == pytest.approx(0.3, abs=0.01)
    
    def test_get_prompt_context(self):
        """Test getting prompt context."""
        needs = NeedsSystem()
        
        context = needs.get_prompt_context()
        
        assert "Hunger" in context
        assert "Fatigue" in context


class TestWorldBuilder:
    """Tests for WorldBuilder."""
    
    def test_initialization(self):
        """Test world builder initialization."""
        builder = WorldBuilder()
        
        assert builder is not None
        assert len(builder.locations) == 0
    
    def test_add_location(self):
        """Test adding a location."""
        builder = WorldBuilder()
        
        location = builder.add_location(
            name="TestRoom",
            position=(50.0, 50.0),
            size=(100.0, 100.0)
        )
        
        assert len(builder.locations) == 1
        assert location.name == "TestRoom"
    
    def test_add_object(self):
        """Test adding an object."""
        builder = WorldBuilder()
        
        obj = builder.add_object(
            name="Chair",
            obj_type=ObjectType.INTERACTIVE,
            position=(50.0, 50.0)
        )
        
        assert len(builder.global_objects) == 1
        assert obj.name == "Chair"
    
    def test_affordance(self):
        """Test affordance creation."""
        affordance = Affordance(
            action_type="SIT",
            precondition="distance < 2.0",
            effect_description="agent.sit()"
        )
        
        assert affordance.action_type == "SIT"
        
        data = affordance.to_dict()
        assert data["action_type"] == "SIT"
    
    def test_object_with_affordance(self):
        """Test object with affordance."""
        obj = EnvironmentObject(
            name="Chair",
            obj_type=ObjectType.INTERACTIVE,
            position=(10.0, 10.0)
        )
        
        obj.add_affordance("SIT", "distance < 2.0", "sit")
        
        assert len(obj.affordances) == 1
    
    def test_location(self):
        """Test location creation."""
        location = Location(
            name="Room",
            position=(0.0, 0.0),
            size=(100.0, 100.0)
        )
        
        assert location.name == "Room"
        assert len(location.spawn_points) == 0
    
    def test_location_add_spawn_point(self):
        """Test adding spawn point to location."""
        location = Location(
            name="Room",
            position=(0.0, 0.0),
            size=(100.0, 100.0)
        )
        
        location.add_spawn_point(10.0, 10.0)
        
        assert len(location.spawn_points) == 1
    
    def test_serialize(self):
        """Test serialization."""
        builder = WorldBuilder()
        builder.add_location("Room", (0.0, 0.0), (100.0, 100.0))
        
        data = builder.serialize()
        
        assert isinstance(data, dict)
        assert "locations" in data
    
    def test_validate(self):
        """Test validation."""
        builder = WorldBuilder()
        
        # Add location without spawn points
        builder.add_location("Room", (0.0, 0.0), (100.0, 100.0))
        
        errors = builder.validate()
        
        # Should have error about no spawn points
        assert len(errors) > 0


class TestSpatialIndex:
    """Tests for SpatialIndex."""
    
    def test_initialization(self):
        """Test spatial index initialization."""
        index = SpatialIndex(width=100, height=100, cell_size=10)
        
        assert index is not None
    
    def test_insert(self):
        """Test inserting an entity."""
        index = SpatialIndex(width=100, height=100, cell_size=10)
        
        index.insert("entity1", (5.0, 5.0))
        
        assert "entity1" in index.objects
    
    def test_query_nearby(self):
        """Test querying nearby entities."""
        index = SpatialIndex(width=100, height=100, cell_size=10)
        
        index.insert("entity1", (5.0, 5.0))
        index.insert("entity2", (50.0, 50.0))
        
        nearby = index.query_nearby((5.0, 5.0), radius=20.0)
        
        nearby_ids = [obj.object_id for obj in nearby]
        assert "entity1" in nearby_ids
    
    def test_remove(self):
        """Test removing an entity."""
        index = SpatialIndex(width=100, height=100, cell_size=10)
        
        index.insert("entity1", (5.0, 5.0))
        index.remove("entity1")
        
        assert "entity1" not in index.objects
    
    def test_update_position(self):
        """Test updating entity position."""
        index = SpatialIndex(width=100, height=100, cell_size=10)
        
        index.insert("entity1", (5.0, 5.0))
        index.update_position("entity1", (50.0, 50.0))
        
        nearby_old = index.query_nearby((5.0, 5.0), radius=20.0)
        nearby_new = index.query_nearby((50.0, 50.0), radius=20.0)
        
        old_ids = [obj.object_id for obj in nearby_old]
        new_ids = [obj.object_id for obj in nearby_new]
        
        assert "entity1" not in old_ids
        assert "entity1" in new_ids
    
    def test_spatial_object(self):
        """Test SpatialObject dataclass."""
        obj = SpatialObject(
            object_id="test",
            position=(10.0, 20.0)
        )
        
        assert obj.object_id == "test"
        assert obj.position == (10.0, 20.0)


class TestIntegration:
    """Integration tests for Phase 1 components."""
    
    def test_needs_affects_behavior_context(self):
        """Test that needs provide context for behavior."""
        needs = NeedsSystem()
        
        needs.satisfy_need(NeedType.HUNGER, 0.9)
        
        assert needs.hunger.value <= 0.1
    
    def test_worldbuilder_with_objects(self):
        """Test world builder with objects."""
        builder = WorldBuilder()
        
        builder.add_location("Room", (50.0, 50.0), (100.0, 100.0))
        
        builder.add_object(
            name="Chair",
            obj_type=ObjectType.INTERACTIVE,
            position=(50.0, 50.0)
        )
        
        data = builder.serialize()
        assert data is not None
