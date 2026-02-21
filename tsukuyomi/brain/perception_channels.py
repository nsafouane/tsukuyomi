import logging
import uuid
import time
import math
import random
from typing import List, Dict, Optional, Any, Tuple
from tsukuyomi.proto import core_pb2, common_pb2, perception_pb2
from .spatial_utils import Raycaster, SensoryProfile, AgentInternalState

logger = logging.getLogger("PerceptionChannels")

class PerceptionChannelsMixin:
    def _process_vision_deep(
        self,
        world_state: core_pb2.WorldState,
        my_actor: core_pb2.Actor,
        agent_state: AgentInternalState,
        my_pos: Tuple[float, float],
        my_facing: Tuple[float, float],
    ) -> List[perception_pb2.Percept]:
        """
        Deep perception: Full FOV + range + occlusion checks.
        Called every N ticks to avoid O(A^2) bottleneck.

        Enhanced with:
        - Accurate FOV cone calculation using raycasting
        - Line-of-sight checking against walls
        - Spatial index for efficient proximity filtering
        """
        percepts = []
        visible_polygon = self.raycaster.get_visible_polygon(
            my_pos,
            my_facing,
            self.profile.vision_fov,
            self.profile.vision_range,
            room_id=my_actor.current_location,
            num_rays=32,
        )

        # Query spatial index for nearby actors (performance optimization)
        nearby_actors = []
        if self.spatial_index:
            # Query for actors within vision range
            spatial_results = self.spatial_index.query(
                my_pos, radius=self.profile.vision_range, exclude_self=self.agent_id
            )
            nearby_actors = [
                (obj_id, pos)
                for obj_id, pos in spatial_results
                if obj_id in world_state.actors
            ]
            logger.debug(
                f"Spatial index found {len(nearby_actors)} nearby actors for agent {self.agent_id}"
            )
        else:
            # Fallback: check all actors
            nearby_actors = [
                (actor_id, (actor.position.x, actor.position.y))
                for actor_id, actor in world_state.actors.items()
                if actor_id != self.agent_id
            ]

        # Process each nearby actor
        for actor_id, actor_pos in nearby_actors:
            # Check FOV cone
            if not self._in_vision_cone(my_pos, actor_pos, my_facing):
                continue

            # Check occlusion using raycasting
            if not self.raycaster.is_point_visible(
                my_pos, actor_pos, room_id=my_actor.current_location
            ):
                continue

            # Calculate distance and certainty
            distance = self._distance(my_pos, actor_pos)
            certainty = self._calculate_visual_certainty(distance)

            if certainty < 0.1:
                continue

            # Get actor object
            actor = world_state.actors.get(actor_id)
            if not actor:
                continue

            # Calculate salience with Surprise Factor base
            salience = self._calculate_salience(
                actor, agent_state, my_pos, perception_pb2.Percept.VISION, distance
            )

            # Update memory echo for this actor
            self._update_memory_echo(
                actor_id, "actor", common_pb2.Vector2(x=actor_pos[0], y=actor_pos[1]), self._tick_counter
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
                            common_pb2.Vector2(x=actor_pos[0], y=actor_pos[1]), certainty
                        ),
                        visible_action_state=actor.state,
                        visible_emotional_cue=self._read_emotional_cue(actor),
                    ),
                    salience=salience,
                    certainty=certainty,
                )
            )

        # Process objects in vision (using spatial index if available)
        nearby_objects = []
        if self.spatial_index:
            # Query for objects within vision range
            spatial_results = self.spatial_index.query(
                my_pos, radius=self.profile.vision_range, exclude_self=None
            )
            # Filter out actors (they're handled separately)
            nearby_objects = [
                (obj_id, pos)
                for obj_id, pos in spatial_results
                if obj_id not in world_state.actors and obj_id in world_state.objects
            ]
        else:
            # Fallback: check all objects
            nearby_objects = [
                (obj_id, (obj.position.x, obj.position.y))
                for obj_id, obj in world_state.objects.items()
            ]

        for obj_id, obj_pos in nearby_objects:
            distance = self._distance(my_pos, obj_pos)
            if distance > self.profile.vision_range:
                continue

            # Check FOV cone
            if not self._in_vision_cone(my_pos, obj_pos, my_facing):
                continue

            # Check occlusion
            if not self.raycaster.is_point_visible(
                my_pos, obj_pos, room_id=my_actor.current_location
            ):
                continue

            obj = world_state.objects.get(obj_id)
            if not obj:
                continue

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
                            common_pb2.Vector2(x=obj_pos[0], y=obj_pos[1]), certainty
                        ),
                        visible_affordances=self._extract_visible_affordances(obj),
                    ),
                    salience=salience,
                    certainty=certainty,
                )
            )

        return percepts

    def _process_vision_proximity(
        self,
        world_state: core_pb2.WorldState,
        my_actor: core_pb2.Actor,
        agent_state: AgentInternalState,
        my_pos: Tuple[float, float],
    ) -> List[perception_pb2.Percept]:
        """
        Lightweight proximity check. Only tracks entities within critical range.
        No FOV or occlusion checks (assumes very close entities are always visible).

        Enhanced with spatial index for O(1) proximity queries.
        """
        percepts = []
        critical_range = 5.0  # Only very close entities

        # Use spatial index for efficient proximity query
        if self.spatial_index:
            spatial_results = self.spatial_index.query(
                my_pos, radius=critical_range, exclude_self=self.agent_id
            )
            nearby_entities = [
                (obj_id, pos)
                for obj_id, pos in spatial_results
                if obj_id in world_state.actors
            ]
        else:
            # Fallback: check all actors
            nearby_entities = [
                (actor_id, (actor.position.x, actor.position.y))
                for actor_id, actor in world_state.actors.items()
                if actor_id != self.agent_id
            ]

        for actor_id, actor_pos in nearby_entities:
            distance = self._distance(my_pos, actor_pos)
            if distance <= critical_range:
                # High certainty for close proximity
                certainty = max(0.5, 1.0 - (distance / critical_range))
                salience = 0.7  # Base salience for close entities

                actor = world_state.actors.get(actor_id)
                if not actor:
                    continue

                percepts.append(
                    perception_pb2.Percept(
                        percept_id=str(uuid.uuid4()),
                        tick_observed=self._tick_counter,
                        channel=perception_pb2.Percept.VISION,
                        actor=perception_pb2.ActorPercept(
                            actor_id=actor_id,
                            name=actor.name,
                            approximate_position=common_pb2.Vector2(
                                x=actor_pos[0], y=actor_pos[1]
                            ),
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
        my_pos: Tuple[float, float],
        agent_state: AgentInternalState,
    ) -> List[perception_pb2.Percept]:
        """
        Process hearing - omnidirectional within range.
        """
        percepts = []

        # Use spatial index for efficient hearing range queries
        if self.spatial_index:
            spatial_results = self.spatial_index.query(
                my_pos, radius=self.profile.hearing_range, exclude_self=self.agent_id
            )
            nearby_actors = [
                (obj_id, pos)
                for obj_id, pos in spatial_results
                if obj_id in world_state.actors
            ]
        else:
            # Fallback: check all actors
            nearby_actors = [
                (actor_id, (actor.position.x, actor.position.y))
                for actor_id, actor in world_state.actors.items()
                if actor_id != self.agent_id
            ]

        # Process speech events from actor interactions
        for actor_id, actor_pos in nearby_actors:
            actor = world_state.actors.get(actor_id)
            if not actor:
                continue

            # Check if actor is speaking (in interaction state)
            if "speaking" in actor.state.lower():
                distance = self._distance(my_pos, actor_pos)

                # Assume base loudness for speaking
                loudness = 0.8
                effective_range = self.profile.hearing_range * loudness

                if distance <= effective_range:
                    # Wall attenuation (using raycaster)
                    wall_attenuation = self._calculate_wall_attenuation(
                        my_pos, actor_pos, world_state
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

    def _process_gossip_channel(
        self, world_state: core_pb2.WorldState, current_tick: int
    ) -> List[perception_pb2.Percept]:
        """
        Process gossip channel - convert rumors into percepts.
        """
        percepts = []

        try:
            from tsukuyomi.brain.gossip_protocol import get_gossip_protocol

            gossip_protocol = get_gossip_protocol()
            recent_gossip = gossip_protocol.get_gossip_for_agent(self.agent_id)

            for gossip in recent_gossip:
                # Convert gossip into percepts with HEARING channel
                percepts.append(
                    perception_pb2.Percept(
                        percept_id=str(uuid.uuid4()),
                        tick_observed=current_tick,
                        channel=perception_pb2.Percept.HEARING,
                        speech=perception_pb2.SpeechPercept(
                            speaker_id=gossip.source_actor_id,
                            speaker_name=gossip.source_actor_name or "Unknown",
                            content=gossip.content,
                            loudness=0.5,
                            is_direct_address=False,
                        ),
                        salience=0.3,  # Moderate salience for gossip
                        certainty=0.6,  # Moderate certainty
                    )
                )
        except ImportError:
            logger.debug("GossipProtocol not available, skipping gossip processing")
        except Exception as e:
            logger.error(f"Error processing gossip channel: {e}")

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
                    distance_from_echo = self._distance(
                        (actual_pos.x, actual_pos.y),
                        (expected_pos.x, expected_pos.y),
                    )

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

    def _distance(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return math.sqrt(dx * dx + dy * dy)

    def _in_vision_cone(
        self,
        my_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        facing: Tuple[float, float],
    ) -> bool:
        """
        Check if target is within FOV cone using the facing direction.

        Args:
            my_pos: Agent's position (x, y)
            target_pos: Target's position (x, y)
            facing: Normalized facing direction vector (dx, dy)

        Returns:
            True if target is within FOV cone, False otherwise
        """
        distance = self._distance(my_pos, target_pos)
        if distance > self.profile.vision_range:
            return False

        # Calculate angle to target
        dx = target_pos[0] - my_pos[0]
        dy = target_pos[1] - my_pos[1]
        target_angle = math.atan2(dy, dx)

        # Calculate facing angle
        facing_angle = math.atan2(facing[1], facing[0])

        # Calculate angle difference
        angle_diff = abs(target_angle - facing_angle)
        # Handle angle wraparound (e.g., 359° vs 1°)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        # Check if within FOV
        fov_half_rad = math.radians(self.profile.vision_fov / 2)
        return angle_diff <= fov_half_rad

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
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        world_state: core_pb2.WorldState,
    ) -> float:
        """
        Calculate sound attenuation through walls using raycasting.

        Returns:
            Attenuation factor (0.0 = fully blocked, 1.0 = no attenuation)
        """
        # Use raycaster to check if walls block the sound
        blocked, _, _ = self.raycaster.cast_ray(start_pos, end_pos, step_size=1.0)

        if blocked:
            # Sound attenuated by walls
            return 0.4  # Can still hear faintly through walls
        else:
            return 1.0  # No attenuation

    def _calculate_salience(
        self,
        target: core_pb2.Actor,
        agent_state: AgentInternalState,
        my_pos: Tuple[float, float],
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

    def _get_facing_vector(
        self, actor: core_pb2.Actor, agent_state: AgentInternalState
    ) -> Tuple[float, float]:
        """
        Get the direction the actor is facing.

        Uses agent_state.facing_direction if available, otherwise defaults to +X.
        Real implementation would track rotation or movement direction.
        """
        if agent_state.facing_direction:
            # Normalize if needed
            fx, fy = agent_state.facing_direction
            mag = math.sqrt(fx**2 + fy**2)
            if mag > 0:
                return (fx / mag, fy / mag)
        return (1.0, 0.0)  # Default: facing +X

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

    def get_visual_context_summary(self) -> str:
        """
        Generate a summary of the current visual context for LLM prompts.

        Returns:
            String describing what the agent can currently see
        """
        if not self._percept_queue:
            return "You don't see anything notable right now."

        # Filter for vision channel percepts
        vision_percepts = [
            p for p in self._percept_queue if p.channel == perception_pb2.Percept.VISION
        ]

        if not vision_percepts:
            return "Your immediate surroundings are clear."

        # Build summary
        summary_parts = []
        seen_actors = []
        seen_objects = []

        for percept in vision_percepts[:10]:  # Top 10 salient
            if percept.HasField("actor"):
                actor = percept.actor
                seen_actors.append(f"{actor.name} (state: {actor.visible_action_state})")
            elif percept.HasField("object"):
                obj = percept.object
                seen_objects.append(f"{obj.apparent_type}")

        if seen_actors:
            summary_parts.append(f"Nearby: {', '.join(seen_actors)}")
        if seen_objects:
            summary_parts.append(f"Visible objects: {', '.join(seen_objects)}")

        return " | ".join(summary_parts) if summary_parts else "Your vision is unobstructed."
