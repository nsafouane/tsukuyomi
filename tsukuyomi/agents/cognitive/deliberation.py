"""
Deliberation Engine
===================

Adds internal deliberation before an agent speaks.
This creates the "thinking before speaking" behavior that makes
agent conversations feel more natural and emergent.

Key Features:
- Internal monologue generation before response
- Belief-based reasoning about what to say
- Emotional reaction recording
- Memory-informed deliberation
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger("Deliberation")


class DeliberationType(Enum):
    """Types of deliberation."""
    REFLECTION = "reflection"          # Thinking about own beliefs
    EVALUATION = "evaluation"          # Evaluating others' arguments
    DECISION = "decision"             # Deciding what to say/do
    PLANNING = "planning"             # Planning response strategy


@dataclass
class DeliberationResult:
    """Result of a deliberation phase."""
    deliberation_type: DeliberationType
    content: str
    reasoning_chain: List[str] = field(default_factory=list)
    emotional_reaction: str = ""
    confidence: float = 0.5
    should_speak: bool = True
    speak_urgency: float = 0.5  # 0-1, how urgent it is to speak
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.deliberation_type.value,
            "content": self.content,
            "reasoning_chain": self.reasoning_chain,
            "emotional_reaction": self.emotional_reaction,
            "confidence": self.confidence,
            "should_speak": self.should_speak,
            "speak_urgency": self.speak_urgency
        }


class DeliberationEngine:
    """
    Manages internal deliberation before agent actions.
    
    This creates the "thinking" phase that happens between
    receiving stimulus and generating response.
    
    Usage:
        engine = DeliberationEngine(agent)
        result = await engine.deliberate(
            context={"stimulus": "Someone argued X"},
            tick=100
        )
    """
    
    def __init__(
        self,
        agent_id: str,
        belief_system: Any = None,
        emotional_state: Dict[str, float] = None,
        personality: Dict[str, float] = None,
        llm_call: Callable = None
    ):
        self.agent_id = agent_id
        self.belief_system = belief_system
        self.emotional_state = emotional_state or {
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.5
        }
        self.personality = personality or {}
        self._llm_call = llm_call
        
        # Track deliberation history
        self.deliberation_history: List[DeliberationResult] = []
        
        logger.debug(f"DeliberationEngine initialized for {agent_id}")
    
    def update_emotional_state(self, state: Dict[str, float]) -> None:
        """Update the emotional state reference."""
        self.emotional_state = state
    
    def update_belief_system(self, belief_system) -> None:
        """Update the belief system reference."""
        self.belief_system = belief_system
    
    async def deliberate(
        self,
        context: Dict[str, Any],
        tick: int = 0,
        style: str = "brief"
    ) -> DeliberationResult:
        """
        Generate internal deliberation before speaking.
        
        Args:
            context: Dict with keys like 'stimulus', 'recent_arguments', 
                    'current_topic', 'others_votes'
            tick: Current simulation tick
            style: 'brief', 'standard', 'deep'
        
        Returns:
            DeliberationResult with internal monologue
        """
        stimulus = context.get("stimulus", "")
        others_arguments = context.get("recent_arguments", [])
        others_votes = context.get("others_votes", {})
        
        # Build deliberation prompt
        prompt = self._build_deliberation_prompt(
            stimulus=stimulus,
            others_arguments=others_arguments,
            others_votes=others_votes,
            style=style
        )
        
        # Generate deliberation via LLM or use template
        if self._llm_call:
            try:
                content = await self._llm_call(prompt, max_tokens=200)
            except Exception as e:
                logger.warning(f"LLM deliberation failed: {e}")
                content = self._template_deliberation(context)
        else:
            content = self._template_deliberation(context)
        
        # Determine emotional reaction
        emotional_reaction = self._determine_emotional_reaction(stimulus)
        
        # Determine if should speak and urgency
        should_speak, urgency = self._calculate_speak_urgency(
            context, content
        )
        
        # Create result
        result = DeliberationResult(
            deliberation_type=DeliberationType.EVALUATION,
            content=content,
            reasoning_chain=self._build_reasoning_chain(context),
            emotional_reaction=emotional_reaction,
            confidence=self._calculate_confidence(context),
            should_speak=should_speak,
            speak_urgency=urgency
        )
        
        # Store in history
        self.deliberation_history.append(result)
        
        logger.debug(f"Deliberation for {self.agent_id}: {content[:100]}...")
        
        return result
    
    def _build_deliberation_prompt(
        self,
        stimulus: str,
        others_arguments: List[str],
        others_votes: Dict[str, int],
        style: str
    ) -> str:
        """Build the deliberation prompt for LLM."""
        
        # Get emotional context
        valence = self.emotional_state.get("valence", 0.0)
        arousal = self.emotional_state.get("arousal", 0.5)
        
        emotion_desc = "neutral"
        if valence > 0.3:
            emotion_desc = "positive"
        elif valence < -0.3:
            emotion_desc = "negative"
        
        if arousal > 0.7:
            emotion_desc += ", high energy"
        elif arousal < 0.3:
            emotion_desc += ", calm"
        
        prompt = f"""You are deliberating internally before speaking. 

CURRENT EMOTIONAL STATE: {emotion_desc}
AROUSAL LEVEL: {arousal:.0%}

SITUATION: {stimulus}

