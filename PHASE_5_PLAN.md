# 🏛️ Project Tsukuyomi - Phase 5 Implementation Plan

**Current Status:** Phase 4 (gRPC) Completed.
**Next Phase:** Phase 5 (Enhanced Simulation & Persistence).

## 🎯 Objectives
1.  **World Expansion:** Add environmental objects (trees, items, furniture) with interaction rules.
2.  **Persistent Storage:** Implement TickHistory persistence to a SQLite database.
3.  **Visualizer Foundation:** Create a basic CLI/Web dashboard to monitor world state in real-time.

## 📂 New Structure (Planned)
```
tsukuyomi/
├── persistence/           # New: Database management
│   ├── db_manager.py      # SQLite/SQLAlchemy setup
│   └── models.py          # ORM models for Actors, Items, Ticks
├── world/                 # New: Domain logic
│   ├── environment.py     # Static and dynamic objects
│   └── objects.py         # Item definitions and behaviors
└── dashboard/             # New: Visualizer
    ├── app.py             # Simple Flask/FastAPI server
    └── static/            # Visualizer frontend
```

## 🛠️ Step 1: Environment & Objects
- Define `EnvironmentObject` protobuf in `core.proto`.
- Implement `environment.py` to manage objects in the `WorldState`.
- Add `COLLECT` and `USE` action types to the `FateEngine`.

## 🛠️ Step 2: Persistent TickHistory
- Create `TickHistoryStore` to save `TickState` snapshots.
- Use SQLite for MVP persistence (low overhead).
- Ensure async writing to avoid blocking the tick loop (Outbox pattern).

## 🛠️ Step 3: Real-time Visualizer
- Create a server-streaming gRPC client that feeds a dashboard.
- Display actor positions, states, and recent events.

---

## 📋 Task List (Phase 5)
- [ ] Update `core.proto` with `EnvironmentObject` and new actions.
- [ ] Implement `db_manager.py` for SQLite storage.
- [ ] Integrate DB persistence into `simulation_loop.py` or `fate_engine.py`.
- [ ] Add static objects to the world initialization.
- [ ] Create basic dashboard prototype.

*Plan drafted by Tanit (Executor) — February 5, 2026.*
