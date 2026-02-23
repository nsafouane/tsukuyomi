"""
Tsukuyomi MVP v0.1 - Unified Agent Simulation Engine

A deterministic, high-performance simulation engine where AI agents
coexist, think, remember, and interact in shared social spaces.

Key Features:
- 20 TPS deterministic simulation loop
- Unified agent architecture (standalone + simulation modes)
- RAG-based long-term memory
- Personality-driven decision making
- Social dynamics with gossip propagation

Architecture:
- agents/: Agent System (cognitive, internal, runtime)
- environment/: Environment System (engine, world, physics)
- narrative/: Narrative System (director, events, flow)
- services/: Shared Services (LLM, embedding, vector, database)
- transport/: Communication Layer (gRPC, SDK, proto)
- shared/: Common utilities and exceptions

Usage:
    # Agent System
    from tsukuyomi.agents import BaseAgent, StandaloneAgent
    from tsukuyomi.agents.cognitive import MemorySystem, DeliberationEngine
    
    # Environment System
    from tsukuyomi.environment import FateEngine, WorldBuilder
    
    # Narrative System
    from tsukuyomi.narrative import DramaDirector, EventLibrary
    
    # Services
    from tsukuyomi.services import LLMService, EmbeddingService
    
    # Transport
    from tsukuyomi.transport.grpc import FateEngineClient, GrpcServer

For more information, see README.md and docs/.
"""

__version__ = "0.1.0"
__author__ = "safouane & Tanit"