from abc import ABC, abstractmethod
from typing import Any

from tsukuyomi.core.emotion.base import BaseEmotionalEngine
from tsukuyomi.core.memory.base import BaseMemorySystem
from tsukuyomi.core.belief.base import BaseBeliefTracker

class BaseAgent(ABC):
    """
    Unified abstract base class for all Tsukuyomi agents.
    Provides standard interface for simulation and standalone modes.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Core subsystems via composition
        self.emotion_engine: BaseEmotionalEngine = None
        self.memory_system: BaseMemorySystem = None
        self.belief_tracker: BaseBeliefTracker = None
        
    @abstractmethod
    async def perceive(self, *args, **kwargs) -> Any:
        """Process incoming stimuli or events."""
        pass
        
    @abstractmethod
    async def deliberate(self, *args, **kwargs) -> Any:
        """Internal reasoning cycle."""
        pass
        
    @abstractmethod
    async def act(self, *args, **kwargs) -> Any:
        """Produce an output or behavior."""
        pass
        
    # Formal Lifecycle Management
    @abstractmethod
    def start(self):
        """Start the agent lifecycle."""
        pass
        
    @abstractmethod
    def pause(self):
        """Pause agent processing."""
        pass
        
    @abstractmethod
    def resume(self):
        """Resume agent processing."""
        pass
        
    @abstractmethod
    def cleanup(self):
        """Clean up resources before shutdown."""
        pass
