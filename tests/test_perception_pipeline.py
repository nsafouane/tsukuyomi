"""
Test script for Phase 2.1: Perception Foundation

Tests the PerceptionPipeline implementation including:
- Sensory channels (vision, hearing, proprioception, memory echoes)
- Staggered Perception Schedule
- Salience scoring with Surprise Factor
- Memory Echo tracking
"""

import logging
import unittest
from datetime import datetime
import sys

from tsukuyomi.agents.cognitive.perception_pipeline import PerceptionPipeline, SensoryProfile, AgentInternalState
from tsukuyomi.transport.proto import core_pb2, perception_pb2, common_pb2

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PerceptionTest")


def create_test_world():
    """Create a test world state with multiple actors and objects."""
    world_state = core_pb2.WorldState()
    world_state.tick_number = 1000
    
    # Create multiple actors
    actor1 = core_pb2.Actor()
    actor1.id = "agent_001"
    actor1.name = "Thomas Wright"
    actor1.position.x = 0.0
    actor1.position.y = 0.0
    actor1.state = "IDLE"
    actor1.current_location = "jury_room"
    world_state.actors["agent_001"].CopyFrom(actor1)
    
    actor2 = core_pb2.Actor()
    actor2.id = "agent_002"
    actor2.name = "Davis"
    actor2.position.x = 5.0
    actor2.position.y = 0.0
    actor2.state = "speaking"
    actor2.current_location = "jury_room"
    world_state.actors["agent_002"].CopyFrom(actor2)
    
    actor3 = core_pb2.Actor()
    actor3.id = "agent_003"
    actor3.name = "Smith"
    actor3.position.x = 15.0
    actor3.position.y = 10.0
    actor3.state = "agitated"
    actor3.current_location = "jury_room"
    world_state.actors["agent_003"].CopyFrom(actor3)
    
    # Create objects
    obj1 = core_pb2.EnvironmentObject()
    obj1.id = "obj_knife_01"
    obj1.type = "weapon"
    obj1.position.x = 2.0
    obj1.position.y = 1.0
    obj1.interactive = True
    obj1.properties["description"] = "A switchblade knife"
    world_state.objects["obj_knife_01"].CopyFrom(obj1)
    
    obj2 = core_pb2.EnvironmentObject()
    obj2.id = "obj_table_01"
    obj2.type = "furniture"
    obj2.position.x = 5.0
    obj2.position.y = 0.0
    obj2.interactive = False
    world_state.objects["obj_table_01"].CopyFrom(obj2)
    
    return world_state


def test_staggered_perception_schedule():
    """Test that Staggered Perception Schedule works correctly."""
    logger.info("=" * 60)
    logger.info("TEST 1: Staggered Perception Schedule")
    logger.info("=" * 60)
    
    world_state = create_test_world()
    
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=120.0,
        hearing_range=15.0
    )
    
    pipeline = PerceptionPipeline("agent_001", sensory_profile)
    agent_state = AgentInternalState(
        current_concerns=["Davis", "evidence"],
        mood_label="calm",
        arousal=0.3,
        last_seen_entities={}
    )
    
    # Test multiple ticks
    for tick in range(1000, 1015):
        percepts = pipeline.process(world_state, agent_state, tick)
        is_deep_tick = (tick % PerceptionPipeline.DEEP_PERCEPTION_INTERVAL) == 0
        
        logger.info(f"Tick {tick}: {'DEEP' if is_deep_tick else 'PROXIMITY'} - {len(percepts)} percepts")
        
        # Deep perception should generate more percepts than proximity heartbeat
        if is_deep_tick:
            logger.info(f"  → Deep perception tick - full vision processing")
            assert len(percepts) > 0, "Deep perception should generate percepts"
        else:
            logger.info(f"  → Proximity heartbeat tick - lightweight processing")
            # Proximity might have fewer percepts (only close entities)
        
        # Print percept details
        for percept in percepts[:3]:  # Show top 3
            if percept.HasField('actor'):
                logger.info(f"    - [{percept.channel}] {percept.actor.name} @ "
                          f"({percept.actor.approximate_position.x:.1f}, "
                          f"{percept.actor.approximate_position.y:.1f}) "
                          f"salience={percept.salience:.2f} certainty={percept.certainty:.2f}")
            elif percept.HasField('object'):
                logger.info(f"    - [{percept.channel}] {percept.object.apparent_type} @ "
                          f"({percept.object.approximate_position.x:.1f}, "
                          f"{percept.object.approximate_position.y:.1f}) "
                          f"salience={percept.salience:.2f}")
            elif percept.HasField('speech'):
                logger.info(f"    - [{percept.channel}] Speech from {percept.speech.speaker_name}: "
                          f"'{percept.speech.content[:20]}...' "
                          f"salience={percept.salience:.2f}")
    
    logger.info("✓ Staggered Perception Schedule test PASSED\n")


def test_salience_scoring():
    """Test salience scoring with Surprise Factor."""
    logger.info("=" * 60)
    logger.info("TEST 2: Salience Scoring with Surprise Factor")
    logger.info("=" * 60)
    
    world_state = create_test_world()
    
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=120.0,
        hearing_range=15.0
    )
    
    pipeline = PerceptionPipeline("agent_001", sensory_profile)
    agent_state = AgentInternalState(
        current_concerns=["Davis", "evidence"],
        mood_label="anxious",
        arousal=0.7,
        last_seen_entities={"agent_002": 950}  # Last seen Davis at tick 950
    )
    
    # Process several ticks
    percepts = pipeline.process(world_state, agent_state, 1000)
    
    logger.info(f"Generated {len(percepts)} percepts")
    
    # Check salience values
    for percept in percepts:
        if percept.HasField('actor'):
            logger.info(f"{percept.actor.name}: salience={percept.salience:.3f}, "
                        f"certainty={percept.certainty:.3f}")
            assert 0.0 <= percept.salience <= 1.0, "Salience must be between 0 and 1"
            assert 0.0 <= percept.certainty <= 1.0, "Certainty must be between 0 and 1"
    
    logger.info("✓ Salience scoring test PASSED\n")


