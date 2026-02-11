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

**Key Features:**
- **Event-Driven Architecture:** Agents perceive, decide, and act based on scheduled event ticks.
- **Deterministic Fate Engine:** A central resolution engine ensures consistent and reproducible simulation outcomes.
- **gRPC Communication:** High-performance, language-agnostic protocol for external agent integrations.
- **Protobuf State:** Efficient binary serialization for world state and action proposals.
- **Extensible Brain:** Built-in support for personality models (PAD, Big Five) and emotional state tracking.
- **Spatial Logic:** Supports multi-room environments and location-based interactions.
- **Guest SDK:** Python library allowing external clients (AI models, human players, or other systems) to connect to Fate Engine and participate in the simulation.

## 🏗 Architecture

The system is composed of three core components:

1.  **Fate Engine (Core):** The "Game Master" of the simulation. It manages the `WorldState`, accepts action proposals from agents, resolves conflicts, and advances the simulation tick.
2.  **Agent Brain:** The internal logic of an agent. It processes sensory data, consults memory and personality profiles, and generates action proposals.
3.  **Guest SDK:** A Python library allowing external clients (AI models, human players, or other systems) to connect to the Fate Engine and participate in the simulation.

### Data Flow

1.  **Tick Start:** Fate Engine broadcasts current `WorldState` to all connected agents.
2.  **Perception:** Agents process the `WorldState` through their `PerceptionPipeline`, generating a filtered list of relevant events.
3.  **Decision:** The `AgentBrain` evaluates the percept, updates internal emotional state (`StateManager`), and selects an action.
4.  **Action:** The agent submits a `Proposal` to the Fate Engine.
5.  **Resolution:** The Fate Engine collects all proposals, resolves them (handling conflicts), applies changes, and generates `Resolutions`.

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package installer)
- `protoc` (Protobuf compiler, often included with `grpcio-tools`)

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/nsafouane/tsukuyomi.git
    cd tsukuyomi
    ```

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

### Running the Fate Engine
The simplest way to run a simulation is using the provided examples or scripts in `experiments/`.

```bash
# Run the Angry Man Room scenario
python -m experiments.scenarios.angry_man_room
```

### Using the Guest SDK
You can build your own agent using the `GuestAgent` SDK.

```python
import asyncio
from tsukuyomi.guest_sdk import GuestAgent

async def main():
    # 1. Initialize your agent
    agent = GuestAgent(
        agent_id="my-agent-01", 
        agent_name="My AI Agent"
    )

    # 2. Connect to the simulation server
    # Note: Ensure the server is running and you have the correct address/token
    connected = await agent.connect(access_token="YOUR_SECRET_TOKEN")
    if not connected:
        print("Connection failed!")
        return

    # 3. Submit an action
    # e.g., Move to the tavern
    success = await agent.submit_proposal(
        action="MOVE", 
        params={"destination": "tavern"}
    )
    
    # 4. Listen for updates (stream)
    async for tick_state in agent.stream_updates():
        print(f"Tick {tick_state.tick_number}: Processing new state...")
        # ... your agent's logic ...
        
if __name__ == "__main__":
    asyncio.run(main())
```

### Running Tests
Tsukuyomi includes a comprehensive test suite. Run it using `pytest`:

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
tsukuyomi/
├── proto/                 # Protocol Buffer definitions (.proto)
│   ├── core.proto         # Core state and enums
│   ├── guest_api.proto    # gRPC service definitions
│   └── fate_engine.proto  # Internal engine types
├── tsukuyomi/
│   ├── brain/            # Agent logic (Brain, StateManager, Perception)
│   ├── proto/             # Generated Python protobuf classes
│   └── guest_sdk.py      # External client SDK
├── tests/               # Unit and integration tests
├── experiments/          # Simulation scenarios and examples
│   ├── scenarios/        # Pre-built scenarios (e.g., Angry Man Room)
│   └── profiles/         # Character profiles and configurations
└── README.md
```

## 🤝 Contributing

We welcome contributions, especially in:
- New agent behaviors and brain modules.
- Performance optimizations.
- Additional scenarios and profiles.
- Bug fixes and test coverage improvements.

1.  Fork the project.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📮 Citation

If you use Tsukuyomi in your research, please cite it:

```bibtex
@software{tsukuyomi,
  title={Tsukuyomi: Multi-Agent Simulation Engine},
  author={Safouane},
  year={2026},
  url={https://github.com/nsafouane/tsukuyomi}
}
```

---
*Maintained by Tsukuyomi*
