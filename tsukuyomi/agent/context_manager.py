"""
Context Manager
==============

Manages cross-turn conversation memory and context tracking.

Key Features:
- Turn-by-turn context tracking
- Speaker identification and attribution
- Key point extraction
- Context summarization
- Topic tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Tuple
from collections import defaultdict
import json
import random


class ContextType(Enum):
    """Types of context elements."""
    STATEMENT = "statement"       # Something said
    QUESTION = "question"         # A question asked
    ARGUMENT = "argument"         # A persuasive argument
    EVIDENCE = "evidence"         # Evidence presented
    AGREEMENT = "agreement"       # Agreement expressed
    DISAGREEMENT = "disagreement" # Disagreement expressed
    OBJECTION = "objection"       # Objection raised
    VOTE = "vote"                 # A vote or position
    EMOTION = "emotion"           # Emotional expression


@dataclass
class Utterance:
    """
    A single utterance in the conversation.
    """
    id: str = field(default_factory=lambda: f"utt_{random.randint(100000, 999999)}")
    speaker_id: str = ""
    content: str = ""
    context_type: ContextType = ContextType.STATEMENT
    
    # Metadata
    tick: int = 0
    turn: int = 0
    round: int = 0  # Deliberation round
    
    # Analysis
    topics: List[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1 to 1
    keywords: List[str] = field(default_factory=list)
    
    # References
    references: List[str] = field(default_factory=list)  # IDs of referenced utterances
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "speaker_id": self.speaker_id,
            "content": self.content,
            "context_type": self.context_type.value,
            "tick": self.tick,
            "turn": self.turn,
            "round": self.round,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "keywords": self.keywords,
            "references": self.references
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Utterance":
        return cls(
            id=data["id"],
            speaker_id=data["speaker_id"],
            content=data["content"],
            context_type=ContextType(data["context_type"]),
            tick=data["tick"],
            turn=data["turn"],
            round=data.get("round", 0),
            topics=data.get("topics", []),
            sentiment=data.get("sentiment", 0.0),
            keywords=data.get("keywords", []),
            references=data.get("references", [])
        )


@dataclass
class KeyPoint:
    """
    A key point extracted from conversation.
    """
    id: str = field(default_factory=lambda: f"kp_{random.randint(100000, 999999)}")
    content: str = ""
    speakers: List[str] = field(default_factory=list)  # Who mentioned this
    utterance_ids: List[str] = field(default_factory=list)
    importance: float = 0.5
    topic: str = ""
    tick: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "speakers": self.speakers,
            "utterance_ids": self.utterance_ids,
            "importance": self.importance,
            "topic": self.topic,
            "tick": self.tick
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KeyPoint":
        return cls(**data)


@dataclass
class Turn:
    """
    A single turn in the conversation.
    """
    turn_number: int = 0
    round_number: int = 0
    utterances: List[str] = field(default_factory=list)  # Utterance IDs
    tick: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "turn_number": self.turn_number,
            "round_number": self.round_number,
            "utterances": self.utterances,
            "tick": self.tick
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Turn":
        return cls(**data)


class ContextManager:
    """
    Manages conversation context across turns.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Storage
        self.utterances: Dict[str, Utterance] = {}
        self.key_points: Dict[str, KeyPoint] = {}
        self.turns: Dict[int, Turn] = {}
        
        # Indexes
        self.speaker_history: Dict[str, List[str]] = defaultdict(list)  # speaker -> utterance IDs
        self.topic_utterances: Dict[str, List[str]] = defaultdict(list)  # topic -> utterance IDs
        
        # Counters
        self.current_turn = 0
        self.current_round = 0
        self.total_utterances = 0
        
        # Configuration
        self.max_utterances = 1000
        self.max_key_points = 50
        self.summary_trigger = 100  # utterances before summarization
    
    # ==================== ADDING CONTENT ====================
    
    def add_utterance(
        self,
        speaker_id: str,
        content: str,
        context_type: ContextType = ContextType.STATEMENT,
        tick: int = 0,
        topics: Optional[List[str]] = None,
        sentiment: float = 0.0,
        keywords: Optional[List[str]] = None,
        references: Optional[List[str]] = None
    ) -> Utterance:
        """
        Add an utterance to the conversation.
        """
        # Check max
        if len(self.utterances) >= self.max_utterances:
            self._prune_old_utterances()
        
        utterance = Utterance(
            speaker_id=speaker_id,
            content=content,
            context_type=context_type,
            tick=tick,
            turn=self.current_turn,
            round=self.current_round,
            topics=topics or [],
            sentiment=sentiment,
            keywords=keywords or [],
            references=references or []
        )
        
        self.utterances[utterance.id] = utterance
        
        # Update indexes
        self.speaker_history[speaker_id].append(utterance.id)
        for topic in utterance.topics:
            self.topic_utterances[topic].append(utterance.id)
        
        self.total_utterances += 1
        
        return utterance
    
    def next_turn(self):
        """Advance to next turn."""
        self.current_turn += 1
    
    def next_round(self):
        """Advance to next round."""
        self.current_round += 1
        self.current_turn = 0
    
    # ==================== KEY POINTS ====================
    
    def add_key_point(
        self,
        content: str,
        speaker_id: str,
        utterance_id: str,
        importance: float = 0.5,
        topic: str = "",
        tick: int = 0
    ) -> KeyPoint:
        """
        Add a key point from conversation.
        """
        # Check if point already exists
        existing = self._find_existing_key_point(content)
        if existing:
            # Update existing
            if speaker_id not in existing.speakers:
                existing.speakers.append(speaker_id)
            existing.utterance_ids.append(utterance_id)
            existing.importance = max(existing.importance, importance)
            return existing
        
        # Check max
        if len(self.key_points) >= self.max_key_points:
            self._prune_key_points()
        
        point = KeyPoint(
            content=content,
            speakers=[speaker_id],
            utterance_ids=[utterance_id],
            importance=importance,
            topic=topic,
            tick=tick
        )
        
        self.key_points[point.id] = point
        return point
    
    def _find_existing_key_point(self, content: str) -> Optional[KeyPoint]:
        """Find existing key point with similar content."""
        content_lower = content.lower()
        for point in self.key_points.values():
            if content_lower in point.content.lower() or point.content.lower() in content_lower:
                return point
        return None
    
    # ==================== RETRIEVAL ====================
    
    def get_recent_utterances(
        self,
        n: int = 10,
        speaker_id: Optional[str] = None
    ) -> List[Utterance]:
        """Get most recent utterances."""
        all_ids = sorted(
            self.utterances.keys(),
            key=lambda i: self.utterances[i].tick,
            reverse=True
        )
        
        if speaker_id:
            all_ids = [i for i in all_ids if self.utterances[i].speaker_id == speaker_id]
        
        return [self.utterances[i] for i in all_ids[:n]]
    
    def get_speaker_utterances(
        self,
        speaker_id: str,
        limit: int = 50
    ) -> List[Utterance]:
        """Get all utterances by a speaker."""
        ids = self.speaker_history.get(speaker_id, [])
        return [self.utterances[i] for i in ids[-limit:]]
    
    def get_topic_utterances(
        self,
        topic: str,
        limit: int = 20
    ) -> List[Utterance]:
        """Get utterances about a topic."""
        ids = self.topic_utterances.get(topic, [])
        return [self.utterances[i] for i in ids[-limit:]]
    
    def get_key_points(self, topic: Optional[str] = None) -> List[KeyPoint]:
        """Get key points, optionally filtered by topic."""
        points = list(self.key_points.values())
        
        if topic:
            points = [p for p in points if p.topic == topic]
        
        return sorted(points, key=lambda p: p.importance, reverse=True)
    
    def search_utterances(
        self,
        query: str,
        speaker_id: Optional[str] = None
    ) -> List[Utterance]:
        """Search utterances by content."""
        query_lower = query.lower()
        results = []
        
        for utt in self.utterances.values():
            if query_lower in utt.content.lower():
                if speaker_id is None or utt.speaker_id == speaker_id:
                    results.append(utt)
        
        return sorted(results, key=lambda u: u.tick, reverse=True)
    
    def get_utterances_since(
        self,
        tick: int,
        speaker_id: Optional[str] = None
    ) -> List[Utterance]:
        """Get all utterances since a tick."""
        results = [
            u for u in self.utterances.values()
            if u.tick > tick and (speaker_id is None or u.speaker_id == speaker_id)
        ]
        return sorted(results, key=lambda u: u.tick)
    
    # ==================== ATTRIBUTION ====================
    
    def get_speaker_statements(
        self,
        target_speaker_id: str,
        speaker_id: Optional[str] = None
    ) -> List[Utterance]:
        """Get statements made about a speaker."""
        target = target_speaker_id.lower()
        results = []
        
        for utt in self.utterances.values():
            if target in utt.content.lower():
                if speaker_id is None or utt.speaker_id == speaker_id:
                    results.append(utt)
        
        return sorted(results, key=lambda u: u.tick, reverse=True)
    
    def who_agreed_with(self, utterance_id: str) -> List[str]:
        """Find who agreed with an utterance."""
        original = self.utterances.get(utterance_id)
        if not original:
            return []
        
        # Find utterances that reference this one
        agree_ids = [
            u.speaker_id for u in self.utterances.values()
            if utterance_id in u.references and "agree" in u.content.lower()
        ]
        
        return list(set(agree_ids))
    
    def who_disagreed_with(self, utterance_id: str) -> List[str]:
        """Find who disagreed with an utterance."""
        original = self.utterances.get(utterance_id)
        if not original:
            return []
        
        disagree_ids = [
            u.speaker_id for u in self.utterances.values()
            if utterance_id in u.references and "disagree" in u.content.lower()
        ]
        
        return list(set(disagree_ids))
    
    # ==================== SUMMARY ====================
    
    def get_conversation_summary(
        self,
        speakers: Optional[List[str]] = None
    ) -> str:
        """Get a summary of the conversation."""
        lines = [
            "CONVERSATION SUMMARY",
            "=" * 40,
            f"Total utterances: {self.total_utterances}",
            f"Current turn: {self.current_turn}",
            f"Key points: {len(self.key_points)}",
            ""
        ]
        
        if speakers:
            lines.append("SPEAKER ACTIVITY:")
            for speaker in speakers:
                count = len(self.speaker_history.get(speaker, []))
                lines.append(f"  {speaker}: {count} utterances")
            lines.append("")
        
        # Key points
        if self.key_points:
            lines.append("KEY POINTS:")
            for kp in sorted(self.key_points.values(), key=lambda k: k.importance, reverse=True)[:5]:
                speakers_str = ", ".join(kp.speakers[:3])
                lines.append(f"  • {kp.content[:80]}...")
                lines.append(f"    Mentioned by: {speakers_str}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_turn_summary(self, turn_number: int) -> str:
        """Get summary of a specific turn."""
        turn_utts = [
            u for u in self.utterances.values()
            if u.turn == turn_number
        ]
        
        if not turn_utts:
            return f"Turn {turn_number}: No utterances"
        
        lines = [f"Turn {turn_number} ({len(turn_utts)} utterances):"]
        
        for utt in sorted(turn_utts, key=lambda u: u.tick):
            content_preview = utt.content[:60] + "..." if len(utt.content) > 60 else utt.content
            lines.append(f"  {utt.speaker_id}: {content_preview}")
        
        return "\n".join(lines)
    
    def get_participant_summary(self, speaker_id: str) -> str:
        """Get summary of what a participant said."""
        utts = self.get_speaker_utterances(speaker_id)
        
        if not utts:
            return f"No utterances from {speaker_id}"
        
        # Get key points they raised
        speaker_points = [kp for kp in self.key_points.values() if speaker_id in kp.speakers]
        
        lines = [
            f"PARTICIPANT: {speaker_id}",
            "=" * 40,
            f"Total utterances: {len(utts)}",
            f"Key points raised: {len(speaker_points)}",
            ""
        ]
        
        if utts:
            # First and last
            lines.append(f"First utterance (tick {utts[0].tick}): {utts[0].content[:60]}...")
            lines.append(f"Last utterance (tick {utts[-1].tick}): {utts[-1].content[:60]}...")
            lines.append("")
        
        if speaker_points:
            lines.append("Key points made:")
            for kp in sorted(speaker_points, key=lambda k: k.importance, reverse=True)[:3]:
                lines.append(f"  • {kp.content[:70]}...")
        
        return "\n".join(lines)
    
    # ==================== INTERNAL ====================
    
    def _prune_old_utterances(self):
        """Remove oldest utterances when limit reached."""
        # Keep key points' utterances
        kept_ids = set()
        for kp in self.key_points.values():
            kept_ids.update(kp.utterance_ids)
        
        # Sort by tick
        sorted_ids = sorted(
            self.utterances.keys(),
            key=lambda i: self.utterances[i].tick
        )
        
        # Remove oldest until under limit
        remove_count = self.max_utterances // 4
        for utt_id in sorted_ids[:remove_count]:
            if utt_id not in kept_ids:
                del self.utterances[utt_id]
    
    def _prune_key_points(self):
        """Remove lowest importance key points."""
        sorted_points = sorted(
            self.key_points.values(),
            key=lambda p: p.importance
        )
        
        remove_count = self.max_key_points // 4
        for point in sorted_points[:remove_count]:
            del self.key_points[point.id]
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "utterances": {uid: u.to_dict() for uid, u in self.utterances.items()},
            "key_points": {kpid: kp.to_dict() for kpid, kp in self.key_points.items()},
            "turns": {k: t.to_dict() for k, t in self.turns.items()},
            "speaker_history": {k: v for k, v in self.speaker_history.items()},
            "topic_utterances": {k: v for k, v in self.topic_utterances.items()},
            "current_turn": self.current_turn,
            "current_round": self.current_round,
            "total_utterances": self.total_utterances
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ContextManager":
        manager = cls(agent_id=data["agent_id"])
        manager.utterances = {
            uid: Utterance.from_dict(u) for uid, u in data.get("utterances", {}).items()
        }
        manager.key_points = {
            kpid: KeyPoint.from_dict(kp) for kpid, kp in data.get("key_points", {}).items()
        }
        manager.turns = {
            k: Turn.from_dict(t) for k, t in data.get("turns", {}).items()
        }
        manager.speaker_history = defaultdict(list, data.get("speaker_history", {}))
        manager.topic_utterances = defaultdict(list, data.get("topic_utterances", {}))
        manager.current_turn = data.get("current_turn", 0)
        manager.current_round = data.get("current_round", 0)
        manager.total_utterances = data.get("total_utterances", 0)
        return manager


# ==================== HELPER FUNCTIONS ====================

def extract_keywords(content: str, max_keywords: int = 5) -> List[str]:
    """Simple keyword extraction (placeholder for NLP)."""
    # Simple approach: extract capitalized words and common terms
    words = content.split()
    keywords = []
    
    # Look for capitalized words (potential names, places)
    for word in words:
        if word[0].isupper() and len(word) > 2:
            keywords.append(word.strip(".,!?"))
            if len(keywords) >= max_keywords:
                break
    
    return keywords


def extract_topics(content: str) -> List[str]:
    """Extract topics from content (placeholder)."""
    topics = []
    
    content_lower = content.lower()
    
    # Simple keyword matching
    topic_keywords = {
        "evidence": ["evidence", "proof", "witness", "testimony"],
        "guilt": ["guilty", "innocent", "crime", "murder"],
        "procedure": ["vote", "deliberation", "jury", "court"],
        "character": ["character", "reputation", "honest"],
    }
    
    for topic, keywords in topic_keywords.items():
        if any(kw in content_lower for kw in keywords):
            topics.append(topic)
    
    return topics
