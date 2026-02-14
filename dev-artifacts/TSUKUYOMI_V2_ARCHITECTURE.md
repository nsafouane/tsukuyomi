# 🏗️ Tsukuyomi V2 - Technical Specification

**Version:** 2.0 (Real World Simulation)
**Status:** Proposed Architecture

## 1. 🎯 Executive Summary

The Tsukuyomi Engine transforms from a static narrative demo to an autonomous, state-driven simulation platform. Agents possess "bodies" (Avatars), "drives" (Internal Needs), and "memory" (RAG), and they live within a dynamic world governed by physics and interaction rules.

**Core Philosophy:**
*   **General Purpose:** The engine must be a generic platform (Server), while scenarios provide specific context (Agents).
*   **State-Driven:** Agents act because their internal state (Hunger, Fatigue) changes, not just because they are asked to.
*   **World-Based:** The environment is the primary driver. Agents react to objects and events, not just each other.

---

## 2. 🦾 Component 1: Fate Engine (The Core)

**Role:** The authoritative simulation loop and state manager.

### 2.1 V2 Architecture Requirements

#### A. Spatial Indexing (Partitioning)
**Problem:** Current O(N) collision checks do not scale.
**Solution:** Implement `SpatialHash` (Grid-based for simplicity) or `QuadTree`.
*   **Implementation:**
    ```python
    class SpatialIndex:
        def __init__(self, width, height):
            self.width = width
            self.height = height
            self.grid = {} # (x, y) -> List[ObjectID]

        def insert(self, obj_id, x, y):
            gx, gy = int(x), int(y)
            self.grid.setdefault((gx, gy), []).append(obj_id)

        def query(self, x, y, radius):
            # Check surrounding grid cells
            results = []
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    results.extend(self.grid.get((x + dx, y + dy), []))
            return results
    ```

#### B. Proposal Windows (Commitment Phase)
**Problem:** Instant actions make complex counter-play impossible.
**Solution:** Introduce `ProposalWindow` logic.
*   **Mechanism:**
    1.  Engine opens window (e.g., Ticks 100-105).
    2.  Agents submit proposals.
    3.  Engine closes window.
    4.  Engine resolves proposals (e.g., based on timestamp, speed).
    5.  Engine broadcasts `Resolution`.
*   **Benefit:** Enables "Fast-Paced Combat" and "Simultaneous Interaction".

#### C. Conflict Resolution
**Problem:** "Last write wins" is naive.
**Solution:** `ConflictResolver` module.
*   **Logic:**
    *   `ActionPriority`: EMOTE (social) > INTERACT (physical) > MOVE.
    *   `Stamina`: Agent with higher stamina wins physical conflicts.
    *   `Randomness`: Small chance factor to prevent stalemates.
*   **Benefit:** Enables emergent behavior (Theft, wrestling, blocking).

### 2.2 gRPC Protocol Specification

**File:** `tsukuyomi/proto/core.proto`

**Key Messages:**
*   **`Actor`**: `{id, name, position (Vector2), state, inventory, interactions}`
*   **`Proposal`**: `{proposal_id, actor_id, action (enum), parameters (map<string, string>)}`
*   **`Resolution`**: `{proposal_id, success, outcome (details), modified_action}`
*   **`EnvironmentObject`**: `{id, type, position, properties (map), affordances (list)}`

---

## 3. 🧠 Component 2: Agent Brain (The Intelligence)

**Role:** Client-side controller. Acts as the "Cortex".

### 3.1 Perception Pipeline

*   **`ProximityHeartbeat`**: Low-freq check (e.g., every 5 ticks). "Is Actor B near me?"
*   **`DeepPerception`**: High-freq scan (e.g., every 10 ticks). "What are the distinct objects in the room?"
*   **`VisualPerception` (Future)**: Raycasting/FOV. "Can I see the thief behind the pillar?"

**V2 Change:** Add **Tagging**.
*   *Old:* Logs raw list: `[actor_1, actor_2, obj_1]`
*   *New:* Logs tagged percepts: `[PERCEPT:PROXIMITY:PLAYER_NEAR(actor_1), PERCEPT:VISUAL:PROP(table)]`
*   *Benefit:* LLM can filter relevant info faster.

### 3.2 The "Static Loop" Fix (Drive System)

**Problem:** Agents do nothing in an empty room because "Do nothing" is the safest option.
**Solution:** **Needs System** (Internal Motivational Model).
*   **Implementation:**
    ```python
    class NeedsSystem:
        def __init__(self):
            self.hunger = 0.0
            self.fatigue = 0.0
            self.boredom = 0.0 # Increases over time

        def update(self, dt):
            self.hunger += dt * 0.1
            self.fatigue += dt * 0.05
            if self.hunger > 0.8: return "EAT"
            if self.boredom > 0.9: return "EXPLORE"
    ```
*   **Integration:** The `AgentBrain` passes these scores to the LLM in the system prompt: *"Your hunger is 80%. You see an apple stall. What do you do?"*
*   **Benefit:** Agents become autonomous actors seeking goals, not just passive chatbots.

### 3.3 Memory Architecture

*   **Short-Term:** `GossipProtocol` (Key-Value store). "Did you see X?" (Valid for 1-2 ticks).
*   **Long-Term:** (Future V3) `RAG (Retrieval-Augmented Generation)`.
    *   *Mechanism:* Vector Database (e.g., Qdrant).
    *   *Store Memories:* "The merchant overcharged me."
    *   *Query:* `memories.similar("merchant")` -> Influence LLM decisions.

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

**Role:** Ensures story moves forward. Prevents "sandbox death" (agents idling forever).

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

*   **Prompt Caching:** System prompts ("You are a juror...") are static. Cache the fully rendered string. Do not re-render percepts into natural language every tick if not necessary.
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
                  | Agent Brain |  |  | Agent Brain |
                  | (Client)   |  |  |  (Client)   |
                  +---------------+  |  +---------+  |
               |        |  |  |         |
               v        |  v        |  v        |  v
      +-------------------------------------------------------------------+
      |              gRPC Server (Fate Engine)                     |
      |  (Python, asyncio, bidirectional streaming)              |
      +-------------------------------------------------------------------+
               ^        |  ^        |  ^        |  ^
               |        |  |        |  |        |
      +---------+  |  +---------+  |  +---------+
      |         |  |  |         |  |         |
      | Spatial |  |  | Object  |  |  Actor  |  |  Object |
      |  Index   |  |  Manager |  |  Store   |  |  Manager |
      +---------+  |  +---------+  |  +---------+
               |        |  |        |  |        |  |
               v        |  v        |  v        |  v        |  v
      +-------------------------------------------------------------------+
      |                World State (The DB)                        |
      +-------------------------------------------------------------------+
```

---

## 8. 🔐 Security & Reliability

*   **Input Sanitization:** All `parameters` from LLM must be strings (handled in `AgentBrain`). Prevents Python injection attacks.
*   **State Persistence:** (V3) Periodic checkpointing of `WorldState` to a database (PostgreSQL). Allows recovery from crashes.
*   **Rate Limiting:** Application-level queues. If LLM provider fails 429, queue the request and retry later (don't crash the agent).

---

## 9. 📊 Success Metrics (V2 Goals)

We define success by the following metrics:

1.  **Autonomy:** % of ticks where agents act *without* an explicit user command.
2.  **Coherence:** % of interactions that are logically consistent (e.g., Merchant doesn't try to eat a table).
3.  **Throughput:** Engine ticks per second (Target: >10 ticks/sec with 50 agents).
4.  **Stability:** Mean Time Between Failures (MTBF) > 1 hour.

---

**End of Specification**
