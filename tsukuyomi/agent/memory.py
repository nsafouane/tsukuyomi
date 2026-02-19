"""
Conversation Memory System
==========================

Tracks agent's personal narrative and conversation history for continuity.
This is a GENERAL system applicable to any social simulation.

Location: tsukuyomi/agent/memory.py
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger("ConversationMemory")


# Topic keywords for extraction
TOPIC_KEYWORDS = {
    "evidence": ["evidence", "proof", "witness", "testimony", "fact", "prove"],
    "alibi": ["alibi", "whereabouts", "location", "time", "when", "place"],
    "weapon": ["knife", "switchblade", "weapon", "weapon", "murder weapon"],
    "character": ["character", "background", "record", "personality", "reputation"],
    "procedure": ["verdict", "vote", "decision", "guilty", "innocent", "procedure"],
    "emotion": ["feel", "think", "believe", "doubt", "opinion", "feeling"],
    "truth": ["truth", "real", "really", "honest", "lie", "false"],
    "doubt": ["doubt", "uncertain", "unsure", "maybe", "possibly", "might"],
    "logic": ["reason", "because", "therefore", "thus", "hence", "logical"],
}


@dataclass
class Utterance:
    """
    A single utterance by an agent.
    
    Tracks what was said, when, and what topics were discussed.
    """
    tick: int
    content: str
    topic: Optional[str] = None
    position: Optional[str] = None  # "pro", "con", "neutral", "guilty", "not_guilty"
    referenced_agents: List[str] = field(default_factory=list)
    referenced_topics: List[str] = field(default_factory=list)
    tone: str = "neutral"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def key_topics(self) -> Set[str]:
        """Extract key topics from utterance."""
        topics = set()
        content_lower = self.content.lower()
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in content_lower for kw in keywords):
                topics.add(topic)
        
        return topics
    
    def to_dict(self) -> Dict:
        return {
            "tick": self.tick,
            "content": self.content,
            "topic": self.topic,
            "position": self.position,
            "referenced_agents": self.referenced_agents,
            "referenced_topics": self.referenced_topics,
            "tone": self.tone,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ConversationMemory:
    """
    Tracks an agent's conversation history for continuity.
    
    This is a GENERAL system that prevents:
    - Repetition of already-discussed topics
    - Contradicting one's own stated positions
    - Breaking personal narrative continuity
    
    Applicable to any simulation where agents have multi-turn conversations.
    """
    
    max_utterances: int = 50
    utterances: List[Utterance] = field(default_factory=list)
    
    # Topic tracking
    discussed_topics: Set[str] = field(default_factory=set)
    topic_positions: Dict[str, str] = field(default_factory=dict)  # topic -> position
    
    # Agent references
    referenced_agents: Set[str] = field(default_factory=set)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # agent_id -> {trust, interactions}
    
    # Narrative tracking
    first_position: Optional[str] = None
    position_changes: int = 0
    
    def add(self, utterance: Utterance):
        """
        Add an utterance to memory.
        
        Updates all tracking indices.
        """
        self.utterances.append(utterance)
        
        # Update topic tracking
        topics = utterance.key_topics()
        self.discussed_topics.update(topics)
        
        # Track positions if stated
        if utterance.position:
            for topic in topics:
                old_position = self.topic_positions.get(topic)
                if old_position and old_position != utterance.position:
                    self.position_changes += 1
                self.topic_positions[topic] = utterance.position
            
            # Track overall position (e.g., guilty/not_guilty)
            if utterance.position in ["guilty", "not_guilty"]:
                if self.first_position is None:
                    self.first_position = utterance.position
                elif self.first_position != utterance.position:
                    self.position_changes += 1
        
        # Track referenced agents
        self.referenced_agents.update(utterance.referenced_agents)
        
        # Trim old utterances
        while len(self.utterances) > self.max_utterances:
            self.utterances.pop(0)
            # Note: Topics and positions are cumulative, not removed
        
        logger.debug(
            f"Utterance added: tick={utterance.tick}, "
            f"topics={list(topics)}, position={utterance.position}"
        )
    
    def has_discussed(self, topic: str) -> bool:
        """Check if a topic has been discussed."""
        return topic in self.discussed_topics
    
    def get_position_on(self, topic: str) -> Optional[str]:
        """Get agent's stated position on a topic."""
        return self.topic_positions.get(topic)
    
    def get_recent_utterances(self, n: int = 5) -> List[Utterance]:
        """Get the n most recent utterances."""
        return self.utterances[-n:] if self.utterances else []
    
    def consistency_check(self, new_content: str) -> Dict[str, Any]:
        """
        Check if new statement is consistent with past positions.
        
        Returns dict with:
        - is_consistent: bool
        - conflicting_topics: List[str]
        - suggested_acknowledgment: str
        - previously_stated: List[str]
        """
        new_topics = Utterance(tick=0, content=new_content).key_topics()
        
        conflicts = []
        previously_stated = []
        
        for topic in new_topics:
            old_position = self.topic_positions.get(topic)
            if old_position:
                previously_stated.append(f"{topic}: {old_position}")
                # Check if new content contradicts old position
                content_lower = new_content.lower()
                
                if "not guilty" in content_lower or "innocent" in content_lower:
                    if old_position == "guilty":
                        conflicts.append(topic)
                elif "guilty" in content_lower:
                    if old_position in ["not_guilty", "not guilty", "innocent"]:
                        conflicts.append(topic)
        
        return {
            "is_consistent": len(conflicts) == 0,
            "conflicting_topics": conflicts,
            "suggested_acknowledgment": self._build_acknowledgment(conflicts) if conflicts else None,
            "previously_stated": previously_stated
        }
    
    def _build_acknowledgment(self, conflicts: List[str]) -> str:
        """Build phrase acknowledging position change."""
        if not conflicts:
            return ""
        
        if len(conflicts) == 1:
            return f"I've reconsidered my position on {conflicts[0]}."
        return f"I've reconsidered my positions on {', '.join(conflicts)}."
    
    def get_personal_narrative(self) -> str:
        """
        Generate a summary of the agent's conversation history.
        
        Useful for maintaining consistency in prompts.
        """
        if not self.utterances:
            return "You haven't spoken yet in this conversation."
        
        parts = ["## YOUR CONVERSATION HISTORY"]
        
        # Position summary
        if self.first_position:
            parts.append(f"- First stated position: {self.first_position}")
            if self.position_changes > 0:
                parts.append(f"- Position changes: {self.position_changes}")
        
        # Topics discussed
        if self.discussed_topics:
            topics_str = ", ".join(sorted(self.discussed_topics))
            parts.append(f"- Topics discussed: {topics_str}")
        
        # Recent statements
        recent = self.get_recent_utterances(3)
        if recent:
            parts.append("\n## RECENT STATEMENTS")
            for u in recent:
                preview = u.content[:80] + "..." if len(u.content) > 80 else u.content
                parts.append(f"- Tick {u.tick}: \"{preview}\"")
        
        return "\n".join(parts)
    
    def update_relationship(self, agent_id: str, trust_delta: float, interaction_type: str):
        """
        Update relationship with another agent.
        
        Args:
            agent_id: ID of the other agent
            trust_delta: Change in trust (-1 to 1)
            interaction_type: "agreed", "disagreed", "supported", "ignored"
        """
        if agent_id not in self.relationships:
            self.relationships[agent_id] = {"trust": 0.5, "interactions": 0}
        
        rel = self.relationships[agent_id]
        rel["trust"] = max(0, min(1, rel["trust"] + trust_delta))
        rel["interactions"] += 1
        rel["last_interaction"] = interaction_type
    
    def get_relationship(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship info with another agent."""
        return self.relationships.get(agent_id)
    
    def to_dict(self) -> Dict:
        """Serialize for persistence."""
        return {
            "max_utterances": self.max_utterances,
            "utterances": [u.to_dict() for u in self.utterances],
            "discussed_topics": list(self.discussed_topics),
            "topic_positions": dict(self.topic_positions),
            "referenced_agents": list(self.referenced_agents),
            "relationships": dict(self.relationships),
            "first_position": self.first_position,
            "position_changes": self.position_changes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMemory':
        """Deserialize from dict."""
        memory = cls(max_utterances=data.get("max_utterances", 50))
        
        for u_data in data.get("utterances", []):
            ut = Utterance(
                tick=u_data["tick"],
                content=u_data["content"],
                topic=u_data.get("topic"),
                position=u_data.get("position"),
                referenced_agents=u_data.get("referenced_agents", []),
                tone=u_data.get("tone", "neutral")
            )
            memory.utterances.append(ut)
        
        memory.discussed_topics = set(data.get("discussed_topics", []))
        memory.topic_positions = data.get("topic_positions", {})
        memory.referenced_agents = set(data.get("referenced_agents", []))
        memory.relationships = data.get("relationships", {})
        memory.first_position = data.get("first_position")
        memory.position_changes = data.get("position_changes", 0)
        
        return memory
