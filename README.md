# 🌙 Tsukuyomi - Intelligent Simulation Engine

**The Complete AI Infrastructure for Games, Storytelling, and Agent Simulations.**

**Current Version:** MVP v0.1 (Architecture Unification)  
**Status:** 🏗️ Phase 1 Active | Consolidating Core Logic

---

## 🎯 Vision

Tsukuyomi is an open-source, universal backend engine designed to simulate complex, dynamic worlds populated by autonomous AI agents. It goes beyond static chatbots by creating a "Living World." Agents have **bodies (Avatars)**, **needs (Drives)**, **perspectives (Beliefs & Memory)**, and **emotions (PAD State)**.

**The Goal:** Serve as the ultimate AI infrastructure that natively drives world physics, environmental rules, and dynamic narrative flow, capable of producing complete, unscripted story-worlds where agents live, interact, and govern themselves.

---

## 🏗️ Architecture Overview

Tsukuyomi relies on a highly modular **Client-Server** and **Unified Base** architecture. The engine supports both tick-based simulations (gRPC) and standalone asynchronous operation, all running on the exact same underlying logic.

### 1. The Unified Core (`BaseAgent`)
*   **Role:** The single source of truth for all cognitive features. 
*   **Features:**
    *   3-Tier Memory System (Working, Semantic, RAG Episodic)
    *   Unified PAD Emotional Core (Pleasure-Arousal-Dominance)
    *   Belief Dynamics and Tracking
    *   Needs System (Hunger, Fatigue, Social)

### 2. Fate Engine (The Server)
*   **Role:** The authoritative "Source of Truth" for world state and physics.
*   **Tech:** Python `asyncio`, gRPC Server.
*   **Features:**
    *   Deterministic simulation tick loop
    *   Spatial proximity and raycasting validation
    *   Affordance-based interaction checking
    *   Proposal window with conflict resolution

### 3. Agent Brain (The Client)
*   **Role:** Connects the `BaseAgent` intelligence to the `FateEngine` world via gRPC. 
*   **Process:** Evaluates the engine's "Percepts" through its core emotional and memory systems, then submits action "Proposals" back to the server.

### 4. Drama Director (The Narrator)
*   **Role:** Ensures narrative momentum and prevents "sandbox death".
*   **Features:**
    *   Context-aware tension tracking
    *   Event injection (weather, disasters, world changes)
    *   Dynamic story oversight directly from the engine

---

## 🚀 Quick Start

### Prerequisites
*   Python 3.10+
*   `pip install -r requirements.txt`

### 1. Start the Fate Engine Server
```bash
cd tsukuyomi
python3 -m tsukuyomi.proto.grpc_server
```

### 2. Run Tests
*All tests must be run from the dedicated `/tests/` directory.*
```bash
# Run all tests
python3 -m pytest tests/ -v
```

### 3. Run a Scenario Experiment
*Scenarios are isolated experiments used purely to test engine capabilities.*
```bash
# Marketplace simulation
python3 experiments/marketplace_roleplay.py

# Angry Men jury simulation
python3 experiments/angry_men.py
```

---

## 📁 Project Structure

```text
tsukuyomi/
├── tsukuyomi/
│   ├── core/                  # Unified BaseAgent, emotion, memory, and engine logic
│   ├── brain/                 # Simulation/gRPC specific implementations
│   ├── agent/                 # Standalone/Async specific implementations
│   ├── proto/                 # gRPC protocol schemas and server implementation
│   ├── dev-artifacts/         # Specifications, roadmaps, and architecture plans (REQUIRED)
│   └── guest_sdk.py           # External agent SDK
├── docs/                      # Official manuals, published architecture, and guides
├── tests/                     # Dedicated test suite (all tests live here)
└── experiments/               # Isolated testing scenarios and demo scripts
```

---

## 🔧 Configuration

### Environment Variables
```bash
# LLM Service (Provider configurable)
export GROQ_API_KEY=your_key_here

# gRPC Server
export GRPC_PORT=50051

# TLS (Optional)
export TLS_CERT_PATH=certs/server.crt
```

---

## 🤝 Contributing

We welcome contributions! Please review the `rules.md` at the root of the project before contributing.
*All specifications, plans, and architectural proposals MUST be placed in `/tsukuyomi/dev-artifacts/`.*

*   **Design Philosophy:** "Unified Engine" over "Custom Scenarios". Build generic systems that govern any narrative, not hardcoded scripts.
*   **Code Style:** Python `snake_case` files, `PascalCase` classes, strict <700 lines-of-code per file limits.
*   **Workflow:** Discuss → Plan in `dev-artifacts/` → Code → Test → PR.

---

## 📝 License

MIT License - See LICENSE file for details.

---

**Maintained by:** safouane