"""
Scenario Schema - Validation for scenario format.

Provides dataclasses and validation logic for scenario definitions.
Ensures scenario files conform to the expected structure.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import re
import logging

logger = logging.getLogger("ScenarioSchema")


class BeatType(Enum):
    """Types of narrative beats."""
    RISING_ACTION = "rising_action"
    CONFLICT = "conflict"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    BRANCH = "branch"
    CHARACTER_DEVELOPMENT = "character_development"
    INTENSIFICATION = "intensification"


class EndConditionType(Enum):
    """Types of end conditions."""
    CONSENSUS = "consensus"
    TIMEOUT = "timeout"
    HUNG_JURY = "hung_jury"
    CUSTOM = "custom"


@dataclass
class BranchCondition:
    """Defines a branching condition for narrative paths."""
    id: str
    condition: str
    then: str  # Target beat ID
    
    def validate(self) -> List[str]:
        """Validate branch condition. Returns list of errors."""
        errors = []
        if not self.id:
            errors.append("Branch condition missing 'id'")
        if not self.condition:
            errors.append(f"Branch '{self.id}' missing 'condition'")
        if not self.then:
            errors.append(f"Branch '{self.id}' missing 'then' target")
        return errors


@dataclass
class TriggerCondition:
    """A condition that triggers a narrative beat."""
    condition: str
    
    def validate(self) -> List[str]:
        """Validate trigger condition. Returns list of errors."""
        errors = []
        if not self.condition:
            errors.append("Trigger condition is empty")
        # Basic syntax check for condition
        valid_operators = ['>', '<', '>=', '<=', '==', '!=']
        has_operator = any(op in self.condition for op in valid_operators)
        if not has_operator and not any(kw in self.condition.lower() for kw in ['and', 'or', 'not', 'true', 'false']):
            logger.warning(f"Condition may lack valid operator: {self.condition}")
        return errors


@dataclass
class BeatAction:
    """An action to take when a beat triggers."""
    type: str
    event: Optional[str] = None
    target: Optional[str] = None
    thought: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate beat action. Returns list of errors."""
        errors = []
        valid_types = ['inject_event', 'inject_thought', 'inject_dialogue', 'modify_state', 'trigger_catalyst']
        if self.type not in valid_types:
            errors.append(f"Unknown action type: {self.type}. Valid: {valid_types}")
        
        if self.type == 'inject_thought' and not self.target:
            errors.append("inject_thought action requires 'target'")
        if self.type == 'inject_thought' and not self.thought:
            errors.append("inject_thought action requires 'thought'")
        return errors


@dataclass
class NarrativeBeat:
    """A single narrative beat in the scenario."""
    id: str
    tick: int
    type: BeatType
    description: str
    trigger_if: List[TriggerCondition] = field(default_factory=list)
    action: Optional[BeatAction] = None
    prerequisite: Optional[str] = None
    branches: List[BranchCondition] = field(default_factory=list)
    beats: List['NarrativeBeat'] = field(default_factory=list)  # For branch beats
    
    def validate(self, all_beat_ids: Set[str]) -> List[str]:
        """Validate narrative beat. Returns list of errors."""
        errors = []
        
        if not self.id:
            errors.append("Beat missing 'id'")
        
        if self.tick < 0:
            errors.append(f"Beat '{self.id}' has negative tick: {self.tick}")
        
        if not isinstance(self.type, BeatType):
            errors.append(f"Beat '{self.id}' has invalid type: {self.type}")
        
        if not self.description:
            errors.append(f"Beat '{self.id}' missing description")
        
        # Validate trigger conditions
        for tc in self.trigger_if:
            errors.extend(tc.validate())
        
        # Validate action
        if self.action:
            errors.extend(self.action.validate())
        
        # Validate prerequisite
        if self.prerequisite and self.prerequisite not in all_beat_ids:
            errors.append(f"Beat '{self.id}' prerequisite '{self.prerequisite}' not found")
        
        # Validate branches
        for branch in self.branches:
            branch_errors = branch.validate()
            errors.extend(branch_errors)
            if branch.then not in all_beat_ids:
                errors.append(f"Beat '{self.id}' branch target '{branch.then}' not found")
        
        # Validate nested beats (for branch type)
        if self.type == BeatType.BRANCH:
            for nested in self.beats:
                errors.extend(nested.validate(all_beat_ids))
        
        return errors


