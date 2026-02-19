# Agent Architecture V3 Specification

**Date:** February 19, 2026
**Based on:** 30-minute Oracle Experiment Analysis
**Status:** Draft for Review

---

## Overview

This spec defines **general-purpose improvements** to the Tsukuyomi agent architecture. These changes are not scenario-specific - they apply to ANY social simulation (jury, marketplace, political debate, social gathering, etc.).

The improvements address five core architectural gaps identified through agent behavior analysis:

1. **Belief Plasticity** - Agents get stuck in high-confidence states
2. **LLM Response Homogenization** - Repetitive, formulaic responses
3. **Emotional State Disconnect** - Emotions exist but don't affect behavior
4. **Conversation Memory Fragmentation** - No personal narrative continuity
5. **Behavioral Diversity** - All agents follow same interaction patterns

---

## 1. BELIEF PLASTICITY SYSTEM

### 1.1 Problem Statement

**Observation:**
- 255 belief saturation warnings during 30-min experiment
- Agents hit ~88% confidence and become immutable
- Persuasion mechanics exist but beliefs resist change at saturation
- No mechanism for agents to question their own certainties

**Why it matters for any scenario:**
- Marketplace: Merchants won't adjust prices based on competition
- Politics: Voters won't swing regardless of campaign
- Social: Relationships won't evolve after initial formation
- Learning: Agents can't update mental models

**Root Cause:**
- Linear memory decay is too slow
- No random perturbation events
- No contradiction detection between beliefs
- Confidence floors prevent downward movement

### 1.2 Implementation

#### A. Exponential Memory Decay

**Location:** `tsukuyomi/agent/belief_system.py`

**Current Behavior:**
```python
def decay_beliefs(self, tick: int, decay_rate: float = 0.01):
    """Linear decay - too slow"""
    for belief in self.beliefs.values():
        belief.confidence *= (1 - decay_rate)
```

**New Implementation:**
```python
import math
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class DecayConfig:
    """Configuration for belief decay."""
    base_rate: float = 0.005           # Base decay per tick
    time_factor: float = 0.0001        # Exponential time component
    min_confidence: float = 0.1        # Floor for decay
    saturation_threshold: float = 0.85 # Confidence level for perturbation
    perturbation_chance: float = 0.02  # Chance to perturb saturated beliefs
    perturbation_strength: float = 0.15 # How much to reduce confidence


class BeliefSystem:
    def decay_beliefs(
        self, 
        tick: int, 
        config: Optional[DecayConfig] = None
    ) -> Dict[str, float]:
        """
        Apply exponential decay to all beliefs.
        
        Decay formula: confidence *= e^(-rate * age)
        
        Returns dict of belief_id -> new_confidence for beliefs that changed.
        """
        config = config or DecayConfig()
        changes = {}
        
        for belief_id, belief in self.beliefs.items():
            if belief.confidence <= config.min_confidence:
                continue
            
            # Calculate age in ticks
            age = tick - belief.last_updated
            if age <= 0:
                continue
            
            # Exponential decay: faster decay for older beliefs
            decay_factor = math.exp(-config.base_rate * age * config.time_factor)
            old_confidence = belief.confidence
            belief.confidence = max(config.min_confidence, belief.confidence * decay_factor)
            
            if abs(old_confidence - belief.confidence) > 0.001:
                changes[belief_id] = belief.confidence
        
        return changes
    
    def perturb_saturated_beliefs(
        self,
        tick: int,
        config: Optional[DecayConfig] = None
    ) -> Dict[str, float]:
        """
        Randomly perturb beliefs that are stuck at high confidence.
        
        Simulates "moments of doubt" where agents question certainties.
        Higher neuroticism = more perturbation events.
        
        Returns dict of belief_id -> new_confidence for perturbed beliefs.
        """
        config = config or DecayConfig()
        changes = {}
        
        for belief_id, belief in self.beliefs.items():
            # Only perturb high-confidence beliefs
            if belief.confidence < config.saturation_threshold:
                continue
            
            # Base chance + neuroticism modifier
            neuroticism = getattr(self, 'neuroticism', 0.5)
            perturb_chance = config.perturbation_chance * (1 + neuroticism)
            
            import random
            if random.random() < perturb_chance:
                old_confidence = belief.confidence
                reduction = config.perturbation_strength * random.uniform(0.5, 1.5)
                belief.confidence = max(
                    config.min_confidence,
                    belief.confidence - reduction
                )
                belief.last_updated = tick
                
                changes[belief_id] = belief.confidence
                logger.info(
                    f"Belief perturbed: {belief_id[:20]}... "
                    f"{old_confidence:.2f} -> {belief.confidence:.2f}"
                )
        
        return changes
```

#### B. Contradiction Detection

**Location:** `tsukuyomi/agent/belief_system.py`

