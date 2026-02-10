import asyncio
import logging
import uuid
import json
from typing import Dict
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto import core_pb2, common_pb2, perception_pb2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRelationship")

async def test_relationship_tracking():
    actor_id = "juror_8"
    profile = {
        "name": "Davis",
        "backstory": "An architect who believes in reasonable doubt.",
        "personality_baseline": {"valence": 0.1, "arousal": 0.3},
        "personality_bias": {"confirmation_bias": 0.8},
        "sensory_profile": {"vision_range": 10.0}
    }
    
    # We won't call run() because it needs a gRPC server.
    # Instead, we'll manually feed ticks to _process_tick.
    brain = AgentBrain(actor_id, profile)
    
    # Mock TickState
    tick_state = core_pb2.TickState(tick_number=100)
    tick_state.world_state.tick_number = 100
    
    # Add myself and another actor
    tick_state.world_state.actors[actor_id].CopyFrom(core_pb2.Actor(
        id=actor_id, name="Davis", position=common_pb2.Vector2(x=0, y=0), state="IDLE"
    ))
    
    other_id = "juror_3"
    tick_state.world_state.actors[other_id].CopyFrom(core_pb2.Actor(
        id=other_id, name="Angry Man", position=common_pb2.Vector2(x=1, y=1), state="SPEAKING"
    ))
    
    # 1. Test Direct Address
    logger.info("--- Testing Direct Address ---")
    
    # We need to mock the PerceptionPipeline.process to return a direct address
    # Actually, PerceptionPipeline.process extracts speech from actor states.
    # PerceptionPipeline._process_hearing checks if "speaking" is in actor.state.
    
    # Feed tick to brain
    await brain._process_tick(tick_state)
    
    # Check affinity
    affinity = brain.relationships.get_affinity(other_id)
    logger.info(f"Affinity with {other_id} after hearing them: {affinity:.4f}")
    
    # 2. Test context generation
    context = brain.relationships.to_llm_context()
    logger.info(f"LLM Context:\n{context}")
    
    assert other_id in context
    assert affinity > 0 # Since speaking gives 0.01
    
    # 3. Test Gossip
    logger.info("--- Testing Gossip Impact ---")
    from tsukuyomi.brain.GossipProtocol import get_gossip_protocol
    gossip_protocol = get_gossip_protocol()
    gossip_protocol.base_leakage_probability = 1.0 # Force leakage
    
    # Register a thought for juror_3
    gossip_protocol.register_deliberation(
        other_id, "I think he's guilty!", "EMOTE", 100, 
        world_state_context={"actors": {actor_id: {"position": {"x":0, "y":0}}, other_id: {"position": {"x":1, "y":1}}}}
    )
    
    # Register a thought for juror_8 so they can overhear
    gossip_protocol.register_deliberation(
        actor_id, "I'm thinking too.", "IDLE", 100,
        world_state_context={"actors": {actor_id: {"position": {"x":0, "y":0}}, other_id: {"position": {"x":1, "y":1}}}}
    )
    
    # Process gossip (Juror 8 should overhear)
    gossip_protocol.process_gossip(101)
    
    # Juror 8 processes tick 101
    tick_state_2 = core_pb2.TickState(tick_number=101)
    tick_state_2.world_state.CopyFrom(tick_state.world_state)
    await brain._process_tick(tick_state_2)
    
    affinity_2 = brain.relationships.get_affinity(other_id)
    logger.info(f"Affinity with {other_id} after gossip: {affinity_2:.4f}")
    assert affinity_2 > affinity
    
    logger.info("Relationship tracking test passed!")

if __name__ == "__main__":
    asyncio.run(test_relationship_tracking())
