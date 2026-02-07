"""
PerceptionPipeline - Phase 2.1: Perception Foundation

Implements the Perception Layer for Tsukuyomi agents:
- Sensory channels (vision, hearing, proprioception, memory echoes)
- Staggered Perception Schedule (rotating deep perception ticks)
- Salience scoring with Surprise Factor (detecting Memory Echo violations)
- Memory Echo tracking for last-known positions

Reference:
- PHASE_2_SPEC.md §3: Module 1: The Perception Layer
- PHASE_2_REVIEW_SUMMARY.md: Staggered Perception Schedule & Surprise Factor
"""

import math
import uuid
import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from tsukuyomi.proto import core_pb2
from tsukuyomi.proto import perception_pb2
from tsukuyomi.proto import common_pb2

logger = logging.getLogger("PerceptionPipeline")


@dataclass
class SensoryProfile:
    """Configuration for an agent's sensory capabilities."""

    vision_range: float = 20.0  # Max vision distance (meters)
    vision_fov: float = 120.0  # Field of view in degrees
    hearing_range: float = 15.0  # Max hearing distance (meters)
    vision_certainty_decay: float = 0.1  # How fast visual certainty decays per meter
    hearing_certainty_decay: float = (
        0.15  # How fast auditory certainty decays per meter
    )


@dataclass
class AgentInternalState:
    """Simplified agent internal state for perception calculations."""

    current_concerns: List[str]  # Topics the agent is concerned about
    mood_label: str  # "frustrated", "anxious", "calm", etc.
    arousal: float  # 0.0 - 1.0
    last_seen_entities: Dict[str, int]  # entity_id -> last_seen_tick


