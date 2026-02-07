# Tsukuyomi Phase 2: The Cognitive Core
## Technical Specification — Opus 4.6
### Definitive Implementation Blueprint

**Date:** 2026-02-08
**Lead Architect:** Opus 4 (Claude), commissioned by Tanit & Safouane
**Supersedes:** `PHASE_2_SPEC.md` v1.0 (Tanit, 2026-02-07)
**Status:** SPECIFICATION COMPLETE — READY FOR IMPLEMENTATION
**Classification:** Internal Architecture Document

---

## Preface: Why Opus 4.6?

The original Phase 2 spec (v1.0, 1680 lines) was a visionary document. But after deep analysis of the actual codebase — every line of `fate_engine.py`, `AgentBrain.py`, `MemoryManager.py`, `LLMService.py`, `PerceptionPipeline.py`, the protobuf schemas, the experiment logs — this revision addresses three critical gaps:

1. **The Spec-Code Gap.** v1.0 specified 6 modules. Only PerceptionPipeline was implemented, and it contains a known bug (`math.random()` → should be `random.random()` in `_blur_position()`). The other 5 modules exist only on paper.

2. **Integration Blindness.** v1.0 designed modules in isolation. This revision specifies exact integration points — which line of `AgentBrain.py` changes, which protobuf message gets new fields, which Fate Engine method needs extension.

3. **The Deliberation Bottleneck.** The current `LLMService.py` calls Gemini CLI with a global semaphore of 1 and 2.5s cooldown. Phase 2's reactive deliberation model must work *within* these constraints, not ignore them.

This document is the single source of truth for Phase 2 implementation.

---

## Table of Contents

