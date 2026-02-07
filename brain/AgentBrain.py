import asyncio
import uuid
import logging
import json
import re
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

logger = logging.getLogger("AgentBrain")


class AgentBrain:
    """
    The Dual-Mode Cognitive Controller for Tsukuyomi Agents.
    """

    def __init__(
        self, actor_id: str, profile: Dict, server_addr: str = "localhost:50051"
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
            actor_id,
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

        self.state_manager.update(percepts, tick_state.tick_number)

        self.memory.ingest_tick(tick_state)

        if tick_state.tick_number % 10 == 0:
            self.memory.tick_decay(tick_state.tick_number)

        await self._run_reflexes(tick_state)

        reactive_trigger = self._check_reactive_triggers(percepts)

        if not self.is_thinking:
            if reactive_trigger:
                asyncio.create_task(
                    self._deliberate(tick_state, percepts, reason=reactive_trigger)
                )
            elif self._should_deliberate(tick_state):
                asyncio.create_task(
                    self._deliberate(tick_state, percepts, reason="scheduled")
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
        """Rule: Deliberate every 50 ticks with a unique offset."""
        return (tick_state.tick_number + self.tick_offset) % 50 == 0

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
            emotional_modifier = self.state_manager.get_emotional_modifier()
            working_memory_context = self.working_memory.to_llm_context()

            plan = await LLMService.generate_plan_v2(
                self.profile,
                working_memory_context,
                belief_context,
                emotional_modifier,
                reason,
            )

            if self._cancel_current_deliberation:
                return

            if plan["action"] == "REFLECT":
                self._handle_reflect(plan, tick_state.tick_number)

            cot_log = f"/root/.openclaw/workspace/tsukuyomi/experiments/logs/chain_of_thought/{self.profile['name'].replace(' ', '_')}.jsonl"
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
                dialogue_log = "/root/.openclaw/workspace/tsukuyomi/experiments/logs/dialogue/transcript.jsonl"
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

            await self.client.submit_proposal(
                self.actor_id, plan["action"], plan.get("params", {})
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
