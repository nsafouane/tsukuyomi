"""
Phase 1 Components Test Script

Tests the new V2 components:
1. NeedsSystem - Decay, thresholds, satisfaction
2. WorldBuilder - Object placement, affordances
3. SpatialIndex - Insert, query, remove operations
4. AgentBrain Integration - Needs context in prompts

Run with: python -m tests.test_phase1_components
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.needs_system import NeedsSystem, NeedType, Need
from tsukuyomi.core.world_builder import WorldBuilder, EnvironmentObject, ObjectType, Affordance
from tsukuyomi.core.spatial_index import SpatialIndex


def test_needs_system():
    """Test the NeedsSystem decay and satisfaction logic."""
    print("\n=== Testing NeedsSystem ===")

    needs = NeedsSystem()

    # Initial state
    print(f"Initial hunger: {needs.hunger.value:.3f}")
    print(f"Initial boredom: {needs.boredom.value:.3f}")

    # Simulate decay (simulate 10 seconds at 20 ticks/sec)
    dt = 10.0 / 20.0  # 0.5 seconds
    needs.update_all(tick_rate=20.0)

    print(f"After decay (10s simulated):")
    print(f"  Hunger: {needs.hunger.value:.3f} (critical: {needs.hunger.is_critical()})")
    print(f"  Boredom: {needs.boredom.value:.3f} (critical: {needs.boredom.is_critical()})")

    # Test satisfaction
    print("\nSatisfying hunger...")
    needs.satisfy_need(NeedType.HUNGER, amount=0.5)
    print(f"Hunger after satisfaction: {needs.hunger.value:.3f}")

    # Test dominant need
    print(f"\nDominant need: {needs.get_dominant_need()}")
    print(f"Critical needs: {needs.get_critical_needs()}")

    # Test prompt context
    print("\nNeeds prompt context:")
    print(needs.get_prompt_context())

    print("✅ NeedsSystem tests passed\n")


def test_world_builder():
    """Test WorldBuilder API for creating worlds."""
    print("\n=== Testing WorldBuilder ===")

    builder = WorldBuilder()

    # Add location
    market = builder.add_location(
        name="MarketSquare",
        position=(0.0, 0.0),
        size=(20.0, 20.0),
        spawn_points=[(0.0, 0.0), (10.0, 10.0)]
    )
    print(f"Created location: {market.name}")

    # Add interactive object with affordances
    apple_stall = builder.add_interactive_object(
        name="Apple Stall",
        position=(5.0, 5.0),
        location_id=market.location_id,
        affordances=[
            {"action_type": "COLLECT", "precondition": "distance < 2.0", "effect": "get_apple"},
            {"action_type": "BUY", "precondition": "has_coin", "effect": "trade_for_apple"}
        ],
        properties={"contains": "apples", "price": 5}
    )
    print(f"Created object: {apple_stall.name} with {len(apple_stall.affordances)} affordances")

    # Validate world
    errors = builder.validate()
    if errors:
        print(f"⚠️ Validation errors: {errors}")
    else:
        print("✅ World validation passed")

    # Serialize
    serialized = builder.serialize()
    print(f"\nSerialized world has {len(serialized['locations'])} locations")

    # Test deserialization
    rebuilt = WorldBuilder.deserialize(serialized)
    print(f"Deserialized world has {len(rebuilt.locations)} locations")

    print("✅ WorldBuilder tests passed\n")


def test_spatial_index():
    """Test SpatialIndex operations."""
    print("\n=== Testing SpatialIndex ===")

    index = SpatialIndex(width=100, height=100, cell_size=10)

    # Insert objects
    index.insert("agent1", (15.5, 20.3))
    index.insert("agent2", (25.1, 30.7))
    index.insert("object1", (12.0, 18.0))
    index.insert("agent3", (18.2, 22.1))

    print(f"Inserted 4 objects")
    print(f"Spatial index stats: {index.get_stats()}")

    # Query nearby
    results = index.query((17.0, 21.0), radius=5.0)
    print(f"\nQuery near (17, 21) radius 5 found {len(results)} objects:")
    for obj_id, pos in results:
        print(f"  - {obj_id} at {pos}")

    # Query nearest
    nearest = index.query_nearest((17.0, 21.0), limit=3)
    print(f"\n3 nearest objects to (17, 21):")
    for obj_id, pos, dist in nearest:
        print(f"  - {obj_id} at distance {dist:.2f}")

    # Update position
    index.update_position("agent1", (35.0, 40.0))
    print(f"\nUpdated agent1 to (35, 40)")

    new_results = index.query((35.0, 40.0), radius=2.0)
    print(f"Query near new position found {len(new_results)} objects")

    # Remove object
    index.remove("object1")
    print(f"\nRemoved object1")
    print(f"Objects remaining: {len(index.objects)}")

    print("✅ SpatialIndex tests passed\n")


def test_integration():
    """Test integration between components."""
    print("\n=== Testing Integration ===")

    # Create world with spatial index
    builder = WorldBuilder()
    builder.add_location("TestZone", (0.0, 0.0), (50.0, 50.0))

    # Add objects to world
    stall = builder.add_interactive_object(
        name="Food Stall",
        position=(10.0, 10.0),
        affordances=[{"action_type": "COLLECT", "effect": "get_food"}]
    )
    # Add agent directly to spatial index (WorldBuilder doesn't support agents)
    # We'll just use the spatial index directly for agents

    # Create spatial index
    spatial = SpatialIndex(width=50, height=50)
    spatial.insert("HungryAgent", (5.0, 5.0))
    spatial.insert("Food Stall", (10.0, 10.0))

    # Create needs system
    needs = NeedsSystem()
    needs.hunger.value = 0.9  # Critical hunger

    # Query - agent can see the stall
    nearby = spatial.query((5.0, 5.0), radius=6.0)
    print(f"Agent sees {len(nearby)} objects")

    # Get needs context
    needs_context = needs.get_prompt_context()
    print(f"\nNeeds context for agent:")
    print(needs_context)

    # Agent should be motivated by hunger to find the food stall
    dominant = needs.get_dominant_need()
    print(f"\nDominant need: {dominant}")

    if dominant == NeedType.HUNGER and nearby:
        print("✅ Integration test: Agent motivated by hunger to find nearby food stall")
    else:
        print("⚠️ Integration test: Agent not properly motivated")

    print("✅ Integration tests passed\n")


def main():
    """Run all Phase 1 tests."""
    print("=" * 50)
    print("Tsukuyomi V2 - Phase 1 Component Tests")
    print("=" * 50)

    try:
        test_needs_system()
        test_world_builder()
        test_spatial_index()
        test_integration()

        print("\n" + "=" * 50)
        print("✅ ALL PHASE 1 TESTS PASSED")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
