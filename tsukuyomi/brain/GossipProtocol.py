"""
Gossip Protocol - Information Leakage Between Deliberating Agents

The Gossip Protocol enables information exchange between agents during deliberation,
simulating how real people share and spread information through conversation,
observation, and social interaction.

Key Concepts:
- Gossip: Information shared between agents
- Leakage Probability: Chance that information spreads between agents
- Information Decay: Gossip becomes less accurate over time
- Social Proximity: Agents closer together are more likely to gossip

Author: Tanit (OpenClaw Agent)
Date: February 7, 2026
"""

import logging
import random
import time
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger("GossipProtocol")


@dataclass
class GossipItem:
    """
    A single piece of gossip information.
    """
    id: str  # Unique ID for tracking
    content: str  # The gossip message itself
    source_actor_id: str  # Who originally shared this gossip
    original_tick: int  # When this gossip was first created
    propagation_count: int = 0  # How many times it has been shared
    accuracy: float = 1.0  # Accuracy decays as gossip spreads
    tags: List[str] = None  # Type of gossip (e.g., "stance", "observation", "rumor")

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class GossipEvent:
    """
    Records when gossip was shared between actors.
    """
    tick: int  # When the gossip happened
    from_actor_id: str  # Who shared the gossip
    to_actor_id: str  # Who received the gossip
    gossip_id: str  # Which gossip was shared
    method: str  # How it was shared (e.g., "overhearing", "conversation", "observation")


