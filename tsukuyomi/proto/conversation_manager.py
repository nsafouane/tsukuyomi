"""
Conversation Manager
===================

Manages variable turn-taking, interruptions, and natural conversation flow
in multi-agent dialogues.

Key Features:
- Probabilistic speaking decisions based on personality
- Interruption handling
- Silence management
- Conversation pacing
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("ConversationManager")


class TurnDecision(Enum):
    """Decision for turn-taking."""
    SPEAK = "speak"
    WAIT = "wait"
    INTERRUPT = "interrupt"
    PASS = "pass"


@dataclass
class TurnContext:
    """Context for turn decision."""
    tick: int
    agent_id: str
    last_speaker_id: Optional[str] = None
    time_since_last_speech: int = 0
    current_topic: str = ""
    tension_level: float = 0.5
    vote_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class TurnResult:
    """Result of turn decision."""
    decision: TurnDecision
    urgency: float  # 0-1
    reason: str
    interrupt_target: Optional[str] = None


class ConversationManager:
    """
    Manages conversation flow between multiple agents.
    
    Handles:
    - Who speaks when
    - Interruptions
    - Silence/pauses
    - Conversation pacing
    
    Usage:
        cm = ConversationManager(agents=[agent1, agent2, agent3])
        
        for tick in ticks:
            for agent in agents:
                result = cm.should_agent_speak(agent, TurnContext(...))
                if result.decision == TurnDecision.SPEAK:
                    # Agent speaks
    """
    
    def __init__(
        self,
        agents: List[Any] = None,
        enable_interruptions: bool = True,
        base_speak_probability: float = 0.3,
        min_turn_gap: int = 10
    ):
        """
        Initialize conversation manager.
        
        Args:
            agents: List of agent objects with personality traits
            enable_interruptions: Whether to allow interruptions
            base_speak_probability: Base probability of speaking
            min_turn_gap: Minimum ticks between same agent can speak
        """
        self.agents = agents or []
        self.enable_interruptions = enable_interruptions
        self.base_speak_probability = base_speak_probability
        self.min_turn_gap = min_turn_gap
        
        # Track speaking state
        self.last_speaker_id: Optional[str] = None
        self.last_speak_tick: Dict[str, int] = defaultdict(int)
        self.interruption_cooldown: Dict[str, int] = defaultdict(int)
        self.currently_speaking: Set[str] = set()
        self.silence_count: int = 0
        
        # Statistics
        self.turn_statistics: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "speaks": 0,
            "waits": 0,
            "interrupts": 0,
            "passed": 0
        })
        
        logger.info(f"ConversationManager initialized with {len(self.agents)} agents")
    
    def add_agent(self, agent: Any) -> None:
        """Add an agent to the conversation."""
        self.agents.append(agent)
        logger.debug(f"Added agent {agent.agent_id} to conversation")
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the conversation."""
        self.agents = [a for a in self.agents if a.agent_id != agent_id]
        logger.debug(f"Removed agent {agent_id} from conversation")
    
    def should_agent_speak(
        self,
        agent: Any,
        context: TurnContext
    ) -> TurnResult:
        """
        Determine if an agent should speak given the context.
        
        Args:
            agent: The agent to check
            context: Current conversation context
        
        Returns:
            TurnResult with decision and reasoning
        """
        # Get agent personality/traits
        personality = self._get_agent_personality(agent)
        
        # Base probability
        speak_prob = self.base_speak_probability
        
        # === FACTOR 1: Time since last speech ===
        time_since_speech = context.tick - self.last_speak_tick.get(agent.agent_id, 0)
        
        if time_since_speech < self.min_turn_gap:
            # Recently spoke, reduce probability significantly
            speak_prob *= 0.2
        elif time_since_speech > 100:
            # Hasn't spoken in a while, increase probability
            speak_prob += 0.2
        
        # === FACTOR 2: Patience trait ===
        # High patience = less likely to jump in
        patience = personality.get("patience", 0.5)
        speak_prob -= patience * 0.15
        
        # === FACTOR 3: Extraversion trait ===
        # High extraversion = more likely to speak
        extraversion = personality.get("extraversion", 0.0)
        speak_prob += extraversion * 0.2
        
        # === FACTOR 4: Arousal/emotional state ===
        arousal = personality.get("arousal", 0.5)
        if arousal > 0.7:
            speak_prob += 0.15  # High energy = more likely to speak
        elif arousal < 0.3:
            speak_prob -= 0.1  # Low energy = less likely
        
        # === FACTOR 5: Minority pressure ===
        # If in minority, more likely to speak up
        if context.vote_distribution:
            my_vote = personality.get("current_vote", "guilty")
            total = sum(context.vote_distribution.values())
            if total > 0:
                my_count = context.vote_distribution.get(my_vote, 0)
                minority_ratio = my_count / total
                
                if minority_ratio < 0.4:
                    # Strong minority - increase urge to speak
                    speak_prob += 0.25
                elif minority_ratio < 0.5:
                    # Weak minority
                    speak_prob += 0.1
        
        # === FACTOR 6: Tension level ===
        # High tension = more interruptions possible
        if context.tension_level > 0.7 and self.enable_interruptions:
            speak_prob += 0.1
        
        # === FACTOR 7: Last speaker ===
        if context.last_speaker_id:
            if context.last_speaker_id == agent.agent_id:
                # Just spoke, much less likely
                speak_prob *= 0.3
            
            # Check if should interrupt last speaker
            if (self.enable_interruptions and 
                context.tension_level > 0.6 and
                arousal > 0.5 and
                random.random() < 0.1):  # 10% chance to interrupt
                
                return TurnResult(
                    decision=TurnDecision.INTERRUPT,
                    urgency=arousal,
                    reason="High tension and arousal triggered interruption attempt",
                    interrupt_target=context.last_speaker_id
                )
        
        # Clamp probability
        speak_prob = max(0.05, min(0.9, speak_prob))
        
        # Make decision
        if random.random() < speak_prob:
            self.last_speaker_id = agent.agent_id
            self.last_speak_tick[agent.agent_id] = context.tick
            self.turn_statistics[agent.agent_id]["speaks"] += 1
            
            return TurnResult(
                decision=TurnDecision.SPEAK,
                urgency=speak_prob,
                reason=self._build_reason(personality, context)
            )
        else:
            self.turn_statistics[agent.agent_id]["waits"] += 1
            
            return TurnResult(
                decision=TurnDecision.WAIT,
                urgency=speak_prob,
                reason="Not enough urgency to speak"
            )
    
    def _get_agent_personality(self, agent: Any) -> Dict[str, float]:
        """Extract personality traits from agent."""
        traits = {}
        
        # Try to get from agent object
        if hasattr(agent, 'profile'):
            personality = agent.profile.get('personality', {})
            traits.update(personality.get('traits', {}))
            traits.update(personality.get('big_five', {}))
            
            # Also get emotional state
            if hasattr(agent, 'emotional_state'):
                es = agent.emotional_state
                traits['arousal'] = es.get('arousal', 0.5)
                traits['valence'] = es.get('valence', 0.0)
        
        # Add current vote if available
        if hasattr(agent, 'current_vote'):
            traits['current_vote'] = agent.current_vote
        
        # Add stubbornness
        if hasattr(agent, 'get_stubbornness'):
            traits['stubbornness'] = agent.get_stubbornness()
        
        return traits
    
    def _build_reason(self, personality: Dict[str, float], context: TurnContext) -> str:
        """Build human-readable reason for speaking decision."""
        reasons = []
        
        if personality.get('extraversion', 0) > 0.3:
            reasons.append("extraverted")
        
        if personality.get('arousal', 0.5) > 0.6:
            reasons.append("highly aroused")
        
        time_since = context.tick - self.last_speak_tick.get(context.agent_id, 0)
        if time_since > 50:
            reasons.append("hasn't spoken recently")
        
        if context.vote_distribution:
            my_vote = personality.get('current_vote', 'guilty')
            total = sum(context.vote_distribution.values())
            if total > 0:
                my_count = context.vote_distribution.get(my_vote, 0)
                if my_count / total < 0.5:
                    reasons.append("in minority")
        
        return ", ".join(reasons) if reasons else "random chance"
    
    def get_next_speaker(
        self,
        context: TurnContext,
        exclude_recent: bool = True
    ) -> Optional[str]:
        """
        Get the next likely speaker without forcing decision.
        
        Useful for narrative/gap detection.
        """
        candidates = []
        
        for agent in self.agents:
            if agent.agent_id == context.agent_id:
                continue
            
            if exclude_recent:
                time_since = context.tick - self.last_speak_tick.get(agent.agent_id, 0)
                if time_since < self.min_turn_gap:
                    continue
            
            # Score this agent
            personality = self._get_agent_personality(agent)
            score = 0.5
            
            # Prefer less talkative agents
            score += (1 - self.turn_statistics[agent.agent_id]["speaks"] / max(1, sum(self.turn_statistics[agent.agent_id].values())))
            
            # Bonus for extraversion
            score += personality.get('extraversion', 0) * 0.3
            
            candidates.append((agent.agent_id, score))
        
        if not candidates:
            return None
        
        # Return highest score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def record_speech_start(self, agent_id: str, tick: int) -> None:
        """Record that an agent started speaking."""
        self.currently_speaking.add(agent_id)
        self.last_speaker_id = agent_id
        self.last_speak_tick[agent_id] = tick
        self.silence_count = 0
        
        logger.debug(f"{agent_id} started speaking at tick {tick}")
    
    def record_speech_end(self, agent_id: str, tick: int) -> None:
        """Record that an agent finished speaking."""
        self.currently_speaking.discard(agent_id)
        logger.debug(f"{agent_id} finished speaking at tick {tick}")
    
    def get_silence_count(self) -> int:
        """Get number of consecutive ticks with no speech."""
        return self.silence_count
    
    def increment_silence(self) -> None:
        """Increment silence counter (call when no one speaks)."""
        self.silence_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        total_turns = sum(
            sum(stats.values()) 
            for stats in self.turn_statistics.values()
        )
        
        return {
            "total_turns": total_turns,
            "by_agent": dict(self.turn_statistics),
            "silence_count": self.silence_count,
            "last_speaker": self.last_speaker_id,
            "currently_speaking": list(self.currently_speaking)
        }
    
    def reset(self) -> None:
        """Reset conversation state."""
        self.last_speaker_id = None
        self.last_speak_tick.clear()
        self.interruption_cooldown.clear()
        self.currently_speaking.clear()
        self.silence_count = 0
        logger.info("ConversationManager reset")


