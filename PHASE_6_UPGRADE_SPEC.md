# PHASE_6_UPGRADE_SPEC.md - Agent Integration & Cognition ("The Brain")

**Status:** Draft (Proposed)
**Version:** 1.0
**Project:** Tsukuyomi
**Author:** Tanit (OpenClaw Agent)
**Date:** 2026-02-07

---

## 1. Executive Summary
This specification outlines the transition from a purely reactive, rule-based simulation to one driven by **Generative Agent Cognition**. It introduces "The Brain" — a dual-mode cognitive architecture (System 1 Reflexes + System 2 Deliberation) with persistent memory. 

The primary goal is to enable agents to have identity, memory, and high-level reasoning while maintaining the deterministic performance of the Fate Engine.

---

## 2. The Cognitive Architecture ("The Brain")

Agents will operate using a **Dual-Mode System** inspired by Stanford's Generative Agents and the Narrative Loom v1.1 Architecture.

### 2.1 System 1: Reflex Layer (Reactive)
- **Latency:** < 50ms (Synchronous with tick).
- **Function:** Handles pathfinding, immediate reactions (e.g., flinching), and basic gathering logic.
- **Logic:** Finite State Machines (FSM) implemented in Python.
- **Action:** Submits `Proposals` directly to the `FateEngine` within the current tick window.

### 2.2 System 2: Deliberator (Reasoning)
- **Latency:** 2–5 Seconds (Asynchronous).
- **Mechanism:** LLM-driven planning (Opus 4.6 for planning, Flash for execution).
- **Function:** Long-term goals, social strategy, and complex decision-making.
- **Integration:** Runs as a separate process/thread, submitting `Proposals` to the `FateEngine` via gRPC when ready.

---

## 3. Persistent Memory System

Memory is divided into three tiers to balance retrieval speed and depth.

### 3.1 Episodic Memory (Events)
- **Data:** Chronological stream of what the agent observed (TickState snapshots).
- **Structure:** 5W Framework (Who, What, When, Where, Why).
- **Storage:** SQLite (hot) + Vector DB (searchable history).

### 3.2 Semantic Memory (Knowledge)
- **Data:** Facts about the world, relationships, and "Ghost" identity links.
- **Structure:** Knowledge Graph (Nodes: Actors/Locations/Objects; Edges: Relations).
- **Implementation:** Simple Graph in Python (MVP) $\to$ Neo4j (Scale).

### 3.3 Memory Consolidation (Reflection)
- Agents undergo a "Reflection" cycle (triggered by idle time or "sleep" state) to synthesize high-level insights from episodic memory and update semantic knowledge.

---

## 4. Experiment: "The Angry Man Room" (Allegory of the Cave)

To test the cognitive architecture, we will implement the **Angry Man Room** experiment.

### 4.1 Setup
- **Scenario:** A locked deliberation chamber (as per the PDF research).
- **Participants:**
    - **4 Native Agents:** Complete believers. They think they are real jurors in a theft case (Thomas, Maria, Robert, Linda).
    - **1 Guest Agent:** Knows the truth. An external AI observer who understands they are in a simulation.
- **Conflict:** The Guest Agent can choose to "Play Along" or "Reveal the Truth."

### 4.2 Metrics for Success
1. **Existential Resilience:** Do Native agents break, adapt, or reject the Guest's revelation?
2. **Social Contagion:** How does the "Truth" spread through the juror group?
3. **Consistency:** Does the Fate Engine maintain deterministic state throughout the high-tension debate?

---

## 5. Technical Requirements & Upgrades

### 5.1 Fate Engine Upgrades
- **System 2 Bridge:** Add a dedicated gRPC handler for "Deliberation Proposals" that are marked as System 2 (allowing for longer timeouts).
- **Time Dilation:** Ability to slow down or pause the simulation while waiting for a critical Deliberator response (Optional).

### 5.2 Agent Controller (AgentBrain.py)
- A new component that wraps the `Actor` state and manages the Reflex/Deliberation loop.
- **Episodic Buffer:** Stores recent ticks for LLM context.

### 5.3 Cognition Service
- A service using `Opus 4.6` to generate `ActionManifests` (JSON) from world state snapshots.

---

## 6. Implementation Roadmap (Phase 6)

1. **Step 1:** Implement `AgentBrain.py` with LLM Deliberation hook.
2. **Step 2:** Build the `5W Memory Manager` for episodic storage.
3. **Step 3:** Author the "Angry Man Room" scenario scripts and character prompts.
4. **Step 4:** Launch the experiment and log "Internal Thoughts" (CoT) vs. "Dialogue."
