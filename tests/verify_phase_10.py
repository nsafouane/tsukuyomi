import asyncio
import logging
import grpc
import sys
import os
from pathlib import Path

# Relative path setup
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "proto"))
sys.path.insert(0, str(project_root))

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
        from tsukuyomi.guest_sdk import GuestAgent
        client = GuestAgent("guest-verifier-01", "Verifier Bot", server_addr="localhost:50055")
        
        # 3. Perform Handshake
        logger.info("Step 1: Handshake")
        # Use env var or fall back to default
        token = os.getenv("TSUKUYOMI_GUEST_TOKEN", "tsukuyomi-secret-2026")
        success = await client.connect(access_token=token)
        
        if not success:
            logger.error("Handshake failed!")
            return False
            
        logger.info("Handshake SUCCESS")
        
        # 4. Verify Action Submission
        logger.info("Step 2: Action Submission")
        accepted = await client.submit_proposal("EMOTE", {"type": "salute"})
        if accepted:
            logger.info("Action ACCEPTED")
        else:
            logger.error(f"Action REJECTED")
            return False
            
        # 5. Verify Subscription (Basic Check)
        logger.info("Step 3: Subscription (Streaming 1 tick)")
        async for tick in client.stream_updates():
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
