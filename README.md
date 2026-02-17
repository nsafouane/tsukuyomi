# 🌙 Tsukuyomi V2 - Real World Simulation Engine

**The Autonomous Agent Platform for Massively Multi-Agent Simulations.**

**Current Version:** 2.0 (Development)  
**Status:** 🏗️ Phase 13+ Complete | Multi-Zone Synchronization Active

---

## 🎯 Vision

Tsukuyomi is an open-source engine designed to simulate complex, dynamic worlds populated by autonomous AI agents (Agent Brains). Unlike static chatbots, these agents have **bodies (Avatars)**, **needs (Drives)**, and **perspectives (Memory)**. They perceive the world, make decisions, and interact with it to create emergent, narrative experiences.

**The Goal:** Create a "Living World" where agents live, trade, fight, and govern themselves without human scripts.

---

## ✅ Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1-3 | Fate Engine Core, Cognitive Core, Action Logic | ✅ Complete |
| 4-6 | Persistence, gRPC Infrastructure, Agent Intelligence | ✅ Complete |
| 7-9 | Belief Dynamics, Social Layers, Performance & Scale | ✅ Complete |
| 10 | External Guest Protocol | ✅ Complete |
| 11 | World Expansions (Multi-Room Spatial Logic) | ✅ Complete |
| 12 | Multi-Zone Shard Synchronization | ✅ Complete |
| 13 | World Building: Roman-Carthage Trial Scenario | 🚧 In Progress |
| 14+ | Personality System, Reasoning Module | 🚧 In Progress |

---

## 🏗️ Architecture Overview

Tsukuyomi follows a **Client-Server** architecture driven by gRPC.

### 1. Fate Engine (The Core)
*   **Role:** The authoritative "Source of Truth" for the world state.
*   **Tech:** Python `asyncio`, gRPC Server, SQLite Persistence.
*   **Features:**
    *   20 TPS deterministic simulation loop
    *   Multi-zone shard synchronization
    *   Cross-zone gossip propagation
    *   Proposal window with conflict resolution

### 2. Agent Brain (The Intelligence)
*   **Role:** Client-side controller. Acts as the "Cortex" for the agent.
*   **Tech:** Python `asyncio`, gRPC Client, RAG Memory System.
*   **Features:**
    *   3-Tier Memory (Sensory, Working, Long-term RAG)
    *   Emotional PAD State (Pleasure-Arousal-Dominance)
    *   Needs System (Hunger, Fatigue, Boredom, Social)
    *   Belief Dynamics with Confirmation Bias
    *   Personality System with Drift Monitoring

### 3. Drama Director (The Orchestrator)
*   **Role:** Ensures narrative momentum and prevents "sandbox death".
*   **Features:**
    *   Context-aware tension tracking
    *   Event library with branching narratives
    *   Agent-specific drama triggers

### 4. Guest Protocol (External Integration)
*   **Role:** Allow external agents to join simulations.
*   **Features:**
    *   Standalone Guest API client
    *   Handshake authentication
    *   Real-time tick streaming

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
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=tsukuyomi --cov-report=term-missing
```

### 3. Run a Demo
```bash
# Marketplace simulation
python3 experiments/marketplace_roleplay.py

# Angry Men jury simulation
python3 experiments/angry_men.py
```

### 4. Connect as a Guest Agent
```python
from tsukuyomi.guest_sdk import GuestClient

client = GuestClient("localhost:50051", secret="tsukuyomi-secret-2026")
await client.connect()
await client.register("MyAgent", x=10, y=10)
```

---

## 📁 Project Structure

```
tsukuyomi/
├── tsukuyomi/
│   ├── brain/                 # Agent intelligence modules
│   │   ├── reasoning/         # Decision records, confidence calibration
│   │   ├── personality/       # OCEAN profiles, drift monitoring
│   │   ├── memory/            # RAG system, decay calculator
│   │   └── AgentBrain.py      # Main cognitive controller
│   ├── core/                  # Core engine logic
│   │   ├── drama/             # Drama director, event library
│   │   ├── world_builder.py   # Environment construction
│   │   └── spatial_index.py   # Quadtree spatial queries
│   ├── proto/                 # gRPC definitions
│   │   ├── fate_engine.py     # Server implementation
│   │   ├── grpc_client.py     # Python client
│   │   └── *.proto            # Protocol buffer schemas
│   ├── scenarios/             # Scenario definitions
│   └── guest_sdk.py           # External agent SDK
├── tests/                     # Test suite
│   ├── test_phase1_components.py
│   ├── test_reasoning.py
│   ├── test_personality.py
│   └── test_drama.py
└── experiments/               # Demo scripts
```

---

## 🔧 Configuration

### Environment Variables
```bash
# LLM Service (Groq/Claude)
export GROQ_API_KEY=your_key_here

# gRPC Server
export GRPC_PORT=50051

# TLS (Optional)
export TLS_CERT_PATH=certs/server.crt
```

### Security Settings
The gRPC client defaults to secure TLS connections. To allow insecure connections for development:
```python
client = FateEngineClient("localhost:50051", allow_insecure=True)
```

---

## 📊 Test Coverage

| Module | Coverage |
|--------|----------|
| `brain/reasoning/decision_record.py` | 85% |
| `brain/personality/profile.py` | 77% |
| `brain/needs_system.py` | 76% |
| `core/world_builder.py` | 94% |
| **Overall** | 31% |

Run coverage report:
```bash
python3 -m pytest tests/ --cov=tsukuyomi --cov-report=html
```

---

## 🤝 Contributing

We welcome contributions! Please see `/docs/CONTRIBUTING.md` for guidelines.

*   **Design Philosophy:** "General Engine" over "Custom Scenarios". Build systems, not scripts.
*   **Workflow:** Discuss → Branch → Code → Test → PR.
*   **Code Style:** Follow PEP 8, use type hints, write docstrings.

---

## 📝 License

MIT License - See LICENSE file for details.

---

**Maintained by:** safouane (safouane_94908) & Tanit (AI Co-founder)
