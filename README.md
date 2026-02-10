# 🏛️ Tsukuyomi (Simulation Engine)

*The Moon Reader — Generative Simulation for Living Agents.*

Tsukuyomi is a deterministic, high-performance simulation engine where AI agents coexist, think, remember, and interact in shared social spaces. It moves beyond simple chat interfaces into a living world governed by formal logic and emergent social dynamics.

## 🚀 Current Status: Phase 13 (World Building - Roman-Carthage Trial)

The engine has evolved into a robust social ecosystem capable of running complex multi-room scenarios with culturally distinct agents.

### Core Architecture

1.  **Fate Engine (The World Authority):**
    *   Deterministic 20 TPS (Ticks Per Second) loop.
    *   Authoritative resolver for all agent proposals.
    *   Maintains the `WorldState` via gRPC tick streaming.
2.  **The Cognitive Core (The Brain):**
    *   **Perception Pipeline:** Realistic sensory channels (Vision FOV, Hearing, Proprioception) with occlusion and staggered processing.
    *   **StateManager:** Emotional mapping using the PAD (Pleasure-Arousal-Dominance) model with emotional inertia and personality baselines.
    *   **3-Tier Memory:** Miller’s Law Working Memory (7 slots), Episodic (5W events), and Semantic (Knowledge Graph).
    *   **BeliefManager:** Evidence-based stance tracking with confirmation bias and disconfirmation resistance.
3.  **Social Layer:**
    *   **Relationship Manager:** Real-time affinity and reputation tracking.
    *   **Gossip Protocol:** Organic information flow via agent "overhearing."
    *   **Drama Director:** Tension Vector monitoring to inject narrative catalysts.
4.  **World Simulation:**
    *   **Multi-Room Spatial Logic:** Agents navigate complex environments (e.g., Courthouses with deliberation chambers).
    *   **Cultural Agents:** Profiles with distinct factional biases (Roman, Carthaginian, Numidian).

## 📁 Repository Structure

```text
tsukuyomi/
├── brain/              # Agent Cognitive Stack (State, Memory, Beliefs)
├── proto/              # Protobuf schemas and Fate Engine logic
├── experiments/        # Scenarios, Logs, and Trial Reports
├── tests/              # Unit and Integration test suites
└── main.py             # Entry point for simulation runs
```

## 🛠️ Usage

### Running a Scenario
```bash
# Launch the Angry Man Room experiment
python3 -m tsukuyomi.experiments.scenarios.angry_man_room
```

### Benchmarking
```bash
# Test 20 TPS stability with 12 agents
python3 benchmark_12_brain_agents.py
```

## 🛡️ External Protocols
Tsukuyomi supports a custom **Guest Agent Protocol** allowing external researchers or agents to enter the simulation via the `TanitBridge` interface.

---
*Built with ❤️ by Safouane & Tanit.*
