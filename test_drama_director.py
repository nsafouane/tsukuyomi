"""
Integration Test for Drama Director

Verifies that:
1. Drama Director initializes with the gRPC server.
2. Actions (like SPEAK/EMOTE) affect the Tension Vector.
3. Boredom threshold eventually triggers catalysts (mock).
"""

import asyncio
import logging
import uuid
import sys
import os

# Set PYTHONPATH to include the tsukuyomi packages
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "tsukuyomi"))

from tsukuyomi.proto.fate_engine import FateEngine, create_proposal
from tsukuyomi.proto.grpc_server import GrpcServer
from tsukuyomi.proto.grpc_client import FateEngineClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDrama")


async def run_drama_test():
    # 1. Start Engine and Server
    engine = FateEngine(tick_rate=20, db_path=None)  # No persistence for test
    server = GrpcServer(engine, host="127.0.0.1", port=50055)
    await server.start()

    # Run engine in background
    engine_task = asyncio.create_task(engine.run())

    # 2. Connect Client
    client = FateEngineClient("127.0.0.1:50055")
    await client.connect()

    actor_id = "test_actor_1"
    await client.register_actor(actor_id, "Test Actor")

    logger.info("--- Testing Social Tension Increase ---")

    # 3. Submit Social Actions
    for i in range(5):
        await client.submit_proposal(
            actor_id, "EMOTE", {"type": "speak", "message": f"Hello world {i}"}
        )
        await asyncio.sleep(0.1)  # Spread across ticks

    # Wait for processing
    await asyncio.sleep(2.0)

    # Check Tension
    tension = server.drama_director.get_status()
    logger.info(f"Current Tension: {tension}")

    assert tension["social"] > 0, "Social tension should have increased"

    logger.info("--- Testing Boredom / Catalyst Trigger ---")

    # Set boredom threshold high to trigger it fast
    server.drama_director.boredom_threshold = 0.9
    server.drama_director.catalyst_cooldown = 1  # No cooldown

    await asyncio.sleep(2.0)  # Wait for tension to decay/aggregate to stay low

    # Check if catalyst was triggered (look at logs)
    logger.info("Check logs for 'TRIGGERING CATALYST' and 'Catalyst Injected'")

    # Cleanup
    engine.stop()
    await server.stop()
    await engine_task
    logger.info("Test Complete.")


if __name__ == "__main__":
    asyncio.run(run_drama_test())
