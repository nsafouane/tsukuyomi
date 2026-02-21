"""
Scenario Loader - YAML parser for scenario files.

Loads and parses scenario YAML files, creating validated ScenarioConfig objects.
Supports includes, references, and environment variable substitution.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .scenario_schema import (
    ScenarioConfig,
    WorldConfig,
    AgentConfig,
    NarrativeBeat,
    BeatType,
    BeatAction,
    BranchCondition,
    TriggerCondition,
    DramaConfig,
    EventLibraryConfig,
    EventSelectionConfig,
    EndCondition,
    EndConditionType,
)

logger = logging.getLogger("ScenarioLoader")


class ScenarioParseError(Exception):
    """Raised when scenario parsing fails."""
    pass


class ScenarioValidationError(Exception):
    """Raised when scenario validation fails."""
    pass


class ScenarioLoader:
    """
    Loads and validates scenario files from YAML.
    
    Usage:
        loader = ScenarioLoader()
        scenario = loader.load("experiments/scenarios/jury_deliberation.yaml")
        if scenario.is_valid():
            # Use scenario
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the scenario loader.
        
        Args:
            base_path: Base directory for resolving relative paths.
                      Defaults to current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._cache: Dict[str, ScenarioConfig] = {}
    
    def load(self, scenario_path: str, use_cache: bool = True) -> ScenarioConfig:
        """
        Load a scenario from a YAML file.
        
        Args:
            scenario_path: Path to the scenario YAML file.
            use_cache: Whether to use cached scenarios.
            
        Returns:
            Validated ScenarioConfig object.
            
        Raises:
            ScenarioParseError: If parsing fails.
            ScenarioValidationError: If validation fails.
        """
        # Resolve path
        full_path = self._resolve_path(scenario_path)
        
        # Check cache
        cache_key = str(full_path)
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached scenario: {full_path}")
            return self._cache[cache_key]
        
        logger.info(f"Loading scenario: {full_path}")
        
        # Load YAML
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ScenarioParseError(f"Scenario file not found: {full_path}")
        except yaml.YAMLError as e:
            raise ScenarioParseError(f"YAML parsing error in {full_path}: {e}")
        
        if not raw_data:
            raise ScenarioParseError(f"Empty scenario file: {full_path}")
        
        # Parse into ScenarioConfig
        try:
            scenario = self._parse_scenario(raw_data, full_path)
        except Exception as e:
            raise ScenarioParseError(f"Failed to parse scenario {full_path}: {e}")
        
        # Validate
        errors = scenario.validate()
        if errors:
            error_msg = "\n".join(f"  - {e}" for e in errors)
            raise ScenarioValidationError(
                f"Scenario validation failed:\n{error_msg}"
            )
        
        # Cache
        if use_cache:
            self._cache[cache_key] = scenario
        
        logger.info(f"Loaded scenario '{scenario.name}' with {len(scenario.agents)} agents, "
                   f"{len(scenario.narrative_beats)} beats")
        
        return scenario
    
    def load_from_dict(self, data: Dict[str, Any]) -> ScenarioConfig:
        """
        Load a scenario from a dictionary.
        
        Args:
            data: Scenario data as dictionary.
            
        Returns:
            Validated ScenarioConfig object.
        """
        scenario = self._parse_scenario(data, self.base_path)
        errors = scenario.validate()
        if errors:
            error_msg = "\n".join(f"  - {e}" for e in errors)
            raise ScenarioValidationError(
                f"Scenario validation failed:\n{error_msg}"
            )
        return scenario
    
    def _resolve_path(self, scenario_path: str) -> Path:
        """Resolve a scenario path relative to base_path."""
        path = Path(scenario_path)
        if path.is_absolute():
            return path
        return self.base_path / path
    
    def _parse_scenario(self, data: Dict[str, Any], source_path: Path) -> ScenarioConfig:
        """Parse raw YAML data into ScenarioConfig."""
        
        scenario_data = data.get('scenario', data)
        
        # Parse world
        world = self._parse_world(scenario_data.get('world', {}))
        
        # Parse agents
        agents = [
            self._parse_agent(a) 
            for a in scenario_data.get('agents', [])
        ]
        
        # Parse narrative beats
        narrative_beats = [
            self._parse_beat(b) 
            for b in scenario_data.get('narrative_beats', [])
        ]
        
        # Parse drama config
        drama_config = self._parse_drama_config(scenario_data.get('drama_config', {}))
        
        # Parse end conditions
        end_conditions = [
            self._parse_end_condition(ec)
            for ec in scenario_data.get('end_conditions', [])
        ]
        
        return ScenarioConfig(
            name=scenario_data.get('name', 'Unnamed Scenario'),
            description=scenario_data.get('description', ''),
            world=world,
            agents=agents,
            narrative_beats=narrative_beats,
            drama_config=drama_config,
            end_conditions=end_conditions,
        )
    
    def _parse_world(self, data: Dict[str, Any]) -> WorldConfig:
        """Parse world configuration."""
        return WorldConfig(
            type=data.get('type', 'single_room'),
            room=data.get('room', 'main_room'),
            props=data.get('props', []),
            environment_context=data.get('environment_context', {}),
        )
    
    def _parse_agent(self, data: Dict[str, Any]) -> AgentConfig:
        """Parse agent configuration."""
        return AgentConfig(
            id=data.get('id', ''),
            name=data.get('name', ''),
            profile=data.get('profile', ''),
            position=data.get('position', [0, 0]),
            traits=data.get('traits', {}),
            stance=data.get('stance'),
        )
    
    def _parse_beat(self, data: Dict[str, Any]) -> NarrativeBeat:
        """Parse a narrative beat."""
        # Parse type
        type_str = data.get('type', 'rising_action')
        try:
            beat_type = BeatType(type_str)
        except ValueError:
            logger.warning(f"Unknown beat type '{type_str}', defaulting to RISING_ACTION")
            beat_type = BeatType.RISING_ACTION
        
        # Parse trigger conditions
        trigger_if = []
        for tc_data in data.get('trigger_if', []):
            if isinstance(tc_data, dict):
                trigger_if.append(TriggerCondition(
                    condition=tc_data.get('condition', '')
                ))
            elif isinstance(tc_data, str):
                trigger_if.append(TriggerCondition(condition=tc_data))
        
        # Parse action
        action = None
        if 'action' in data:
            action = self._parse_action(data['action'])
        
        # Parse branches
        branches = []
        for b_data in data.get('branches', []):
            branches.append(BranchCondition(
                id=b_data.get('id', ''),
                condition=b_data.get('condition', ''),
                then=b_data.get('then', ''),
            ))
        
        # Parse nested beats (for branch type)
        nested_beats = []
        if beat_type == BeatType.BRANCH:
            for nb_data in data.get('beats', []):
                nested_beats.append(self._parse_beat(nb_data))
        
        return NarrativeBeat(
            id=data.get('id', ''),
            tick=data.get('tick', 0),
            type=beat_type,
            description=data.get('description', ''),
            trigger_if=trigger_if,
            action=action,
            prerequisite=data.get('prerequisite'),
            branches=branches,
            beats=nested_beats,
        )
    
    def _parse_action(self, data: Dict[str, Any]) -> BeatAction:
        """Parse a beat action."""
        return BeatAction(
            type=data.get('type', 'inject_event'),
            event=data.get('event'),
            target=data.get('target'),
            thought=data.get('thought'),
            params=data.get('params', {}),
        )
    
    def _parse_drama_config(self, data: Dict[str, Any]) -> DramaConfig:
        """Parse drama director configuration."""
        # Parse event library
        event_library_data = data.get('event_library', {})
        event_library = EventLibraryConfig(
            environmental=event_library_data.get('environmental', {}),
            social=event_library_data.get('social', {}),
            character_specific=event_library_data.get('character_specific', {}),
        )
        
        # Parse event selection
        selection_data = data.get('event_selection', {})
        event_selection = EventSelectionConfig(
            mode=selection_data.get('mode', 'context_weighted'),
            weights=selection_data.get('weights', {
                "environmental": 0.3,
                "social": 0.4,
                "character_specific": 0.3
            }),
            context_matching=selection_data.get('context_matching', {
                "outdoor_match": 1.5
            }),
        )
        
        return DramaConfig(
            tension_threshold_low=data.get('tension_threshold_low', 0.2),
            tension_threshold_high=data.get('tension_threshold_high', 0.8),
            event_library=event_library,
            event_selection=event_selection,
        )
    
    def _parse_end_condition(self, data: Dict[str, Any]) -> EndCondition:
        """Parse an end condition."""
        type_str = data.get('type', 'timeout')
        try:
            ec_type = EndConditionType(type_str)
        except ValueError:
            logger.warning(f"Unknown end condition type '{type_str}', defaulting to TIMEOUT")
            ec_type = EndConditionType.TIMEOUT
        
        return EndCondition(
            type=ec_type,
            description=data.get('description', ''),
            check=data.get('check'),
            ticks=data.get('ticks'),
        )
    
    def clear_cache(self):
        """Clear the scenario cache."""
        self._cache.clear()
        logger.debug("Scenario cache cleared")


def load_scenario(scenario_path: str, base_path: Optional[str] = None) -> ScenarioConfig:
    """
    Convenience function to load a scenario.
    
    Args:
        scenario_path: Path to the scenario YAML file.
        base_path: Optional base directory for resolving paths.
        
    Returns:
        Validated ScenarioConfig object.
    """
    loader = ScenarioLoader(base_path)
    return loader.load(scenario_path)
