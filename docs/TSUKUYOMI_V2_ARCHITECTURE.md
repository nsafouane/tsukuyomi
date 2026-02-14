# 📚 Tsukuyomi Engine V2 - Full Technical Design & Architecture Report

**Date:** 2026-02-14
**Status:** Proposed Architecture (Post-Iteration 1 Analysis)

## 1. 🎯 Executive Summary

The **Tsukuyomi Engine** is designed to facilitate **Massive Multi-Agent Simulations (MAS)** using LLM-driven cognitive models. The primary goal is to enable "Real World Simulations" where autonomous agents interact, trade, fight, and live in a persistent, dynamic environment, rather than just processing static text prompts.

**Key Shift from V1:**
*   **V1:** "Angry Men" style. Agents in a static box. Reliant on dialogue prompts. No persistent objects.
*   **V2:** "Busy Marketplace" style. Agents in a dynamic world. Spatial navigation. Object affordances. Resource economy.

---

## 2. 🦾 Component 1: Fate Engine (The Core)

**Role:** The authoritative server simulation loop. It is the "source of truth" for the world state.

### 2.1 Current Architecture (V1)
*   **Language:** Python 3.10+.
*   **Async Runtime:** `asyncio` for non-blocking I/O.
*   **Communication:** gRPC (Bidirectional streaming).
*   **State Management:** In-memory dictionaries (`self.actors`, `self.world_state`).
*   **Tick Mechanism:** Fixed duration (configurable, typically ~100ms).
*   **Concurrency:** Handles simultaneous streams from multiple clients (Agent Brains).

### 2.2 V2 Architecture Requirements

To support "Real World Simulations", the Fate Engine requires three major upgrades:

#### A. Spatial Indexing (Partitioning)
**Problem:** In V1, checking collisions or "nearby" agents was O(N) against all world objects. This scales poorly.
**Solution:** Implement a **Spatial Index** (Quadtree or Grid).
*   **Implementation Details:**
    *   `SpatialIndex.add(obj, position)`: Insert object.
    *   `SpatialIndex.query(position, radius)`: Return list of IDs within radius.
    *   **Benefit:** Enables complex crowd simulation (100+ agents) with minimal lag.

#### B. Proposal Windows (Commitment Phase)
**Problem:** Agents acted instantly. If Agent A decided to move to (10,10), Agent B decided to move to (10,10) in the same tick, simple logic determined "who arrived first".
**Solution:** Introduce a **Time Window** for proposals.
*   **Mechanism:**
    1.  Engine opens window (e.g., Ticks 100-105).
    2.  Agents submit proposals.
    3.  Engine closes window.
    4.  Engine sorts proposals (e.g., by timestamp, speed).
    5.  Engine resolves proposals sequentially or simultaneously with conflict logic.
*   **Benefit:** Supports "fast-paced combat" and "simultaneous interaction" without logic breaking.

#### C. Conflict Resolution
**Problem:** "Last write wins" was the only logic. Two agents grabbing the same coin succeeded.
**Solution:** **Conflict Resolver** module.
*   **Logic:**
    *   `ActionPriority`: EMOTE (social) > INTERACT (physical) > MOVE.
    *   `Stamina`: Agent with higher stamina wins physical conflicts.
    *   `Randomness`: Small chance factor to prevent stalemates.
*   **Benefit:** Enables emergent behavior (Theft, wrestling, blocking).

### 2.3 gRPC Protocol Specification
The `core.proto` file defines the data contract between Agent Brains and the Server.

**Key Messages:**
*   **`Actor`**: `{id, name, position (Vector2), state, inventory, interactions}`
*   **`Proposal`**: `{proposal_id, actor_id, action (enum), parameters (map<string, string>)}`
*   **`Resolution`**: `{proposal_id, success, outcome (details), modified_action}`
*   **`EnvironmentObject`**: `{id, type, position, properties (map), affordances (list)}`

---

## 3. 🧠 Component 2: Agent Brain (The Intelligence)

**Role:** Client-side controller. Acts as the "Cortex" for the agent.

### 3.1 Perception Pipeline
How the agent sees the world.