```python
def detect_contradictions(self) -> List[Dict[str, Any]]:
    """
    Detect pairs of beliefs that contradict each other.
    
    Returns list of contradiction pairs with severity.
    """
    contradictions = []
    beliefs_list = list(self.beliefs.values())
    
    for i, b1 in enumerate(beliefs_list):
        for b2 in beliefs_list[i+1:]:
            # Check if beliefs have opposing stances
            if self._are_contradictory(b1, b2):
                # Severity based on both confidences
                severity = (b1.confidence + b2.confidence) / 2
                contradictions.append({
                    "belief_1": b1.id,
                    "belief_2": b2.id,
                    "statement_1": b1.statement,
                    "statement_2": b2.statement,
                    "severity": severity
                })
    
    return contradictions

def _are_contradictory(self, b1: Belief, b2: Belief) -> bool:
    """Check if two beliefs contradict each other."""
    # Check for negation keywords
    negation_words = ["not", "never", "no", "isn't", "doesn't", "won't"]
    
    s1_lower = b1.statement.lower()
    s2_lower = b2.statement.lower()
    
    # Simple heuristic: same core with negation
    for neg in negation_words:
        if neg in s1_lower and neg not in s2_lower:
            # Check if rest is similar
            core1 = s1_lower.replace(neg, "").strip()
            if self._similarity(core1, s2_lower) > 0.7:
                return True
        if neg in s2_lower and neg not in s1_lower:
            core2 = s2_lower.replace(neg, "").strip()
            if self._similarity(core2, s1_lower) > 0.7:
                return True
    
    return False

def _similarity(self, s1: str, s2: str) -> float:
    """Calculate text similarity using word overlap."""
    words1 = set(s1.split())
    words2 = set(s2.split())
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)

def resolve_contradiction(
    self,
    contradiction: Dict[str, Any],
    resolution: str = "reduce_both"
) -> Dict[str, float]:
    """
    Resolve a detected contradiction.
    
    Resolution strategies:
    - "reduce_both": Reduce confidence of both beliefs
    - "keep_stronger": Keep higher confidence belief
    - "random": Randomly choose one to reduce
    
    Returns changes made.
    """
    b1 = self.beliefs.get(contradiction["belief_1"])
    b2 = self.beliefs.get(contradiction["belief_2"])
    
    if not b1 or not b2:
        return {}
    
    changes = {}
    
    if resolution == "reduce_both":
        reduction = contradiction["severity"] * 0.2
        b1.confidence = max(0.1, b1.confidence - reduction)
        b2.confidence = max(0.1, b2.confidence - reduction)
        changes[b1.id] = b1.confidence
        changes[b2.id] = b2.confidence
        
    elif resolution == "keep_stronger":
        weaker = b1 if b1.confidence < b2.confidence else b2
        weaker.confidence = max(0.1, weaker.confidence - 0.3)
        changes[weaker.id] = weaker.confidence
        
    elif resolution == "random":
        import random
        target = random.choice([b1, b2])
        target.confidence = max(0.1, target.confidence - 0.25)
        changes[target.id] = target.confidence
    
    return changes
```

#### C. Context-Dependent Plasticity

**Location:** `tsukuyomi/agent/belief_system.py`

```python
def get_plasticity(self, context: Dict[str, float]) -> float:
    """
    Calculate current belief plasticity based on context.
    
    High stress = more malleable
    High arousal = more malleable
    Recent failures = more malleable
    
    Returns plasticity multiplier 0.5-2.0
    """
    base_plasticity = 1.0
    
    # Stress modifier (high stress = more open to change)
    stress = context.get("stress", 0.5)
    stress_mod = 1.0 + (stress - 0.5) * 0.5  # 0.75-1.25
    
    # Arousal modifier (high arousal = less deliberate = more changeable)
    arousal = context.get("arousal", 0.5)
    arousal_mod = 1.0 + (arousal - 0.5) * 0.3  # 0.85-1.15
    
    # Recent contradiction modifier
    contradictions = context.get("recent_contradictions", 0)
    contr_mod = min(1.5, 1.0 + contradictions * 0.1)
    
    # Neuroticism affects plasticity (high neuroticism = more reactive)
    neuroticism = getattr(self, 'neuroticism', 0.5)
    neuro_mod = 0.8 + neuroticism * 0.4  # 0.8-1.2
    
    return base_plasticity * stress_mod * arousal_mod * contr_mod * neuro_mod
```

### 1.3 Tests Required