class GossipProtocol:
    """
    Manages information exchange between deliberating agents.
    
    The protocol works by:
    1. Agents register their current deliberation thoughts
    2. There's a probability that other agents "overhear" these thoughts
    3. Overheard information becomes gossip items
    4. Gossip propagates through the agent network
    """

    def __init__(
        self,
        base_leakage_probability: float = 0.1,  # 10% chance of overhearing per tick
        proximity_multiplier: float = 2.0,  # 2x chance if actors are close
        accuracy_decay: float = 0.1,  # 10% accuracy loss per propagation
        max_propagation_depth: int = 5,  # Gossip stops after 5 hops
    ):
        self.base_leakage_probability = base_leakage_probability
        self.proximity_multiplier = proximity_multiplier
        self.accuracy_decay = accuracy_decay
        self.max_propagation_depth = max_propagation_depth

        # Storage
        self.gossip_items: Dict[str, GossipItem] = {}  # gossip_id -> GossipItem
        self.gossip_events: List[GossipEvent] = []  # History of gossip exchanges
        self.agent_gossip_memory: Dict[str, Set[str]] = {}  # actor_id -> set of gossip_ids they know

        # Current deliberation thoughts (for this tick)
        self.current_deliberations: Dict[str, Dict] = {}  # actor_id -> thought data

        logger.info(
            f"GossipProtocol initialized: "
            f"leakage={base_leakage_probability}, "
            f"proximity_mult={proximity_multiplier}, "
            f"accuracy_decay={accuracy_decay}"
        )

    def register_deliberation(
        self,
        actor_id: str,
        thought: str,
        action: str,
        tick: int,
        world_state_context: Optional[Dict] = None
    ):
        """
        Register an agent's current deliberation thought.

        This is called when an agent is about to make a decision.
        Other agents might "overhear" this thought and use it in their reasoning.
        """
        deliberation_data = {
            "actor_id": actor_id,
            "thought": thought,
            "action": action,
            "tick": tick,
            "world_state": world_state_context
        }

        self.current_deliberations[actor_id] = deliberation_data

        logger.debug(f"Registered deliberation for {actor_id}: {thought[:50]}...")

    def process_gossip(self, tick: int) -> List[GossipEvent]:
        """
        Process gossip for this tick.

        Returns a list of new gossip events that occurred.
        """
        # Periodic pruning (every 100 ticks)
        if tick % 100 == 0:
            self.prune_history(tick)

        new_events = []

        # For each agent deliberating, check if others overhear them
        for source_actor_id, deliberation in self.current_deliberations.items():
            # Check which other actors might overhear
            potential_recipients = [
                actor_id for actor_id in self.current_deliberations.keys()
                if actor_id != source_actor_id
            ]

            for recipient_actor_id in potential_recipients:
                if self._should_gossip(source_actor_id, recipient_actor_id, deliberation):
                    # Create gossip item if it doesn't exist
                    gossip = self._create_gossip_from_deliberation(
                        source_actor_id, deliberation, tick
                    )

                    # Check if recipient already knows this gossip
                    known_gossip = self.agent_gossip_memory.get(recipient_actor_id, set())

                    if gossip.id not in known_gossip:
                        # Share gossip
                        event = GossipEvent(
                            tick=tick,
                            from_actor_id=source_actor_id,
                            to_actor_id=recipient_actor_id,
                            gossip_id=gossip.id,
                            method="overhearing"
                        )

                        new_events.append(event)
                        self.gossip_events.append(event)

                        # Update agent's memory
                        self.agent_gossip_memory.setdefault(recipient_actor_id, set()).add(gossip.id)

                        # Impact affinity based on gossip (Step 3 of Phase 9)
                        # In a real system, we'd analyze sentiment. For now, small random impact
                        # representing 'the act of sharing'
                        # Note: GossipProtocol is global, it doesn't have direct access to AgentBrain instances.
                        # We'll log it and the AgentBrain can pick it up if we had a registry.
                        # For now, let's just log the intent.

                        # Potentially decay gossip accuracy
                        self._propagate_gossip(gossip)

                        logger.info(
                            f"🗣️ GOSSIP: {source_actor_id} -> {recipient_actor_id}: "
                            f'"{gossip.content[:50]}..." '
                            f'(accuracy: {gossip.accuracy:.2f})'
                        )

        # Clear current deliberations for next tick
        self.current_deliberations.clear()

        return new_events

    def prune_history(self, current_tick: int, max_age: int = 1000):
        """
        Prune old gossip events and memory to prevent memory leaks.
        """
        # 1. Remove old events
        self.gossip_events = [
            e for e in self.gossip_events 
            if (current_tick - e.tick) < max_age
        ]

        # 2. Prune gossip items that are no longer referenced in events
        active_gossip_ids = {e.gossip_id for e in self.gossip_events}
        
        # Also keep items that were just created (within max_age)
        for gid, item in list(self.gossip_items.items()):
            if gid not in active_gossip_ids and (current_tick - item.original_tick) >= max_age:
                del self.gossip_items[gid]

        # 3. Prune agent memory of removed gossip IDs
        current_gossip_ids = set(self.gossip_items.keys())
        for actor_id in list(self.agent_gossip_memory.keys()):
            self.agent_gossip_memory[actor_id] &= current_gossip_ids
            
            # Remove actor from memory if they know nothing
            if not self.agent_gossip_memory[actor_id]:
                del self.agent_gossip_memory[actor_id]

        logger.debug(f"Pruned gossip history at tick {current_tick}. Active items: {len(self.gossip_items)}")

    def _should_gossip(
        self,
        source_actor_id: str,
        recipient_actor_id: str,
        deliberation: Dict
    ) -> bool:
        """
        Determine if gossip should occur between two agents.
        """
        # Base probability
        probability = self.base_leakage_probability

        # Proximity bonus if actors are close together
        world_state = deliberation.get("world_state", {})
        if self._actors_are_proximal(source_actor_id, recipient_actor_id, world_state):
            probability *= self.proximity_multiplier

        # Roll for gossip
        should_gossip = random.random() < probability

        logger.debug(
            f"Gossip check {source_actor_id} -> {recipient_actor_id}: "
            f"prob={probability:.3f}, result={should_gossip}"
        )

        return should_gossip

    def _actors_are_proximal(
        self,
        actor1_id: str,
        actor2_id: str,
        world_state: Dict
    ) -> bool:
        """
        Check if two actors are close enough for gossip.
        """
        # Extract actor positions from world state
        actors = world_state.get("actors", {})
        actor1 = actors.get(actor1_id)
        actor2 = actors.get(actor2_id)

        if not actor1 or not actor2:
            return False

        # Calculate distance
        pos1 = actor1.get("position", {})
        pos2 = actor2.get("position", {})

        if "x" not in pos1 or "y" not in pos1:
            return False
        if "x" not in pos2 or "y" not in pos2:
            return False

        distance = ((pos1["x"] - pos2["x"])**2 + (pos1["y"] - pos2["y"])**2)**0.5

        # Define proximity threshold (e.g., within 5 units)
        is_proximal = distance < 5.0

        if is_proximal:
            logger.debug(f"Actors {actor1_id} and {actor2_id} are proximal (dist={distance:.2f})")

        return is_proximal

    def _create_gossip_from_deliberation(
        self,
        source_actor_id: str,
        deliberation: Dict,
        tick: int
    ) -> GossipItem:
        """
        Create a gossip item from an agent's deliberation.
        """
        thought = deliberation.get("thought", "")
        action = deliberation.get("action", "")

        # Create gossip content
        content = f"{source_actor_id} was thinking: {thought}"

        # Generate unique ID
        gossip_id = f"{source_actor_id}_{tick}_{hash(content) & 0xFFFFFFFFFFFFFFFF}"

        # Check if gossip already exists
        if gossip_id in self.gossip_items:
            return self.gossip_items[gossip_id]

        # Create new gossip item
        gossip = GossipItem(
            id=gossip_id,
            content=content,
            source_actor_id=source_actor_id,
            original_tick=tick,
            propagation_count=0,
            accuracy=1.0,
            tags=["deliberation", action.lower()]
        )

        self.gossip_items[gossip_id] = gossip

        return gossip

    def _propagate_gossip(self, gossip: GossipItem):
        """
        Update gossip metadata when it propagates.
        """
        gossip.propagation_count += 1

        # Decay accuracy based on propagation depth
        if gossip.propagation_count > 1:
            gossip.accuracy *= (1.0 - self.accuracy_decay)

        # Cap propagation depth
        if gossip.propagation_count >= self.max_propagation_depth:
            # Mark gossip as "stopped" - don't propagate further
            gossip.tags.append("stopped")

        logger.debug(
            f"Gossip {gossip.id} propagated (count={gossip.propagation_count}, "
            f"accuracy={gossip.accuracy:.2f})"
        )

    def get_gossip_for_agent(self, actor_id: str) -> List[GossipItem]:
        """
        Get all gossip items known to an agent.
        """
        known_gossip_ids = self.agent_gossip_memory.get(actor_id, set())
        gossip_list = []

        for gossip_id in known_gossip_ids:
            if gossip_id in self.gossip_items:
                gossip_list.append(self.gossip_items[gossip_id])

        return gossip_list

    def get_gossip_summary_for_agent(self, actor_id: str) -> str:
        """
        Get a formatted summary of gossip known to an agent.
        Used in LLM prompts for deliberation.
        """
        gossip_items = self.get_gossip_for_agent(actor_id)

        if not gossip_items:
            return "You haven't heard any gossip recently."

        summary_lines = ["GOSSIP YOU'VE HEARD:"]

        for gossip in gossip_items[-10:]:  # Last 10 gossip items
            summary_lines.append(
                f"- {gossip.content[:100]}... "
                f"(from {gossip.source_actor_id}, "
                f"accuracy: {gossip.accuracy:.1f})"
            )

        return "\n".join(summary_lines)

    def export_events(self) -> str:
        """
        Export all gossip events to JSON string for analysis.
        """
        events_data = [asdict(event) for event in self.gossip_events]
        return json.dumps(events_data, indent=2)

    def get_statistics(self) -> Dict:
        """
        Get statistics about gossip propagation.
        """
        total_gossip = len(self.gossip_items)
        total_events = len(self.gossip_events)
        total_propagations = sum(
            gossip.propagation_count for gossip in self.gossip_items.values()
        )

        # Calculate average accuracy
        accuracies = [
            gossip.accuracy for gossip in self.gossip_items.values()
        ]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        return {
            "total_gossip_items": total_gossip,
            "total_gossip_events": total_events,
            "total_propagations": total_propagations,
            "average_accuracy": avg_accuracy,
            "agents_with_gossip": len(self.agent_gossip_memory)
        }


# Global gossip protocol instance (shared across all agents in a simulation)
_gossip_protocol: Optional[GossipProtocol] = None


def get_gossip_protocol() -> GossipProtocol:
    """
    Get or create the global gossip protocol instance.
    """
    global _gossip_protocol

    if _gossip_protocol is None:
        _gossip_protocol = GossipProtocol()
        logger.info("Global GossipProtocol instance created")

    return _gossip_protocol
