# System Improvements Specification

**Date:** February 18, 2026
**Based on:** 30-minute Oracle Experiment Analysis

---

## Overview

This spec defines improvements in two categories:
1. **General System** - Affects agents in ANY scenario
2. **Jury-Specific** - Only affects "Angry Men" deliberation experiments

---

## PART 1: GENERAL SYSTEM IMPROVEMENTS

### 1.1 Asymmetric Influence System

**Problem:** All agents influence each other equally, regardless of personality, credibility, or relationship.

**Current Behavior:**
```
Observer → Sarah: 1,453 belief updates
Sarah → Observer: 1,453 belief updates
```

**Expected Behavior:**
- High openness agents more influenceable
- High credibility speakers more persuasive
- Trust history affects influence weight
- Argument quality matters

**Implementation:**

#### A. Add `InfluenceWeightCalculator` class

Location: `tsukuyomi/agent/influence.py` (NEW FILE)

```python
@dataclass
class InfluenceFactors:
    """Factors that determine influence weight."""
    speaker_credibility: float = 0.5      # Expertise, history
    listener_openness: float = 0.5        # Big Five openness
    relationship_trust: float = 0.5       # History between agents
    argument_quality: float = 0.5         # Strength of argument
    personality_compatibility: float = 0.5  # Similar traits
    
    @property
    def total_weight(self) -> float:
        """Calculate composite influence weight."""
        return (
            self.speaker_credibility * 0.25 +
            self.listener_openness * 0.25 +
            self.relationship_trust * 0.20 +
            self.argument_quality * 0.15 +
            self.personality_compatibility * 0.15
        )
```

#### B. Add `get_influence_weight()` to BeliefSystem

Location: `tsukuyomi/agent/belief_system.py`

```python
def get_influence_weight(
    self,
    speaker_id: str,
    speaker_personality: Dict[str, float],
    speaker_credibility: float,
    argument_strength: float,
    relationship_trust: float
) -> float:
    """
    Calculate how much influence a speaker has on this agent.
    
    Returns weight 0.0-1.0, where:
    - 0.0 = no influence
    - 0.5 = moderate influence
    - 1.0 = strong influence
    """
    # Listener's openness
    openness = self.openness
    
    # Personality compatibility (similar traits = more influence)
    compatibility = self._calculate_compatibility(speaker_personality)
    
    factors = InfluenceFactors(
        speaker_credibility=speaker_credibility,
        listener_openness=openness,
        relationship_trust=relationship_trust,
        argument_quality=argument_strength,
        personality_compatibility=compatibility
    )
    
    return factors.total_weight
```

#### C. Modify evidence evaluation to use influence weight

Location: `tsukuyomi/agent/belief_system.py` - `evaluate_evidence()`

```python
def evaluate_evidence(
    self,
    belief_id: str,
    evidence_id: str,
    tick: int = 0,
    influence_weight: float = 0.5  # NEW PARAMETER
) -> Optional[BeliefUpdate]:
    """..."""
    # ... existing code ...
    
    # Apply influence weight to impact
    impact *= influence_weight  # NEW: Scale by influence
    
    # ... rest of existing code ...
```

**Tests Required:**
- `test_influence_weight_high_openness()` - High openness = more influenceable
- `test_influence_weight_low_openness()` - Low openness = less influenceable
- `test_influence_weight_high_trust()` - High trust = more influence
- `test_influence_weight_credibility()` - High credibility = more influence
- `test_influence_weight_asymmetric()` - A→B ≠ B→A

---

### 1.2 Repetitive Dialogue Prevention

**Problem:** Agents repeat similar phrases in late stages.

**Implementation:**

Location: `tsukuyomi/proto/conversation_manager.py`

```python
class ConversationManager:
    def __init__(self, agents, base_speak_probability=0.3):
        # ... existing ...
        self.recent_phrases: Dict[str, List[str]] = {}  # agent_id -> phrases
        self.repetition_threshold = 0.7  # Similarity threshold
    
    def record_phrase(self, agent_id: str, phrase: str):
        """Record a phrase spoken by an agent."""
        if agent_id not in self.recent_phrases:
            self.recent_phrases[agent_id] = []
        self.recent_phrases[agent_id].append(phrase.lower())
        # Keep only last 10 phrases
        self.recent_phrases[agent_id] = self.recent_phrases[agent_id][-10:]
    
    def is_repetitive(self, agent_id: str, new_phrase: str) -> bool:
        """Check if phrase is too similar to recent ones."""
        if agent_id not in self.recent_phrases:
            return False
        
        new_lower = new_phrase.lower()
        for recent in self.recent_phrases[agent_id]:
            similarity = self._phrase_similarity(new_lower, recent)
            if similarity > self.repetition_threshold:
                return True
        return False
    
    def _phrase_similarity(self, p1: str, p2: str) -> float:
        """Calculate similarity between two phrases."""
        words1 = set(p1.split())
        words2 = set(p2.split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
```