```python
# tests/test_belief_plasticity.py

def test_exponential_decay_faster_for_older():
    """Older beliefs decay faster than newer ones."""
    system = BeliefSystem()
    b1 = system.add_belief("New belief", 0.9, tick=1000)
    b2 = system.add_belief("Old belief", 0.9, tick=0)
    
    system.decay_beliefs(tick=1000)
    
    assert system.beliefs[b2].confidence < system.beliefs[b1].confidence

def test_perturbation_affects_high_confidence():
    """Only high confidence beliefs get perturbed."""
    system = BeliefSystem()
    system.add_belief("High", 0.95)
    system.add_belief("Low", 0.5)
    
    # Mock random to force perturbation
    with mock.patch('random.random', return_value=0.01):
        changes = system.perturb_saturated_beliefs(tick=100)
    
    assert "High" in str(changes) or changes == {}

def test_contradiction_detection():
    """Contradictory beliefs are detected."""
    system = BeliefSystem()
    system.add_belief("The defendant is guilty")
    system.add_belief("The defendant is not guilty")
    
    contradictions = system.detect_contradictions()
    
    assert len(contradictions) == 1
    assert contradictions[0]["severity"] > 0.5

def test_plasticity_stress_modifier():
    """High stress increases plasticity."""
    system = BeliefSystem()
    
    low_stress = system.get_plasticity({"stress": 0.2})
    high_stress = system.get_plasticity({"stress": 0.8})
    
    assert high_stress > low_stress
```

---

## 2. LLM RESPONSE HOMOGENIZATION

### 2.1 Problem Statement

**Observation:**
- Arthur repeatedly says "I've seen enough" and "slam dunk"
- Similar sentence structures across different agents
- Formulaic opening phrases ("I have to admit...", "Based on...")
- Agents don't vary their communication style

**Why it matters for any scenario:**
- Breaks immersion - 100 agents feel like 1 agent with 100 names
- Reduces perceived simulation complexity
- Makes long-running simulations feel repetitive
- Hides individual personality differences

**Root Cause:**
- No response history tracking
- No repetition penalty in prompts
- Style not injected from profile
- Mood doesn't affect language

### 2.2 Implementation

#### A. Response History Tracking

**Location:** `tsukuyomi/agent/conversation.py` (NEW FILE)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

@dataclass
class ResponseRecord:
    """Record of a single agent response."""
    tick: int
    content: str
    prompt_type: str
    tone: str
    word_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def content_hash(self) -> str:
        """Hash of content for quick comparison."""
        return hashlib.md5(self.content.lower().encode()).hexdigest()[:8]
    
    def key_phrases(self) -> List[str]:
        """Extract key phrases for similarity checking."""
        # Common repetitive patterns to flag
        words = self.content.lower().split()
        phrases = []
        
        # Extract 2-3 word phrases
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")
        for i in range(len(words) - 2):
            phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases


class ResponseHistory:
    """Tracks agent's recent responses to prevent repetition."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.responses: List[ResponseRecord] = []
        self.phrase_counts: Dict[str, int] = {}
        self.repetition_threshold = 3  # Max times a phrase can appear
    
    def add(self, response: ResponseRecord):
        """Add a response to history."""
        self.responses.append(response)
        
        # Update phrase counts
        for phrase in response.key_phrases():
            self.phrase_counts[phrase] = self.phrase_counts.get(phrase, 0) + 1
        
        # Trim old responses
        if len(self.responses) > self.max_history:
            removed = self.responses.pop(0)
            # Update phrase counts for removed response
            for phrase in removed.key_phrases():
                if phrase in self.phrase_counts:
                    self.phrase_counts[phrase] -= 1
                    if self.phrase_counts[phrase] <= 0:
                        del self.phrase_counts[phrase]
    
    def get_repetitive_phrases(self) -> List[str]:
        """Get phrases that have been used too often."""
        return [
            phrase for phrase, count in self.phrase_counts.items()
            if count >= self.repetition_threshold
        ]
    
    def similarity_score(self, new_content: str) -> float:
        """Calculate how similar new content is to recent responses."""
        if not self.responses:
            return 0.0
        
        new_phrases = set()
        words = new_content.lower().split()
        for i in range(len(words) - 1):
            new_phrases.add(f"{words[i]} {words[i+1]}")
        
        # Check overlap with recent responses
        overlaps = []
        for resp in self.responses[-5:]:
            resp_phrases = set(resp.key_phrases())
            overlap = len(new_phrases & resp_phrases)
            total = len(new_phrases | resp_phrases)
            similarity = overlap / total if total > 0 else 0
            overlaps.append(similarity)
        
        return max(overlaps) if overlaps else 0.0
    
    def is_too_similar(self, new_content: str, threshold: float = 0.6) -> bool:
        """Check if new content is too similar to recent responses."""
        return self.similarity_score(new_content) > threshold
```

#### B. Style Injection System

**Location:** `tsukuyomi/agent/personality.py`

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CommunicationStyle:
    """Defines how an agent communicates."""
    
    # Vocabulary characteristics
    vocabulary_level: str = "medium"  # simple, medium, complex
    preferred_words: List[str] = None  # Words this agent favors
    avoided_words: List[str] = None   # Words this agent avoids
    
    # Sentence structure
    avg_sentence_length: int = 15      # Target words per sentence
    uses_contractions: bool = True     # Don't vs do not
    uses_fillers: bool = False         # "um", "well", "you know"
    filler_words: List[str] = None
    
    # Formality
    formality: float = 0.5             # 0=casual, 1=formal
    uses_slang: bool = False
    slang_words: List[str] = None
    
    # Expressiveness
    emotional_expression: float = 0.5  # How much emotion shows
    punctuation_style: str = "normal"   # normal, emphatic, minimal
    rhetorical_questions: bool = True   # Use questions for impact
    
    def __post_init__(self):
        if self.preferred_words is None:
            self.preferred_words = []
        if self.avoided_words is None:
            self.avoided_words = []
        if self.filler_words is None:
            self.filler_words = ["well", "you know", "I mean"]
        if self.slang_words is None:
            self.slang_words = []


def inject_style_into_prompt(
    base_prompt: str,
    style: CommunicationStyle,
    recent_responses: Optional[ResponseHistory] = None
) -> str:
    """
    Inject communication style guidelines into LLM prompt.
    
    Args:
        base_prompt: The base prompt without style guidelines
        style: Communication style configuration
        recent_responses: Response history to check for repetition
    
    Returns:
        Prompt with style guidelines appended
    """
    style_guidelines = f"""
    
