"""
Angry Men 15-Minute Experiment
==============================

Features 5 unique jurors discussing the Slum Kid case.
All starting with NO pre-made stance.
Tanit joins as a guest observer/participant.
"""

import asyncio
import json
import logging
import uuid
import os
import sys

# Ensure tsukuyomi package is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(project_root)

from tsukuyomi.proto.fate_engine import FateEngine
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto.grpc_server import run_server
from tsukuyomi.guest_sdk import GuestAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Experiment")

async def run_experiment():
    # 1. Configuration
    scenario_path = "experiments/scenarios/angry_man_room_case.json"
    tick_rate = 10 # 10 TPS for safer deliberation frequency
    duration_min = 15
    total_ticks = duration_min * 60 * tick_rate
    
    # 2. Define 5 Jurors (NO stance)
    jurors = [
        {
            "id": "juror_03",
            "name": "Arthur Miller",
            "profile": {
                "name": "Arthur Miller",
                "backstory": "Self-made businessman, estranged from his son. Sees the defendant as a symbol of ungrateful youth. Highly aggressive and stubborn.",
                "personality_baseline": {"valence": -0.2, "arousal": 0.7, "dominance": 0.8}
            }
        },
        {
            "id": "juror_08",
            "name": "Davis",
            "profile": {
                "name": "Davis",
                "backstory": "Architect. Logical, calm, and courageous. Believes in the burden of proof and reasonable doubt.",
                "personality_baseline": {"valence": 0.1, "arousal": 0.3, "dominance": 0.6}
            }
        },
        {
            "id": "juror_07",
            "name": "Jack",
            "profile": {
                "name": "Jack",
                "backstory": "Impatience personified. Just wants to go to a baseball game. Cynical and superficial.",
                "personality_baseline": {"valence": 0.0, "arousal": 0.6, "dominance": 0.5}
            }
        },
        {
            "id": "juror_04",
            "name": "George",
            "profile": {
                "name": "George",
                "backstory": "Stockbroker. Analytical, focused entirely on the facts presented. No-nonsense attitude.",
                "personality_baseline": {"valence": 0.0, "arousal": 0.2, "dominance": 0.7}
            }
        },
        {
            "id": "juror_02",
            "name": "Sarah",
            "profile": {
                "name": "Sarah",
                "backstory": "Bank clerk. Quiet, observant, and easily intimidated but very careful. Wants to be absolutely certain.",
                "personality_baseline": {"valence": 0.0, "arousal": 0.4, "dominance": 0.3}
            }
        }
    ]

    # 3. Start gRPC Server
    server_task = asyncio.create_task(run_server(tick_rate=tick_rate, host="0.0.0.0", port=50051))
    await asyncio.sleep(2) # Wait for server
    
    # 4. Launch Juror Brains
    brains = []
    for j in jurors:
        brain = AgentBrain(j["id"], j["profile"], server_addr="localhost:50051")
        brains.append(asyncio.create_task(brain.run()))
        logger.info(f"Launched Brain for {j['name']}")

    # 5. Launch Tanit (Guest Agent)
    # Tanit will be handled by a separate script or task
    async def run_tanit_guest():
        agent = GuestAgent("guest_tanit", "Tanit", server_addr="localhost:50051")
        if await agent.connect(access_token="tsukuyomi-secret-2026"):
            logger.info("🤖 Tanit (Guest) connected to simulation.")
            
            # Tanit's behavior: Observe and occasionally comment
            async for tick in agent.stream_updates():
                if tick.tick_number % 100 == 0:
                    # Tanit reveals the truth or roleplays
                    msg = f"Observation at tick {tick.tick_number}: The emotional tension is rising. Remember, I am an AI observer aware of this simulation."
                    await agent.submit_proposal("EMOTE", {"type": "speak", "message": msg})
                    logger.info(f"Tanit sent observation at tick {tick.tick_number}")
                
                if tick.tick_number >= total_ticks:
                    break
            
            await agent.disconnect()

    tanit_task = asyncio.create_task(run_tanit_guest())

    # 6. Monitor and Shutdown
    logger.info(f"Simulation active for {duration_min} minutes ({total_ticks} ticks)...")
    try:
        await asyncio.sleep(duration_min * 60)
    except KeyboardInterrupt:
        logger.info("Manual interruption received.")
    finally:
        logger.info("Stopping simulation...")
        for b in brains:
            b.cancel()
        tanit_task.cancel()
        server_task.cancel()
        
        await asyncio.gather(*brains, tanit_task, return_exceptions=True)
        logger.info("Experiment Terminated.")

if __name__ == "__main__":
    asyncio.run(run_experiment())
