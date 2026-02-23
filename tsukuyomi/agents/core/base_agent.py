from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsukuyomi.agents.internal.emotion import BaseEmotionalEngine
    from tsukuyomi.agents.cognitive.memory import BaseMemorySystem
    from tsukuyomi.agents.internal.beliefs.manager import BeliefManager

class BaseAgent(ABC):
    """
    Unified abstract base class for all Tsukuyomi agents.
    Provides standard interface for simulation and standalone modes.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        self.emotion_engine: Optional["BaseEmotionalEngine"] = None
        self.memory_system: Optional["BaseMemorySystem"] = None
        self.belief_tracker: Optional["BeliefManager"] = None
        
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
