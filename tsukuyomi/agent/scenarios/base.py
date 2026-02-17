"""
Scenario Base Class
==================

Base class for all simulation scenarios.

Scenarios define:
- How agents are initialized
- What actions they can take
- How the simulation progresses
- How outcomes are determined
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger("Scenario")


@dataclass
class ScenarioConfig:
    """Configuration for a scenario."""
    name: str = "unknown"
    max_ticks: int = 10000
    max_real_time_minutes: int = 60
    
    # Agent settings
    num_agents: int = 5
    agent_profiles_dir: str = ""
    
    # LLM settings
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.8
    llm_max_tokens: int = 500
    llm_rate_limit_per_minute: int = 30


class Scenario(ABC):
    """
    Abstract base class for simulation scenarios.
    
    Subclasses implement specific scenarios like:
    - Jury deliberation
    - Combat encounters
    - Social gatherings
    - Negotiations
    """
    
    def __init__(self, config: ScenarioConfig = None):
        self.config = config or ScenarioConfig()
        self.agents: List[Any] = []
        self.current_tick = 0
        self.is_running = False
        self.results: Dict[str, Any] = {}
        
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the scenario.
        
        - Load agents
        - Set up initial state
        - Prepare environment
        """
        pass
    
    @abstractmethod
    async def step(self) -> bool:
        """
        Execute one simulation step.
        
        Returns:
            True if simulation should continue, False if done
        """
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current scenario state."""
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """Check if scenario is complete."""
        pass
    
    async def run(self, max_ticks: int = None) -> Dict[str, Any]:
        """
        Run the complete scenario.
        
        Args:
            max_ticks: Maximum ticks to run (overrides config)
        
        Returns:
            Final results
        """
        max_ticks = max_ticks or self.config.max_ticks
        
        await self.initialize()
        self.is_running = True
        
        logger.info(f"Starting scenario: {self.config.name}")
        
        while self.current_tick < max_ticks and not self.is_complete():
            should_continue = await self.step()
            
            if not should_continue:
                break
            
            self.current_tick += 1
        
        self.is_running = False
        self.results = self.get_state()
        
        logger.info(f"Scenario complete: {self.config.name} at tick {self.current_tick}")
        
        return self.results
    
    def save_results(self, filepath: str) -> None:
        """Save scenario results to file."""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")


__all__ = ["ScenarioConfig", "Scenario"]