class PerceptionPipeline:
    """
    Transforms raw WorldState into agent-specific Percepts.

    Implements Staggered Perception Schedule:
    - Every tick: Proximity heartbeat (lightweight)
    - Every N ticks: Deep perception (full vision/occlusion)
    - Rotation ensures full perception without O(A^2) per tick
    """

    # Configuration
    DEEP_PERCEPTION_INTERVAL = 3  # Deep perception every N ticks
    ECHO_DECAY_TICKS = 100  # How long memory echoes last
    ECHO_DECAY_RATE = 0.01  # Per-tick decay for echoes

    # Event type base weights for salience
    SALIENCE_BASE_WEIGHTS = {
        "speech": 0.6,
        "movement": 0.2,
        "violence": 1.0,
        "threat": 0.9,
        "door_opened": 0.3,
        "item_dropped": 0.4,
        "unknown": 0.2,
    }

    def __init__(self, agent_id: str, sensory_profile: SensoryProfile):
        self.agent_id = agent_id
        self.profile = sensory_profile

        # Memory Echo tracking
        self.memory_echoes: Dict[str, perception_pb2.MemoryEcho] = {}

        # Staggered perception state
        self._tick_counter = 0
        self._percept_queue: List[perception_pb2.Percept] = []

        logger.info(f"PerceptionPipeline initialized for agent {agent_id}")

    def process(
        self,
        world_state: core_pb2.WorldState,
        agent_internal_state: AgentInternalState,
        current_tick: int,
    ) -> List[perception_pb2.Percept]:
        """
        Main processing method. Returns salience-sorted percepts.

        Implements Staggered Perception Schedule:
        - Tick % interval == 0: Deep perception (full vision + occlusion)
        - Other ticks: Proximity heartbeat (distance check only)
        """
        self._tick_counter = current_tick
        percepts = []

        # Check if this is a deep perception tick
        is_deep_tick = (current_tick % self.DEEP_PERCEPTION_INTERVAL) == 0

        # Get agent's own position and state
        my_actor = world_state.actors.get(self.agent_id)
        if not my_actor:
            logger.warning(f"Agent {self.agent_id} not found in world state")
            return []

        my_pos = my_actor.position
        my_facing = self._get_facing_vector(my_actor)  # Assuming we can get this

        # Process sensory channels based on schedule
        if is_deep_tick:
            logger.debug(f"Tick {current_tick}: Deep perception for {self.agent_id}")
            percepts.extend(
                self._process_vision_deep(world_state, my_actor, agent_internal_state)
            )
        else:
            logger.debug(
                f"Tick {current_tick}: Proximity heartbeat for {self.agent_id}"
            )
            percepts.extend(self._process_vision_proximity(world_state, my_actor))

        # Always process hearing (omnidirectional, less expensive)
        percepts.extend(
            self._process_hearing(world_state, my_pos, agent_internal_state)
        )

        # Process proprioception (self-state awareness)
        percepts.extend(self._process_proprioception(my_actor, current_tick))

        # Update and process memory echoes
        percepts.extend(self._process_memory_echoes(world_state, current_tick))

        # Calculate Surprise Factor for each percept
        percepts = self._apply_surprise_factor(percepts)

        # Sort by salience (descending)
        percepts.sort(key=lambda p: p.salience, reverse=True)

        self._percept_queue = percepts

        logger.debug(f"Agent {self.agent_id} generated {len(percepts)} percepts")
        return percepts

    def _process_vision_deep(
        self,
        world_state: core_pb2.WorldState,
        my_actor: core_pb2.Actor,
        agent_state: AgentInternalState,
    ) -> List[perception_pb2.Percept]:
        """
        Deep perception: Full FOV + range + occlusion checks.
        Called every N ticks to avoid O(A^2) bottleneck.
        """
        percepts = []
        my_pos = my_actor.position

        for actor_id, actor in world_state.actors.items():
            if actor_id == self.agent_id:
                continue

            # Check FOV cone
            if not self._in_vision_cone(my_pos, actor.position):
                continue

            # Check occlusion (simplified - real implementation needs raycasting)
            if self._is_occluded(my_pos, actor.position, world_state):
                continue

            # Calculate certainty based on distance
            distance = self._distance(my_pos, actor.position)
            certainty = self._calculate_visual_certainty(distance)

            if certainty < 0.1:
                continue

            # Calculate salience with Surprise Factor base
            salience = self._calculate_salience(
                actor, agent_state, my_pos, perception_pb2.Percept.VISION, distance
            )

            # Update memory echo for this actor
            self._update_memory_echo(
                actor_id, "actor", actor.position, self._tick_counter
            )

            percepts.append(
                perception_pb2.Percept(
                    percept_id=str(uuid.uuid4()),
                    tick_observed=self._tick_counter,
                    channel=perception_pb2.Percept.VISION,
                    actor=perception_pb2.ActorPercept(
                        actor_id=actor_id,
                        name=actor.name,
                        approximate_position=self._blur_position(
                            actor.position, certainty
                        ),
                        visible_action_state=actor.state,
                        visible_emotional_cue=self._read_emotional_cue(actor),
                    ),
                    salience=salience,
                    certainty=certainty,
                )
            )

        # Process objects in vision
        for obj_id, obj in world_state.objects.items():
            distance = self._distance(my_pos, obj.position)
            if distance <= self.profile.vision_range:
                certainty = self._calculate_visual_certainty(distance)
                salience = self._calculate_object_salience(obj, distance, agent_state)

                percepts.append(
                    perception_pb2.Percept(
                        percept_id=str(uuid.uuid4()),
                        tick_observed=self._tick_counter,
                        channel=perception_pb2.Percept.VISION,
                        object=perception_pb2.ObjectPercept(
                            object_id=obj_id,
                            apparent_type=obj.type,
                            approximate_position=self._blur_position(
                                obj.position, certainty
                            ),
                            visible_affordances=self._extract_visible_affordances(obj),
                        ),
                        salience=salience,
                        certainty=certainty,
                    )
                )

        return percepts

    def _process_vision_proximity(
        self, world_state: core_pb2.WorldState, my_actor: core_pb2.Actor
    ) -> List[perception_pb2.Percept]:
        """
        Lightweight proximity check. Only tracks entities within critical range.
        No FOV or occlusion checks.
        """
        percepts = []
        my_pos = my_actor.position
        critical_range = 5.0  # Only very close entities

        for actor_id, actor in world_state.actors.items():
            if actor_id == self.agent_id:
                continue

            distance = self._distance(my_pos, actor.position)
            if distance <= critical_range:
                # High certainty for close proximity
                certainty = max(0.5, 1.0 - (distance / critical_range))
                salience = 0.7  # Base salience for close entities

                percepts.append(
                    perception_pb2.Percept(
                        percept_id=str(uuid.uuid4()),
                        tick_observed=self._tick_counter,
                        channel=perception_pb2.Percept.VISION,
                        actor=perception_pb2.ActorPercept(
                            actor_id=actor_id,
                            name=actor.name,
                            approximate_position=actor.position,
                            visible_action_state=actor.state,
                            visible_emotional_cue=self._read_emotional_cue(actor),
                        ),
                        salience=salience,
                        certainty=certainty,
                    )
                )

        return percepts

    def _process_hearing(
        self,
        world_state: core_pb2.WorldState,
        my_pos: common_pb2.Vector2,
        agent_state: AgentInternalState,
    ) -> List[perception_pb2.Percept]:
        """
        Process hearing - omnidirectional within range.
        """
        percepts = []

        # Process speech events from actor interactions
        for actor_id, actor in world_state.actors.items():
            if actor_id == self.agent_id:
                continue

            # Check if actor is speaking (in interaction state)
            if "speaking" in actor.state.lower():
                speaker_pos = actor.position
                distance = self._distance(my_pos, speaker_pos)

                # Assume base loudness for speaking
                loudness = 0.8
                effective_range = self.profile.hearing_range * loudness

                if distance <= effective_range:
                    # Wall attenuation (simplified)
                    wall_attenuation = self._calculate_wall_attenuation(
                        my_pos, speaker_pos, world_state
                    )

                    if wall_attenuation > 0.3:  # Can still hear through walls
                        # Extract speech content from interactions if available
                        speech_content = self._extract_speech_content(actor)

                        percepts.append(
                            perception_pb2.Percept(
                                percept_id=str(uuid.uuid4()),
                                tick_observed=self._tick_counter,
                                channel=perception_pb2.Percept.HEARING,
                                speech=perception_pb2.SpeechPercept(
                                    speaker_id=actor_id,
                                    speaker_name=actor.name,
                                    content=speech_content,
                                    loudness=loudness * wall_attenuation,
                                    is_direct_address=self._is_direct_address(
                                        speech_content
                                    ),
                                ),
                                salience=self._calculate_speech_salience(
                                    speech_content, agent_state, wall_attenuation
                                ),
                                certainty=wall_attenuation,
                            )
                        )

        return percepts

    def _process_proprioception(
        self, my_actor: core_pb2.Actor, current_tick: int
    ) -> List[perception_pb2.Percept]:
        """
        Self-state awareness. Always accurate (certainty = 1.0).
        """
        # Proprioception is typically low salience unless state changed
        percepts = []

        percepts.append(
            perception_pb2.Percept(
                percept_id=str(uuid.uuid4()),
                tick_observed=current_tick,
                channel=perception_pb2.Percept.PROPRIOCEPTION,
                actor=perception_pb2.ActorPercept(
                    actor_id=self.agent_id,
                    name=my_actor.name,
                    approximate_position=my_actor.position,
                    visible_action_state=my_actor.state,
                    visible_emotional_cue="self",
                ),
                salience=0.05,  # Low salience for self-awareness
                certainty=1.0,  # Always accurate
            )
        )

        return percepts

    def _process_memory_echoes(
        self, world_state: core_pb2.WorldState, current_tick: int
    ) -> List[perception_pb2.Percept]:
        """
        Generate percepts for memory echoes of entities not currently seen.
        """
        percepts = []
        echoes_to_remove = []

        for entity_id, echo in self.memory_echoes.items():
            # Decay echo certainty
            echo.current_certainty -= self.ECHO_DECAY_RATE

            # Remove expired echoes
            if echo.current_certainty <= 0.1:
                echoes_to_remove.append(entity_id)
                continue

            # Check if entity is currently in world
            if echo.entity_type == "actor":
                if entity_id in world_state.actors:
                    # Entity exists but not seen this tick
                    percepts.append(
                        perception_pb2.Percept(
                            percept_id=str(uuid.uuid4()),
                            tick_observed=current_tick,
                            channel=perception_pb2.Percept.MEMORY_ECHO,
                            actor=perception_pb2.ActorPercept(
                                actor_id=entity_id,
                                approximate_position=echo.last_position,
                                visible_action_state="unknown",
                                visible_emotional_cue="unknown",
                            ),
                            salience=0.1,  # Low salience for memory echoes
                            certainty=echo.current_certainty,
                        )
                    )

        # Remove expired echoes
        for entity_id in echoes_to_remove:
            del self.memory_echoes[entity_id]

        return percepts

    def _update_memory_echo(
        self,
        entity_id: str,
        entity_type: str,
        position: common_pb2.Vector2,
        current_tick: int,
    ):
        """Update or create a memory echo for an entity."""
        if entity_id in self.memory_echoes:
            echo = self.memory_echoes[entity_id]
            echo.last_position.CopyFrom(position)
            echo.last_seen_tick = current_tick
            echo.current_certainty = 1.0  # Reset certainty
        else:
            self.memory_echoes[entity_id] = perception_pb2.MemoryEcho(
                entity_id=entity_id,
                entity_type=entity_type,
                last_position=position,
                last_seen_tick=current_tick,
                decay_rate=self.ECHO_DECAY_RATE,
                current_certainty=1.0,
            )

    def _apply_surprise_factor(
        self, percepts: List[perception_pb2.Percept]
    ) -> List[perception_pb2.Percept]:
        """
        Apply Surprise Factor refinement from review:
        Boost salience for events that violate Memory Echo expectations.

        Examples:
        - Seeing a door open that was previously closed
        - Seeing an actor at a different position than their memory echo
        - Hearing an actor who should be elsewhere (based on echo)
        """
        for percept in percepts:
            entity_id = None
            expected_position = None

            # Extract entity info based on percept type
            if percept.HasField("actor"):
                entity_id = percept.actor.actor_id
            elif percept.HasField("object"):
                entity_id = percept.object.object_id

            if entity_id and entity_id in self.memory_echoes:
                echo = self.memory_echoes[entity_id]

                # Check for position violation
                if percept.HasField("actor"):
                    actual_pos = percept.actor.approximate_position
                    expected_pos = echo.last_position
                    distance_from_echo = self._distance(actual_pos, expected_pos)

                    # Surprise: Actor moved faster than expected or teleported
                    ticks_since_seen = self._tick_counter - echo.last_seen_tick
                    if (
                        ticks_since_seen < self.ECHO_DECAY_TICKS
                        and distance_from_echo > 2.0
                    ):
                        surprise_boost = 0.3 * (distance_from_echo / 5.0)
                        percept.salience = min(1.0, percept.salience + surprise_boost)
                        logger.debug(
                            f"Surprise! Entity {entity_id} moved {distance_from_echo:.1f}m "
                            f"in {ticks_since_seen} ticks. Salience boosted to {percept.salience:.2f}"
                        )

            # Surprise for unexpected state changes
            if percept.HasField("event"):
                event_type = percept.event.event_type
                # Unexpected events get surprise boost
                if event_type in ["door_opened", "sudden_movement", "violence"]:
                    percept.salience = min(1.0, percept.salience + 0.2)
                    logger.debug(f"Surprise! Unexpected event: {event_type}")

        return percepts

    # ===== Helper Methods =====

    def _distance(self, pos1: common_pb2.Vector2, pos2: common_pb2.Vector2) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return math.sqrt(dx * dx + dy * dy)

    def _in_vision_cone(
        self, my_pos: common_pb2.Vector2, target_pos: common_pb2.Vector2
    ) -> bool:
        """
        Check if target is within FOV cone.
        Simplified implementation - assumes agent faces +X direction.
        Real implementation would track agent's facing direction.
        """
        distance = self._distance(my_pos, target_pos)
        if distance > self.profile.vision_range:
            return False

        # Calculate angle to target
        dx = target_pos.x - my_pos.x
        dy = target_pos.y - my_pos.y
        angle = math.degrees(math.atan2(dy, dx))

        # Check if within FOV (assuming facing +X, so angle should be within [-FOV/2, FOV/2])
        fov_half = self.profile.vision_fov / 2
        return abs(angle) <= fov_half

    def _is_occluded(
        self,
        start_pos: common_pb2.Vector2,
        end_pos: common_pb2.Vector2,
        world_state: core_pb2.WorldState,
    ) -> bool:
        """
        Check if line of sight is blocked by objects/walls.
        Simplified implementation - real version would use raycasting.
        """
        # TODO: Implement proper raycasting occlusion
        # For now, return False (no occlusion)
        return False

    def _calculate_visual_certainty(self, distance: float) -> float:
        """Calculate visual certainty based on distance."""
        if distance <= 0:
            return 1.0
        return max(
            0.0,
            1.0
            - (
                distance
                * self.profile.vision_certainty_decay
                / self.profile.vision_range
            ),
        )

    def _calculate_wall_attenuation(
        self,
        start_pos: common_pb2.Vector2,
        end_pos: common_pb2.Vector2,
        world_state: core_pb2.WorldState,
    ) -> float:
        """Calculate sound attenuation through walls."""
        # TODO: Implement proper wall detection
        # For now, return 1.0 (no attenuation)
        return 1.0

    def _calculate_salience(
        self,
        target: core_pb2.Actor,
        agent_state: AgentInternalState,
        my_pos: common_pb2.Vector2,
        channel: int,
        distance: float,
    ) -> float:
        """
        Calculate salience score for a percept.

        Formula from spec:
        Salience = (BaseWeight × EmotionalRelevance) + (Proximity × 0.3) + (DirectAddress × 0.5) + (Novelty × 0.2)
        """
        # Base weight based on action state
        base_weight = 0.2  # Default for seeing an actor
        if "speaking" in target.state.lower():
            base_weight = self.SALIENCE_BASE_WEIGHTS["speech"]
        elif "violence" in target.state.lower():
            base_weight = self.SALIENCE_BASE_WEIGHTS["violence"]

        # Emotional relevance (simplified)
        emotional_relevance = 1.0
        if agent_state.current_concerns:
            # If actor name appears in concerns, boost relevance
            for concern in agent_state.current_concerns:
                if concern.lower() in target.name.lower():
                    emotional_relevance = 1.3
                    break

        # Proximity
        proximity = max(0.0, 1.0 - (distance / self.profile.vision_range))

        # Direct address (for vision, check if looking at agent)
        direct_address = 0.0
        if channel == perception_pb2.Percept.HEARING:
            # Direct address is handled in speech salience
            pass

        # Novelty (has this entity been seen recently?)
        novelty = 0.0
        # Use actor_id instead of target.id
        actor_id = getattr(target, "id", None) or getattr(target, "name", "")
        if actor_id not in agent_state.last_seen_entities:
            novelty = 0.2
        else:
            ticks_since_seen = (
                self._tick_counter - agent_state.last_seen_entities[actor_id]
            )
            if ticks_since_seen > 100:
                novelty = 0.2

        # Calculate final salience
        salience = (
            (base_weight * emotional_relevance) + (proximity * 0.3) + (novelty * 0.2)
        )

        return min(1.0, max(0.0, salience))

    def _calculate_object_salience(
        self,
        obj: core_pb2.EnvironmentObject,
        distance: float,
        agent_state: AgentInternalState,
    ) -> float:
        """Calculate salience for object perception."""
        # Base salience for objects
        base_weight = 0.2

        # Boost for interactive objects
        if obj.interactive:
            base_weight += 0.2

        # Proximity
        proximity = max(0.0, 1.0 - (distance / self.profile.vision_range))

        salience = base_weight + (proximity * 0.3)
        return min(1.0, salience)

    def _calculate_speech_salience(
        self, content: str, agent_state: AgentInternalState, wall_attenuation: float
    ) -> float:
        """Calculate salience for speech perception."""
        base_weight = self.SALIENCE_BASE_WEIGHTS["speech"]

        # Check for direct address
        direct_address = 0.0
        if self._is_direct_address(content):
            direct_address = 0.5

        # Check emotional relevance
        emotional_relevance = 1.0
        for concern in agent_state.current_concerns:
            if concern.lower() in content.lower():
                emotional_relevance = 1.3
                break

        # Apply wall attenuation
        salience = (base_weight * emotional_relevance) + direct_address
        salience *= wall_attenuation  # Muffled speech is less salient

        return min(1.0, max(0.0, salience))

    def _blur_position(
        self, position: common_pb2.Vector2, certainty: float
    ) -> common_pb2.Vector2:
        """
        Blur position based on certainty.
        Less certain = more positional error.
        """
        if certainty >= 0.9:
            return position

        # Add random noise based on uncertainty
        noise = (1.0 - certainty) * 2.0  # Up to 2m error
        blurred = common_pb2.Vector2(
            x=position.x + (random.random() - 0.5) * noise,
            y=position.y + (random.random() - 0.5) * noise,
        )
        return blurred

    def _read_emotional_cue(self, actor: core_pb2.Actor) -> str:
        """
        Read visible emotional cue from actor state.
        Simplified - real implementation would have explicit emotional states.
        """
        # Infer emotion from action state
        if "agitated" in actor.state.lower():
            return "angry"
        elif "calm" in actor.state.lower():
            return "calm"
        elif "happy" in actor.state.lower():
            return "happy"
        else:
            return "neutral"

    def _get_facing_vector(self, actor: core_pb2.Actor) -> common_pb2.Vector2:
        """
        Get the direction the actor is facing.
        Simplified - assumes +X direction.
        Real implementation would track rotation.
        """
        return common_pb2.Vector2(x=1.0, y=0.0)

    def _extract_speech_content(self, actor: core_pb2.Actor) -> str:
        """
        Extract speech content from actor interactions.
        Simplified - returns placeholder.
        Real implementation would have actual speech content.
        """
        # Look for speech in interactions
        for interaction in actor.interactions:
            if interaction.type == "talk" or interaction.type == "speak":
                # Try to extract message from interaction details
                # For now, return placeholder
                return "speech detected"
        return "speech detected"

    def _is_direct_address(self, speech_content: str) -> bool:
        """Check if speech is a direct address to this agent."""
        # Simple heuristic: look for "you" or direct address markers
        direct_address_patterns = ["you", "hey", "listen", "excuse me"]
        content_lower = speech_content.lower()
        return any(pattern in content_lower for pattern in direct_address_patterns)

    def _extract_visible_affordances(
        self, obj: core_pb2.EnvironmentObject
    ) -> List[str]:
        """
        Extract visible affordances from object.
        Simplified - returns basic affordances for interactive objects.
        """
        if not obj.interactive:
            return []

        # Basic affordances for interactive objects
        affordances = ["examine"]

        # Add type-specific affordances
        obj_type = obj.type.lower()
        if obj_type in ["item", "food", "weapon", "tool"]:
            affordances.append("take")
        if obj_type in ["door", "container", "chest"]:
            affordances.append("open")

        return affordances
