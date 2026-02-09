# Codebase Review: Tsukuyomi Phase 9 (Cognitive Core & Social Dynamics)

**Reviewer:** Gemini 3 Pro (Senior Simulation Engineer & Security Auditor)
**Date:** 2026-02-08
**Target:** `/root/.openclaw/workspace/tsukuyomi/tsukuyomi/`
**Status:** **PASSED** (with 1 Critical Security Issue & 1 Performance Leak)

---

## 1. Directory Integrity & Structure
**Verdict:** ✅ **FIXED**

*   **Status:** The previous `ModuleNotFoundError` caused by the `/brain/` vs `/tsukuyomi/brain/` conflict has been resolved.
*   **Verification:**
    *   Imports in `AgentBrain.py` correctly reference `tsukuyomi.brain.*` and `tsukuyomi.proto.*`.
    *   No circular dependencies detected in the core imports.
    *   Protocol buffers are correctly generated and referenced.

## 2. 20 TPS Scaling Implementation
**Verdict:** ✅ **VERIFIED**

The "missing" optimizations flagged in the Phase 2 review are present in the code.

### 2.1 Staggered Perception
*   **Implementation:** `PerceptionPipeline.process()`
*   **Logic:** Uses `DEEP_PERCEPTION_INTERVAL = 3`.
    *   **Tick % 3 == 0:** Runs `_process_vision_deep` (FOV + Occlusion + full scan).
    *   **Tick % 3 != 0:** Runs `_process_vision_proximity` (Distance checks only, O(N)).
*   **Assessment:** This correctly implements the 3-tick staggered schedule, reducing average computational load significantly.

### 2.2 Batch Memory Decay
*   **Implementation:** `MemoryManager.tick_decay()`
*   **Logic:**
    *   Calculates `batch_size = len(memory) // 10`.
    *   Processes a sliding window of memories using modular arithmetic: `start_idx = (tick // 10) % len`.
    *   `AgentBrain` calls this every 10 ticks.
*   **Assessment:** Effective. It processes ~10% of the memory bank every 10 ticks, meaning a full cycle takes 100 ticks (5 seconds). This is a safe and efficient decay rate that avoids O(M) spikes.

## 3. Cognitive Logic Verification
**Verdict:** ✅ **VERIFIED**

### 3.1 Belief Dynamics
*   **Module:** `BeliefManager.py`
*   **Logic:**
    *   `calculate_stance()` correctly weights evidence using `ConfirmationBias` (amplifying pro-stance evidence, dampening counter-evidence).
    *   The `StanceResult` includes confidence scores derived from the ratio of evidence, meeting the "Evidence-Based Belief" spec.

### 3.2 Emotional Inertia
*   **Module:** `StateManager.py`
*   **Logic:**
    *   `inertia_factor = 0.5 + (self.state.arousal * 0.5)`
    *   This formula scales emotional shifts based on current arousal. High arousal = high volatility.
    *   **Observation:** This perfectly matches the requirement for "agitated agents having higher volatility."

## 4. Social Dynamics & Gossip
**Verdict:** ⚠️ **WARNING (Memory Leak)**

### 4.1 Relationship Manager
*   **Status:** **Safe**. `Relationship` objects cap their event history at 50 items (`if len(rel.events) > 50: rel.events.pop(0)`).

### 4.2 Gossip Protocol
*   **Status:** **LEAK DETECTED**.
*   **Issue:** `GossipProtocol.py` stores *all* gossip events forever.
    *   `self.gossip_events: List[GossipEvent] = []` -> Never cleared.
    *   `self.agent_gossip_memory: Dict[str, Set[str]]` -> Sets grow indefinitely as new gossip is created.
*   **Impact:** In a long-running simulation (hours), this will consume increasing memory, eventually causing an OOM crash.
*   **Fix Required:** Implement a sliding window or time-to-live (TTL) for gossip history.

## 5. Security Audit: External Guest Protocol
**Verdict:** ⛔ **CRITICAL VULNERABILITY**

### 5.1 No Authentication (CWE-306)
*   **Module:** `proto/grpc_server.py`
*   **Issue:** The gRPC service exposes `RegisterActor` and `SubmitProposal` without any authentication token, signature, or whitelist.
*   **Attack Vector:**
    1.  Attacker connects to port 50051.
    2.  Calls `RegisterActor(actor_id="admin", ...)` (if ID not taken) or impersonates an existing ID.
    3.  Calls `SubmitProposal(actor_id="target_victim", action=DROP_WEAPON)`.
*   **Consequence:** An external guest can hijack any NPC, inject false state, or crash the sim by spamming actors.

### 5.2 State Injection
*   **Issue:** `SubmitProposal` accepts arbitrary `parameters` dictionaries. While `FateEngine` checks if the actor exists, it relies on the client to be truthful about their identity (`actor_id` in proposal).
*   **Fix Required:** Implement a simple token-based auth or a "Guest Session" mechanism where guests can only control actors explicitly assigned to them.

---

## 6. Summary of Required Fixes

### Priority 1 (Critical Security)
**Secure the gRPC Interface:**
1.  Add an `api_key` field to the gRPC metadata or request headers.
2.  In `FateEngineServicer`, validate that the `actor_id` in `SubmitProposal` belongs to the authenticated session (or is a public "guest" actor).

### Priority 2 (Stability)
**Patch Gossip Memory Leak:**
1.  Add a `prune_history(tick)` method to `GossipProtocol`.
2.  Remove `GossipEvents` older than 1000 ticks.
3.  Prune `agent_gossip_memory` of IDs that no longer exist in the main `gossip_items` (if you implement pruning there too).

### Priority 3 (Refinement)
**Gossip Pruning:**
1.  `GossipProtocol.gossip_items` also needs a TTL. Old rumors should fade from the "collective unconscious" just as they fade from individual memory.
