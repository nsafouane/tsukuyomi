# V3 Architecture Documentation

## Overview

The V3 architecture introduces five major improvements to the Tsukuyomi agent system, addressing key limitations identified during the 30-minute Oracle experiment:

1. **Belief Plasticity** - Agents no longer get stuck in high-confidence states
2. **LLM Response Homogenization** - Diverse, personality-consistent dialogue
3. **Emotional State Integration** - PAD model affects behavior and spreads through contagion
4. **Conversation Memory** - Personal narrative continuity and consistency
5. **Behavioral Diversity** - Distinct interaction patterns (leaders, followers, initiators)

## Quick Start

```python
from tsukuyomi.agent import (
    enhance_agent,
    enhance_prompt,
    EmotionalState,
    ResponseHistory,
    ConversationMemory,
    BehavioralTraits,
    CommunicationStyle
)

# Enhance an agent with V3 components
profile = {
    "personality": {
        "big_five": {
            "neuroticism": 0.6,
            "extraversion": 0.3,
            "agreeableness": 0.7,
            "conscientiousness": 0.5,
            "openness": 0.4
        }
    },
    "role": "juror"
}

components = enhance_agent(None, profile)

# Access components
emotional_state = components["emotional_state"]
response_history = components["response_history"]
conversation_memory = components["conversation_memory"]
behavioral_traits = components["behavioral_traits"]
communication_style = components["communication_style"]
```

## Components

### 1. Emotional State (`emotional_state.py`)

PAD (Pleasure-Arousal-Dominance) emotional model.

```python
from tsukuyomi.agent import EmotionalState, EmotionalTone

state = EmotionalState(pleasure=-0.5, arousal=0.5)
print(state.tone)  # EmotionalTone.ANGRY

# Update based on events
state.update("contradicted", intensity=0.5, tick=100)

# Apply to prompt
enhanced_prompt = state.apply_to_prompt(base_prompt)
```

**Features:**
- 12 emotional tones (ANGRY, ANXIOUS, EXCITED, CALM, etc.)
- 18 event types with PAD effects
- Emotional contagion between nearby agents
- Automatic decay towards baseline

### 2. Response History (`conversation.py`)

Tracks recent responses to prevent repetition.

```python
from tsukuyomi.agent import ResponseHistory, ResponseRecord

history = ResponseHistory(max_history=10)

# Record responses
history.add(ResponseRecord(
    tick=100,
    content="I think the defendant is guilty",
    prompt_type="vote",
    tone="certain",
    word_count=7
))

# Check for repetition
if history.is_too_similar(new_content, threshold=0.6):
    # Generate different response
    pass

# Get variety warning for prompt
warning = history.get_variety_warning()
```

**Features:**
- Rolling window of recent responses
- Phrase frequency tracking
- Similarity scoring
- Automatic variety warnings

### 3. Communication Style (`personality.py`)

Defines how an agent speaks.

```python
from tsukuyomi.agent import CommunicationStyle, inject_style_into_prompt

style = CommunicationStyle(
    vocabulary_level="simple",
    formality=0.8,
    verbosity=0.3,
    preferred_words=["concerning", "however"],
    avoided_words=["maybe", "perhaps"]
)

# Inject into prompt
enhanced = inject_style_into_prompt(base_prompt, style, response_history)
```

**Features:**
- Vocabulary level control
- Formality and verbosity settings
- Preferred/avoided word lists
- Style presets (formal, casual, analytical, etc.)

### 4. Conversation Memory (`memory.py`)

Personal narrative tracking.

```python
from tsukuyomi.agent import ConversationMemory, Utterance

memory = ConversationMemory(max_utterances=50)

# Record utterance
memory.add(Utterance(
    tick=100,
    content="I vote guilty based on the evidence",
    position="guilty"
))

# Check consistency
result = memory.consistency_check("I think not guilty")
if not result["is_consistent"]:
    print(f"Conflict: {result['conflicting_topics']}")
    print(f"Acknowledge: {result['suggested_acknowledgment']}")

# Get narrative summary
narrative = memory.get_personal_narrative()
```

