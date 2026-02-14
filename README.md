# 🌙 Tsukuyomi V2 - Real World Simulation Engine

**The Autonomous Agent Platform for Massively Multi-Agent Simulations.**

**Current Version:** 2.0 (Development)
**Status:** 🏗️ Under Active Construction

---

## 🎯 Vision

Tsukuyomi is an open-source engine designed to simulate complex, dynamic worlds populated by autonomous AI agents (Agent Brains). Unlike static chatbots, these agents have **bodies (Avatars)**, **needs (Drives)**, and **perspectives (Memory)**. They perceive the world, make decisions, and interact with it to create emergent, narrative experiences.

**The Goal:** Create a "Living World" where agents live, trade, fight, and govern themselves without human scripts.

---

## 🏗️ Architecture Overview

Tsukuyomi follows a **Client-Server** architecture driven by gRPC.

### 1. Fate Engine (The Core)
*   **Role:** The authoritative "Source of Truth" for the world state.
*   **Tech:** Python `asyncio`, gRPC Server.
*   **Responsibilities:**
    *   Manages the Simulation Tick (Time).
    *   Maintains `WorldState` (All Actors, Objects, Locations).
    *   Resolves `Proposals` (Agent Actions: Move, Interact, Idle, Emote).
    *   Handles Conflict Resolution (Who gets the coin?).
    *   Stores Persistence (Database).

### 2. Agent Brain (The Intelligence)
*   **Role:** Client-side controller. Acts as the "Cortex" for the agent.
*   **Tech:** Python `asyncio`, gRPC Client.
*   **Responsibilities:**
    *   Receives `Percepts` (Sensory Data).
    *   Manages `Memory` (Short-term Gossip, Long-term RAG).
    *   Manages `Needs` (Hunger, Fatigue, Boredom).
    *   Generates `Proposals` (Intent to Act).
    *   Interfaces with `LLM Service` (Reasoning Engine).

### 3. World Management (The Stage)
*   **Role:** Defines the environment, objects, and rules of physics/interaction.
*   **Responsibilities:**
    *   Holds `EnvironmentObjects` (Props, Doors, Terrain).
    *   Defines `Affordances` (Rules: "Can I sit here?", "Can I pick this up?").
    *   Enforces Spatial constraints (Walls, Collision).

### 4. Orchestration (The Director)
*   **Role:** Ensures the story moves forward. Prevents "sandbox death" (agents idling forever).
*   **Responsibilities:**
    *   Tension tracking (4-axis metric).
    *   Event injection (Environmental triggers).

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   A running Fate Engine server (default: `localhost:50051`).
*   Groq/Claude API Key (set in `.env`).

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/safouane/tsukuyomi.git
cd tsukuyomi

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Fate Engine
python3 tsukuyomi/core/fate_engine.py
```

### Running a Scenario
```bash
# Run the "Busy Marketplace" scenario
python3 experiments/marketplace_roleplay.py
```

---

## 📋 Development Roadmap

We are currently transitioning from **Phase 1 (Foundations)** to **Phase 2 (Interaction & Physics)**. For detailed technical specs, see `/docs/ROADMAP.md`.

### Phase 1: Foundations (Weeks 1-2)
*   **[x]** Fix Type Mismatch in `AgentBrain` (gRPC params).
*   **[x]** Switch to high-throughput model (`llama-3.1-8b-instant`) to fix rate limits.
*   **[ ]** Implement `AgentNeeds` class (Hunger, Fatigue, Boredom).
*   **[ ]** Implement `WorldBuilder` API to server.
*   **[ ]** Write "Marketplace" scenario script (Proof of Concept).

### Phase 2: World Dynamics (Weeks 3-5)
*   **[ ]** Implement `SpatialIndex` (Grid or Quadtree).
*   **[ ]** Implement `ProposalWindow` logic (Commitment phase).
*   **[ ]** Add `Affordance` system to `EnvironmentObject`.
*   **[ ]** Implement `Visual` percepts (Raycasting/Line-of-sight).

### Phase 3: Persistence & Scale (Weeks 6-8)
*   **[ ]** Database schema design (PostgreSQL).
*   **[ ]** Implement `SaveWorld` / `LoadWorld` gRPC methods.
*   **[ ]** Optimize gRPC streaming for 100+ concurrent agents.
*   **[ ]** Long-term memory (RAG) integration.

---

## 🗂️ Project Structure

*   `/tsukuyomi/core/` - Core engine logic (Fate Engine, World).
*   `/tsukuyomi/brain/` - Client logic (Agent Brain, Needs System).
*   `/tsukuyomi/proto/` - gRPC definitions (`.proto` files).
*   `/tsukuyomi/experiments/` - Scenario scripts (`angry_men.py`, `marketplace.py`).
*   `/tsukuyomi/docs/` - Architecture and Roadmap.
*   `/tsukuyomi/dev-artifacts/` - Analysis and temporary files.

---

## 🤝 Contributing

We welcome contributions! Please see `/docs/CONTRIBUTING.md` for guidelines.

*   **Design Philosophy:** "General Engine" over "Custom Scenarios". Build systems, not scripts.
*   **Workflow:** Discuss -> Branch -> Code -> Test -> PR.
*   **Prohibited:** Do not hardcode logic for specific scenarios (e.g., "If Davis, say X") in the engine core.

---

**Maintained by:** safouane (safouane_94908)
