# 🛠️ Coding Standards & Maintainability

This document outlines the coding standards, file structure, and contribution guidelines for the **Tsukuyomi** project to ensure long-term maintainability and scalability.

## 📏� Core Principles
1.  **Readability First:** Code is written once and modified by many. Keep it clear and concise.
2.  **Modularity:** Classes and functions should be small, single-responsibility entities.
3.  **Determinism:** The simulation engine is deterministic. Avoid randomness unless explicitly seeded.
4.  **Type Hints:** Use modern Python type hinting (`Optional`, `List`, `Dict`) for better IDE support.

---

## 📂 File Structure Conventions

### Directory Layout
```text
tsukuyomi/
├── brain/              # Agent cognition & decision-making
│   ├── AgentBrain.py
│   ├── StateManager.py
│   └── PerceptionPipeline.py
├── proto/              # gRPC & Protobuf definitions
│   ├── grpc_server.py
│   └── fate_engine.py
├── experiments/        # Simulations and scenarios
├── tests/               # Unit & Integration tests
└── tsukuyomi/        # Package initialization
```

### File Naming
- **Python Files:** `snake_case.py`
- **Protobuf Files:** `PascalCase.proto`
- **Classes:** `PascalCase` (e.g., `AgentBrain`, `FateEngine`)

---

## ✍ Code Style Guidelines

### 1. Imports
Always use **absolute imports** from the `tsukuyomi` package root.

```python
# ✅ CORRECT
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto import core_pb2

# ❌ INCORRECT (Relative imports are discouraged)
from .brain.AgentBrain import AgentBrain
from .proto.core_pb2 import core_pb2
```

### 2. Line Length & Complexity
To maintain scalability and readability:
- **Max Line Length:** 700 characters.
- **Max Function Length:** 50 lines.
- **Cyclomatic Complexity:** Keep it low. If a function needs `if` > 3 deep, consider refactoring into a separate method.

### 3. Docstrings
All public classes and methods must have a **Google-style docstring**.

```python
def resolve_action(self, proposal: Proposal) -> Resolution:
    """
    Resolve a conflict between two agents.

    Args:
        proposal: The action proposal to resolve.

    Returns:
        Resolution: The outcome of the resolution.
    """
    pass
```

### 4. Logging
Use the standard `logging` module. Do not use `print()` statements in library code.

```python
# ✅ CORRECT
import logging
logger = logging.getLogger(__name__)
logger.info("Agent disconnected.")

# ❌ INCORRECT
print("Agent disconnected.")
```

---

## 🧪 Testing Guidelines

### Coverage Requirements
- **Target:** Maintain > 80% unit test coverage.
- **Placement:** All tests must reside in the `tsukuyomi/tests/` directory.

### Test Structure
Tests should be organized by the module they cover.

- `tests/test_brain/` -> `AgentBrain`, `StateManager`
- `tests/test_proto/` -> `FateEngine`, gRPC communication
- `tests/test_experiments/` -> Scenario integrity

### Naming Tests
Test files should clearly indicate what they are testing:
- `test_statemanager.py`
- `test_action_resolution.py`
- `test_memory_consistency.py`

---

## 🤝 Contributing

### Workflow
1.  Fork the repository.
2.  Create a feature branch from `master`.
3.  Write code adhering to these standards.
4.  Update/extend documentation.
5.  Ensure all tests pass locally.
6.  Submit a Pull Request to `master`.

### Pre-commit Checks
Ensure your code passes:
- `pytest tsukuyomi/`
- `pylint tsukuyomi/` (checking for style)

### Commit Messages
Use clear, descriptive commit messages:
- `feat(agent): add advanced memory recall logic`
- `fix(proto): resolve race condition in gRPC stream`
- `docs: update roadmap for v1.2`

---
*Last Updated: Feb 10, 2026*
