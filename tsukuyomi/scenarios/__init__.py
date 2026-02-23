"""
Scenario Module - Scenario loading and validation for Tsukuyomi.

Provides tools for defining and loading narrative scenarios.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
Updated: February 22, 2026 (Moved to top-level scenarios module)
"""

from .schema import (
    # Enums
    BeatType,
    EndConditionType,
    # Dataclasses
    BranchCondition,
    TriggerCondition,
    BeatAction,
    NarrativeBeat,
    AgentConfig,
    WorldConfig,
    EventLibraryConfig,
    EventSelectionConfig,
    DramaConfig,
    EndCondition,
    ScenarioConfig,
)
from .loader import (
    ScenarioLoader,
    ScenarioParseError,
    ScenarioValidationError,
    load_scenario,
)

__all__ = [
    # Enums
    "BeatType",
    "EndConditionType",
    # Dataclasses
    "BranchCondition",
    "TriggerCondition",
    "BeatAction",
    "NarrativeBeat",
    "AgentConfig",
    "WorldConfig",
    "EventLibraryConfig",
    "EventSelectionConfig",
    "DramaConfig",
    "EndCondition",
    "ScenarioConfig",
    # Loader
    "ScenarioLoader",
    "ScenarioParseError",
    "ScenarioValidationError",
    "load_scenario",
]
