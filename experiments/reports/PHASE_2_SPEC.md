# Tsukuyomi Phase 2: The Cognitive Core
## Technical Specification Document v1.0

**Date:** February 7th, 2026  
**Lead Architect:** Tanit (Subagent)  
**Status:** SPECIFICATION COMPLETE  
**Supersedes:** Phase 1 (Nervous System)

---

## Executive Summary

Phase 1 ("The Angry Man Room") successfully validated Tsukuyomi's core architecture: the 20 TPS tick loop, Dual-Mode Cognition (System 1/2), episodic memory persistence, and gRPC-based orchestration. Agents demonstrated coherent character arcs across 24,000 ticks and authentic social dynamics.

**Phase 2 expands the cognitive architecture to achieve four critical goals:**

1. **Authentic Emotional States** – Agents possess dynamic internal emotional vectors that influence perception and decision-making.
2. **Liberated Belief Systems** – No hardcoded stances. Agents form opinions through evidence accumulation and persuasion.
3. **Living Environments** – Objects become first-class citizens with affordances, enabling physical interaction and discovery.
4. **Embodied Spatial Awareness** – Agents perceive the world through a sensory pipeline, not omniscient data access.

This specification defines the new modules, schema changes, and protocols required to evolve Tsukuyomi from a dialogue simulator into a true cognitive sandbox.

---

## Table of Contents

