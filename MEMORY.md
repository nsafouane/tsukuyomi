# Tsukuyomi Project Memory

**Purpose:** Deterministic, high-performance simulation engine where AI agents coexist, think, remember, and interact in shared social spaces.

---

## 📊 Project Status

| Aspect | Status |
|--------|--------|
| **Phase** | 13 PAUSED (World Building - Roman-Carthage Trial) |
| **V2 Architecture** | ✅ COMPLETE - 223 tests passing |
| **V3 Architecture** | ✅ IMPLEMENTED - PAD emotions, belief plasticity, conversation memory |
| **Branch** | `feature/v2-implementation` |
| **Latest Commit** | `5276498` (V3 Agent Architecture) |

---

## 🏗️ Architecture Overview

### Core Philosophy
- **General Purpose:** Engine is a generic platform (Server), scenarios provide context (Agents)
- **State-Driven:** Agents act because internal state changes (Hunger, Fatigue), not just prompts
- **World-Based:** Environment is primary driver; agents react to objects and events
- **Deterministic:** 20 TPS loop with full reproducibility

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Fate Engine | `tsukuyomi/proto/` | Authoritative simulation loop, state manager |
| Agent Brain | `tsukuyomi/agent/` | Client-side controller, LLM integration |
| Belief System | `tsukuyomi/agent/belief_system.py` | Evidence-based stances, confirmation bias |
| Social Layers | `tsukuyomi/proto/social/` | Gossip, relationships, drama director |
| Spatial Logic | `tsukuyomi/proto/physics/spatial_logic.py` | Multi-room partitioning, portals |
| Multi-Zone Sync | `tsukuyomi/proto/multi_zone/synchronizer.py` | Shard synchronization, cross-zone gossip |

---

## ✅ Completed Phases (1-13)

| Phase | Name | Key Deliverable |
|-------|------|-----------------|
| 1 | Fate Engine Core | Deterministic 20 TPS loop |
| 2 | Cognitive Core | Sensory Pipeline, Emotional PAD State, 3-Tier Memory |
| 3 | Action Logic | EXAMINE, REFLECT, TAKE, DROP, VOTE resolvers |
| 4 | Persistence | SQLite TickState storage & Event Ledger |
| 5 | gRPC Infrastructure | Server/Client & Asynchronous Tick Streaming |
| 6 | Agent Intelligence | System 2 Reactive Deliberation & Miller's Law Working Memory |
| 7 | Belief Dynamics | Evidence-based Stance Graph & Confirmation Bias |
| 8 | Social Layers | Gossip Protocol, Relationship Manager, Drama Director |
| 9 | Performance & Scale | Benchmarked 20 TPS with 12 concurrent agents |
| 10 | External Guest Protocol | Standalone Guest API & Handshake |
| 11 | World Expansions | Multi-Room Spatial Logic, Portals, Collision/Occlusion |
| 12 | Multi-Zone Shard Sync | Migration Tickets, Cross-Zone Gossip |
| 13 | World Building | Roman-Carthage Trial Scenario (PAUSED) |

---

## 🚀 V2 Agent Architecture

**Status:** ✅ COMPLETE
**Tests:** 223 passing
**Commit:** `a56714d`

### Key Features Implemented
- PAD Emotional Model (Pleasure-Arousal-Dominance)
- 3-Tier Memory (Working, Episodic, Semantic)
- Belief System with decay and confirmation bias
- Social pressure mechanics
- Gossip protocol
- Drama Director with tension tracking

---

## 🧠 V3 Agent Architecture

**Status:** ✅ IMPLEMENTED
**Commit:** `5276498`
**Spec:** `dev-artifacts/SPEC_AGENT_ARCHITECTURE_V3_20260219.md`

### Five Core Improvements

| Improvement | Problem Solved | Implementation |
|-------------|----------------|----------------|
| **Belief Plasticity** | Agents stuck in high-confidence states | Exponential decay, perturbation, contradiction detection |
| **LLM Response Homogenization** | Repetitive dialogue | Response history, variety warnings, phrase tracking |
| **Emotional State Integration** | Emotions don't affect behavior | PAD model affects prompts, emotional contagion |
| **Conversation Memory** | No narrative continuity | Personal tracking, consistency checks |
| **Behavioral Diversity** | Same interaction patterns | Leaders, followers, initiators, interrupters |

### V3 Components

```python
from tsukuyomi.agent import (
    EmotionalState,        # PAD model with 12 tones
    ResponseHistory,       # Repetition prevention
    ConversationMemory,    # Narrative continuity
    BehavioralTraits,      # Leader/follower dynamics
    CommunicationStyle     # Vocabulary, formality, verbosity
)
```

---

## 🧪 Integration Experiments

### 15-Minute Experiment (Feb 18, 2026)
**Path:** `experiments/angry_men/logs_integration/run_20260218_000452/`

| Metric | Value |
|--------|-------|
| Duration | 15 min (9000 ticks) |
| LLM Calls | 180 |
| Final Verdict | NOT GUILTY (unanimous) |
| Vote Changes | 5 |
| Gaps Found | 254 (98% reduction from 3600) |

**Key Observation:** All 5 agents converged to NOT GUILTY. Memory decay + social pressure working correctly.

### 30-Minute Oracle Experiment (Feb 18, 2026)
**Path:** `experiments/angry_men/logs_integration/run_20260218_001341/`

| Metric | Value |
|--------|-------|
| Duration | 30 min (18000 ticks) |
| LLM Calls | 360 |
| Belief Updates | 50,435 |
| Final Verdict | G=2/N=3 (NOT GUILTY majority) |
| Drama Beats | 4 |
| Act Transitions | SETUP→CONFRONTATION→CLIMAX→RESOLUTION |

