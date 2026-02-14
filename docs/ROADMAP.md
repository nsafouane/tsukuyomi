# 🛣️ Tsukuyomi V2 - Development Roadmap

**Status:** V1 (Prototype) -> V2 (Real World Simulation)

## 🎯 Objective
Transform Tsukuyomi from a static narrative demo into an **autonomous multi-agent world simulation platform** where agents live, trade, fight, and persist in a dynamic environment.

---

## 🗺️ Current Status (V1)
*   **Core:** `FateEngine` (gRPC Server) + `AgentBrain` (LLM Client).
*   **Issue:** "Static Narrative Loop". Agents perceive nothing -> do nothing -> sleep.
*   **Scenario:** "Angry Men 5 Agents" (Empty Jury Room).

---

## 🚀 Phase 1: Foundations of Autonomy (Weeks 1-2)
**Goal:** Make agents self-sufficient. They should move and act without user prompts.

### 1.1 Needs System Implementation
*   [ ] Create `AgentNeeds` class (Hunger, Fatigue, Boredom, Social).
*   [ ] Integrate `Needs` into `AgentBrain` prompt template.
    *   *Logic:* High need overrides IDLE state.
*   [ ] Implement decay logic (needs increase over time).

### 1.2 World Builder API
*   [ ] Create `WorldBuilder` Python class.
*   [ ] Implement `add_object(id, type, position, properties)` method.
*   [ ] Update `FateEngine` to accept world initialization via gRPC.

### 1.3 Scenario: The Busy Marketplace (V1 Proof)
*   [ ] Script: `experiments/marketplace_roleplay.py` (Created).
*   [ ] Setup: Spawn 4 agents (Merchant, Guard, Peasant, Thief).
*   [ ] Goal: Agents wander, trade, and interact with stalls autonomously.
*   [ ] Test: Verify agents generate `MOVE` and `INTERACT` proposals without hardcoded triggers.

---

## 🤝 Phase 2: Interaction & Physics (Weeks 3-5)
**Goal:** Make the world feel "Real" and responsive.

### 2.1 Spatial Partitioning
*   [ ] Implement `SpatialHash` or `QuadTree` index.
*   [ ] Replace O(N) proximity checks with O(log N) queries.
*   [ ] Benefit: Support 50+ agents moving fluidly.

### 2.2 Affordance System
*   [ ] Define `Affordance` structure (Action, Condition, Effect).
*   [ ] Attach affordances to `EnvironmentObject`s.
    *   *Example:* Door has "OPEN" affordance if "key" in inventory.
*   [ ] Resolution: `FateEngine` checks affordances before resolving `INTERACT`.

### 2.3 Visual Perception (Raycasting)
*   [ ] Implement `VisionCone` for agents.
*   [ ] Generate "Visual Percepts": `PERCEPT:VISUAL:OBJ_TABLE(distance:2, occluded:false)`.
*   [ ] Benefit: Agents can hide behind walls or see only in front.

---

## 🌐 Phase 3: Persistence & Scale (Weeks 6-8)
**Goal:** Robust service capable of running for hours/days.

### 3.1 Database Persistence
*   [ ] Connect `FateEngine` to PostgreSQL (or SQLite for dev).
*   [ ] Save `WorldState` snapshot every 100 ticks.
*   [ ] Save `Actor` state (inventory, position) on change.
*   [ ] Load logic: `./run --resume-from-tick 5000`.

### 3.2 Proposal Windows (Combat/Speed)
*   [ ] Implement `ProposalWindow` class.
    *   *Logic:* Agents submit plans for future ticks.
    *   *Benefit:* Enables "Commitment Phase" (Counter-play).
*   [ ] Conflict resolution: Compare stamina/speed for simultaneous moves.

### 3.3 Federation (Multi-World)
*   [ ] Support for multiple `FateEngine` nodes (Town, Forest).
*   [ ] Agents travel between nodes via "Portals".
*   [ ] Event synchronization (Chat/Trade across worlds).

---

## 🧠 Phase 4: Advanced Intelligence (Weeks 9+)
**Goal:** Narrative depth and long-term memory.

### 4.1 Long-Term Memory (RAG)
*   [ ] Integrate Vector Database (Qdrant/Weaviate).
*   [ ] Store agent memories: "Merchant overcharged me".
*   [ ] Query memories: "memories.similar('merchant')" -> Bias decisions.
*   [ ] Update prompt: "Recall that Marcus is dishonest."

### 4.2 Drama Director
*   [ ] Implement `TensionTracker` (4-axis metric).
*   [ ] Event System: Inject environmental events (Thunder, Fire).
*   [ ] Plot Hooks: Ensure story progresses (Ending the conflict).

---

## ✅ Success Metrics

We will consider V2 successful when:
1.  [ ] 50 agents run simultaneously with < 200ms tick time.
2.  [ ] Agents survive 1 hour without user input (Autonomy > 95%).
3.  [ ] World state can be saved and restored (Persistence).
4.  [ ] Complex interactions (Trade > 5 steps) occur without logic errors.

---

**Last Updated:** 2026-02-14
