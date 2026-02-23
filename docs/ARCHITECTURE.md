# Tsukuyomi Architecture

**Version:** 1.0
**Date:** 2026-02-22
**Status:** Restructured MVP v0.1

---

## Table of Contents

1. [Introduction](#introduction)
2. [Design Philosophy](#design-philosophy)
3. [System Architecture](#system-architecture)
4. [Core Principles](#core-principles)
5. [System Components](#system-components)
6. [Data Flow](#data-flow)
7. [Deployment Modes](#deployment-modes)
8. [Technology Stack](#technology-stack)

---

## Introduction

Tsukuyomi is a **backend AI infrastructure platform** for creating autonomous agent simulations with narrative orchestration. It provides three major engines that work together to create rich, story-driven agent experiences:

- **Agent System** - Manages autonomous AI agents that perceive, think, and act
- **Environment System** - Provides authoritative world simulation
- **Narrative System** - Orchestrates story flow and dramatic tension

### Core Capabilities

- Autonomous agents with PAD-based emotion, memory, and belief systems
- Deterministic tick-based world simulation (20 TPS)
- Dynamic narrative direction with tension tracking
- RAG-based long-term memory retrieval
- Multi-agent social dynamics (relationships, reputation, influence)
- LLM-powered deliberation and decision-making

---

## Design Philosophy

### Unified Codebase

Tsukuyomi MVP v0.1 maintains a **singular, unified platform**. "Simulation Mode" and "Standalone Mode" are merely different interfaces for the same underlying `BaseAgent` logic.

- No version fragmentation - all improvements belong in MVP v0.1
- Engine code drives the world with `FateEngine` and `DramaDirector`
- Experiment-specific data lives in `experiments/`, not core engine

### Separation of Concerns

The restructuring organizes code into clear, independent systems:

```
TSUKUYOMI PLATFORM
├── AGENT SYSTEM     - Cognitive, internal state, runtime
├── ENVIRONMENT      - World state, physics, rules, spatial
├── NARRATIVE        - Drama, events, flow, context
├── SERVICES         - LLM, embedding, vector, database
└── TRANSPORT        - gRPC, SDK, protocol buffers
```

### Production Readiness

- Strict lifecycle management (`start()`, `pause()`, `resume()`, `cleanup()`)
- Graceful degradation and circuit breaking
- Input validation and sanitization
- No file exceeds 700 lines of code

---

## System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TSUKUYOMI PLATFORM                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   AGENT         │   ENVIRONMENT   │        NARRATIVE            │
│   SYSTEM        │   SYSTEM        │        SYSTEM               │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ - Cognitive     │ - World State   │ - Drama Director            │
│ - Internal      │ - Physics       │ - Event Library             │
│ - Runtime       │ - Rules         │ - Narrative Flow            │
│ - Prompts       │ - Spatial       │ - Context Awareness         │
└────────┬────────┴────────┬────────┴───────────────┬─────────────┘
         │                 │                        │
         └─────────────────┴────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │          SHARED SERVICES          │
         ├───────────────────────────────────┤
         │ LLM │ Embedding │ Vector │ DB     │
         └─────────────────┴─────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │         TRANSPORT LAYER           │
         ├───────────────────────────────────┤
         │ gRPC Server │ gRPC Client │ Proto │
         └───────────────────────────────────┘
```

### Directory Structure

```
tsukuyomi/
├── agents/          # Agent system (core, cognitive, internal, social, runtime, prompts)
├── environment/     # Environment system (core, physics, rules, spatial)
├── narrative/       # Narrative system (core, events, flow, context)
├── services/        # External services (llm, embedding, vector, database)
├── shared/          # Shared utilities (config, logging, exceptions, utils, types)
├── transport/       # Communication layer (grpc, sdk, proto)
├── scenarios/       # Scenario definitions and loading
└── experiments/     # Test scenarios (isolated from engine)
```

---

## Core Principles

### 1. Unified Agent Interface

All agents inherit from `BaseAgent` with consistent lifecycle:
- `start()` - Initialize agent
- `pause()` - Temporarily suspend
- `resume()` - Resume from pause
- `cleanup()` - Release resources

### 2. Deterministic Environment

The environment operates on a **fixed tick rate (20 TPS)**:
- All state changes occur during tick resolution
- Proposals are collected and resolved atomically
- No external state mutations between ticks

### 3. LLM Integration with Fallbacks

- Primary LLM for deliberation (Groq/OpenAI/Anthropic)
- Timeout protection (30s default)
- Circuit breaking on repeated failures
- Fallback to rule-based behavior when unavailable

### 4. Memory with RAG

- Episodic, semantic, working, and procedural memory
- Vector embedding for semantic retrieval
- Importance-based retention
- Temporal decay simulation

### 5. Social Dynamics

- Relationship tracking (affinity, familiarity, trust)
- Gossip and information propagation
- Reputation systems
- Influence and persuasion

---

## System Components

### Agent System

**Purpose:** Manages autonomous AI agents that perceive, think, and act.

**Key Components:**

| Component | Description |
|-----------|-------------|
| `BaseAgent` | Abstract interface for all agents |
| `PerceptionPipeline` | Transform world state to percepts |
| `DeliberationEngine` | Decision-making with LLM |
| `MemorySystem` | Unified memory management |
| `EmotionalEngine` | PAD emotional state (Pleasure-Arousal-Dominance) |
| `BeliefTracker` | Evidence-based beliefs with confidence |
| `NeedsSystem` | Motivational drives (hunger, fatigue, etc.) |
| `RelationshipManager` | Social relationships and affinity |
| `SimulationAgent` | gRPC-connected agent for FateEngine |
| `StandaloneAgent` | Independent execution for testing |

**Responsibilities:**
- Agent lifecycle (creation, runtime, cleanup)
- Cognitive processes (perception, deliberation, decision-making)
- Internal state (emotions, beliefs, needs, relationships)
- Memory systems (episodic, semantic, working, long-term)
- Prompt generation for LLM interactions

**Does NOT:**
- Manage world state
- Control narrative flow
- Handle physics/collision
- Store world objects

### Environment System

**Purpose:** Provides the authoritative world simulation where agents exist.

**Key Components:**

| Component | Description |
|-----------|-------------|
| `FateEngine` | Main tick loop and world state |
| `WorldState` | Authoritative world data |
| `SpatialIndex` | Quadtree for spatial queries |
| `ProposalWindow` | Action proposal collection and resolution |
| `AffordanceManager` | What actions are possible where |
| `PhysicsEngine` | Collision, movement, raycasting |
| `RuleValidator` | World rule enforcement |

**Responsibilities:**
- World state management (actors, objects, locations)
- Tick-based simulation loop (deterministic 20 TPS)
- Action proposal and resolution
- Physics and spatial indexing
- Object affordances and interactions
- Rule enforcement and validation

**Does NOT:**
- Make decisions for agents
- Control narrative pacing
- Track agent internal state

### Narrative System

**Purpose:** Orchestrates the story flow and dramatic tension.

**Key Components:**

| Component | Description |
|-----------|-------------|
| `DramaDirector` | Tension monitoring and event injection |
| `CatalystSystem` | Dramatic event triggers |
| `EventLibrary` | Predefined and procedural events |
| `BranchManager` | Story branching and paths |
| `ContextAwareDirector` | Context-aware event selection |

**Responsibilities:**
- Tension monitoring and management
- Event injection (catalysts)
- Narrative beat tracking
- Branching story support
- Context-aware event selection

**Does NOT:**
- Control agent decisions
- Modify world state directly
- Handle physics
- Manage agent memory

### Shared Services

**Purpose:** Provides external service abstractions used by all systems.

| Service | Description |
|---------|-------------|
| `LLMService` | Provider abstraction (OpenAI, Groq, Anthropic) |
| `EmbeddingService` | Text vectorization |
| `VectorStore` | Qdrant or in-memory vector database |
| `DatabaseManager` | PostgreSQL, SQLite, or in-memory |

### Transport Layer

**Purpose:** Handles communication between components.

| Component | Description |
|-----------|-------------|
| `gRPCServer` | FateEngine server for agent connections |
| `gRPCClient` | Agent connection to FateEngine |
| `GuestSDK` | Python SDK for external integrations |
| `ProtocolBuffers` | Message definitions |

---

## Data Flow

### Simulation Tick Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FATE ENGINE TICK                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DRAMA DIRECTOR                                          │
│     ├── Check tension levels                                │
│     ├── Inject catalyst events if needed                    │
│     └── Update narrative context                            │
│                                                              │
│  2. AGENT PERCEPTION                                        │
│     ├── For each agent:                                     │
│     │   ├── Query spatial index for nearby entities         │
│     │   ├── Filter by visibility/audibility                 │
│     │   └── Generate percepts                               │
│     └── Broadcast world events                              │
│                                                              │
│  3. AGENT DELIBERATION                                     │
│     ├── For each agent:                                     │
│     │   ├── Gather context (percepts, memory, beliefs)      │
│     │   ├── Build prompt                                    │
│     │   ├── Call LLM (with timeout)                         │
│     │   └── Generate action proposal                        │
│     └── Collect all proposals                               │
│                                                              │
│  4. PROPOSAL RESOLUTION                                    │
│     ├── Validate all proposals against world rules          │
│     ├── Resolve conflicts (multiple agents targeting same)  │
│     ├── Execute valid proposals in order                    │
│     └── Update world state atomically                       │
│                                                              │
│  5. STATE UPDATE                                           │
│     ├── Update agent positions                              │
│     ├── Process emotional decay                             │
│     ├── Update memory importance                           │
│     └── Trigger new events                                  │
│                                                              │
│  6. PERSISTENCE (if enabled)                               │
│     └── Save world snapshot                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Standalone Mode Flow

```
┌─────────────────────────────────────────────┐
│         STANDALONE AGENT                     │
├─────────────────────────────────────────────┤
│                                             │
│  1. Initialize with world state             │
│  2. perceive() - Generate percepts          │
│  3. deliberate() - Think with LLM           │
│  4. act() - Execute action                  │
│  5. update_internal_state()                 │
│  6. Loop to 2                               │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Deployment Modes

### Simulation Mode (gRPC)

Agents connect to a central `FateEngine` server via gRPC:

```
┌──────────────┐         ┌──────────────┐
│   Agent 1    │         │              │
└──────┬───────┘         │              │
       │ gRPC            │ FateEngine   │
┌──────┴───────┐         │   Server     │
│   Agent 2    │────────▶│              │
└──────────────┘         └──────────────┘
```

**Use cases:**
- Multi-agent simulations
- Centralized world state
- Deterministic simulation
- Production deployments

### Standalone Mode

Agents run independently without central server:

```
┌──────────────┐
│ Standalone   │
│    Agent     │
│              │
│ - Internal   │
│   world      │
│ - Self       │
│   contained  │
└──────────────┘
```

**Use cases:**
- Testing and development
- Single-agent scenarios
- API integrations
- Chatbot-style interactions

---

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.10+ | Core implementation |
| Async | asyncio | Concurrent operations |
| Serialization | protobuf | Efficient data exchange |
| Communication | gRPC | Agent-server communication |

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| aiohttp | Latest | Async HTTP for LLM APIs |
| python-dotenv | Latest | Environment configuration |
| sentence-transformers | Latest | Embedding generation |
| qdrant-client | Latest | Vector database (optional) |
| psycopg2-binary | Latest | PostgreSQL (optional) |

### LLM Providers

| Provider | Models | Status |
|----------|--------|--------|
| Groq | Llama 3.3 70B | ✅ Supported |
| OpenAI | GPT-4, GPT-3.5 | ✅ Supported |
| Anthropic | Claude Opus, Sonnet | ✅ Supported |
| Local | Ollama, LM Studio | ✅ Supported |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-22 | Initial restructured architecture (MVP v0.1) |

---

**See Also:**
- [API Reference](API.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Agent System Documentation](agents/README.md)
- [Environment System Documentation](environment/README.md)
- [Narrative System Documentation](narrative/README.md)
