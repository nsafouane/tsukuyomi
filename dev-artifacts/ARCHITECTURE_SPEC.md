# Tsukuyomi Architecture Remediation Specification

> **Status:** DRAFT
> **Objective:** Transform the Tsukuyomi Engine into a cohesive, professional, production-ready open-source simulation system by eliminating duplicated logic, establishing a single source of truth, and strictly enforcing engineering standards.

---

## Phase 1: Core System Consolidation

The current architecture is dangerously split into two independent runtimes (`brain/` vs. `agent/`). Phase 1 focuses on merging these parallel tracks into a unified, singular core engine.

### 1.1 Unified Agent Abstraction (`BaseAgent`)
To support both Tick-based Simulation Mode (gRPC) and Standalone Async Mode, all agent entities must derive from a single abstraction.

*   **Implementation:** Create `core/agent_base.py` defining an abstract `BaseAgent` class.
*   **Requirements:**
    *   Must define a standard interface for basic actions: `perceive()`, `deliberate()`, `act()`.
    *   `UniversalAgent` (from `agent/`) and `AgentBrain` (from `brain/`) must both inherit from `BaseAgent`.
    *   All core subsystems (Memory, Emotion, Beliefs) must be instantiated as composition properties on `BaseAgent`, ensuring both modes share the exact same underlying mechanics.

### 1.2 Singular Emotional Core
We currently have two emotional state implementations (`StateManager`, `EmotionalState`). This will be reduced to **one**.

*   **Implementation:** Consolidate around a standard `BaseEmotionalEngine` interface mapping Pleasure-Arousal-Dominance (PAD).
*   **Requirements:**
    *   Create a single source of truth in `core/emotion/`.
    *   Extract the useful features of `agent/emotional_state.py` (contagion) and `brain/StateManager.py` (inertia and regression-to-baseline).
    *   Remove all other implementations. `AgentBrain` and `UniversalAgent` must both use this exact standard component to evaluate internal affect.

### 1.3 Singular Memory System
Four competing memory models currently exist, fragmenting context retrieval. Furthermore, the `MemoryType` enum is duplicated in three separate locations with conflicting definitions. We will standardize on a tiered memory architecture.

*   **Implementation:** Adopt the `MemoryType` enumerations from `brain/rag_memory.py` as the canonical truth.
*   **Requirements:**
    *   Combine episodic timeline generation (`MemoryManager`) with vector-based retrieval (`RAGMemorySystem`).
    *   The unified system will categorize memories securely into `[EPISODIC, SEMANTIC, PROCEDURAL, WORKING]`.
    *   Deprecate `agent/memory_system.py` (`LongTermMemory`) entirely. Any keyword-based retrieval logic must be either absorbed into the RAG filter stack or discarded.

### 1.4 Singular Belief System
The simplistic `BeliefManager` and overly complex `BeliefSystem` must be unified into a scalable, interface-driven component.

*   **Implementation:** Extract a `BaseBeliefTracker` interface in `core/belief/`.
*   **Requirements:**
    *   Migrate the stable, full-lifecycle logic from `agent/belief_system.py` (confidence decay, contradiction detection) into the unified engine.
    *   Refactor the implementation to ensure it formats effectively for LLM prompt context injection (a strength of the older `BeliefManager`).
    *   Delete the legacy `BeliefManager` class entirely.

---

## Phase 2: Unused Code & Deprecation Roadmap

Tsukuyomi carries significant dead code, experimental unintegrated versions, and orphaned dependencies. Phase 2 defines the precise roadmap for their eviction to drastically reduce the codebase footprint.

### 2.1 Dependency Pruning
The project's dependency surface is artificially bloated without matching usage in the source code.
*   **Action:** Completely remove `asyncpg` and `sqlalchemy` (database dependencies unsupported by the current architecture).
*   **Action:** Remove `pydantic` (zero imports detected across the entire codebase despite its presence in requirements).
*   **Action:** Audit `qdrant-client` and `sentence-transformers`; if the `RAGMemorySystem` maintains `in_memory=True` exclusively, remove these heavy dependencies in favor of lightweight native alternatives.

### 2.2 Unification of Experimental Architecture Layers
The `agent/v3_integration.py` layer and other experimental "upgrades" across the codebase introduce brittle duck-typing and unused mixins, attempting to patch components onto objects dynamically at runtime.
*   **Action:** Delete `V3AgentMixin`, `enhance_agent()`, and `enhance_prompt()` functions entirely, along with any other version-specific wrappers.
*   **Requirement:** We will eliminate all concepts of "V1, V2, V3" from the codebase vocabulary. All valid logic will be consolidated into the unified **MVP v0.1**. Agent components (emotion, memory, beliefs) MUST be statically defined on the `BaseAgent` class through composition (as defined in Phase 1). Dynamic attachment at runtime is explicitly banned to maintain type safety and debuggability.

