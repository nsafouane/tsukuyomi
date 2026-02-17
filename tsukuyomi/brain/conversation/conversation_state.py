"""
Conversation State Module - Tsukuyomi V2

This module implements data structures for tracking conversation state,
including turn history, topic tracking, and sentiment flow.

Key Components:
- ConversationState: Tracks ongoing conversation state
- ConversationTurn: A single turn in a conversation
- SentimentSnapshot: Captures sentiment at a point in time
- Interruption: Records interruption events
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import uuid
import time


class IntentType(Enum):
    """Types of speech intent."""
    INFORM = "inform"
    PERSUADE = "persuade"
    CHALLENGE = "challenge"
    AGREE = "agree"
    DISAGREE = "disagree"
    QUESTION = "question"
    COMMAND = "command"
    APOLOGIZE = "apologize"
    DEFEND = "defend"


@dataclass
class SentimentSnapshot:
    """
    Capture sentiment at a point in conversation.
    
    Sentiment is analyzed using rule-based patterns to determine
    the emotional tone and impact of speech on relationships.
    
    Attributes:
        tick: Simulation tick when sentiment was captured
        speaker: ID of the agent who spoke
        sentiment_score: -1.0 (hostile) to 1.0 (friendly)
        emotion_labels: List of detected emotion labels
        confidence: Confidence in the sentiment analysis (0.0 to 1.0)
    """
    tick: int
    speaker: str
    sentiment_score: float = 0.0  # -1.0 (hostile) to 1.0 (friendly)
    emotion_labels: List[str] = field(default_factory=list)  # ["anger", "frustration", "neutral", ...]
    confidence: float = 0.0  # How confident in the analysis
    
    def is_hostile(self) -> bool:
        """Check if sentiment is hostile."""
        return self.sentiment_score < -0.3
    
    def is_friendly(self) -> bool:
        """Check if sentiment is friendly."""
        return self.sentiment_score > 0.3
    
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return -0.3 <= self.sentiment_score <= 0.3
    
    def get_summary(self) -> str:
        """Get a human-readable summary."""
        if self.is_hostile():
            return f"hostile ({', '.join(self.emotion_labels)})"
        elif self.is_friendly():
            return f"friendly ({', '.join(self.emotion_labels)})"
        else:
            return f"neutral ({', '.join(self.emotion_labels) if self.emotion_labels else 'calm'})"


@dataclass
class Interruption:
    """
    Record of an interruption event.
    
    Tracks when one agent interrupts another during conversation,
    which can affect social dynamics and heat level.
    
    Attributes:
        tick: When the interruption occurred
        interrupter_id: ID of the agent who interrupted
        interrupted_id: ID of the agent who was interrupted
        partial_speech: What was said before interruption
        context: Additional context about the interruption
    """
    tick: int
    interrupter_id: str
    interrupted_id: str
    partial_speech: str
    context: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "tick": self.tick,
            "interrupter_id": self.interrupter_id,
            "interrupted_id": self.interrupted_id,
            "partial_speech": self.partial_speech,
            "context": self.context
        }


@dataclass
class ConversationTurn:
    """
    A single turn in a conversation.
    
    Represents one agent speaking to another (or to all) with
    full context including sentiment analysis and impact.
    
    Attributes:
        turn_id: Unique identifier for this turn
        speaker: ID of the speaking agent
        listener: ID of primary listener (or "all" for group)
        speech: The actual speech content
        intent: Classified intent of the speech
        sentiment: Sentiment analysis snapshot
        emotional_impact: How this affected the listener(s)
        topic_shift: Whether this changed the conversation topic
        tick: When this turn occurred
        duration_ticks: Approximate duration in ticks
        was_interrupted: Whether this turn was interrupted
        interruption: Details if interrupted
    """
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    speaker: str = ""
    listener: str = "all"
    speech: str = ""
    intent: IntentType = IntentType.INFORM
    sentiment: SentimentSnapshot = field(default_factory=lambda: SentimentSnapshot(tick=0, speaker=""))
    emotional_impact: float = 0.0  # How it affected listener
    topic_shift: bool = False
    tick: int = 0
    duration_ticks: int = 5  # Approximate
    was_interrupted: bool = False
    interruption: Optional[Interruption] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "turn_id": self.turn_id,
            "speaker": self.speaker,
            "listener": self.listener,
            "speech": self.speech,
            "intent": self.intent.value,
            "sentiment": {
                "tick": self.sentiment.tick,
                "speaker": self.sentiment.speaker,
                "sentiment_score": self.sentiment.sentiment_score,
                "emotion_labels": self.sentiment.emotion_labels,
                "confidence": self.sentiment.confidence
            },
            "emotional_impact": self.emotional_impact,
            "topic_shift": self.topic_shift,
            "tick": self.tick,
            "duration_ticks": self.duration_ticks,
            "was_interrupted": self.was_interrupted
        }
    
    def get_formatted(self, speaker_name: str = None) -> str:
        """
        Get a formatted string representation of this turn.
        
        Args:
            speaker_name: Optional display name for the speaker
        
        Returns:
            Formatted string for display
        """
        name = speaker_name or self.speaker
        sentiment_marker = ""
        
        if self.sentiment.is_hostile():
            sentiment_marker = " [hostile]"
        elif self.sentiment.is_friendly():
            sentiment_marker = " [friendly]"
        
        return f'{name}{sentiment_marker}: "{self.speech}"'


@dataclass
class ConversationState:
    """
    Track ongoing conversation state.
    
    Maintains the full context of a conversation including
    participants, turn history, topic tracking, and social dynamics.
    
    Attributes:
        conversation_id: Unique identifier for this conversation
        participants: List of participant agent IDs
        turns: History of conversation turns
        current_topic: Current topic being discussed
        topic_history: List of previous topics
        turn_taking: Who spoke how much (agent_id -> count)
        interruptions: List of interruption events
        heat_level: Argument intensity (0.0 to 1.0)
        sentiment_flow: Sentiment over time
        started_tick: When conversation started
        last_activity_tick: Last activity timestamp
        is_active: Whether conversation is still active
    """
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    participants: List[str] = field(default_factory=list)
    turns: List[ConversationTurn] = field(default_factory=list)
    current_topic: str = ""
    topic_history: List[str] = field(default_factory=list)
    turn_taking: Dict[str, int] = field(default_factory=dict)
    interruptions: List[Interruption] = field(default_factory=list)
    heat_level: float = 0.0  # 0.0 to 1.0 (argument intensity)
    sentiment_flow: List[SentimentSnapshot] = field(default_factory=list)
    started_tick: int = 0
    last_activity_tick: int = 0
    is_active: bool = True
    
    def add_participant(self, agent_id: str) -> None:
        """Add a participant to the conversation."""
        if agent_id not in self.participants:
            self.participants.append(agent_id)
            self.turn_taking[agent_id] = 0
    
    def record_turn(self, turn: ConversationTurn) -> None:
        """
        Record a conversation turn and update state.
        
        Args:
            turn: The conversation turn to record
        """
        self.turns.append(turn)
        self.last_activity_tick = turn.tick
        
        # Update turn taking
        if turn.speaker in self.turn_taking:
            self.turn_taking[turn.speaker] += 1
        else:
            self.turn_taking[turn.speaker] = 1
        
        # Update sentiment flow
        self.sentiment_flow.append(turn.sentiment)
        
        # Handle interruptions
        if turn.was_interrupted and turn.interruption:
            self.interruptions.append(turn.interruption)
    
    def get_recent_turns(self, limit: int = 10) -> List[ConversationTurn]:
        """
        Get the most recent turns.
        
        Args:
            limit: Maximum number of turns to return
        
        Returns:
            List of recent conversation turns
        """
        return self.turns[-limit:] if self.turns else []
    
    def get_dominant_speaker(self) -> Optional[str]:
        """
        Get the agent who has spoken the most.
        
        Returns:
            Agent ID of dominant speaker, or None if no turns yet
        """
        if not self.turn_taking:
            return None
        
        return max(self.turn_taking.items(), key=lambda x: x[1])[0]
    
    def get_speaker_balance(self) -> float:
        """
        Get a measure of how evenly distributed speech is.
        
        Returns:
            Balance score (1.0 = perfectly even, 0.0 = one person dominates)
        """
        if len(self.participants) < 2:
            return 1.0
        
        total_turns = sum(self.turn_taking.values())
        if total_turns == 0:
            return 1.0
        
        # Calculate entropy-based balance
        import math
        balance = 0.0
        for agent_id in self.participants:
            if agent_id in self.turn_taking:
                p = self.turn_taking[agent_id] / total_turns
                if p > 0:
                    balance -= p * math.log2(p)
        
        # Normalize to 0-1
        max_entropy = math.log2(len(self.participants))
        return balance / max_entropy if max_entropy > 0 else 1.0
    
    def get_average_sentiment(self, recent: int = 0) -> float:
        """
        Get average sentiment over the conversation.
        
        Args:
            recent: If > 0, only consider last N turns
        
        Returns:
            Average sentiment score
        """
        sentiments = self.sentiment_flow[-recent:] if recent > 0 else self.sentiment_flow
        if not sentiments:
            return 0.0
        
        return sum(s.sentiment_score for s in sentiments) / len(sentiments)
    
    def get_sentiment_trend(self) -> str:
        """
        Analyze the trend of sentiment over time.
        
        Returns:
            Trend description: "improving", "degrading", "stable", "volatile"
        """
        if len(self.sentiment_flow) < 3:
            return "stable"
        
        recent = self.sentiment_flow[-5:]
        if len(recent) < 3:
            return "stable"
        
        # Calculate trend
        scores = [s.sentiment_score for s in recent]
        
        # Simple linear trend
        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2) if len(scores)//2 > 0 else 0
        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2) if (len(scores) - len(scores)//2) > 0 else 0
        
        diff = second_half - first_half
        variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
        
        if variance > 0.3:
            return "volatile"
        elif diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "degrading"
        else:
            return "stable"
    
    def update_topic(self, new_topic: str) -> None:
        """
        Update the current topic.
        
        Args:
            new_topic: The new topic
        """
        if self.current_topic and self.current_topic != new_topic:
            self.topic_history.append(self.current_topic)
        self.current_topic = new_topic
    
    def get_heat_description(self) -> str:
        """Get a human-readable description of heat level."""
        if self.heat_level < 0.2:
            return "calm"
        elif self.heat_level < 0.4:
            return "tense"
        elif self.heat_level < 0.6:
            return "heated"
        elif self.heat_level < 0.8:
            return "intense"
        else:
            return "volatile"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "conversation_id": self.conversation_id,
            "participants": self.participants,
            "turn_count": len(self.turns),
            "current_topic": self.current_topic,
            "heat_level": self.heat_level,
            "heat_description": self.get_heat_description(),
            "turn_taking": self.turn_taking,
            "interruption_count": len(self.interruptions),
            "average_sentiment": self.get_average_sentiment(),
            "sentiment_trend": self.get_sentiment_trend(),
            "is_active": self.is_active,
            "started_tick": self.started_tick,
            "last_activity_tick": self.last_activity_tick
        }
    
    def get_summary(self) -> str:
        """
        Get a brief summary of the conversation.
        
        Returns:
            Human-readable summary string
        """
        parts = [
            f"Conversation ({self.conversation_id[:8]}...)",
            f"Participants: {', '.join(self.participants)}",
            f"Turns: {len(self.turns)}",
            f"Topic: {self.current_topic or 'undefined'}",
            f"Heat: {self.get_heat_description()} ({self.heat_level:.0%})",
            f"Sentiment: {self.get_sentiment_trend()} (avg: {self.get_average_sentiment():.2f})"
        ]
        
        if self.interruptions:
            parts.append(f"Interruptions: {len(self.interruptions)}")
        
        return "\n".join(parts)


# Convenience functions

def create_conversation(participants: List[str], tick: int, topic: str = "") -> ConversationState:
    """
    Create a new conversation with the given participants.
    
    Args:
        participants: List of participant agent IDs
        tick: Starting tick
        topic: Initial topic (optional)
    
    Returns:
        Initialized ConversationState
    """
    state = ConversationState(
        participants=participants,
        started_tick=tick,
        last_activity_tick=tick,
        current_topic=topic
    )
    
    for participant in participants:
        state.turn_taking[participant] = 0
    
    return state