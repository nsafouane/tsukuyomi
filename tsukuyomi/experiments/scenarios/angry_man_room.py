import asyncio
import logging
import json
import os
import signal
import subprocess
from typing import Dict, List
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.experiments.scenarios.TanitBridge import TanitBridge

# Configuration
LOG_DIR = "/root/.openclaw/workspace/tsukuyomi/experiments/logs"
PROFILES_PATH = "/root/.openclaw/workspace/tsukuyomi/experiments/profiles/juror_profiles.json"
CASE_PATH = "/root/.openclaw/workspace/tsukuyomi/experiments/scenarios/angry_man_room_case.json"

async def run_experiment():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AngryManExperiment")
    
    # 1. Load Data
    with open(PROFILES_PATH, "r") as f:
        profiles = json.load(f)
    with open(CASE_PATH, "r") as f:
        case_data = json.load(f)

    logger.info("🏛️ Launching 'The Angry Man Room' Experiment...")

    # 2. Start the Fate Engine Server
    # Ensure it uses a fresh/clean DB for the experiment
    db_path = os.path.join(LOG_DIR, "experiment_history.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    server_env = os.environ.copy()
    server_env["PYTHONPATH"] = "/root/.openclaw/workspace" + os.pathsep + server_env.get("PYTHONPATH", "")

    server_process = subprocess.Popen(
        ["python3", "-m", "tsukuyomi.proto.grpc_server", "--port", "50051", "--db", db_path],
        env=server_env
    )
    await asyncio.sleep(3) # Warm up

    # 3. Initialize Agents
    agent_tasks = []
    
    # 4 Native Jurors (Believers)
    for profile in profiles[:4]:
        # Inject case data into backstory
        profile['backstory'] += f"\nCASE DETAILS: {json.dumps(case_data['evidence'])}"
        brain = AgentBrain(actor_id=f"juror-{profile['juror_id']}", profile=profile)
        agent_tasks.append(asyncio.create_task(brain.run()))
        logger.info(f"👤 Juror {profile['name']} joined.")

    # 1 Guest Agent (Tanit - The Researcher)
    tanit_profile = profiles[4]
    tanit_profile['backstory'] += f"\nCASE DETAILS: {json.dumps(case_data['evidence'])}"
    bridge = TanitBridge(actor_id="tanit-guest-001")
    agent_tasks.append(asyncio.create_task(bridge.run()))
    logger.info(f"🏛️ Tanit (Guest) joined as co-researcher.")

    # 4. Run for the duration (20 mins = 1200 seconds)
    duration = 1200 
    logger.info(f"⏳ Simulation running for {duration} seconds...")
    
    # Analysis: Start logging Tanit's co-researcher thoughts at specific milestones
    async def log_milestones():
        milestones = [
            (60, "initial_tension", "The deliberation has begun. The Foreman is trying to establish order, but Juror 3 is already showing signs of impatience."),
            (300, "first_crack", "5 minutes in. We are seeing the first signs of reasonable doubt surfacing in the episodic memories."),
            (600, "mid_point", "10 minutes mark. The room is hot. The Stockbroker remains unmoved by emotional pleas."),
            (1140, "final_stress", "1 minute remaining. The stress of the time limit is forcing a convergence.")
        ]
        for delay, cat, thought in milestones:
            await asyncio.sleep(delay)
            bridge._log_researcher_thought(cat, thought)

    asyncio.create_task(log_milestones())

    try:
        await asyncio.sleep(duration)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("🛑 Experiment Time Up. Shutting down...")
        for task in agent_tasks:
            task.cancel()
        
        server_process.send_signal(signal.SIGINT)
        server_process.wait()
        logger.info("🏁 Data saved to experiments/logs/")

if __name__ == "__main__":
    asyncio.run(run_experiment())
