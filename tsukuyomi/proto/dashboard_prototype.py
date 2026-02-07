import sys
import os
import asyncio
import logging
from typing import List, Optional

# Ensure the proto directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tsukuyomi.proto.fate_engine import FateEngine
from tsukuyomi.proto import core_pb2

# Set up logging to capture fate engine output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DashboardDemo")

class DashboardPrototype:
    def __init__(self, engine: FateEngine):
        self.engine = engine
        self.last_tick_processed = -1
        
    async def render_cli(self):
        """A simple CLI-based dashboard that updates as the engine ticks."""
        while self.engine.running:
            current_tick = self.engine.current_tick
            if current_tick != self.last_tick_processed:
                self.last_tick_processed = current_tick
                world_state = self.engine.world_state
                
                # Clear screen (simple way for CLI)
                print("\033[H\033[J", end="")
                print(f"🏛️ TSUKUYOMI DASHBOARD PROTOTYPE | Tick: {current_tick}")
                print("-" * 50)
                
                print("ACTORS:")
                for actor_id, actor in world_state.actors.items():
                    print(f"  👤 {actor.name:10} | Pos: ({actor.position.x:4.1f}, {actor.position.y:4.1f}) | Loc: {actor.current_location or 'N/A'}")
                
                print("\nOBJECTS:")
                for obj_id, obj in world_state.objects.items():
                    print(f"  📦 {obj_id:15} | Type: {obj.type:10} | Pos: ({obj.position.x:4.1f}, {obj.position.y:4.1f})")
                
                print("\nLOCATIONS:")
                for loc_name, loc in world_state.locations.items():
                    print(f"  📍 {loc_name:15} | Pos: ({loc.position.x:4.1f}, {loc.position.y:4.1f})")
                
                print("-" * 50)
                print("Press Ctrl+C to stop simulation.")

            await asyncio.sleep(0.1) # Update rate for dashboard

async def run_prototype():
    engine = FateEngine(tick_rate=5, seed=42) # Slower tick rate for visibility
    
    # Register actors
    engine.register_actor("agent_001", "Tanit", position=(0, 0))
    engine.register_actor("agent_002", "Safouane", position=(2, 2))
    
    dashboard = DashboardPrototype(engine)
    
    # Start engine and dashboard
    try:
        # We can add a periodic task to submit random proposals to see movement
        async def random_behavior():
            locations = list(engine.world_state.locations.keys())
            while engine.running:
                await asyncio.sleep(2)
                actor_id = "agent_001" if engine.current_tick % 2 == 0 else "agent_002"
                dest = locations[engine.current_tick % len(locations)]
                
                # Create movement proposal
                from tsukuyomi.proto.fate_engine import create_proposal
                p = await create_proposal(actor_id, "MOVE", {"destination": dest})
                await engine.submit_proposal(p)
        
        await asyncio.gather(
            engine.run(),
            dashboard.render_cli(),
            random_behavior()
        )
    except KeyboardInterrupt:
        engine.stop()
        print("\nSimulation stopped.")

if __name__ == "__main__":
    asyncio.run(run_prototype())
