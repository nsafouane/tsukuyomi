import asyncio
import logging
import uuid
import sys
import os
from pathlib import Path

# Relative path setup
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto.grpc_server import GrpcServer as FateEngineServer
from tsukuyomi.proto.fate_engine import FateEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AngryManScenario")

async def run_scenario():
    # 1. Start Fate Engine
    engine = FateEngine(tick_rate=20, db_path="angry_man.db")
    server = FateEngineServer(engine, port=50051)
    
    server_task = asyncio.create_task(server.start())
    engine_task = asyncio.create_task(engine.run())
    
    logger.info("Fate Engine & gRPC Server running.")
    await asyncio.sleep(1) # Allow server to bind

    # 2. Initialize Jurors
    jurors = [
        {
            "name": "Arthur Miller (Juror 3)",
            "profile": {
                "name": "Arthur Miller",
                "role": "Juror 3",
                "traits": "Aggressive, stubborn, angry",
                "stance": "GUILTY",
                "backstory": "Sees his own estranged son in the defendant. Desperate for order/punishment.",
                "goal": "Convince everyone the boy is guilty and end this."
            }
        },
        {
            "name": "Davis (Juror 8)",
            "profile": {
                "name": "Davis",
                "role": "Juror 8",
                "traits": "Calm, persistent, rational",
                "stance": "NOT GUILTY",
                "backstory": "Architect. Believes in reasonable doubt.",
                "goal": "Force others to examine the evidence fairly."
            }
        }
    ]

    brains = []
    for j in jurors:
        actor_id = str(uuid.uuid4())
        brain = AgentBrain(actor_id, j["profile"])
        brains.append(asyncio.create_task(brain.run()))
        logger.info(f"Launched Brain for {j['name']}")

    # 3. Run for 300 ticks (~15 seconds at 20 TPS, enough for a few deliberation cycles)
    logger.info("Scenario running. Monitoring logs...")
    try:
        await asyncio.sleep(20) 
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down scenario.")
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

if __name__ == "__main__":
    asyncio.run(run_scenario())