**Features:**
- Topic tracking
- Position consistency checking
- Relationship tracking
- Personal narrative generation

### 5. Behavioral Traits (`behavior.py`)

Decision-making for social behavior.

```python
from tsukuyomi.agent import BehavioralTraits, BehavioralDecider

traits = BehavioralTraits(
    introversion=0.3,
    dominance=0.8,
    speak_probability=0.5
)

# Check if should speak
if traits.should_speak(tick=100, addressing_me=True):
    # Generate response
    pass

# Decide action
decider = BehavioralDecider(traits)
decision = decider.decide_action({
    "tick": 100,
    "addressing_me": False,
    "topic_age": 30
})
# Returns: {"action": "silent"} or {"action": "respond"} or {"action": "new_topic"}
```

**Features:**
- Introversion/extroversion
- Dominance (leadership style)
- Topic initiation probability
- Interrupt probability
- Presets (leader, follower, skeptic, listener, etc.)

### 6. Belief Plasticity (`belief_system.py`)

Enhanced belief dynamics.

```python
from tsukuyomi.agent import BeliefSystem, DecayConfig

system = BeliefSystem(agent_id="test")

# Configure decay
config = DecayConfig(
    base_rate=0.005,
    perturbation_chance=0.02
)

# Apply exponential decay
changes = system.decay_beliefs(tick=1000, config=config)

# Perturb saturated beliefs
perturbed = system.perturb_saturated_beliefs(tick=1000, config=config)

# Detect contradictions
contradictions = system.detect_contradictions()
```

**Features:**
- Exponential decay (older beliefs decay faster)
- Random perturbation for saturated beliefs
- Contradiction detection
- Context-dependent plasticity

## Integration

### Using V3AgentMixin

```python
from tsukuyomi.agent import V3AgentMixin

class EnhancedAgent(V3AgentMixin):
    def __init__(self, agent_id, profile):
        self.agent_id = agent_id
        self.init_v3(profile)  # Initialize all V3 components
    
    async def generate_response(self, prompt, system_prompt, tick):
        # Enhance prompts with V3 context
        prompt, system_prompt = self.enhance_prompt_v3(prompt, system_prompt)
        
        # Generate with LLM
        response = await self.llm.generate(prompt, system_prompt)
        
        # Record in V3 systems
        self.record_response_v3(tick, response, "deliberation")
        
        return response
```

### Using enhance_prompt

```python
from tsukuyomi.agent import enhance_prompt

# Before sending to LLM
enhanced_prompt, enhanced_system = enhance_prompt(
    base_prompt="What do you think?",
    base_system_prompt="You are a juror.",
    emotional_state=agent.emotional_state,
    response_history=agent.response_history,
    communication_style=agent.communication_style,
    conversation_memory=agent.conversation_memory
)

response = await llm.generate(enhanced_prompt, enhanced_system)
```

## Testing

Run all V3 tests:

```bash
cd tsukuyomi
python3 -m pytest tsukuyomi/agent/tests/test_belief_plasticity.py \
                  tsukuyomi/agent/tests/test_emotional_integration.py \
                  tsukuyomi/agent/tests/test_response_variety.py \
                  tsukuyomi/agent/tests/test_conversation_memory.py \
                  tsukuyomi/agent/tests/test_behavioral_diversity.py \
                  tsukuyomi/agent/tests/test_v3_integration.py -v
```

Expected: 87 tests passing

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `emotional_state.py` | PAD emotional model | ~420 |
| `conversation.py` | Response tracking | ~250 |
| `personality.py` | Communication style | ~250 |
| `memory.py` | Conversation memory | ~280 |
| `behavior.py` | Behavioral traits | ~350 |
| `v3_integration.py` | Integration helpers | ~320 |
| `test_*.py` | Test files (6) | ~800 |

## Files Modified

| File | Changes |
|------|---------|
| `belief_system.py` | Added DecayConfig, exponential decay, perturbation, plasticity |
| `__init__.py` | Added V3 exports |

---

*Created: February 19, 2026*
*Status: Complete - 87 tests passing*