1. [Lessons from Phase 1](#1-lessons-from-phase-1)
2. [Architecture Overview](#2-architecture-overview)
3. [Module 1: The Perception Layer](#3-module-1-the-perception-layer)
4. [Module 2: The State Manager (Emotional Core)](#4-module-2-the-state-manager-emotional-core)
5. [Module 3: Enhanced Memory Hydration](#5-module-3-enhanced-memory-hydration)
6. [Module 4: Reactive Deliberation Engine](#6-module-4-reactive-deliberation-engine)
7. [Module 5: Object Affordance System](#7-module-5-object-affordance-system)
8. [Module 6: Belief & Stance Dynamics](#8-module-6-belief--stance-dynamics)
9. [Fate Engine Modifications](#9-fate-engine-modifications)
10. [Formal Action Types](#10-formal-action-types)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Risk Analysis](#12-risk-analysis)

---

## 1. Lessons from Phase 1

### 1.1 What Worked

| Component | Observation | Evidence |
|-----------|-------------|----------|
| **Dual-Mode Cognition** | Staggered deliberation (tick offset) created organic pacing | CoT logs show unique timing per agent |
| **Episodic Memory** | Agents recalled dialogue from 5000+ ticks prior | Bank Teller referenced "the old man's timing" |
| **Character Consistency** | Angry Man maintained aggression; Stockbroker remained analytical | All 4 CoT logs show profile-aligned reasoning |
| **Guest Agent Injection** | Tanit's probes successfully influenced native agents | Stockbroker deflected; Bank Teller integrated |

### 1.2 What Was Missing

| Gap | Impact | Phase 2 Solution |
|-----|--------|------------------|
| **Static Stances** | Agents couldn't genuinely change their vote | Belief Dynamics System (§8) |
| **No Object Interaction** | The switchblade was referenced but couldn't be examined | Object Affordance System (§7) |
| **Omniscient Perception** | All agents "saw" everything instantly | Perception Layer (§3) |
| **Flat Emotional Model** | "Angry" was a profile trait, not a dynamic state | State Manager (§4) |
| **Memory = Recent Events** | No distinction between working memory and long-term | Enhanced Hydration (§5) |

### 1.3 Key Observations from Logs

From `/experiments/logs/chain_of_thought/`:

```
The_Angry_Man (Tick 4479): "I can't believe we're still wasting time on how fast an old man can walk."
```
→ **Observation:** Emotional frustration is expressed, but has no *mechanical* effect on his reasoning or perception.

```
The_Bank_Teller (Tick 4886): "Would the old man really have been able to hear the boy shout over all that noise?"
```
→ **Observation:** Emergent deduction occurred, but there's no formal mechanism to track this as "evidence against testimony reliability."

---

## 2. Architecture Overview

### 2.1 Phase 2 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TSUKUYOMI PHASE 2                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────────┐    ┌───────────────────────────┐   │
│  │   WORLD     │───▶│  PERCEPTION     │───▶│       AGENT BRAIN         │   │
│  │   STATE     │    │    LAYER        │    │                           │   │
│  │             │    │  (Per-Agent)    │    │  ┌─────────────────────┐  │   │
│  │ • Actors    │    │                 │    │  │   STATE MANAGER     │  │   │
│  │ • Objects   │    │ • Visibility    │    │  │   (Emotional Core)  │  │   │
│  │ • Zones     │    │ • Audibility    │    │  │                     │  │   │
│  │             │    │ • Attention     │    │  │  Arousal  ────┐     │  │   │
│  └─────────────┘    │ • Salience      │    │  │  Valence  ────┼──┐  │  │   │
│        ▲            └────────┬────────┘    │  │  Dominance ───┘  │  │  │   │
│        │                     │             │  │                  ▼  │  │   │
│        │                     ▼             │  │  [Mood Vector]      │  │   │
│        │            ┌─────────────────┐    │  └─────────┬───────────┘  │   │
│        │            │  PERCEPT QUEUE  │    │            │              │   │
│        │            │  (Salience-Sorted)   │            ▼              │   │
│        │            └────────┬────────┘    │  ┌─────────────────────┐  │   │
│        │                     │             │  │   BELIEF GRAPH      │  │   │
│        │                     ▼             │  │                     │  │   │
│        │            ┌─────────────────┐    │  │  Topic → Stance     │  │   │
│        │            │  MEMORY SYSTEM  │    │  │  Evidence Ledger    │  │   │
│        │            │                 │    │  │  Confidence Scores  │  │   │
│        │            │ ┌─────────────┐ │    │  └─────────┬───────────┘  │   │
│        │            │ │  WORKING    │ │    │            │              │   │
│        │            │ │  MEMORY     │◀┼────┼────────────┘              │   │
│        │            │ │  (7±2 slots)│ │    │                           │   │
│        │            │ └─────────────┘ │    │  ┌─────────────────────┐  │   │
│        │            │       ▲ ▼       │    │  │   DELIBERATOR       │  │   │
│        │            │ ┌─────────────┐ │    │  │   (Reactive Mode)   │  │   │
│        │            │ │  EPISODIC   │ │    │  │                     │  │   │
│        │            │ │  STORE      │ │    │  │  Interrupts ───▶ ⚡ │  │   │
│        │            │ └─────────────┘ │    │  │  Priority Queue     │  │   │
│        │            │       ▲ ▼       │    │  │  Context Switching  │  │   │
│        │            │ ┌─────────────┐ │    │  └─────────┬───────────┘  │   │
│        │            │ │  SEMANTIC   │ │    │            │              │   │
│        │            │ │  GRAPH      │ │    │            ▼              │   │
│        │            │ └─────────────┘ │    │  ┌─────────────────────┐  │   │
│        │            └─────────────────┘    │  │   ACTION RESOLVER   │  │   │
│        │                                   │  │                     │  │   │
│        │                                   │  │  EXAMINE / USE /    │  │   │
│        │                                   │  │  TAKE / DROP / ...  │  │   │
│        │                                   │  └─────────┬───────────┘  │   │
│        │                                   └────────────┼──────────────┘   │
│        │                                                │                  │
│        │            ┌───────────────────────────────────┘                  │
│        │            ▼                                                      │
│  ┌─────┴────────────────┐                                                  │
│  │      FATE ENGINE     │◀──────── Proposal / Resolution Protocol ────────│
│  │   (World Authority)  │                                                  │
│  │                      │                                                  │
│  │  • Physics Contract  │                                                  │
│  │  • Conflict Resolution                                                  │
│  │  • Object State Mgmt │                                                  │
│  │  • Stance Arbitration│  ◀── NEW: Formal belief change events            │
│  └──────────────────────┘                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Summary

1. **World State** is the canonical truth (PostgreSQL).
2. **Perception Layer** filters world state per-agent based on sensory capabilities.
3. **Percepts** enter a salience-sorted queue (attention mechanism).
4. **Memory System** hydrates context from episodic/semantic stores.
5. **State Manager** modulates perception and reasoning via emotional vectors.
6. **Belief Graph** tracks stances with evidence chains.
7. **Deliberator** makes decisions reactively (event-driven) or proactively (periodic).
8. **Actions** are submitted as Proposals to the Fate Engine.
9. **Resolutions** update World State, closing the loop.

---

## 3. Module 1: The Perception Layer

### 3.1 Purpose

Phase 1 gave agents omniscient access to `WorldState`. This is unrealistic and eliminates emergent information asymmetry. Phase 2 introduces a **Perception Layer** that filters world data through sensory constraints.

### 3.2 Sensory Channels

| Channel | Description | Range | Occlusion |
|---------|-------------|-------|-----------|
| **Vision** | See actors/objects | FOV cone (120°) + max distance (20m) | Yes (walls, objects) |
| **Hearing** | Detect speech, loud events | Omnidirectional sphere (15m) | Partial (walls reduce 50%) |
| **Proprioception** | Self-state awareness | Self only | No |
| **Memory Echo** | Last-known positions of tracked entities | Decays over time | N/A |

### 3.3 Schema: `Percept`

```protobuf
message Percept {
  string percept_id = 1;
  int64 tick_observed = 2;
  
  enum Channel {
    VISION = 0;
    HEARING = 1;
    PROPRIOCEPTION = 2;
    MEMORY_ECHO = 3;
  }
  Channel channel = 3;
  
  oneof content {
    ActorPercept actor = 4;
    ObjectPercept object = 5;
    EventPercept event = 6;
    SpeechPercept speech = 7;
  }
  
  float salience = 8;  // 0.0 - 1.0, affects attention priority
  float certainty = 9; // 0.0 - 1.0, degrades with distance/occlusion
}

message ActorPercept {
  string actor_id = 1;
  string name = 2;
  Position approximate_position = 3;  // Blurred by distance
  string visible_action_state = 4;    // "speaking", "idle", "moving"
  string visible_emotional_cue = 5;   // "angry", "calm" (external reading)
}

message ObjectPercept {
  string object_id = 1;
  string apparent_type = 2;           // May differ from true type if obscured
  Position approximate_position = 3;
  repeated string visible_affordances = 4;  // ["examine", "take", "use"]
}

message SpeechPercept {
  string speaker_id = 1;
  string speaker_name = 2;
  string content = 3;
  float loudness = 4;                 // Affects hearing range
  bool is_direct_address = 5;        // "Hey YOU" vs general speech
}

message EventPercept {
  string event_type = 1;             // "door_opened", "item_dropped"
  map<string, string> details = 2;
}
```

### 3.4 Salience Calculation

Salience determines what enters the agent's attention. Higher salience = higher priority in the percept queue.

```
Salience = (BaseWeight × EmotionalRelevance) + (Proximity × 0.3) + (DirectAddress × 0.5) + (Novelty × 0.2)
```

| Factor | Description |
|--------|-------------|
| **BaseWeight** | Event type weight (speech=0.6, movement=0.2, violence=1.0) |
| **EmotionalRelevance** | Cross-reference with agent's current concerns (State Manager) |
| **Proximity** | `1.0 - (distance / max_range)` |
| **DirectAddress** | +0.5 if the agent is mentioned or addressed directly |
| **Novelty** | +0.2 if this entity wasn't seen in the last 100 ticks |

### 3.5 Implementation: `PerceptionPipeline`

```python
# tsukuyomi/brain/PerceptionPipeline.py

class PerceptionPipeline:
    """
    Transforms raw WorldState into agent-specific Percepts.
    """
    
    def __init__(self, agent_id: str, sensory_profile: SensoryProfile):
        self.agent_id = agent_id
        self.profile = sensory_profile
        self.last_known_positions: Dict[str, Position] = {}
        
    def process(self, world_state: WorldState, agent_state: AgentInternalState) -> List[Percept]:
        percepts = []
        my_pos = world_state.actors[self.agent_id].position
        my_facing = world_state.actors[self.agent_id].rotation
        
        # Vision: FOV + Range + Occlusion
        for actor_id, actor in world_state.actors.items():
            if actor_id == self.agent_id:
                continue
            
            if self._in_vision_cone(my_pos, my_facing, actor.position):
                if not self._is_occluded(my_pos, actor.position, world_state):
                    certainty = self._calculate_visual_certainty(my_pos, actor.position)
                    salience = self._calculate_salience(
                        actor, agent_state, my_pos, PerceptChannel.VISION
                    )
                    percepts.append(Percept(
                        channel=PerceptChannel.VISION,
                        actor=ActorPercept(
                            actor_id=actor_id,
                            name=actor.name,
                            approximate_position=self._blur_position(actor.position, certainty),
                            visible_action_state=actor.current_action_state,
                            visible_emotional_cue=self._read_emotional_cue(actor)
                        ),
                        salience=salience,
                        certainty=certainty
                    ))
                    self.last_known_positions[actor_id] = actor.position
        
        # Hearing: Omnidirectional within range
        for speech_event in world_state.pending_speech_events:
            speaker_pos = world_state.actors[speech_event.speaker_id].position
            distance = self._distance(my_pos, speaker_pos)
            effective_range = self.profile.hearing_range * speech_event.loudness
            
            if distance <= effective_range:
                wall_attenuation = self._calculate_wall_attenuation(my_pos, speaker_pos, world_state)
                if wall_attenuation > 0.3:  # Can still hear through walls, but muffled
                    percepts.append(Percept(
                        channel=PerceptChannel.HEARING,
                        speech=SpeechPercept(
                            speaker_id=speech_event.speaker_id,
                            speaker_name=speech_event.speaker_name,
                            content=self._muffle_if_needed(speech_event.content, wall_attenuation),
                            loudness=speech_event.loudness * wall_attenuation,
                            is_direct_address=self.agent_id in speech_event.addressed_to
                        ),
                        salience=self._calculate_speech_salience(speech_event, agent_state),
                        certainty=wall_attenuation
                    ))
        
        # Memory Echoes: Last-known positions for tracked entities
        for entity_id, last_pos in self.last_known_positions.items():
            if entity_id not in [p.actor.actor_id for p in percepts if p.HasField('actor')]:
                decay = self._calculate_echo_decay(entity_id)
                if decay > 0.1:
                    percepts.append(Percept(
                        channel=PerceptChannel.MEMORY_ECHO,
                        actor=ActorPercept(
                            actor_id=entity_id,
                            approximate_position=last_pos
                        ),
                        salience=0.1,
                        certainty=decay
                    ))
        
        # Sort by salience (descending)
        percepts.sort(key=lambda p: p.salience, reverse=True)
        
        return percepts
```

---

## 4. Module 2: The State Manager (Emotional Core)

### 4.1 Purpose

Phase 1 agents had static emotional profiles ("angry", "meek"). Phase 2 introduces **dynamic emotional states** that evolve based on events and influence perception/reasoning.

### 4.2 The PAD Emotional Model

We adopt the **PAD (Pleasure-Arousal-Dominance)** model from affective computing:

| Dimension | Range | Description |
|-----------|-------|-------------|
| **Pleasure (Valence)** | -1.0 to +1.0 | Negative (distress) ↔ Positive (joy) |
| **Arousal** | 0.0 to 1.0 | Low (calm) ↔ High (excited/agitated) |
| **Dominance** | -1.0 to +1.0 | Submissive ↔ Dominant |

### 4.3 Emotional State Schema

```protobuf
message EmotionalState {
  float valence = 1;    // -1.0 to 1.0
  float arousal = 2;    // 0.0 to 1.0
  float dominance = 3;  // -1.0 to 1.0
  
  // Derived mood label for LLM context
  string mood_label = 4;  // "frustrated", "anxious", "calm", "confident"
  
  // Active emotional episodes (temporary spikes)
  repeated EmotionalEpisode active_episodes = 5;
}

message EmotionalEpisode {
  string trigger_event_id = 1;
  string emotion_type = 2;  // "anger", "fear", "surprise", "contempt"
  float intensity = 3;      // 0.0 to 1.0
  int64 onset_tick = 4;
  int64 decay_rate = 5;     // Ticks until intensity halves
}
```

### 4.4 Emotional Dynamics

#### 4.4.1 Baseline Personality (Static)

Each agent has a personality baseline (from profile) that their emotional state regresses towards:

```python
class PersonalityBaseline:
    """Big Five mapped to PAD baseline."""
    
    # Example: "The Angry Man"
    ANGRY_MAN = PersonalityBaseline(
        valence_baseline=-0.3,   # Tends negative
        arousal_baseline=0.7,    # High energy
        dominance_baseline=0.6,  # Wants control
        regression_rate=0.01    # Slow return to baseline
    )
    
    # Example: "The Bank Teller"
    BANK_TELLER = PersonalityBaseline(
        valence_baseline=0.1,    # Slightly positive
        arousal_baseline=0.3,    # Low energy
        dominance_baseline=-0.4, # Submissive
        regression_rate=0.02    # Faster return (meek)
    )
```

#### 4.4.2 Event Impact Functions

Events shift emotional state:

```python
class EmotionalImpactRules:
    """Maps events to PAD deltas."""
    
    IMPACTS = {
        "criticized": {
            "valence_delta": -0.2,
            "arousal_delta": +0.15,
            "dominance_delta": -0.1
        },
        "agreed_with": {
            "valence_delta": +0.15,
            "arousal_delta": +0.05,
            "dominance_delta": +0.1
        },
        "ignored": {
            "valence_delta": -0.1,
            "arousal_delta": +0.1,
            "dominance_delta": -0.15
        },
        "contradicted_by_evidence": {
            "valence_delta": -0.25,
            "arousal_delta": +0.2,
            "dominance_delta": -0.2
        },
        "physical_threat": {
            "valence_delta": -0.5,
            "arousal_delta": +0.8,
            "dominance_delta": -0.3
        }
    }
```

#### 4.4.3 Tick Update Loop

```python
def update_emotional_state(self, tick_state: TickState, percepts: List[Percept]):
    # 1. Process emotional episodes from percepts
    for percept in percepts:
        if impact := self._classify_emotional_impact(percept):
            self.state.valence = clamp(self.state.valence + impact.valence_delta, -1, 1)
            self.state.arousal = clamp(self.state.arousal + impact.arousal_delta, 0, 1)
            self.state.dominance = clamp(self.state.dominance + impact.dominance_delta, -1, 1)
            
            # Create emotional episode for intense events
            if abs(impact.valence_delta) > 0.3 or impact.arousal_delta > 0.5:
                self.state.active_episodes.append(EmotionalEpisode(
                    trigger_event_id=percept.percept_id,
                    emotion_type=impact.emotion_label,
                    intensity=abs(impact.valence_delta),
                    onset_tick=tick_state.tick_number,
                    decay_rate=200  # ~10 seconds at 20 TPS
                ))
    
    # 2. Decay active episodes
    self.state.active_episodes = [
        ep for ep in self.state.active_episodes 
        if ep.intensity > 0.1
    ]
    for ep in self.state.active_episodes:
        ep.intensity *= 0.995  # Per-tick decay
    
    # 3. Regress towards personality baseline
    self.state.valence += (self.baseline.valence - self.state.valence) * self.baseline.regression_rate
    self.state.arousal += (self.baseline.arousal - self.state.arousal) * self.baseline.regression_rate
    self.state.dominance += (self.baseline.dominance - self.state.dominance) * self.baseline.regression_rate
    
    # 4. Derive mood label
    self.state.mood_label = self._derive_mood_label()
```

### 4.5 Emotional Influence on Cognition

| PAD State | Perception Effect | Reasoning Effect |
|-----------|-------------------|------------------|
| High Arousal | Narrowed attention (tunnel vision) | Faster, less thorough deliberation |
| Low Valence | Heightened threat detection | Pessimistic inference |
| High Dominance | Lower salience for dissent | More assertive action choices |
| Low Dominance | Higher salience for social cues | Avoidance-oriented actions |

Implementation in Deliberator:

```python
def _build_llm_context(self, percepts: List[Percept]) -> str:
    emotional_modifier = ""
    if self.state_manager.arousal > 0.7:
        emotional_modifier = "You are feeling highly agitated. Focus on the most pressing issue."
    if self.state_manager.valence < -0.5:
        emotional_modifier += " You feel defensive and frustrated."
    if self.state_manager.dominance > 0.5:
        emotional_modifier += " Assert your position confidently."
    
    return f"""
    INTERNAL STATE:
    Mood: {self.state_manager.mood_label}
    {emotional_modifier}
    
    PERCEPTION:
    {self._format_percepts(percepts)}
    """
```

---

## 5. Module 3: Enhanced Memory Hydration

### 5.1 Current Limitation

Phase 1's `MemoryManager.query_recent(limit=10)` retrieves the last N events chronologically. This is insufficient for:
- **Relevance-based recall** (remembering what matters, not what's recent)
- **Working memory constraints** (cognitive load limits)
- **Emotional memory enhancement** (emotionally significant events are remembered better)

### 5.2 Three-Tier Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKING MEMORY                           │
│                    (7 ± 2 slots)                            │
│                                                             │
│  Active focus items that influence current deliberation.    │
│  Refreshed each tick based on salience + relevance.         │
│  Capacity: 5-9 items (Miller's Law)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Consolidation (decay + importance)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   EPISODIC MEMORY                           │
│                   (Event Store)                             │
│                                                             │
│  Timestamped 5W memories with emotional tags.               │
│  Indexed by: tick, actor, location, emotion_intensity       │
│  Decay: Linear relevance decay (0.001/tick)                 │
│  Emotional Enhancement: High-emotion events decay 5x slower │
└────────────────────────┬────────────────────────────────────┘
                         │ Abstraction (pattern extraction)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SEMANTIC MEMORY                           │
│                   (Knowledge Graph)                         │
│                                                             │
│  Timeless facts and relationships.                          │
│  Subject → Predicate → Object triples                       │
│  Confidence scores updated by evidence accumulation         │
│  No decay (persistent beliefs)                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Working Memory Implementation

```python
class WorkingMemory:
    """
    Cognitively-bounded active context.
    Implements Miller's Law: 7 ± 2 chunks.
    """
    
    MAX_SLOTS = 7
    
    def __init__(self):
        self.slots: List[MemoryChunk] = []
        
    def refresh(self, percepts: List[Percept], episodic: EpisodicMemory, 
                semantic: SemanticMemory, emotional_state: EmotionalState):
        """
        Select the most relevant items for current working memory.
        Called each deliberation cycle.
        """
        candidates = []
        
        # 1. Current percepts (immediate awareness)
        for p in percepts[:3]:  # Top 3 salient percepts
            candidates.append(MemoryChunk(
                source="percept",
                content=p,
                relevance=p.salience
            ))
        
        # 2. Recently activated episodic memories
        recent_relevant = episodic.query_by_relevance(
            current_topics=self._extract_topics(percepts),
            emotional_filter=emotional_state.mood_label,
            limit=5
        )
        for mem in recent_relevant:
            candidates.append(MemoryChunk(
                source="episodic",
                content=mem,
                relevance=mem.relevance_score
            ))
        
        # 3. Semantic facts about current percept subjects
        for p in percepts:
            subject_id = self._extract_subject(p)
            if subject_id:
                facts = semantic.get_relations(subject_id)
                for pred, objs in facts.items():
                    for obj in objs[:2]:  # Limit per relation
                        candidates.append(MemoryChunk(
                            source="semantic",
                            content=f"{subject_id} {pred} {obj}",
                            relevance=0.5
                        ))
        
        # 4. Sort by relevance and take top MAX_SLOTS
        candidates.sort(key=lambda c: c.relevance, reverse=True)
        self.slots = candidates[:self.MAX_SLOTS]
    
    def to_llm_context(self) -> str:
        """Format working memory for LLM prompt."""
        sections = {
            "percept": [],
            "episodic": [],
            "semantic": []
        }
        for chunk in self.slots:
            sections[chunk.source].append(str(chunk.content))
        
        return f"""
WORKING MEMORY ({len(self.slots)} active items):

[IMMEDIATE AWARENESS]
{chr(10).join(sections['percept']) or 'Nothing salient.'}

[RELEVANT MEMORIES]
{chr(10).join(sections['episodic']) or 'No relevant memories activated.'}

[KNOWN FACTS]
{chr(10).join(sections['semantic']) or 'No relevant facts.'}
"""
```

### 5.4 Emotional Memory Enhancement

Memories tagged with high emotional intensity decay slower and are more easily retrieved:

```python
class EpisodicMemory:
    def add_memory(self, memory: Memory5W, emotional_intensity: float):
        memory.relevance_score = 1.0
        memory.emotional_tag = emotional_intensity
        memory.decay_rate = 0.001 if emotional_intensity < 0.5 else 0.0002
        self.store.append(memory)
    
    def tick_decay(self):
        for mem in self.store:
            mem.relevance_score -= mem.decay_rate
        # Prune irrelevant memories
        self.store = [m for m in self.store if m.relevance_score > 0.05]
    
    def query_by_relevance(self, current_topics: List[str], emotional_filter: str, limit: int) -> List[Memory5W]:
        """Retrieve memories by topic match + emotional congruence."""
        scored = []
        for mem in self.store:
            topic_match = len(set(mem.topics) & set(current_topics)) / max(len(current_topics), 1)
            emotional_congruence = 1.0 if mem.emotional_tag > 0.5 else 0.5
            
            score = (mem.relevance_score * 0.4) + (topic_match * 0.4) + (emotional_congruence * 0.2)
            scored.append((score, mem))
        
        scored.sort(reverse=True)
        return [m for _, m in scored[:limit]]
```

---

## 6. Module 4: Reactive Deliberation Engine

### 6.1 Current Limitation

Phase 1's deliberation is **proactive only**: agents think every N ticks based on offset. This creates two problems:
1. Agents don't react to urgent events between deliberation cycles.
2. No mechanism to interrupt ongoing thought for high-priority stimuli.

### 6.2 Reactive Deliberation Model

Phase 2 introduces **event-driven deliberation** with preemption:

```
┌──────────────────────────────────────────────────────────────┐
│                  DELIBERATION SCHEDULER                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    │
│  │  REACTIVE   │     │  PROACTIVE  │     │  BACKGROUND │    │
│  │  TRIGGERS   │     │  SCHEDULE   │     │  PLANNING   │    │
│  │             │     │             │     │             │    │
│  │ • Direct    │     │ • Every 50  │     │ • Long-term │    │
│  │   address   │     │   ticks     │     │   goals     │    │
│  │ • Threat    │     │   (offset)  │     │ • When idle │    │
│  │ • High-     │     │             │     │             │    │
│  │   salience  │     │             │     │             │    │
│  │   event     │     │             │     │             │    │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘    │
│         │                   │                   │            │
│         └─────────┬─────────┴─────────┬─────────┘            │
│                   ▼                   ▼                      │
│           ┌─────────────────────────────────┐                │
│           │      PRIORITY QUEUE             │                │
│           │                                 │                │
│           │  Priority = Urgency × Importance│                │
│           │                                 │                │
│           │  [1] Direct threat (P=1.0)      │                │
│           │  [2] Direct address (P=0.8)     │                │
│           │  [3] Scheduled think (P=0.5)    │                │
│           │  [4] Background (P=0.2)         │                │
│           └──────────────┬──────────────────┘                │
│                          │                                   │
│                          ▼                                   │
│           ┌─────────────────────────────────┐                │
│           │      DELIBERATION EXECUTOR      │                │
│           │                                 │                │
│           │  • Single active task           │                │
│           │  • Preemption via CancellationToken              │
│           │  • Context switching overhead   │                │
│           └─────────────────────────────────┘                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.3 Reactive Trigger Classification

```python
class ReactiveTrigger:
    """Classify percepts for reactive deliberation."""
    
    @staticmethod
    def classify(percept: Percept, emotional_state: EmotionalState) -> Optional[DeliberationRequest]:
        # Priority 1: Direct threats
        if percept.HasField('event') and percept.event.event_type in ['attack', 'physical_threat']:
            return DeliberationRequest(
                priority=1.0,
                reason="threat_response",
                context=percept
            )
        
        # Priority 2: Direct address
        if percept.HasField('speech') and percept.speech.is_direct_address:
            return DeliberationRequest(
                priority=0.8,
                reason="social_response",
                context=percept
            )
        
        # Priority 3: High-salience event (surprising or relevant)
        if percept.salience > 0.8:
            return DeliberationRequest(
                priority=0.7,
                reason="attention_capture",
                context=percept
            )
        
        # Priority 4: Emotional trigger (someone said something that angered/pleased)
        if percept.HasField('speech'):
            sentiment = analyze_sentiment(percept.speech.content)
            if abs(sentiment) > 0.6 and emotional_state.arousal > 0.5:
                return DeliberationRequest(
                    priority=0.6,
                    reason="emotional_response",
                    context=percept
                )
        
        return None
```

### 6.4 Preemption Protocol

```python
class DeliberationExecutor:
    """Execute deliberation tasks with preemption support."""
    
    def __init__(self):
        self.current_task: Optional[asyncio.Task] = None
        self.current_priority: float = 0.0
        self.cancellation_token = CancellationToken()
    
    async def submit(self, request: DeliberationRequest):
        if request.priority > self.current_priority:
            # Preempt current task
            if self.current_task and not self.current_task.done():
                logger.info(f"⚡ PREEMPTING deliberation (old P={self.current_priority}, new P={request.priority})")
                self.cancellation_token.cancel()
                await self.current_task  # Wait for graceful abort
            
            # Start new deliberation
            self.cancellation_token = CancellationToken()
            self.current_priority = request.priority
            self.current_task = asyncio.create_task(
                self._execute(request, self.cancellation_token)
            )
    
    async def _execute(self, request: DeliberationRequest, token: CancellationToken):
        try:
            # Check for cancellation at key points
            if token.is_cancelled():
                return
            
            # Build context
            context = self._build_context(request)
            
            if token.is_cancelled():
                return
            
            # LLM inference
            plan = await LLMService.generate_plan_with_cancel(
                self.profile, context, token
            )
            
            if token.is_cancelled():
                logger.info("Deliberation cancelled before action submission")
                return
            
            # Submit action
            await self.client.submit_proposal(self.actor_id, plan['action'], plan.get('params', {}))
            
        finally:
            self.current_priority = 0.0
```

---

## 7. Module 5: Object Affordance System

### 7.1 Purpose

Phase 1 mentioned "the switchblade" and "evidence" but agents couldn't interact with physical objects meaningfully. Phase 2 introduces a formal **Affordance System** where objects declare what actions they support.

### 7.2 Affordance Schema

```protobuf
message EnvironmentObject {
  string object_id = 1;
  string type = 2;
  string display_name = 3;
  Position position = 4;
  bool interactive = 5;
  
  // NEW: Affordances
  repeated Affordance affordances = 6;
  
  // NEW: Hidden properties (revealed via EXAMINE)
  map<string, string> hidden_properties = 7;
  
  // NEW: Current state
  string state = 8;  // "open", "closed", "damaged", etc.
}

message Affordance {
  string action_type = 1;  // "EXAMINE", "TAKE", "USE", "OPEN", "READ"
  
  // Preconditions (JSON expression)
  string precondition = 2;  // e.g., '{"requires_item": null}' or '{"requires_item": "key_01"}'
  
  // Effect description (for LLM context)
  string effect_description = 3;  // "Reveals the object's details"
  
  // Semantic tags for LLM reasoning
  repeated string semantic_tags = 4;  // ["information", "evidence", "destructive"]
}
```

### 7.3 Example: The Switchblade (12 Angry Men)

```python
switchblade = EnvironmentObject(
    object_id="evidence_knife_01",
    type="weapon",
    display_name="The Murder Weapon (Switchblade)",
    position=Position(x=5.0, y=2.0),  # On the table
    interactive=True,
    state="in_evidence_bag",
    affordances=[
        Affordance(
            action_type="EXAMINE",
            precondition='{}',  # No requirements
            effect_description="Study the knife's unique carved handle pattern",
            semantic_tags=["evidence", "visual_inspection"]
        ),
        Affordance(
            action_type="TAKE",
            precondition='{"requires_role": "foreman"}',
            effect_description="Pick up the knife for demonstration",
            semantic_tags=["possession", "authority"]
        ),
        Affordance(
            action_type="COMPARE",
            precondition='{"requires_item": "second_knife"}',
            effect_description="Compare this knife to another switchblade",
            semantic_tags=["evidence", "logical_argument"]
        )
    ],
    hidden_properties={
        "manufacture_location": "common_store",
        "uniqueness": "not_unique",
        "handle_markings": "standard_carved_pattern"
    }
)
```

### 7.4 Formal Action Types

| Action | Parameters | Preconditions | Effect |
|--------|------------|---------------|--------|
| **EXAMINE** | `target_id` | In perception range | Reveals `hidden_properties` to agent's memory |
| **TAKE** | `target_id` | In reach (≤2m), not owned by another | Moves object to agent's inventory |
| **DROP** | `item_id` | Item in inventory | Creates object at agent's position |
| **USE** | `item_id`, `target_id?` | Item in inventory | Triggers item-specific effect |
| **GIVE** | `item_id`, `recipient_id` | Both agents in range | Transfers item ownership |
| **OPEN** | `target_id` | Object has "openable" affordance | Changes object state to "open" |
| **READ** | `target_id` | Object has "readable" affordance | Reveals text content to memory |

### 7.5 EXAMINE Action Flow

```
Agent                    Fate Engine                 World State
  │                           │                           │
  │  EXAMINE(target="knife")  │                           │
  │──────────────────────────▶│                           │
  │                           │                           │
  │                           │  Validate: In range?      │
  │                           │  Check affordance exists? │
  │                           │                           │
  │                           │  Success: Extract         │
  │                           │  hidden_properties        │
  │                           │◀──────────────────────────│
  │                           │                           │
  │  Resolution: EXAMINE_SUCCESS                          │
  │  + revealed_properties: {                             │
  │      "manufacture_location": "common_store",          │
  │      "uniqueness": "not_unique"                       │
  │    }                                                  │
  │◀──────────────────────────│                           │
  │                           │                           │
  │  (Agent Memory Updated)   │                           │
  │  → Semantic: knife_01 is_unique FALSE                 │
  │  → Episodic: "I examined the knife at tick 5000"      │
```

### 7.6 Object Affordance in LLM Context

When an object is perceived, its affordances are included in the LLM prompt:

```
VISIBLE OBJECTS:
- "The Murder Weapon (Switchblade)" at table
  State: in evidence bag
  Available Actions:
    • EXAMINE - Study the knife's unique carved handle pattern [tags: evidence, visual_inspection]
    • TAKE - Pick up the knife for demonstration [requires: foreman role]
```

---

## 8. Module 6: Belief & Stance Dynamics

### 8.1 The Core Problem

Phase 1 hardcoded stances:
```python
juror_profile = {
    "stance": "guilty",  # STATIC - never changes
}
```

This prevented genuine deliberation. The Bank Teller could never actually change his vote, only express doubt.

### 8.2 The Belief Graph

Phase 2 introduces a **Belief Graph** where stances emerge from accumulated evidence:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BELIEF GRAPH                                 │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TOPIC: "defendant_guilt"                                    │   │
│  │                                                              │   │
│  │  Current Stance: GUILTY (confidence: 0.72)                   │   │
│  │                                                              │   │
│  │  Evidence FOR (guilt):                                       │   │
│  │    [+0.8] eyewitness_woman: "Saw the stabbing"              │   │
│  │    [+0.6] motive: "Boy threatened father"                   │   │
│  │    [+0.4] weapon_match: "Same type of knife"                │   │
│  │                                                              │   │
│  │  Evidence AGAINST (reasonable doubt):                        │   │
│  │    [-0.3] timing_inconsistency: "Old man's 15 seconds"      │   │
│  │    [-0.2] train_noise: "Could he hear over the train?"      │   │
│  │    [-0.1] glasses_theory: "Woman may not wear glasses"      │   │
│  │                                                              │   │
│  │  Net Score: +1.8 - 0.6 = +1.2 → GUILTY (72% confidence)     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TOPIC: "old_man_reliability"                                │   │
│  │                                                              │   │
│  │  Current Stance: UNRELIABLE (confidence: 0.45)               │   │
│  │                                                              │   │
│  │  Evidence FOR (reliable):                                    │   │
│  │    [+0.4] official_testimony: "Testified under oath"        │   │
│  │                                                              │   │
│  │  Evidence AGAINST (unreliable):                              │   │
│  │    [-0.5] timing_proof: "Can't walk 40ft in 15 sec"        │   │
│  │    [-0.2] hearing_doubt: "Train noise"                      │   │
│  │                                                              │   │
│  │  Net Score: +0.4 - 0.7 = -0.3 → UNRELIABLE (45% confidence) │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Belief Schema

```protobuf
message BeliefGraph {
  repeated BeliefTopic topics = 1;
}

message BeliefTopic {
  string topic_id = 1;
  string topic_name = 2;
  
  StancePosition current_stance = 3;
  float confidence = 4;  // 0.0 to 1.0
  
  repeated EvidenceItem evidence_for = 5;
  repeated EvidenceItem evidence_against = 6;
  
  // Stance history for narrative
  repeated StanceChange history = 7;
}

message EvidenceItem {
  string evidence_id = 1;
  string description = 2;
  float weight = 3;           // Impact on stance (0.0 to 1.0)
  string source_type = 4;     // "testimony", "observation", "reasoning", "social_pressure"
  int64 acquired_tick = 5;
  string source_agent_id = 6; // Who told me / where I observed
}

message StanceChange {
  int64 tick = 1;
  StancePosition old_stance = 2;
  StancePosition new_stance = 3;
  string trigger_evidence_id = 4;
  string internal_reasoning = 5;
}

enum StancePosition {
  STRONGLY_FOR = 0;
  LEANING_FOR = 1;
  NEUTRAL = 2;
  LEANING_AGAINST = 3;
  STRONGLY_AGAINST = 4;
}
```

### 8.4 Stance Calculation

```python
class BeliefManager:
    """Manages dynamic belief/stance for an agent."""
    
    def calculate_stance(self, topic_id: str) -> Tuple[StancePosition, float]:
        topic = self.topics[topic_id]
        
        # Calculate weighted scores
        for_score = sum(e.weight for e in topic.evidence_for)
        against_score = sum(e.weight for e in topic.evidence_against)
        
        # Apply personality modifiers
        for_score *= self._get_personality_bias(topic_id, "for")
        against_score *= self._get_personality_bias(topic_id, "against")
        
        # Net score
        net = for_score - against_score
        
        # Map to stance
        if net > 1.5:
            stance = StancePosition.STRONGLY_FOR
        elif net > 0.5:
            stance = StancePosition.LEANING_FOR
        elif net > -0.5:
            stance = StancePosition.NEUTRAL
        elif net > -1.5:
            stance = StancePosition.LEANING_AGAINST
        else:
            stance = StancePosition.STRONGLY_AGAINST
        
        # Confidence based on evidence volume and consistency
        total_evidence = len(topic.evidence_for) + len(topic.evidence_against)
        consistency = abs(net) / max(for_score + against_score, 0.1)
        confidence = min(0.3 + (total_evidence * 0.1) + (consistency * 0.3), 1.0)
        
        return stance, confidence
    
    def add_evidence(self, topic_id: str, evidence: EvidenceItem, position: str):
        """Add evidence and potentially trigger stance shift."""
        topic = self.topics[topic_id]
        old_stance, old_conf = self.calculate_stance(topic_id)
        
        if position == "for":
            topic.evidence_for.append(evidence)
        else:
            topic.evidence_against.append(evidence)
        
        new_stance, new_conf = self.calculate_stance(topic_id)
        
        # Record stance change if significant
        if old_stance != new_stance:
            topic.history.append(StanceChange(
                tick=self.current_tick,
                old_stance=old_stance,
                new_stance=new_stance,
                trigger_evidence_id=evidence.evidence_id,
                internal_reasoning=self._generate_shift_reasoning(topic_id, old_stance, new_stance)
            ))
            
            # Emit event for Fate Engine
            return StanceShiftEvent(
                agent_id=self.agent_id,
                topic_id=topic_id,
                old_stance=old_stance,
                new_stance=new_stance
            )
        
        return None
```

### 8.5 Personality Bias (Resistance to Change)

Different personalities resist or embrace evidence differently:

```python
class PersonalityBias:
    """Personality-based evidence weighting."""
    
    PROFILES = {
        "the_angry_man": {
            "confirmation_bias": 1.5,      # Weights confirming evidence 50% higher
            "disconfirmation_resistance": 0.5,  # Weights disconfirming evidence 50% lower
            "social_pressure_immunity": 0.8,    # Resistant to "everyone thinks..."
        },
        "the_bank_teller": {
            "confirmation_bias": 1.0,      # Neutral
            "disconfirmation_resistance": 1.0,  # Open to counter-evidence
            "social_pressure_immunity": 0.3,    # Highly influenced by group
        },
        "the_stockbroker": {
            "confirmation_bias": 1.2,
            "disconfirmation_resistance": 0.8,
            "social_pressure_immunity": 0.9,    # Facts over feelings
        }
    }
```

### 8.6 LLM Integration for Stance Shifting

When the LLM deliberates, it receives the current belief state and can propose evidence additions:

```python
BELIEF_PROMPT_SECTION = """
YOUR CURRENT BELIEFS:
Topic: Defendant's Guilt
  Stance: Leaning Guilty (68% confident)
  Key Evidence FOR: Eyewitness saw stabbing, boy owned same knife type
  Key Evidence AGAINST: Old man's timing seems impossible, train noise

Based on the discussion, you may:
1. Add new evidence to your belief graph via the REFLECT action
2. Maintain your current position
3. Express doubt via EMOTE without changing stance

If you change your mind, use:
{
  "action": "REFLECT",
  "params": {
    "topic": "defendant_guilt",
    "new_evidence": {
      "description": "The knife isn't unique - there's a store nearby",
      "position": "against",
      "weight": 0.4,
      "source": "logical_reasoning"
    }
  }
}
"""
```

### 8.7 Formal STANCE_SHIFT Event

When an agent's stance changes, the Fate Engine broadcasts this as a world event:

```protobuf
message StanceShiftEvent {
  string agent_id = 1;
  string agent_name = 2;
  string topic_id = 3;
  StancePosition old_stance = 4;
  StancePosition new_stance = 5;
  string visible_expression = 6;  // What other agents perceive: "looks troubled", "nods slowly"
}
```

This event becomes visible to other agents through the Perception Layer, potentially triggering their own deliberation (social contagion).

---

## 9. Fate Engine Modifications

### 9.1 New Resolution Types

```python
class FateEngine:
    """Phase 2 additions to the Fate Engine."""
    
    async def _resolve_proposal(self, proposal: Proposal) -> Resolution:
        match proposal.action_type:
            # Existing
            case "MOVE": return await self._resolve_move(proposal)
            case "EMOTE": return await self._resolve_emote(proposal)
            case "IDLE": return await self._resolve_idle(proposal)
            case "COLLECT": return await ActionResolver.resolve_collect(...)
            case "USE": return await ActionResolver.resolve_use(...)
            
            # NEW Phase 2 Actions
            case "EXAMINE": return await self._resolve_examine(proposal)
            case "TAKE": return await self._resolve_take(proposal)
            case "DROP": return await self._resolve_drop(proposal)
            case "GIVE": return await self._resolve_give(proposal)
            case "OPEN": return await self._resolve_open(proposal)
            case "READ": return await self._resolve_read(proposal)
            case "REFLECT": return await self._resolve_reflect(proposal)
    
    async def _resolve_examine(self, proposal: Proposal) -> Resolution:
        """
        Reveal hidden properties of an object to the examining agent.
        """
        actor = self.world_state.actors[proposal.actor_id]
        target_id = proposal.parameters["target_id"]
        
        if target_id not in self.world_state.objects:
            return Resolution(success=False, reason="Object not found")
        
        obj = self.world_state.objects[target_id]
        
        # Check affordance
        examine_affordance = next(
            (a for a in obj.affordances if a.action_type == "EXAMINE"), 
            None
        )
        if not examine_affordance:
            return Resolution(success=False, reason="Cannot examine this object")
        
        # Check preconditions
        if not self._check_preconditions(examine_affordance.precondition, actor):
            return Resolution(success=False, reason="Preconditions not met")
        
        # Check range (vision range)
        distance = self._calculate_distance(actor.position, obj.position)
        if distance > 10.0:  # Vision range for detailed examination
            return Resolution(success=False, reason="Too far to examine in detail")
        
        # Success: Return hidden properties
        return Resolution(
            success=True,
            outcome={
                "action": "examine",
                "object_id": target_id,
                "revealed_properties": dict(obj.hidden_properties),
                "affordance_used": "EXAMINE"
            }
        )
    
    async def _resolve_reflect(self, proposal: Proposal) -> Resolution:
        """
        Internal action: Agent adds evidence to their belief graph.
        This is NOT validated by Fate Engine (internal cognition).
        """
        return Resolution(
            success=True,
            outcome={
                "action": "reflect",
                "topic": proposal.parameters["topic"],
                "evidence": proposal.parameters["new_evidence"],
                "internal": True  # Flag: Don't broadcast to other agents
            }
        )
```

### 9.2 Speech Event Pipeline

Phase 2 formalizes speech as a first-class event with metadata:

```python
async def _resolve_emote(self, proposal: Proposal) -> Resolution:
    if proposal.parameters.get("type") == "speak":
        actor = self.world_state.actors[proposal.actor_id]
        message = proposal.parameters["message"]
        
        # Create speech event for perception pipeline
        speech_event = SpeechEvent(
            event_id=str(uuid.uuid4()),
            speaker_id=proposal.actor_id,
            speaker_name=actor.name,
            content=message,
            loudness=proposal.parameters.get("loudness", 0.7),
            addressed_to=self._parse_addressed_entities(message),
            emotion_tone=self._classify_tone(message),
            tick=self.current_tick
        )
        
        self.pending_speech_events.append(speech_event)
        
        return Resolution(
            success=True,
            outcome={
                "action": "speak",
                "message": message,
                "speech_event_id": speech_event.event_id
            }
        )
```

### 9.3 Stance Arbitration

When an agent formally changes stance, the Fate Engine records it:

```python
async def record_stance_shift(self, event: StanceShiftEvent):
    """Record stance change in world history for other agents to perceive."""
    
    # Add to tick history
    self.tick_history.append(TickEvent(
        tick=self.current_tick,
        event_type="stance_shift",
        agent_id=event.agent_id,
        details={
            "topic": event.topic_id,
            "old_stance": event.old_stance.name,
            "new_stance": event.new_stance.name,
            "visible_expression": event.visible_expression
        }
    ))
    
    # Broadcast to Drama Director
    if self.drama_director:
        await self.drama_director.on_stance_shift(event)
```

---

## 10. Formal Action Types

### 10.1 Complete Action Manifest (Phase 2)

| Action | Category | Parameters | Requires | Effect |
|--------|----------|------------|----------|--------|
| **MOVE** | Navigation | `destination: Position` | Valid path | Agent relocates |
| **IDLE** | State | `duration: int` | None | Agent waits |
| **EMOTE** | Social | `type: str, message?: str, emotion?: str` | None | Expression/Speech |
| **EXAMINE** | Object | `target_id: str` | In vision range, affordance exists | Reveals hidden_properties |
| **TAKE** | Object | `target_id: str` | In reach, not owned, affordance exists | Item → inventory |
| **DROP** | Object | `item_id: str` | Item in inventory | Creates object at position |
| **USE** | Object | `item_id: str, target_id?: str` | Item in inventory, affordance exists | Item-specific effect |
| **GIVE** | Social | `item_id: str, recipient_id: str` | Both in range, item owned | Transfer ownership |
| **OPEN** | Object | `target_id: str` | Affordance exists, preconditions met | State → "open" |
| **READ** | Object | `target_id: str` | Affordance exists, in range | Text → memory |
| **REFLECT** | Internal | `topic: str, evidence: EvidenceItem` | None (internal) | Updates belief graph |
| **VOTE** | Social | `topic: str, position: str` | Context-specific | Formal stance declaration |

### 10.2 LLM Action Schema (JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentAction",
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "action": { "const": "MOVE" },
        "params": {
          "type": "object",
          "properties": {
            "destination": { "type": "string" }
          },
          "required": ["destination"]
        }
      }
    },
    {
      "type": "object",
      "properties": {
        "action": { "const": "EMOTE" },
        "params": {
          "type": "object",
          "properties": {
            "type": { "enum": ["speak", "gesture", "expression"] },
            "message": { "type": "string" },
            "emotion": { "type": "string" },
            "addressed_to": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["type"]
        }
      }
    },
    {
      "type": "object",
      "properties": {
        "action": { "const": "EXAMINE" },
        "params": {
          "type": "object",
          "properties": {
            "target_id": { "type": "string" }
          },
          "required": ["target_id"]
        }
      }
    },
    {
      "type": "object",
      "properties": {
        "action": { "const": "REFLECT" },
        "params": {
          "type": "object",
          "properties": {
            "topic": { "type": "string" },
            "new_evidence": {
              "type": "object",
              "properties": {
                "description": { "type": "string" },
                "position": { "enum": ["for", "against"] },
                "weight": { "type": "number", "minimum": 0, "maximum": 1 },
                "source": { "type": "string" }
              },
              "required": ["description", "position", "weight"]
            }
          },
          "required": ["topic", "new_evidence"]
        }
      }
    }
  ]
}
```

---

## 11. Implementation Roadmap

### Phase 2.1: Perception Foundation (Week 1-2)

| Task | Description | Files |
|------|-------------|-------|
| 2.1.1 | Implement `PerceptionPipeline` class | `brain/PerceptionPipeline.py` |
| 2.1.2 | Add `Percept` protobuf definitions | `proto/perception.proto` |
| 2.1.3 | Integrate FOV calculation (vision cone) | `PerceptionPipeline._in_vision_cone()` |
| 2.1.4 | Implement salience scoring | `PerceptionPipeline._calculate_salience()` |
| 2.1.5 | Add unit tests for perception | `tests/test_perception.py` |
| **Milestone** | Agents receive filtered percepts instead of raw WorldState | |

### Phase 2.2: Emotional Core (Week 2-3)

| Task | Description | Files |
|------|-------------|-------|
| 2.2.1 | Implement `StateManager` with PAD model | `brain/StateManager.py` |
| 2.2.2 | Define personality baselines for test agents | `brain/PersonalityProfiles.py` |
| 2.2.3 | Implement emotional impact rules | `StateManager.EmotionalImpactRules` |
| 2.2.4 | Add emotional decay and regression | `StateManager.update()` |
| 2.2.5 | Integrate emotional state into LLM prompt | `AgentBrain._build_llm_context()` |
| **Milestone** | Agents show dynamic emotional responses to events | |

### Phase 2.3: Memory Hydration (Week 3-4)

| Task | Description | Files |
|------|-------------|-------|
| 2.3.1 | Implement `WorkingMemory` with slot limits | `brain/WorkingMemory.py` |
| 2.3.2 | Refactor `EpisodicMemory` with decay + emotional tags | `brain/MemoryManager.py` |
| 2.3.3 | Implement relevance-based memory retrieval | `EpisodicMemory.query_by_relevance()` |
| 2.3.4 | Add emotional memory enhancement | `EpisodicMemory.add_memory()` |
| 2.3.5 | Integrate working memory into deliberation | `AgentBrain._deliberate()` |
| **Milestone** | Agents recall relevant (not just recent) memories | |

### Phase 2.4: Object Affordances (Week 4-5)

| Task | Description | Files |
|------|-------------|-------|
| 2.4.1 | Extend `EnvironmentObject` protobuf | `proto/common.proto` |
| 2.4.2 | Implement `EXAMINE` action resolution | `FateEngine._resolve_examine()` |
| 2.4.3 | Implement `TAKE`, `DROP`, `GIVE` actions | `FateEngine._resolve_*()` |
| 2.4.4 | Add affordance display in perception | `PerceptionPipeline._format_object()` |
| 2.4.5 | Create test scenario with interactive evidence | `experiments/scenarios/evidence_room.py` |
| **Milestone** | Agents can examine objects and gain knowledge | |

### Phase 2.5: Belief Dynamics (Week 5-6)

| Task | Description | Files |
|------|-------------|-------|
| 2.5.1 | Implement `BeliefManager` class | `brain/BeliefManager.py` |
| 2.5.2 | Define `BeliefTopic` schema | `proto/belief.proto` |
| 2.5.3 | Implement stance calculation from evidence | `BeliefManager.calculate_stance()` |
| 2.5.4 | Implement `REFLECT` action | `FateEngine._resolve_reflect()` |
| 2.5.5 | Add personality bias weighting | `BeliefManager._apply_personality_bias()` |
| 2.5.6 | Integrate belief state into LLM prompt | `AgentBrain._build_llm_context()` |
| **Milestone** | Agents can change their stance based on evidence | |

### Phase 2.6: Reactive Deliberation (Week 6-7)

| Task | Description | Files |
|------|-------------|-------|
| 2.6.1 | Implement `DeliberationScheduler` | `brain/DeliberationScheduler.py` |
| 2.6.2 | Add reactive trigger classification | `ReactiveTrigger.classify()` |
| 2.6.3 | Implement preemption with CancellationToken | `DeliberationExecutor.submit()` |
| 2.6.4 | Integrate reactive + proactive scheduling | `AgentBrain._process_tick()` |
| 2.6.5 | Add interrupt tests | `tests/test_deliberation.py` |
| **Milestone** | Agents respond to urgent events immediately | |

### Phase 2.7: Integration & Testing (Week 7-8)

| Task | Description | Files |
|------|-------------|-------|
| 2.7.1 | Full integration test: "12 Angry Men v2" | `experiments/scenarios/angry_man_v2.py` |
| 2.7.2 | Verify stance shifting in simulation | Analysis report |
| 2.7.3 | Performance profiling (20 TPS with new modules) | `tests/perf_phase2.py` |
| 2.7.4 | Documentation update | `ARCHITECTURE.md` v2 |
| **Milestone** | Phase 2 complete; ready for Phase 3 (Social & Scale) | |

---

## 12. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM Context Overflow** | High | Medium | Working memory limits; aggressive summarization |
| **Perception Overhead** | Medium | Medium | LOD for perception (only calculate for Tier 0/1 agents) |
| **Emotional State Instability** | Medium | Low | Regression to baseline; cap extreme values |
| **Belief Graph Complexity** | Low | High | Limit topics per agent; prune low-confidence evidence |
| **Preemption Race Conditions** | Medium | High | Mutex on deliberation state; graceful cancellation |
| **Test Scenario Complexity** | High | Medium | Start with simplified "12 Angry Men" (4 jurors, 1 topic) |

---

## Appendix A: Updated Agent Profile Schema

```python
@dataclass
class AgentProfile:
    """Phase 2 Agent Profile."""
    
    # Identity
    name: str
    actor_id: str
    backstory: str
    
    # Personality (Big Five → PAD baseline)
    personality: PersonalityBaseline
    
    # Sensory capabilities
    sensory_profile: SensoryProfile
    
    # Initial beliefs (can be empty for "blank slate")
    initial_beliefs: Dict[str, BeliefTopic]
    
    # Cognitive settings
    deliberation_offset: int  # Tick offset for proactive deliberation
    reactive_threshold: float  # Salience threshold for reactive deliberation
    
    # NO MORE STATIC STANCE
    # stance: str  ← REMOVED

# Example: Phase 2 Bank Teller
BANK_TELLER_V2 = AgentProfile(
    name="The Bank Teller",
    actor_id="juror-2",
    backstory="Works as a bank teller for 12 years. Observant but avoids confrontation.",
    personality=PersonalityBaseline(
        valence_baseline=0.1,
        arousal_baseline=0.3,
        dominance_baseline=-0.4,
        regression_rate=0.02,
        confirmation_bias=1.0,
        disconfirmation_resistance=1.0,
        social_pressure_immunity=0.3
    ),
    sensory_profile=SensoryProfile(
        vision_range=20.0,
        vision_fov=120,
        hearing_range=15.0
    ),
    initial_beliefs={
        "defendant_guilt": BeliefTopic(
            topic_id="defendant_guilt",
            topic_name="Is the defendant guilty?",
            evidence_for=[
                EvidenceItem(description="Eyewitness saw stabbing", weight=0.8, source_type="testimony"),
                EvidenceItem(description="Boy owned similar knife", weight=0.4, source_type="physical_evidence")
            ],
            evidence_against=[]  # Will discover through simulation
        )
    },
    deliberation_offset=14,
    reactive_threshold=0.7
)
```

---

## Appendix B: LLM Prompt Template (Phase 2)

```
=== TSUKUYOMI COGNITIVE FRAME ===

IDENTITY:
You are {agent.name}.
{agent.backstory}

INTERNAL STATE:
Mood: {state_manager.mood_label}
Arousal: {state_manager.arousal:.2f} | Valence: {state_manager.valence:.2f}
{emotional_modifier}

CURRENT BELIEFS:
{belief_manager.format_beliefs()}

WORKING MEMORY ({working_memory.slot_count} active items):
{working_memory.to_llm_context()}

AVAILABLE ACTIONS:
- MOVE(destination) - Walk to a location
- IDLE(duration) - Wait and observe
- EMOTE(type="speak", message="...", addressed_to=[]) - Speak to others
- EXAMINE(target_id) - Study an object in detail
- TAKE(target_id) - Pick up an object
- REFLECT(topic, new_evidence) - Update your beliefs based on new reasoning

VISIBLE OBJECTS:
{perception.format_objects_with_affordances()}

INSTRUCTIONS:
Based on your identity, emotional state, beliefs, and current perceptions, decide your next action.
You may change your beliefs if you find compelling evidence.
You should NOT simply agree with others unless you find their arguments convincing.
Your response must be valid JSON matching the action schema.

RESPONSE FORMAT:
{
  "thought": "your internal reasoning (Chain of Thought)",
  "action": "ACTION_TYPE",
  "params": {...}
}
```

---

## Conclusion

Phase 2 transforms Tsukuyomi from a dialogue simulator into a cognitive sandbox where:

1. **Perception creates information asymmetry** – Agents don't know everything; they discover.
2. **Emotions drive behavior** – The Angry Man isn't just "angry by script"; his frustration builds and influences his tunnel vision.
3. **Beliefs are earned, not assigned** – The Bank Teller can genuinely change his vote when evidence accumulates.
4. **Objects are actors** – The switchblade isn't a prop; it's a source of discoverable truth.
5. **Attention is bounded** – Working memory limits force agents to prioritize, creating realistic cognitive load.

The "12 Angry Men v2" experiment will be the validation milestone: we expect to see at least one juror change their vote based on accumulated evidence, demonstrating authentic deliberation rather than scripted performance.

---

**Specification Finalized.**  
*Tsukuyomi Phase 2: The Cognitive Core*  
*Lead Architect: Tanit*
