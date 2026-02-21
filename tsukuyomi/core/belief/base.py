from abc import ABC, abstractmethod
from typing import Any

class BaseBeliefTracker(ABC):
    """
    Unified scalable, interface-driven belief component.
    """
    
    @abstractmethod
    def add_belief(self, *args, **kwargs) -> Any:
        """Add a new belief."""
        pass
        
    @abstractmethod
    def get_belief(self, *args, **kwargs) -> Any:
        """Retrieve a belief."""
        pass
        
    @abstractmethod
    def update_belief(self, *args, **kwargs) -> Any:
        """Update an existing belief."""
        pass
