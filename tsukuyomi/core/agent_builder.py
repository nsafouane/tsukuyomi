"""
Agent Builder Factory
=====================

Factory for assembling BaseAgent variants with specialized core modules.
"""

from typing import Dict, Any, Type
from tsukuyomi.core.agent_base import BaseAgent
from tsukuyomi.brain.agent_brain import AgentBrain
from tsukuyomi.agent.universal_agent import UniversalAgent, AgentConfig

class AgentBuilder:
    """Factory class for assembling initialized Tsukuyomi agents."""
    
    @staticmethod
    def build_agent_brain(actor_id: str, profile: Dict[str, Any], server_addr: str = "localhost:50051") -> AgentBrain:
        """
        Assembles and configures an AgentBrain for the simulation engine.
        
        Args:
            actor_id: Unique identifier for the agent
            profile: Profile configuration dict
            server_addr: FateEngine server address
            
        Returns:
            Configured AgentBrain instance
        """
        agent = AgentBrain(actor_id=actor_id, profile=profile, server_addr=server_addr)
        return agent

    @staticmethod
    def build_universal_agent(config: AgentConfig) -> UniversalAgent:
        """
        Assembles and configures a UniversalAgent for standalone play.
        
        Args:
            config: Agent configuration object
            
        Returns:
            Configured UniversalAgent instance
        """
        agent = UniversalAgent(config=config)
        return agent

__all__ = ["AgentBuilder"]
