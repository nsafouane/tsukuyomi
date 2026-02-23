"""
Environment Core Module

Contains the core engine and resolution logic.
"""

from tsukuyomi.environment.core.engine import (
    EnvironmentEngine,
    FateEngine,  # Backward compatibility alias
    create_proposal,
    serve
)
from tsukuyomi.environment.core.resolution import FateResolvers
from tsukuyomi.environment.core.proposal import ProposalWindow, ConflictResolution
from tsukuyomi.environment.core.world_builder import WorldBuilder

__all__ = [
    "EnvironmentEngine",
    "FateEngine",  # Backward compatibility
    "create_proposal",
    "serve",
    "FateResolvers",
    "ProposalWindow",
    "ConflictResolution",
    "WorldBuilder",
]
