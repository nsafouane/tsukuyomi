# 🤝 Code of Conduct

**Version:** 2.0 (Real World Simulation)

## 1. 🎯 Core Principles

*   **"General Engine" Philosophy:**
    *   We are building a platform, not a script.
    *   Code in `/tsukuyomi/core/` and `/tsukuyomi/brain/` must be generic and reusable by *any* scenario.
    *   Scenarios (`/tsukuyomi/experiments/`) provide specific context (Agent Profiles, World Setup) but rely on the engine's general systems (Needs, Affordances, Spatial Indexing).

*   **Autonomy First:**
    *   Agents must be self-sufficient. They should act because of their internal state (Hunger, Goals), not just because a human script tells them to.
    *   The engine should support agents living independently without external prompts for extended periods.

*   **State-Driven Architecture:**
    *   The world is the "Source of Truth". Agents do not "own" world state; they perceive it and interact with it via valid proposals.
    *   The `FateEngine` (Server) is the only authority on state changes.

---

## 2. 📁 File Organization

*   **`/tsukuyomi/core/`** - Server logic (FateEngine, WorldBuilder, SpatialIndex).
*   **`/tsukuyomi/brain/`** - Client logic (AgentBrain, NeedsSystem, PerceptionPipeline).
*   **`/tsukuyomi/proto/`** - gRPC definitions (.proto files).
*   **`/tsukuyomi/experiments/`** - Scenario scripts (e.g., marketplace.py).
*   **`/tsukuyomi/docs/`** - Documentation (Roadmap, Specs, Guides).
*   **`/tsukuyomi/tests/`** - Unit tests (to be implemented).
*   **`/tsukuyomi/dev-artifacts/`** - Analysis and temporary files (Not committed to git).

---

## 3. 🧠 Coding Standards

### 3.1 Style
*   **Python Version:** 3.10+
*   **Formatting:** 4 spaces indentation.
*   **Docstrings:** Use Google-style docstrings for all public modules, classes, and functions.
*   **Type Hinting:** Use `typing` hints (e.g., `def func(x: int) -> str`).

### 3.2 Logging
*   Use the `logging` module, not `print()` statements.
*   `logger.info()` for general events.
*   `logger.debug()` for detailed loop data (percepts, proposals).
*   `logger.error()` for failures.

### 3.3 Error Handling
*   **gRPC:** Wrap all gRPC calls (e.g., `client.submit_proposal`) in `try...except` blocks to handle connection failures or server restarts gracefully.
*   **LLM:** Handle `API Error 429` (Rate Limits) with exponential backoff. Do not crash the agent.

---

## 4. 🚫 Contribution Workflow

1.  **Discuss:** Open a GitHub Issue or start a Discord thread about the feature.
2.  **Branch:** Create a feature branch from `main` (e.g., `feat/spatial-indexing`).
3.  **Implement:** Write the code following the "General Engine" philosophy.
4.  **Test:** Write a scenario script or a unit test to validate the change.
5.  **PR:** Open a Pull Request. Ensure it passes CI (if available) and references the Issue.

---

## 5. 🛠️ Scenario Guidelines

*   **Do Not Modify Core for Scenarios:** If a scenario requires "If agent is X, say Y", implement this as a **Role Profile** or a **Trait** in the agent's config, or as a subclass of `AgentBrain`. Do not add `if agent.id == 'davis'` logic to the main `FateEngine` class.
*   **World Building:** Use the `WorldBuilder` API (to be implemented in Phase 1) to define objects, locations, and rules for your specific scenario.
*   **Validation:** Ensure your scenario runs for at least 100 ticks without agents entering a "Static Loop" (doing nothing).

---

**Adhere to these principles to ensure the Tsukuyomi V2 engine remains a robust, general-purpose simulation platform.**
