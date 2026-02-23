"""
Shared utilities and common code for Tsukuyomi.

This module contains configuration, logging, exceptions, and utility functions
used across all Tsukuyomi systems (agents, environment, narrative).
"""

from tsukuyomi.shared.config import configure_logging, get_config
from tsukuyomi.shared.exceptions import (
    TsukuyomiError,
    AgentError,
    EnvironmentError,
    NarrativeError,
    ServiceError,
    ValidationError,
)
from tsukuyomi.shared.utils import generate_id, to_pb_timestamp, from_pb_timestamp

__all__ = [
    # Configuration
    "configure_logging",
    "get_config",
    # Exceptions
    "TsukuyomiError",
    "AgentError",
    "EnvironmentError",
    "NarrativeError",
    "ServiceError",
    "ValidationError",
    # Utilities
    "generate_id",
    "to_pb_timestamp",
    "from_pb_timestamp",
]
