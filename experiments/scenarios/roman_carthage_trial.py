"""
PHASE 13: Roman-Carthage Trial Scenario
==========================================

Multi-room legal trial scenario ported from "Angry Man Room" logic.
Integrates spatial_logic for room transitions and character profiles from JSON.
"""

import asyncio
import json
import logging
import uuid
import sys
import os
from pathlib import Path

# Ensure tsukuyomi package is in path
sys.path.append("/root/.openclaw/workspace/tsukuyomi")

from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto.grpc_server import GrpcServer as FateEngineServer
from tsukuyomi.proto.fate_engine import FateEngine
from tsukuyomi.proto.physics.spatial_logic import SpatialLogic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RomanCarthageTrial")

# Paths
SCENARIO_DIR = Path("/root/.openclaw/workspace/tsukuyomi/experiments/scenarios")
PROFILES_DIR = Path("/root/.openclaw/workspace/tsukuyomi/experiments/profiles")

async def load_scenario():
    """Load scenario definition and character profiles."""
    scenario_path = SCENARIO_DIR / "roman_carthage_trial.json"
    profiles_path = PROFILES_DIR / "roman_carthage_trial_characters.json"
    
    with open(scenario_path, 'r') as f:
        scenario = json.load(f)
    
    with open(profiles_path, 'r') as f:
        characters = json.load(f)
    
    return scenario, characters

async def run_scenario():
    # 1. Start Fate Engine
    engine = FateEngine(tick_rate=20, db_path="roman_carthage_trial.db")
    server = FateEngineServer(engine, port=50052)
    
    server_task = asyncio.create_task(server.start())
    engine_task = asyncio.create_task(engine.run())
    
    logger.info("=== ROMAN-CARTHAGE TRIAL: The Dispute of the Purple Dye ===")
    logger.info(f"Location: {scenario['location']}")
    
    await asyncio.sleep(1) # Allow server to bind

    # 2. Load Scenario and Characters
    scenario, characters = await load_scenario()
    
    # 3. Initialize Agents with Brain
    brains = []
    actor_room_assignments = {}
    
    # Map character roles to starting rooms
    # Plaintiff, Defendant, Jurors start in courtroom_main
    # Public starts in lobby
    for char in characters:
        actor_id = str(uuid.uuid4())
        
        # Determine starting room
        if char["role"] in ["plaintiff", "defendant", "juror"]:
            start_room = "courtroom_main"
        else:
            start_room = "lobby"  # Public spectators
        
        actor_room_assignments[actor_id] = {
            "room": start_room,
            "position": {"x": 10.0, "y": 5.0}  # Default courtroom center
        }
        
        # Create AgentBrain
        brain = AgentBrain(actor_id, char)
        brains.append(asyncio.create_task(brain.run()))
        logger.info(f"Launched Brain: {char['name']} ({char['faction']} {char['role']}) → Room: {start_room}")

    # 4. Log Scenario Details
    logger.info(f"\n--- CASE DETAILS ---")
    logger.info(f"Plaintiff: {scenario['case']['plaintiff']}")
    logger.info(f"Defendant: {scenario['case']['defendant']}")
    logger.info(f"Charge: {scenario['case']['charge']}")
    logger.info(f"Evidence: {len(scenario['case']['evidence'])} items presented")
    
    # 5. Log Room Configuration
    logger.info(f"\n--- ROOM CONFIGURATION ---")
    for room in scenario['rooms']:
        logger.info(f"  [{room['id']}] {room['name']}")
        logger.info(f"      {room['description']}")
    
    # 6. Run Scenario for extended duration (600 ticks = 30 seconds)
    # This allows for: opening arguments, evidence presentation, juror deliberation
    logger.info(f"\n=== TRIAL IN PROGRESS (600 ticks / 30 seconds) ===")
    
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("Trial interrupted by user.")
    finally:
        logger.info("\n=== SHUTTING DOWN SCENARIO ===")
        # Cancel brains first to stop their tick streams
        for b in brains:
            b.cancel()
        await asyncio.gather(*brains, return_exceptions=True)
        
        # Stop engine and server
        engine.stop()
        if server:
            await server.stop()
        
        # Allow loop to settle
        await asyncio.sleep(1)
        
        logger.info("Trial complete. Database saved to: roman_carthage_trial.db")

if __name__ == "__main__":
    scenario, _ = asyncio.run(load_scenario())
    asyncio.run(run_scenario())