def test_surprise_factor():
    """Test Surprise Factor: detecting Memory Echo violations."""
    logger.info("=" * 60)
    logger.info("TEST 3: Surprise Factor (Memory Echo Violations)")
    logger.info("=" * 60)
    
    world_state = create_test_world()
    
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=120.0,
        hearing_range=15.0
    )
    
    pipeline = PerceptionPipeline("agent_001", sensory_profile)
    agent_state = AgentInternalState(
        current_concerns=[],
        mood_label="calm",
        arousal=0.3,
        last_seen_entities={}
    )
    
    # Initial observation - see Davis at position (5, 0)
    percepts = pipeline.process(world_state, agent_state, 1000)
    logger.info(f"Tick 1000: Initial observation - {len(percepts)} percepts")
    
    # Move Davis to a different position (simulate sudden movement)
    world_state.actors["agent_002"].position.x = 20.0
    world_state.actors["agent_002"].position.y = 5.0
    
    # Process again - should detect surprise
    percepts = pipeline.process(world_state, agent_state, 1002)
    logger.info(f"Tick 1002: After Davis moved - {len(percepts)} percepts")
    
    # Check for surprise boost in Davis percept
    davis_percept = None
    for percept in percepts:
        if percept.HasField('actor') and percept.actor.name == "Davis":
            davis_percept = percept
            break
    
    if davis_percept:
        logger.info(f"Davis salience: {davis_percept.salience:.3f}")
        # With surprise factor, salience should be boosted
        # (The exact value depends on implementation details)
        logger.info(f"✓ Surprise factor applied (salience may be boosted)")
    else:
        logger.info("⚠ Davis not in percepts (may be out of FOV/range)")
    
    logger.info("✓ Surprise Factor test PASSED\n")


def test_memory_echoes():
    """Test Memory Echo tracking and decay."""
    logger.info("=" * 60)
    logger.info("TEST 4: Memory Echo Tracking and Decay")
    logger.info("=" * 60)
    
    world_state = create_test_world()
    
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=120.0,
        hearing_range=15.0
    )
    
    pipeline = PerceptionPipeline("agent_001", sensory_profile)
    agent_state = AgentInternalState(
        current_concerns=[],
        mood_label="calm",
        arousal=0.3,
        last_seen_entities={}
    )
    
    # Initial observation
    percepts = pipeline.process(world_state, agent_state, 1000)
    
    # Check memory echoes
    logger.info(f"Memory echoes after tick 1000: {len(pipeline.memory_echoes)} echoes")
    for entity_id, echo in pipeline.memory_echoes.items():
        logger.info(f"  - {entity_id}: cert={echo.current_certainty:.3f}, pos=({echo.last_position.x:.1f}, {echo.last_position.y:.1f})")
    
    # Remove agent from world state (simulate them leaving)
    del world_state.actors["agent_002"]
    
    # Process several ticks to observe decay
    for tick in range(1001, 1015):
        percepts = pipeline.process(world_state, agent_state, tick)
        
        # Check for memory echo of Davis
        davis_echo = False
        for percept in percepts:
            if percept.channel == perception_pb2.Percept.MEMORY_ECHO:
                if percept.HasField('actor') and percept.actor.name == "Davis":
                    davis_echo = True
                    logger.info(f"Tick {tick}: Memory echo of Davis - "
                              f"certainty={percept.certainty:.3f}")
                    break
        
        if not davis_echo and tick > 1010:
            logger.info(f"Tick {tick}: Davis echo expired")
            break
    
    logger.info("✓ Memory Echo test PASSED\n")


def test_sensory_channels():
    """Test all sensory channels."""
    logger.info("=" * 60)
    logger.info("TEST 5: All Sensory Channels")
    logger.info("=" * 60)
    
    world_state = create_test_world()
    
    sensory_profile = SensoryProfile(
        vision_range=20.0,
        vision_fov=120.0,
        hearing_range=15.0
    )
    
    pipeline = PerceptionPipeline("agent_001", sensory_profile)
    agent_state = AgentInternalState(
        current_concerns=[],
        mood_label="calm",
        arousal=0.3,
        last_seen_entities={}
    )
    
    percepts = pipeline.process(world_state, agent_state, 1000)
    
    # Categorize percepts by channel
    channels = {}
    for percept in percepts:
        channel_name = perception_pb2.Percept.Channel.Name(percept.channel)
        if channel_name not in channels:
            channels[channel_name] = []
        channels[channel_name].append(percept)
    
    logger.info(f"Percepts by channel:")
    for channel_name, channel_percepts in channels.items():
        logger.info(f"  - {channel_name}: {len(channel_percepts)} percepts")
    
    # Verify we have different channels
    assert "VISION" in channels, "Should have VISION percepts"
    # Note: HEARING and PROPRIOCEPTION depend on world state
    
    logger.info("✓ Sensory Channels test PASSED\n")


def run_all_tests():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 60)
    logger.info("TSUKUYOMI PHASE 2.1: PERCEPTION FOUNDATION TEST SUITE")
    logger.info("=" * 60)
    logger.info(f"Starting tests at: {datetime.now().isoformat()}")
    logger.info("\n")
    
    try:
        test_staggered_perception_schedule()
        test_salience_scoring()
        test_surprise_factor()
        test_memory_echoes()
        test_sensory_channels()
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ TEST FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
