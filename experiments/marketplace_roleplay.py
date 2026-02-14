#!/usr/bin/env python3
"""
Tsukuyomi Engine - Experiment: The Busy Marketplace

Tests general capabilities: Spatial Nav, Object Interaction, Role Logic.
"""

import asyncio
import logging
from typing import Dict
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.client.GrpcClient import GrpcClient
from tsukuyomi.proto import common_pb2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Simplified Role Logic for this Experiment (No full Python classes to keep it contained)
ROLE_PROMPTS = {
    "Merchant": "You are a Merchant selling goods. Sell to peasants. Collect money.",
    "Guard": "You are a Guard. Patrol the square. Watch for thieves. Stop thieves.",
    "Peasant": "You are a Peasant. You have no money. Beg merchants for goods.",
    "Thief": "You are a Thief. Steal from merchants or peasants. Avoid guards."
}

class RoleAgent:
    """Minimalist agent wrapper for the scenario."""
    def __init__(self, client, profile, world_builder):
        self.client = client
        self.profile = profile
        self.actor_id = profile["id"]
        self.role = profile["role"]
        self.location = profile.get("location", "TownSquare")
        self.world = world_builder # Shared ref
        
    async def register(self):
        await self.client.register_actor(self.actor_id)
        logger.info(f"Registered {self.actor_id} ({self.role})")

    async def run_loop(self):
        """Main loop."""
        # 1. Check for nearby agents (Simple Distance Check)
        #    Ideally, we get world state here.
        #    For now, we just wait and LLM decides.
        
        prompt = ROLE_PROMPTS.get(self.role, "You are an agent.")
        
        # 2. Get Brain Decision
        #    We rely on AgentBrain's LLM call
        #    We just call it periodically.
        
        if random.random() < 0.2: # 20% chance to think
            logger.debug(f"{self.actor_id} is deliberating...")
            # Inject observation into brain
            # In a real setup, this would be percepts. 
            # Here we just inject a "heartbeat" prompt.
            # We can't access self.brain directly if we don't instantiate it in this scope,
            # but we can call a generic "generate" via the client if we had a generic LLM service wrapper.
            # Since we don't, we simulate "thinking" by logging.
            pass
        
        # 3. Action Phase (Simulated for this file)
        #    The real AgentBrain would submit_proposal.
        #    Here we just log what we *would* do based on role logic.
        
        action = "IDLE"
        params = {}
        
        if self.role == "Merchant":
            if random.random() > 0.5:
                action = "EMOTE"
                params = {"type": "speak", "message": "Fresh apples! Get your apples!"}
        else:
                action = "IDLE" # Waiting for customers
        
        elif self.role == "Peasant":
            # Look for money or beg
            if random.random() > 0.7:
                action = "EMOTE"
                params = {"type": "speak", "message": "Please sir, I'm hungry."}
        
        elif self.role == "Guard":
            # Patrol or Watch
            if random.random() > 0.8:
                action = "MOVE"
                params = {"destination": "market_stall_1"} # Arbitrary location
        
        elif self.role == "Thief":
            # Steal
            if random.random() > 0.7:
                action = "INTERACT"
                params = {"target": "market_stall_2", "action": "steal"}

        if action != "IDLE":
            logger.info(f"{self.actor_id} ({self.role}) performs {action}: {params}")
            # In a real setup, submit to Fate Engine.
            # await self.client.submit_proposal(self.actor_id, action, params)
        
        # 4. Wait
        await asyncio.sleep(random.uniform(1.0, 3.0))

class MarketplaceExperiment:
    def __init__(self, client_addr: str):
        self.client_addr = client_addr
        self.client = GrpcClient(client_addr)
        self.agents: Dict[str, RoleAgent] = {}
        self.world = None # Placeholder
        self.running = True

    async def run(self):
        # Setup Mock World (Using AgentBrain to manage state for simplicity)
        # We don't have a WorldBuilder class imported that works easily here.
        # We will rely on the default "Empty Jury Room" world provided by the Fate Engine.
        # Agents will spawn at (0,0).
        
        # Define Agents
        profiles = [
            {"id": "merchant_01", "name": "Marcus", "role": "Merchant", "location": "TownSquare"},
            {"id": "guard_01", "name": "Brutus", "role": "Guard", "location": "TownSquare"},
            {"id": "peasant_01", "name": "Cassius", "role": "Peasant", "location": "TownSquare"},
            {"id": "thief_01", "name": "Sneaky", "role": "Thief", "location": "TownSquare"},
        ]

        for p in profiles:
            # We pass `self` as the "world" arg, but RoleAgent won't use it effectively in this simple version.
            agent = RoleAgent(self.client, p, self)
            self.agents[p["id"]] = agent
            await agent.register()

        logger.info(f"Marketplace started with {len(self.agents)} agents.")
        
        try:
            while self.running:
                tasks = [agent.run_loop() for agent in self.agents.values()]
                await asyncio.sleep(0.5) # Global tick
        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.running = False
        finally:
            await self.client.disconnect()

async def main():
    import os
    client_addr = os.getenv("FATE_ENGINE_ADDR", "localhost:50051")
    exp = MarketplaceExperiment(client_addr)
    await exp.run()

if __name__ == "__main__":
    asyncio.run(main())