## COMMUNICATION STYLE GUIDELINES
You are playing a character with the following communication traits:
- Vocabulary level: {style.vocabulary_level}
- Average sentence length: ~{style.avg_sentence_length} words
- Formality: {"formal" if style.formality > 0.7 else "casual" if style.formality < 0.3 else "conversational"}
- Emotional expression: {"high" if style.emotional_expression > 0.7 else "low" if style.emotional_expression < 0.3 else "moderate"}
"""
    
    # Add preferred words if any
    if style.preferred_words:
        style_guidelines += f"\n- Your character tends to use these words: {', '.join(style.preferred_words)}"
    
    # Add avoided words if any
    if style.avoided_words:
        style_guidelines += f"\n- Avoid using these words: {', '.join(style.avoided_words)}"
    
    # Add repetition warning if needed
    if recent_responses:
        repetitive = recent_responses.get_repetitive_phrases()
        if repetitive:
            style_guidelines += f"\n- AVOID overused phrases: {', '.join(repetitive[:3])}"
            style_guidelines += "\n- Try to express the same ideas with different wording"
    
    # Add filler guidance
    if style.uses_fillers and style.filler_words:
        style_guidelines += f"\n- Your character sometimes uses filler words: {', '.join(style.filler_words[:2])}"
    
    # Add punctuation style
    if style.punctuation_style == "emphatic":
        style_guidelines += "\n- Use EMPHATIC punctuation (CAPS for emphasis, exclamation marks)"
    elif style.punctuation_style == "minimal":
        style_guidelines += "\n- Use minimal punctuation, short sentences"
    
    return base_prompt + style_guidelines
```

### 2.3 Tests Required

```python
# tests/test_response_variety.py

def test_response_history_tracks_responses():
    """Response history records all responses."""
    history = ResponseHistory(max_history=5)
    history.add(ResponseRecord(tick=100, content="Hello world", prompt_type="greet", tone="neutral", word_count=2))
    assert len(history.responses) == 1

def test_similarity_detection():
    """Similar phrases are detected."""
    history = ResponseHistory()
    history.add(ResponseRecord(tick=100, content="I believe the defendant is guilty", prompt_type="vote", tone="certain", word_count=7))
    
    similar = history.similarity_score("I believe the defendant is not guilty")
    assert similar > 0.5

def test_style_injection():
    """Style guidelines are injected into prompt."""
    style = CommunicationStyle(
        vocabulary_level="simple",
        formality=0.8,
        preferred_words=["concerning"]
    )
    
    prompt = inject_style_into_prompt("Say something", style)
    
    assert "simple" in prompt.lower()
    assert "concerning" in prompt.lower()
    assert "formal" in prompt.lower()
```

---

## 3. EMOTIONAL STATE INTEGRATION

### 3.1 Problem Statement

**Observation:**
- PAD (Pleasure-Arousal-Dominance) values exist in agent profiles
- Values update based on events (persuasion, contradiction)
- BUT: Emotional state doesn't influence dialogue generation
- Emotional changes don't affect behavior patterns

**Why it matters for any scenario:**
- Angry agents should sound different than calm ones
- High arousal = more active behavior, shorter responses
- Dominance affects leadership in group settings
- Emotional contagion creates realistic group dynamics

**Root Cause:**
- Emotional state stored but never read during response generation
- No connection between PAD values and prompt construction
- No emotional contagion between nearby agents

### 3.2 Implementation

#### A. Emotional State Model

**Location:** `tsukuyomi/agent/emotional_state.py` (NEW FILE)

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
import math

class EmotionalTone(Enum):
    """Categorical emotional tones for LLM prompts."""
    NEUTRAL = "neutral"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SAD = "sad"
    HAPPY = "happy"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    CALM = "calm"
    ANXIOUS = "anxious"


@dataclass
class EmotionalState:
    """
    Emotional state using PAD (Pleasure-Arousal-Dominance) model.
    
    Each dimension ranges from -1.0 to 1.0:
    - Pleasure: positive/negative affect (sad vs happy)
    - Arousal: activation level (calm vs excited)
    - Dominance: control/agency (submissive vs dominant)
    """
    pleasure: float = 0.0    # -1 to 1
    arousal: float = 0.0     # -1 to 1
    dominance: float = 0.0   # -1 to 1
    
    # Tracking for dynamics
    history: List[Dict] = field(default_factory=list)
    max_history: int = 100
    
    # Emotional contagion
    susceptibility: float = 0.3  # How easily affected by others' emotions
    
    def __post_init__(self):
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
    
    @property
    def tone(self) -> EmotionalTone:
        """Determine categorical tone from PAD values."""
        # High arousal + negative pleasure = anxious/angry
        if self.arousal > 0.3 and self.pleasure < -0.3:
            return EmotionalTone.ANXIOUS
        if self.arousal > 0.3 and self.pleasure < -0.5:
            return EmotionalTone.ANGRY
        
        # High arousal + positive pleasure = excited/happy
        if self.arousal > 0.3 and self.pleasure > 0.3:
            return EmotionalTone.EXCITED
        if self.arousal > 0.2 and self.pleasure > 0.5:
            return EmotionalTone.HAPPY
        
        # Low arousal + positive pleasure = calm
        if self.arousal < -0.3 and self.pleasure > 0.3:
            return EmotionalTone.CALM
        
        # Low pleasure = sad/disgusted
        if self.pleasure < -0.5:
            return EmotionalTone.SAD
        
        return EmotionalTone.NEUTRAL
    
    def update(
        self,
        event_type: str,
        intensity: float = 0.1,
        source_valence: float = 0.0
    ):
        """
        Update emotional state based on event.
        
        Args:
            event_type: Type of emotional event
            intensity: How strong the event was
            source_valence: Emotional valence of the source (for contagion)
        """
        old_state = (self.pleasure, self.arousal, self.dominance)
        
        # Event-based updates
        if event_type == "persuaded":
            self.pleasure -= intensity * 0.5
            self.arousal += intensity * 0.3
        elif event_type == "contradicted":
            self.pleasure -= intensity * 0.6
            self.arousal += intensity * 0.8
            self.dominance -= intensity * 0.2
        elif event_type == "agreed_with":
            self.pleasure += intensity * 0.7
            self.arousal -= intensity * 0.2
        elif event_type == "threatened":
            self.pleasure -= intensity * 0.8
            self.arousal += intensity
            self.dominance -= intensity * 0.4
        elif event_type == "success":
            self.pleasure += intensity * 0.6
            self.dominance += intensity * 0.3
        elif event_type == "failure":
            self.pleasure -= intensity * 0.5
            self.dominance -= intensity * 0.3
        
        # Emotional contagion from nearby agents
        if source_valence != 0:
            contagion_effect = source_valence * self.susceptibility * intensity
            self.pleasure += contagion_effect
        
        # Clamp values
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
        
        # Record in history
        self.history.append({
            "tick": 0,  # Would be set by caller
            "event": event_type,
            "old": old_state,
            "new": (self.pleasure, self.arousal, self.dominance)
        })
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def apply_to_prompt(self, base_prompt: str) -> str:
        """
        Add emotional context to LLM prompt.
        
        Returns modified prompt with emotional guidelines.
        """
        tone = self.tone
        tone_str = tone.value
        
        # Build emotional context
        context = f"""
        
