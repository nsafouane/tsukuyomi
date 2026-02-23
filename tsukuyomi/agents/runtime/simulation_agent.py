"""
Simulation Agent - AgentBrain
============================

The dual-mode cognitive controller for Tsukuyomi agents.
Connected to the Fate Engine via gRPC for simulation mode.
"""

import asyncio
import uuid
import logging
import json
import re
import os
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from tsukuyomi.transport.grpc.client import FateEngineClient
from tsukuyomi.transport.proto import core_pb2
from tsukuyomi.agents.cognitive.memory import MemoryManager
from tsukuyomi.services.llm import LLMService
from tsukuyomi.agents.internal.needs.needs_system import NeedsSystem, NeedType
from tsukuyomi.agents.cognitive.working_memory import WorkingMemory
from tsukuyomi.agents.internal.emotion import (
    StateManager,
    PersonalityBaseline,
    EmotionalState,
)
from tsukuyomi.agents.internal.beliefs.unified import BeliefManager, PersonalityBias
from tsukuyomi.agents.social.relationship_manager import RelationshipManager
from tsukuyomi.narrative.core.director import DramaDirector
from tsukuyomi.agents.social.gossip_protocol import get_gossip_protocol
from tsukuyomi.agents.cognitive.deliberation import DeliberationEngine
from tsukuyomi.agents.core.base_agent import BaseAgent

logger = logging.getLogger("AgentBrain")


@dataclass
class SensoryProfile:
    vision_range: float = 20.0
    vision_fov: float = 120.0
    hearing_range: float = 15.0


class PerceptionPipeline:
    def __init__(self, actor_id: str, profile: SensoryProfile):
        self.actor_id = actor_id
        self.profile = profile
        self.spatial_index = None

    def set_spatial_index(self, spatial_index):
        self.spatial_index = spatial_index

    def process(self, world_state, *args, **kwargs) -> List[Any]:
        return []


class EmotionalExpression:
    def __init__(self, pad_state: Dict, personality: Dict):
        self.pad_state = pad_state
        self.personality = personality


class AgentBrain(BaseAgent):
    """
    The Dual-Mode Cognitive Controller for Tsukuyomi Agents.
    """

    SimulationAgent = None  # Alias for backward compatibility

    def __init__(
        self,
        actor_id: str,
        profile: Dict,
        server_addr: str = "localhost:50051",
        fate_engine=None,
    ):
        self.actor_id = actor_id
        super().__init__(agent_id=actor_id)
        self.profile = profile
        self.client = FateEngineClient(server_addr)
        self.memory = MemoryManager(actor_id)
        self.is_thinking = False
        self._running = True
        self._paused = False
        self._cancel_current_deliberation = False
        match = re.search(r"\d+", actor_id)
        self.tick_offset = int(match.group()) * 7 if match else 0

        baseline_params = profile.get("personality_baseline", {})
        self.state_manager = StateManager(
            PersonalityBaseline(
                valence_baseline=baseline_params.get("valence", 0.0),
                arousal_baseline=baseline_params.get("arousal", 0.5),
                dominance_baseline=baseline_params.get("dominance", 0.0),
                regression_rate=baseline_params.get("regression_rate", 0.015),
            ),
        )

        bias_params = profile.get("personality_bias", {})
        self.belief_manager = BeliefManager(
            actor_id,
            PersonalityBias(
                confirmation_bias=bias_params.get("confirmation_bias", 1.0),
                disconfirmation_resistance=bias_params.get(
                    "disconfirmation_resistance", 1.0
                ),
                social_pressure_immunity=bias_params.get(
                    "social_pressure_immunity", 1.0
                ),
            ),
        )

        sensory_params = profile.get("sensory_profile", {})
        self.perception = PerceptionPipeline(
            actor_id,
            SensoryProfile(
                vision_range=sensory_params.get("vision_range", 20.0),
                vision_fov=sensory_params.get("vision_fov", 120.0),
                hearing_range=sensory_params.get("hearing_range", 15.0),
            ),
        )

        self.working_memory = WorkingMemory()
        self.relationships = RelationshipManager(actor_id)

        self.needs = NeedsSystem()
        logger.info(f"AgentBrain for {profile.get('name', 'Unknown')} initialized with NeedsSystem")

        self.rag_system = None
        self.spatial_index = None
        self.spatial_logic = None
        self.drama_director = None

        self.deliberation_engine = DeliberationEngine(
            actor_id,
            belief_system=self.belief_manager,
            emotional_state=self.state_manager.get_emotional_context(),
            personality=profile.get("personality", {}),
            llm_call=None
        )
        self.expression_layer = EmotionalExpression(
            pad_state=self.state_manager.get_emotional_context(),
            personality=profile.get("personality", {})
        )

    def set_spatial_index(self, spatial_index):
        self.spatial_index = spatial_index
        self.perception.set_spatial_index(spatial_index)
        logger.info(f"AgentBrain {self.profile.get('name', 'Unknown')} connected to SpatialIndex")

    def set_spatial_logic(self, spatial_logic):
        self.spatial_logic = spatial_logic

    async def perceive(self, world_state: Any) -> List[Any]:
        percepts = []
        tick = getattr(world_state, 'tick_number', 0) if world_state else 0
        
        if tick % 20 != (self.tick_offset % 20):
            return percepts

        return self.perception.process(world_state)

    async def deliberate(self, percepts: List[Any]) -> Any:
        if not percepts:
            return None
        
        emotional_context = self.state_manager.get_emotional_context()
        decision = await self.deliberation_engine.deliberate(percepts, emotional_context)
        return decision

    async def act(self, decision: Any) -> Any:
        if decision is None:
            return None
        
        proposal = await self._create_proposal(decision)
        if proposal:
            await self.client.submit_proposal(proposal)
        return proposal

    async def _create_proposal(self, decision):
        return None

    def start(self):
        self._running = True
        self._paused = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def cleanup(self):
        self._running = False


SimulationAgent = AgentBrain