*   **`ProximityHeartbeat`**: Low-freq check. "Is anyone within 2 meters?"
*   **`DeepPerception`**: High-freq scan. "What are the distinct objects in the room?"
*   **`VisualPerception` (Future)**: Raycasting. "Can I see the thief behind the pillar?"

**V2 Change:** Add **Tagging**.
*   *Old:* Logs raw list: `[actor_1, actor_2, obj_1]`
*   *New:* Logs tagged percepts: `[PERCEPT:PROXIMITY:PLAYER_NEAR(actor_1), PERCEPT:VISUAL:PROP(table)]`
*   *Benefit:* LLM can filter relevant info faster.

### 3.2 The "Static Loop" Fix (Drive System)
**Problem:** Agents did nothing in an empty room because "Do nothing" was the safest option.
**Solution:** **Needs System** (Internal Motivational Model).
*   **Implementation:**
    *   Variables tracked: `Hunger`, `Fatigue`, `Boredom`, `SocialNeed`.
    *   Decay mechanism: Values increase every tick.
    *   Thresholds: `Hunger > 0.8` triggers "Find Food" goal.
    *   Prompt Injection: "Your hunger is 85%. You see an apple stall. What do you do?"
*   **Benefit:** Agents become autonomous actors seeking goals, not just passive chatbots.

### 3.3 Memory Architecture
*   **Short-Term:** `GossipProtocol` (Key-Value store). "Did you see X?" (Valid for 1-2 ticks).
*   **Long-Term:** (Future V3) `RAG (Retrieval-Augmented Generation)`.
    *   Vector DB (e.g., Qdrant).
    *   Store memories: "The merchant overcharged me."
    *   Query: `memories.similar("merchant")` -> Influence LLM decisions.

---

## 4. 🌍 Component 3: World Management (The Stage)

**Role:** Defines the environment, objects, and rules of physics/interaction.

### 4.1 Object Affordances
**Concept:** An object defines what *can* happen to it.
**Structure:**
```python
Affordance = {
    "action_type": "COLLECT",
    "precondition": "distance < 1.5 AND agent.holding == False",
    "effect_description": "agent.inventory.add(item_id)"
}
```

**Examples:**
*   **Door:** `OPEN` (if unlocked), `LOCK` (if key).
*   **Stall:** `INTERACT` (Buy), `COLLECT` (Steal).
*   **Water:** `COLLECT` (Fill canteen).

### 4.2 WorldBuilder API
**Goal:** Decouple world design from engine code.
**API Design:**
```python
builder = WorldBuilder()
builder.add_location("TownSquare", Vector2(0,0))
builder.add_object("fountain", "decoration", Vector2(5,5), {"water": "true"})
builder.add_agent("merchant", "Marcus", "Merchant")
await client.initialize_world(builder.serialize())
```

---

## 5. 🗣️ Component 4: Orchestration (The Director)

**Role:** Ensures the story moves forward. Prevents "sandbox death" (agents idling forever).

### 5.1 Tension Metrics
**Problem:** Simulation is stable but boring.
**Solution:** Track 4-dimensional tension.
*   **`Cognitive` (Confusion):** Is the situation too complex for agents?
*   **`Social` (Conflict):** Are agents arguing?
*   **`Moral` (Dilemma):** Are agents breaking taboos?
*   **`Emotional` (Intensity):** Are agents screaming/fighting?

### 5.2 Plot Orchestration
**Mechanism:** If `aggregate_tension` is < 0.2 for > 10 ticks, inject an event.
*   **Event Types:**
    *   "Environmental": Lights flicker, wind blows.
    *   "Systemic": Fire alarm, gong rings.
    *   "Narrative": A courier enters with news.

---

## 6. 🗃️ Component 5: LLM Integration (The Voice)

**Role:** Provides the reasoning power. Maps observations to JSON actions.

### 6.1 Optimization Strategy
*   **Prompt Caching:** System prompts ("You are a juror...") are static. Cache the fully rendered string. Do not re-render for every tick.
*   **Streaming:** Use `stream=True` in API calls. Stop generation if the model enters "thinking" mode (e.g., `(thinking)`) which is slow/costly. We only need the final JSON action.
*   **JSON Mode:** Force the model to output strictly JSON. Reduces parsing errors and allows for structured data extraction.