**Tests Required:**
- `test_phrase_similarity()` - Similar phrases detected
- `test_phrase_different()` - Different phrases not flagged
- `test_repetition_detection()` - Consecutive similar phrases flagged

---

### 1.3 Existential Response System

**Problem:** Agents dismiss Observer's existential claims without genuine reaction.

**Implementation:**

Location: `tsukuyomi/agent/belief_system.py`

```python
# Add to BeliefType enum
class BeliefType(Enum):
    # ... existing ...
    METAPHYSICAL = "metaphysical"  # Beliefs about reality/existence

# Add to BeliefSystem
def process_existential_challenge(
    self,
    claim: str,
    source_id: str,
    tick: int = 0
) -> Dict[str, Any]:
    """
    Process a challenge to the nature of reality.
    
    High openness agents are more affected.
    Low conscientiousness agents experience more doubt.
    
    Returns dict with effects applied.
    """
    effects = {
        "reality_stability_affected": False,
        "new_beliefs_formed": [],
        "emotional_impact": 0.0
    }
    
    # Only high openness agents genuinely question reality
    if self.openness > 0.6:
        # Form a metaphysical belief
        belief_id = self.add_belief(
            statement=f"Possibility: {claim[:50]}",
            confidence=0.2 + (self.openness - 0.6) * 0.5,  # 0.2-0.4
            belief_type=BeliefType.METAPHYSICAL,
            source=source_id,
            tick=tick,
            tags=["existential", "uncertain"]
        )
        effects["new_beliefs_formed"].append(belief_id)
        effects["reality_stability_affected"] = True
    
    # Emotional impact based on neuroticism
    neuroticism = getattr(self, 'neuroticism', 0.5)
    effects["emotional_impact"] = neuroticism * 0.1
    
    return effects
```

**Tests Required:**
- `test_existential_high_openness()` - High openness forms belief
- `test_existential_low_openness()` - Low openness ignores
- `test_metaphysical_belief_type()` - Correct belief type

---

## PART 2: JURY-SPECIFIC IMPROVEMENTS

### 2.1 Dynamic Tension Calculation

**Problem:** Tension flatlines when votes stabilize.

**Implementation:**

Location: `experiments/angry_men/drama/director.py`

```python
def calculate_tension(
    self,
    agents: List[Any],
    vote_state: Dict[str, int],
    conversation_intensity: float = 0.0
) -> float:
    """
    Calculate tension from multiple sources.
    
    Not just vote disagreement, but also:
    - Emotional intensity
    - Personality clashes
    - Existential crisis events
    - Argument heat
    """
    # Vote disagreement (existing)
    total_votes = sum(vote_state.values())
    if total_votes == 0:
        vote_tension = 0.0
    else:
        majority = max(vote_state.values())
        minority = min(vote_state.values())
        vote_tension = minority / total_votes  # 0-0.5
    
    # Emotional intensity
    emotional_tension = 0.0
    for agent in agents:
        if hasattr(agent, 'emotional_state'):
            arousal = getattr(agent.emotional_state, 'arousal', 0.0)
            emotional_tension += arousal
    emotional_tension = min(0.5, emotional_tension / len(agents)) if agents else 0.0
    
    # Existential events (Observer revelations)
    existential_tension = min(0.3, self.existential_events * 0.05)
    
    # Argument intensity (caps lock, aggression keywords)
    arg_tension = min(0.2, conversation_intensity * 0.1)
    
    # Combine with weights
    total = (
        vote_tension * 0.4 +
        emotional_tension * 0.25 +
        existential_tension * 0.20 +
        arg_tension * 0.15
    )
    
    return min(1.0, max(0.1, total))
```

**Tests Required:**
- `test_tension_vote_disagreement()` - Vote split increases tension
- `test_tension_emotional()` - Emotional arousal increases tension
- `test_tension_existential()` - Revelation events increase tension
- `test_tension_combined()` - Multiple sources combine

