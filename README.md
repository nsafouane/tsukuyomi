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
| Phase 3: MVP Implementation | 🔄 IN PROGRESS | Complete MVP_SPEC.md & ship testable MVP |

---

## 🎯 CURRENT PRIORITY

**Complete MVP_SPEC.md entirely and ship testable MVP**
1. Finalize all sections of MVP_SPEC.md
2. Implement remaining components per spec
3. Achieve test coverage target (85%+)
4. Package for testing

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