### 6.2 Rate Limit Handling
*   **Provider:** Groq (free tier) has strict limits.
*   **Mitigation:**
    *   Use smaller, faster models (`llama-3.1-8b-instant`) for frequent ticks.
    *   Reserve large models (`llama-3.3-70b-versatile`) for "Deep Deliberation" (rare events, flashbacks).
    *   Implement "Exponential Backoff" on `API Error 429`.

---

## 7. 🏗️ Architecture Diagram (V2)

```text
+-------------------------------------------------------------------+
|                     External LLM (Groq/Claude/Local)              |
|                     (Reasoning Engine)                     |
+-------------------------------------------------------------------+
                              ^  |  |  v
                              |  |  |  JSON Action
                        +---------+  |  |  +---------+
                        |         |  |  |  |
      +---------------+  |  +---------+  |  |  +---------------+
      |               |  |  |         |  |  |               |
      |  Agent Brain   |  |  |  Agent  |  |  |  Agent Brain   |
      |  (Client)      |  |  |  Brain   |  |  |  (Client)      |
      +---------------+  |  +---------+  |  |  +---------------+
               |        |  |        |  |        |  |
               v        |  v        |  v        |  v        |  |
      +-------------------------------------------------------------------+
      |              gRPC Server (Fate Engine)                     |
      |  (Python, asyncio, bidirectional streaming)              |
      +-------------------------------------------------------------------+
               ^        |  ^        |  ^        |  ^        |  |  ^
               |        |  |        |  |        |  |  |
      +---------+  |  +---------+  |  +---------+  |  +---------+
      |         |  |  |         |  |         |  |         |
      |  Spatial |  |  | Object  |  |  |  Actor  |  |  |  Object |
      |  Index   |  |  | Manager |  |  |  Store  |  |  |  Manager |
      +---------+  |  +---------+  |  +---------+  |  +---------+
               |        |  |        |  |        |  |  |
               v        |  v        |  v        |  v        |  v
      +-------------------------------------------------------------------+
      |                World State (The DB)                        |
      +-------------------------------------------------------------------+
```

---

## 8. 🔐 Security & Reliability

*   **Input Sanitization:** All `parameters` from LLM must be strings (handled in `AgentBrain`). Prevents Python injection attacks.
*   **State Persistence:** (V3) Periodic checkpointing of `WorldState` to database (PostgreSQL). Allows recovery from crashes.
*   **Rate Limiting:** Application-level queues. If LLM provider fails 429, queue the request and retry later (don't crash the agent).

---

## 9. 📊 Success Metrics (V2 Goals)

We define success by the following metrics:

1.  **Autonomy:** % of ticks where agents act *without* an explicit user command.
2.  **Coherence:** % of interactions that are logically consistent (e.g., Merchant doesn't try to eat a table).
3.  **Throughput:** Engine ticks per second (Target: >10 ticks/sec with 50 agents).
4.  **Stability:** Mean Time Between Failures (MTBF) > 1 hour.

---

## 10. 📝 Engineering Roadmap

### Phase 1: Foundation (Current)
*   [x] Fix Type Mismatch in `AgentBrain`.
*   [x] Switch to faster LLM model (`llama-3.1-8b`) to fix rate limits.
*   [x] Create `MarketplaceRoleplay` scenario (V1 Proof of Concept).

### Phase 2: World Dynamics (Next Sprint)
*   [ ] Implement `SpatialIndex` (Grid-based for simplicity first).
*   [ ] Implement `ProposalWindow` logic.
*   [ ] Add `WorldBuilder` API to server.

### Phase 3: Behavioral Depth (Mid Term)
*   [ ] Integrate `NeedsSystem` into `AgentBrain`.
*   [ ] Implement `GossipProtocol` for short-term memory.
*   [ ] Add `DramaDirector` for tension tracking.

### Phase 4: Productionization (Long Term)
*   [ ] Multi-Node Federation.
*   [ ] PostgreSQL persistence.
*   [ ] RAG (Vector DB) for long-term memory.
*   [ ] Web Dashboard (Visualizing simulation).

---

**End of Report.**