@dataclass
class AgentConfig:
    """Configuration for a single agent in the scenario."""
    id: str
    name: str
    profile: str  # Path to profile YAML
    position: List[int] = field(default_factory=lambda: [0, 0])
    traits: Dict[str, float] = field(default_factory=dict)
    stance: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validate agent config. Returns list of errors."""
        errors = []
        
        if not self.id:
            errors.append("Agent missing 'id'")
        if not self.name:
            errors.append(f"Agent '{self.id}' missing 'name'")
        if not self.profile:
            errors.append(f"Agent '{self.id}' missing 'profile' path")
        
        # Validate position
        if len(self.position) != 2:
            errors.append(f"Agent '{self.id}' position must be [x, y], got: {self.position}")
        
        # Validate traits range
        for trait, value in self.traits.items():
            if not -1.0 <= value <= 1.0:
                errors.append(f"Agent '{self.id}' trait '{trait}' out of range [-1, 1]: {value}")
        
        return errors


@dataclass
class WorldConfig:
    """Configuration for the world/scene."""
    type: str = "single_room"
    room: str = "main_room"
    props: List[str] = field(default_factory=list)
    environment_context: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate world config. Returns list of errors."""
        errors = []
        
        valid_world_types = ['single_room', 'multi_room', 'open_world']
        if self.type not in valid_world_types:
            errors.append(f"Unknown world type: {self.type}. Valid: {valid_world_types}")
        
        if not self.room:
            errors.append("World config missing 'room'")
        
        return errors


