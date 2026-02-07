# MVP_COMPLETION_CHECKLIST.md - Final Verification for Working MVP

**Status:** UPDATED (Task 1 & 2 Complete)
**Project:** Tsukuyomi
**Model:** Opus 4.6 (Planning)
**Date:** 2026-02-07

---

## 1. Goal
Verify that current codebase fully implements a "testable working MVP" as per `MVP_SPEC.md`, ensuring all foundational systems (Engine, gRPC, Actions, Persistence) are robust before moving to Phase 6 (Cognition).

---

## 2. Core Functional Checklist

### [✅] Phase 1-4: Engine & Infrastructure
- [x] **Fate Engine:** Deterministic 20 TPS loop.
- [x] **Protobuf:** All data structures use generated bindings.
- [x] **gRPC Server:** `SubmitProposal`, `GetWorldState`, `StreamTickUpdates` operational.
- [x] **gRPC Client:** Python client for remote actor control.
- [x] **Persistence:** SQLite storage of all `TickState` data.
- [x] **Resume:** Engine resumes correctly from latest DB tick.

### [⚠️] Phase 5: Action Logic & Reflexes (Verification Needed)
- [x] **COLLECT Action:** Logic implemented and tested in `test_phase_6.py`.
- [x] **USE Action:** Logic implemented and tested.
- [x] **Varied Objects:** ✅ IMPLEMENTED. Expanded world with `apple_market`, `hammer_tool`, and `chest_wood`.
- [x] **Reflex Integration:** ✅ IMPLEMENTED. NPCs now perceive and collect nearby `food` and `tool` objects.

### [✅] Missing MVP "Working" Deliverables
- [x] **Integrated Scenario Test:** ✅ IMPLEMENTED & PASSED. `test_mvp_complete.py` verifies Server-Client-Action-Persistence loop.
- [ ] **Web Visualizer (Optional but recommended):** The CLI dashboard works, but a basic HTTP/WebSocket relay for a browser view would make it "testable" by others.

---

## 3. Engineering Audit
- [x] **Test Coverage:** ✅ All `proto/test_*.py` and `test_mvp_complete.py` passing.
- [ ] **Log Audit:** Ensure \"Latency vs Intelligence\" logs (tick duration) are clear.
- [ ] **Documentation:** README update with \"How to run full MVP demo\" instructions.

---

## 4. Next Steps (Pre-Upgrade)
1. Build `test_mvp_complete.py` (The "Boss" Test).
2. Review this checklist with Gemini 3 Pro.
