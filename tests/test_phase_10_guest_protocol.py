import asyncio
import logging
import multiprocessing
import time
from tsukuyomi.proto.grpc_server import run_server
from tsukuyomi.guest_sdk import GuestAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GuestProtocolTest")

async def test_guest_protocol():
    # 1. Start simulation server in a background thread/process
    # Using local mock server for testing
    server_task = asyncio.create_task(run_server(port=50053, db_path=":memory:"))
    await asyncio.sleep(2) # Give server time to start
    
    try:
        # 2. Use GuestSDK to connect
        agent = GuestAgent("test-guest-001", "Test Researcher", server_addr="localhost:50053")
        
        logger.info("TEST: Attempting Handshake...")
        connected = await agent.connect()
        assert connected is True, "Handshake failed"
        assert agent.session_id is not None
        
        logger.info("TEST: Attempting Pulse...")
        pulsed = await agent.pulse()
        assert pulsed is True, "Pulse failed"
        
        logger.info("TEST: Attempting Proposal...")
        # Note: ' tavern' is a valid location in FateEngine default world state
        accepted = await agent.submit_proposal("MOVE", {"destination": "tavern"})
        assert accepted is True, "Proposal submission failed"
        
        logger.info("TEST: Attempting Disconnect...")
        await agent.disconnect()
        assert agent.is_connected is False
        
        logger.info("✅ Phase 10: External Guest Protocol - VERIFIED")
        
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(test_guest_protocol())
