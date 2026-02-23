"""
Personality Evolution Manager
=============================

Manages intentional personality changes over time.
"""

from typing import List, Dict, Any
import logging

from .profile import PersonalityProfile
from .drift_types import PersonalityEvolutionEvent


logger = logging.getLogger("PersonalityEvolutionManager")


class PersonalityEvolutionManager:
    """
    Manage intentional personality changes over time.
    
    Personality can evolve through dramatic events, character growth,
    or trauma. This manager tracks and limits such changes to maintain
    personality integrity while allowing for meaningful character arcs.
    """
    
    MAX_DRIFT_PER_TRAIT: float = 0.3
    MAX_CHANGE_PER_EVENT: float = 0.1
    
    VALID_REASONS = {
        "traumatic_event",
        "character_growth",
        "relationship_development",
        "life_experience",
        "forced_adaptation",
        "revelation",
    }
    
    def __init__(self, profile: PersonalityProfile):
        self.profile = profile
        self.evolution_history: List[PersonalityEvolutionEvent] = []
        self._base_traits = {
            'openness': profile.openness,
            'conscientiousness': profile.conscientiousness,
            'extraversion': profile.extraversion,
            'agreeableness': profile.agreeableness,
            'neuroticism': profile.neuroticism,
        }
    
    def evolve_trait(
        self,
        trait: str,
        change: float,
        reason: str,
        trigger: str,
        tick: int
    ) -> bool:
        """Apply intentional personality change."""
        if trait not in self._base_traits:
            logger.error(f"Invalid trait name: {trait}")
            return False
        
        if reason not in self.VALID_REASONS:
            logger.error(f"Invalid evolution reason: {reason}")
            return False
        
        change = max(-self.MAX_CHANGE_PER_EVENT, min(self.MAX_CHANGE_PER_EVENT, change))
        
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        if abs(total_change + change) > self.MAX_DRIFT_PER_TRAIT:
            logger.warning(
                f"Trait {trait} evolution capped at {self.MAX_DRIFT_PER_TRAIT}. "
                f"Current total change: {total_change:.2f}"
            )
            return False
        
        event = PersonalityEvolutionEvent(
            tick=tick,
            trait=trait,
            change=change,
            reason=reason,
            trigger_event=trigger
        )
        self.evolution_history.append(event)
        
        current_value = getattr(self.profile, trait)
        new_value = max(-1.0, min(1.0, current_value + change))
        setattr(self.profile, trait, new_value)
        
        logger.info(
            f"Personality evolution: {self.profile.name}'s {trait} "
            f"changed by {change:+.2f} ({reason}) - now {new_value:.2f}"
        )
        
        return True
    
    def get_trait_evolution_summary(self, trait: str) -> Dict[str, Any]:
        """Get summary of evolution for a specific trait."""
        trait_events = [e for e in self.evolution_history if e.trait == trait]
        
        if not trait_events:
            return {
                'trait': trait,
                'base_value': self._base_traits.get(trait, 0.0),
                'current_value': getattr(self.profile, trait, 0.0),
                'total_change': 0.0,
                'events': []
            }
        
        total_change = sum(e.change for e in trait_events)
        
        return {
            'trait': trait,
            'base_value': self._base_traits.get(trait, 0.0),
            'current_value': getattr(self.profile, trait, 0.0),
            'total_change': total_change,
            'events': [
                {
                    'tick': e.tick,
                    'change': e.change,
                    'reason': e.reason,
                    'trigger': e.trigger_event
                }
                for e in trait_events
            ]
        }
    
    def can_evolve(self, trait: str, change: float) -> bool:
        """Check if a trait can evolve by the given amount."""
        if trait not in self._base_traits:
            return False
        
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        return abs(total_change + change) <= self.MAX_DRIFT_PER_TRAIT
    
    def get_available_evolution_room(self, trait: str) -> float:
        """Get remaining evolution room for a trait."""
        if trait not in self._base_traits:
            return 0.0
        
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        positive_room = self.MAX_DRIFT_PER_TRAIT - total_change
        negative_room = -self.MAX_DRIFT_PER_TRAIT - total_change
        
        return max(positive_room, abs(negative_room))
