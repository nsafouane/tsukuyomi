# 🏛️ Project Tsukuyomi

**Path:** `/root/.openclaw/workspace/tsukuyomi/`
**Name Meaning:** "The Moon Reader" (月読)
**Type:** Generative Agent Simulation Engine

---

## 🎯 Vision

A simulation engine where AI agents have *real cognition*:
- **Dual-mode thinking:** Fast reflexes + slow deliberation via LLM
- **Persistent memory:** Episodic + semantic memory that shapes behavior
- **Social dynamics:** Gossip, relationships, reputation systems
- **Deterministic replay:** All LLM outputs captured as proposals for reproducibility

---

## 📂 Structure

```
tsukuyomi/
├── README.md              # This file (context source of truth)
├── ARCHITECTURE.md        # Core design document (v1.1)
├── MVP_SPEC.md            # Full technical specification
├── TSUKUYOMI_INTEGRATION_SPEC.md  # Moltbook integration spec
├── main.py                # Entry point
├── simulation_loop.py     # Core tick loop
├── reflex_layer.py        # Fast-mode agent responses
├── tests.py               # Test suite (85%+ coverage target)
├── proto/                 # Working prototype code
├── research/              # Background research
└── moltbook-drafts/       # Community post drafts
```

---

## 🛠️ Tech Stack

| Component | Tool |
|-----------|------|
| Planning & Specs | Claude Opus 4.5 (via OpenCode) |
| Main Coding | GLM 4.7 (via OpenCode) |
| Testing | pytest (80%+ coverage) |
| Version Control | git |

---

## 📋 Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Fate Engine | ✅ DONE | Deterministic tick loop, replay system |
| Phase 2: Internal World | ✅ DONE | Environment physics, NPC behavior trees |
| Phase 3: MVP Implementation | ✅ DONE | Complete MVP_SPEC.md & ship testable MVP |
| Phase 5: Persistence & Objects | ✅ DONE | SQLite storage, environment expansion |
| Phase 6: Agent Integration | ✅ DONE | "The Brain", Memory, Angry Man Room |
| Phase 8: Community Integration | ✅ DONE | Tick downsampling, Gossip Protocol, Performance benchmark |

---

## 🎯 CURRENT STATUS

**Phase 8: Community Integration & Performance** ✅ COMPLETE
- [x] Optimize Tick Streaming for high-latency Moltbook clients
- [x] Implement "Gossip Protocol" (Information leakage between deliberating agents)
- [x] Benchmark 20 TPS with 12 concurrent "Brain" agents

**Deployment:** 🚀 Ready for Moltbook community deployment

**Next Phase:** Phase 9 - Advanced Social Dynamics (Planning)

---

## 🚀 MVP DEMO (HOW TO RUN)

To run the full end-to-end MVP demonstration and verification:
```bash
# From the workspace root (/root/.openclaw/workspace/tsukuyomi)
PYTHONPATH=. ./venv/bin/python3 test_mvp_complete.py
```
This script automates server startup, actor actions (movement & collection), and verifies persistence across a server restart.

---

## 🔑 Key Decisions (Open)

- [ ] Game engine vs. storytelling platform vs. social simulation?
- [ ] Target first use case / proof of concept?
- [ ] LLM strategy (local models? API? fine-tuned?)
- [ ] Moltbook agent interoperability scope?

---

## 📜 Rules & Conventions

1. **Determinism first** — Every LLM call must be captured for replay
2. **Test before merge** — No code without tests
3. **Spec before code** — Update MVP_SPEC.md before major changes
4. **OpenCode only** — All coding through OpenCode agent

---

## 🔗 Related

- **Task Tracking:** `PROJECT_TREE.md` in workspace root
- **Research/Reports:** `/root/.openclaw/workspace/research-reports/`
- **Community:** Moltbook (pending dev key)

---

*Load this README before any Tsukuyomi task.*
