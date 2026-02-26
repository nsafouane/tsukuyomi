# Server Entry Point

**Path:** `server.py`

**Last Updated:** 2026-02-26

---

## Overview

The `server.py` file serves as the main high-level entry point for the Tsukuyomi MVP v0.1 platform. It orchestrates the initialization and lifecycle of the core systems: Agent, Environment, and Narrative.

While the `transport/grpc/server.py` provides a gRPC interface for distributed simulations, `server.py` acts as a unified platform controller suitable for local execution, orchestration, and simplified runners.

## Design Philosophy

- **Centralized Orchestration**: Single class (`TsukuyomiServer`) to manage system lifecycles.
- **Lazy Loading**: Imports core engines only when needed to avoid circular dependencies and heavy startup costs.
- **Unified Logging**: Uses shared configuration for consistent logging across all systems.
- **Graceful Lifecycle**: Proper `start()` and `stop()` methods for clean resource management.

---

## Component: TsukuyomiServer

The `TsukuyomiServer` class is the primary orchestrator.

### Initialization

```python
server = TsukuyomiServer()
```

- Loads system configuration via `get_config()`.
- Prepares internal state for engine references.

### Methods

| Method | Description |
|--------|-------------|
| `start()` | Initializes the LLM Service, Environment Engine (`FateEngine`), and Narrative Director (`DramaDirector`). |
| `stop()` | Gracefully cleans up all systems in reverse order of initialization. |
| `run_tick()` | Executes a single simulation tick through the Environment Engine. |

### Startup Sequence

1. **LLM Service**: Initializes the bridge to external providers (Groq/OpenAI).
2. **Environment Engine**: Starts the authoritative world simulation (`FateEngine`).
3. **Narrative Director**: Attaches the `DramaDirector` to the engine for narrative orchestration.

---

## Usage

### Direct Execution

To run a basic server instance and execute a test tick:

```bash
python server.py
```

### Programmatic Usage

The server can be integrated into other applications (e.g., a GUI or a batch processor):

```python
from server import TsukuyomiServer
import asyncio

async def run():
    server = TsukuyomiServer()
    await server.start()
    
    # Run simulation for 1000 ticks
    for _ in range(1000):
        await server.run_tick()
        
    await server.stop()

asyncio.run(run())
```

---

## Error Handling

The server utilizes the `TsukuyomiError` hierarchy from `shared.exceptions` to provide structured error feedback during startup or runtime failures.

- **Startup Failures**: Catches and logs initialization errors for LLM, Environment, or Narrative systems.
- **Runtime Errors**: Provides safety checks to ensure the server is running before attempting to process ticks.

---

## Related Files

- `tsukuyomi/environment/core/engine.py`: The underlying `FateEngine`.
- `tsukuyomi/narrative/core/director.py`: The underlying `DramaDirector`.
- `tsukuyomi/transport/grpc/server.py`: The gRPC server implementation for networked simulations.