@dataclass
class EventLibraryConfig:
    """Configuration for the event library."""
    environmental: Dict[str, List[str]] = field(default_factory=dict)
    social: Dict[str, List[str]] = field(default_factory=dict)
    character_specific: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate event library config. Returns list of errors."""
        errors = []
        
        # Environmental events should have category pools
        if not self.environmental:
            logger.warning("No environmental events defined")
        
        # Social events should have category pools
        if not self.social:
            logger.warning("No social events defined")
        
        # Validate character_specific triggers have condition and events
        for trigger_name, trigger_config in self.character_specific.items():
            if 'condition' not in trigger_config:
                errors.append(f"Character trigger '{trigger_name}' missing 'condition'")
            if 'events' not in trigger_config:
                errors.append(f"Character trigger '{trigger_name}' missing 'events' list")
            elif not isinstance(trigger_config['events'], list):
                errors.append(f"Character trigger '{trigger_name}' events must be a list")
        
        return errors


@dataclass
class EventSelectionConfig:
    """Configuration for event selection logic."""
    mode: str = "context_weighted"
    weights: Dict[str, float] = field(default_factory=lambda: {
        "environmental": 0.3,
        "social": 0.4,
        "character_specific": 0.3
    })
    context_matching: Dict[str, float] = field(default_factory=lambda: {
        "outdoor_match": 1.5
    })
    
    def validate(self) -> List[str]:
        """Validate event selection config. Returns list of errors."""
        errors = []
        
        valid_modes = ['random', 'context_weighted', 'state_machine']
        if self.mode not in valid_modes:
            errors.append(f"Unknown event selection mode: {self.mode}. Valid: {valid_modes}")
        
        # Weights should be non-negative
        for category, weight in self.weights.items():
            if weight < 0:
                errors.append(f"Weight for '{category}' cannot be negative: {weight}")
        
        # Weights should sum to approximately 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.1:
            logger.warning(f"Event weights sum to {total_weight}, not 1.0")
        
        return errors


@dataclass
class DramaConfig:
    """Configuration for the Drama Director."""
    tension_threshold_low: float = 0.2
    tension_threshold_high: float = 0.8
    event_library: EventLibraryConfig = field(default_factory=EventLibraryConfig)
    event_selection: EventSelectionConfig = field(default_factory=EventSelectionConfig)
    
    def validate(self) -> List[str]:
        """Validate drama config. Returns list of errors."""
        errors = []
        
        if not 0.0 <= self.tension_threshold_low <= 1.0:
            errors.append(f"tension_threshold_low out of range: {self.tension_threshold_low}")
        
        if not 0.0 <= self.tension_threshold_high <= 1.0:
            errors.append(f"tension_threshold_high out of range: {self.tension_threshold_high}")
        
        if self.tension_threshold_low >= self.tension_threshold_high:
            errors.append("tension_threshold_low must be less than tension_threshold_high")
        
        errors.extend(self.event_library.validate())
        errors.extend(self.event_selection.validate())
        
        return errors


@dataclass
class EndCondition:
    """Defines an end condition for the scenario."""
    type: EndConditionType
    description: str = ""
    check: Optional[str] = None
    ticks: Optional[int] = None
    
    def validate(self) -> List[str]:
        """Validate end condition. Returns list of errors."""
        errors = []
        
        if not isinstance(self.type, EndConditionType):
            errors.append(f"Invalid end condition type: {self.type}")
        
        if self.type == EndConditionType.TIMEOUT and self.ticks is None:
            errors.append("Timeout end condition requires 'ticks'")
        
        if self.type == EndConditionType.CONSENSUS and not self.check:
            errors.append("Consensus end condition requires 'check' expression")
        
        return errors


@dataclass
class ScenarioConfig:
    """Complete scenario configuration."""
    name: str
    description: str
    world: WorldConfig
    agents: List[AgentConfig]
    narrative_beats: List[NarrativeBeat]
    drama_config: DramaConfig = field(default_factory=DramaConfig)
    end_conditions: List[EndCondition] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate complete scenario. Returns list of errors."""
        errors = []
        
        # Basic validation
        if not self.name:
            errors.append("Scenario missing 'name'")
        if not self.description:
            errors.append("Scenario missing 'description'")
        
        # Validate world
        errors.extend(self.world.validate())
        
        # Validate agents
        if not self.agents:
            errors.append("Scenario has no agents defined")
        agent_ids = set()
        for agent in self.agents:
            errors.extend(agent.validate())
            if agent.id in agent_ids:
                errors.append(f"Duplicate agent id: {agent.id}")
            agent_ids.add(agent.id)
        
        # Validate narrative beats
        beat_ids = {beat.id for beat in self.narrative_beats}
        # Also collect nested beat IDs
        for beat in self.narrative_beats:
            if beat.type == BeatType.BRANCH:
                for nested in beat.beats:
                    beat_ids.add(nested.id)
        
        for beat in self.narrative_beats:
            errors.extend(beat.validate(beat_ids))
        
        # Check for duplicate beat IDs
        if len(beat_ids) != len(self.narrative_beats):
            seen = set()
            for beat in self.narrative_beats:
                if beat.id in seen:
                    errors.append(f"Duplicate beat id: {beat.id}")
                seen.add(beat.id)
        
        # Validate drama config
        errors.extend(self.drama_config.validate())
        
        # Validate end conditions
        if not self.end_conditions:
            errors.append("Scenario has no end conditions defined")
        for ec in self.end_conditions:
            errors.extend(ec.validate())
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if scenario is valid."""
        return len(self.validate()) == 0
    
    def get_beat_by_id(self, beat_id: str) -> Optional[NarrativeBeat]:
        """Find a beat by its ID, including nested beats."""
        for beat in self.narrative_beats:
            if beat.id == beat_id:
                return beat
            if beat.type == BeatType.BRANCH:
                for nested in beat.beats:
                    if nested.id == beat_id:
                        return nested
        return None
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Find an agent by its ID."""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None
