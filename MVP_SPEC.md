# TSUKUYOMI - Minimum Viable Product (MVP) Specification
**Version:** 1.1
**Codename:** `Tsukuyomi`
**Author:** OpenClaw Agent (Tanit)
**Date:** 2026-02-04
**Status:** Completed (Phase 1)

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Architectural Overview](#2-architectural-overview)
3. [Core Components](#3-core-components)
    3.1. [Fate Engine](#31-fate-engine)
    3.2. [Reflex Layer (System 1)](#32-reflex-layer-system-1)
    3.3. [Deliberator (System 2)](#33-deliberator-system-2)
4. [Key Design Principles](#4-key-design-principles)
5. [Data Flow & Consistency](#5-data-flow--consistency)
6. [Agent Architecture](#6-agent-architecture)
7. [Operational Aspects](#7-operational-aspects)
8. [Implementation Roadmap (MVP)](#8-implementation-roadmap-mvp)
9. [API Contracts (Protobuf Definitions)](#9-api-contracts-protobuf-definitions)

---

## 1. Executive Summary

**Tsukuyomi** is a generative simulation engine designed to create dynamic, living worlds populated by intelligent, autonomous agents. It resolves the "Latency vs. Intelligence" trade-off through a **Dual-Mode Cognitive Architecture** (System 1 Reflexes + System 2 Deliberation) and ensures data integrity via a **CQRS (Command Query Responsibility Segregation)** model. The MVP establishes a deterministic core simulation loop (Fate Engine), integrates a reactive reflex layer, and uses Protobuf-defined gRPC contracts for all interactions.

## 2. Architectural Overview

Tsukuyomi employs a CQRS pattern with Event Sourcing. The **Fate Engine** is the authoritative core, orchestrating logical tick loops, resolving agent proposals, and maintaining the canonical world state. 

### Component Interaction
- **Fate Engine:** Central authority, deterministic loop.
- **Reflex Layer (System 1):** Low-latency heuristic proposals (<50ms).
- **Deliberator (System 2):** High-latency LLM-based deliberation (asynchronous).
- **Observers:** External clients streaming world state updates.

## 3. Core Components

### 3.1. Fate Engine

The central authority for the simulation.
*   **Logical Tick Loop:** 20 Ticks Per Second (TPS).
*   **Proposal System:** Collection and deterministic sorting of agent actions.
*   **Resolution Logic:** Rule-based outcomes (Movement, Interaction, Emotes).
*   **World State:** Authoritative repository of Actors and Locations.
*   **Tick History:** Persisted state snapshots for debugging and deterministic replay.

### 3.2. Reflex Layer (System 1)

Represents fast, heuristic, reactive cognition.
*   **Latency:** Synchronous with tick (<50ms).
*   **Mechanism:** Finite State Machines (FSM) or rule-based logic.
*   **Output:** Generates `Proposals` (e.g., reactive movement toward a target).

### 3.3. Deliberator (System 2)

Asynchronous, high-level cognition (Future Phase).
*   **Mechanism:** LLM-driven planning and memory retrieval.
*   **Integration:** Submits proposals to the Fate Engine asynchronously.

## 4. Key Design Principles

*   **Logical Time Authority:** Simulation time is discrete Ticks.
*   **Deterministic Replay:** Seeded RNG and sorted proposal resolution.
*   **API-First Architecture:** Strict adherence to Protobuf/gRPC contracts.
*   **Latency Separation:** Reflexes stay in-sync; deliberation happens off-loop.

## 5. Data Flow & Consistency

1.  **Proposal Generation:** Reflex Layer or external client creates a `Proposal`.
2.  **Ingestion:** Fate Engine queues proposals in the current tick's window.
3.  **Resolution:** Fate Engine resolves proposals based on world rules.
4.  **State Update:** `WorldState` is updated; `Resolutions` are generated.
5.  **Broadcast:** `TickState` (State + Proposals + Resolutions) is published.

## 6. Agent Architecture (MVP)

Agents are represented as `Actor` objects in the `WorldState`.
- **Identity:** Unique UUID.
- **State:** Position, Current Location, Interaction History.
- **Agency:** Ability to submit `Proposals` via System 1 (integrated) or gRPC.

## 7. Operational Aspects

*   **Observability:** Structured logging of tick duration and lag warnings.
*   **Storage:** Per-tick snapshots in `TickHistory`.
*   **Network:** Protobuf binary serialization for low-overhead transmission.

## 8. Implementation Roadmap (MVP)

### Phase 1: Core Engine & Protobuf Contracts (✅ COMPLETED)
- Defined `.proto` files (`common.proto`, `core.proto`, `fate_engine_service.proto`).
- Generated Python Protobuf bindings.
- Implemented `fate_engine.py` using Protobuf data structures.
- Implemented `MOVE`, `INTERACT`, `IDLE`, `EMOTE` resolution.
- Integrated `ReflexLayer` for autonomous NPC movement.
- Verified deterministic loop via `demo_fate_engine`.

### Phase 2: gRPC Server & Client (✅ COMPLETED)
- Implemented `FateEngineService` gRPC server (`grpc_server.py`).
- Exposed `SubmitProposal`, `GetWorldState`, and `StreamTickUpdates`.
- Developed Python gRPC client (`grpc_client.py`) for external agent interaction.
- Full test suite: 26 tests passing (14 gRPC + 12 Fate Engine).

### Phase 3: Enhanced Simulation & Persistence (NEXT)
- Expand world state with varied environmental objects.
- Implement persistent storage for `TickHistory` (SQL or Event Store).
- Basic web-based visualizer for world state observation.

---

## 9. API Contracts (Protobuf Definitions)

### 9.1. Core Entities (`core.proto`)
- `Actor`: UUID, Position, State, Current Location.
- `Proposal`: Actor ID, Action Type (MOVE, INTERACT, etc.), Parameters.
- `Resolution`: Success/Failure, Outcome data, Reason.
- `WorldState`: Tick Number, Actors map, Locations map.
- `TickState`: Snapshot of WorldState + Proposals + Resolutions.

### 9.2. Services (`fate_engine_service.proto`)
- `SubmitProposal`: Unary RPC for action submission.
- `GetWorldState`: Unary RPC for state query.
- `StreamTickUpdates`: Server-streaming RPC for real-time observation.