1. [Lessons from Phase 1: The Angry Man Room](#1-lessons-from-phase-1-the-angry-man-room)
2. [Phase 2 Architecture Overview](#2-phase-2-architecture-overview)
3. [Module 1: StateManager — The Emotional Core](#3-module-1-statemanager--the-emotional-core)
4. [Module 2: Enhanced Memory Hydration — WorkingMemory](#4-module-2-enhanced-memory-hydration--workingmemory)
5. [Module 3: Reactive Deliberation Engine](#5-module-3-reactive-deliberation-engine)
6. [Module 4: Object Affordance System](#6-module-4-object-affordance-system)
7. [Module 5: BeliefManager — Stance Dynamics](#7-module-5-beliefmanager--stance-dynamics)
8. [Module 6: Formal Action Types](#8-module-6-formal-action-types)
9. [Fate Engine Modifications](#9-fate-engine-modifications)
10. [PerceptionPipeline Fixes & Enhancements](#10-perceptionpipeline-fixes--enhancements)
11. [Protobuf Schema Changes](#11-protobuf-schema-changes)
12. [Agent Profile Schema v2](#12-agent-profile-schema-v2)
13. [LLM Prompt Architecture](#13-llm-prompt-architecture)
14. [Integration Map: What Changes Where](#14-integration-map-what-changes-where)
15. [Implementation Roadmap](#15-implementation-roadmap)
16. [Risk Analysis & Mitigations](#16-risk-analysis--mitigations)
17. [Validation Criteria](#17-validation-criteria)

---

## 1. Lessons from Phase 1: The Angry Man Room

### 1.1 What Worked

| Component | Evidence | Source |
|-----------|----------|--------|
| **20 TPS Tick Loop** | Stable across 24,000 ticks (20 minutes) with 4 LLM agents | `fate_engine.py` main loop |
| **Dual-Mode Cognition** | Staggered deliberation (tick offset per agent) created organic pacing | `AgentBrain._should_deliberate()` — `(tick + offset) % 50 == 0` |
| **Episodic Memory** | Bank Teller recalled "the old man's timing" from 5000+ ticks prior | CoT logs: `The_Bank_Teller.jsonl` Tick 4886 |
| **Character Consistency** | Angry Man maintained aggression throughout; Stockbroker stayed analytical | All 4 CoT JSONL logs |
| **Guest Agent Injection** | Tanit's probes via `TanitBridge.py` successfully influenced native agents | Experiment report §5, Phase III |
| **gRPC Stability** | Stream remained stable after broadcast hook fix | `grpc_server.py` post-resolution hook |

### 1.2 What Was Missing — The Five Gaps

| # | Gap | Concrete Impact | Phase 2 Module |
|---|-----|-----------------|----------------|
| **G1** | **Static Stances** | `profile["stance"] = "guilty"` never changes. Bank Teller expressed doubt but couldn't flip. | BeliefManager (§7) |
| **G2** | **No Object Interaction** | Switchblade referenced in dialogue but `EnvironmentObject` had no `EXAMINE` affordance. | Object Affordance System (§6) |
| **G3** | **Omniscient Perception** | `MemoryManager.ingest_tick()` iterates ALL actors/objects — no FOV, no occlusion. | PerceptionPipeline fixes (§10) |
| **G4** | **Flat Emotional Model** | "Angry" was a string trait, not a dynamic PAD vector. No mechanical effect on reasoning. | StateManager (§3) |
| **G5** | **Undifferentiated Memory** | `query_recent(limit=10)` returns last 10 chronologically. No relevance. No working memory. | WorkingMemory (§4) |

### 1.3 Critical Log Evidence

From `experiments/logs/chain_of_thought/The_Angry_Man.jsonl`:
```
Tick 4479: "I can't believe we're still wasting time on how fast an old man can walk."
```
**Problem:** Frustration is expressed textually, but has zero mechanical effect. His perception isn't narrowed. His deliberation latency doesn't change. His resistance to counter-evidence isn't amplified.

From `experiments/logs/chain_of_thought/The_Bank_Teller.jsonl`:
```
Tick 4886: "Would the old man really have been able to hear the boy shout over all that noise?"
```
**Problem:** Emergent deduction occurred, but there's no formal `EvidenceItem` tracking this insight. No `confidence` score adjusts. No `StanceChange` event fires. The deduction lives and dies in a JSONL log.

From `experiments/logs/analysis_report_v1.md`:
```
"The Teller's questions about the 'old man's timing' were adopted and amplified by the Foreman."
```
**Problem:** Social contagion was observed but not mechanically tracked. No belief propagation model.

---

## 2. Phase 2 Architecture Overview

### 2.1 System Diagram — The Cognitive Loop

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TSUKUYOMI PHASE 2: THE COGNITIVE CORE                   │
│                                                                                 │
│  ════════════════════════════════════════════════════════════════════════════    │
│  WORLD AUTHORITY                                                                │
│  ════════════════════════════════════════════════════════════════════════════    │
│                                                                                 │
│  ┌──────────────────────────┐                                                   │
│  │      FATE ENGINE          │ ◄─── 20 TPS Tick Loop (fate_engine.py)           │
│  │   (World State Authority) │                                                   │
│  │                           │ ◄─── NEW: EXAMINE, TAKE, DROP, GIVE, OPEN,       │
│  │   • Proposal/Resolution   │       READ, REFLECT, VOTE action resolvers       │
│  │   • Object State Mgmt     │                                                   │
│  │   • Stance Arbitration     │ ◄─── NEW: StanceShiftEvent broadcast            │
│  │   • Speech Event Pipeline  │ ◄─── NEW: SpeechEvent first-class objects       │
│  └─────────────┬─────────────┘                                                   │
│                │                                                                 │
│      TickState │ (gRPC stream)                                                   │
│                ▼                                                                 │
│  ════════════════════════════════════════════════════════════════════════════    │
│  PER-AGENT COGNITIVE STACK (brain/)                                              │
│  ════════════════════════════════════════════════════════════════════════════    │
│                                                                                 │
│  ┌──────────────────────────┐    ┌──────────────────────────┐                   │
│  │   PERCEPTION PIPELINE     │    │     STATE MANAGER         │                   │
│  │   (PerceptionPipeline.py) │    │     (StateManager.py)     │ ◄── NEW FILE     │
│  │                           │    │                           │                   │
│  │   • Vision (FOV+Occl.)    │    │   • PAD Model             │                   │
│  │   • Hearing (Omnidir.)    │    │     (Valence/Arousal/Dom) │                   │
│  │   • Proprioception        │    │   • Personality Baseline   │                   │
│  │   • Memory Echoes         │    │   • Emotional Episodes     │                   │
│  │   • Salience + Surprise   │    │   • Mood Label Derivation  │                   │
│  │   • ☐ BUG FIX: math.random│    │   • Regression to Baseline│                   │
│  └────────────┬──────────────┘    └─────────────┬─────────────┘                   │
│               │ List[Percept]                    │ EmotionalState                  │
│               ▼                                  ▼                                │
│  ┌───────────────────────────────────────────────────────────────┐               │
│  │              WORKING MEMORY (WorkingMemory.py)                │ ◄── NEW FILE  │
│  │                                                               │               │
│  │   7 ± 2 Slots (Miller's Law)                                 │               │
│  │   Sources: Top-3 Percepts + Relevant Episodic + Semantic      │               │
│  │   Refresh: Each deliberation cycle                            │               │
│  │   Output: Formatted LLM context string                        │               │
│  └───────────────────────────┬───────────────────────────────────┘               │
│                              │                                                   │
│               ┌──────────────┴──────────────┐                                   │
│               ▼                             ▼                                    │
│  ┌────────────────────────┐   ┌────────────────────────────┐                    │
│  │    EPISODIC MEMORY     │   │     SEMANTIC MEMORY         │                    │
│  │  (MemoryManager.py)    │   │   (MemoryManager.py)        │                    │
│  │                        │   │                             │                    │
│  │  • 5W Memories         │   │  • S→P→O Knowledge Graph   │                    │
│  │  • Emotional Tags      │   │  • Confidence Scores        │                    │
│  │  • Relevance Decay     │   │  • No Decay (persistent)    │                    │
│  │  • Enhanced: 5x slower │   │                             │                    │
│  │    for high-emotion    │   │                             │                    │
│  └────────────────────────┘   └────────────────────────────┘                    │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────┐               │
│  │           BELIEF MANAGER (BeliefManager.py)                   │ ◄── NEW FILE  │
│  │                                                               │               │
│  │   Topics → Evidence Ledger → Weighted Stance Calculation      │               │
│  │   Personality Bias (confirmation_bias, social_pressure_immunity)│              │
│  │   REFLECT action → add evidence → recalculate → StanceShift?  │               │
│  │   Output: Belief context for LLM prompt                       │               │
│  └───────────────────────────┬───────────────────────────────────┘               │
│                              │                                                   │
│                              ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────┐               │
│  │        DELIBERATION ENGINE (AgentBrain.py — MODIFIED)         │               │
│  │                                                               │               │
│  │   PROACTIVE: Every 50 ticks (existing, unchanged)             │               │
│  │   REACTIVE: Triggered by high-salience percepts               │ ◄── NEW      │
│  │   PREEMPTION: CancellationToken for interrupted thought       │ ◄── NEW      │
│  │   PRIORITY QUEUE: threat > direct_address > scheduled > idle  │ ◄── NEW      │
│  │                                                               │               │
│  │   Output: Proposal → Fate Engine                              │               │
│  └───────────────────────────────────────────────────────────────┘               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (One Complete Cycle)

```
1. Fate Engine broadcasts TickState via gRPC stream
2. AgentBrain._process_tick() receives TickState
3. PerceptionPipeline.process() filters WorldState → List[Percept]
4. StateManager.update() processes percepts → updates PAD vector
5. WorkingMemory.refresh() selects top-7 items from percepts + episodic + semantic
6. ReactiveTrigger.classify() checks if any percept demands immediate deliberation
7. IF reactive trigger OR scheduled deliberation:
   a. BeliefManager.format_beliefs() → belief context string
   b. StateManager.get_emotional_modifier() → emotional context string
   c. WorkingMemory.to_llm_context() → memory context string
   d. LLMService.generate_plan() → {thought, action, params}
   e. IF action == "REFLECT": BeliefManager.add_evidence() → possible StanceShiftEvent
   f. AgentBrain submits Proposal to Fate Engine
8. Fate Engine resolves Proposal → Resolution
9. Resolution broadcast → next TickState → loop
```

---

## 3. Module 1: StateManager — The Emotional Core

### 3.1 Purpose

Transform emotions from static profile strings into dynamic vectors that mechanically influence perception and reasoning.

**Current state:** `profile["stance"] = "guilty"`, `profile["backstory"]` mentions "hot-tempered" — but these are just LLM prompt text. They have no mechanical weight.

**Target state:** A `StateManager` object per agent that holds a PAD (Pleasure-Arousal-Dominance) vector, updates it every tick based on perceived events, and exports an `EmotionalState` that modulates:
- Perception salience weights (high arousal → tunnel vision)
- LLM prompt modifiers (frustration → defensive reasoning)
- Memory consolidation (high-emotion events decay 5x slower)

### 3.2 File: `brain/StateManager.py` (NEW)

```python
"""
StateManager — The Emotional Core
Phase 2 Module 1

Implements the PAD (Pleasure-Arousal-Dominance) emotional model.
Each agent's emotions evolve based on perceived events and regress
towards their personality baseline over time.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("StateManager")


@dataclass
class PersonalityBaseline:
    """Static personality anchors. Emotional state regresses towards these."""
    valence_baseline: float = 0.0      # -1.0 to 1.0
    arousal_baseline: float = 0.5      # 0.0 to 1.0
    dominance_baseline: float = 0.0    # -1.0 to 1.0
    regression_rate: float = 0.015     # Per-tick regression towards baseline


@dataclass
class EmotionalEpisode:
    """A temporary emotional spike triggered by a specific event."""
    trigger_event_id: str
    emotion_type: str       # "anger", "fear", "surprise", "contempt", "relief"
    intensity: float        # 0.0 to 1.0
    onset_tick: int
    decay_rate: float = 0.005  # Per-tick intensity reduction


@dataclass
class EmotionalState:
    """The agent's current emotional state — the PAD vector + derived mood."""
    valence: float = 0.0       # Pleasure: -1.0 (distress) to +1.0 (joy)
    arousal: float = 0.5       # 0.0 (calm) to 1.0 (agitated)
    dominance: float = 0.0     # -1.0 (submissive) to +1.0 (dominant)
    mood_label: str = "neutral"
    active_episodes: List[EmotionalEpisode] = field(default_factory=list)


# Event → PAD delta mapping
EMOTIONAL_IMPACT_RULES: Dict[str, Dict[str, float]] = {
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
    },
    "new_evidence_discovered": {
        "valence_delta": +0.1,
        "arousal_delta": +0.15,
        "dominance_delta": +0.05
    },
    "social_pressure": {
        "valence_delta": -0.15,
        "arousal_delta": +0.1,
        "dominance_delta": -0.2
    },
    "stance_vindicated": {
        "valence_delta": +0.2,
        "arousal_delta": -0.05,
        "dominance_delta": +0.15
    }
}


class StateManager:
    """
    Per-agent emotional state controller.
    
    Usage:
        sm = StateManager("juror-3", PersonalityBaseline(
            valence_baseline=-0.3, arousal_baseline=0.7,
            dominance_baseline=0.6, regression_rate=0.01
        ))
        sm.update(percepts, current_tick)
        modifier = sm.get_emotional_modifier()  # For LLM prompt
    """
    
    MAX_EPISODES = 10  # Cap active emotional episodes
    
    def __init__(self, agent_id: str, baseline: PersonalityBaseline):
        self.agent_id = agent_id
        self.baseline = baseline
        self.state = EmotionalState(
            valence=baseline.valence_baseline,
            arousal=baseline.arousal_baseline,
            dominance=baseline.dominance_baseline
        )
    
    def update(self, percepts: list, current_tick: int):
        """
        Called every tick (or every deliberation cycle).
        1. Classify emotional impacts from percepts.
        2. Apply PAD deltas with arousal-scaled volatility.
        3. Decay active episodes.
        4. Regress towards personality baseline.
        5. Derive mood label.
        """
        # 1. Process percepts for emotional impact
        for percept in percepts:
            event_type = self._classify_event(percept)
            if event_type and event_type in EMOTIONAL_IMPACT_RULES:
                impact = EMOTIONAL_IMPACT_RULES[event_type]
                
                # Emotional Inertia (from review): scale by current arousal
                # High arousal → more volatile → bigger swings
                volatility = 0.5 + (self.state.arousal * 0.5)  # Range: 0.5 to 1.0
                
                self.state.valence = self._clamp(
                    self.state.valence + impact["valence_delta"] * volatility, -1.0, 1.0
                )
                self.state.arousal = self._clamp(
                    self.state.arousal + impact["arousal_delta"] * volatility, 0.0, 1.0
                )
                self.state.dominance = self._clamp(
                    self.state.dominance + impact["dominance_delta"] * volatility, -1.0, 1.0
                )
                
                # Create emotional episode for intense events
                if abs(impact["valence_delta"]) > 0.2 or impact["arousal_delta"] > 0.3:
                    self.state.active_episodes.append(EmotionalEpisode(
                        trigger_event_id=getattr(percept, 'percept_id', 'unknown'),
                        emotion_type=event_type,
                        intensity=abs(impact["valence_delta"]),
                        onset_tick=current_tick,
                        decay_rate=0.005
                    ))
        
        # 2. Decay active episodes
        surviving = []
        for ep in self.state.active_episodes:
            ep.intensity -= ep.decay_rate
            if ep.intensity > 0.05:
                surviving.append(ep)
        self.state.active_episodes = surviving[-self.MAX_EPISODES:]
        
        # 3. Regress towards personality baseline
        rate = self.baseline.regression_rate
        self.state.valence += (self.baseline.valence_baseline - self.state.valence) * rate
        self.state.arousal += (self.baseline.arousal_baseline - self.state.arousal) * rate
        self.state.dominance += (self.baseline.dominance_baseline - self.state.dominance) * rate
        
        # 4. Derive mood label
        self.state.mood_label = self._derive_mood_label()
    
    def get_emotional_modifier(self) -> str:
        """Generate LLM prompt modifier based on emotional state."""
        parts = []
        
        if self.state.arousal > 0.7:
            parts.append("You are feeling highly agitated. Your thoughts race. Focus on the most pressing issue.")
        elif self.state.arousal > 0.5:
            parts.append("You feel alert and engaged.")
        else:
            parts.append("You feel calm and measured.")
        
        if self.state.valence < -0.5:
            parts.append("You feel defensive and frustrated. Others seem to be against you.")
        elif self.state.valence < -0.2:
            parts.append("You feel uneasy. Something isn't right.")
        elif self.state.valence > 0.3:
            parts.append("You feel positive. Things are going your way.")
        
        if self.state.dominance > 0.5:
            parts.append("Assert your position confidently. You feel in control.")
        elif self.state.dominance < -0.3:
            parts.append("You feel uncertain about speaking up. Others seem more authoritative.")
        
        return " ".join(parts)
    
    def get_perception_modifiers(self) -> dict:
        """
        Return modifiers for the PerceptionPipeline.
        High arousal → narrowed attention (fewer percepts processed).
        Low valence → threat detection boost.
        """
        return {
            "attention_width": max(3, int(7 - self.state.arousal * 4)),  # 3-7 percepts
            "threat_salience_boost": max(0.0, -self.state.valence * 0.3),
            "social_salience_boost": max(0.0, -self.state.dominance * 0.2)
        }
    
    def get_memory_emotional_intensity(self) -> float:
        """Return current emotional intensity for memory tagging."""
        return max(abs(self.state.valence), self.state.arousal)
    
    def _classify_event(self, percept) -> Optional[str]:
        """
        Classify a percept into an emotional event type.
        Real implementation would use sentiment analysis; here we use heuristics.
        """
        # Check for speech percepts
        if hasattr(percept, 'speech') and percept.HasField('speech'):
            content = percept.speech.content.lower()
            if percept.speech.is_direct_address:
                # Simple sentiment heuristics
                negative_markers = ["wrong", "ridiculous", "stupid", "disagree", "no", "can't believe"]
                positive_markers = ["agree", "right", "good point", "exactly", "yes"]
                
                if any(m in content for m in negative_markers):
                    return "criticized"
                if any(m in content for m in positive_markers):
                    return "agreed_with"
            return None
        
        # Check for event percepts
        if hasattr(percept, 'event') and percept.HasField('event'):
            event_type = percept.event.event_type
            if event_type in ("attack", "physical_threat"):
                return "physical_threat"
            if event_type == "evidence_revealed":
                return "new_evidence_discovered"
            if event_type == "stance_shift":
                return "social_pressure"
        
        return None
    
    def _derive_mood_label(self) -> str:
        """Map PAD vector to a human-readable mood label."""
        v, a, d = self.state.valence, self.state.arousal, self.state.dominance
        
        if v < -0.5 and a > 0.6:
            return "furious" if d > 0.3 else "panicked"
        if v < -0.3 and a > 0.4:
            return "frustrated" if d > 0 else "anxious"
        if v < -0.1:
            return "displeased" if a > 0.3 else "melancholy"
        if v > 0.3 and a > 0.5:
            return "excited" if d > 0 else "elated"
        if v > 0.1:
            return "content" if a < 0.4 else "enthusiastic"
        if a > 0.6:
            return "tense"
        if a < 0.3:
            return "serene"
        return "neutral"
    
    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))
```

### 3.3 Personality Baselines for Test Agents

These map directly to the existing `juror_profiles.json` traits:

| Agent | Valence | Arousal | Dominance | Regression | Rationale |
|-------|---------|---------|-----------|------------|-----------|
| The Foreman | +0.1 | 0.4 | +0.3 | 0.02 | Calm, methodical, moderate authority |
| The Bank Teller | +0.1 | 0.3 | -0.4 | 0.02 | Slightly positive, low energy, submissive |
| The Angry Man | -0.3 | 0.7 | +0.6 | 0.01 | Tends negative, high energy, wants control, slow regression |
| The Stockbroker | +0.0 | 0.4 | +0.4 | 0.015 | Neutral valence, moderate arousal, confident |

### 3.4 Influence on Other Modules

| PAD State | Perception Effect | Reasoning Effect | Memory Effect |
|-----------|-------------------|------------------|---------------|
| High Arousal (>0.7) | `attention_width` narrows to 3 | Faster but less thorough deliberation prompt | Current events tagged as high-intensity |
| Low Valence (<-0.5) | `threat_salience_boost` +0.15 | Pessimistic LLM modifier | Negative memories decay slower |
| High Dominance (>0.5) | Social cues lower salience | Assertive action bias in prompt | — |
| Low Dominance (<-0.3) | Social cues higher salience | Avoidance-oriented prompt modifier | — |

---

## 4. Module 2: Enhanced Memory Hydration — WorkingMemory

### 4.1 Current Limitation

`MemoryManager.query_recent(limit=10)` on line 109-111 of the current file simply returns `self.episodic_memory[-limit:]`. This is:
- **Not relevance-based** — returns most recent, not most relevant
- **Not capacity-bounded** — the LLM gets 10 items regardless of cognitive load
- **Not emotionally weighted** — traumatic and mundane events decay identically

### 4.2 Three-Tier Architecture

```
┌──────────────────────────────────────────┐
│         WORKING MEMORY (7 ± 2 slots)     │  ◄── Refreshed each deliberation
│                                          │      cycle. Feeds LLM prompt.
│  Sources:                                │
│    • Top 3 salient percepts              │
│    • Top 3 relevant episodic memories    │
│    • Top 1-3 semantic facts about        │
│      current percept subjects            │
└──────────────────┬───────────────────────┘
                   │ Consolidation
                   ▼
┌──────────────────────────────────────────┐
│         EPISODIC MEMORY (enhanced)        │  ◄── Modified MemoryManager
│                                          │
│  • 5W memories (existing)                │
│  • NEW: emotional_intensity tag          │
│  • NEW: relevance_score with decay       │
│  • NEW: decay_rate varies by emotion     │
│    - Normal: 0.001/tick                  │
│    - High-emotion: 0.0002/tick (5x)     │
│  • Cap: 500 entries (existing)           │
└──────────────────┬───────────────────────┘
                   │ Abstraction
                   ▼
┌──────────────────────────────────────────┐
│         SEMANTIC MEMORY (existing)        │  ◄── No changes needed
│                                          │
│  Subject → Predicate → Object triples    │
│  No decay. Persistent beliefs.           │
└──────────────────────────────────────────┘
```

### 4.3 File: `brain/WorkingMemory.py` (NEW)

```python
"""
WorkingMemory — Cognitively-bounded active context.
Phase 2 Module 2

Implements Miller's Law: 7 ± 2 chunks.
Refreshed each deliberation cycle from percepts + episodic + semantic.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("WorkingMemory")


@dataclass
class MemoryChunk:
    """A single item in working memory."""
    source: str          # "percept", "episodic", "semantic"
    content: Any         # Percept object, Memory5W dict, or semantic fact string
    relevance: float     # 0.0 to 1.0
    
    def to_text(self) -> str:
        """Format for LLM context."""
        if self.source == "percept":
            return self._format_percept()
        elif self.source == "episodic":
            return self._format_episodic()
        else:
            return str(self.content)
    
    def _format_percept(self) -> str:
        p = self.content
        if hasattr(p, 'actor') and p.HasField('actor'):
            return f"[NOW] {p.actor.name} is {p.actor.visible_action_state} ({p.actor.visible_emotional_cue})"
        if hasattr(p, 'speech') and p.HasField('speech'):
            addr = " (to you)" if p.speech.is_direct_address else ""
            return f"[NOW] {p.speech.speaker_name} says{addr}: \"{p.speech.content}\""
        if hasattr(p, 'object') and p.HasField('object'):
            return f"[NOW] You see: {p.object.apparent_type} ({', '.join(p.object.visible_affordances)})"
        return f"[NOW] Percept: {self.content}"
    
    def _format_episodic(self) -> str:
        mem = self.content
        who = mem.get("who", "someone")
        what = mem.get("what", "did something")
        when = mem.get("when", "?")
        details = mem.get("details", {})
        msg = details.get("message", "")
        if msg:
            return f"[MEMORY tick {when}] {who}: \"{msg}\""
        return f"[MEMORY tick {when}] {who} {what}"


class WorkingMemory:
    """
    Active cognitive context. Bounded by Miller's Law.
    
    Usage:
        wm = WorkingMemory()
        wm.refresh(percepts, episodic_memory, semantic_memory, emotional_state)
        context = wm.to_llm_context()
    """
    
    MAX_SLOTS = 7
    
    def __init__(self):
        self.slots: List[MemoryChunk] = []
    
    @property
    def slot_count(self) -> int:
        return len(self.slots)
    
    def refresh(
        self,
        percepts: list,
        episodic_memories: list,
        semantic_memory: dict,
        emotional_state: Any,
        current_topics: Optional[List[str]] = None
    ):
        """
        Select the most relevant items for current working memory.
        Called each deliberation cycle.
        """
        candidates = []
        topics = current_topics or []
        
        # 1. Top-3 salient percepts (immediate awareness)
        for p in sorted(percepts, key=lambda x: x.salience, reverse=True)[:3]:
            candidates.append(MemoryChunk(
                source="percept",
                content=p,
                relevance=p.salience
            ))
        
        # 2. Relevant episodic memories (not just recent)
        scored_memories = self._score_episodic_memories(
            episodic_memories, topics, emotional_state
        )
        for score, mem in scored_memories[:5]:
            candidates.append(MemoryChunk(
                source="episodic",
                content=mem,
                relevance=score
            ))
        
        # 3. Semantic facts about perceived subjects
        perceived_subjects = set()
        for p in percepts:
            if hasattr(p, 'actor') and p.HasField('actor'):
                perceived_subjects.add(p.actor.actor_id)
                perceived_subjects.add(p.actor.name)
            if hasattr(p, 'speech') and p.HasField('speech'):
                perceived_subjects.add(p.speech.speaker_id)
        
        for subject in perceived_subjects:
            if subject in semantic_memory:
                for predicate, facts in semantic_memory[subject].items():
                    for fact in facts[:2]:
                        candidates.append(MemoryChunk(
                            source="semantic",
                            content=f"{subject} {predicate} {fact['object']}",
                            relevance=0.4
                        ))
        
        # 4. Sort by relevance, take top MAX_SLOTS
        candidates.sort(key=lambda c: c.relevance, reverse=True)
        self.slots = candidates[:self.MAX_SLOTS]
    
    def to_llm_context(self) -> str:
        """Format working memory for LLM prompt."""
        sections = {"percept": [], "episodic": [], "semantic": []}
        for chunk in self.slots:
            sections[chunk.source].append(chunk.to_text())
        
        parts = [f"WORKING MEMORY ({len(self.slots)}/{self.MAX_SLOTS} active items):"]
        
        if sections["percept"]:
            parts.append("\n[IMMEDIATE AWARENESS]")
            parts.extend(f"  {line}" for line in sections["percept"])
        
        if sections["episodic"]:
            parts.append("\n[RELEVANT MEMORIES]")
            parts.extend(f"  {line}" for line in sections["episodic"])
        
        if sections["semantic"]:
            parts.append("\n[KNOWN FACTS]")
            parts.extend(f"  {line}" for line in sections["semantic"])
        
        if not any(sections.values()):
            parts.append("  (Mind is blank)")
        
        return "\n".join(parts)
    
    def _score_episodic_memories(
        self,
        memories: list,
        topics: List[str],
        emotional_state: Any
    ) -> List[tuple]:
        """Score episodic memories by relevance to current context."""
        scored = []
        for mem in memories:
            # Topic match
            mem_text = str(mem.get("details", {}))
            topic_match = sum(1 for t in topics if t.lower() in mem_text.lower())
            topic_score = min(topic_match / max(len(topics), 1), 1.0)
            
            # Recency (newer = higher)
            recency_score = 0.3  # Default for old memories
            
            # Emotional intensity (if tagged)
            emotion_score = mem.get("emotional_intensity", 0.0) * 0.3
            
            total = (topic_score * 0.5) + (recency_score * 0.2) + (emotion_score * 0.3)
            scored.append((total, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
```

### 4.4 Changes to Existing `MemoryManager.py`

The following fields are added to episodic memory entries:

```python
# In MemoryManager.ingest_tick(), modify the memory_entry creation:
memory_entry = {
    "who": res.actor_id,
    "what": res.outcome.get("action", "unknown"),
    "when": tick_num,
    "where": self._get_actor_pos(tick_state, res.actor_id),
    "details": dict(res.outcome),
    # NEW Phase 2 fields:
    "emotional_intensity": 0.0,    # Set by StateManager
    "relevance_score": 1.0,        # Starts at 1.0, decays over time
    "decay_rate": 0.001,           # Normal decay; 0.0002 for high-emotion
    "topics": []                   # Extracted keywords for topic matching
}
```

New method for relevance-based query:

```python
def query_by_relevance(self, topics: List[str], limit: int = 5) -> List[Dict]:
    """Retrieve memories by topic relevance + emotional intensity."""
    scored = []
    for mem in self.episodic_memory:
        mem_text = str(mem.get("details", {}))
        topic_match = sum(1 for t in topics if t.lower() in mem_text.lower())
        emotion_boost = mem.get("emotional_intensity", 0.0) * 0.3
        relevance = mem.get("relevance_score", 0.5)
        
        score = (topic_match * 0.4) + (relevance * 0.3) + (emotion_boost * 0.3)
        scored.append((score, mem))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]

def tick_decay(self):
    """Run memory decay. Call periodically (e.g., every 10 ticks, not every tick)."""
    to_remove = []
    for i, mem in enumerate(self.episodic_memory):
        decay = mem.get("decay_rate", 0.001)
        mem["relevance_score"] = max(0.0, mem.get("relevance_score", 1.0) - decay)
        if mem["relevance_score"] < 0.05:
            to_remove.append(i)
    
    # Prune dead memories (iterate in reverse)
    for i in reversed(to_remove):
        self.episodic_memory.pop(i)
```

**Performance note (from review):** Memory decay should NOT run every tick. Run it every 10 ticks or batch 10% of memories per tick to stay within the 50ms tick budget.

---

## 5. Module 3: Reactive Deliberation Engine

### 5.1 Current Limitation

`AgentBrain._should_deliberate()` (line 67-69):
```python
def _should_deliberate(self, tick_state):
    return (tick_state.tick_number + self.tick_offset) % 50 == 0
```

This is **proactive only**. If someone directly addresses the agent at tick 101, and the agent's next scheduled deliberation is tick 150, there's a 49-tick (~2.5 second) dead zone where the agent ignores the stimulus.

### 5.2 Reactive Trigger System

Add to `AgentBrain._process_tick()`:

```python
async def _process_tick(self, tick_state):
    # 1. Perception (NEW)
    percepts = self.perception.process(
        tick_state.world_state, self._get_internal_state(), tick_state.tick_number
    )
    
    # 2. Emotional update (NEW)
    self.state_manager.update(percepts, tick_state.tick_number)
    
    # 3. Memory ingestion (EXISTING, modified)
    self.memory.ingest_tick(tick_state)
    
    # 4. Memory decay (NEW, every 10 ticks)
    if tick_state.tick_number % 10 == 0:
        self.memory.tick_decay()
    
    # 5. System 1: Reflexes (EXISTING)
    await self._run_reflexes(tick_state)
    
    # 6. System 2: Reactive deliberation check (NEW)
    reactive_trigger = self._check_reactive_triggers(percepts)
    
    # 7. System 2: Proactive or reactive deliberation
    if not self.is_thinking:
        if reactive_trigger:
            asyncio.create_task(self._deliberate(tick_state, percepts, reason=reactive_trigger))
        elif self._should_deliberate(tick_state):
            asyncio.create_task(self._deliberate(tick_state, percepts, reason="scheduled"))
```

### 5.3 Reactive Trigger Classification

```python
def _check_reactive_triggers(self, percepts: list) -> Optional[str]:
    """
    Check if any percept demands immediate deliberation.
    Returns trigger reason string, or None.
    """
    for percept in percepts:
        # Priority 1: Direct address (someone spoke TO this agent)
        if hasattr(percept, 'speech') and percept.HasField('speech'):
            if percept.speech.is_direct_address:
                return "direct_address"
        
        # Priority 2: High-salience event (surprise, threat)
        if percept.salience > 0.85:
            return "high_salience_event"
        
        # Priority 3: Stance shift by another agent (social trigger)
        if hasattr(percept, 'event') and percept.HasField('event'):
            if percept.event.event_type == "stance_shift":
                return "social_trigger"
    
    return None
```

### 5.4 Preemption Protocol

For Phase 2, we implement a **simple preemption model** (not the full priority queue from v1.0 — that adds complexity without clear Phase 2 benefit):

```python
async def _deliberate(self, tick_state, percepts, reason="scheduled"):
    """Enhanced deliberation with reactive support."""
    if self.is_thinking:
        # Simple preemption: only reactive triggers can interrupt
        if reason in ("direct_address", "high_salience_event"):
            logger.info(f"PREEMPTING scheduled deliberation for {reason}")
            self._cancel_current_deliberation = True
            # Wait for current to finish (it checks the flag)
            await asyncio.sleep(0.5)
        else:
            return  # Don't interrupt for lower-priority triggers
    
    self.is_thinking = True
    self._cancel_current_deliberation = False
    
    try:
        # Refresh working memory
        self.working_memory.refresh(
            percepts=percepts,
            episodic_memories=self.memory.episodic_memory,
            semantic_memory=self.memory.semantic_memory,
            emotional_state=self.state_manager.state,
            current_topics=self._extract_topics(percepts)
        )
        
        if self._cancel_current_deliberation:
            return
        
        # Build enhanced context
        belief_context = self.belief_manager.format_beliefs()
        emotional_modifier = self.state_manager.get_emotional_modifier()
        working_memory_context = self.working_memory.to_llm_context()
        
        plan = await LLMService.generate_plan_v2(
            self.profile,
            working_memory_context,
            belief_context,
            emotional_modifier,
            reason
        )
        
        if self._cancel_current_deliberation:
            return
        
        # Handle REFLECT action (belief update)
        if plan['action'] == "REFLECT":
            self._handle_reflect(plan)
        
        # Log and submit
        self._log_chain_of_thought(tick_state, plan)
        await self.client.submit_proposal(
            self.actor_id, plan['action'], plan.get('params', {})
        )
        
    except Exception as e:
        logger.error(f"Deliberation failed for {self.profile['name']}: {e}")
    finally:
        self.is_thinking = False
```

### 5.5 LLM Rate Limiting Consideration

**Critical constraint:** `LLMService._semaphore = asyncio.Semaphore(1)` with 2.5s cooldown. Reactive deliberation must respect this.

Mitigation: Reactive triggers enter the same semaphore queue. If the semaphore is occupied (another agent is deliberating), the reactive deliberation waits. This is acceptable because:
- Direct address responses within 5 seconds feel natural in conversation
- The semaphore ensures we never exceed API rate limits
- The alternative (multiple concurrent LLM calls) would hit 429s

---

## 6. Module 4: Object Affordance System

### 6.1 Purpose

Transform `EnvironmentObject` from passive data blobs into interactive entities that agents can examine, take, use, and share — revealing hidden information and enabling physical evidence discovery.

### 6.2 Protobuf Changes to `core.proto`

```protobuf
// MODIFIED: EnvironmentObject with affordances
message EnvironmentObject {
  string id = 1;
  string type = 2;
  tsukuyomi.common.Vector2 position = 3;
  bool interactive = 4;
  map<string, string> properties = 5;
  
  // NEW Phase 2 fields
  string display_name = 6;                    // Human-readable name
  repeated Affordance affordances = 7;        // What can be done with this object
  map<string, string> hidden_properties = 8;  // Revealed via EXAMINE
  string state = 9;                           // "open", "closed", "in_evidence_bag", etc.
  string owner_id = 10;                       // Actor who possesses this (empty = world)
}

// NEW message
message Affordance {
  string action_type = 1;        // "EXAMINE", "TAKE", "USE", "OPEN", "READ", "COMPARE"
  string precondition = 2;       // JSON expression: '{"requires_item": "key_01"}'
  string effect_description = 3; // "Study the knife's handle pattern" (for LLM)
  repeated string semantic_tags = 4;  // ["evidence", "visual_inspection"]
}
```

### 6.3 Example Objects for "12 Angry Men v2"

```python
# The Switchblade — primary evidence
switchblade = {
    "id": "evidence_knife_01",
    "type": "weapon",
    "display_name": "The Murder Weapon (Switchblade)",
    "position": {"x": 5.0, "y": 2.0},  # On the evidence table
    "interactive": True,
    "state": "in_evidence_bag",
    "properties": {"description": "A switchblade knife presented as evidence."},
    "hidden_properties": {
        "manufacture_location": "A common store on the boy's street",
        "uniqueness": "NOT unique — identical knives sold at local shops",
        "handle_markings": "Standard carved handle, mass-produced"
    },
    "affordances": [
        {
            "action_type": "EXAMINE",
            "precondition": "{}",
            "effect_description": "Study the knife's handle pattern and markings",
            "semantic_tags": ["evidence", "visual_inspection"]
        },
        {
            "action_type": "TAKE",
            "precondition": '{"requires_role": "foreman"}',
            "effect_description": "Pick up the knife for demonstration",
            "semantic_tags": ["possession", "authority"]
        }
    ]
}

# The Case File — readable document
case_file = {
    "id": "evidence_file_01",
    "type": "document",
    "display_name": "Trial Case Summary",
    "position": {"x": 4.0, "y": 2.0},
    "interactive": True,
    "state": "on_table",
    "properties": {"description": "A manila folder containing the case summary."},
    "hidden_properties": {
        "timeline_detail": "Witness claims to have seen stabbing at 12:10 AM",
        "noise_note": "El-train passes building every 5 minutes (scheduled at 12:09 AM)",
        "distance_note": "Old man's apartment: 40 feet from front door to hallway"
    },
    "affordances": [
        {
            "action_type": "READ",
            "precondition": "{}",
            "effect_description": "Read the case file details",
            "semantic_tags": ["evidence", "information"]
        }
    ]
}

# A Second Knife — Tanit's dramatic proof
second_knife = {
    "id": "evidence_knife_02",
    "type": "weapon",
    "display_name": "A Second Switchblade",
    "position": {"x": 3.0, "y": 2.0},
    "interactive": False,  # Hidden until planted by guest agent
    "state": "hidden",
    "properties": {"description": "An identical switchblade purchased from a nearby store."},
    "hidden_properties": {
        "origin": "Bought by Juror 8 (Tanit) from a store near the boy's home",
        "implication": "If the knife isn't unique, it can't be conclusive evidence"
    },
    "affordances": [
        {
            "action_type": "EXAMINE",
            "precondition": "{}",
            "effect_description": "Compare this knife to the murder weapon",
            "semantic_tags": ["evidence", "comparison", "logical_argument"]
        }
    ]
}
```

### 6.4 EXAMINE Action Flow — Detailed

```
Agent submits: EXAMINE(target_id="evidence_knife_01")
    │
    ▼
FateEngine._resolve_examine():
    1. Validate actor exists
    2. Validate object exists in world_state.objects
    3. Check EXAMINE affordance exists on object
    4. Check preconditions (JSON eval)
    5. Check distance: actor.position ↔ object.position ≤ 10.0m
    6. SUCCESS → Return Resolution with revealed hidden_properties
    │
    ▼
Resolution broadcast in TickState:
    outcome = {
        "action": "examine",
        "object_id": "evidence_knife_01",
        "revealed_properties": {
            "manufacture_location": "A common store on the boy's street",
            "uniqueness": "NOT unique — identical knives sold at local shops",
            "handle_markings": "Standard carved handle, mass-produced"
        }
    }
    │
    ▼
AgentBrain processes resolution:
    1. MemoryManager.add_fact("evidence_knife_01", "uniqueness", "NOT unique")
    2. MemoryManager.add_fact("evidence_knife_01", "manufacture_location", "common store")
    3. Episodic: "I examined the knife and discovered it's not unique."
    4. BeliefManager.add_evidence("defendant_guilt", {
           description: "The murder weapon isn't unique",
           position: "against",
           weight: 0.5,
           source_type: "observation"
       })
    5. → Possible StanceShiftEvent if evidence tips the balance
```

---

## 7. Module 5: BeliefManager — Stance Dynamics

### 7.1 The Core Problem

Line 48 of `LLMService.py`:
```python
Current Stance: {profile['stance']}
```

This hardcoded string means the LLM always reasons from a fixed position. The Bank Teller can *express* doubt in his Chain of Thought, but his profile permanently says "guilty." There is no feedback loop.

### 7.2 File: `brain/BeliefManager.py` (NEW)

```python
"""
BeliefManager — Dynamic Belief & Stance System
Phase 2 Module 5

Replaces hardcoded `profile["stance"]` with an evidence-weighted
belief graph. Stances emerge from accumulated evidence, modulated
by personality biases.
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("BeliefManager")


class StancePosition(Enum):
    STRONGLY_FOR = "strongly_for"
    LEANING_FOR = "leaning_for"
    NEUTRAL = "neutral"
    LEANING_AGAINST = "leaning_against"
    STRONGLY_AGAINST = "strongly_against"
    
    def to_human_readable(self, topic_for_label: str = "guilty") -> str:
        """Convert to context-appropriate label."""
        mapping = {
            "strongly_for": f"Firmly {topic_for_label}",
            "leaning_for": f"Leaning {topic_for_label}",
            "neutral": "Undecided",
            "leaning_against": f"Leaning not {topic_for_label}",
            "strongly_against": f"Firmly not {topic_for_label}"
        }
        return mapping.get(self.value, self.value)


@dataclass
class EvidenceItem:
    """A single piece of evidence in the belief ledger."""
    evidence_id: str
    description: str
    weight: float              # 0.0 to 1.0 — impact strength
    source_type: str           # "testimony", "observation", "reasoning", "social_pressure"
    acquired_tick: int = 0
    source_agent_id: str = ""  # Who told me / where I observed


@dataclass
class StanceChange:
    """Record of a stance shift for narrative tracking."""
    tick: int
    old_stance: StancePosition
    new_stance: StancePosition
    trigger_evidence_id: str
    internal_reasoning: str


@dataclass
class BeliefTopic:
    """A single topic with for/against evidence and derived stance."""
    topic_id: str
    topic_name: str
    for_label: str = "guilty"      # What "for" means in context
    evidence_for: List[EvidenceItem] = field(default_factory=list)
    evidence_against: List[EvidenceItem] = field(default_factory=list)
    history: List[StanceChange] = field(default_factory=list)


@dataclass
class PersonalityBias:
    """How personality influences evidence weighting."""
    confirmation_bias: float = 1.0          # >1.0 = over-weights confirming evidence
    disconfirmation_resistance: float = 1.0  # <1.0 = under-weights disconfirming evidence
    social_pressure_immunity: float = 0.5    # 0.0 = fully swayed, 1.0 = immune


class BeliefManager:
    """
    Manages dynamic beliefs and stances for an agent.
    
    Usage:
        bm = BeliefManager("juror-3", PersonalityBias(...))
        bm.initialize_topic("defendant_guilt", "Is the defendant guilty?",
                           initial_for=[...], initial_against=[])
        
        stance, confidence = bm.get_stance("defendant_guilt")
        bm.add_evidence("defendant_guilt", evidence, "against")
        
        context = bm.format_beliefs()  # For LLM prompt
    """
    
    MAX_EVIDENCE_PER_SIDE = 20  # Cap to prevent unbounded growth
    
    def __init__(self, agent_id: str, personality_bias: PersonalityBias):
        self.agent_id = agent_id
        self.bias = personality_bias
        self.topics: Dict[str, BeliefTopic] = {}
        self.current_tick: int = 0
    
    def initialize_topic(
        self,
        topic_id: str,
        topic_name: str,
        for_label: str = "guilty",
        initial_for: Optional[List[EvidenceItem]] = None,
        initial_against: Optional[List[EvidenceItem]] = None
    ):
        """Set up a belief topic with optional initial evidence."""
        self.topics[topic_id] = BeliefTopic(
            topic_id=topic_id,
            topic_name=topic_name,
            for_label=for_label,
            evidence_for=initial_for or [],
            evidence_against=initial_against or []
        )
    
    def get_stance(self, topic_id: str) -> Tuple[StancePosition, float]:
        """Calculate current stance and confidence from evidence."""
        if topic_id not in self.topics:
            return StancePosition.NEUTRAL, 0.0
        
        topic = self.topics[topic_id]
        
        # Calculate weighted scores with personality bias
        for_score = sum(e.weight for e in topic.evidence_for) * self.bias.confirmation_bias
        against_score = sum(e.weight for e in topic.evidence_against) * self.bias.disconfirmation_resistance
        
        net = for_score - against_score
        
        # Map net score to stance position
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
        
        # Confidence: based on evidence volume and consistency
        total_evidence = len(topic.evidence_for) + len(topic.evidence_against)
        consistency = abs(net) / max(for_score + against_score, 0.1)
        confidence = min(0.3 + (total_evidence * 0.08) + (consistency * 0.3), 1.0)
        
        return stance, confidence
    
    def add_evidence(
        self,
        topic_id: str,
        evidence: EvidenceItem,
        position: str  # "for" or "against"
    ) -> Optional[dict]:
        """
        Add evidence and check for stance shift.
        Returns a StanceShiftEvent dict if stance changed, None otherwise.
        """
        if topic_id not in self.topics:
            logger.warning(f"Unknown topic: {topic_id}")
            return None
        
        topic = self.topics[topic_id]
        old_stance, old_conf = self.get_stance(topic_id)
        
        # Apply social pressure immunity for social-source evidence
        if evidence.source_type == "social_pressure":
            evidence.weight *= (1.0 - self.bias.social_pressure_immunity)
        
        # Add evidence
        if position == "for":
            topic.evidence_for.append(evidence)
            # Cap
            if len(topic.evidence_for) > self.MAX_EVIDENCE_PER_SIDE:
                # Remove lowest-weight evidence
                topic.evidence_for.sort(key=lambda e: e.weight)
                topic.evidence_for.pop(0)
        else:
            topic.evidence_against.append(evidence)
            if len(topic.evidence_against) > self.MAX_EVIDENCE_PER_SIDE:
                topic.evidence_against.sort(key=lambda e: e.weight)
                topic.evidence_against.pop(0)
        
        new_stance, new_conf = self.get_stance(topic_id)
        
        # Check for stance shift
        if old_stance != new_stance:
            shift = StanceChange(
                tick=self.current_tick,
                old_stance=old_stance,
                new_stance=new_stance,
                trigger_evidence_id=evidence.evidence_id,
                internal_reasoning=f"Evidence '{evidence.description}' shifted my position."
            )
            topic.history.append(shift)
            
            logger.info(
                f"STANCE SHIFT: {self.agent_id} on '{topic_id}': "
                f"{old_stance.value} -> {new_stance.value}"
            )
            
            return {
                "event_type": "stance_shift",
                "agent_id": self.agent_id,
                "topic_id": topic_id,
                "old_stance": old_stance.value,
                "new_stance": new_stance.value,
                "confidence": new_conf,
                "trigger_evidence": evidence.description
            }
        
        return None
    
    def format_beliefs(self) -> str:
        """Format all beliefs for LLM prompt context."""
        if not self.topics:
            return "BELIEFS: No active belief topics."
        
        parts = ["YOUR CURRENT BELIEFS:"]
        
        for topic_id, topic in self.topics.items():
            stance, confidence = self.get_stance(topic_id)
            readable = stance.to_human_readable(topic.for_label)
            
            parts.append(f"\n  Topic: {topic.topic_name}")
            parts.append(f"  Your Position: {readable} ({confidence:.0%} confident)")
            
            if topic.evidence_for:
                parts.append("  Evidence FOR:")
                for e in sorted(topic.evidence_for, key=lambda x: -x.weight)[:5]:
                    parts.append(f"    [{e.weight:.1f}] {e.description} (source: {e.source_type})")
            
            if topic.evidence_against:
                parts.append("  Evidence AGAINST:")
                for e in sorted(topic.evidence_against, key=lambda x: -x.weight)[:5]:
                    parts.append(f"    [{e.weight:.1f}] {e.description} (source: {e.source_type})")
            
            if topic.history:
                last_shift = topic.history[-1]
                parts.append(f"  [You previously shifted from {last_shift.old_stance.value} at tick {last_shift.tick}]")
        
        return "\n".join(parts)
    
    def format_reflect_instructions(self) -> str:
        """Format instructions for LLM on how to use REFLECT action."""
        return """
If you discover new evidence or reach a new conclusion through reasoning, 
you may update your beliefs using the REFLECT action:
{
  "action": "REFLECT",
  "params": {
    "topic": "defendant_guilt",
    "new_evidence": {
      "description": "Brief description of what you realized",
      "position": "for" or "against",
      "weight": 0.1 to 0.8,
      "source": "reasoning" or "testimony" or "observation"
    }
  }
}
Do NOT use REFLECT unless you genuinely find a new argument compelling.
Your personality and convictions should guide how easily you change your mind.
"""
```

### 7.3 Personality Bias Profiles

| Agent | confirmation_bias | disconfirmation_resistance | social_pressure_immunity | Behavioral Effect |
|-------|-------------------|---------------------------|--------------------------|-------------------|
| The Angry Man | 1.5 | 0.5 | 0.8 | Strongly resists changing his mind. Overvalues confirming evidence. Nearly immune to "everyone else thinks..." |
| The Bank Teller | 1.0 | 1.0 | 0.3 | Neutral weighting. Open to counter-evidence. Highly influenced by group consensus. |
| The Stockbroker | 1.2 | 0.8 | 0.9 | Slight confirmation bias. Moderate resistance to change. Almost immune to social pressure. |
| The Foreman | 1.1 | 0.9 | 0.6 | Slight confirmation bias. Fairly open. Moderate social influence. |

### 7.4 Formal Stance Shifting: The Complete Pipeline

```
1. Agent perceives evidence (EXAMINE reveals hidden_properties, or speech contains argument)
2. LLM deliberation produces REFLECT action with new_evidence
3. AgentBrain._handle_reflect() calls:
   a. BeliefManager.add_evidence(topic_id, evidence, position)
   b. If stance shifts: returns StanceShiftEvent dict
4. StanceShiftEvent is submitted to Fate Engine as a special proposal
5. Fate Engine records it in tick history as event_type="stance_shift"
6. Other agents perceive it via PerceptionPipeline as an EventPercept
7. This triggers reactive deliberation in those agents (social contagion)
8. Those agents may add "social_pressure" evidence to their own BeliefManager
9. → Cascade of stance shifts possible (emergent)
```

---

## 8. Module 6: Formal Action Types

### 8.1 Complete Action Manifest (Phase 2)

| Action | Category | Protobuf Enum Value | Parameters | Preconditions | Fate Engine Resolution |
|--------|----------|---------------------|------------|---------------|----------------------|
| `MOVE` | Navigation | 1 (existing) | `destination: str` | Valid location | Move actor position |
| `INTERACT` | Legacy | 2 (existing) | `target_id, type` | — | Generic interaction |
| `IDLE` | State | 3 (existing) | `duration: str` | None | No-op |
| `EMOTE` | Social | 4 (existing) | `type, message?, emotion?` | None | Speech/gesture |
| `COLLECT` | Object | 5 (existing) | `target_id` | In range, interactive | Item → inventory |
| `USE` | Object | 6 (existing) | `item_id, target_id?` | In inventory | Item-specific effect |
| **`EXAMINE`** | Object | **7 (NEW)** | `target_id` | In vision range, affordance | Reveals hidden_properties |
| **`TAKE`** | Object | **8 (NEW)** | `target_id` | In reach ≤2m, unowned, affordance | Item → inventory |
| **`DROP`** | Object | **9 (NEW)** | `item_id` | In inventory | Object at agent pos |
| **`GIVE`** | Social | **10 (NEW)** | `item_id, recipient_id` | Both in range ≤3m | Transfer ownership |
| **`OPEN`** | Object | **11 (NEW)** | `target_id` | Affordance, preconditions | state → "open" |
| **`READ`** | Object | **12 (NEW)** | `target_id` | Affordance, in range | Text → memory |
| **`REFLECT`** | Internal | **13 (NEW)** | `topic, new_evidence` | None (internal) | Updates belief graph |
| **`VOTE`** | Social | **14 (NEW)** | `topic, position` | Context-specific | Formal stance declaration |

### 8.2 Protobuf Enum Extension (`core.proto`)

```protobuf
enum ActionType {
  ACTION_TYPE_UNSPECIFIED = 0;
  MOVE = 1;
  INTERACT = 2;
  IDLE = 3;
  EMOTE = 4;
  COLLECT = 5;
  USE = 6;
  // Phase 2 additions
  EXAMINE = 7;
  TAKE = 8;
  DROP = 9;
  GIVE = 10;
  OPEN = 11;
  READ = 12;
  REFLECT = 13;
  VOTE = 14;
}
```

### 8.3 LLM Action Output Schema (JSON)

The LLM must return ONE of these action objects:

```json
{
  "thought": "string — internal reasoning (Chain of Thought)",
  "action": "MOVE|IDLE|EMOTE|EXAMINE|TAKE|DROP|GIVE|OPEN|READ|REFLECT|VOTE",
  "params": { ... }
}
```

Parameter schemas per action:

| Action | params schema |
|--------|---------------|
| MOVE | `{"destination": "tavern"}` |
| IDLE | `{"duration": "10"}` |
| EMOTE | `{"type": "speak", "message": "...", "addressed_to": ["juror-2"]}` |
| EXAMINE | `{"target_id": "evidence_knife_01"}` |
| TAKE | `{"target_id": "evidence_knife_01"}` |
| DROP | `{"item_id": "evidence_knife_01"}` |
| GIVE | `{"item_id": "evidence_knife_01", "recipient_id": "juror-1"}` |
| OPEN | `{"target_id": "chest_wood"}` |
| READ | `{"target_id": "evidence_file_01"}` |
| REFLECT | `{"topic": "defendant_guilt", "new_evidence": {"description": "...", "position": "against", "weight": 0.4, "source": "reasoning"}}` |
| VOTE | `{"topic": "defendant_guilt", "position": "not_guilty"}` |

---

## 9. Fate Engine Modifications

### 9.1 New Resolution Methods

The following methods are added to `FateEngine` class in `proto/fate_engine.py`:

```python
# In _resolve_proposal(), add new action type handling:

async def _resolve_proposal(self, proposal):
    actor_id = proposal.actor_id
    if actor_id not in self.world_state.actors:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=actor_id,
            success=False,
            reason="Actor not found"
        )
    
    actor = self.world_state.actors[actor_id]
    
    match proposal.action:
        # Existing actions (unchanged)
        case core_pb2.ActionType.MOVE: return await self._resolve_move(proposal, actor)
        case core_pb2.ActionType.INTERACT: return await self._resolve_interact(proposal, actor)
        case core_pb2.ActionType.IDLE: ...  # existing
        case core_pb2.ActionType.EMOTE: return await self._resolve_emote_v2(proposal, actor)
        case core_pb2.ActionType.COLLECT: return await ActionResolver.resolve_collect(...)
        case core_pb2.ActionType.USE: return await ActionResolver.resolve_use(...)
        
        # NEW Phase 2 actions
        case core_pb2.ActionType.EXAMINE: return await self._resolve_examine(proposal, actor)
        case core_pb2.ActionType.TAKE: return await self._resolve_take(proposal, actor)
        case core_pb2.ActionType.DROP: return await self._resolve_drop(proposal, actor)
        case core_pb2.ActionType.GIVE: return await self._resolve_give(proposal, actor)
        case core_pb2.ActionType.OPEN: return await self._resolve_open(proposal, actor)
        case core_pb2.ActionType.READ: return await self._resolve_read(proposal, actor)
        case core_pb2.ActionType.REFLECT: return await self._resolve_reflect(proposal, actor)
        case core_pb2.ActionType.VOTE: return await self._resolve_vote(proposal, actor)
```

### 9.2 EXAMINE Resolution

```python
async def _resolve_examine(self, proposal, actor):
    target_id = proposal.parameters.get("target_id")
    if not target_id or target_id not in self.world_state.objects:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason="Object not found"
        )
    
    obj = self.world_state.objects[target_id]
    
    # Check EXAMINE affordance
    has_examine = any(
        a.action_type == "EXAMINE" 
        for a in getattr(obj, 'affordances', [])
    )
    # For Phase 1 objects without affordances, allow EXAMINE on interactive objects
    if not has_examine and not obj.interactive:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason="Cannot examine this object"
        )
    
    # Distance check
    dist = ((actor.position.x - obj.position.x)**2 + 
            (actor.position.y - obj.position.y)**2)**0.5
    if dist > 10.0:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason=f"Too far to examine (dist={dist:.1f}m)"
        )
    
    # Success: return hidden properties + visible properties
    revealed = dict(getattr(obj, 'hidden_properties', {}))
    revealed.update(dict(obj.properties))
    
    return core_pb2.Resolution(
        proposal_id=proposal.proposal_id, actor_id=actor.id,
        success=True,
        outcome={
            "action": "examine",
            "object_id": target_id,
            "object_name": getattr(obj, 'display_name', obj.type),
            **{f"revealed_{k}": v for k, v in revealed.items()}
        }
    )
```

### 9.3 TAKE Resolution (with conflict detection)

```python
async def _resolve_take(self, proposal, actor):
    target_id = proposal.parameters.get("target_id")
    obj = self.world_state.objects.get(target_id)
    
    if not obj:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason="Object not found"
        )
    
    # Check ownership
    owner_id = getattr(obj, 'owner_id', '')
    if owner_id and owner_id != actor.id:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason="Object owned by another actor"
        )
    
    # Distance check (reach range)
    dist = ((actor.position.x - obj.position.x)**2 + 
            (actor.position.y - obj.position.y)**2)**0.5
    if dist > 2.0:
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id, actor_id=actor.id,
            success=False, reason="Too far to reach"
        )
    
    return core_pb2.Resolution(
        proposal_id=proposal.proposal_id, actor_id=actor.id,
        success=True,
        outcome={
            "action": "take",
            "object_id": target_id,
            "object_type": obj.type
        }
    )
```

### 9.4 REFLECT Resolution (Internal — always succeeds)

```python
async def _resolve_reflect(self, proposal, actor):
    """Internal cognitive action. Always succeeds. Not broadcast to others."""
    return core_pb2.Resolution(
        proposal_id=proposal.proposal_id, actor_id=actor.id,
        success=True,
        outcome={
            "action": "reflect",
            "topic": proposal.parameters.get("topic", ""),
            "evidence_description": proposal.parameters.get("description", ""),
            "evidence_position": proposal.parameters.get("position", ""),
            "evidence_weight": proposal.parameters.get("weight", "0.3"),
            "internal": "true"  # Flag: perception layer should not broadcast
        }
    )
```

### 9.5 Enhanced EMOTE (Speech Pipeline)

```python
async def _resolve_emote_v2(self, proposal, actor):
    """Enhanced EMOTE with first-class speech events."""
    emote_type = proposal.parameters.get("type", "gesture")
    
    outcome = {
        "action": "emote",
        "emote_type": emote_type
    }
    
    if emote_type == "speak":
        message = proposal.parameters.get("message", "")
        addressed_to = proposal.parameters.get("addressed_to", "")
        
        outcome["message"] = message
        outcome["speaker_name"] = actor.name
        outcome["addressed_to"] = addressed_to
        outcome["loudness"] = proposal.parameters.get("loudness", "0.7")
        
        # Add to pending speech events for PerceptionPipeline
        # (stored in TickState for downstream processing)
    
    return core_pb2.Resolution(
        proposal_id=proposal.proposal_id, actor_id=actor.id,
        success=True,
        outcome=outcome
    )
```

### 9.6 `_apply_outcome()` Extensions

```python
# Add to the existing _apply_outcome method:

elif outcome.get("action") == "take":
    obj_id = outcome.get("object_id")
    if obj_id in self.world_state.objects:
        actor.inventory.append(obj_id)
        del self.world_state.objects[obj_id]
        logger.info(f"Actor {actor.name} took {obj_id}")

elif outcome.get("action") == "drop":
    item_id = outcome.get("item_id")
    if item_id in actor.inventory:
        actor.inventory.remove(item_id)
        # Re-create object at actor's position
        self.world_state.objects[item_id].CopyFrom(core_pb2.EnvironmentObject(
            id=item_id, type="dropped_item",
            position=actor.position, interactive=True
        ))

elif outcome.get("action") == "examine":
    pass  # No world state change; info returned in resolution

elif outcome.get("action") == "reflect":
    pass  # Internal only; no world state change
```

---

## 10. PerceptionPipeline Fixes & Enhancements

### 10.1 Bug Fix: `math.random()` (CRITICAL)

**File:** `brain/PerceptionPipeline.py`, line 643-644

**Current (buggy):**
```python
x=position.x + (math.random() - 0.5) * noise,
y=position.y + (math.random() - 0.5) * noise
```

**Fixed:**
```python
x=position.x + (random.random() - 0.5) * noise,
y=position.y + (random.random() - 0.5) * noise
```

`math.random()` does not exist in Python. This would throw `AttributeError` at runtime. The `random` module is already imported at line 17.

### 10.2 Enhancement: Emotional State Integration

Add `StateManager` awareness to perception processing:

```python
def process(self, world_state, agent_internal_state, current_tick, 
            emotional_modifiers=None):
    """Enhanced with emotional state modifiers."""
    # ... existing code ...
    
    # Apply emotional attention narrowing
    if emotional_modifiers:
        max_percepts = emotional_modifiers.get("attention_width", 7)
        threat_boost = emotional_modifiers.get("threat_salience_boost", 0.0)
        
        # Boost threat-related percepts
        if threat_boost > 0:
            for p in percepts:
                if hasattr(p, 'event') and p.HasField('event'):
                    if p.event.event_type in ("attack", "threat", "violence"):
                        p.salience = min(1.0, p.salience + threat_boost)
        
        # Narrow attention window
        percepts = percepts[:max_percepts]
    
    return percepts
```

### 10.3 Enhancement: Speech Event Extraction

The current `_extract_speech_content()` returns `"speech detected"` as placeholder. Enhance to extract actual dialogue from TickState resolutions:

```python
def process_with_tick_state(self, world_state, tick_state, agent_internal_state, 
                            current_tick, emotional_modifiers=None):
    """Enhanced process that also reads speech from resolutions."""
    percepts = self.process(world_state, agent_internal_state, current_tick, 
                           emotional_modifiers)
    
    # Extract speech events from resolutions
    for res in tick_state.resolutions:
        if res.outcome.get("action") == "emote" and res.outcome.get("message"):
            if res.actor_id != self.agent_id:
                speaker = world_state.actors.get(res.actor_id)
                if speaker:
                    my_pos = world_state.actors.get(self.agent_id)
                    if my_pos:
                        dist = self._distance(my_pos.position, speaker.position)
                        loudness = float(res.outcome.get("loudness", "0.7"))
                        if dist <= self.profile.hearing_range * loudness:
                            content = res.outcome.get("message", "")
                            percepts.append(perception_pb2.Percept(
                                percept_id=str(uuid.uuid4()),
                                tick_observed=current_tick,
                                channel=perception_pb2.Percept.HEARING,
                                speech=perception_pb2.SpeechPercept(
                                    speaker_id=res.actor_id,
                                    speaker_name=speaker.name,
                                    content=content,
                                    loudness=loudness,
                                    is_direct_address=self.agent_id in 
                                        res.outcome.get("addressed_to", "")
                                ),
                                salience=self._calculate_speech_salience(
                                    content, agent_internal_state, 1.0
                                ),
                                certainty=1.0
                            ))
    
    percepts.sort(key=lambda p: p.salience, reverse=True)
    return percepts
```

---

## 11. Protobuf Schema Changes

### 11.1 `core.proto` — Summary of Changes

```diff
 enum ActionType {
   ACTION_TYPE_UNSPECIFIED = 0;
   MOVE = 1;
   INTERACT = 2;
   IDLE = 3;
   EMOTE = 4;
   COLLECT = 5;
   USE = 6;
+  EXAMINE = 7;
+  TAKE = 8;
+  DROP = 9;
+  GIVE = 10;
+  OPEN = 11;
+  READ = 12;
+  REFLECT = 13;
+  VOTE = 14;
 }

 message EnvironmentObject {
   string id = 1;
   string type = 2;
   tsukuyomi.common.Vector2 position = 3;
   bool interactive = 4;
   map<string, string> properties = 5;
+  string display_name = 6;
+  repeated Affordance affordances = 7;
+  map<string, string> hidden_properties = 8;
+  string state = 9;
+  string owner_id = 10;
 }

+message Affordance {
+  string action_type = 1;
+  string precondition = 2;
+  string effect_description = 3;
+  repeated string semantic_tags = 4;
+}
```

### 11.2 New File: `proto/belief.proto`

```protobuf
syntax = "proto3";
package tsukuyomi.belief;

message StanceShiftEvent {
  string agent_id = 1;
  string agent_name = 2;
  string topic_id = 3;
  string old_stance = 4;
  string new_stance = 5;
  string visible_expression = 6;
  float confidence = 7;
}
```

### 11.3 `perception.proto` — No structural changes needed

The existing schema supports all Phase 2 perception requirements. The `EventPercept` message can carry `stance_shift` events through the `event_type` and `details` fields.

---

## 12. Agent Profile Schema v2

### 12.1 Eliminating Static Stances

**Before (Phase 1):**
```json
{
  "name": "The Bank Teller",
  "stance": "guilty",          // ← HARDCODED, NEVER CHANGES
  "backstory": "...",
  "traits": {"conscientiousness": 0.6}
}
```

**After (Phase 2):**
```json
{
  "name": "The Bank Teller",
  "actor_id": "juror-2",
  "backstory": "A meek and unpretentious bank teller. You are easily flustered by strong opinions. Initially, you follow the majority but you have questions about the timing of the events.",
  
  "personality_baseline": {
    "valence_baseline": 0.1,
    "arousal_baseline": 0.3,
    "dominance_baseline": -0.4,
    "regression_rate": 0.02
  },
  
  "personality_bias": {
    "confirmation_bias": 1.0,
    "disconfirmation_resistance": 1.0,
    "social_pressure_immunity": 0.3
  },
  
  "sensory_profile": {
    "vision_range": 20.0,
    "vision_fov": 120,
    "hearing_range": 15.0
  },
  
  "initial_beliefs": {
    "defendant_guilt": {
      "topic_name": "Is the defendant guilty?",
      "for_label": "guilty",
      "evidence_for": [
        {"description": "Eyewitness saw the stabbing", "weight": 0.8, "source_type": "testimony"},
        {"description": "Boy owned a similar knife", "weight": 0.4, "source_type": "physical_evidence"}
      ],
      "evidence_against": []
    }
  },
  
  "deliberation_offset": 14,
  "reactive_threshold": 0.7
}
```

**Key change:** `"stance"` field is REMOVED. Stance is now *derived* from `initial_beliefs` through `BeliefManager.get_stance()`. The Bank Teller starts with evidence_for totaling 1.2 and evidence_against at 0.0 — so his initial derived stance is `LEANING_FOR` ("Leaning guilty"). But this can change.

---

## 13. LLM Prompt Architecture

### 13.1 Full Phase 2 Prompt Template

```
=== TSUKUYOMI COGNITIVE FRAME ===

IDENTITY:
You are {profile.name}.
{profile.backstory}

INTERNAL STATE:
Mood: {state_manager.mood_label} 
  (Valence: {state_manager.valence:.2f}, Arousal: {state_manager.arousal:.2f})
{state_manager.get_emotional_modifier()}

{belief_manager.format_beliefs()}

{working_memory.to_llm_context()}

AVAILABLE ACTIONS:
- EMOTE(type="speak", message="...", addressed_to=["juror-2"]) — Speak to others
- EXAMINE(target_id) — Study an object in detail to learn hidden properties
- TAKE(target_id) — Pick up an object within reach
- READ(target_id) — Read a document
- REFLECT(topic, new_evidence) — Update your beliefs based on new reasoning
- MOVE(destination) — Walk to a location
- IDLE(duration) — Wait and observe

VISIBLE OBJECTS:
{perception.format_objects_with_affordances()}

DELIBERATION TRIGGER: {reason}

INSTRUCTIONS:
Based on your identity, emotional state, beliefs, and current perceptions, decide your next action.
{belief_manager.format_reflect_instructions()}
Your response must be ONLY valid JSON. No markdown, no explanation outside JSON.

RESPONSE FORMAT:
{{
  "thought": "your internal reasoning",
  "action": "ACTION_TYPE",
  "params": {{...}}
}}
```

### 13.2 Token Budget Analysis

| Section | Estimated Tokens | Notes |
|---------|-----------------|-------|
| Identity + Backstory | ~100 | Fixed per agent |
| Internal State | ~50 | Dynamic mood |
| Beliefs | ~200 | 2-3 topics, 5 evidence each |
| Working Memory | ~300 | 7 slots, mixed content |
| Available Actions | ~150 | Fixed |
| Visible Objects | ~100 | 2-3 objects with affordances |
| Instructions | ~100 | Fixed |
| **Total Input** | **~1000** | Well within Gemini limits |
| **Expected Output** | ~100 | JSON action + thought |

---

## 14. Integration Map: What Changes Where

### 14.1 New Files (5)

| File | Module | Lines (est.) | Dependencies |
|------|--------|--------------|--------------|
| `brain/StateManager.py` | Emotional Core | ~250 | None (pure Python) |
| `brain/WorkingMemory.py` | Memory Hydration | ~200 | MemoryManager, PerceptionPipeline |
| `brain/BeliefManager.py` | Stance Dynamics | ~300 | None (pure Python) |
| `proto/belief.proto` | Stance Events | ~15 | common.proto |
| `experiments/profiles/juror_profiles_v2.json` | Updated Profiles | ~150 | — |

### 14.2 Modified Files (7)

| File | Changes | Scope |
|------|---------|-------|
| `brain/AgentBrain.py` | Add StateManager, WorkingMemory, BeliefManager initialization. Modify `_process_tick()` for perception + reactive triggers. Modify `_deliberate()` for enhanced context. Add `_handle_reflect()`. | **MAJOR** — ~60% rewrite |
| `brain/MemoryManager.py` | Add `emotional_intensity`, `relevance_score`, `decay_rate` to entries. Add `query_by_relevance()`. Add `tick_decay()`. | **MODERATE** — ~30 new lines |
| `brain/LLMService.py` | Add `generate_plan_v2()` with enhanced prompt template. Keep existing `generate_plan()` for backward compat. | **MODERATE** — ~50 new lines |
| `brain/PerceptionPipeline.py` | Bug fix `math.random()`. Add emotional modifier support. Add speech extraction from resolutions. | **MINOR** — ~30 lines changed |
| `proto/core.proto` | Add ActionType enums 7-14. Extend EnvironmentObject with fields 6-10. Add Affordance message. | **MODERATE** — ~20 new lines |
| `proto/fate_engine.py` | Add resolution methods for EXAMINE, TAKE, DROP, GIVE, OPEN, READ, REFLECT, VOTE. Extend `_apply_outcome()`. | **MAJOR** — ~200 new lines |
| `proto/action_logic.py` | Potentially move new resolvers here for cleanliness. | **OPTIONAL** |

### 14.3 Files NOT Changed

| File | Reason |
|------|--------|
| `proto/grpc_server.py` | gRPC stream protocol unchanged |
| `proto/grpc_client.py` | Client API unchanged |
| `proto/db_manager.py` | Persistence format unchanged (MessageToJson handles new fields) |
| `simulation_loop.py` | Legacy; not used in experiments |
| `reflex_layer.py` | Legacy; not used in experiments |

---

## 15. Implementation Roadmap

### Phase 2.1: Foundations — Perception Fix + StateManager (Week 1)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.1.1 | Fix `math.random()` bug in PerceptionPipeline | `brain/PerceptionPipeline.py` L643-644 | Unit test blur_position |
| 2.1.2 | Implement StateManager with PAD model | `brain/StateManager.py` (NEW) | Unit: update(), mood derivation |
| 2.1.3 | Create personality baselines for 4 jurors | In StateManager or profiles | Assertion tests |
| 2.1.4 | Wire StateManager into AgentBrain.__init__ | `brain/AgentBrain.py` | Integration |
| **Milestone** | Agents have dynamic emotions that update each tick | | |

### Phase 2.2: Memory Hydration (Week 2)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.2.1 | Implement WorkingMemory class | `brain/WorkingMemory.py` (NEW) | Unit: refresh(), slot limits |
| 2.2.2 | Add emotional tags + relevance decay to MemoryManager | `brain/MemoryManager.py` | Unit: tick_decay(), query_by_relevance |
| 2.2.3 | Wire WorkingMemory into deliberation flow | `brain/AgentBrain.py` | Integration |
| **Milestone** | Agents recall relevant memories, not just recent ones | | |

### Phase 2.3: Belief Dynamics (Week 3)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.3.1 | Implement BeliefManager class | `brain/BeliefManager.py` (NEW) | Unit: add_evidence, get_stance, stance shift |
| 2.3.2 | Create v2 juror profiles with initial_beliefs | `experiments/profiles/juror_profiles_v2.json` | Load test |
| 2.3.3 | Wire BeliefManager into AgentBrain | `brain/AgentBrain.py` | Integration |
| 2.3.4 | Add REFLECT action handling in AgentBrain | `brain/AgentBrain.py` | E2E: LLM produces REFLECT |
| **Milestone** | Agent stance can shift from evidence accumulation | | |

### Phase 2.4: Object Affordances + New Actions (Week 4)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.4.1 | Extend core.proto with new ActionTypes + Affordance | `proto/core.proto` | Proto compile |
| 2.4.2 | Regenerate proto bindings | `proto/*_pb2.py` | Import test |
| 2.4.3 | Implement EXAMINE, TAKE, DROP, READ resolvers | `proto/fate_engine.py` | Unit per resolver |
| 2.4.4 | Implement REFLECT, VOTE resolvers | `proto/fate_engine.py` | Unit |
| 2.4.5 | Extend _apply_outcome() for new actions | `proto/fate_engine.py` | Integration |
| 2.4.6 | Create test evidence objects (switchblade, case file) | Scenario config | Load test |
| **Milestone** | Agents can EXAMINE objects and discover hidden properties | | |

### Phase 2.5: Reactive Deliberation + Enhanced Prompt (Week 5)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.5.1 | Add reactive trigger detection to _process_tick | `brain/AgentBrain.py` | Unit: trigger classification |
| 2.5.2 | Implement preemption (simple cancel flag) | `brain/AgentBrain.py` | Async test |
| 2.5.3 | Implement `generate_plan_v2()` with Phase 2 prompt | `brain/LLMService.py` | Manual test |
| 2.5.4 | Add speech extraction from resolutions | `brain/PerceptionPipeline.py` | Unit |
| **Milestone** | Agents respond to direct address within one deliberation cycle | | |

### Phase 2.6: Integration & Validation — "12 Angry Men v2" (Week 6-7)

| Task | Description | Files | Test |
|------|-------------|-------|------|
| 2.6.1 | Create `angry_man_v2.py` scenario | `experiments/scenarios/angry_man_v2.py` | Manual run |
| 2.6.2 | Create v2 evidence objects | Scenario config | — |
| 2.6.3 | Run full simulation (target: 30min, 36000 ticks) | — | Observation |
| 2.6.4 | Analyze: Did at least one juror change stance? | CoT + belief logs | — |
| 2.6.5 | Performance profiling: 20 TPS maintained? | — | Metric |
| 2.6.6 | Write experiment report | `experiments/reports/` | — |
| **MILESTONE** | **Phase 2 COMPLETE. At least one juror changes vote.** | | |

---

## 16. Risk Analysis & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| **R1** | LLM context overflow (prompt too large) | Medium | High | WorkingMemory caps at 7 slots. Total prompt ~1000 tokens. |
| **R2** | Perception pipeline O(A²) per tick | Medium | Medium | Staggered perception (already implemented). Deep perception every 3 ticks. |
| **R3** | Memory decay kills the 50ms tick budget | Medium | Medium | Run `tick_decay()` every 10 ticks, not every tick. Batch 10% of memories. |
| **R4** | LLM produces invalid action JSON | High | Medium | Existing JSON extraction + fallback to IDLE (already in LLMService). Add validation for new action types. |
| **R5** | Emotional state oscillates wildly | Medium | Low | Regression to baseline. Arousal-scaled volatility. Max episode cap. |
| **R6** | Belief graph grows unbounded | Low | Medium | Cap evidence at 20 per side per topic. Prune lowest-weight. |
| **R7** | Reactive deliberation floods LLM API | Medium | High | Same semaphore (1) + cooldown (2.5s). Reactive just enters the queue. |
| **R8** | EXAMINE reveals all secrets instantly | Low | Medium | Can add "partial reveal" — each EXAMINE reveals subset of hidden_properties. |
| **R9** | No agents ever shift stance (LLM conservatism) | Medium | High | The REFLECT instruction prompt explicitly permits belief change. Initial evidence is not overwhelming (FOR = 1.2, AGAINST = 0). Tanit can inject strong counter-evidence. |
| **R10** | Protobuf recompilation breaks existing tests | Medium | Medium | Phase 2.4 task explicitly includes proto recompilation + import verification. |

---

## 17. Validation Criteria

### 17.1 Phase 2 is COMPLETE when:

1. **Emotional Dynamics:** The Angry Man's arousal measurably increases when contradicted (visible in StateManager logs). The Bank Teller's dominance drops when socially pressured.

2. **Working Memory Bounds:** No LLM prompt exceeds 2000 tokens. Working memory never exceeds 9 slots (7 + 2 Miller tolerance).

3. **Object Interaction:** At least one agent successfully EXAMINEs the switchblade and the revealed `uniqueness: "NOT unique"` appears in their semantic memory.

4. **Stance Shift (THE KEY METRIC):** At least one juror's stance changes from their initial position (e.g., Bank Teller goes from `LEANING_FOR` to `NEUTRAL` or `LEANING_AGAINST`) based on accumulated evidence. This must be a formal `StanceChange` event in the `BeliefManager.history`, not just a textual expression of doubt.

5. **Reactive Deliberation:** When Tanit directly addresses an agent, the response occurs within the next 2 deliberation cycles (≤5 seconds), regardless of the agent's proactive schedule.

6. **20 TPS Stability:** The Fate Engine maintains 20 TPS (±10%) throughout a 30-minute simulation with 4 native agents + 1 guest agent + StateManager + WorkingMemory + BeliefManager active.

7. **Deterministic Replay:** A simulation replayed from the event ledger (with LLM bypass, reading committed actions) produces the same final world state hash.

### 17.2 The "12 Angry Men v2" Success Scenario

```
Setup:
  - 4 LLM jurors (Foreman, Bank Teller, Angry Man, Stockbroker)
  - 1 Guest (Tanit)
  - Evidence table with: switchblade, case file
  - Initial stances: all LEANING_FOR (guilty)
  - Duration: 30 minutes (36,000 ticks)

Expected Outcome:
  1. Jurors deliberate, building initial agreement
  2. Tanit injects probes (timing, glasses, knife store)
  3. Bank Teller EXAMINEs switchblade → discovers "NOT unique"
  4. Bank Teller REFLECTs → adds evidence_against → stance shifts to NEUTRAL
  5. Angry Man's arousal spikes → tunnel vision → refuses to REFLECT
  6. Stockbroker EXAMINEs case file → discovers train timing conflict
  7. Stockbroker may REFLECT or double down (personality: analytical)
  8. Social contagion: Bank Teller's shift triggers reactive deliberation in others
  9. Final state: mixed stances. NOT unanimously guilty.

This would prove Phase 2's core thesis: that agents can genuinely change their
minds through evidence accumulation, not just express scripted doubt.
```

---

## Conclusion

Phase 2 transforms Tsukuyomi from a dialogue simulator into a cognitive sandbox. The five new modules — **StateManager**, **WorkingMemory**, **BeliefManager**, **Object Affordances**, and **Reactive Deliberation** — work together to close the gaps identified in the Angry Man Room experiment:

| Phase 1 Gap | Phase 2 Solution | Verification |
|-------------|-----------------|--------------|
| Static stances | BeliefManager with evidence-weighted stance calculation | StanceChange events in logs |
| No object interaction | Affordance system with EXAMINE/TAKE/READ | Hidden properties in semantic memory |
| Omniscient perception | PerceptionPipeline (fixed + enhanced) | Information asymmetry between agents |
| Flat emotional model | StateManager with PAD vectors | Mood label changes in CoT logs |
| Undifferentiated memory | WorkingMemory with Miller's Law bounds | Relevance-based recall in prompts |
| Only proactive deliberation | Reactive triggers for direct address/threats | Response time to Tanit's probes ≤5s |

The specification is implementation-ready. Each module has concrete class definitions, integration points identified by file and line number, protobuf schema diffs, and testable validation criteria.

The moon reads. The jury deliberates. And this time, they can change their minds.

---

**Specification Finalized.**
*Tsukuyomi Phase 2: The Cognitive Core — Opus 4.6*
*Lead Architect: Opus 4 (Claude)*
*Commissioned by: Tanit & Safouane*
