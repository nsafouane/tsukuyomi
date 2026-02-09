# 🏛️ Tsukuyomi Experiment Report: The Angry Man Room

**Date:** February 8th, 2026
**Lead Researcher:** Tanit
**Trial Identifier:** TRIAL-20260207-01 (Baseline) / TRIAL-20260208-FAILED (Cognitive Core)

---

## 1. Executive Summary
This report analyzes two experimental trials of "The Angry Man Room" scenario. The first trial (Feb 7th) demonstrated stable 20 TPS performance and coherent character consistency but highlighted the limitations of "static" agents. The second trial (Feb 8th) was an attempt to launch the **Cognitive Core (Phase 2)**, which resulted in a silent crash of the agent brains due to a directory structure conflict, though the engine itself remained stable.

## 2. Trial Analysis (Feb 7th - Successful Baseline)

### Observations
*   **Stability:** The Fate Engine maintained a steady 20 TPS across 23,601 ticks (~20 minutes).
*   **Consistency:** "The Angry Man" maintained a hostile, dismissive tone throughout, while "The Bank Teller" consistently voiced uncertainty.
*   **Emergent Deduction:** The Bank Teller correctly identified the contradiction between the old man's physical condition and the timing of his testimony (Tick 4886).
*   **Social Contagion:** Probes injected by Tanit (Guest Agent) regarding the stroke-limp and the glasses visibility were successfully "picked up" and amplified by other jurors.

### Weaknesses & Gaps
1.  **Static Stance Trap:** Despite voicing "reasonable doubt," the Bank Teller never flipped their internal `stance` variable. The doubt remained textual, never becoming mechanical.
2.  **Omniscience:** Agents responded to events they shouldn't have seen/heard (e.g., quiet thoughts or distant movements), indicating a lack of sensory occlusion.
3.  **Flat Emotions:** Emotional states were defined by static strings in profiles rather than dynamic vectors. There was no "momentum" or "inertia" to their moods.
4.  **Recency Bias:** Memory retrieval was purely chronological. Agents forgot critical facts once they fell out of the "last 10 memories" buffer.

## 3. Post-Mortem (Feb 8th - Phase 2 Failed Launch)

**Result:** Silent Brain Crash.
**Root Cause:** The autonomous implementation sprint created a directory conflict between `/brain/` and `/tsukuyomi/brain/`. Brains launched with `ModuleNotFoundError` for internal dependencies.
**Resolution:** Codebase consolidated and verified. Imports fixed. All Phase 2 modules (BeliefManager, StateManager, WorkingMemory) are now verified functional in unit tests.

## 4. Architectural Improvements (Phase 9 Implementation)

We have implemented the following to address the gaps identified in the baseline trial:

*   **Belief Graph:** Replaced static stances with an evidence-based graph. Agents now "flip" when the weight of evidence against a stance exceeds their `ConfirmationBias` threshold.
*   **PAD Emotional Model:** Introduced 3D emotional vectors (Pleasure, Arousal, Dominance). Agitated agents (high arousal) now have narrower perception and higher volatility.
*   **Miller’s Law Working Memory:** Implemented a 7-slot sliding window that prioritizes **salience** and **relevance** over chronological order.
*   **Gossip & Relationship Graphs:** Social status now influences weight of evidence. A juror is less likely to believe someone they have a negative relationship with.

## 5. Next Steps: "The Evidence Room" (Trial 3)

The next experiment will validate the **Cognitive Core**.
*   **Objective:** Force a stance flip.
*   **Scenario:** Add a "Switchblade" object with a `hidden_property` ("NOT unique").
*   **Protocol:** Agents must EXAMINE the knife to discover the property, which will then flow into the BeliefGraph as evidence.

---
*Status: Codebase is verified. Ready for re-run.*
