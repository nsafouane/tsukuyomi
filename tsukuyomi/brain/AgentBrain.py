import asyncio
import uuid
import logging
import json
import re
import os
from typing import Dict, Optional, List, Any, Tuple
from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.proto import core_pb2
from tsukuyomi.brain.MemoryManager import MemoryManager
from tsukuyomi.brain.LLMService import LLMService
from tsukuyomi.brain.needs_system import NeedsSystem, NeedType  # V2: Add needs import
from tsukuyomi.brain.rag_memory import RAGMemorySystem, RAGConfig  # V3: Add RAG import
from tsukuyomi.brain.PerceptionPipeline import (
    PerceptionPipeline,
    SensoryProfile,
    AgentInternalState,
)
from tsukuyomi.brain.StateManager import (
    StateManager,
    PersonalityBaseline,
    EmotionalState,
)
from tsukuyomi.brain.WorkingMemory import WorkingMemory
from tsukuyomi.brain.BeliefManager import BeliefManager, PersonalityBias
from tsukuyomi.brain.RelationshipManager import RelationshipManager
from tsukuyomi.brain.DramaDirector import DramaDirector
from tsukuyomi.brain.GossipProtocol import get_gossip_protocol  # Moved from late imports
from tsukuyomi.brain.deliberation import DeliberationEngine
from tsukuyomi.proto.emotional_expression import EmotionalExpression

logger = logging.getLogger("AgentBrain")