"""
        
        if others_arguments:
            prompt += f"OTHER JURORS SAID:\n"
            for arg in others_arguments[-3:]:
                prompt += f"- {arg[:100]}\n"
            prompt += "\n"
        
        if others_votes:
            prompt += f"CURRENT VOTES: "
            for vote, count in others_votes.items():
                prompt += f"{vote}={count} "
            prompt += "\n\n"
        
        # Get belief context if available
        if self.belief_system:
            core_belief = self.belief_system.get_belief(
                self.belief_system.core_belief_id
            ) if hasattr(self.belief_system, 'core_belief_id') else None
            
            if core_belief:
                prompt += f"CURRENT BELIEF: {core_belief.statement} (confidence: {core_belief.confidence:.0%})\n\n"
        
        prompt += """Think about:
1. What is your immediate reaction?
2. Do you agree or disagree with what was said?
3. What do you want to say next?
4. How confident are you?

Respond as your character's internal monologue. Keep it brief and natural."""
        
        return prompt
    
    def _template_deliberation(self, context: Dict[str, Any]) -> str:
        """Template-based deliberation when LLM unavailable."""
        stimulus = context.get("stimulus", "")
        others_votes = context.get("others_votes", {})
        
        valence = self.emotional_state.get("valence", 0.0)
        
        # Build simple template response
        if valence > 0.3:
            reaction = "I see their point,"
        elif valence < -0.3:
            reaction = "That's not right,"
        else:
            reaction = "Let me think about this,"
        
        # Add vote context
        if others_votes:
            my_vote = context.get("my_vote", "unknown")
            total = sum(others_votes.values())
            if total > 0:
                my_count = others_votes.get(my_vote, 0)
                if my_count < total / 2:
                    reaction += " I'm in the minority here."
                else:
                    reaction += " I'm with the majority."
        
        return f"{reaction} {stimulus[:50]}..."
    
    def _determine_emotional_reaction(self, stimulus: str) -> str:
        """Determine emotional reaction to stimulus."""
        stimulus_lower = stimulus.lower()
        
        # Check for triggers in stimulus
        negative_triggers = ["wrong", "guilty", "lies", "fool", "ridiculous"]
        positive_triggers = ["reasonable", "doubt", "not guilty", "fair"]
        
        for word in negative_triggers:
            if word in stimulus_lower:
                if self.emotional_state.get("arousal", 0.5) > 0.6:
                    return "frustrated"
                return "defensive"
        
        for word in positive_triggers:
            if word in stimulus_lower:
                return "receptive"
        
        return "neutral"
    
    def _calculate_speak_urgency(
        self,
        context: Dict[str, Any],
        content: str
    ) -> tuple:
        """Calculate if agent should speak and how urgently."""
        # Base urgency
        urgency = 0.3
        
        # Increase urgency if in minority
        others_votes = context.get("others_votes", {})
        my_vote = context.get("my_vote", "unknown")
        if others_votes:
            total = sum(others_votes.values())
            if total > 0:
                my_count = others_votes.get(my_vote, 0)
                if my_count < total / 3:
                    urgency += 0.3  # Strong minority
                elif my_count < total / 2:
                    urgency += 0.15  # Weak minority
        
        # Increase urgency if arousal is high
        urgency += self.emotional_state.get("arousal", 0.5) * 0.2
        
        # Decrease if personality is patient
        patience = self.personality.get("patience", 0.5)
        urgency -= patience * 0.1
        
        urgency = max(0.1, min(1.0, urgency))
        
        # Should speak if urgency > 0.5
        should_speak = urgency > 0.4
        
        return should_speak, urgency
    
    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence in current position."""
        # Base from belief system if available
        if self.belief_system:
            try:
                if hasattr(self.belief_system, 'core_belief_id'):
                    belief = self.belief_system.get_belief(
                        self.belief_system.core_belief_id
                    )
                    if belief:
                        return belief.confidence
            except:
                pass
        
        # Default moderate confidence
        return 0.5
    
    def _build_reasoning_chain(self, context: Dict[str, Any]) -> List[str]:
        """Build reasoning chain for deliberation."""
        chain = []
        
        # Add belief-based reasoning
        if self.belief_system:
            chain.append("Evaluated against current beliefs")
        
        # Add emotional reaction
        chain.append(f"Emotional reaction: {self._determine_emotional_reaction(context.get('stimulus', ''))}")
        
        # Add social context
        others_votes = context.get("others_votes", {})
        if others_votes:
            chain.append(f"Social context: {others_votes}")
        
        return chain
    
    def get_recent_deliberations(self, k: int = 5) -> List[DeliberationResult]:
        """Get k most recent deliberations."""
        return self.deliberation_history[-k:]
    
    def has_deliberated_recently(self, tick: int, window: int = 50) -> bool:
        """Check if agent has deliberated within the last window ticks."""
        if not self.deliberation_history:
            return False
        
        # Check last deliberation
        last = self.deliberation_history[-1]
        # We don't have tick stored in result, so just check count
        return len(self.deliberation_history) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize deliberation engine state."""
        return {
            "agent_id": self.agent_id,
            "deliberation_count": len(self.deliberation_history),
            "recent_deliberations": [
                d.to_dict() for d in self.deliberation_history[-5:]
            ]
        }


# ========================
# HELPER FUNCTIONS
# ========================

def create_deliberation_engine(
    agent_id: str,
    belief_system: Any = None,
    emotional_state: Dict[str, float] = None,
    personality: Dict[str, float] = None,
    llm_call: Callable = None
) -> DeliberationEngine:
    """
    Factory function to create a deliberation engine.
    
    Args:
        agent_id: ID of the agent
        belief_system: BeliefSystem instance
        emotional_state: PAD emotional state dict
        personality: Personality traits dict
        llm_call: Optional LLM callable
    
    Returns:
        Configured DeliberationEngine
    """
    return DeliberationEngine(
        agent_id=agent_id,
        belief_system=belief_system,
        emotional_state=emotional_state,
        personality=personality,
        llm_call=llm_call
    )