---

### 2.2 Time-Based Act Fallback

**Problem:** Experiment stuck in CONFRONTATION, never reached CLIMAX.

**Implementation:**

Location: `experiments/angry_men/drama/director.py`

```python
def get_act_transition(
    self,
    tick: int,
    total_ticks: int
) -> Optional[Act]:
    """
    Determine if act should transition.
    
    Uses BOTH tension-based AND time-based triggers.
    Time-based ensures progression even with low tension.
    """
    progress = tick / total_ticks if total_ticks > 0 else 0.0
    
    # Existing tension-based logic
    if self.state.tension > 0.6 and self.state.current_act == Act.CONFRONTATION:
        return Act.CLIMAX
    
    if self.state.tension < 0.2 and self.state.current_act == Act.CLIMAX:
        return Act.RESOLUTION
    
    # NEW: Time-based fallback (ensures progression)
    if progress >= 0.85 and self.state.current_act != Act.RESOLUTION:
        return Act.RESOLUTION
    
    if progress >= 0.50 and self.state.current_act == Act.CONFRONTATION:
        return Act.CLIMAX
    
    if progress >= 0.20 and self.state.current_act == Act.SETUP:
        return Act.CONFRONTATION
    
    return None
```

**Tests Required:**
- `test_act_setup_to_confrontation_time()` - Time-based transition
- `test_act_confrontation_to_climax_time()` - Time-based fallback
- `test_act_climax_to_resolution_time()` - Time-based ending

---

### 2.3 Dynamic Drama Beats

**Problem:** No drama beats after early stage.

**Implementation:**

Location: `experiments/angry_men/drama/director.py`

```python
def generate_dynamic_beat(
    self,
    tick: int,
    agents: List[Any],
    recent_events: List[str]
) -> Optional[DramaBeat]:
    """
    Generate a drama beat dynamically based on current state.
    
    Not just predefined beats, but also:
    - Vote change events
    - Belief conflicts
    - Existential revelations
    - Emotional outbursts
    """
    # Check for vote change
    if self._detect_vote_change(recent_events):
        return DramaBeat(
            name="Vote Shift",
            description="A juror changes their vote",
            trigger_type="vote_change",
            directives=["Focus on the reasoning behind the change"]
        )
    
    # Check for existential revelation
    if self._detect_existential_event(recent_events):
        return DramaBeat(
            name="Existential Moment",
            description="Reality is questioned",
            trigger_type="existential",
            directives=["React to the philosophical claim"]
        )
    
    # Check for emotional peak
    high_emotion_agents = [
        a for a in agents
        if hasattr(a, 'emotional_state') and 
        getattr(a.emotional_state, 'arousal', 0) > 0.7
    ]
    if len(high_emotion_agents) >= 2:
        return DramaBeat(
            name="Heated Exchange",
            description="Emotions run high",
            trigger_type="emotional",
            directives=["Express strong feelings"]
        )
    
    return None
```

**Tests Required:**
- `test_dynamic_beat_vote_change()` - Vote change triggers beat
- `test_dynamic_beat_existential()` - Revelation triggers beat
- `test_dynamic_beat_emotional()` - High emotion triggers beat

---

## IMPLEMENTATION ORDER

| Step | Component | Priority | Effort |
|------|-----------|----------|--------|
| 1 | Asymmetric Influence | Critical | 4h |
| 2 | Dynamic Tension | High | 2h |
| 3 | Time-Based Acts | High | 1h |
| 4 | Dynamic Beats | High | 2h |
| 5 | Repetitive Dialogue | Medium | 2h |
| 6 | Existential Response | Medium | 2h |

**Total Estimated:** 13 hours

---

## FILES TO MODIFY

### New Files
- `tsukuyomi/agent/influence.py` - Influence weight calculator

### Modified Files
- `tsukuyomi/agent/belief_system.py` - Influence integration, existential response
- `tsukuyomi/agent/persuasion.py` - Connect influence to persuasion
- `tsukuyomi/proto/conversation_manager.py` - Repetition detection
- `experiments/angry_men/drama/director.py` - Tension, acts, beats
- `experiments/angry_men/run_full_integration.py` - Use new influence system

### Test Files
- `tests/test_influence.py` (NEW)
- `tests/test_belief_system.py` - Add influence tests
- `tests/test_conversation_manager.py` - Add repetition tests
- `tests/test_drama.py` - Add tension/act tests

---

*Spec created: February 18, 2026*
