<div align="center">

# **Tsukuyomi** 
### *Multi-Agent Simulation Engine*

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-3.8.4/)
[![gRPC](https://img.shields.io/badge/grpc-1.50+-green.svg)](https://grpc.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A high-performance, event-driven simulation engine for multi-agent systems (MAS), written in Python.*

</div>

## 🧠 Overview

Tsukuyomi is a powerful simulation framework designed to model complex interactions between autonomous agents. It provides a deterministic, tick-based world state that allows for precise control over agent behavior, environment dynamics, and emergent phenomena.

**Key Features (V1.0):**
- **Deterministic Fate Engine:** A central resolution engine ensures consistent and reproducible simulation outcomes at 20 TPS.
- **System 2 Cognitive Core:** Advanced AI agents with deliberate reasoning using LLM abstraction (OpenAI, Anthropic, Groq).
- **Episodic & Semantic Memory:** 3-tier memory system enabling agents to remember past events and build a knowledge graph.
- **Secure gRPC Communication:** Production-ready TLS/SSL encryption and JWT-based authentication for external agents.
- **Extensible Brain:** Built-in support for emotional models (PAD) and relationship dynamics.
- **Spatial Logic:** Multi-room partitioning with portal logic and occlusion.

## 🏗 Architecture

The system is composed of three core components:

1.  **Fate Engine (Core):** The authoritative "Game Master". Manages `WorldState`, resolves action proposals, and advances ticks.
2.  **Agent Brain:** The cognitive engine. Includes Perception, State Management (PAD), Belief Dynamics, and Deliberation (LLM-based).
3.  **Guest SDK:** A Python library allowing external clients to connect securely to the simulation.

## 📦 Installation

### Prerequisites
- Python 3.12+
- `pip`
- `protoc` (for regenerating protocol buffers)

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/nsafouane/tsukuyomi.git
    cd tsukuyomi
    ```

2.  Create and activate virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Configure environment:
    ```bash
    cp .env.example .env
    # Edit .env with your LLM API keys
    ```

## 🚀 Usage

### Running the Server
```bash
python -m tsukuyomi.proto.grpc_server --port 50051
```

### Running the Angry Men Experiment
```bash
python -m experiments.scenarios.angry_man_room
```

### Running Tests
```bash
pytest tests/ -v
```

## 📁 Project Structure

```
tsukuyomi/
├── proto/                 # Protocol Buffer definitions
├── tsukuyomi/
│   ├── brain/            # Cognitive modules (LLMService, MemoryManager, etc.)
│   ├── proto/             # gRPC Server and Client implementation
│   └── guest_sdk.py      # Secure External Client SDK
├── tests/               # Comprehensive test suite
├── experiments/          # Simulation scenarios (Angry Men, Carthage Trial)
└── docs/                 # Detailed documentation
```

## 📄 License
MIT License.

---
*Maintained by Tsukuyomi Team*
