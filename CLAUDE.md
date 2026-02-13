# CLAUDE.md for Tsukuyomi

This file provides information on common tasks, project structure, and architectural patterns for the Tsukuyomi project.

## Project Overview
Tsukuyomi is a high-performance, event-driven multi-agent simulation engine. It features a deterministic "Fate Engine", secure gRPC-based communication (TLS/JWT), and a complex cognitive brain for agents.

## Common Commands

### Build & Setup
- **Install dependencies**: `pip install -r requirements.txt`
- **Protobuf compilation**: `python -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. proto/*.proto`
- **Environment**: `cp .env.example .env` (Requires `LLM_API_KEY`)

### Testing
- **Run all tests**: `pytest`
- **Run specific test file**: `pytest tests/test_fate_engine.py`
- **Run with verbose output**: `pytest -v`

### Running Simulations
- **Run server**: `python -m tsukuyomi.proto.grpc_server`
- **Run Angry Men experiment**: `python -m experiments.scenarios.angry_man_room`
- **Run Carthage Trial experiment**: `python -m experiments.run_trial`

## Project Structure
- `tsukuyomi/`: Core library code.
    - `brain/`: Agent cognitive logic (LLMService, Memory, Perception, PAD Emotions).
    - `proto/`: gRPC server/client and generated protobuf code.
    - `guest_sdk.py`: Secure SDK for external agent integration.
- `tests/`: Comprehensive test suite (48+ tests, 100% pass target).
- `experiments/`: Scenarios, character profiles, and simulation scripts.
- `proto/`: Raw `.proto` definition files.

## Architectural Patterns
- **Fate Engine (Core)**: 20 TPS deterministic authority loop (Broadcast → Window → Resolution).
- **System 2 Intelligence**: Non-blocking LLM deliberation with provider abstraction (OpenAI, Anthropic, Groq).
- **Security**: 
    - **TLS/SSL**: All gRPC traffic is encrypted using RSA-4096 certs.
    - **JWT Auth**: Agents must authenticate via JWT session tokens.
- **Cognitive Core**: 
    - **PAD Model**: Emotional tracking (Pleasure, Arousal, Dominance).
    - **Memory**: 3-tier system (Working, Episodic, Semantic Knowledge Graph).
- **Event-Driven**: Asynchronous gRPC streaming for real-time updates.

## Code Style & Standards
- **Python**: 3.12+
- **Testing**: `pytest` with `pytest-asyncio`.
- **Security**: No hardcoded secrets; use `.env` and `InputSanitizer`.
