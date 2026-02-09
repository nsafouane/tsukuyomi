# Tsukuyomi Fixes & Optimization Specification
**Status:** DRAFT | **Reviewer:** Pony Alpha (Senior Tech Lead) | **Date:** Feb 9, 2026

## 1. Critical Bug Fixes (High Priority)

### 1.1 Codebase Consolidation (CRITICAL)
*   **Issue:** Two `proto` directories exist (`/root/tsukuyomi/proto` and `/root/tsukuyomi/tsukuyomi/proto`). They have significantly drifted. The root version contains legacy medieval data and lacks security fixes present in the package version.
*   **Fix:** DELETE the root `proto/` directory. Ensure all references in tests and scripts point to `tsukuyomi.proto`.
*   **Correction to Previous Spec:** The previous spec pointed to `tsukuyomi/proto/fate_engine.py`, which actually *contains* the fix already. The real issue is the presence of the legacy root folder.

### 1.2 Fate Engine: EXAMINE Resolver Refinement
*   **Issue:** While the fix exists in `tsukuyomi/proto`, the `revealed_properties` logic is still a shallow copy of `hidden_properties`.
*   **Fix:** Ensure `FateEngine._apply_outcome` actually merges `revealed_properties` into the object's public `properties` so other agents can see them in future ticks.
*   **File:** `tsukuyomi/proto/fate_engine.py`

### 1.3 Guest API: Security Bypass Fix
*   **Issue:** `GuestServicer.SubmitProposal` lacks the session/token validation implemented in `FateEngineServicer`. This allows an attacker to control any actor via the Guest API.
*   **Fix:** Implement session validation in `GuestServicer.SubmitProposal` and `GuestServicer.Subscribe`. Only allow actions for the `agent_id` associated with the `session_id`.
*   **File:** `tsukuyomi/proto/grpc_server.py`

## 2. Architecture & Structure Improvements

### 2.1 Drama Engine Integration (GAPS FOUND)
*   **Issue:** `DramaDirector` and `CatalystSystem` are "zombie modules"—implemented but never instantiated or hooked into the simulation loop.
*   **Fix:** 
    1. Instantiate `DramaDirector` in `GrpcServer.__init__`.
    2. Attach `DramaDirector.on_tick_resolved` to `engine.post_resolution_hooks`.
    3. Update `AgentBrain` to call `DramaDirector.update_sentiment` after LLM plan generation.
*   **Files:** `tsukuyomi/proto/grpc_server.py`, `tsukuyomi/brain/AgentBrain.py`

### 2.2 Scenario Alignment: Modern Catalyst Templates
*   **Issue:** `CatalystSystem` templates are medieval (Omen, Straggler, War). These break immersion in the juror/trial simulation.
*   **Fix:** Replace medieval templates with modern trial-relevant ones: "Leaked Evidence", "Witness Outburst", "Anonymous Tip", "Social Media Trend".
*   **File:** `tsukuyomi/brain/CatalystSystem.py`

### 2.3 Gossip Perception Loop
*   **Issue:** Agents "leak" thoughts but cannot "hear" gossip. `PerceptionPipeline` has no hook to `GossipProtocol`.
*   **Fix:** Add `_process_gossip_channel` to `PerceptionPipeline.process`. It should query `GossipProtocol.get_gossip_for_agent` and convert rumors into `Percept` objects with the `HEARING` channel or a new `SOCIAL` channel.
*   **Files:** `tsukuyomi/brain/PerceptionPipeline.py`, `tsukuyomi/brain/AgentBrain.py`

## 3. Performance & Logic Refinement

### 3.1 Perception Occlusion (Logic Gap)
*   **Issue:** `PerceptionPipeline._is_occluded` is a `TODO`. Agents currently have X-ray vision through walls.
*   **Fix:** Implement a simple bounding-box occlusion check against `world_state.objects` that have a "blocks_vision" property.
*   **File:** `tsukuyomi/brain/PerceptionPipeline.py`

### 3.2 Memory Indexing
*   **Issue:** (Confirmed) String search in `WorkingMemory.refresh` is O(N).
*   **Fix:** Implement keyword pre-indexing in `MemoryManager.ingest_tick`.

## 4. Implementation Plan (GLM 4.7)

1.  **Codebase Purge:** Remove redundant root `proto/` and fix imports.
2.  **Unified Security:** Secure the Guest API to match FateEngine standards.
3.  **Activate Drama:** Hook `DramaDirector` into the Fate Engine and update Catalyst templates.
4.  **Close Gossip Loop:** Wire Gossip into Perception so agents actually "hear" rumors.
5.  **Refine Persistence:** Ensure `EXAMINE` findings persist in WorldState.

---
*Verified by Senior Technical Lead Pony Alpha.*
