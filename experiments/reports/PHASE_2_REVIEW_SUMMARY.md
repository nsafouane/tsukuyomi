# Tsukuyomi Phase 2 Review Report: The Cognitive Core

**Reviewer:** Senior Simulation Engineer & AI Architect (Gemini 2.5 Pro subagent)
**Subject:** Rigorous Analysis of Technical Specification v1.0
**Status:** APPROVED (with critical performance refinements)

## 1. Architectural Verdict
The proposed Phase 2 architecture is a sophisticated leap forward. The **Belief Graph** and **Stance Shifting** mechanisms are state-of-the-art for LLM-driven agents, moving from scripted performance to true emergent agency.

## 2. Critical Performance Risks & Mitigations
The primary concern is maintaining the **20 TPS (50ms/tick)** target given the new per-agent processing.

### Risk A: Perception Pipeline (O(A * (A+O)))
- **Observation:** Running geometric occlusion checks and saliency scoring for all agents every tick will bottleneck the engine.
- **Refinement:** **Staggered Perception Schedule.** We will not calculate full vision for every agent on every tick. Agents will rotate through "Deep Perception" ticks while performing lightweight "Proximity Heartbeats" on others.

### Risk B: Memory Decay (O(M))
- **Observation:** Linear decay of thousands of episodic memories per agent per tick is unsustainable.
- **Refinement:** Decouple decay from the main loop. Run memory pruning asynchronously or in batches (e.g., process 10% of memories per tick).

## 3. Logic & Handshake "Gotchas"
### Conflicting Actions
- **Issue:** The spec lacked detail on simultaneous actions (e.g., two agents trying to `TAKE` the same object).
- **Refinement:** Fate Engine will implement a **Deterministic Priority Queue** (first-come, first-served within a tick) and return specific failure reasons (e.g., `Object ownership changed`).

### The 'USE' Action
- **Issue:** `USE` is currently a black box.
- **Refinement:** Extend the `Affordance` schema to include `valid_targets_by_type` and `effect_script_ids` to map actions to specific Fate Engine logic handlers.

## 4. Feature Improvements
- **Emotional Inertia:** Emotional shifts will be scaled by **Arousal**. Calm agents will be more stable; agitated agents will be more volatile.
- **Surprise Factor:** Saliency will be boosted for events that violate the agent's **Memory Echo** (e.g., seeing a door open that was previously closed).

## 5. Next Steps: Implementation
We are proceeding to the **Coding Phase**. 
- **Lead Coder:** GLM 4.7 (via OpenCode)
- **Primary Task:** Implement the `PerceptionLayer` and `StateManager` with the performance refinements outlined above.