### 2.3 Resolving Orphaned Core Modules
Several unintegrated modules exist scattered under `brain/` (`brain/memory/`, `brain/reasoning/`, `brain/personality/`, `brain/conversation/`). These were intended as upgrades but were never fully implemented into the event loop.
*   **Action (Delete):** Remove `brain/conversation/`. It is completely isolated with zero external imports.
*   **Action (Integrate into v0.1):** The `brain/reasoning/` directory provides valuable algorithmic transparency. This logic must be officially wired into the new `BaseAgent` deliberation cycle for the MVP release.
*   **Action (Evaluate & Prune):** `brain/memory/` and `brain/personality/` must be evaluated against the consolidated memory/emotion interfaces specified in Phase 1. If their logic is fully redundant to the core implementations, they will be archived/deleted. We will not maintain parallel "newer" implementations.

---

## Phase 3: Engineering Standards & Quality Enforcements

To accept outside contributions as an open-source project, the MVP v0.1 codebase must establish and strictly enforce rigorous professional standards.

### 3.1 Strict Size Constraints
Massive monolithic files make navigation impossible and violate separation of concerns.
*   **Action:** Refactor all files currently exceeding 700 lines. 
*   **Key Targets:** `agent/belief_system.py` (~1500L), `brain/PerceptionPipeline.py` (~1300L), `proto/fate_engine.py` (~1100L).
*   **Requirement:** Logic must be extracted into focused sub-modules (e.g., separating impact rules from state management, or strategy algorithms from the core decision engine).

### 3.2 Naming and Formatting Conventions
The split architecture resulted in competing naming conventions across directories.
*   **Action:** Standardize entirely on Python `snake_case` for all filenames (e.g., `agent_brain.py` instead of `AgentBrain.py`).
*   **Action:** Standardize class naming to strict `PascalCase` with consistent suffixing (e.g., avoiding prefixes like `RAG...` when generic interfaces are established).

### 3.3 Stable ID Generation
The current codebase mixes random integer generation and UUIDs, creating unacceptable state collision risks.
*   **Action:** Audit all entity creation and replace `random.randint(...)` implementations globally with standard `uuid.uuid4()`.

### 3.4 Formal Agent Lifecycle Management
The current simulation relies on a bare `while True` loop with no shutdown capability, which is unacceptable for a production engine running network services.
*   **Action:** Define strict `start()`, `pause()`, `resume()`, and `cleanup()` interfaces on the `BaseAgent` and the engine `GrpcServer`.
*   **Requirement:** The engine must be able to gracefully degrade if agents fail to respond, circuit break on LLM timeouts, and cleanly close network channels on shutdown to prevent memory leaks.

---

## Phase 4: Execution Workflow

To ensure stability during this massive refactor, execution will proceed in strict, isolated stages from lowest risk to highest risk. No stage may begin until the previous stage passes all tests and is committed.

### Stage 1: The Purge (Lowest Risk)
- **Objective:** Radically reduce the codebase surface area.
- **Tasks:**
  1. Delete `agent/v3_integration.py` and all references to mixins.
  2. Delete `brain/conversation/`.
  3. Remove `asyncpg`, `sqlalchemy`, and `pydantic` from `requirements.txt`.
  4. Run the test suite to verify no live code was depending on these dead paths.

### Stage 2: Foundation & Interfaces (Medium Risk)
- **Objective:** Establish the new `core/` interfaces without breaking existing logic yet.
- **Tasks:**
  1. Create `core/agent_base.py` (`BaseAgent`).
  2. Create standard interfaces in `core/emotion/`, `core/memory/`, and `core/belief/`.
  3. Rename core files to `snake_case` (e.g., `agent_brain.py`, `state_manager.py`).
  4. Apply global UUID generation fixes.

### Stage 3: The Great Unification (High Risk)
- **Objective:** Migrate existing classes to the new interfaces and delete the duplicates.
- **Tasks:**
  1. Modify `AgentBrain` and `UniversalAgent` to inherit from `BaseAgent`.
  2. Consolidate `StateManager` and `EmotionalState` into the new `core/emotion/` implementation. Delete the losers.
  3. Consolidate `BeliefManager` and `BeliefSystem` into the new `core/belief/` implementation. Delete the losers.
  4. Unify the memory enums and tie the new structure to `BaseAgent`.

### Stage 4: Module Splitting & Lifecycle (Highest Risk)
- **Objective:** Break down monolithic files and enforce the engine lifecycle.
- **Tasks:**
  1. Extract logic from the 700+ line behemoths (`belief_system` equivalent, `perception_pipeline`, `fate_engine`).
  2. Implement `start()`, `pause()`, `stop()` on `AgentBrain` and the `GrpcServer`.
  3. Conduct full integration testing of a scenario run to ensure the MVP v0.1 engine is stable, deterministic, and free of memory leaks.

---

> **Final Review:** This specification serves as the absolute blueprint for Tsukuyomi's MVP v0.1 architecture. All pull requests must align with these mandates. No new features may be merged until Stage 4 is complete.