class AgentBrain:
    """
    The Dual-Mode Cognitive Controller for Tsukuyomi Agents.
    """

    def __init__(
        self,
        actor_id: str,
        profile: Dict,
        server_addr: str = "localhost:50051",
        fate_engine=None,
    ):
        self.actor_id = actor_id
        self.profile = profile
        self.client = FateEngineClient(server_addr)
        self.memory = MemoryManager(actor_id)
        self.is_thinking = False
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

        # V2: Initialize Needs System for autonomous behavior
        self.needs = NeedsSystem()
        logger.info(f"AgentBrain for {profile.get('name', 'Unknown')} initialized with NeedsSystem")

        # V3: Initialize RAG System for long-term memory
        rag_config = RAGConfig(
            vector_collection=f"memories_{actor_id}",
            in_memory=True  # Use in-memory for now until vector DB service is up
        )
        self.rag_system = RAGMemorySystem(rag_config)
        logger.info(f"AgentBrain for {profile.get('name', 'Unknown')} initialized with RAGMemorySystem")

        # Phase 2: Spatial Index integration for efficient perception
        self.spatial_index = None  # Will be set by external initialization
        self.spatial_logic = None  # Will be set by external initialization

        # FIX: Get drama director instance for sentiment updates
        from tsukuyomi.brain.DramaDirector import DramaDirector

        self.drama_director = None

        # Cognitive Richness (Phase 1 & 2)
        self.deliberation_engine = DeliberationEngine(
            actor_id,
            belief_system=self.belief_manager,
            emotional_state=self.state_manager.get_emotional_context(),
            personality=profile.get("personality", {}),
            llm_call=None # Placeholder
        )
        self.expression_layer = EmotionalExpression(
            pad_state=self.state_manager.get_emotional_context(),
            personality=profile.get("personality", {})
        )

    def set_spatial_index(self, spatial_index):
        """
        Set the spatial index for efficient proximity detection.

        This is called during world initialization to integrate the agent
        with the spatial partitioning system.

        Args:
            spatial_index: SpatialIndex instance from the world
        """
        self.spatial_index = spatial_index
        self.perception.set_spatial_index(spatial_index)
        logger.info(f"AgentBrain {self.profile['name']} connected to SpatialIndex")

    def set_spatial_logic(self, spatial_logic):
        """
        Set the spatial logic for room/portal awareness.

        This provides the agent with knowledge of room boundaries,
        portals, and occluding obstacles for accurate line-of-sight.

        Args:
            spatial_logic: SpatialLogic instance from the world
        """
        self.spatial_logic = spatial_logic
        self.perception.set_spatial_logic(spatial_logic)
        logger.info(f"AgentBrain {self.profile['name']} connected to SpatialLogic")


    async def run(self):
        """Main cognitive loop: stream ticks and decide actions."""
        logger.info(
            f"AgentBrain for {self.profile['name']} ({self.actor_id}) starting..."
        )

        if not await self.client.connect():
            logger.error(
                f"Agent {self.profile['name']} failed to connect to Fate Engine."
            )
            return

        # Register actor in the engine
        await self.client.register_actor(self.actor_id, self.profile["name"])
        logger.info(f"Agent {self.profile['name']} registered in Fate Engine.")

        async for tick_state in self.client.stream_tick_updates():
            await self._process_tick(tick_state)

    async def _process_tick(self, tick_state: core_pb2.TickState):
        # Phase 2: Update spatial index with current position
        my_actor = tick_state.world_state.actors.get(self.agent_id)
        if my_actor and self.spatial_index:
            # Update agent's position in spatial index for efficient queries
            self.spatial_index.update_position(
                self.agent_id,
                (my_actor.position.x, my_actor.position.y)
            )

        # Calculate facing direction (simplified - could be derived from movement)
        facing_direction = self._calculate_facing_direction(my_actor)

        agent_state = AgentInternalState(
            current_concerns=[],
            mood_label=self.state_manager.state.mood_label,
            arousal=self.state_manager.state.arousal,
            last_seen_entities={},
            facing_direction=facing_direction,
        )

        percepts = self.perception.process(
            tick_state.world_state, agent_state, tick_state.tick_number
        )

        self.state_manager.update(tick_state.tick_number, percepts)
        self._process_social_signals(percepts, tick_state.tick_number)
        self._process_gossip_signals(tick_state.tick_number)

        self.memory.ingest_tick(tick_state)

        if tick_state.tick_number % 10 == 0:
            self.memory.tick_decay(tick_state.tick_number)

        # V2: Update needs every tick (based on tick rate)
        self.needs.update_all(tick_rate=20.0)  # 20 ticks per second

        # Process gossip propagation each tick
        gossip_protocol = get_gossip_protocol()
        gossip_events = gossip_protocol.process_gossip(tick_state.tick_number)
        if gossip_events:
            logger.debug(
                f"{self.profile['name']} processed {len(gossip_events)} gossip events"
            )

        await self._run_reflexes(tick_state)

        reactive_trigger = self._check_reactive_triggers(percepts)
        directive_trigger = await self._check_llm_directives(tick_state)

        if not self.is_thinking:
            if reactive_trigger:
                asyncio.create_task(
                    self._deliberate(tick_state, percepts, reason=reactive_trigger)
                )
            elif directive_trigger:
                asyncio.create_task(
                    self._deliberate(tick_state, percepts, reason=f"directive: {directive_trigger}")
                )
            elif self._should_deliberate(tick_state):
                asyncio.create_task(
                    self._deliberate(tick_state, percepts, reason="scheduled")
                )

    async def _check_llm_directives(self, tick_state: core_pb2.TickState) -> Optional[str]:
        """Check for active LLM directives before deliberation."""
        # Check for pending directives from long-term memory
        directive_memories = self.memory.query_long_term(["directive"], limit=1)
        
        if directive_memories:
            return directive_memories[0].get("content", "")
        
        return None

    def _process_social_signals(self, percepts: list, tick: int):
        """Process perception signals to update relationships."""
        for percept in percepts:
            if hasattr(percept, "speech") and percept.HasField("speech"):
                speaker_id = percept.speech.speaker_id
                if not speaker_id:
                    continue

                if percept.speech.is_direct_address:
                    # Positive impact for direct address (attention)
                    self.relationships.record_event(
                        speaker_id,
                        tick,
                        "direct_address",
                        0.05,
                        f"{percept.speech.speaker_name} addressed you directly.",
                    )

                # Sentiment analysis of speech would go here
                # For now, neutral/slight positive for communication
                self.relationships.record_event(
                    speaker_id,
                    tick,
                    "interact",
                    0.01,
                    f"{percept.speech.speaker_name} spoke: {percept.speech.content[:30]}...",
                )

    def _process_gossip_signals(self, tick: int):
        """Check for new gossip and update relationships."""
        gossip_protocol = get_gossip_protocol()
        recent_gossip = gossip_protocol.get_gossip_for_agent(self.actor_id)

        # Basic logic: Hearing gossip about someone affects reputation/affinity
        # For simplicity, we just record the 'event' of overhearing
        for gossip in recent_gossip:
            # If the gossip is about someone else
            if gossip.source_actor_id != self.actor_id:
                # Small affinity boost for the 'sharer' (indirectly)
                # In this model, sharing is overhearing
                self.relationships.record_event(
                    gossip.source_actor_id,
                    tick,
                    "gossip_overhear",
                    0.005,
                    f"Overheard a thought from {gossip.source_actor_id}: '{gossip.content[:30]}...'",
                )

    def _check_reactive_triggers(self, percepts: list) -> Optional[str]:
        for percept in percepts:
            if hasattr(percept, "speech") and percept.HasField("speech"):
                if percept.speech.is_direct_address:
                    return "direct_address"

            if percept.salience > 0.85:
                return "high_salience_event"

            if hasattr(percept, "event") and percept.HasField("event"):
                if percept.event.event_type == "stance_shift":
                    return "social_trigger"

        return None

    async def _run_reflexes(self, tick_state: core_pb2.TickState):
        actor = tick_state.world_state.actors.get(self.actor_id)
        if not actor:
            return

        # Collection Reflex: If near food/tool, grab it.
        for obj_id, obj in tick_state.world_state.objects.items():
            if obj.type in ("food", "tool"):
                dist = (
                    (actor.position.x - obj.position.x) ** 2
                    + (actor.position.y - obj.position.y) ** 2
                ) ** 0.5
                if dist < 2.0:
                    logger.info(
                        f"⚡ {self.profile['name']} REFLEX: Collecting {obj_id}"
                    )
                    await self.client.submit_proposal(
                        self.actor_id, "COLLECT", {"target_id": obj_id}
                    )

    def _should_deliberate(self, tick_state: core_pb2.TickState) -> bool:
        """Rule: Deliberate every 200 ticks with a unique offset (safe for Groq 30 RPM)."""
        return (tick_state.tick_number + self.tick_offset) % 200 == 0

    async def _deliberate(
        self, tick_state: core_pb2.TickState, percepts: list, reason: str = "scheduled"
    ):
        if self.is_thinking:
            if reason in ("direct_address", "high_salience_event"):
                logger.info(f"PREEMPTING scheduled deliberation for {reason}")
                self._cancel_current_deliberation = True
                await asyncio.sleep(0.5)
            else:
                return

        self.is_thinking = True
        self._cancel_current_deliberation = False

        try:
            self.working_memory.refresh(
                percepts=percepts,
                episodic_memories=self.memory.episodic_memory,
                semantic_memory=self.memory.semantic_memory,
                emotional_state=self.state_manager.state,
                current_topics=self._extract_topics(percepts),
            )

            if self._cancel_current_deliberation:
                return

            belief_context = self.belief_manager.format_beliefs(["defendant_guilt"])
            relationship_context = self.relationships.to_llm_context()
            emotional_modifier = self.state_manager.get_emotional_context()
            working_memory_context = self.working_memory.to_llm_context()

            # V2: Get needs context for LLM prompt
            needs_context = self.needs.get_prompt_context()

            # Phase 2: Get visual context from perception pipeline
            visual_context = self.get_visual_context_for_llm()

            # Phase 3: RAG Retrieval
            rag_context = ""
            if hasattr(self, "rag_system") and self.rag_system:
                # Construct query from current context
                query_parts = []
                if current_topics:
                    query_parts.extend(current_topics[:3])
                if reason:
                    query_parts.append(reason)
                
                query = " ".join(query_parts) if query_parts else "general context"
                
                memories = self.rag_system.retrieve_memories(
                    query=query,
                    top_k=5,
                    min_importance=None  # Get all relevant memories
                )
                
                rag_context = self.rag_system.format_context_for_llm(memories)
                if rag_context:
                    logger.debug(f"Retrieved {len(memories)} RAG memories for query: '{query}'")

            # Pass arguments in correct order matching function signature
            plan = await LLMService.generate_plan_v2(
                self.profile,
                working_memory_context,
                belief_context,
                relationship_context,
                emotional_modifier,
                needs_context,
                visual_context,
                rag_context,  # Phase 3: Pass RAG context
                reason,
            )

            # FIX: Update drama director sentiment after LLM plan generation
            if self.drama_director:
                sentiment_score = emotional_modifier.get("arousal", 0.5)
                self.drama_director.update_sentiment(sentiment_score)

            if self._cancel_current_deliberation:
                return

            # Register deliberation with GossipProtocol for information leakage
            gossip_protocol = get_gossip_protocol()
            gossip_protocol.register_deliberation(
                actor_id=self.actor_id,
                thought=plan["thought"],
                action=plan["action"],
                tick=tick_state.tick_number,
                world_state_context=self._build_world_state_dict(tick_state),
            )

            if plan["action"] == "REFLECT":
                self._handle_reflect(plan, tick_state.tick_number)

            cot_log_dir = os.path.join(os.getcwd(), "experiments/logs/chain_of_thought")
            os.makedirs(cot_log_dir, exist_ok=True)
            cot_log = os.path.join(cot_log_dir, f"{self.profile['name'].replace(' ', '_')}.jsonl")
            with open(cot_log, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "tick": tick_state.tick_number,
                            "thought": plan["thought"],
                            "action": plan["action"],
                            "params": plan.get("params", {}),
                            "reason": reason,
                        }
                    )
                    + "\n"
                )

            if plan["action"] == "EMOTE" and (
                plan.get("params", {}).get("type") == "speak"
                or "message" in plan.get("params", {})
            ):
                dialogue_log_dir = os.path.join(os.getcwd(), "experiments/logs/dialogue")
                os.makedirs(dialogue_log_dir, exist_ok=True)
                dialogue_log = os.path.join(dialogue_log_dir, "transcript.jsonl")
                with open(dialogue_log, "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "tick": tick_state.tick_number,
                                "who": self.profile["name"],
                                "message": plan.get("params", {}).get("message", "")
                                or plan.get("params", {}).get("type", ""),
                            }
                        )
                        + "\n"
                    )

            logger.info(
                f"🧠 {self.profile['name']} DECIDED ({reason}): {plan['thought']} -> {plan['action']}"
            )

            # Ensure all parameters are strings for gRPC/protobuf
            params = {k: str(v) for k, v in plan.get("params", {}).items()}

            await self.client.submit_proposal(
                self.actor_id, plan["action"], params
            )
            logger.debug(
                f"PROPOSAL SUBMITTED: {self.profile['name']} -> {plan['action']}"
            )

            # V2: Satisfy needs based on action taken
            self._satisfy_needs_for_action(plan["action"])

        except Exception as e:
            logger.error(f"Deliberation failed for {self.profile['name']}: {e}")
        finally:
            self.is_thinking = False

    def _satisfy_needs_for_action(self, action: str) -> None:
        """
        V2: Satisfy needs based on the action taken.
        This provides feedback to the needs system when the agent successfully
        addresses a need through action.

        Args:
            action: The action that was submitted
        """
        from tsukuyomi.brain.NeedsSystem import NeedType

        # Map actions to needs they satisfy
        action_need_map = {
            "EAT": (NeedType.HUNGER, 0.7),  # Eating reduces hunger significantly
            "DRINK": (NeedType.HUNGER, 0.3),
            "SIT": (NeedType.FATIGUE, 0.2),  # Resting reduces fatigue
            "SLEEP": (NeedType.FATIGUE, 0.8),  # Sleeping reduces fatigue significantly
            "SOCIALIZE": (NeedType.SOCIAL, 0.5),  # Social interaction reduces social need
            "DANCE": (NeedType.BOREDOM, 0.6),  # Dancing reduces boredom
            "EXPLORE": (NeedType.BOREDOM, 0.3),  # Exploration reduces boredom slightly
            "MOVE": (NeedType.BOREDOM, 0.1),  # Moving slightly reduces boredom
            "EMOTE": (NeedType.SOCIAL, 0.1),  # Speaking reduces social need slightly
        }

        if action in action_need_map:
            need_type, amount = action_need_map[action]
            self.needs.satisfy_need(need_type, amount)
            logger.debug(f"Action {action} satisfied {need_type.value} need by {amount}")

    def _extract_topics(self, percepts: list) -> List[str]:
        topics = []
        for p in percepts:
            if hasattr(p, "speech") and p.HasField("speech"):
                topics.extend(p.speech.content.lower().split())
            if hasattr(p, "object") and p.HasField("object"):
                topics.append(p.object.apparent_type.lower())
        return list(set(topics))

    def _build_world_state_dict(self, tick_state: core_pb2.TickState) -> Dict:
        """Build a simplified world state dict for GossipProtocol."""
        world_dict = {"actors": {}, "tick": tick_state.tick_number}

        for actor_id, actor in tick_state.world_state.actors.items():
            world_dict["actors"][actor_id] = {
                "position": {"x": actor.position.x, "y": actor.position.y},
                "name": actor.name,
                "state": actor.state,
            }

        return world_dict

    def _handle_reflect(self, plan: dict, tick_number: int):
        """Handle REFLECT action by adding evidence to belief manager."""
        params = plan.get("params", {})
        topic = params.get("topic", "defendant_guilt")
        position = params.get("position", "neutral")
        weight = params.get("weight", 0.5)
        reasoning = params.get("reasoning", "")

        self.belief_manager.add_evidence(
            topic=topic,
            position=position,
            weight=weight,
            source_type="reasoning",
            description=reasoning or f"Reflective reasoning about {topic}",
            tick_added=tick_number,
            confidence=0.8,
        )

        stance = self.belief_manager.calculate_stance(topic)
        if stance:
            logger.info(
                f"📊 {self.profile['name']} Updated stance on {topic}: {stance.position} (confidence: {stance.confidence:.2f})"
            )

    def _calculate_facing_direction(self, actor: core_pb2.Actor) -> Optional[Tuple[float, float]]:
        """
        Calculate the actor's facing direction based on state and interactions.

        Args:
            actor: The actor to calculate facing direction for

        Returns:
            Normalized (dx, dy) facing direction, or None if unknown
        """
        if not actor:
            return None

        # Infer facing from action state (simplified)
        state_lower = actor.state.lower()

        # If actor is in "moving" state, we could track their movement direction
        # For MVP, use a simple heuristic based on state
        if "moving" in state_lower or "walking" in state_lower:
            # In a full implementation, we'd track previous position to infer direction
            # For now, return a default forward direction
            return (1.0, 0.0)
        elif "speaking" in state_lower:
            # When speaking, face towards the most recent interaction target
            if actor.interactions:
                last_interaction = actor.interactions[-1]
                # This would need position info of the target
                # For MVP, use default
                return (1.0, 0.0)

        # Default facing direction
        return (1.0, 0.0)

    def get_visual_context_for_llm(self) -> str:
        """
        Get visual context summary for LLM prompt generation.

        This integrates with PerceptionPipeline to provide spatial awareness
        to the LLM for more grounded decision-making.

        Returns:
            String describing the visual context
        """
        return self.perception.get_visual_context_summary()

    # === COGNITIVE RICHNESS METHODS (Phase 1 & 2) ===

    async def deliberate(self, stimulus: str, others_votes: Dict[str, int]) -> str:
        """
        Phase 1: Thinking before speaking.
        """
        # Sync state
        self.deliberation_engine.update_emotional_state(self.state_manager.get_emotional_context())
        
        result = await self.deliberation_engine.deliberate({
            "stimulus": stimulus,
            "others_votes": others_votes,
            "my_vote": self.profile.get("stance", "neutral")
        })
        
        return result.content

    def get_tone_modifiers(self) -> str:
        """
        Phase 2: Dialogue reflections of emotional state.
        """
        # Sync state
        self.expression_layer.update_pad(self.state_manager.get_emotional_context())
        
        modifiers = self.expression_layer.get_tone_modifiers()
        return modifiers.get_prompt_additions()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Example Juror Profile from 'Angry Man Room'
    juror_profile = {
        "name": "Thomas Wright",
        "stance": "guilty",
        "backstory": "High school teacher for 25 years. Believes in order and rules.",
    }

    brain = AgentBrain(str(uuid.uuid4()), juror_profile)
    asyncio.run(brain.run())
