# 📜 Tsukuyomi V2 - Project Rules & Standards

**Purpose:** Define the engineering philosophy and coding standards for the Tsukuyomi Engine V2.

## 1. 🎯 Design Philosophy: "General Engine"

### 1.1 Core Principle
The **Fate Engine** and **Agent Brain** are generic platforms. **Scenarios** (e.g., "Angry Men", "Marketplace") are **applications** running on this platform.

*   **Engine Code:** Must contain NO specific narrative logic (e.g., "If actor is Davis, he says..."). Engine only handles physics, state, and generic affordances.
*   **Agent Logic:** Is generic ("I am hungry" -> "Find Food"). Specific behaviors (e.g., "If I am a Guard, patrol") must be encoded in the **Agent's Profile** (Traits, Backstory), or handled via a **Role Subclass**, not hardcoded in the engine.

### 1.2 Allowed Customizations
*   **Profiles:** You can define agent `Personality`, `Traits`, and `Role` in the scenario setup.
*   **World Setup:** You can use `WorldBuilder` to spawn specific `EnvironmentObjects` (Stalls, Doors, Fountains) for a scenario.
*   **Prohibited:** Do NOT modify `/tsukuyomi/core/` to support a specific scenario. If a scenario needs "X", implement "X" in a generic way (e.g., a `MoveTo` action that accepts any target).

## 2. 🗂️ Coding Standards

### 2.1 File Structure
*   `/tsukuyomi/core/`: Server logic. `FateEngine`, `WorldBuilder`.
*   `/tsukuyomi/brain/`: Client logic. `AgentBrain`, `NeedsSystem`.
*   `/tsukuyomi/proto/`: gRPC definitions.
*   `/tsukuyomi/experiments/`: Scenario scripts.

### 2.2 Style Guide
*   **Python:** Version 3.10+.
*   **Indentation:** 4 spaces.
*   **Docstrings:** Use Google-style docstrings for all public functions/modules.
*   **Typing:** Use `typing` module for hints (e.g., `def func(x: int) -> str`).

### 2.3 Logging
*   Use the standard `logging` module.
*   Do NOT use `print()` for operational logs.

## 3. 🧠 Component Rules

### 3.1 Fate Engine (Server)
*   **State Authority:** The server is the ONLY place where `WorldState` (Actors, Objects) changes. Clients cannot modify state directly; they must submit `Proposal`s.
*   **Loop:** The main simulation tick must be non-blocking (`asyncio.sleep`).
*   **Validation:** All input from clients must be treated as untrusted and validated (sanitization).

### 3.2 Agent Brain (Client)
*   **Caching:** Do NOT regenerate the system prompt ("You are a juror...") on every tick. Cache it.
*   **Percepts:** Filter sensory data. Do not send the entire world state to the LLM every tick.
*   **Safety:** Wrap all gRPC calls in `try/except` blocks to handle network errors.

### 3.3 World Management
*   **Affordances:** All interactions must be validated against an object's `Affordance` list.
*   **Spatial:** Use a spatial index (Grid/Quadtree) for collision checks. Do not use O(N) loops.

## 4. 🚫 Contribution Workflow

1.  **Check Docs:** Read `/docs/ROADMAP.md` to see current priorities.
2.  **Issue:** Open an issue if you are starting a new major component (e.g., Spatial Indexing).
3.  **Branch:** Create a feature branch (e.g., `feat/spatial-index`).
4.  **PR:** Ensure your PR describes the "General System" impact, not just the specific scenario fix.

## 5. 🚫 Prohibited Practices

*   **Scripting:** Do not edit `experiments/angry_men_5_agents.py` to fix bugs that should be in the core engine. Fix the root cause in `/tsukuyomi/core/`.
*   **Hardcoding:** Do not write `if agent_name == "Davis":` in the engine core. Use roles, traits, or profile data.

---

**Last Updated:** 2026-02-14 (V2)
