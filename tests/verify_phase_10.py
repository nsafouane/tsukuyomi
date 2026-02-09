import asyncio
import logging
import grpc
import sys
import os

# Manual path adjustments to fix environment issues in this specific setup
sys.path.insert(0, '/root/.openclaw/workspace/tsukuyomi/proto')
sys.path.insert(0, '/root/.openclaw/workspace/tsukuyomi')

from tsukuyomi.proto import guest_api_pb2
from tsukuyomi.proto import guest_api_pb2_grpc
from tsukuyomi.proto import core_pb2
from tsukuyomi.proto.grpc_server import run_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GuestVerify")

async def verify_guest_flow():
    # 1. Start Server in background
    # Using a non-standard port to avoid conflicts if a main server is running
    server_task = asyncio.create_task(run_server(port=50055, db_path=":memory:"))
    await asyncio.sleep(2) # Give server time to start
    
    try:
        # 2. Initialize Guest Client
        import guest_client
        client = guest_client.TsukuyomiGuestClient(server_address="localhost:50055")
        
        # 3. Perform Handshake
        logger.info("Step 1: Handshake")
        success = await client.connect(
            agent_id="guest-verifier-01",
            agent_name="Verifier Bot",
            access_token="tsukuyomi-secret-2026"
        )
        
        if not success:
            logger.error("Handshake failed!")
            return False
            
        logger.info("Handshake SUCCESS")
        
        # 4. Verify Action Submission
        logger.info("Step 2: Action Submission")
        response = await client.submit_action("EMOTE", {"type": "salute"})
        if response.accepted:
            logger.info("Action ACCEPTED")
        else:
            logger.error(f"Action REJECTED: {response.message}")
            return False
            
        # 5. Verify Subscription (Basic Check)
        logger.info("Step 3: Subscription (Streaming 1 tick)")
        # In current prototype, subscribe yields one placeholder
        async for tick in client.subscribe():
            logger.info(f"Received Tick: {tick.tick_number}")
            break
        
        logger.info("Subscription flow VERIFIED")
            
        # 6. Disconnect
        logger.info("Step 4: Disconnect")
        await client.disconnect(reason="Verification complete")
        logger.info("Guest verification flow COMPLETE")
        return True

    except Exception as e:
        logger.exception(f"Verification failed with error: {e}")
        return False
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    result = asyncio.run(verify_guest_flow())
    if result:
        print("\n✅ PHASE 10 VERIFICATION PASSED")
    else:
        print("\n❌ PHASE 10 VERIFICATION FAILED")
        exit(1)