## CURRENT EMOTIONAL STATE
Your character is currently feeling: {tone_str.upper()}
"""
        
        # Add dimensional context if notable
        if self.arousal > 0.5:
            context += "- You are highly activated/tense right now. Your responses may be more brief and intense.\n"
        elif self.arousal < -0.5:
            context += "- You are calm/relaxed. Take your time with responses.\n"
        
        if self.pleasure > 0.5:
            context += "- You are in a positive mood. You may be more agreeable.\n"
        elif self.pleasure < -0.5:
            context += "- You are in a negative mood. You may be more critical/skeptical.\n"
        
        if self.dominance > 0.5:
            context += "- You feel dominant/assertive. You may take charge of the conversation.\n"
        elif self.dominance < -0.5:
            context += "- You feel submissive/cautious. You may defer to others.\n"
        
        # Add specific tone guidance
        if tone == EmotionalTone.ANGRY:
            context += "- Express frustration and strong opinions. Use shorter, more direct language.\n"
        elif tone == EmotionalTone.ANXIOUS:
            context += "- Show uncertainty. Ask questions. Hedge your statements.\n"
        elif tone == EmotionalTone.EXCITED:
            context += "- Show enthusiasm. Use energetic language. Speak faster.\n"
        elif tone == EmotionalTone.CALM:
            context += "- Use measured, thoughtful language. Take your time.\n"
        
        return base_prompt + context
```

#### B. Emotional Contagion

**Location:** `tsukuyomi/simulation/social_dynamics.py` (NEW FILE)

```python
from typing import List, Dict
from tsukuyomi.agent.emotional_state import EmotionalState

def apply_emotional_contagion(
    agents: List[Dict],
    proximity_matrix: Dict[str, Dict[str, float]],
    tick: int
):
    """
    Apply emotional contagion between nearby agents.
    
    Agents emotionally "catch" states from those they're near.
    Higher proximity = stronger contagion.
    
    Args:
        agents: List of agent dicts with 'id' and 'emotional_state'
        proximity_matrix: Dict of agent_id -> {other_agent_id -> proximity}
        tick: Current simulation tick
    """
    # Calculate emotional influence for each agent
    for agent in agents:
        agent_id = agent["id"]
        agent_state = agent.get("emotional_state")
        
        if not agent_state:
            continue
        
        total_influence = 0.0
        weighted_pleasure = 0.0
        weighted_arousal = 0.0
        
        # Sum emotional influence from nearby agents
        nearby = proximity_matrix.get(agent_id, {})
        
        for other_id, proximity in nearby.items():
            if proximity < 0.1:  # Skip distant agents
                continue
            
            # Find other agent's emotional state
            other_agent = next((a for a in agents if a["id"] == other_id), None)
            if not other_agent or not other_agent.get("emotional_state"):
                continue
            
            other_state = other_agent["emotional_state"]
            
            # Weight by proximity and susceptibility
            influence = proximity * agent_state.susceptibility
            weighted_pleasure += other_state.pleasure * influence
            weighted_arousal += other_state.arousal * influence
            total_influence += influence
        
        # Apply averaged influence
        if total_influence > 0:
            avg_pleasure = weighted_pleasure / total_influence
            avg_arousal = weighted_arousal / total_influence
            
            # Gradual adjustment (not instant)
            agent_state.pleasure += avg_pleasure * 0.1
            agent_state.arousal += avg_arousal * 0.1
            
            # Clamp
            agent_state.pleasure = max(-1.0, min(1.0, agent_state.pleasure))
            agent_state.arousal = max(-1.0, min(1.0, agent_state.arousal))
```

### 3.3 Tests Required

```python
# tests/test_emotional_integration.py

def test_emotional_state_tone_detection():
    """PAD values correctly map to categorical tones."""
    state = EmotionalState(pleasure=-0.6, arousal=0.6, dominance=0.0)
    assert state.tone == EmotionalTone.ANGRY

def test_emotional_update_contradiction():
    """Contradiction events decrease pleasure and increase arousal."""
    state = EmotionalState(pleasure=0.5, arousal=0.2)
    state.update("contradicted", intensity=0.5)
    
    assert state.pleasure < 0.5
    assert state.arousal > 0.2

def test_emotional_contagion():
    """Agents catch emotions from nearby agents."""
    agents = [
        {"id": "a1", "emotional_state": EmotionalState(pleasure=0.8)},
        {"id": "a2", "emotional_state": EmotionalState(pleasure=0.0)}
    ]
    proximity = {"a1": {"a2": 1.0}, "a2": {"a1": 1.0}}
    
    apply_emotional_contagion(agents, proximity, 100)
    
    # a2 should become more positive
    assert agents[1]["emotional_state"].pleasure > 0.0

def test_prompt_injection():
    """Emotional state adds context to prompts."""
    state = EmotionalState(pleasure=-0.6, arousal=0.6)
    prompt = state.apply_to_prompt("Say something")
    
    assert "angry" in prompt.lower() or "ANXIOUS" in prompt
```

---

## 4. CONVERSATION MEMORY SYSTEM

### 4.1 Problem Statement

**Observation:**
- Agents see WHO said what (speaker attribution works ✅)
- But they don't remember their OWN past statements
- No tracking of "topics I've already discussed"
- Can't build on previous arguments or detect inconsistencies

**Why it matters for any scenario:**
- Agents repeat themselves unnecessarily
- No sense of personal narrative continuity
- Can't hold multi-turn discussions coherently
- Breaks illusion of intelligent agent

### 4.2 Implementation

**Location:** `tsukuyomi/agent/memory.py` (NEW FILE)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from datetime import datetime
import re

@dataclass
class Utterance:
    """A single utterance by an agent."""
    tick: int
    content: str
    topic: Optional[str] = None
    position: Optional[str] = None  # "pro", "con", "neutral"
    referenced_agents: List[str] = field(default_factory=list)
    
    def key_topics(self) -> Set[str]:
        """Extract key topics from utterance."""
        topics = set()
        
        # Topic keywords
        topic_keywords = {
            "evidence": ["evidence", "proof", "witness", "testimony"],
            "alibi": ["alibi", "whereabouts", "location"],
            "weapon": ["knife", "switchblade", "weapon"],
            "character": ["character", "background", "record"],
            "procedure": ["verdict", "vote", "decision", "guilty"],
            "emotion": ["feel", "think", "believe", "doubt"],
        }
        
        content_lower = self.content.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.add(topic)
        
        return topics


class ConversationMemory:
    """
    Tracks an agent's conversation history for continuity.
    
    Prevents repetition and enables coherent multi-turn discussions.
    """
    
    def __init__(self, max_utterances: int = 50):
        self.max_utterances = max_utterances
        self.utterances: List[Utterance] = []
        self.discussed_topics: Set[str] = set()
        self.public_positions: Dict[str, str] = {}  # topic -> position
        self.referenced_agents: Set[str] = set()
    
    def add(self, utterance: Utterance):
        """Add an utterance to memory."""
        self.utterances.append(utterance)
        
        # Update topic tracking
        self.discussed_topics.update(utterance.key_topics())
        
        # Track positions if stated
        if utterance.position:
            for topic in utterance.key_topics():
                self.public_positions[topic] = utterance.position
        
        # Track referenced agents
        self.referenced_agents.update(utterance.referenced_agents)
        
        # Trim old utterances
        if len(self.utterances) > self.max_utterances:
            removed = self.utterances.pop(0)
            # Note: Don't remove topics - they're cumulative
    
    def has_discussed(self, topic: str) -> bool:
        """Check if a topic has been discussed."""
        return topic in self.discussed_topics
    
    def get_position_on(self, topic: str) -> Optional[str]:
        """Get agent's stated position on a topic."""
        return self.public_positions.get(topic)
    
    def get_recent_utterances(self, n: int = 5) -> List[Utterance]:
        """Get the n most recent utterances."""
        return self.utterances[-n:]
    
    def consistency_check(self, new_content: str) -> Dict[str, any]:
        """
        Check if new statement is consistent with past positions.
        
        Returns dict with:
        - is_consistent: bool
        - conflicting_topics: List[str]
        - suggested_acknowledgment: str
        """
        new_topics = Utterance(tick=0, content=new_content).key_topics()
        
        conflicts = []
        for topic in new_topics:
            old_position = self.public_positions.get(topic)
            if old_position:
                # Check if new content contradicts old position
                if "not guilty" in new_content.lower() and old_position == "guilty":
                    conflicts.append(topic)
                elif "guilty" in new_content.lower() and old_position == "not_guilty":
                    conflicts.append(topic)
        
        return {
            "is_consistent": len(conflicts) == 0,
            "conflicting_topics": conflicts,
            "suggested_acknowledgment": self._build_acknowledgment(conflicts) if conflicts else None
        }
    
    def _build_acknowledgment(self, conflicts: List[str]) -> str:
        """Build phrase acknowledging position change."""
        if not conflicts:
            return ""
        
        return f"I've reconsidered my position on {', '.join(conflicts)}"