# ========================
# HELPER FUNCTIONS
# ========================

def create_conversation_manager(
    agents: List[Any],
    enable_interruptions: bool = True
) -> ConversationManager:
    """
    Factory function to create a conversation manager.
    
    Args:
        agents: List of agent objects
        enable_interruptions: Whether to allow interruptions
    
    Returns:
        Configured ConversationManager
    """
    return ConversationManager(
        agents=agents,
        enable_interruptions=enable_interruptions
    )


# ========================
# UNIT TESTS
# ========================

class MockAgent:
    """Mock agent for testing."""
    def __init__(self, agent_id: str, traits: Dict[str, float]):
        self.agent_id = agent_id
        self.profile = {
            "personality": {
                "traits": traits,
                "big_five": {}
            }
        }
        self.emotional_state = {"arousal": 0.5, "valence": 0.0}
        self.current_vote = "guilty"


def test_conversation_manager():
    """Test conversation manager functionality."""
    
    # Create mock agents
    agent1 = MockAgent("agent_1", {"patience": 0.3, "extraversion": 0.7})
    agent2 = MockAgent("agent_2", {"patience": 0.8, "extraversion": 0.2})
    agent3 = MockAgent("agent_3", {"patience": 0.5, "extraversion": 0.5})
    
    cm = ConversationManager(
        agents=[agent1, agent2, agent3],
        enable_interruptions=True,
        base_speak_probability=0.3
    )
    
    # Test 1: More extraverted agent more likely to speak
    speak_counts = {"agent_1": 0, "agent_2": 0, "agent_3": 0}
    
    for tick in range(100):
        for agent in [agent1, agent2, agent3]:
            context = TurnContext(
                tick=tick,
                agent_id=agent.agent_id,
                last_speaker_id=None,
                time_since_last_speech=50,
                vote_distribution={"guilty": 2, "not_guilty": 1}
            )
            result = cm.should_agent_speak(agent, context)
            if result.decision == TurnDecision.SPEAK:
                speak_counts[agent.agent_id] += 1
    
    # Extraverted agent (1) should speak more than introverted (2)
    assert speak_counts["agent_1"] >= speak_counts["agent_2"], \
        f"Extraverted agent should speak more: {speak_counts}"
    print(f"✅ Test 1: Extraversion affects speaking frequency")
    print(f"   Speak counts: {speak_counts}")
    
    # Test 2: Recent speakers are less likely to speak again
    agent1.last_speak_tick = {agent1.agent_id: 50}
    context = TurnContext(
        tick=55,
        agent_id=agent1.agent_id,
        last_speaker_id=agent1.agent_id,
        time_since_last_speech=5
    )
    result = cm.should_agent_speak(agent1, context)
    assert result.decision == TurnDecision.WAIT, "Should wait after just speaking"
    print("✅ Test 2: Recent speakers wait")
    
    # Test 3: Minority pressure increases speak probability
    context = TurnContext(
        tick=100,
        agent_id=agent1.agent_id,
        last_speaker_id=agent3.agent_id,
        time_since_last_speech=50,
        vote_distribution={"guilty": 4, "not_guilty": 1}  # agent1 is not_guilty
    )
    agent1.current_vote = "not_guilty"
    result = cm.should_agent_speak(agent1, context)
    print(f"✅ Test 3: Minority pressure check (decision: {result.decision})")
    
    # Test 4: Statistics tracking
    stats = cm.get_statistics()
    assert "total_turns" in stats
    assert stats["total_turns"] > 0
    print("✅ Test 4: Statistics tracking works")
    
    print("\n✅ All conversation manager tests passed!")


if __name__ == "__main__":
    test_conversation_manager()
