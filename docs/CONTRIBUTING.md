# 🤝 Contributing to Tsukuyomi V2

Welcome! We are building an autonomous, general-purpose multi-agent simulation engine. Please follow these guidelines to keep the codebase organized and scalable.

## 🎯 Design Philosophy

**"General Engine" over "Custom Scenarios"**

*   **Don't Hardcode:** Do not write specific scenario logic (e.g., "If agent is Davis, say X") directly into the `FateEngine` or `AgentBrain` files.
*   **Use Systems:** Implement *general systems* (Needs System, Spatial Index, Affordance System) that apply to *all* agents.
*   **Be Abstract:** A "Merchant" is just an agent with high `Social Need` and an inventory. A "Guard" is an agent with a `Patrol Goal`. Write the logic for the *role* into the agent profile or a subclass, not the core engine.

## 🏗️ Project Structure

*   `/tsukuyomi/core/` - Server logic (FateEngine, World, SpatialIndex).
*   `/tsukuyomi/brain/` - Client logic (AgentBrain, Perception, Memory).
*   `/tsukuyomi/proto/` - gRPC definitions (`.proto` files).
*   `/tsukuyomi/experiments/` - Scenario scripts (e.g., `marketplace.py`).
*   `/tsukuyomi/docs/` - Documentation (This directory).

## 📝 Contribution Workflow

1.  **Discuss:** Open a GitHub Issue or Discord discussion.
2.  **Branch:** Create a feature branch (e.g., `feat/spatial-index`).
3.  **Code:** Write code following Python standards (PEP8) and docstring conventions.
4.  **Test:** Write a test in `/tsukuyomi/tests/` (or a scenario script) validating the change.
5.  **PR:** Submit a Pull Request with description and linking to Issue.

## 🧠 Guidelines for Components

### Fate Engine (Server)
*   **Keep it Async:** Avoid blocking I/O in the main tick loop.
*   **State Authority:** All world state changes must happen via `Proposal` -> `Resolution`.
*   **Input Validation:** Trust nothing from `AgentBrain`. Sanitize parameters.

### Agent Brain (Client)
*   **Perception:** Filter and tag percepts. Don't dump the whole world state to the LLM every tick.
*   **Memory:** Implement short-term (Gossip) and long-term (RAG) storage strategies.
*   **Caching:** Cache system prompts (Role, Backstory) to save API calls/tokens.

### World Management
*   **Objects:** Define objects using the `WorldBuilder` API.
*   **Affordances:** Define what *can* happen, not just what *is*.
*   **Spatial:** Use the `SpatialIndex` for collision detection, not O(N) loops.

## 🚫 Prohibited Changes

*   **Do not modify** `experiments/angry_men_5_agents.py` to fix a general engine bug. Fix the engine in `/tsukuyomi/core/`.
*   **Do not add** "If actor ID == 'davis'" logic to `FateEngine`. Use roles and traits instead.
*   **Do not hardcode** specific scenarios into the core engine files. Scenarios belong in `/experiments/`.

## 📜 Code Style

*   Use `typing` hints (e.g., `def func(x: int) -> str`).
*   Use the `logging` module, not `print()` statements.
*   Error handling: Wrap gRPC calls in `try/except` blocks.
