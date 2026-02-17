"""
Scenarios Module
==============

Pre-built scenarios for simulation:
- Jury Deliberation: 12 Angry Men-style deliberations
- (More to come: Combat, Social, Negotiation)
"""

from .base import Scenario, ScenarioConfig
from .jury import (
    JuryConfig,
    JurorAgent,
    Vote,
    JuryDeliberationScenario,
    create_jury_scenario
)

__all__ = [
    # Base
    "Scenario",
    "ScenarioConfig",
    
    # Jury
    "JuryConfig",
    "JurorAgent",
    "Vote",
    "JuryDeliberationScenario",
    "create_jury_scenario"
]