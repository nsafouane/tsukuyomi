# 🧠 AI Assistant Operating Memory: Tsukuyomi MVP v0.1

**CRITICAL INSTRUCTION FOR ALL AI ASSISTANTS:**
If you are reading this file, you MUST immediately read `rules.md` in the root directory. `rules.md` contains the absolute coding standards, prohibited practices, and architectural philosophy for this project. Do not write a single line of code or plan any features before fully understanding `rules.md`.

---

## 🎯 Project Vision & Current Objective

**Vision:** Tsukuyomi is a complete AI infrastructure for games, storytelling, and agent simulations. It is a universal backend engine that natively drives world physics, environmental rules, and dynamic narrative flow (`FateEngine`, `DramaDirector`), creating living story-worlds where autonomous agents (powered by `BaseAgent`) interact naturally.

**Current Status:** 🏗️ **Phase 1: Architecture Unification (MVP v0.1)**
We are actively dismantling fragmented "V1/V2/V3" prototype code and consolidating "Simulation" and "Standalone" modes into a single, unified MVP v0.1 codebase.
*Immediate Priority: Stage 1 - The Purge (Removing dead code, unused dependencies, and dynamic duck-typing mixins).*

---

## 🗂️ Mandatory Directory Structure & Rules

You must strictly adhere to this folder structure. Misplacing files is a direct violation of project rules.

### 1. The Engine Source Code (`/tsukuyomi/`)
*   `core/`: The singular source of truth. Contains the unified `BaseAgent` and core interfaces (emotion, memory, belief). Engine physics and narrative control live here. **NO hardcoded testing/scenario logic is allowed here.**
*   `brain/`: Simulation/gRPC specific implementations (must inherit from `core/`).
*   `agent/`: Standalone/Async specific implementations (must inherit from `core/`).
*   `proto/`: gRPC definitions.

### 2. Developmental Artifacts (`/dev-artifacts/`)
*   **Purpose:** The ONLY place for developer/AI planning.
*   **Contents:** Specifications (`ARCHITECTURE_SPEC.md`), codebase analysis, reports, and the project `ROADMAP.md`.
*   **Rule:** Always read `ROADMAP.md` here to understand the current overarching goals and phases. Never place these files in the root or `docs/`.

### 3. Documentation (`/docs/`)
*   **Purpose:** Official, user-facing documentation.
*   **Contents:** Published user manuals, finalized component APIs, and architecture overviews. Drafts and specs do not belong here.

### 4. Testing (`/tests/`)
*   **Purpose:** The exclusive home for all test scripts and test fixtures.
*   **Rule:** Do not place tests in the root or alongside source code. Use this folder exclusively.

### 5. Experiments (`/experiments/`)
*   **Purpose:** ISOLATION for testing scenarios.
*   **Rule:** We use scenarios (e.g., "Angry Men", "Marketplace") *strictly* as isolated experiments to test our engine improvements. All specific entity names, dialogue, testing states, and hardcoded environment rules belong exclusively in these scripts. Never pollute the Engine (`core/`) with scenario-specific scripting.

---

## 📜 Key References for AI Coding

To ensure perfect alignment with the project trajectory, an AI assistant should always consult these files:

1.  **`rules.md`**: The absolute law of the codebase. Defines styling (snake_case, <700 lines), constraints (no duck-typing, no random IDs), and production readiness requirements.
2.  **`dev-artifacts/ROADMAP.md`**: The definitive phased approach to delivering the MVP v0.1 and beyond. Defines the current scope of work.
3.  **`dev-artifacts/ARCHITECTURE_SPEC.md`**: The blueprint for the current refactoring effort. Details exactly how the `BaseAgent` and core systems must be unified and what dead code must be purged.
4.  **`README.md`**: The public-facing summary of the engine's capabilities and architecture.

---

## 🚫 AI Assistant Anti-Patterns (DO NOT DO THIS)

*   **DO NOT** use terms like "V2", "V3", or "Phase 15". We only recognize the unified **MVP v0.1** and the phases defined in the current roadmap.
*   **DO NOT** create monolithic files over 700 lines. Refactor proactively.
*   **DO NOT** use `random.randint()` for IDs (use `uuid.uuid4()`).
*   **DO NOT** write "scripted" narrative logic inside the `tsukuyomi/core/` engine. True narrative is driven dynamically; scripted tests belong in `experiments/`.
*   **DO NOT** introduce heavy frameworks or databases (like `sqlalchemy` or `asyncpg`) without explicit architectural approval in `ROADMAP.md`.

---
*Last Updated: 2026-02-21 (Alignment with MVP v0.1 Architecture Spec)*
