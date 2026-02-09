import asyncio
import logging
import json
import os
import signal
import subprocess
import uuid
from typing import Dict, List
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.experiments.scenarios.TanitBridge import TanitBridge
from tsukuyomi.proto import core_pb2, common_pb2

# Configuration
LOG_DIR = "/root/.openclaw/workspace/tsukuyomi/experiments/logs"
PROFILES_PATH = "/root/.openclaw/workspace/tsukuyomi/tsukuyomi/experiments/profiles/juror_profiles.json"
CASE_PATH = "/root/.openclaw/workspace/tsukuyomi/tsukuyomi/experiments/scenarios/evidence_room_case.json"

async def run_experiment():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("EvidenceRoomTrial")
    
    # 1. Load Data
    with open(PROFILES_PATH, "r") as f:
        profiles = json.load(f)
    with open(CASE_PATH, "r") as f:
        case_data = json.load(f)

    logger.info("🏛️ Launching 'The Evidence Room' Trial (Trial 3)...")

    # 2. Start the Fate Engine Server
    db_path = os.path.join(LOG_DIR, "experiment_history.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    server_env = os.environ.copy()
    server_env["PYTHONPATH"] = "/root/.openclaw/workspace/tsukuyomi" + os.pathsep + server_env.get("PYTHONPATH", "")
    server_env["SCENARIO_JSON"] = CASE_PATH

    # We start the server as a subprocess so it has its own event loop
    server_process = subprocess.Popen(
        ["python3", "-m", "tsukuyomi.proto.grpc_server", "--port", "50051", "--db", db_path],
        env=server_env
    )
    await asyncio.sleep(3) # Warm up

    # 3. Inject Evidence Objects directly via a temporary gRPC client or by modifying the engine if we had access
    # Since we're launching the server as a subprocess, we'll assume the engine starts empty.
    # In a real scenario, we'd have a 'ScenarioManager' register these.
    # For this trial, I will have the Agents 'see' the object which is already in the world state if the server was initialized with it.
    # FIX: Since I can't easily reach into the subprocess, I'll update the server to load a scenario file.
    # Actually, the simplest way is to have one agent 'create' or 'discover' it, but the best way is server-side.
    
    # 4. Initialize Agents
    agent_tasks = []
    
    # 4 Native Jurors
    for profile in profiles[:4]:
        # Provide the initial 'leaning' and backstory
        profile['backstory'] += f"\nCASE OBJECTIVE: {case_data['objective']}"
        brain = AgentBrain(actor_id=f"juror-{profile['juror_id']}", profile=profile)
        agent_tasks.append(asyncio.create_task(brain.run()))
        logger.info(f"👤 Juror {profile['name']} joined.")

    # 1 Guest Agent (Tanit - The Researcher)
    bridge = TanitBridge(actor_id="tanit-guest-001")
    agent_tasks.append(asyncio.create_task(bridge.run()))
    logger.info(f"🏛️ Tanit (Guest) joined.")

    # 5. Run for 15 minutes (900 seconds)
    duration = 900 
    logger.info(f"⏳ Simulation running for {duration} seconds...")
    
    try:
        await asyncio.sleep(duration)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("🛑 Trial Time Up. Shutting down...")
        for task in agent_tasks:
            task.cancel()
        
        server_process.send_signal(signal.SIGINT)
        server_process.wait()
        logger.info("🏁 Data saved to experiments/logs/")

if __name__ == "__main__":
    asyncio.run(run_experiment())
