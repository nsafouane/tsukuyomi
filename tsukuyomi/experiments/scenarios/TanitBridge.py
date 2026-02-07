import asyncio
import logging
import json
import os
from typing import Dict, List, Optional
from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.proto import core_pb2

logger = logging.getLogger("TanitBridge")

class TanitBridge:
    """
    The Guest Agent Bridge for Tanit (The Co-Founder).
    Allows Tanit to enter the 'Angry Man Room' and observe/interact.
    """
    
    def __init__(self, actor_id: str, server_addr: str = "localhost:50051"):
        self.actor_id = actor_id
        self.client = FateEngineClient(server_addr)
        self.log_path = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/tanit_guest_log.jsonl"
        self.research_log_path = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/tanit_thoughts/researcher_notes.jsonl"
        self.observations: List[Dict] = []
        
    def _log_observation(self, type: str, content: Dict):
        """Record an observation or thought to the guest log."""
        entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "type": type,
            "content": content
        }
        # Standard observation log
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"TANIT OBSERVED [{type}]: {json.dumps(content)}")

    def _log_researcher_thought(self, category: str, thought: str):
        """Separate researcher-grade analysis from simulation feelings."""
        entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "category": category, # "environment", "agents", "meta_simulation"
            "thought": thought
        }
        with open(self.research_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"🧪 RESEARCHER [{category.upper()}]: {thought}")

    async def run(self):
        """Tanit's observation and interaction loop."""
        logger.info(f"Tanit Bridge (Guest Agent) starting...")
        
        if not await self.client.connect():
            logger.error("Tanit failed to connect to Fate Engine.")
            return

        # Register Tanit in the engine
        await self.client.register_actor(self.actor_id, "Tanit")
        logger.info("Tanit registered in Fate Engine.")

        self._log_observation("system", {"event": "tanit_entered_simulation", "actor_id": self.actor_id})

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

        # 2. TRIGGER: When it is deliberation time (every 50 ticks),
        # output the scene to the co-founder chat so Tanit (the main agent) can respond.
        if tick_num % 50 == 0:
            scene_summary = {
                "tick": tick_num,
                "actors": {aid: a.name for aid, a in tick_state.world_state.actors.items()},
                "recent_actions": [
                    {"who": res.actor_id, "what": res.outcome.get("action"), "outcome": res.outcome}
                    for res in tick_state.resolutions if res.success
                ]
            }
            # Write a trigger file for the main session to read
            trigger_path = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/tanit_input_trigger.json"
            with open(trigger_path, "w") as f:
                json.dump(scene_summary, f)
            
            logger.info(f"🚨 TICK {tick_num}: Scene summary ready for Tanit's decision.")
            
            # Check for existing response from previous trigger
            response_path = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/tanit_response.json"
            if os.path.exists(response_path):
                try:
                    with open(response_path, "r") as f:
                        resp = json.load(f)
                    
                    if resp.get("action"):
                        logger.info(f"📤 Tanit submitting response action: {resp['action']}")
                        await self.client.submit_proposal(self.actor_id, resp['action'], resp.get('params', {}))
                        self._log_observation("tanit_action", resp)
                    
                    # Clear response file after reading
                    os.remove(response_path)
                except Exception as e:
                    logger.error(f"Error processing Tanit response: {e}")
        
    async def submit_thought(self, thought: str):
        """Allow Tanit to record a conscious thought during the experiment."""
        self._log_observation("tanit_thought", {"thought": thought})

    async def speak(self, message: str):
        """Submit a dialogue proposal (to be implemented in ActionResolver)."""
        # For now, we use EMOTE as a placeholder for dialogue
        await self.client.submit_proposal(self.actor_id, "EMOTE", {"type": "speak", "message": message})
        self._log_observation("tanit_action", {"action": "speak", "message": message})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Tanit's unique ID in the simulation
    tanit_id = "tanit-guest-001"
    bridge = TanitBridge(tanit_id)
    asyncio.run(bridge.run())
