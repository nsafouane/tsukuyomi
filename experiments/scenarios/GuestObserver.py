import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.proto import core_pb2

logger = logging.getLogger("GuestObserver")

class GuestObserver:
    """
    An example Guest Agent that observes the simulation and logs events.
    Can be used for debugging, visualization, or external agent integration.
    """
    
    def __init__(self, actor_id: str, server_addr: str = "localhost:50051"):
        self.actor_id = actor_id
        self.client = FateEngineClient(server_addr)
        
        # Relative paths for logs
        base_dir = Path(__file__).resolve().parent.parent / "logs"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_path = base_dir / "guest_observer_log.jsonl"
        self.research_log_path = base_dir / "researcher_notes.jsonl"
        self.trigger_path = base_dir / "input_trigger.json"
        self.response_path = base_dir / "agent_response.json"
        
        self.observations: List[Dict] = []
        
    def _log_observation(self, type: str, content: Dict):
        """Record an observation or thought to the guest log."""
        entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "type": type,
            "content": content
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"OBSERVED [{type}]: {json.dumps(content)}")

    async def run(self):
        """Observation and interaction loop."""
        logger.info(f"Guest Observer starting...")
        
        if not await self.client.connect():
            logger.error("Failed to connect to Fate Engine.")
            return

        # Register in the engine
        await self.client.register_actor(self.actor_id, "GuestObserver")
        logger.info("Registered in Fate Engine.")

        self._log_observation("system", {"event": "entered_simulation", "actor_id": self.actor_id})

        async for tick_state in self.client.stream_tick_updates():
            await self._on_tick(tick_state)

    async def _on_tick(self, tick_state: core_pb2.TickState):
        """Process world state and record findings."""
        tick_num = tick_state.tick_number
        
        # 1. Standard telemetry logging
        for actor_id, actor in tick_state.world_state.actors.items():
            if actor_id != self.actor_id:
                self._log_observation("agent_observation", {
                    "tick": tick_num,
                    "agent_name": actor.name,
                    "pos": f"({actor.position.x}, {actor.position.y})",
                    "state": actor.state
                })

        # 2. External Trigger Logic (Example: every 50 ticks)
        if tick_num % 50 == 0:
            scene_summary = {
                "tick": tick_num,
                "actors": {aid: a.name for aid, a in tick_state.world_state.actors.items()},
                "recent_actions": [
                    {"who": res.actor_id, "what": res.outcome.get("action"), "outcome": res.outcome}
                    for res in tick_state.resolutions if res.success
                ]
            }
            
            with open(self.trigger_path, "w") as f:
                json.dump(scene_summary, f)
            
            logger.info(f"TICK {tick_num}: Scene summary exported.")
            
            # Check for response
            if self.response_path.exists():
                try:
                    with open(self.response_path, "r") as f:
                        resp = json.load(f)
                    
                    if resp.get("action"):
                        logger.info(f"Submitting response action: {resp['action']}")
                        await self.client.submit_proposal(self.actor_id, resp['action'], resp.get('params', {}))
                        self._log_observation("action_submitted", resp)
                    
                    self.response_path.unlink()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    observer = GuestObserver("guest-observer-01")
    asyncio.run(observer.run())
