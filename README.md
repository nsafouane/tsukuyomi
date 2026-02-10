# Tsukuyomi Engine

**The Generative Simulation Engine for Living Agents.**

Tsukuyomi is a high-performance, deterministic simulation engine designed to power complex social worlds where AI agents coexist, deliberate, remember, and interact. It bridges the gap between static chatbots and emergent virtual societies by enforcing formal logic, physics, and causal history upon generative agent behaviors.

## 🌟 Core Features

- **Deterministic Fate Engine:** A 20 TPS (Ticks Per Second) authoritative loop ensuring exact state replication and replayability.
- **Cognitive Architecture:**
  - **Sensory Pipeline:** Realistic vision (FOV), hearing, and proprioception with occlusion.
  - **Emotional State:** PAD (Pleasure-Arousal-Dominance) modeling with inertia and personality baselines.
  - **Memory Systems:** Miller’s Law working memory, episodic retrieval, and semantic knowledge graphs.
  - **Belief Dynamics:** Evidence-based stance tracking with confirmation bias.
- **Social Simulation:**
  - **Gossip Protocol:** Organic information propagation via proximity and overhearing.
  - **Relationship Manager:** Dynamic affinity, reputation, and social history tracking.
  - **Drama Director:** Automated narrative tension monitoring and catalyst injection.
- **Spatial Logic:** Multi-room partitioning, portals, and dynamic collision/occlusion.
- **External Interfaces:** gRPC-based Guest Protocol for external agent integration.

## 📚 Documentation

Detailed architecture and design documents are available in the `docs/` directory:

- [**System Overview**](docs/architecture/overview.md): High-level architecture, data flow, and consistency models.
- [**Deep Dive**](docs/architecture/deep_dive.md): In-depth look at the Cognitive Core and Fate Engine internals.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `pip` and `virtualenv`

### Installation

```bash
git clone https://github.com/yourusername/tsukuyomi.git
cd tsukuyomi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running a Scenario

Tsukuyomi comes with pre-built scenarios to demonstrate engine capabilities.

```bash
# Run the Roman-Carthage Legal Trial simulation
python3 -m tsukuyomi.experiments.scenarios.roman_carthage_trial
```

### Running Tests

```bash
pytest tests/
```

## 📁 Repository Structure

```text
tsukuyomi/
├── tsukuyomi/
│   ├── brain/          # Agent Cognitive Stack (Memory, Emotion, Beliefs)
│   ├── proto/          # Fate Engine, Physics, and gRPC Schemas
│   └── integrations/   # External API adaptors
├── experiments/        # Scenarios, Profiles, and Simulation Logs
├── tests/              # Unit and Integration Test Suites
└── docs/               # Architecture and Usage Documentation
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contribution Guidelines](CONTRIBUTING.md) before submitting a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built with ❤️ by the Tsukuyomi Team.*
