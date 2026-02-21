from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseEmotionalEngine(ABC):
    """
    Unified emotional engine mapping Pleasure-Arousal-Dominance (PAD).
    """
    
    @abstractmethod
    def get_pad_state(self) -> Dict[str, float]:
        """Return the current PAD state."""
        pass
        
    @abstractmethod
    def update(self, *args, **kwargs) -> Any:
        """Update emotional state based on internal/external events."""
        pass
