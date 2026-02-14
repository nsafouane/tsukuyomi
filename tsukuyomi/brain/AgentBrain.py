import asyncio
import uuid
import logging
import json
import re
import os
from typing import Dict, Optional, List, Any
from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.proto import core_pb2
from tsukuyomi.brain.MemoryManager import MemoryManager
from tsukuyomi.brain.LLMService import LLMService
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

        # FIX: Get drama director instance for sentiment updates
        from tsukuyomi.brain.DramaDirector import DramaDirector

        self.drama_director = None

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
        agent_state = AgentInternalState(
            current_concerns=[],
            mood_label=self.state_manager.state.mood_label,
            arousal=self.state_manager.state.arousal,
            last_seen_entities={},
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

        # FIX: Process gossip propagation each tick
        from tsukuyomi.brain.GossipProtocol import get_gossip_protocol

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
        from tsukuyomi.brain.GossipProtocol import get_gossip_protocol

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

            plan = await LLMService.generate_plan_v2(
                self.profile,
                working_memory_context,
                belief_context,
                relationship_context,
                emotional_modifier,
                reason,
            )

            # FIX: Update drama director sentiment after LLM plan generation
            if self.drama_director:
                sentiment_score = emotional_modifier.get("arousal", 0.5)
                self.drama_director.update_sentiment(sentiment_score)

            if self._cancel_current_deliberation:
                return

            # FIX: Register deliberation with GossipProtocol for information leakage
            from tsukuyomi.brain.GossipProtocol import get_gossip_protocol

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

        except Exception as e:
            logger.error(f"Deliberation failed for {self.profile['name']}: {e}")
        finally:
            self.is_thinking = False

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
