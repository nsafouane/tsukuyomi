import asyncio
import uuid
import logging
import json
from typing import Dict, Optional, List
from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.proto import core_pb2
from tsukuyomi.brain.MemoryManager import MemoryManager
from tsukuyomi.brain.LLMService import LLMService
from tsukuyomi.brain.GossipProtocol import get_gossip_protocol

logger = logging.getLogger("AgentBrain")

class AgentBrain:
    """
    The Dual-Mode Cognitive Controller for Tsukuyomi Agents.
    """
    
    def __init__(self, actor_id: str, profile: Dict, server_addr: str = "localhost:50051"):
        self.actor_id = actor_id
        self.profile = profile
        self.client = FateEngineClient(server_addr)
        self.memory = MemoryManager(actor_id)
        self.is_thinking = False
        import re
        match = re.search(r'\d+', actor_id)
        self.tick_offset = int(match.group()) * 7 if match else 0
        
    async def run(self):
        """Main cognitive loop: stream ticks and decide actions."""
        logger.info(f"AgentBrain for {self.profile['name']} ({self.actor_id}) starting...")
        
        if not await self.client.connect():
            logger.error(f"Agent {self.profile['name']} failed to connect to Fate Engine.")
            return

        # Register actor in the engine
        await self.client.register_actor(self.actor_id, self.profile['name'])
        logger.info(f"Agent {self.profile['name']} registered in Fate Engine.")

        async for tick_state in self.client.stream_tick_updates():
            await self._process_tick(tick_state)

    async def _process_tick(self, tick_state: core_pb2.TickState):
        # 1. Observation (Memory Ingestion)
        self.memory.ingest_tick(tick_state)
        
        # 2. System 1: Reflexes (Fast)
        await self._run_reflexes(tick_state)
        
        # 3. System 2: Deliberation (Slow Reasoning)
        if self._should_deliberate(tick_state) and not self.is_thinking:
            # Run System 2 asynchronously to not block tick consumption
            asyncio.create_task(self._deliberate(tick_state))

    async def _run_reflexes(self, tick_state: core_pb2.TickState):
        actor = tick_state.world_state.actors.get(self.actor_id)
        if not actor: return

        # Collection Reflex: If near food/tool, grab it.
        for obj_id, obj in tick_state.world_state.objects.items():
            if obj.type in ("food", "tool"):
                dist = ((actor.position.x - obj.position.x)**2 + (actor.position.y - obj.position.y)**2)**0.5
                if dist < 2.0:
                    logger.info(f"⚡ {self.profile['name']} REFLEX: Collecting {obj_id}")
                    await self.client.submit_proposal(self.actor_id, "COLLECT", {"target_id": obj_id})

    def _should_deliberate(self, tick_state: core_pb2.TickState) -> bool:
        """Rule: Deliberate every 50 ticks with a unique offset."""
        return (tick_state.tick_number + self.tick_offset) % 50 == 0

    async def _deliberate(self, tick_state: core_pb2.TickState):
        self.is_thinking = True
        try:
            recent_memories = self.memory.query_recent(limit=10)
            semantic_facts = self.memory.get_semantic_summary()
            
            # GOSSIP: Fetch what we've overheard
            gossip_protocol = get_gossip_protocol()
            gossip_summary = gossip_protocol.get_gossip_summary_for_agent(self.actor_id)

            summary = f"Tick {tick_state.tick_number}. World has {len(tick_state.world_state.actors)} actors."
            
            plan = await LLMService.generate_plan(
                self.profile, 
                recent_memories, 
                semantic_facts, 
                summary,
                gossip=gossip_summary
            )
            
            # GOSSIP: Register our thought for others to potentially overhear
            gossip_protocol.register_deliberation(
                self.actor_id,
                plan['thought'],
                plan['action'],
                tick_state.tick_number,
                world_state_context={"actors": {k: {"position": {"x": v.position.x, "y": v.position.y}} for k, v in tick_state.world_state.actors.items()}}
            )
            
            # GOSSIP: Process all overheard info for this tick
            gossip_protocol.process_gossip(tick_state.tick_number)

            # Log Chain of Thought for analysis
            cot_log = f"/root/.openclaw/workspace/tsukuyomi/experiments/logs/chain_of_thought/{self.profile['name'].replace(' ', '_')}.jsonl"
            with open(cot_log, "a") as f:
                f.write(json.dumps({
                    "tick": tick_state.tick_number, 
                    "thought": plan['thought'], 
                    "action": plan['action'],
                    "params": plan.get('params', {})
                }) + "\n")

            # NEW: Log dialogue specifically
            if plan['action'] == "EMOTE" and (plan.get('params', {}).get('type') == "speak" or "message" in plan.get('params', {})):
                dialogue_log = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/dialogue/transcript.jsonl"
                with open(dialogue_log, "a") as f:
                    f.write(json.dumps({
                        "tick": tick_state.tick_number,
                        "who": self.profile['name'],
                        "message": plan.get('params', {}).get('message', '') or plan.get('params', {}).get('type', '')
                    }) + "\n")

            logger.info(f"🧠 {self.profile['name']} DECIDED: {plan['thought']} -> {plan['action']}")
            
            # Submit the high-level plan as a proposal
            await self.client.submit_proposal(
                self.actor_id, 
                plan['action'], 
                plan.get('params', {})
            )
            
        except Exception as e:
            logger.error(f"Deliberation failed for {self.profile['name']}: {e}")
        finally:
            self.is_thinking = False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example Juror Profile from 'Angry Man Room'
    juror_profile = {
        "name": "Thomas Wright",
        "stance": "guilty",
        "backstory": "High school teacher for 25 years. Believes in order and rules."
    }
    
    brain = AgentBrain(str(uuid.uuid4()), juror_profile)
    asyncio.run(brain.run())
