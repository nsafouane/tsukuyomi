"""
Conversation Memory Module
=========================

Provides ConversationMemory and Utterance classes for tracking dialogue.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import uuid


VERDICT_KEYWORDS = ["guilty", "innocent", "vote", "verdict", "decision"]
EVIDENCE_KEYWORDS = ["evidence", "testimony", "witness", "proof", "fact"]
PROCEDURE_KEYWORDS = ["rule", "law", "procedure", "process", "requirement"]


@dataclass
class Utterance:
    """A single utterance in conversation."""
    tick: int = 0
    content: str = ""
    topic: str = ""
    position: str = ""
    speaker_id: str = ""
    
    def __post_init__(self):
        if not self.speaker_id:
            self.speaker_id = str(uuid.uuid4())[:8]
    
    def key_topics(self) -> List[str]:
        """Extract key topics from the utterance content."""
        topics = []
        content_lower = self.content.lower()
        
        if self.topic:
            topics.append(self.topic)
        
        if any(kw in content_lower for kw in VERDICT_KEYWORDS):
            topics.append("verdict")
        if any(kw in content_lower for kw in EVIDENCE_KEYWORDS):
            topics.append("evidence")
        if any(kw in content_lower for kw in PROCEDURE_KEYWORDS):
            topics.append("procedure")
        if self.position:
            topics.append("position")
        
        return list(set(topics))
    
    def to_dict(self) -> Dict:
        return {
            "tick": self.tick,
            "content": self.content,
            "topic": self.topic,
            "position": self.position,
            "speaker_id": self.speaker_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Utterance":
        return cls(
            tick=data.get("tick", 0),
            content=data.get("content", ""),
            topic=data.get("topic", ""),
            position=data.get("position", ""),
            speaker_id=data.get("speaker_id", "")
        )


@dataclass
class ConversationMemory:
    """
    Manages conversation history and narrative tracking.
    """
    max_utterances: int = 100
    utterances: List[Utterance] = field(default_factory=list)
    discussed_topics: List[str] = field(default_factory=list)
    
    def add(self, utterance: Utterance) -> None:
        """Add an utterance to memory."""
        self.utterances.append(utterance)
        
        topics = utterance.key_topics()
        for topic in topics:
            if topic not in self.discussed_topics:
                self.discussed_topics.append(topic)
        
        while len(self.utterances) > self.max_utterances:
            self.utterances.pop(0)
    
    def get_recent(self, n: int = 5) -> List[Utterance]:
        """Get the n most recent utterances."""
        return self.utterances[-n:] if self.utterances else []
    
    def get_by_topic(self, topic: str) -> List[Utterance]:
        """Get all utterances related to a topic."""
        return [u for u in self.utterances if topic in u.key_topics()]
    
    def get_by_speaker(self, speaker_id: str) -> List[Utterance]:
        """Get all utterances by a speaker."""
        return [u for u in self.utterances if u.speaker_id == speaker_id]
    
    def get_speaker_positions(self) -> Dict[str, str]:
        """Get the latest position of each speaker."""
        positions = {}
        for utterance in reversed(self.utterances):
            if utterance.position and utterance.speaker_id not in positions:
                positions[utterance.speaker_id] = utterance.position
        return positions
    
    def summarize(self) -> str:
        """Generate a summary of the conversation."""
        if not self.utterances:
            return "No conversation yet."
        
        lines = [
            f"Conversation has {len(self.utterances)} utterances.",
            f"Topics discussed: {', '.join(self.discussed_topics) if self.discussed_topics else 'none'}"
        ]
        
        positions = self.get_speaker_positions()
        if positions:
            lines.append("Current positions:")
            for speaker, pos in positions.items():
                lines.append(f"  {speaker}: {pos}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        return {
            "max_utterances": self.max_utterances,
            "utterances": [u.to_dict() for u in self.utterances],
            "discussed_topics": self.discussed_topics
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationMemory":
        memory = cls(max_utterances=data.get("max_utterances", 100))
        memory.utterances = [Utterance.from_dict(u) for u in data.get("utterances", [])]
        memory.discussed_topics = data.get("discussed_topics", [])
        return memory


__all__ = ["ConversationMemory", "Utterance"]