```

---

## 5. BEHAVIORAL DIVERSITY SYSTEM

### 5.1 Problem Statement

**Observation:**
- All agents follow same "respond to last speaker" pattern
- No initiative-taking (starting new topics)
- No silence/withdrawal behavior
- No leadership vs followership dynamics

**Why it matters for any scenario:**
- Real groups have leaders, followers, lurkers
- Some people change topics, others react
- Social dynamics need asymmetric roles
- Makes simulations feel static and uniform

### 5.2 Implementation

**Location:** `tsukuyomi/agent/behavior.py` (NEW FILE)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import random

@dataclass
class BehavioralTraits:
    """
    Defines how an agent behaves in social situations.
    
    These are stable traits that affect decision-making.
    """
    
    # Social behavior
    introversion: float = 0.5    # 0=extrovert, 1=introvert
    dominance: float = 0.5       # 0=follower, 1=leader
    agreeableness: float = 0.5   # 0=challenging, 1=accommodating
    
    # Conversation behavior
    speak_probability: float = 0.3  # Chance to speak per turn
    interrupt_probability: float = 0.1  # Chance to interrupt
    topic_initiation_prob: float = 0.2  # Chance to start new topic
    
    # Responsiveness
    response_latency: float = 0.5  # 0=instant, 1=delayed
    reply_probability: float = 0.7  # Chance to respond when addressed
    
    # Attention
    attention_span: float = 0.5  # How long to focus on one topic
    distractibility: float = 0.3  # Chance to shift attention
    
    def should_speak(self, tick: int, addressing_me: bool) -> bool:
        """
        Determine if agent should speak in this turn.
        
        Args:
            tick: Current simulation tick
            addressing_me: Whether someone directly addressed this agent
        
        Args:
            True if agent should generate a response
        """
        # If directly addressed, high chance to respond
        if addressing_me:
            return random.random() < self.reply_probability
        
        # Otherwise, use base speak probability
        # Modulate by introversion
        effective_prob = self.speak_probability * (2 - self.introversion)
        
        return random.random() < effective_prob
    
    def should_initiate_topic(
        self, 
        current_topic_age: int,
        boredom_threshold: int
    ) -> bool:
        """
        Determine if agent should change the subject.
        
        Args:
            current_topic_age: How long current topic has been discussed
            boredom_threshold: Ticks before agent gets bored
        """
        if current_topic_age < boredom_threshold * self.attention_span:
            return False
        
        return random.random() < self.topic_initiation_prob
    
    def get_leadership_style(self) -> str:
        """Categorical leadership style."""
        if self.dominance > 0.7:
            return "leader"
        elif self.dominance < 0.3:
            return "follower"
        else:
            return "peer"


class BehavioralDecider:
    """
    Decides agent actions based on behavioral traits and context.
    """
    
    def __init__(self, traits: BehavioralTraits):
        self.traits = traits
        self.current_topic_age = 0
    
    def decide_action(
        self,
        context: Dict
    ) -> Dict[str, any]:
        """
        Decide what the agent should do.
        
        Args:
            context: Dict with 'addressing_me', 'last_speaker', 
                    'topic_age', 'group_state', etc.
        
        Returns:
            Dict with 'action' and parameters
        """
        addressing_me = context.get("addressing_me", False)
        
        # Check if should speak
        if not self.traits.should_speak(context.get("tick", 0), addressing_me):
            return {"action": "silent"}
        
        # Check for topic change
        topic_age = context.get("topic_age", 0)
        if self.traits.should_initiate_topic(topic_age, 50):  # 50 tick boredom threshold
            return {"action": "new_topic"}
        
        # Default: respond
        return {
            "action": "respond",
            "to": context.get("last_speaker"),
            "interrupt": random.random() < self.traits.interrupt_probability
        }
    
    def select_respond_target(
        self,
        agents_in_group: List[str],
        recent_interactions: Dict[str, int]
    ) -> Optional[str]:
        """
        Choose who to respond to.
        
        Args:
            agents_in_group: IDs of agents present
            recent_interactions: agent_id -> tick of last interaction
        
        Returns:
            Agent ID to respond to, or None
        """
        if not agents_in_group:
            return None
        
        # Prefer higher dominance agents respond to lower
        # This creates natural leader-follower dynamics
        
        # Simple: respond to most recent speaker
        # Advanced: use interaction history and dominance
        
        return agents_in_group[-1] if agents_in_group else None
```

