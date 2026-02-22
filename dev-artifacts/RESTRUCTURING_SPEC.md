# Tsukuyomi Architecture Restructuring Specification

**Version:** 1.0  
**Date:** 2026-02-21  
**Status:** Draft  
**Author:** System Analysis

---

## Executive Summary

This document defines the architectural restructuring plan for Tsukuyomi MVP v0.1. The goal is to reorganize the codebase into three major systems (Agents, Environment, Narrative) plus shared infrastructure, creating a clear separation of concerns and professional structure suitable for production deployment.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Problems Identified](#2-problems-identified)
3. [Proposed Architecture](#3-proposed-architecture)
4. [System Specifications](#4-system-specifications)
5. [Directory Structure](#5-directory-structure)
6. [Component Mapping](#6-component-mapping)
7. [Interface Definitions](#7-interface-definitions)
8. [Implementation Phases](#8-implementation-phases)
9. [Migration Checklist](#9-migration-checklist)
10. [Risk Assessment](#10-risk-assessment)

---

## 1. Current Architecture Analysis

### 1.1 Current Directory Structure

```
tsukuyomi/
├── core/                    # Mixed: base classes + world + drama
│   ├── agent_base.py
│   ├── world_builder.py
│   ├── spatial_index.py
│   ├── affordance.py
│   ├── proposal_window.py
│   ├── belief/
│   ├── emotion/
│   ├── memory/
│   ├── drama/
│   └── scenarios/
├── brain/                   # Mixed: agent implementation + services + systems
│   ├── agent_brain.py
│   ├── drama_director.py
│   ├── perception_pipeline.py
│   ├── memory_manager.py
│   ├── needs_system.py
│   ├── relationship_manager.py
│   ├── llm_service.py
│   ├── embedding_service.py
│   ├── vector_store.py
│   └── rag_memory.py
├── agent/                   # Standalone agent implementation
│   ├── universal_agent.py
│   ├── identity.py
│   ├── memory_system.py
│   └── immersive_prompt.py
├── proto/                   # gRPC + engine + services
│   ├── fate_engine.py
│   ├── grpc_server.py
│   ├── grpc_client.py
│   ├── action_logic.py
│   └── [protobuf files]
└── experiments/             # Test scenarios
```

### 1.2 Current Responsibility Distribution

| Component | Current Responsibilities | Issues |
|-----------|-------------------------|--------|
| `brain/agent_brain.py` | Agent runtime, perception integration, deliberation, LLM calls, memory, relationships, needs, gossip | God class - 694 lines, too many responsibilities |
| `proto/fate_engine.py` | Tick loop, state management, proposal handling, spatial index, resolution | Mixed environment + engine logic |
| `brain/drama_director.py` | Tension tracking, catalyst injection | Unclear ownership - should be narrative system |
| `brain/llm_service.py` | Provider abstraction, prompt templates, rate limiting | Service layer mixed with agent code |

### 1.3 Dependency Analysis

```
Current Dependency Graph (problematic):

agent_brain.py
    ├── fate_engine.py (proto/)
    ├── drama_director.py (brain/)
    ├── llm_service.py (brain/)
    ├── memory_manager.py (brain/)
    ├── needs_system.py (brain/)
    ├── relationship_manager.py (brain/)
    ├── perception_pipeline.py (brain/)
    ├── rag_memory.py (brain/)
    └── [core emotion, belief, memory bases]

fate_engine.py
    ├── spatial_index.py (core/)
    ├── affordance.py (core/)
    ├── proposal_window.py (core/)
    └── action_logic.py (proto/)

grpc_server.py
    ├── fate_engine.py
    └── drama_director.py (brain/)
```

**Problem:** Circular and deep dependencies make testing and maintenance difficult.

---

## 2. Problems Identified

### 2.1 Structural Problems

| ID | Problem | Impact |
|----|---------|--------|
| S1 | `brain/` directory contains unrelated systems | Confusing navigation, unclear ownership |
| S2 | Agent implementation split between `brain/` and `agent/` | Code duplication, inconsistent patterns |
| S3 | Environment logic scattered across `core/`, `proto/`, `brain/` | Hard to understand world simulation |
| S4 | Narrative system embedded in `brain/` | Cannot develop narrative independently |
| S5 | Services (LLM, Vector, Embedding) mixed with domain logic | Cannot swap providers easily |

### 2.2 Design Problems

| ID | Problem | Impact |
|----|---------|--------|
| D1 | `AgentBrain` is a god class (694 lines) | Hard to test, maintain, extend |
| D2 | Tight coupling between agent and engine | Cannot run agents standalone |
| D3 | No clear service abstraction layer | Hard to add new LLM providers |
| D4 | Missing dependency injection | Hard to mock for testing |
| D5 | Inconsistent naming conventions | Confusion between similar components |

### 2.3 File Size Violations

| File | Lines | Status |
|------|-------|--------|
| `core/emotion/unified.py` | 1375+ | **VIOLATION** (>700) |
| `brain/memory/retrieval.py` | 763 | **VIOLATION** (>700) |
| `core/spatial_index.py` | 857 | **VIOLATION** (>700) |
| `brain/agent_brain.py` | 694 | Warning (approaching limit) |
| `brain/llm_service.py` | 825 | **VIOLATION** (>700) |
| `brain/rag_memory.py` | 509 | OK |
| `core/drama/context_aware_director.py` | 525 | OK |

---

## 3. Proposed Architecture

### 3.1 Architectural Vision

Tsukuyomi is a **backend AI infrastructure** for:
- Storytelling applications
- Game AI systems
- Agent simulations

The system provides three major engines that work together:

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
         └───────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │         TRANSPORT LAYER           │
         ├───────────────────────────────────┤
         │ gRPC Server │ gRPC Client │ Proto │
         └───────────────────────────────────┘
```

### 3.2 System Boundaries

#### Agent System
**Purpose:** Manages autonomous AI agents that perceive, think, and act.

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

#### Environment System
**Purpose:** Provides the authoritative world simulation where agents exist.

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

#### Narrative System
**Purpose:** Orchestrates the story flow and dramatic tension.

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

#### Shared Services
**Purpose:** Provides external service abstractions used by all systems.

**Components:**
- LLM Provider (OpenAI, Groq, Anthropic, etc.)
- Embedding Service (text vectorization)
- Vector Store (Qdrant, in-memory)
- Database Manager (persistence)

---

## 4. System Specifications

### 4.1 Agent System Specification

```
agents/
├── core/                    # Core abstractions
│   ├── base.py             # BaseAgent abstract class
│   ├── types.py            # Agent-related types
│   └── agent_builder.py    # Factory for agent creation
├── cognitive/              # Thinking systems
│   ├── perception.py       # Perception pipeline
│   ├── deliberation.py     # Decision-making engine
│   └── memory.py           # Memory systems (episodic, semantic, working, RAG)
├── internal/               # Internal state
│   ├── emotion.py          # PAD emotional engine
│   ├── beliefs.py          # Belief tracking and bias
│   ├── needs.py            # Motivational drives (hunger, fatigue, etc.)
│   └── relationships.py    # Social relationships and affinity
├── runtime/                # Agent implementations
│   ├── simulation_agent.py # gRPC-connected agent for FateEngine
│   └── standalone_agent.py # Direct/async agent for testing
└── prompts/                # LLM prompt templates
    ├── templates.py        # Prompt template definitions
    └── context.py          # Context building utilities
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `BaseAgent` | `core/base.py` | Abstract interface for all agents |
| `AgentBuilder` | `core/agent_builder.py` | Factory for creating configured agents |
| `PerceptionPipeline` | `cognitive/perception.py` | Transform world state to percepts |
| `DeliberationEngine` | `cognitive/deliberation.py` | Think before acting |
| `MemorySystem` | `cognitive/memory.py` | Unified memory management |
| `EmotionalEngine` | `internal/emotion.py` | PAD emotional state |
| `BeliefTracker` | `internal/beliefs.py` | Evidence-based beliefs |
| `NeedsSystem` | `internal/needs.py` | Motivational drives |
| `RelationshipManager` | `internal/relationships.py` | Social state |
| `SimulationAgent` | `runtime/simulation_agent.py` | Connected to FateEngine |
| `StandaloneAgent` | `runtime/standalone_agent.py` | Independent execution |

### 4.2 Environment System Specification

```
environment/
├── core/                    # Core engine
│   ├── engine.py           # FateEngine - main tick loop
│   ├── state.py            # WorldState management
│   ├── resolution.py       # Proposal/action resolution
│   └── proposal.py         # Proposal window management
├── world/                   # World structure
│   ├── builder.py          # WorldBuilder API
│   ├── spatial.py          # SpatialIndex for proximity
│   ├── objects.py          # EnvironmentObject definitions
│   └── locations.py        # Location/zone definitions
├── physics/                 # Physical systems
│   ├── affordance.py       # Action validation
│   └── interactions.py     # Object interaction logic
└── rules/                   # Game rules
    ├── action_logic.py     # Action resolution rules
    ├── preconditions.py    # Precondition checkers
    └── effects.py          # Effect application
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `EnvironmentEngine` | `core/engine.py` | Main tick loop authority |
| `WorldState` | `core/state.py` | Immutable world snapshot |
| `ResolutionEngine` | `core/resolution.py` | Proposal resolution |
| `ProposalWindow` | `core/proposal.py` | Multi-tick proposal collection |
| `WorldBuilder` | `world/builder.py` | Programmatic world creation |
| `SpatialIndex` | `world/spatial.py` | Efficient proximity queries |
| `AffordanceValidator` | `physics/affordance.py` | Action preconditions |
| `ActionResolver` | `rules/action_logic.py` | Action-specific logic |

### 4.3 Narrative System Specification

```
narrative/
├── core/                    # Core narrative engine
│   ├── director.py         # DramaDirector - main orchestrator
│   ├── tension.py          # TensionVector calculation
│   └── catalyst.py         # Event injection system
├── events/                  # Event management
│   ├── library.py          # EventLibrary - event definitions
│   ├── types.py            # Event categories and types
│   └── selection.py        # Event selection algorithms
├── flow/                    # Story flow control
│   ├── branching.py        # Narrative branching logic
│   ├── beats.py            # Narrative beat tracking
│   └── hooks.py            # Pre/post tick hooks
└── context/                 # Context awareness
    ├── context_aware.py    # ContextAwareDramaDirector
    └── evaluator.py        # Condition evaluation
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `NarrativeDirector` | `core/director.py` | Main narrative orchestrator |
| `TensionVector` | `core/tension.py` | Tension state representation |
| `CatalystSystem` | `core/catalyst.py` | Event injection |
| `EventLibrary` | `events/library.py` | Event definitions |
| `BranchManager` | `flow/branching.py` | Story branching |
| `BeatTracker` | `flow/beats.py` | Narrative beat scheduling |
| `ContextAwareDirector` | `context/context_aware.py` | Enhanced director |

### 4.4 Shared Services Specification

```
services/
├── llm/                     # LLM abstraction
│   ├── provider.py         # Abstract LLMProvider
│   ├── openai_provider.py  # OpenAI implementation
│   ├── groq_provider.py    # Groq implementation
│   ├── anthropic_provider.py # Anthropic implementation
│   └── prompts.py          # Prompt templates
├── embedding/               # Text embeddings
│   ├── service.py          # EmbeddingService
│   └── providers.py        # Embedding providers
├── vector/                  # Vector database
│   ├── store.py            # VectorStore abstraction
│   ├── qdrant_store.py     # Qdrant implementation
│   └── memory_store.py     # In-memory implementation
└── database/                # Persistence
    ├── manager.py          # Database manager
    └── models.py           # Data models
```

**Key Interfaces:**

| Interface | Location | Methods |
|-----------|----------|---------|
| `LLMProvider` | `llm/provider.py` | `generate()`, `stream()`, `health_check()` |
| `EmbeddingService` | `embedding/service.py` | `embed_text()`, `embed_batch()` |
| `VectorStore` | `vector/store.py` | `add_point()`, `search()`, `delete()` |
| `DatabaseManager` | `database/manager.py` | `save()`, `load()`, `query()` |

---

## 5. Directory Structure

### 5.1 Complete Directory Tree

```
tsukuyomi/
│
├── agents/                          # AGENT SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core abstractions
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseAgent ABC
│   │   ├── types.py                 # Agent-related types
│   │   └── agent_builder.py         # Factory pattern
│   │
│   ├── cognitive/                   # Thinking systems
│   │   ├── __init__.py
│   │   ├── perception.py            # PerceptionPipeline
│   │   ├── deliberation.py          # DeliberationEngine
│   │   └── memory.py                # Unified memory (episodic, semantic, RAG)
│   │
│   ├── internal/                    # Internal state
│   │   ├── __init__.py
│   │   ├── emotion.py               # PAD emotional engine
│   │   ├── beliefs.py               # BeliefTracker
│   │   ├── needs.py                 # NeedsSystem
│   │   └── relationships.py         # RelationshipManager
│   │
│   ├── runtime/                     # Agent implementations
│   │   ├── __init__.py
│   │   ├── simulation_agent.py      # gRPC-connected
│   │   └── standalone_agent.py      # Independent
│   │
│   └── prompts/                     # LLM prompts
│       ├── __init__.py
│       ├── templates.py             # Scenario templates
│       └── context.py               # Context builders
│
├── environment/                     # ENVIRONMENT SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core engine
│   │   ├── __init__.py
│   │   ├── engine.py                # EnvironmentEngine (main tick loop)
│   │   ├── state.py                 # WorldState management
│   │   ├── resolution.py            # Proposal resolution
│   │   └── proposal.py              # ProposalWindow
│   │
│   ├── world/                       # World structure
│   │   ├── __init__.py
│   │   ├── builder.py               # WorldBuilder
│   │   ├── spatial.py               # SpatialIndex
│   │   ├── objects.py               # EnvironmentObject
│   │   └── locations.py             # Location/Zone
│   │
│   ├── physics/                     # Physical systems
│   │   ├── __init__.py
│   │   ├── affordance.py            # AffordanceValidator
│   │   └── interactions.py          # Interaction logic
│   │
│   └── rules/                       # Game rules
│       ├── __init__.py
│       ├── action_logic.py          # Action resolution
│       ├── preconditions.py         # Precondition checkers
│       └── effects.py               # Effect application
│
├── narrative/                       # NARRATIVE SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core narrative
│   │   ├── __init__.py
│   │   ├── director.py              # NarrativeDirector
│   │   ├── tension.py               # TensionVector
│   │   └── catalyst.py              # CatalystSystem
│   │
│   ├── events/                      # Event management
│   │   ├── __init__.py
│   │   ├── library.py               # EventLibrary
│   │   ├── types.py                 # Event types
│   │   └── selection.py             # Selection algorithms
│   │
│   ├── flow/                        # Story flow
│   │   ├── __init__.py
│   │   ├── branching.py             # BranchManager
│   │   ├── beats.py                 # BeatTracker
│   │   └── hooks.py                 # Tick hooks
│   │
│   └── context/                     # Context awareness
│       ├── __init__.py
│       ├── context_aware.py         # ContextAwareDirector
│       └── evaluator.py             # ConditionEvaluator
│
├── services/                        # SHARED SERVICES
│   ├── __init__.py
│   │
│   ├── llm/                         # LLM services
│   │   ├── __init__.py
│   │   ├── provider.py              # LLMProvider ABC
│   │   ├── openai_provider.py       # OpenAI
│   │   ├── groq_provider.py         # Groq
│   │   ├── anthropic_provider.py    # Anthropic
│   │   └── prompts.py               # Prompt templates
│   │
│   ├── embedding/                   # Embedding services
│   │   ├── __init__.py
│   │   ├── service.py               # EmbeddingService
│   │   └── providers.py             # Provider implementations
│   │
│   ├── vector/                      # Vector database
│   │   ├── __init__.py
│   │   ├── store.py                 # VectorStore ABC
│   │   ├── qdrant_store.py          # Qdrant
│   │   └── memory_store.py          # In-memory
│   │
│   └── database/                    # Persistence
│       ├── __init__.py
│       ├── manager.py               # DBManager
│       └── models.py                # Data models
│
├── transport/                       # COMMUNICATION LAYER
│   ├── __init__.py
│   │
│   ├── grpc/                        # gRPC implementation
│   │   ├── __init__.py
│   │   ├── server.py                # GrpcServer
│   │   ├── client.py                # GrpcClient
│   │   │
│   │   └── servicers/               # Service implementations
│   │       ├── __init__.py
│   │       ├── fate.py              # FateEngineServicer
│   │       └── guest.py             # GuestServicer
│   │
│   └── proto/                       # Protocol buffers
│       ├── __init__.py
│       ├── core_pb2.py              # Generated
│       ├── core_pb2_grpc.py         # Generated
│       ├── common_pb2.py            # Generated
│       ├── perception_pb2.py        # Generated
│       ├── fate_engine_service_pb2.py
│       ├── fate_engine_service_pb2_grpc.py
│       ├── guest_api_pb2.py
│       └── guest_api_pb2_grpc.py
│
├── shared/                          # COMMON UTILITIES
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── logging.py                   # Logging utilities
│   ├── exceptions.py                # Custom exceptions
│   ├── types.py                     # Common types
│   └── utils.py                     # Helper functions
│
├── scenarios/                       # SCENARIO DEFINITIONS
│   ├── __init__.py
│   ├── schema.py                    # Scenario configuration schema
│   └── loader.py                    # Scenario loader
│
├── experiments/                     # TEST SCENARIOS (preserve)
│   ├── scenarios/
│   └── logs/
│
├── tests/                           # TESTS (preserve structure)
│   └── [existing tests]
│
├── server.py                        # MAIN ENTRY POINT
├── __init__.py
├── requirements.txt
├── pytest.ini
└── README.md
```

### 5.2 File Size Guidelines

Each file must not exceed **700 lines of code**. If a file approaches this limit:

1. Extract related functionality into a submodule
2. Create a new file within the same package
3. Use composition to delegate responsibilities

---

## 6. Component Mapping

### 6.1 Detailed File Migration

| Source File | Destination | Changes Required |
|-------------|-------------|------------------|
| `core/agent_base.py` | `agents/core/base.py` | Minor import updates |
| `core/agent_builder.py` | `agents/core/agent_builder.py` | Minor import updates |
| `brain/agent_brain.py` | `agents/runtime/simulation_agent.py` | Split into multiple files |
| `agent/universal_agent.py` | `agents/runtime/standalone_agent.py` | Minor import updates |
| `agent/identity.py` | `agents/core/identity.py` | Move to core |
| `agent/immersive_prompt.py` | `agents/prompts/templates.py` | Merge with prompts |
| `core/emotion/base.py` | `agents/internal/emotion.py` | Merge with unified.py |
| `core/emotion/unified.py` | `agents/internal/emotion.py` | Consolidate, split if >700 lines |
| `core/belief/base.py` | `agents/internal/beliefs.py` | Merge with manager.py |
| `core/belief/manager.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/structures.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/logic.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/decay.py` | `agents/internal/beliefs.py` | Merge |
| `core/memory/base.py` | `agents/cognitive/memory.py` | Merge with memory_manager |
| `brain/memory_manager.py` | `agents/cognitive/memory.py` | Merge |
| `brain/rag_memory.py` | `agents/cognitive/memory.py` | Merge RAG functionality |
| `brain/working_memory.py` | `agents/cognitive/memory.py` | Merge |
| `brain/perception_pipeline.py` | `agents/cognitive/perception.py` | Minor updates |
| `brain/perception_channels.py` | `agents/cognitive/perception.py` | Merge |
| `brain/deliberation.py` | `agents/cognitive/deliberation.py` | Minor updates |
| `brain/needs_system.py` | `agents/internal/needs.py` | Minor updates |
| `brain/relationship_manager.py` | `agents/internal/relationships.py` | Minor updates |
| `proto/fate_engine.py` | `environment/core/engine.py` | Split responsibilities |
| `core/world_builder.py` | `environment/world/builder.py` | Minor updates |
| `core/spatial_index.py` | `environment/world/spatial.py` | Split if >700 lines |
| `core/affordance.py` | `environment/physics/affordance.py` | Minor updates |
| `core/proposal_window.py` | `environment/core/proposal.py` | Minor updates |
| `proto/action_logic.py` | `environment/rules/action_logic.py` | Minor updates |
| `proto/fate_resolvers.py` | `environment/core/resolution.py` | Merge |
| `brain/drama_director.py` | `narrative/core/director.py` | Minor updates |
| `brain/catalyst_system.py` | `narrative/core/catalyst.py` | Minor updates |
| `core/drama/context_aware_director.py` | `narrative/context/context_aware.py` | Minor updates |
| `core/drama/event_library.py` | `narrative/events/library.py` | Minor updates |
| `core/drama/branch_manager.py` | `narrative/flow/branching.py` | Minor updates |
| `brain/llm_service.py` | `services/llm/provider.py` | Split into multiple files |
| `brain/embedding_service.py` | `services/embedding/service.py` | Minor updates |
| `brain/vector_store.py` | `services/vector/store.py` | Minor updates |
| `proto/db_manager.py` | `services/database/manager.py` | Minor updates |
| `proto/grpc_server.py` | `transport/grpc/server.py` | Minor updates |
| `proto/grpc_client.py` | `transport/grpc/client.py` | Minor updates |

### 6.2 Files to Delete (Duplicates/Obsolete)

| File | Reason |
|------|--------|
| `core/belief/existential.py` | Consolidate into beliefs.py |
| `core/belief/contradiction.py` | Consolidate into beliefs.py |
| `core/memory/__init__.py` | Move content to cognitive/memory.py |
| `core/emotion/__init__.py` | Move content to internal/emotion.py |
| `agent/memory_system.py` | Duplicate of memory_manager, consolidate |
| `agent/memory.py` | Duplicate, consolidate |
| `agent/behavior.py` | Consolidate into runtime or cognitive |
| `agent/conversation.py` | Consolidate into relationships or prompts |
| `agent/influence.py` | Consolidate into relationships |
| `agent/personality.py` | Consolidate into internal/emotion.py |
| `agent/context_manager.py` | Consolidate into cognitive/perception.py |
| `agent/decision_engine.py` | Consolidate into cognitive/deliberation.py |
| `agent/proposal_handler.py` | Consolidate into runtime |
| `agent/persuasion.py` | Consolidate into relationships |

---

## 7. Interface Definitions

### 7.1 Agent System Interfaces

```python
# agents/core/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    PERCEIVING = "perceiving"
    DELIBERATING = "deliberating"
    ACTING = "acting"
    PAUSED = "paused"

@dataclass
class Percept:
    """A piece of perceived information."""
    percept_id: str
    channel: str  # visual, auditory, social, internal
    content: Dict[str, Any]
    salience: float
    tick: int

@dataclass
class Decision:
    """A decision made by the agent."""
    action: str
    params: Dict[str, Any]
    thought: str
    confidence: float
    reasoning_chain: List[str]

@dataclass
class Proposal:
    """An action proposal to submit to the environment."""
    proposal_id: str
    actor_id: str
    action: str
    params: Dict[str, Any]
    timestamp: float

class BaseAgent(ABC):
    """
    Abstract base class for all Tsukuyomi agents.
    
    All agents must implement the perceive-deliberate-act cycle
    and lifecycle management methods.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state = AgentState.IDLE
        self._running = False
        self._paused = False
    
    @abstractmethod
    async def perceive(self, world_state: Any) -> List[Percept]:
        """
        Process world state into percepts.
        
        Args:
            world_state: Current world state from environment
            
        Returns:
            List of salient percepts
        """
        pass
    
    @abstractmethod
    async def deliberate(self, percepts: List[Percept]) -> Decision:
        """
        Make a decision based on percepts.
        
        Args:
            percepts: List of perceived information
            
        Returns:
            Decision with action and parameters
        """
        pass
    
    @abstractmethod
    async def act(self, decision: Decision) -> Proposal:
        """
        Convert decision to action proposal.
        
        Args:
            decision: The decision to act on
            
        Returns:
            Proposal to submit to environment
        """
        pass
    
    # Lifecycle management
    @abstractmethod
    def start(self) -> None:
        """Start the agent."""
        pass
    
    @abstractmethod
    def pause(self) -> None:
        """Pause agent processing."""
        pass
    
    @abstractmethod
    def resume(self) -> None:
        """Resume agent processing."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources before shutdown."""
        pass
```

### 7.2 Environment System Interfaces

```python
# environment/core/engine.py

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Awaitable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EngineConfig:
    """Configuration for the environment engine."""
    tick_rate: int = 20
    proposal_window_ms: int = 25
    seed: Optional[int] = None
    db_path: Optional[str] = None
    enable_phase2: bool = True
    multi_tick_window: int = 3
    spatial_cell_size: float = 10.0

class EnvironmentEngine:
    """
    The authoritative simulation engine.
    
    Manages world state, tick loop, and action resolution.
    Does NOT make decisions for agents or control narrative.
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.current_tick = 0
        self.running = False
        self._paused = False
        
        # Hooks for external systems (e.g., narrative)
        self._pre_tick_hooks: List[Callable[[int], Awaitable[None]]] = []
        self._post_tick_hooks: List[Callable[[int, List], Awaitable[None]]] = []
    
    async def run(self) -> None:
        """
        Main simulation loop.
        
        Runs indefinitely until stopped.
        """
        pass
    
    async def submit_proposal(self, proposal: Any) -> bool:
        """
        Submit an action proposal for consideration.
        
        Args:
            proposal: The proposal to submit
            
        Returns:
            True if accepted into queue, False if rejected
        """
        pass
    
    def get_world_state(self) -> Any:
        """
        Get current world state snapshot.
        
        Returns:
            Immutable world state
        """
        pass
    
    def register_actor(self, actor_id: str, name: str, position: tuple) -> None:
        """Register a new actor in the world."""
        pass
    
    def unregister_actor(self, actor_id: str) -> None:
        """Remove an actor from the world."""
        pass
    
    # Hook management
    def add_pre_tick_hook(self, hook: Callable[[int], Awaitable[None]]) -> None:
        """Add a hook to run before each tick."""
        self._pre_tick_hooks.append(hook)
    
    def add_post_tick_hook(self, hook: Callable[[int, List], Awaitable[None]]) -> None:
        """Add a hook to run after each tick (receives resolutions)."""
        self._post_tick_hooks.append(hook)
    
    # Lifecycle
    def stop(self) -> None:
        """Stop the simulation."""
        pass
    
    def pause(self) -> None:
        """Pause the simulation."""
        pass
    
    def resume(self) -> None:
        """Resume the simulation."""
        pass
```

### 7.3 Narrative System Interfaces

```python
# narrative/core/director.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class EventCategory(Enum):
    CONFLICT = "conflict"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    NARRATIVE = "narrative"
    MYSTERY = "mystery"

@dataclass
class Event:
    """A narrative event that can be injected into the simulation."""
    id: str
    category: EventCategory
    description: str
    target_agent: Optional[str] = None
    broadcast: bool = True
    context_tags: List[str] = None
    params: Dict[str, Any] = None

@dataclass
class TensionVector:
    """Current narrative tension state."""
    conflict: float = 0.0
    mystery: float = 0.0
    social: float = 0.0
    emotion: float = 0.0
    
    @property
    def aggregate(self) -> float:
        return (self.conflict + self.mystery + self.social + self.emotion) / 4

@dataclass
class NarrativeConfig:
    """Configuration for narrative director."""
    boredom_threshold: float = 0.2
    tension_threshold_high: float = 0.8
    tension_decay_rate: float = 0.001
    min_injection_interval: int = 100

class NarrativeDirector:
    """
    Orchestrates narrative flow and dramatic tension.
    
    Monitors simulation state and injects events when needed.
    Does NOT control agent decisions or modify world state directly.
    """
    
    def __init__(self, engine: Any, config: NarrativeConfig):
        self.engine = engine
        self.config = config
        self.current_tension = TensionVector()
        
        # Attach to engine hooks
        engine.add_post_tick_hook(self._on_tick_resolved)
    
    def evaluate_tick(
        self, 
        tick: int, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """
        Evaluate if narrative intervention is needed.
        
        Args:
            tick: Current simulation tick
            world_state: Current world state
            agent_states: Current agent states
            
        Returns:
            Event to inject, or None if no intervention needed
        """
        pass
    
    def update_tension(self, event: Event) -> None:
        """
        Update tension based on an event.
        
        Args:
            event: The event that occurred
        """
        pass
    
    def get_tension_status(self) -> TensionVector:
        """Get current tension state."""
        return self.current_tension
    
    async def _on_tick_resolved(self, tick: int, resolutions: List) -> None:
        """Internal hook handler."""
        # Update tension from resolutions
        # Check for intervention
        pass
```

### 7.4 Service Interfaces

```python
# services/llm/provider.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncIterator
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    thought: str = ""
    action: str = "IDLE"
    params: Dict[str, Any] = None
    tokens_used: Optional[int] = None
    provider: str = "unknown"

@dataclass
class PromptContext:
    """Context for LLM prompt generation."""
    agent_name: str
    agent_backstory: str
    scenario_type: str
    working_memory: str = ""
    beliefs: str = ""
    relationships: str = ""
    emotional_state: str = ""
    world_context: str = ""
    additional_context: Dict[str, Any] = None

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Implementations: OpenAI, Groq, Anthropic, etc.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[PromptContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Generate a complete response.
        
        Args:
            prompt: The prompt to send
            context: Optional context for the prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured response
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        context: Optional[PromptContext] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream response token by token.
        
        Args:
            prompt: The prompt to send
            context: Optional context for the prompt
            temperature: Sampling temperature
            
        Yields:
            Individual tokens
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
```

---

## 8. Implementation Phases

### 8.1 Phase 1: Create Directory Structure (Day 1)

**Objective:** Create new directory structure without modifying files.

**Tasks:**
1. Create all new directories
2. Create `__init__.py` files in each directory
3. Add placeholder imports in `__init__.py` files
4. Verify no import errors

**Validation:**
- `python -c "import tsukuyomi"` succeeds
- All directories exist with proper structure

### 8.2 Phase 2: Move Files (Days 2-3)

**Objective:** Move files to new locations without modification.

**Tasks:**
1. Move files according to mapping table (Section 6.1)
2. Update import paths in moved files
3. Update import paths in dependent files
4. Run tests to identify broken imports

**Order of Migration:**
1. `shared/` - No dependencies
2. `services/` - Depends only on shared
3. `transport/proto/` - Generated files, no changes
4. `environment/` - Core engine
5. `narrative/` - Depends on environment
6. `agents/` - Depends on all above

**Validation:**
- All imports resolve correctly
- `pytest tests/` runs (may have failures)

### 8.3 Phase 3: Refactor Classes (Days 4-6)

**Objective:** Split large files and consolidate duplicates.

**Priority Order:**

| File | Lines | Action |
|------|-------|--------|
| `core/emotion/unified.py` | 1375+ | Split into emotion.py + mood.py + personality.py |
| `brain/llm_service.py` | 825 | Split into provider.py + prompts.py |
| `core/spatial_index.py` | 857 | Split into spatial.py + query.py + stats.py |
| `brain/agent_brain.py` | 694 | Already split by new structure |

**Tasks:**
1. Identify cohesive modules within large files
2. Extract into separate files
3. Update imports
4. Add deprecation warnings to old imports

**Validation:**
- All files under 700 lines
- Tests pass

### 8.4 Phase 4: Create Unified Entry Point (Day 7)

**Objective:** Create `server.py` as single entry point.

**Tasks:**
1. Create `server.py` with:
   - Configuration loading
   - Engine initialization
   - Narrative director setup
   - gRPC server startup
   - Graceful shutdown
2. Create `shared/config.py` for configuration management
3. Create `scenarios/schema.py` for scenario definitions
4. Update documentation

**Validation:**
- `python server.py --scenario marketplace` starts correctly
- Graceful shutdown works

### 8.5 Phase 5: Update Tests (Days 8-9)

**Objective:** Update all tests to match new structure.

**Tasks:**
1. Update test imports
2. Create new test files for new modules
3. Add integration tests for system boundaries
4. Verify all tests pass

**Validation:**
- `pytest tests/ -v` passes
- Coverage maintained or improved

### 8.6 Phase 6: Cleanup (Day 10)

**Objective:** Remove obsolete files and finalize.

**Tasks:**
1. Delete obsolete files (Section 6.2)
2. Remove empty directories
3. Update `README.md`
4. Update `requirements.txt` if needed


**Validation:**
- No broken imports
- All tests pass
- Documentation updated

---

## 9. Migration Checklist

### 9.1 Pre-Migration

- [ ] Create backup branch
- [ ] Run full test suite, record results
- [ ] Document current coverage
- [ ] List all external dependencies

### 9.2 During Migration

- [ ] Create new directories
- [ ] Move files in dependency order (shared → services → transport → environment → narrative → agents)
- [ ] Update imports after each move
- [ ] Run tests after each major move
- [ ] Refactor large files
- [ ] Create entry point

### 9.3 Post-Migration

- [ ] All tests pass
- [ ] Coverage maintained
- [ ] No files exceed 700 lines
- [ ] Documentation updated
- [ ] Migration guide created

### 9.4 Per-File Migration Template

For each file migration:

```markdown
## File: [source_file] → [destination_file]

### Dependencies (imports)
- [dep1] → [new_location1]
- [dep2] → [new_location2]

### Dependents (imported by)
- [file1] → update import
- [file2] → update import

### Changes Required
- [ ] Update import paths
- [ ] Rename class/method if needed
- [ ] Split into multiple files if >700 lines

### Tests
- [ ] Update test imports
- [ ] Add new tests if needed
```

---

## 10. Risk Assessment

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broken imports during migration | High | Medium | Migrate in dependency order, test after each move |
| Test failures | Medium | Medium | Keep old tests working, add new tests incrementally |
| Circular dependencies | Medium | High | Define clear interfaces, use dependency injection |
| Performance regression | Low | High | Benchmark before/after, profile hot paths |
| Data migration issues | Low | Medium | Ensure backward compatibility for saved states |

### 10.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Underestimated file complexity | Medium | Medium | Add buffer time, prioritize critical paths |
| Dependency surprises | Medium | Medium | Document all dependencies before starting |
| Scope creep | Low | High | Stick to spec, defer improvements to post-migration |

### 10.3 Rollback Plan

If migration fails:

1. **Immediate**: Revert to backup branch
2. **Partial**: Keep completed phases, roll back current phase
3. **Data**: Ensure saved states are compatible with old version

### 10.4 Success Criteria

Migration is successful when:

1. All tests pass
2. No file exceeds 700 lines
3. All three systems have clear boundaries
4. Entry point works correctly
5. Documentation is updated
6. Coverage is maintained or improved

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Agent** | An autonomous entity that perceives, deliberates, and acts |
| **Environment** | The world simulation where agents exist |
| **Narrative** | The dramatic/story system that guides the simulation |
| **Percept** | A piece of information perceived by an agent |
| **Proposal** | An action request submitted to the environment |
| **Resolution** | The outcome of processing a proposal |
| **Tension** | Narrative pressure measured across dimensions |
| **Affordance** | Possible actions on an object |
| **Tick** | One simulation step (50ms at 20 TPS) |

---

## Appendix B: References

- `ARCHITECTURE_SPEC.md` - Existing architecture specification
- `ROADMAP.md` - Development roadmap
- `CLAUDE.md` - Project rules and standards
- `README.md` - Project overview

---

**Document Status:** Ready for Implementation  
**Next Steps:** Create backup branch, begin Phase 1## 3. Proposed Directory Structure

This structure strictly separates the three main systems and extracts shared services and transport layer. It incorporates the recently discovered gents/social/ subsystem and corrects missing files.

`	ext
tsukuyomi/
├── agents/                          # AGENT SYSTEM
│   ├── core/                        # Core abstractions
│   │   ├── base.py                  # BaseAgent ABC ← core/agent_base.py
│   │   ├── types.py                 # Agent-related types
│   │   ├── identity.py              # ← agent/identity.py
│   │   └── builder.py               # ← core/agent_builder.py
│   ├── cognitive/                   # Thinking systems
│   │   ├── perception.py            # ← brain/perception_pipeline.py
│   │   ├── perception_channels.py   # ← brain/perception_channels.py (SPLIT)
│   │   ├── channel_processors.py    # ← split from perception_channels.py
│   │   ├── deliberation.py          # ← brain/deliberation.py
│   │   ├── memory.py                # ← brain/memory_manager.py + working_memory.py
│   │   ├── memory_types.py          # ← brain/memory/memory_types.py
│   │   ├── memory_retrieval.py      # ← brain/memory/retrieval.py
│   │   ├── memory_decay.py          # ← brain/memory/decay_calculator.py
│   │   ├── rag_memory.py            # ← brain/rag_memory.py
│   │   └── reasoning/               # Reasoning and validation
│   │       ├── validator.py         # ← brain/reasoning/reasoning_validator.py (SPLIT)
│   │       ├── validator_rules.py   # ← split from reasoning_validator.py
│   │       ├── calibration.py       # ← brain/reasoning/confidence_calibration.py
│   │       ├── records.py           # ← brain/reasoning/decision_record.py
│   │       └── logger.py            # ← brain/reasoning/reasoning_logger.py
│   ├── internal/                    # Internal state
│   │   ├── emotion.py               # ← core/emotion/unified.py (SPLIT)
│   │   ├── mood.py                  # ← split from unified.py
│   │   ├── personality_baseline.py  # ← split from unified.py
│   │   ├── impact_rules.py          # ← split from unified.py
│   │   ├── expression.py            # ← proto/emotional_expression.py
│   │   ├── belief_system.py         # ← core/belief/system.py (SPLIT)
│   │   ├── belief_evidence.py       # ← split from belief/system.py
│   │   ├── beliefs/                 # ← core/belief/ (KEEP AS SUBMODULE)
│   │   │   ├── structures.py
│   │   │   ├── manager.py
│   │   │   ├── contradiction.py
│   │   │   └── ...
│   │   ├── needs.py                 # ← brain/needs_system.py
│   │   ├── relationships.py         # ← brain/relationship_manager.py
│   │   └── personality/             # Personality management
│   │       ├── profile.py           # ← brain/personality/profile.py
│   │       ├── sampler.py           # ← brain/personality/constraint_sampler.py
│   │       ├── drift.py             # ← brain/personality/drift_monitor.py (SPLIT)
│   │       └── drift_analysis.py    # ← split from drift_monitor.py
│   ├── social/                      # Social interaction
│   │   ├── gossip.py                # ← brain/gossip_protocol.py
│   │   ├── conversation.py          # ← proto/conversation_manager.py
│   │   ├── influence.py             # ← agent/influence.py
│   │   └── persuasion.py            # ← agent/persuasion.py
│   ├── runtime/                     # Agent implementations
│   │   ├── simulation_agent.py      # ← brain/agent_brain.py (refactored)
│   │   ├── standalone_agent.py      # ← agent/universal_agent.py
│   │   ├── behavior.py              # ← agent/behavior.py
│   │   └── proposal_handler.py      # ← agent/proposal_handler.py
│   └── prompts/                     # LLM prompts
│       ├── templates.py             # ← agent/immersive_prompt.py
│       └── context.py               # ← agent/context_manager.py
│
├── environment/                     # ENVIRONMENT SYSTEM
│   ├── core/
│   │   ├── engine.py                # ← proto/fate_engine.py + run() from fate_resolvers.py
│   │   ├── state.py                 # WorldState extract
│   │   ├── resolution.py            # ← resolution methods from proto/fate_resolvers.py
│   │   └── proposal.py              # ← core/proposal_window.py
│   ├── world/
│   │   ├── builder.py               # ← core/world_builder.py
│   │   ├── spatial.py               # ← core/spatial_index.py (SPLIT)
│   │   └── spatial_query.py         # ← split from spatial_index.py
│   ├── physics/
│   │   ├── affordance.py            # ← core/affordance.py
│   │   ├── raycasting.py            # ← brain/spatial_utils.py
│   │   └── spatial_logic.py         # ← proto/physics/spatial_logic.py
│   └── rules/
│       ├── action_logic.py          # ← proto/action_logic.py
│       └── preconditions.py         # Extract from resolution.py
│
├── narrative/                       # NARRATIVE SYSTEM
│   ├── core/
│   │   ├── director.py              # ← brain/drama_director.py
│   │   ├── tension.py               # Extract TensionVector types
│   │   └── catalyst.py              # ← brain/catalyst_system.py
│   ├── events/
│   │   ├── library.py               # ← core/drama/event_library.py
│   │   └── types.py                 # Extract event types
│   ├── flow/
│   │   ├── branching.py             # ← core/drama/branch_manager.py
│   │   ├── beats.py                 # Extract beat tracking
│   │   └── hooks.py                 # Tick hooks
│   └── context/
│       ├── context_aware.py         # ← core/drama/context_aware_director.py
│       └── evaluator.py             # Extract condition evaluation
│
├── services/                        # SHARED SERVICES
│   ├── llm/
│   │   ├── provider.py              # ← LLMProvider ABC from brain/llm_service.py
│   │   ├── openai_provider.py       # ← OpenAICompatibleProvider
│   │   ├── groq_provider.py         # ← GroqProvider
│   │   ├── service.py               # ← LLMService orchestrator
│   │   └── prompts.py               # ← prompt templates
│   ├── embedding/
│   │   └── service.py               # ← brain/embedding_service.py
│   ├── vector/
│   │   └── store.py                 # ← brain/vector_store.py
│   └── database/
│       └── manager.py               # ← proto/db_manager.py
│
├── transport/                       # COMMUNICATION LAYER
│   ├── grpc/
│   │   ├── server.py                # ← proto/grpc_server.py (GrpcServer)
│   │   ├── client.py                # ← proto/grpc_client.py
│   │   └── servicers/
│   │       ├── fate.py              # ← FateEngineServicer
│   │       └── guest.py             # ← GuestServicer
│   ├── sdk/
│   │   └── guest.py                 # ← guest_sdk.py
│   └── proto/                       # Generated protobuf files
│       └── *.pb2.py, *.pb2_grpc.py
│
├── scenarios/                       # SCENARIO DEFINITIONS
│   ├── schema.py                    # ← core/scenarios/scenario_schema.py
│   └── loader.py                    # ← core/scenarios/scenario_loader.py
│
└── shared/                          # COMMON UTILITIES
    ├── config.py                    # unified config management
    ├── logging.py                   # structured logging
    ├── exceptions.py                # custom exceptions
    ├── types.py                     # Common types
    └── utils.py                     # ← proto/utils.py + common helpers
`

## 4. System Specifications

### 4.1 Agent System Specification

```
agents/
├── core/                    # Core abstractions
│   ├── base.py             # BaseAgent abstract class
│   ├── types.py            # Agent-related types
│   └── agent_builder.py    # Factory for agent creation
├── cognitive/              # Thinking systems
│   ├── perception.py       # Perception pipeline
│   ├── deliberation.py     # Decision-making engine
│   └── memory.py           # Memory systems (episodic, semantic, working, RAG)
├── internal/               # Internal state
│   ├── emotion.py          # PAD emotional engine
│   ├── beliefs.py          # Belief tracking and bias
│   ├── needs.py            # Motivational drives (hunger, fatigue, etc.)
│   └── relationships.py    # Social relationships and affinity
├── runtime/                # Agent implementations
│   ├── simulation_agent.py # gRPC-connected agent for FateEngine
│   └── standalone_agent.py # Direct/async agent for testing
└── prompts/                # LLM prompt templates
    ├── templates.py        # Prompt template definitions
    └── context.py          # Context building utilities
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `BaseAgent` | `core/base.py` | Abstract interface for all agents |
| `AgentBuilder` | `core/agent_builder.py` | Factory for creating configured agents |
| `PerceptionPipeline` | `cognitive/perception.py` | Transform world state to percepts |
| `DeliberationEngine` | `cognitive/deliberation.py` | Think before acting |
| `MemorySystem` | `cognitive/memory.py` | Unified memory management |
| `EmotionalEngine` | `internal/emotion.py` | PAD emotional state |
| `BeliefTracker` | `internal/beliefs.py` | Evidence-based beliefs |
| `NeedsSystem` | `internal/needs.py` | Motivational drives |
| `RelationshipManager` | `internal/relationships.py` | Social state |
| `SimulationAgent` | `runtime/simulation_agent.py` | Connected to FateEngine |
| `StandaloneAgent` | `runtime/standalone_agent.py` | Independent execution |

### 4.2 Environment System Specification

```
environment/
├── core/                    # Core engine
│   ├── engine.py           # FateEngine - main tick loop
│   ├── state.py            # WorldState management
│   ├── resolution.py       # Proposal/action resolution
│   └── proposal.py         # Proposal window management
├── world/                   # World structure
│   ├── builder.py          # WorldBuilder API
│   ├── spatial.py          # SpatialIndex for proximity
│   ├── objects.py          # EnvironmentObject definitions
│   └── locations.py        # Location/zone definitions
├── physics/                 # Physical systems
│   ├── affordance.py       # Action validation
│   └── interactions.py     # Object interaction logic
└── rules/                   # Game rules
    ├── action_logic.py     # Action resolution rules
    ├── preconditions.py    # Precondition checkers
    └── effects.py          # Effect application
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `EnvironmentEngine` | `core/engine.py` | Main tick loop authority |
| `WorldState` | `core/state.py` | Immutable world snapshot |
| `ResolutionEngine` | `core/resolution.py` | Proposal resolution |
| `ProposalWindow` | `core/proposal.py` | Multi-tick proposal collection |
| `WorldBuilder` | `world/builder.py` | Programmatic world creation |
| `SpatialIndex` | `world/spatial.py` | Efficient proximity queries |
| `AffordanceValidator` | `physics/affordance.py` | Action preconditions |
| `ActionResolver` | `rules/action_logic.py` | Action-specific logic |

### 4.3 Narrative System Specification

```
narrative/
├── core/                    # Core narrative engine
│   ├── director.py         # DramaDirector - main orchestrator
│   ├── tension.py          # TensionVector calculation
│   └── catalyst.py         # Event injection system
├── events/                  # Event management
│   ├── library.py          # EventLibrary - event definitions
│   ├── types.py            # Event categories and types
│   └── selection.py        # Event selection algorithms
├── flow/                    # Story flow control
│   ├── branching.py        # Narrative branching logic
│   ├── beats.py            # Narrative beat tracking
│   └── hooks.py            # Pre/post tick hooks
└── context/                 # Context awareness
    ├── context_aware.py    # ContextAwareDramaDirector
    └── evaluator.py        # Condition evaluation
```

**Key Classes:**

| Class | Location | Purpose |
|-------|----------|---------|
| `NarrativeDirector` | `core/director.py` | Main narrative orchestrator |
| `TensionVector` | `core/tension.py` | Tension state representation |
| `CatalystSystem` | `core/catalyst.py` | Event injection |
| `EventLibrary` | `events/library.py` | Event definitions |
| `BranchManager` | `flow/branching.py` | Story branching |
| `BeatTracker` | `flow/beats.py` | Narrative beat scheduling |
| `ContextAwareDirector` | `context/context_aware.py` | Enhanced director |

### 4.4 Shared Services Specification

```
services/
├── llm/                     # LLM abstraction
│   ├── provider.py         # Abstract LLMProvider
│   ├── openai_provider.py  # OpenAI implementation
│   ├── groq_provider.py    # Groq implementation
│   ├── anthropic_provider.py # Anthropic implementation
│   └── prompts.py          # Prompt templates
├── embedding/               # Text embeddings
│   ├── service.py          # EmbeddingService
│   └── providers.py        # Embedding providers
├── vector/                  # Vector database
│   ├── store.py            # VectorStore abstraction
│   ├── qdrant_store.py     # Qdrant implementation
│   └── memory_store.py     # In-memory implementation
└── database/                # Persistence
    ├── manager.py          # Database manager
    └── models.py           # Data models
```

**Key Interfaces:**

| Interface | Location | Methods |
|-----------|----------|---------|
| `LLMProvider` | `llm/provider.py` | `generate()`, `stream()`, `health_check()` |
| `EmbeddingService` | `embedding/service.py` | `embed_text()`, `embed_batch()` |
| `VectorStore` | `vector/store.py` | `add_point()`, `search()`, `delete()` |
| `DatabaseManager` | `database/manager.py` | `save()`, `load()`, `query()` |

---

## 5. Directory Structure

### 5.1 Complete Directory Tree

```
tsukuyomi/
│
├── agents/                          # AGENT SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core abstractions
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseAgent ABC
│   │   ├── types.py                 # Agent-related types
│   │   └── agent_builder.py         # Factory pattern
│   │
│   ├── cognitive/                   # Thinking systems
│   │   ├── __init__.py
│   │   ├── perception.py            # PerceptionPipeline
│   │   ├── deliberation.py          # DeliberationEngine
│   │   └── memory.py                # Unified memory (episodic, semantic, RAG)
│   │
│   ├── internal/                    # Internal state
│   │   ├── __init__.py
│   │   ├── emotion.py               # PAD emotional engine
│   │   ├── beliefs.py               # BeliefTracker
│   │   ├── needs.py                 # NeedsSystem
│   │   └── relationships.py         # RelationshipManager
│   │
│   ├── runtime/                     # Agent implementations
│   │   ├── __init__.py
│   │   ├── simulation_agent.py      # gRPC-connected
│   │   └── standalone_agent.py      # Independent
│   │
│   └── prompts/                     # LLM prompts
│       ├── __init__.py
│       ├── templates.py             # Scenario templates
│       └── context.py               # Context builders
│
├── environment/                     # ENVIRONMENT SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core engine
│   │   ├── __init__.py
│   │   ├── engine.py                # EnvironmentEngine (main tick loop)
│   │   ├── state.py                 # WorldState management
│   │   ├── resolution.py            # Proposal resolution
│   │   └── proposal.py              # ProposalWindow
│   │
│   ├── world/                       # World structure
│   │   ├── __init__.py
│   │   ├── builder.py               # WorldBuilder
│   │   ├── spatial.py               # SpatialIndex
│   │   ├── objects.py               # EnvironmentObject
│   │   └── locations.py             # Location/Zone
│   │
│   ├── physics/                     # Physical systems
│   │   ├── __init__.py
│   │   ├── affordance.py            # AffordanceValidator
│   │   └── interactions.py          # Interaction logic
│   │
│   └── rules/                       # Game rules
│       ├── __init__.py
│       ├── action_logic.py          # Action resolution
│       ├── preconditions.py         # Precondition checkers
│       └── effects.py               # Effect application
│
├── narrative/                       # NARRATIVE SYSTEM
│   ├── __init__.py
│   │
│   ├── core/                        # Core narrative
│   │   ├── __init__.py
│   │   ├── director.py              # NarrativeDirector
│   │   ├── tension.py               # TensionVector
│   │   └── catalyst.py              # CatalystSystem
│   │
│   ├── events/                      # Event management
│   │   ├── __init__.py
│   │   ├── library.py               # EventLibrary
│   │   ├── types.py                 # Event types
│   │   └── selection.py             # Selection algorithms
│   │
│   ├── flow/                        # Story flow
│   │   ├── __init__.py
│   │   ├── branching.py             # BranchManager
│   │   ├── beats.py                 # BeatTracker
│   │   └── hooks.py                 # Tick hooks
│   │
│   └── context/                     # Context awareness
│       ├── __init__.py
│       ├── context_aware.py         # ContextAwareDirector
│       └── evaluator.py             # ConditionEvaluator
│
├── services/                        # SHARED SERVICES
│   ├── __init__.py
│   │
│   ├── llm/                         # LLM services
│   │   ├── __init__.py
│   │   ├── provider.py              # LLMProvider ABC
│   │   ├── openai_provider.py       # OpenAI
│   │   ├── groq_provider.py         # Groq
│   │   ├── anthropic_provider.py    # Anthropic
│   │   └── prompts.py               # Prompt templates
│   │
│   ├── embedding/                   # Embedding services
│   │   ├── __init__.py
│   │   ├── service.py               # EmbeddingService
│   │   └── providers.py             # Provider implementations
│   │
│   ├── vector/                      # Vector database
│   │   ├── __init__.py
│   │   ├── store.py                 # VectorStore ABC
│   │   ├── qdrant_store.py          # Qdrant
│   │   └── memory_store.py          # In-memory
│   │
│   └── database/                    # Persistence
│       ├── __init__.py
│       ├── manager.py               # DBManager
│       └── models.py                # Data models
│
├── transport/                       # COMMUNICATION LAYER
│   ├── __init__.py
│   │
│   ├── grpc/                        # gRPC implementation
│   │   ├── __init__.py
│   │   ├── server.py                # GrpcServer
│   │   ├── client.py                # GrpcClient
│   │   │
│   │   └── servicers/               # Service implementations
│   │       ├── __init__.py
│   │       ├── fate.py              # FateEngineServicer
│   │       └── guest.py             # GuestServicer
│   │
│   └── proto/                       # Protocol buffers
│       ├── __init__.py
│       ├── core_pb2.py              # Generated
│       ├── core_pb2_grpc.py         # Generated
│       ├── common_pb2.py            # Generated
│       ├── perception_pb2.py        # Generated
│       ├── fate_engine_service_pb2.py
│       ├── fate_engine_service_pb2_grpc.py
│       ├── guest_api_pb2.py
│       └── guest_api_pb2_grpc.py
│
├── shared/                          # COMMON UTILITIES
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── logging.py                   # Logging utilities
│   ├── exceptions.py                # Custom exceptions
│   ├── types.py                     # Common types
│   └── utils.py                     # Helper functions
│
├── scenarios/                       # SCENARIO DEFINITIONS
│   ├── __init__.py
│   ├── schema.py                    # Scenario configuration schema
│   └── loader.py                    # Scenario loader
│
├── experiments/                     # TEST SCENARIOS (preserve)
│   ├── scenarios/
│   └── logs/
│
├── tests/                           # TESTS (preserve structure)
│   └── [existing tests]
│
├── server.py                        # MAIN ENTRY POINT
├── __init__.py
├── requirements.txt
├── pytest.ini
└── README.md
```

### 5.2 File Size Guidelines

Each file must not exceed **700 lines of code**. If a file approaches this limit:

1. Extract related functionality into a submodule
2. Create a new file within the same package
3. Use composition to delegate responsibilities

---

## 6. Component Mapping

### 6.1 Detailed File Migration

| Source File | Destination | Changes Required |
|-------------|-------------|------------------|
| `core/agent_base.py` | `agents/core/base.py` | Minor import updates |
| `core/agent_builder.py` | `agents/core/agent_builder.py` | Minor import updates |
| `brain/agent_brain.py` | `agents/runtime/simulation_agent.py` | Split into multiple files |
| `agent/universal_agent.py` | `agents/runtime/standalone_agent.py` | Minor import updates |
| `agent/identity.py` | `agents/core/identity.py` | Move to core |
| `agent/immersive_prompt.py` | `agents/prompts/templates.py` | Merge with prompts |
| `core/emotion/base.py` | `agents/internal/emotion.py` | Merge with unified.py |
| `core/emotion/unified.py` | `agents/internal/emotion.py` | Consolidate, split if >700 lines |
| `core/belief/base.py` | `agents/internal/beliefs.py` | Merge with manager.py |
| `core/belief/manager.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/structures.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/logic.py` | `agents/internal/beliefs.py` | Merge |
| `core/belief/decay.py` | `agents/internal/beliefs.py` | Merge |
| `core/memory/base.py` | `agents/cognitive/memory.py` | Merge with memory_manager |
| `brain/memory_manager.py` | `agents/cognitive/memory.py` | Merge |
| `brain/rag_memory.py` | `agents/cognitive/memory.py` | Merge RAG functionality |
| `brain/working_memory.py` | `agents/cognitive/memory.py` | Merge |
| `brain/perception_pipeline.py` | `agents/cognitive/perception.py` | Minor updates |
| `brain/perception_channels.py` | `agents/cognitive/perception.py` | Merge |
| `brain/deliberation.py` | `agents/cognitive/deliberation.py` | Minor updates |
| `brain/needs_system.py` | `agents/internal/needs.py` | Minor updates |
| `brain/relationship_manager.py` | `agents/internal/relationships.py` | Minor updates |
| `proto/fate_engine.py` | `environment/core/engine.py` | Split responsibilities |
| `core/world_builder.py` | `environment/world/builder.py` | Minor updates |
| `core/spatial_index.py` | `environment/world/spatial.py` | Split if >700 lines |
| `core/affordance.py` | `environment/physics/affordance.py` | Minor updates |
| `core/proposal_window.py` | `environment/core/proposal.py` | Minor updates |
| `proto/action_logic.py` | `environment/rules/action_logic.py` | Minor updates |
| `proto/fate_resolvers.py` | `environment/core/resolution.py` | Merge |
| `brain/drama_director.py` | `narrative/core/director.py` | Minor updates |
| `brain/catalyst_system.py` | `narrative/core/catalyst.py` | Minor updates |
| `core/drama/context_aware_director.py` | `narrative/context/context_aware.py` | Minor updates |
| `core/drama/event_library.py` | `narrative/events/library.py` | Minor updates |
| `core/drama/branch_manager.py` | `narrative/flow/branching.py` | Minor updates |
| `brain/llm_service.py` | `services/llm/provider.py` | Split into multiple files |
| `brain/embedding_service.py` | `services/embedding/service.py` | Minor updates |
| `brain/vector_store.py` | `services/vector/store.py` | Minor updates |
| `proto/db_manager.py` | `services/database/manager.py` | Minor updates |
| `proto/grpc_server.py` | `transport/grpc/server.py` | Minor updates |
| `proto/grpc_client.py` | `transport/grpc/client.py` | Minor updates |

### 6.2 Files to Delete (Duplicates/Obsolete)

| File | Reason |
|------|--------|
| `core/belief/existential.py` | Consolidate into beliefs.py |
| `core/belief/contradiction.py` | Consolidate into beliefs.py |
| `core/memory/__init__.py` | Move content to cognitive/memory.py |
| `core/emotion/__init__.py` | Move content to internal/emotion.py |
| `agent/memory_system.py` | Duplicate of memory_manager, consolidate |
| `agent/memory.py` | Duplicate, consolidate |
| `agent/behavior.py` | Consolidate into runtime or cognitive |
| `agent/conversation.py` | Consolidate into relationships or prompts |
| `agent/influence.py` | Consolidate into relationships |
| `agent/personality.py` | Consolidate into internal/emotion.py |
| `agent/context_manager.py` | Consolidate into cognitive/perception.py |
| `agent/decision_engine.py` | Consolidate into cognitive/deliberation.py |
| `agent/proposal_handler.py` | Consolidate into runtime |
| `agent/persuasion.py` | Consolidate into relationships |

---

## 7. Interface Definitions

### 7.1 Agent System Interfaces

```python
# agents/core/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    PERCEIVING = "perceiving"
    DELIBERATING = "deliberating"
    ACTING = "acting"
    PAUSED = "paused"

@dataclass
class Percept:
    """A piece of perceived information."""
    percept_id: str
    channel: str  # visual, auditory, social, internal
    content: Dict[str, Any]
    salience: float
    tick: int

@dataclass
class Decision:
    """A decision made by the agent."""
    action: str
    params: Dict[str, Any]
    thought: str
    confidence: float
    reasoning_chain: List[str]

@dataclass
class Proposal:
    """An action proposal to submit to the environment."""
    proposal_id: str
    actor_id: str
    action: str
    params: Dict[str, Any]
    timestamp: float

class BaseAgent(ABC):
    """
    Abstract base class for all Tsukuyomi agents.
    
    All agents must implement the perceive-deliberate-act cycle
    and lifecycle management methods.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state = AgentState.IDLE
        self._running = False
        self._paused = False
    
    @abstractmethod
    async def perceive(self, world_state: Any) -> List[Percept]:
        """
        Process world state into percepts.
        
        Args:
            world_state: Current world state from environment
            
        Returns:
            List of salient percepts
        """
        pass
    
    @abstractmethod
    async def deliberate(self, percepts: List[Percept]) -> Decision:
        """
        Make a decision based on percepts.
        
        Args:
            percepts: List of perceived information
            
        Returns:
            Decision with action and parameters
        """
        pass
    
    @abstractmethod
    async def act(self, decision: Decision) -> Proposal:
        """
        Convert decision to action proposal.
        
        Args:
            decision: The decision to act on
            
        Returns:
            Proposal to submit to environment
        """
        pass
    
    # Lifecycle management
    @abstractmethod
    def start(self) -> None:
        """Start the agent."""
        pass
    
    @abstractmethod
    def pause(self) -> None:
        """Pause agent processing."""
        pass
    
    @abstractmethod
    def resume(self) -> None:
        """Resume agent processing."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources before shutdown."""
        pass
```

### 7.2 Environment System Interfaces

```python
# environment/core/engine.py

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Awaitable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EngineConfig:
    """Configuration for the environment engine."""
    tick_rate: int = 20
    proposal_window_ms: int = 25
    seed: Optional[int] = None
    db_path: Optional[str] = None
    enable_phase2: bool = True
    multi_tick_window: int = 3
    spatial_cell_size: float = 10.0

class EnvironmentEngine:
    """
    The authoritative simulation engine.
    
    Manages world state, tick loop, and action resolution.
    Does NOT make decisions for agents or control narrative.
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.current_tick = 0
        self.running = False
        self._paused = False
        
        # Hooks for external systems (e.g., narrative)
        self._pre_tick_hooks: List[Callable[[int], Awaitable[None]]] = []
        self._post_tick_hooks: List[Callable[[int, List], Awaitable[None]]] = []
    
    async def run(self) -> None:
        """
        Main simulation loop.
        
        Runs indefinitely until stopped.
        """
        pass
    
    async def submit_proposal(self, proposal: Any) -> bool:
        """
        Submit an action proposal for consideration.
        
        Args:
            proposal: The proposal to submit
            
        Returns:
            True if accepted into queue, False if rejected
        """
        pass
    
    def get_world_state(self) -> Any:
        """
        Get current world state snapshot.
        
        Returns:
            Immutable world state
        """
        pass
    
    def register_actor(self, actor_id: str, name: str, position: tuple) -> None:
        """Register a new actor in the world."""
        pass
    
    def unregister_actor(self, actor_id: str) -> None:
        """Remove an actor from the world."""
        pass
    
    # Hook management
    def add_pre_tick_hook(self, hook: Callable[[int], Awaitable[None]]) -> None:
        """Add a hook to run before each tick."""
        self._pre_tick_hooks.append(hook)
    
    def add_post_tick_hook(self, hook: Callable[[int, List], Awaitable[None]]) -> None:
        """Add a hook to run after each tick (receives resolutions)."""
        self._post_tick_hooks.append(hook)
    
    # Lifecycle
    def stop(self) -> None:
        """Stop the simulation."""
        pass
    
    def pause(self) -> None:
        """Pause the simulation."""
        pass
    
    def resume(self) -> None:
        """Resume the simulation."""
        pass
```

### 7.3 Narrative System Interfaces

```python
# narrative/core/director.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class EventCategory(Enum):
    CONFLICT = "conflict"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    NARRATIVE = "narrative"
    MYSTERY = "mystery"

@dataclass
class Event:
    """A narrative event that can be injected into the simulation."""
    id: str
    category: EventCategory
    description: str
    target_agent: Optional[str] = None
    broadcast: bool = True
    context_tags: List[str] = None
    params: Dict[str, Any] = None

@dataclass
class TensionVector:
    """Current narrative tension state."""
    conflict: float = 0.0
    mystery: float = 0.0
    social: float = 0.0
    emotion: float = 0.0
    
    @property
    def aggregate(self) -> float:
        return (self.conflict + self.mystery + self.social + self.emotion) / 4

@dataclass
class NarrativeConfig:
    """Configuration for narrative director."""
    boredom_threshold: float = 0.2
    tension_threshold_high: float = 0.8
    tension_decay_rate: float = 0.001
    min_injection_interval: int = 100

class NarrativeDirector:
    """
    Orchestrates narrative flow and dramatic tension.
    
    Monitors simulation state and injects events when needed.
    Does NOT control agent decisions or modify world state directly.
    """
    
    def __init__(self, engine: Any, config: NarrativeConfig):
        self.engine = engine
        self.config = config
        self.current_tension = TensionVector()
        
        # Attach to engine hooks
        engine.add_post_tick_hook(self._on_tick_resolved)
    
    def evaluate_tick(
        self, 
        tick: int, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """
        Evaluate if narrative intervention is needed.
        
        Args:
            tick: Current simulation tick
            world_state: Current world state
            agent_states: Current agent states
            
        Returns:
            Event to inject, or None if no intervention needed
        """
        pass
    
    def update_tension(self, event: Event) -> None:
        """
        Update tension based on an event.
        
        Args:
            event: The event that occurred
        """
        pass
    
    def get_tension_status(self) -> TensionVector:
        """Get current tension state."""
        return self.current_tension
    
    async def _on_tick_resolved(self, tick: int, resolutions: List) -> None:
        """Internal hook handler."""
        # Update tension from resolutions
        # Check for intervention
        pass
```

### 7.4 Service Interfaces

```python
# services/llm/provider.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncIterator
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    thought: str = ""
    action: str = "IDLE"
    params: Dict[str, Any] = None
    tokens_used: Optional[int] = None
    provider: str = "unknown"

@dataclass
class PromptContext:
    """Context for LLM prompt generation."""
    agent_name: str
    agent_backstory: str
    scenario_type: str
    working_memory: str = ""
    beliefs: str = ""
    relationships: str = ""
    emotional_state: str = ""
    world_context: str = ""
    additional_context: Dict[str, Any] = None

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Implementations: OpenAI, Groq, Anthropic, etc.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[PromptContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Generate a complete response.
        
        Args:
            prompt: The prompt to send
            context: Optional context for the prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured response
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        context: Optional[PromptContext] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream response token by token.
        
        Args:
            prompt: The prompt to send
            context: Optional context for the prompt
            temperature: Sampling temperature
            
        Yields:
            Individual tokens
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
```

---

## 8. Implementation Phases

### 8.1 Phase 1: Create Directory Structure (Day 1)

**Objective:** Create new directory structure without modifying files.

**Tasks:**
1. Create all new directories
2. Create `__init__.py` files in each directory
3. Add placeholder imports in `__init__.py` files
4. Verify no import errors

**Validation:**
- `python -c "import tsukuyomi"` succeeds
- All directories exist with proper structure

### 8.2 Phase 2: Move Files (Days 2-3)

**Objective:** Move files to new locations without modification.

**Tasks:**
1. Move files according to mapping table (Section 6.1)
2. Update import paths in moved files
3. Update import paths in dependent files
4. Run tests to identify broken imports

**Order of Migration:**
1. `shared/` - No dependencies
2. `services/` - Depends only on shared
3. `transport/proto/` - Generated files, no changes
4. `environment/` - Core engine
5. `narrative/` - Depends on environment
6. `agents/` - Depends on all above

**Validation:**
- All imports resolve correctly
- `pytest tests/` runs (may have failures)

### 8.3 Phase 3: Refactor Classes (Days 4-6)

**Objective:** Split large files and consolidate duplicates.

**Priority Order:**

| File | Lines | Action |
|------|-------|--------|
| `core/emotion/unified.py` | 1375+ | Split into emotion.py + mood.py + personality.py |
| `brain/llm_service.py` | 825 | Split into provider.py + prompts.py |
| `core/spatial_index.py` | 857 | Split into spatial.py + query.py + stats.py |
| `brain/agent_brain.py` | 694 | Already split by new structure |

**Tasks:**
1. Identify cohesive modules within large files
2. Extract into separate files
3. Update imports
4. Add deprecation warnings to old imports

**Validation:**
- All files under 700 lines
- Tests pass

### 8.4 Phase 4: Create Unified Entry Point (Day 7)

**Objective:** Create `server.py` as single entry point.

**Tasks:**
1. Create `server.py` with:
   - Configuration loading
   - Engine initialization
   - Narrative director setup
   - gRPC server startup
   - Graceful shutdown
2. Create `shared/config.py` for configuration management
3. Create `scenarios/schema.py` for scenario definitions
4. Update documentation

**Validation:**
- `python server.py --scenario marketplace` starts correctly
- Graceful shutdown works

### 8.5 Phase 5: Update Tests (Days 8-9)

**Objective:** Update all tests to match new structure.

**Tasks:**
1. Update test imports
2. Create new test files for new modules
3. Add integration tests for system boundaries
4. Verify all tests pass

**Validation:**
- `pytest tests/ -v` passes
- Coverage maintained or improved

### 8.6 Phase 6: Cleanup (Day 10)

**Objective:** Remove obsolete files and finalize.

**Tasks:**
1. Delete obsolete files (Section 6.2)
2. Remove empty directories
3. Update `README.md`
4. Update `requirements.txt` if needed


**Validation:**
- No broken imports
- All tests pass
- Documentation updated

---

## 9. Migration Checklist

### 9.1 Pre-Migration

- [ ] Create backup branch
- [ ] Run full test suite, record results
- [ ] Document current coverage
- [ ] List all external dependencies

### 9.2 During Migration

- [ ] Create new directories
- [ ] Move files in dependency order (shared → services → transport → environment → narrative → agents)
- [ ] Update imports after each move
- [ ] Run tests after each major move
- [ ] Refactor large files
- [ ] Create entry point

### 9.3 Post-Migration

- [ ] All tests pass
- [ ] Coverage maintained
- [ ] No files exceed 700 lines
- [ ] Documentation updated
- [ ] Migration guide created

### 9.4 Per-File Migration Template

For each file migration:

```markdown
## File: [source_file] → [destination_file]

### Dependencies (imports)
- [dep1] → [new_location1]
- [dep2] → [new_location2]

### Dependents (imported by)
- [file1] → update import
- [file2] → update import

### Changes Required
- [ ] Update import paths
- [ ] Rename class/method if needed
- [ ] Split into multiple files if >700 lines

### Tests
- [ ] Update test imports
- [ ] Add new tests if needed
```

---

## 10. Risk Assessment

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broken imports during migration | High | Medium | Migrate in dependency order, test after each move |
| Test failures | Medium | Medium | Keep old tests working, add new tests incrementally |
| Circular dependencies | Medium | High | Define clear interfaces, use dependency injection |
| Performance regression | Low | High | Benchmark before/after, profile hot paths |
| Data migration issues | Low | Medium | Ensure backward compatibility for saved states |

### 10.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Underestimated file complexity | Medium | Medium | Add buffer time, prioritize critical paths |
| Dependency surprises | Medium | Medium | Document all dependencies before starting |
| Scope creep | Low | High | Stick to spec, defer improvements to post-migration |

### 10.3 Rollback Plan

If migration fails:

1. **Immediate**: Revert to backup branch
2. **Partial**: Keep completed phases, roll back current phase
3. **Data**: Ensure saved states are compatible with old version

### 10.4 Success Criteria

Migration is successful when:

1. All tests pass
2. No file exceeds 700 lines
3. All three systems have clear boundaries
4. Entry point works correctly
5. Documentation is updated
6. Coverage is maintained or improved

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Agent** | An autonomous entity that perceives, deliberates, and acts |
| **Environment** | The world simulation where agents exist |
| **Narrative** | The dramatic/story system that guides the simulation |
| **Percept** | A piece of information perceived by an agent |
| **Proposal** | An action request submitted to the environment |
| **Resolution** | The outcome of processing a proposal |
| **Tension** | Narrative pressure measured across dimensions |
| **Affordance** | Possible actions on an object |
| **Tick** | One simulation step (50ms at 20 TPS) |

---

## Appendix B: References

- `ARCHITECTURE_SPEC.md` - Existing architecture specification
- `ROADMAP.md` - Development roadmap
- `CLAUDE.md` - Project rules and standards
- `README.md` - Project overview

---

**Document Status:** Ready for Implementation  
**Next Steps:** Create backup branch, begin Phase 1### Known Violations (To Be Refactored)
| Component | Current Size | Target Size | Refactor Strategy |
|-----------|--------------|-------------|-------------------|
| `core/emotion/unified.py` | 1426 lines | 4 files < 500L | Split into emotion.py, mood.py, personality_baseline.py, and impact_rules.py. |
| `brain/memory/retrieval.py` | 763 lines | 2 files < 500L | Split into retrieval.py and retrieval_strategies.py. |
| `core/belief/system.py` | 957 lines | 2 files < 500L | Split into belief_system.py and belief_evidence.py. |
| `brain/reasoning/reasoning_validator.py` | ~870 lines | 2 files < 500L | Split into validator.py and validator_rules.py. |
| `brain/personality/drift_monitor.py` | ~850 lines | 2 files < 500L | Split into drift.py and drift_analysis.py. |
| `brain/llm_service.py` | 825 lines | 5 files < 200L | Split into provider.py, openai_provider.py, groq_provider.py, service.py, prompts.py. |
| `brain/perception_channels.py` | ~800 lines | 2 files < 500L | Split into perception_channels.py and channel_processors.py. |
| `core/spatial_index.py` | 857 lines | 2 files < 500L | Split into spatial.py and spatial_query.py. |
| `brain/agent_brain.py` | 694 lines | TBD | Reconstruct into Runtime architecture, heavily delegating to new subsystems. |

### 5.4 Files to Refactor/Keep (Previously thought obsolete)

> **Note**: These files contain distinct logic and must NOT be deleted. They are being moved exactly as follows:
- gent/persuasion.py (870L) -> gents/social/persuasion.py
- gent/influence.py (324L) -> gents/social/influence.py
- proto/conversation_manager.py (630L) -> gents/social/conversation.py
- rain/gossip_protocol.py (419L) -> gents/social/gossip.py
- gent/behavior.py -> gents/runtime/behavior.py
- gent/proposal_handler.py -> gents/runtime/proposal_handler.py
- gent/context_manager.py -> gents/prompts/context.py
- gent/decision_engine.py -> Review against gents/cognitive/deliberation.py

### 5.5 Environment Core Duplication Fix
- proto/fate_resolves.py and proto/fate_engine.py duplicate core logic (like the run/tick loop).
- **Target**: proto/fate_engine.py and the 
un() tick loop of ate_resolvers.py merge to form nvironment/core/engine.py.
- **Target**: The resolution-specific methods of ate_resolvers.py break off to form nvironment/core/resolution.py.

## 7. Implementation Phases (Corrected)

### Phase 1: Shared Utilities
Create shared/ directory and populate:
- Create config.py, logging.py, xceptions.py
- Move and merge proto/utils.py and common types into shared/types.py and shared/utils.py

### Phase 2: Shared Services & Large Splits
Create services/ directory:
- Split rain/llm_service.py (825L) into 5 files under services/llm/
- Move rain/embedding_service.py to services/embedding/service.py
- Move rain/vector_store.py to services/vector/store.py
- Move proto/db_manager.py to services/database/manager.py

### Phase 3: Scenarios
Move existing scenario pipeline:
- Move core/scenarios/scenario_schema.py to scenarios/schema.py
- Move core/scenarios/scenario_loader.py to scenarios/loader.py

### Phase 4: Transport Layer
Create 	ransport/ directory:
- Move compiled proto files
- Move proto/grpc_client.py to 	ransport/grpc/client.py
- Split proto/grpc_server.py into Server, FateServicer, and GuestServicer
- Move guest_sdk.py to 	ransport/sdk/guest.py

### Phase 5: Environment System
Create nvironment/ directory:
- Untangle FateEngine and FateResolvers into ngine.py and 
esolution.py
- Split core/spatial_index.py (857L) into spatial.py and spatial_query.py
- Move rain/spatial_utils.py (Raycaster) to nvironment/physics/raycasting.py
- Move proto/physics/spatial_logic.py to nvironment/physics/spatial_logic.py
- Move world builder and affordance.

### Phase 6: Narrative System
Create 
arrative/ directory:
- Move drama director, catalyst system, event library, branch manager, etc. Extract types.

### Phase 7: Agent System (Biggest Phase)
Create gents/ directory:
- Move standalone agent and identity to core/ and 
untime/
- Move/split perception pipeline and deliberation
- **Size Violations**: Split core/emotion/unified.py (1426L), core/belief/system.py (957L), rain/perception_channels.py (~800L), rain/reasoning/reasoning_validator.py (~870L), rain/personality/drift_monitor.py (~850L) into proper files.
- **Missing files**: Move rain/memory/, rain/personality/, rain/reasoning/ contents exactly as mapped.
- **Social**: Create gents/social/ and move gossip.py, conversation.py, persuasion.py, influence.py.

### Phase 8: Entry Point & Tests & Cleanup
- Create unified server.py in the root folder.
- Update all 57 test files in 	ests/ with new import paths.
- Remove old empty directories (rain/, gent/, core/, proto/).


