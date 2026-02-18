# SPEC: Cognitive Richness for Agent Simulation
## Date: 2026-02-18

---

# Executive Summary

This specification addresses critical gaps discovered in the 30-minute Oracle experiment (run_20260218_001341). The analysis revealed that while the agent architecture mechanically functions correctly, agents lack the **cognitive richness** that makes interactions feel natural and emergent.

---

# Part 1: Identified Gaps

## Gap 1: No Internal Deliberation Before Speaking

**Evidence:**
- 100% of utterances follow the pattern: `persuasion_received → persuasion_received → persuasion_received → spoke`
- Agents do not "think" before responding
- No internal monologue logged between stimulus and response

**Impact:**
- Conversations feel robotic and reactive
- Agents cannot reflect on their own positions
- No visible reasoning process

---

## Gap 2: Emotional States Are Invisible

**Evidence:**
- PAD (Pleasure-Arousal-Dominance) emotional model exists in code
- 0% of logged thoughts contain emotional content
- Emotional state never influences dialogue tone

**Impact:**
- Agents sound the same regardless of circumstances
- No emotional escalation or de-escalation
- High-stakes moments feel flat

---

## Gap 3: Turn-Taking Is Perfectly Rigid

**Evidence:**
- Average tick gap between utterances: 48.9 ticks
- Standard deviation: ~0 (nearly constant interval)
- No interruptions, overlapping speech, or silences

**Impact:**
- Unrealistic conversation flow
- No drama from interruptions
- Cannot build tension through overlapping claims

---

## Gap 4: Argument Effectiveness Is Uniform

**Evidence:**
- All argument types (logic, emotion, authority, social proof, scarcity, liking) have identical effectiveness (~4.3%)
- Personality traits do not modulate persuasion susceptibility

**Impact:**
- Persuasion feels mechanical
- No differentiation between agents
- Reduces emergent personality-based dynamics

---

## Gap 5: No Memory-Informed Dialogue

**Evidence:**
- Agents never reference past statements ("Sarah mentioned X earlier...")
- No callbacks to previous arguments
- Each utterance is independent

**Impact:**
- Conversations lack continuity
- Agents appear to have amnesia
- No building on earlier points

---

## Gap 6: Vote History Tracking Failure

**Evidence:**
- George: final_vote=not_guilty but vote_history shows last vote as guilty
- Jack: final_vote=not_guilty but vote_history shows last vote as guilty

**Impact:**
- Cannot reconstruct vote evolution from logs
- Debugging persuasion sequences is impossible

---

# Part 2: Proposed Solutions

## Solution 1: Deliberation Phase

**Architecture Change:**

```
BEFORE (Current):
Stimulus → Belief Update → Speak

AFTER (Proposed):
Stimulus → Belief Update → Emotional Reaction → Deliberation → Memory Retrieval → Response Formulation → Speak
```

**New Components:**

1. **DeliberationThought** - Internal monologue before speaking
2. **EmotionalReaction** - PAD state update visible in logs
3. **MemoryInjection** - Relevant past context injected into LLM prompts

---

## Solution 2: Emotional Expression Layer

**Implementation:**

```python
class EmotionalExpression:
    def __init__(self, pad_state):
        self.pad_state = pad_state
        
    def get_tone_modifiers(self):
        """Returns dialogue modifiers based on emotional state"""
        modifiers = {}
        
        # High arousal = shorter, more emphatic sentences
        if self.pad_state.arousal > 0.7:
            modifiers['sentence_length'] = 'short'
            modifiers['emphasis'] = 'high'
            modifiers['punctuation'] = 'exclamation'
        
        # Low pleasure = defensive, justifying tone
        if self.pad_state.pleasure < 0.3:
            modifiers['justification'] = 'high'
            modifiers['certainty'] = 'medium'
        
        return modifiers
```

---

## Solution 3: Variable Turn-Taking

**Implementation:**

