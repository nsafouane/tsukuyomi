"""
Roman-Carthage Legal Trial Experiment
======================================

A simulation setup for the LLM V1.0 Integration testing.
Features Scipio Aemilianus (Prosecutor) vs Hasdrubal (Defendant).
"""

import asyncio
import json
import logging
import os
from tsukuyomi.proto.fate_engine import FateEngine
from tsukuyomi.brain.AgentBrain import AgentBrain

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Experiment")

async def run_experiment():
    # 1. Initialize Engine with Scenario
    scenario_path = "experiments/scenarios/roman_carthage_trial.json"
    engine = FateEngine(tick_rate=10, scenario_config=scenario_path)
    
    # 2. Load Character Profiles
    with open("experiments/profiles/roman_carthage_profiles.json", "r") as f:
        profiles = json.load(f)
    
    # 3. Initialize Agents
    scipio_brain = AgentBrain("actor_scipio", profiles["scipio_aemilianus"], server_addr="localhost:50051", fate_engine=engine)
    hasdrubal_brain = AgentBrain("actor_hasdrubal", profiles["hasdrubal_the_boetharch"], server_addr="localhost:50051", fate_engine=engine)
    
    # 4. Start Simulation
    logger.info("🏛️ Starting Roman-Carthage Legal Trial Experiment...")
    
    # In a real setup, we'd start the gRPC server and have clients connect.
    # For this fresh experiment, we'll run the brains as tasks that connect to the engine logic directly or via local client.
    
    # Let's use the actual brain run loops which connect to the engine via gRPC client
    # Note: This requires the gRPC server to be running.
    
    # We will spawn the server in the background
    from tsukuyomi.proto.grpc_server import run_server
    
    server_task = asyncio.create_task(run_server(tick_rate=10, scenario_config=scenario_path))
    await asyncio.sleep(2) # Give server time to start
    
    # Run brains
    try:
        await asyncio.gather(
            scipio_brain.run(),
            hasdrubal_brain.run()
        )
    except KeyboardInterrupt:
        logger.info("Stopping experiment...")
    finally:
        engine.stop()

if __name__ == "__main__":
    asyncio.run(run_experiment())
