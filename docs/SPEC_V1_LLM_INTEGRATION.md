# Tsukuyomi Technical Specification V1.0: Deep LLM Integration

**Status:** Proposed
**Phase:** 1 (Narrative & Memory Layer)

## 1. Executive Summary
This specification outlines the architectural changes required to integrate a Large Language Model (LLM) into the Tsukuyomi simulation engine. The goal is to enable agents to generate text, dialogue, and internal monologue that drives their actions, moving beyond rigid rule-based behaviors.

## 2. Context & Objectives
### 2.1. Problem Statement
Current agents in Tsukuyomi operate on simple reactive loops (Stimulus -> Response). While effective for basic simulations, this limits complex storytelling and "Free Will" (adaptable behavior).
- **Objective:** Empower agents with an "AI Consciousness" layer that interprets the world state and generates coherent narratives dynamically.

### 2.2. Scope of V1.0
- **Target Modules:**
    1.  **LLMService:** A production-ready service for managing external AI connections, prompt generation, and response streaming.
    2.  **Memory System Enhancement:** Augment `MemoryManager` to support long-term episodic memory and retrieval for LLM context.
    3.  **AgentBrain Update:** Modify `AgentBrain` to accept external directives (narrative goals) from the LLM service.

## 3. System Architecture (Proposed)

### 3.1. Agent Brain Pipeline
The existing `AgentBrain` runs on a fixed tick cycle:
1.  **Perception:** Process raw `WorldState` -> Filtered Events.
2.  **Decision (Internal):** Check personality, goals, memories -> Select Action.
3.  **Action:** Submit `Proposal` to `FateEngine`.

**V1.0 Modification:**
- **Insert External Directive:**
    - Before Step 2 (Decision), check for active directives from `LLMService`.
    - If directive exists (e.g., "Talk to Character X"), inject prompt parameters or override selection.
- **Stream LLM Generation:**
    - Instead of a local rule-based response (e.g., `if mood == ANGER: shout`), send request to `LLMService`.
    - Receive generated text/dialogue and process it into an `EMOTE` (Emotional State/Action) proposal.

### 3.2. LLM Service Interface
```protobuf
service LLMService {
    rpc GenerateResponse (LLMRequest) returns (stream LLMResponse);
    rpc GetContext (ContextRequest) returns (ContextResponse);
}
```

**Responsibilities:**
- Maintain connection to external LLM provider (API key configurable).
- Manage prompt templates for different scenario types (social, combat, storytelling).
- Handle streaming responses efficiently.

### 3.3. Memory System Integration
The current `MemoryManager` maintains a list of `active_episodes` (short-term).
- **V1.0 Requirement:** Add `long_term_memory` attribute to `AgentState`.
- **Mechanism:**
    - When `AgentBrain` receives a directive (e.g., "Remember the password"), it stores the raw string in `long_term_memory`.
    - When generating a response for the agent, include relevant entries from `long_term_memory` in the LLM prompt.

### 3.4. Fate Engine Modifications
No major structural changes required. The existing `FateEngine` already accepts proposals of type `EMOTE` via `gRPC`, so no new action types are needed.

## 4. Success Criteria
V1.0 is considered successful when:
1.  **Directives Executed:** Agents follow narrative commands from LLM Service (e.g., "Go to the tavern" results in agent movement).
2.  **Narrative Coherence:** Agent dialogue aligns with current world state (they don't talk about things that don't exist).
3.  **Dynamic Behavior:** Agents exhibit personality shifts or unique behaviors based on LLM interactions.

## 5. Implementation Plan

### 5.1. Phase 1: Service Foundation
- **Task:** Implement `LLMService` as a wrapper around OpenAI/Anthropic/Claude SDK.
- **Protocol:** Expose `GenerateResponse` via gRPC to agents.
- **Mocking:** Initially, use mock responses for testing `test_llm_integration.py`.

### 5.2. Phase 2: Memory Augmentation
- **Task:** Extend `StateManager` and `MemoryManager`.
- **Action:** Implement `MemoryManager.store_event(text, tags)` method.
- **Retrieval:** Implement `MemoryManager.retrieve_events(tags)` method.

### 5.3. Phase 3: Agent Brain Loop
- **Task:** Update `AgentBrain` logic.
- **Action:**
    ```python
    # Check for LLM directive
    if self.llm_directive:
        response = await self.llm_service.generate_response(prompt=self.llm_directive)
        # Create EMOTE proposal
        self.submit_proposal("EMOTE", {"text": response})
    ```

### 5.4. Phase 4: Testing & Validation
- **Task:** Create `tests/test_llm_integration.py`.
- **Scenario:** A simple scenario where an agent must use an LLM to decide an action based on a complex social cue.
- **Validation:** Ensure `AgentBrain` correctly prioritizes LLM directives over internal reflexes.

## 6. Dependencies
- `openai` (or preferred provider SDK)
- `python-dotenv` (for API key management)

## 7. Risks & Mitigations
- **Risk:** LLM latency introduces lag to the simulation loop. The 20ms tick rate might become 50ms.
- **Mitigation:** Implement asynchronous LLM calls so they don't block the tick loop. Use `asyncio` in `AgentBrain`.
- **Fallback:** If LLM service fails, revert to internal behavior (default to "IDLE").

## 8. Deliverables
- [ ] `tsukuyomi/llm/` module (New package).
- [ ] `tsukuyomi/tests/test_llm_integration.py`.
- [ ] Updated `tsukuyomi/README.md` referencing LLM capabilities.
- [ ] This specification document.

---
*Version:* 1.0*
*Last Updated:* Feb 10, 2026*