```python
class ConversationManager:
    def __init__(self, agents):
        self.agents = agents
        self.speaking_queue = []
        self.interruption_enabled = True
        
    def should_agent_speak(self, agent, tick):
        # Base probability modified by traits and state
        base_prob = 0.3
        
        # High patience = less likely to interrupt
        patience_factor = (1.0 - agent.traits.get('patience', 0.5))
        
        # High arousal = more interruptive
        arousal_factor = agent.emotional_state.arousal
        
        speak_prob = base_prob + (patience_factor * 0.2) + (arousal_factor * 0.3)
        
        return random.random() < speak_prob
```

---

## Solution 4: Personality-Weighted Persuasion

**Implementation:**

```python
ARGUMENT_EFFECTIVENESS_BY_PERSONALITY = {
    "logic": {
        "openness": 0.8,      # Open agents value logic
        "conscientiousness": 0.6,
    },
    "emotion": {
        "neuroticism": 0.9,    # Neurotic agents are more emotional
        "agreeableness": 0.5,
    },
    "authority": {
        "conscientiousness": 0.8,
        "openness": 0.3,       # Low openness = more deferential
    },
    "social_proof": {
        "extraversion": 0.7,
        "agreeableness": 0.6,
    },
    "scarcity": {
        "conscientiousness": 0.5,
        "neuroticism": 0.7,
    },
    "liking": {
        "agreeableness": 0.8,
        "extraversion": 0.5,
    },
}

def calculate_persuasion_effectiveness(agent, argument_type):
    weights = ARGUMENT_EFFECTIVENESS_BY_PERSONALITY[argument_type]
    
    agent_traits = agent.profile.get('big_five', {})
    
    effectiveness = 0.0
    for trait, weight in weights.items():
        if trait in agent_traits:
            effectiveness += agent_traits[trait] * weight
    
    # Normalize
    effectiveness = effectiveness / len(weights)
    
    return effectiveness
```

---

## Solution 5: Memory-Informed Prompt Injection

**Implementation:**

```python
def build_rich_context_prompt(agent, current_tick, conversation_context):
    prompt_parts = []
    
    # 1. Base character prompt
    prompt_parts.append(agent.immersive_prompt)
    
    # 2. Emotional state injection
    emotional_state = agent.emotional_state
    prompt_parts.append(
        f"\n\nCURRENT EMOTIONAL STATE:\n"
        f"- Pleasure: {emotional_state.pleasure:.2f}\n"
        f"- Arousal: {emotional_state.arousal:.2f}\n"
        f"- Dominance: {emotional_state.dominance:.2f}\n"
    )
    
    # 3. Recent memories (last 3 relevant)
    relevant_memories = agent.memory.retrieve(
        query=conversation_context.get('topic', ''),
        ticks_ago=1000,
        limit=3
    )
    
    if relevant_memories:
        prompt_parts.append("\n\nRECENT RELEVANT MEMORIES:")
        for mem in relevant_memories:
            prompt_parts.append(f"- Tick {mem.tick}: {mem.summary}")
    
    # 4. Pre-deliberation thought
    deliberation = agent.deliberate(conversation_context)
    if deliberation:
        prompt_parts.append(f"\n\nDELIBERATION: {deliberation}")
    
    return "\n".join(prompt_parts)
```

---

## Solution 6: Vote History Fix

**Implementation:**

```python
def update_vote(agent, new_vote, tick, trigger=None):
    old_vote = agent.current_vote
    
    # Update current vote
    agent.current_vote = new_vote
    
    # ALWAYS append to history
    agent.vote_history.append({
        "tick": tick,
        "vote": new_vote,
        "trigger": trigger,
        "confidence": agent.belief_confidence
    })
    
    # Log the change
    logger.info(f"Vote change: {agent.name} {old_vote} -> {new_vote} at tick {tick}")
```

---

# Part 3: Implementation Plan

## Phase 1: Deliberation Layer (Week 1)

| Task | File | Changes |
|------|------|---------|
| Add deliberation method | `AgentBrain.py` | New `deliberate()` method |
| Log deliberation thoughts | `universal_agent.py` | New thought_type: "deliberation" |
| Inject deliberation into prompts | `immersive_prompt.py` | Add deliberation to LLM context |