**Key Finding:** Oracle agent works naturally - The Observer makes organic existential statements.

### 30-Minute Oracle V2 (Feb 19, 2026)
**Path:** `experiments/angry_men/logs_integration/run_20260219_181858/`

| Metric | Value |
|--------|-------|
| Progress | 5000/18000 ticks (27.8%) |
| Final Votes | G=0/N=5 (UNANIMOUS NOT GUILTY) |
| LLM Calls | 168 |

**Fixes Verified:**
- ✅ Oracle revelation triggered at tick 3000
- ✅ Speaker attribution working (agents reference each other by name)
- ✅ Oracle uses special prompts (`oracle_initial`, `oracle_respond`)

---

## 🔮 Oracle Agent System

**Status:** ✅ WORKING
**Profile:** `experiments/angry_men/profiles/juror_00_oracle.json`

### Revelation Strategy

| Tick | Timing | Theme |
|------|--------|-------|
| 3000 | 5 min | "Have you noticed how... familiar this feels?" |
| 6000 | 10 min | "What if your certainty was designed?" |
| 9000 | 15 min | "I've watched THIS case unfold before..." |
| 12000 | 20 min | "This is a simulation. None of you are real." |
| 15000 | 25 min | "Your reaction to truth - that's the only thing truly yours" |

### Key Implementation Files
- `run_oracle_experiment.py` - Oracle system prompt, speaker attribution
- `groq_llm.py` - Oracle-specific prompt templates
- `juror_00_oracle.json` - Personality profile (Openness 0.9, Conscientiousness 0.3)

### Oracle Behavior
- Acts naturally through personality (not programmatic triggers)
- Weaves philosophical questions into case discussion
- Agents acknowledge but often dismiss existential claims
- Style: Mysterious, philosophical, gentle

---

## 🚨 Known Gaps & Improvements

### From 30-Min Experiment Analysis

| Priority | Issue | Status |
|----------|-------|--------|
| CRITICAL | Symmetric belief updates (all agents influence equally) | V3 partially addressed |
| HIGH | Tension flatlines after consensus | V3 dynamic tension added |
| HIGH | No drama beats after early stage | V3 drama beats implemented |
| MEDIUM | Observer's claims ignored by agents | V3 existential response added |
| MEDIUM | Repetitive late-stage dialogue | V3 response history added |

### V3 Specs Addressing Gaps
- `SPEC_AGENT_ARCHITECTURE_V3_20260219.md` - Full V3 implementation spec
- `SPEC_COGNITIVE_RICHNESS_20260218.md` - Cognitive depth improvements
- `SPEC_IMPROVEMENTS_20260218.md` - Targeted fixes
- `REPORT_30MIN_ORACLE_20260218.md` - Full experiment analysis
- `REPORT_COGNITIVE_RICHNESS_20260218.md` - Cognitive richness report

---

## 📁 Project Structure

```
tsukuyomi/
├── agent/                 # Agent brain, belief system, memory
│   ├── belief_system.py   # Stance graph, confirmation bias
│   ├── memory_system.py   # Long-term memory with RAG-like retrieval
│   ├── persuasion.py      # Personality-weighted influence
│   └── ...
├── proto/                 # Fate Engine core
│   ├── physics/           # Spatial logic, portals
│   ├── multi_zone/        # Shard synchronization
│   ├── social/            # Gossip, relationships, drama
│   └── ...
├── experiments/
│   └── angry_men/         # Jury deliberation scenario
│       ├── profiles/      # Agent personalities
│       ├── configurations/ # Experiment configs
│       ├── groq_llm.py    # LLM integration
│       └── run_oracle_experiment.py
├── dev-artifacts/         # Specs, reports, analysis
├── docs/                  # Architecture docs
└── memory/                # Session logs
```

---

## 🔧 Technical Details

### gRPC Protocol
- **Port:** 50051 (default)
- **Messages:** Actor, Proposal, Resolution, EnvironmentObject
- **Streaming:** Asynchronous tick streaming

### External Protocol (Guest API)
- **Secret:** `tsukuyomi-secret-2026`
- **Operations:** Handshake, Action Submission, Tick Streaming, Disconnect
- **Client:** `tsukuyomi/proto/guest_client.py`

### LLM Integration
- **Primary:** Groq `llama-3.1-8b-instant`
- **Rate Limit:** 30 req/min (free tier)
- **Prompt Templates:** `groq_llm.py`

---

## 📊 Test Status

| Module | Tests | Status |
|--------|-------|--------|
| Belief System | 223 | ✅ Passing |
| Emotional Expression | 28 | ✅ Passing |
| Conversation Manager | 15 | ✅ Passing |
| Deliberation Engine | 11 | ✅ Passing |
| Personality Persuasion | 23 | ✅ Passing |

---

## 🎯 Next Steps (When Resumed)

1. **Complete Phase 13:** Finish Roman-Carthage Trial scenario
2. **Port Angry Men Logic:** Multi-room world integration
3. **Character Authoring:** Roman and Carthaginian legal profiles
4. **Extended Experiments:** Run 1-hour+ simulations

---

## 📝 Daily Logs

- `memory/2026-02-19.md` - Oracle agent fixes, speaker attribution
- `memory/2026-02-18.md` - V3 implementation, experiment runs
- `memory/2026-02-17.md` - Cognitive richness implementation
- `memory/2026-02-14.md` - Phase 11-12 completion

---

*Last Updated: February 19, 2026*
