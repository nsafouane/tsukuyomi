"""
Tsukuyomi Environment System

This package contains all environment-related modules including:
- Core engine and resolution logic
- Physics and spatial systems
- Rules and affordances
- Spatial indexing
"""

from tsukuyomi.environment.core.engine import FateEngine, create_proposal, serve
from tsukuyomi.environment.core.resolution import FateResolvers
from tsukuyomi.environment.core.proposal import ProposalWindow, ConflictResolution
from tsukuyomi.environment.core.world_builder import WorldBuilder

__all__ = [
    "FateEngine",
    "create_proposal",
    "serve",
    "FateResolvers",
    "ProposalWindow",
    "ConflictResolution",
    "WorldBuilder",
]