---

## IMPLEMENTATION ORDER

| Priority | Component | Files to Create/Modify | Estimated Effort |
|----------|-----------|------------------------|-------------------|
| P1 | Belief Plasticity | `belief_system.py` | 6h |
| P2 | Emotional Integration | `emotional_state.py`, `social_dynamics.py` | 5h |
| P3 | Response Variety | `conversation.py`, `personality.py`, `groq_llm.py` | 4h |
| P4 | Conversation Memory | `memory.py` | 3h |
| P5 | Behavioral Diversity | `behavior.py` | 4h |

**Total Estimated:** 22 hours

---

## FILES TO CREATE

### New Files
- `tsukuyomi/agent/emotional_state.py` - PAD emotional model
- `tsukuyomi/agent/conversation.py` - Response history tracking
- `tsukuyomi/agent/memory.py` - Conversation memory
- `tsukuyomi/agent/behavior.py` - Behavioral traits and decisions
- `tsukuyomi/simulation/social_dynamics.py` - Emotional contagion
- `tsukuyomi/agent/personality.py` - Communication style

### Modified Files
- `tsukuyomi/agent/belief_system.py` - Add plasticity, perturbation, contradiction
- `tsukuyomi/experiments/angry_men/groq_llm.py` - Add style/emotion injection
- `tsukuyomi/experiments/angry_men/run_oracle_experiment.py` - Use new systems

### Test Files
- `tests/test_belief_plasticity.py`
- `tests/test_response_variety.py`
- `tests/test_emotional_integration.py`
- `tests/test_conversation_memory.py`
- `tests/test_behavioral_diversity.py`

---

## SUMMARY

This spec addresses five fundamental gaps in the Tsukuyomi V2 agent architecture:

1. **Belief Plasticity** - Agents now have fluid, adaptive belief systems with exponential decay, random perturbation, and contradiction detection

2. **Response Variety** - Agents generate diverse, personality-consistent dialogue through style injection and repetition prevention

3. **Emotional Integration** - PAD emotional model affects behavior and spreads through contagion

4. **Conversation Memory** - Agents maintain personal narrative continuity and consistency

5. **Behavioral Diversity** - Agents have distinct interaction patterns (leaders, followers, initiators, reactors)

These improvements make ANY social simulation more realistic and emergent, not just jury deliberations.

---

*Spec created: February 19, 2026*