**Deliverable:** Agents show internal reasoning before speaking

---

## Phase 2: Emotional Expression (Week 2)

| Task | File | Changes |
|------|------|---------|
| Emotional tone modifiers | `AgentBrain.py` | New `get_tone_modifiers()` |
| Inject emotional state | `immersive_prompt.py` | Add PAD state to prompt |
| Response post-processing | `groq_llm.py` | Apply tone modifiers to output |

**Deliverable:** Dialogue reflects emotional state

---

## Phase 3: Conversation Dynamics (Week 3)

| Task | File | Changes |
|------|------|---------|
| Variable turn-taking | `run_full_integration.py` | New `ConversationManager` class |
| Interruption logic | `ConversationManager.py` | New file with interruption rules |
| Silence handling | `ConversationManager.py` | Allow skipped turns |

**Deliverable:** Natural conversation flow with interruptions

---

## Phase 4: Smart Persuasion (Week 4)

| Task | File | Changes |
|------|------|---------|
| Personality-weighted effectiveness | `persuasion.py` | New effectiveness calculation |
| Trait-based resistance | `persuasion.py` | Resistance modifiers by trait |
| Logging effectiveness metrics | `persuasion.py` | Track per-argument success |

**Deliverable:** Different agents react differently to persuasion

---

## Phase 5: Memory Integration (Week 5)

| Task | File | Changes |
|------|------|---------|
| Memory retrieval for prompts | `belief_system.py` | New `retrieve_relevant()` method |
| Callback injection | `immersive_prompt.py` | Add past context to prompts |
| Test callbacks | `tests/test_memory_retrieval.py` | Verify memory references |

**Deliverable:** Agents reference past conversations

---

## Phase 6: Bug Fixes (Week 6)

| Task | File | Changes |
|------|------|---------|
| Vote history tracking | `universal_agent.py` | Fix vote history append |
| Duplicate message prevention | `run_oracle_experiment.py` | Skip LLM on revelation ticks |
| Gap detection expansion | `gap_analysis.py` | Detect more gap types |

**Deliverable:** Clean, accurate experiment logs

---

# Part 4: Testing Strategy

## Unit Tests

| Test | Expected Behavior |
|------|------------------|
| `test_deliberation_before_speak` | Thought type "deliberation" appears before "spoke" |
| `test_emotional_tone_modifiers` | High arousal produces shorter, emphatic output |
| `test_argument_effectiveness_variance` | Different effectiveness by agent personality |
| `test_vote_history_records_change` | Vote history contains all changes |

## Integration Tests

| Test | Expected Behavior |
|------|------------------|
| `test_conversation_interruption` | Higher arousal agents interrupt more |
| `test_memory_callbacks` | Agents reference past statements |
| `test_emotional_escalation` | Tension increases emotional volatility |

---

# Part 5: Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Deliberation thoughts before speaking | 0% | 80% |
| Emotional content in thoughts | 0% | 50% |
| Turn-taking variance (std dev) | ~0 | >10 |
| Argument effectiveness variance | ~0% | >5% |
| Memory callbacks in dialogue | 0% | 30% |
| Vote history accuracy | 33% (2/6 broken) | 100% |

---

# Appendix: File Changes Summary

## New Files

1. `tsukuyomi/proto/conversation_manager.py` - Turn-taking and interruption logic
2. `tsukuyomi/proto/emotional_expression.py` - Tone modifiers from PAD state

## Modified Files

| File | Changes |
|------|---------|
| `tsukuyomi/agent/AgentBrain.py` | Add deliberation, emotional influence |
| `tsukuyomi/agent/universal_agent.py` | Fix vote history, add deliberation logging |
| `tsukuyomi/agent/immersive_prompt.py` | Inject emotional state, memories, deliberation |
| `tsukuyomi/agent/persuasion.py` | Personality-weighted effectiveness |
| `tsukuyomi/agent/belief_system.py` | Memory retrieval methods |
| `experiments/angry_men/run_full_integration.py` | ConversationManager integration |

---

*End of Specification*
*Created: 2026-02-18*
*Version: 1.0*
