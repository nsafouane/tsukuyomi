"""
Event Library - Context-matched event selection for narrative injection.

Provides a library of events categorized by type and context, with intelligent
selection based on current world state, tension levels, and agent states.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

import logging
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("EventLibrary")


class EventCategory(Enum):
    """Categories of events."""
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    CHARACTER_SPECIFIC = "character_specific"
    NARRATIVE = "narrative"


@dataclass
class Event:
    """A narrative event that can be injected into the simulation."""
    id: str
    category: EventCategory
    description: str
    context_tags: List[str] = field(default_factory=list)
    target_agent: Optional[str] = None
    broadcast: bool = True
    params: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.target_agent:
            return f"[{self.category.value}] {self.description} (target: {self.target_agent})"
        return f"[{self.category.value}] {self.description}"


@dataclass
class CharacterTrigger:
    """A trigger condition for character-specific events."""
    trigger_id: str
    condition: str
    events: List[str]
    priority: float = 1.0
    
    def matches(self, agent_state: Dict[str, Any], tension: float, agent_id: Optional[str] = None) -> bool:
        """
        Check if this trigger matches the current state.
        
        Args:
            agent_state: Current agent state dictionary.
            tension: Current tension level.
            agent_id: Optional agent ID for prefix stripping in conditions.
            
        Returns:
            True if condition matches.
        """
        return self._evaluate_condition(self.condition, agent_state, tension, agent_id)
    
    def _evaluate_condition(
        self, 
        condition: str, 
        agent_state: Dict[str, Any], 
        tension: float,
        agent_id: Optional[str] = None
    ) -> bool:
        """Evaluate a condition string against agent state."""
        
        # Simple condition parser
        # Supports: "attr > value", "attr >= value", "attr < value", etc.
        # Also supports AND: "cond1 AND cond2"
        
        if " AND " in condition:
            parts = condition.split(" AND ")
            return all(self._evaluate_condition(p.strip(), agent_state, tension, agent_id) for p in parts)
        
        if " OR " in condition:
            parts = condition.split(" OR ")
            return any(self._evaluate_condition(p.strip(), agent_state, tension, agent_id) for p in parts)
        
        # Parse single condition - support negative values
        match = re.match(r"(\w+(?:\.\w+)?)\s*([><=!]+)\s*(-?[\d.]+)", condition)
        if not match:
            logger.warning(f"Could not parse condition: {condition}")
            return False
        
        attr_path, operator, value_str = match.groups()
        value = float(value_str)
        
        # Handle agent_id prefix in condition
        # If condition is "juror_3.agreeableness > 0.5" and we're checking juror_3's state
        # strip the prefix. If we're checking a different agent's state, this trigger
        # doesn't apply.
        if "." in attr_path:
            parts = attr_path.split(".", 1)
            condition_agent_id = parts[0]
            actual_attr = parts[1]
            
            if agent_id and condition_agent_id == agent_id:
                # Condition references this agent, use the actual attribute
                attr_path = actual_attr
            elif agent_id and condition_agent_id != agent_id:
                # Condition references a different agent, skip this trigger
                return False
            # If no agent_id provided, keep the full path
        
        # Get attribute value
        attr_value = self._get_nested_attr(agent_state, attr_path)
        if attr_value is None:
            # Check if it's a tension reference
            if attr_path == "tension":
                attr_value = tension
            else:
                logger.debug(f"Attribute not found: {attr_path}")
                return False
        
        # Evaluate
        if operator == ">":
            return attr_value > value
        elif operator == ">=":
            return attr_value >= value
        elif operator == "<":
            return attr_value < value
        elif operator == "<=":
            return attr_value <= value
        elif operator == "==" or operator == "=":
            return abs(attr_value - value) < 0.01  # Float comparison
        elif operator == "!=":
            return abs(attr_value - value) >= 0.01
        
        return False
    
    def _get_nested_attr(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        """Get a nested attribute value using dot notation."""
        parts = path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value


class EventLibrary:
    """
    Library of narrative events with context-aware selection.
    
    The library maintains categorized event pools and provides methods
    for selecting events based on current context, tension, and agent states.
    """
    
    def __init__(self):
        """Initialize the event library with default pools."""
        
        # Event pools by category and context
        self._environmental_events: Dict[str, List[str]] = {}
        self._social_events: Dict[str, List[str]] = {}
        self._narrative_events: Dict[str, List[str]] = {}
        
        # Character-specific triggers
        self._character_triggers: Dict[str, CharacterTrigger] = {}
        
        # Selection configuration
        self._selection_mode: str = "context_weighted"
        self._category_weights: Dict[str, float] = {
            "environmental": 0.3,
            "social": 0.4,
            "character_specific": 0.3,
        }
        self._context_match_weights: Dict[str, float] = {}
        
        # Initialize with defaults
        self._init_default_events()
    
    def _init_default_events(self):
        """Initialize with default event pools."""
        
        # Environmental events - outdoor stormy
        self._environmental_events["outdoor_stormy"] = [
            "Loud thunder rumbles outside",
            "Lightning flashes through the window",
            "Rain pounds heavily on the roof",
            "The wind howls outside",
            "A branch crashes down outside",
            "Dark clouds gather ominously",
        ]
        
        # Environmental events - outdoor clear
        self._environmental_events["outdoor_clear"] = [
            "A gentle breeze blows through",
            "Sunlight streams through the window",
            "Birds can be heard chirping outside",
            "The weather is pleasant",
        ]
        
        # Environmental events - indoor generic
        self._environmental_events["indoor_generic"] = [
            "The lights flicker briefly",
            "The air conditioning hums",
            "A draft moves through the room",
            "Someone knocks on the door",
            "A phone buzzes in the distance",
        ]
        
        # Environmental events - indoor tense
        self._environmental_events["indoor_tense"] = [
            "The AC suddenly breaks, the room gets hot",
            "Lights flicker and dim momentarily",
            "A pipe bursts in the corner",
            "The ceiling starts to leak",
            "The door slams shut from a draft",
        ]
        
        # Social events - neutral
        self._social_events["neutral"] = [
            "The foreman reminds everyone of the time",
            "A note is passed to the foreman",
            "Someone clears their throat",
            "The clock ticks loudly in the silence",
            "Paper shuffles across the table",
        ]
        
        # Social events - conflict
        self._social_events["conflict"] = [
            "Two jurors nearly come to blows",
            "Someone storms to the corner",
            "A juror slams their hand on the table",
            "Tension rises as voices get louder",
            "An argument nearly turns physical",
        ]
        
        # Social events - cooperative
        self._social_events["cooperative"] = [
            "Someone suggests a compromise",
            "Jurors begin to find common ground",
            "A thoughtful silence settles over the room",
            "Someone offers to summarize the points",
            "Nods of agreement spread around the table",
        ]
        
        # Character-specific triggers
        self._character_triggers["anger_spike"] = CharacterTrigger(
            trigger_id="anger_spike",
            condition="neuroticism > 0.5 AND tension > 0.6",
            events=[
                "{agent_name} begins pacing angrily",
                "{agent_name}'s face turns red with anger",
                "{agent_name} slams their fist on the table",
                "{agent_name} shouts in frustration",
            ],
            priority=1.5,
        )
        
        self._character_triggers["introvert_discomfort"] = CharacterTrigger(
            trigger_id="introvert_discomfort",
            condition="extraversion < -0.3 AND heat_level > 0.5",
            events=[
                "{agent_name} retreats to the corner",
                "{agent_name} looks increasingly uncomfortable",
                "{agent_name} becomes withdrawn",
            ],
            priority=1.0,
        )
        
        self._character_triggers["calm_under_pressure"] = CharacterTrigger(
            trigger_id="calm_under_pressure",
            condition="neuroticism < 0.3 AND tension > 0.7",
            events=[
                "{agent_name} remains remarkably calm",
                "{agent_name} speaks with measured tones",
                "{agent_name} tries to de-escalate",
            ],
            priority=0.8,
        )
    
    def configure(
        self,
        environmental: Optional[Dict[str, List[str]]] = None,
        social: Optional[Dict[str, List[str]]] = None,
        character_specific: Optional[Dict[str, Dict[str, Any]]] = None,
        selection_mode: str = "context_weighted",
        category_weights: Optional[Dict[str, float]] = None,
        context_match_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Configure the event library from scenario config.
        
        Args:
            environmental: Environmental event pools.
            social: Social event pools.
            character_specific: Character-specific trigger configurations.
            selection_mode: Event selection mode.
            category_weights: Weights for each category.
            context_match_weights: Weights for context matching.
        """
        if environmental:
            self._environmental_events.update(environmental)
        if social:
            self._social_events.update(social)
        
        if character_specific:
            for trigger_id, config in character_specific.items():
                self._character_triggers[trigger_id] = CharacterTrigger(
                    trigger_id=trigger_id,
                    condition=config.get("condition", ""),
                    events=config.get("events", []),
                    priority=config.get("priority", 1.0),
                )
        
        self._selection_mode = selection_mode
        if category_weights:
            self._category_weights.update(category_weights)
        if context_match_weights:
            self._context_match_weights.update(context_match_weights)
    
    def select_event(
        self,
        context: Dict[str, Any],
        tension: float,
        agent_states: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Event:
        """
        Select an appropriate event based on current context.
        
        Args:
            context: Current world context (weather, location, etc.).
            tension: Current tension level (0.0 to 1.0).
            agent_states: Current states of all agents.
            
        Returns:
            Selected Event ready for injection.
        """
        
        # Check for character-specific triggers first
        if agent_states:
            character_event = self._check_character_triggers(agent_states, tension)
            if character_event:
                return character_event
        
        # Select category based on weights and context
        if self._selection_mode == "random":
            category = self._random_category()
        else:
            category = self._context_weighted_category(context, tension)
        
        # Select event from category
        event_description = self._select_from_category(category, context, tension)
        
        # Create and return Event
        return Event(
            id=f"event_{random.randint(10000, 99999)}",
            category=EventCategory(category),
            description=event_description,
            context_tags=self._extract_context_tags(context),
            broadcast=True,
        )
    
    def _check_character_triggers(
        self, 
        agent_states: Dict[str, Dict[str, Any]], 
        tension: float
    ) -> Optional[Event]:
        """Check if any character-specific triggers are met."""
        
        matching_triggers = []
        
        for agent_id, state in agent_states.items():
            for trigger in self._character_triggers.values():
                if trigger.matches(state, tension, agent_id):
                    matching_triggers.append((agent_id, state, trigger))
        
        if not matching_triggers:
            return None
        
        # Sort by priority and select one
        matching_triggers.sort(key=lambda x: x[2].priority, reverse=True)
        agent_id, state, trigger = random.choice(matching_triggers)
        
        # Select event from trigger
        event_template = random.choice(trigger.events)
        event_description = event_template.format(
            agent_name=state.get("name", agent_id)
        )
        
        return Event(
            id=f"char_event_{random.randint(10000, 99999)}",
            category=EventCategory.CHARACTER_SPECIFIC,
            description=event_description,
            target_agent=agent_id,
            broadcast=True,
        )
    
    def _random_category(self) -> str:
        """Select a random category based on weights."""
        return self._weighted_choice(self._category_weights)
    
    def _context_weighted_category(
        self, 
        context: Dict[str, Any], 
        tension: float
    ) -> str:
        """Select category weighted by context relevance."""
        
        weights = self._category_weights.copy()
        
        # Adjust weights based on context
        weather = context.get("weather", "clear")
        location_type = context.get("location_type", "indoor")
        
        # Environmental events more relevant with notable weather
        if weather in ["stormy", "rainy", "snowy"]:
            match_weight = self._context_match_weights.get("outdoor_match", 1.5)
            weights["environmental"] *= match_weight
        
        # Social events more relevant with high tension
        if tension > 0.6:
            weights["social"] *= 1.3
        
        # Normalize and select
        return self._weighted_choice(weights)
    
    def _select_from_category(
        self, 
        category: str, 
        context: Dict[str, Any], 
        tension: float
    ) -> str:
        """Select an event from a specific category pool."""
        
        if category == "environmental":
            return self._select_environmental(context)
        elif category == "social":
            return self._select_social(tension)
        elif category == "character_specific":
            # Fallback to social if no character triggers matched
            return self._select_social(tension)
        elif category == "narrative":
            return self._select_narrative(tension)
        
        return "Something unexpected happens"
    
    def _select_environmental(self, context: Dict[str, Any]) -> str:
        """Select an environmental event matching context."""
        
        weather = context.get("weather", "clear")
        location_type = context.get("location_type", "indoor")
        
        # Determine pool
        if location_type == "outdoor":
            if weather in ["stormy", "rainy"]:
                pool_name = "outdoor_stormy"
            else:
                pool_name = "outdoor_clear"
        else:
            # Indoor - use tension to select pool
            tension = context.get("tension", 0)
            if tension > 0.5:
                pool_name = "indoor_tense"
            else:
                pool_name = "indoor_generic"
        
        pool = self._environmental_events.get(pool_name, self._environmental_events["indoor_generic"])
        return random.choice(pool)
    
    def _select_social(self, tension: float) -> str:
        """Select a social event based on tension level."""
        
        if tension > 0.6:
            pool_name = "conflict"
        elif tension < 0.3:
            pool_name = "cooperative"
        else:
            pool_name = "neutral"
        
        pool = self._social_events.get(pool_name, self._social_events["neutral"])
        return random.choice(pool)
    
    def _select_narrative(self, tension: float) -> str:
        """Select a narrative event."""
        # Placeholder for narrative-specific events
        return "The story continues to unfold"
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """Make a weighted random choice."""
        
        total = sum(weights.values())
        if total <= 0:
            return list(weights.keys())[0] if weights else "social"
        
        r = random.random() * total
        cumulative = 0
        
        for choice, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return choice
        
        return list(weights.keys())[-1]
    
    def _extract_context_tags(self, context: Dict[str, Any]) -> List[str]:
        """Extract relevant context tags."""
        tags = []
        
        if "weather" in context:
            tags.append(context["weather"])
        if "location_type" in context:
            tags.append(context["location_type"])
        if "time_of_day" in context:
            tags.append(context["time_of_day"])
        
        return tags
    
    def get_all_events(self) -> Dict[str, List[str]]:
        """Get all event pools for debugging/inspection."""
        return {
            "environmental": {
                k: list(v) for k, v in self._environmental_events.items()
            },
            "social": {
                k: list(v) for k, v in self._social_events.items()
            },
            "character_triggers": len(self._character_triggers),
        }