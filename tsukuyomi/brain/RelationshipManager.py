import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("RelationshipManager")

@dataclass
class SocialEvent:
    tick: int
    actor_id: str
    target_id: str
    event_type: str  # "interact", "gossip_share", "gossip_overhear", "conflict", "direct_address"
    impact: float    # -1.0 to 1.0
    description: str

@dataclass
class Relationship:
    affinity: float = 0.0  # -1.0 to 1.0
    events: List[SocialEvent] = field(default_factory=list)
    reputation_score: float = 0.0 # How this actor is viewed by the owner (aggregate)

class RelationshipManager:
    """
    Tracks and manages social relationships from the perspective of a single agent.
    """
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        # target_id -> Relationship
        self.relationships: Dict[str, Relationship] = {}

    def record_event(self, target_id: str, tick: int, event_type: str, impact: float, description: str):
        """Update affinity and record a social event."""
        if target_id not in self.relationships:
            self.relationships[target_id] = Relationship()
        
        rel = self.relationships[target_id]
        event = SocialEvent(
            tick=tick,
            actor_id=self.owner_id,
            target_id=target_id,
            event_type=event_type,
            impact=impact,
            description=description
        )
        
        # Update affinity with bounded logic
        rel.affinity = max(-1.0, min(1.0, rel.affinity + impact))
        rel.events.append(event)
        
        # Keep history manageable
        if len(rel.events) > 50:
            rel.events.pop(0)
            
        logger.info(f"Social Update [{self.owner_id} -> {target_id}]: affinity={rel.affinity:.2f} ({event_type})")

    def get_affinity(self, target_id: str) -> float:
        return self.relationships.get(target_id, Relationship()).affinity

    def get_relationship_status(self, target_id: str) -> str:
        if target_id not in self.relationships:
            return "neutral"
        
        affinity = self.relationships[target_id].affinity
        if affinity > 0.6: return "friendly"
        if affinity > 0.2: return "acquaintance"
        if affinity < -0.6: return "hostile"
        if affinity < -0.2: return "unfriendly"
        return "neutral"

    def to_llm_context(self) -> str:
        """Generates context for the LLM regarding all known relationships."""
        if not self.relationships:
            return "SOCIAL RELATIONSHIPS:\nYou have no established relationships with others yet."
        
        lines = ["SOCIAL RELATIONSHIPS:"]
        for target_id, rel in self.relationships.items():
            status = self.get_relationship_status(target_id)
            recent_desc = ""
            if rel.events:
                # Summarize recent events
                recent = rel.events[-3:]
                recent_desc = " Recent history: " + "; ".join([e.description for e in recent])
            
            lines.append(f"- {target_id}: {status} (Affinity: {rel.affinity:.2f}).{recent_desc}")
            
        return "\n".join(lines)
