# test_mvp_complete.py - The "Boss" Test for Tsukuyomi MVP
import asyncio
import uuid
import os
import signal
import subprocess
import time
import pytest
from tsukuyomi.proto.grpc_client import FateEngineClient

# Configuration
SERVER_ADDR = "localhost:50051"
DB_PATH = "tsukuyomi_history.db"

async def run_scenario():
    print("\n🚀 Starting MVP Integrated Scenario Test...")
    
    # 1. Cleanup old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️ Removed old database: {DB_PATH}")

    # 2. Start the gRPC Server in a separate process
    server_process = subprocess.Popen(
        ["python3", "-m", "tsukuyomi.proto.grpc_server", "--port", "50051", "--seed", "123"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("🛰️ Fate Engine Server started.")
    
    # Give server time to warm up
    await asyncio.sleep(2)
    
    client = FateEngineClient(SERVER_ADDR)
    try:
        if not await client.connect():
            print("❌ Failed to connect to server.")
            return

        # 3. Verify Initial World State
        world = await client.get_world_state()
        print(f"🌍 World State @ Tick {world.tick_number} - Objects: {len(world.objects)}")
        
        # 4. Spawn 2 Actors and perform actions
        actors = list(world.actors.keys())
        actor_a = actors[0] # Alice
        actor_b = actors[1] # Bob
        
        print(f"🏃 Actor {actor_a} moving to tavern...")
        await client.move(actor_a, "tavern")
        
        print(f"🏃 Actor {actor_b} moving to market_square...")
        await client.move(actor_b, "market_square")
        
        # Wait for movement
        await asyncio.sleep(1)
        
        # 5. Test Collection (Task 1 fix)
        # Alice is now at tavern, hammer_tool is at (10.5, 5.5)
        print(f"🎒 Actor {actor_a} attempting to collect hammer_tool...")
        await client.submit_proposal(actor_a, "COLLECT", {"target_id": "hammer_tool"})
        
        await asyncio.sleep(1)
        
        # Verify collection
        world = await client.get_world_state()
        alice = world.actors[actor_a]
        if "hammer_tool" in alice.inventory:
            print("✅ Collection Successful: Hammer is in Alice's inventory.")
        else:
            print("❌ Collection Failed.")

        # 6. Shutdown and Restart Server (Persistence Test)
        print("🛑 Shutting down server for persistence test...")
        server_process.send_signal(signal.SIGINT)
        server_process.wait()
        
        print("🔄 Restarting server...")
        server_process = subprocess.Popen(
            ["python3", "-m", "tsukuyomi.proto.grpc_server", "--port", "50051", "--seed", "123"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        await asyncio.sleep(2)
        
        # Reconnect
        await client.connect()
        world = await client.get_world_state()
        print(f"🌍 Resumed World @ Tick {world.tick_number}")
        
        # Verify Alice still has the hammer
        alice = world.actors[actor_a]
        if "hammer_tool" in alice.inventory:
            print("✅ Persistence Successful: Alice still has the hammer after restart.")
        else:
            print("❌ Persistence Failed.")

    except Exception as e:
        print(f"🔥 Test Error: {e}")
    finally:
        print("🧹 Cleaning up...")
        server_process.send_signal(signal.SIGINT)
        server_process.wait()
        await client.disconnect()
        print("🏁 Test Complete.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
