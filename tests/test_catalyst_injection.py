"""
Integration Test for Catalyst Injection System

Verifies that:
1. Drama Director triggers Catalyst System when Tension is low.
2. Catalyst System successfully adds events to FateEngine.
3. Global events are visible in the WorldState snapshot.
"""

import asyncio
import logging
import uuid
import sys
import os
import json

# Set PYTHONPATH to include the tsukuyomi packages
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "tsukuyomi"))

from tsukuyomi.environment.core.engine import FateEngine
from tsukuyomi.transport.grpc.server import GrpcServer
from tsukuyomi.transport.grpc.client import FateEngineClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestCatalyst")

async def run_catalyst_test():
    # 1. Start Engine and Server
    engine = FateEngine(tick_rate=20, db_path=None) # No persistence for test
    server = GrpcServer(engine, host="127.0.0.1", port=50056)
    await server.start()
    
    # Run engine in background
    engine_task = asyncio.create_task(engine.run())
    
    # 2. Connect Client
    client = FateEngineClient("127.0.0.1:50056")
    await client.connect()
    
    logger.info("--- Testing Catalyst Trigger via Low Tension ---")
    
    # Force low tension by setting threshold high
    server.servicer.drama_director.boredom_threshold = 0.9
    server.servicer.drama_director.catalyst_cooldown = 1 # No cooldown
    
    # Wait for processing (several ticks)
    await asyncio.sleep(2.0)
    
    # 3. Check FateEngine for global events
    events = engine.world_state.global_events
    logger.info(f"Global Events in FateEngine: {events}")
    
    assert len(events) > 0, "There should be at least one catalyst event in FateEngine"
    assert "CATALYST" in events[0], "Event should be formatted as a CATALYST"
    
    # 4. Check Client view
    world_state = await client.get_world_state()
    logger.info(f"Global Events in Client WorldState: {world_state.global_events}")
    
    assert len(world_state.global_events) > 0, "Client should see the catalyst events"
    
    # Cleanup
    engine.stop()
    await server.stop()
    await engine_task
    logger.info("Test Complete.")

if __name__ == "__main__":
    asyncio.run(run_catalyst_test())
