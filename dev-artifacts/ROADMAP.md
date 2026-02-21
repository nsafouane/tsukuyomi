# 🛣️ Tsukuyomi MVP v0.1 - Development Roadmap

**Status:** Architecture Unification Phase -> MVP v0.1 (Complete AI Infrastructure)

## 🎯 Final Objective
Transform Tsukuyomi into a **complete AI infrastructure for games, storytelling, and agent simulations**. 

The final system will serve as a universal backend for any environment, capable of adapting to custom physics, world rules, and objects. The engine natively drives the world and the narrative flow via the `FateEngine` and `DramaDirector`, producing complete, living story-worlds where agents interact naturally. 

*Note: While current development uses isolated testing scenarios (e.g., Angry Men, Marketplace) to test agent logic, the ultimate engine will autonomously oversee complete, unscripted narrative environments.*

---

## 🏗️ Phase 1: Architecture Unification (Current Focus)
**Goal:** Consolidate fragmented "Simulation" and "Standalone" modes into a single, unified MVP v0.1 codebase.

### 1.1 The Purge & Foundation
*   [ ] Delete all `v3_integration` wrappers, mixins, and duck-typing logic.
*   [ ] Remove unused databases (`asyncpg`, `sqlalchemy`) from dependencies.
*   [ ] Establish `core/agent_base.py` (`BaseAgent`) as the single abstraction.
*   [ ] Define strict interfaces for `core/emotion/`, `core/memory/`, and `core/belief/`.

### 1.2 Component Consolidation
*   [ ] Unify `StateManager` and `EmotionalState` into a single PAD emotional system.
*   [ ] Unify `BeliefManager` and `BeliefSystem` into a single, LLM-friendly tracker.
*   [ ] Unify the 4 conflicting Memory Models and Enum definitions into `core/memory/`.
*   [ ] Ensure both `AgentBrain` (gRPC) and `UniversalAgent` inherit from `BaseAgent` and use these shared components.

### 1.3 Engineering Standards Enforcement
*   [ ] Refactor monolithic files (>700 lines) into focused sub-modules.
*   [ ] Implement formal `start()`, `pause()`, and `cleanup()` lifecycle methods.
*   [ ] Enforce stable UUID generation globally (replace random integers).

---

## 🤝 Phase 2: Autonomous Intelligence & Interaction
**Goal:** Agents correctly utilize their unified brains to exist and react in the world.

### 2.1 Needs & Urges
*   [ ] Implement generic `NeedsSystem` (Hunger, Fatigue, Social) tied to `BaseAgent`.
*   [ ] Ensure urgent needs dynamically override idle Deliberation.

### 2.2 Spatial & Affordance Physics
*   [ ] Implement `SpatialHash` or `QuadTree` for O(log N) proximity indexing.
*   [ ] Validate interactions via generic `Affordance` rules (Action, Condition, Effect).
*   [ ] Implement visual raycasting so agents only perceive what they can legitimately see.

---

## 🎭 Phase 3: The Narrative Engine
**Goal:** The Engine takes control of the story, shaping the agent simulation into a narrative experience.

### 3.1 Fate Control & Event Injection
*   [ ] Establish the `FateEngine` as the ultimate arbiter of physical truth.
*   [ ] Handle simultaneous proposal conflicts (e.g., two agents grabbing the same item).

### 3.2 Drama Director
*   [ ] Implement `TensionTracker` to monitor narrative pacing.
*   [ ] Dynamically inject environmental events or world state changes to drive story.
*   [ ] Ensure the engine can shape the narrative without relying on hardcoded character scripts.

---

## 🌐 Phase 4: Persistence & Scale
**Goal:** Robust, long-running service for real-world application backends.

### 4.1 State Persistence
*   [ ] Save `WorldState` snapshot intervals.
*   [ ] Ability to resume engine state natively (`--resume-from-tick`).

### 4.2 Production Scalability
*   [ ] Scale to support 50+ concurrent agents with < 200ms tick time.
*   [ ] Implement LLM circuit-breakers and graceful degradation for failed agent requests.

---

**Last Updated:** 2026-02-21 (Architecture Consolidation)
