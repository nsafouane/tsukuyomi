"""
Universal Agent Runtime
======================

The complete, runnable agent that combines:
- Identity (who they are)
- Memory (what they remember)
- Prompts (how they express themselves)

This is the main class for creating and running Tsukuyomi agents.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json

from tsukuyomi.agents.core.identity import AgentIdentity, create_identity
from tsukuyomi.agents.cognitive.memory.memory_system import LongTermMemory, Memory
from tsukuyomi.agents.cognitive.memory.base import MemoryType
from tsukuyomi.agents.prompts.immersive_prompt import (
    ImmersivePromptBuilder, 
    PromptContext, 
    create_prompt_context
)
from tsukuyomi.agents.cognitive.deliberation import DeliberationEngine
from tsukuyomi.agents.internal.emotional_expression import EmotionalExpression

logger = logging.getLogger("UniversalAgent")

def store_event_memory(memory_system, event, *args, **kwargs):
    """Placeholder function for storing event memory."""
    if memory_system:
        return memory_system.store(event)
    return None


class AgentState(Enum):
    """Current state of an agent."""
    IDLE = "idle"           # Not doing anything
    THINKING = "thinking"   # Processing input
    RESPONDING = "responding"  # Generating response
    ACTING = "acting"       # Performing an action
    RESTING = "resting"     # Taking a break


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    # Identity
    identity_file: str = ""  # Path to identity JSON
    identity_dict: Dict = None  # Or direct identity data
    
    # Memory
    max_memories: int = 10000
    memory_file: str = ""  # Path to memory persistence
    
    # LLM
    llm_provider: str = "groq"  # groq, openai, anthropic
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.8
    llm_max_tokens: int = 500
    
    # Behavior
    prompt_style: str = "full"  # full, concise, intense
    auto_memory: bool = True  # Automatically store experiences
    
    # Scenario
    scenario_name: str = "unknown"
    scenario_context: str = ""


from tsukuyomi.agents.core.base_agent import BaseAgent

class UniversalAgent(BaseAgent):
    """
    A complete, runnable agent for any scenario.
    
    This is the main entry point for creating Tsukuyomi agents.
    
    Usage:
        agent = UniversalAgent(config)
        agent.load_identity(identity_file="juror.json")
        response = await agent.respond("What do you think?")
    """
    
    def __init__(self, config: AgentConfig = None):
        super().__init__(agent_id="unknown_temp_id")
        self.config = config or AgentConfig()
        
        # Core components
        self.identity: Optional[AgentIdentity] = None
        self.memory: Optional[LongTermMemory] = None
        self.prompt_builder: Optional[ImmersivePromptBuilder] = None
        self.deliberation_engine: Optional[DeliberationEngine] = None
        self.emotional_expression: Optional[EmotionalExpression] = None
        
        # State
        self.state = AgentState.IDLE
        self.current_tick = 0
        self.conversation_history: List[Dict[str, Any]] = []
        self._running = True
        self._paused = False
        
        # LLM function (injected)
        self._llm_call: Optional[Callable] = None
        
        # Statistics
        self.total_interactions = 0
        self.total_responses = 0
        
        logger.info(f"UniversalAgent initialized with config: {self.config.scenario_name}")
    
    def load_identity(self, identity_file: str = None, identity_dict: Dict = None) -> None:
        """
        Load agent identity from file or dict.
        
        Args:
            identity_file: Path to JSON file with identity
            identity_dict: Direct identity data
        """
        if identity_file:
            with open(identity_file, 'r') as f:
                data = json.load(f)
            self.identity = AgentIdentity.from_dict(data)
            logger.info(f"Loaded identity from {identity_file}")
        
        elif identity_dict:
            self.identity = AgentIdentity.from_dict(identity_dict)
            logger.info("Loaded identity from dict")
        
        elif self.config.identity_file:
            with open(self.config.identity_file, 'r') as f:
                data = json.load(f)
            self.identity = AgentIdentity.from_dict(data)
            logger.info(f"Loaded identity from {self.config.identity_file}")
        
        elif self.config.identity_dict:
            self.identity = AgentIdentity.from_dict(self.config.identity_dict)
        
        else:
            raise ValueError("No identity provided")
        
        # Initialize memory with agent ID
        self.memory = LongTermMemory(
            agent_id=self.identity.id,
            max_memories=self.config.max_memories
        )
        
        # Initialize prompt builder
        self.prompt_builder = ImmersivePromptBuilder(
            identity=self.identity,
            memory_system=self.memory,
            scenario_name=self.config.scenario_name
        )
        
        # Initialize deliberation and emotional expression (Phase 1 & 2)
        self.deliberation_engine = DeliberationEngine(
            agent_id=self.identity.id,
            personality=self.identity.personality.to_dict() if self.identity.personality else {},
            llm_call=self._llm_call
        )
        
        self.emotional_expression = EmotionalExpression(
            pad_state=self.identity.get_baseline_pad(),
            personality=self.identity.personality.to_dict() if self.identity.personality else {}
        )
        
        logger.info(f"Agent identity loaded: {self.identity.name}")
    
    def set_llm(self, llm_call: Callable) -> None:
        """
        Set the LLM call function.
        
        This allows injecting any LLM provider.
        
        Args:
            llm_call: Async function that takes (prompt, **kwargs) and returns response
        """
        self._llm_call = llm_call
        if self.deliberation_engine:
            self.deliberation_engine._llm_call = llm_call
        logger.info(f"LLM set: {self.config.llm_provider}")
    
    async def respond(
        self,
        input_text: str,
        context: PromptContext = None,
        store_interaction: bool = True
    ) -> str:
        """
        Generate a response to input.
        
        Args:
            input_text: What to respond to
            context: Optional context override
            store_interaction: Whether to store in memory
        
        Returns:
            Agent's response
        """
        if not self.identity:
            raise RuntimeError("Agent identity not loaded")
        
        if not self._llm_call:
            raise RuntimeError("LLM not set - call set_llm() first")
        
        self.state = AgentState.THINKING
        
        # Phase 1: Internal Deliberation
        deliberation_text = ""
        if self.deliberation_engine:
            deliberation_result = await self.deliberation_engine.deliberate(
                context={
                    "stimulus": input_text,
                    "recent_arguments": [h["content"] for h in self.conversation_history[-3:] if h["role"] == "user"]
                },
                tick=self.current_tick
            )
            deliberation_text = deliberation_result.content
            
        # Phase 2: Emotional Expression (Tone Modifiers)
        tone_modifiers_text = ""
        if self.emotional_expression:
            modifiers = self.emotional_expression.get_tone_modifiers()
            tone_modifiers_text = modifiers.get_prompt_additions()
        
        # Build context if not provided
        if context is None:
            context = create_prompt_context(
                situation=input_text,
                recent_events=[h["content"] for h in self.conversation_history[-3:]],
                emotional_state=self._get_current_emotional_state(),
                deliberation=deliberation_text,
                tone_modifiers=tone_modifiers_text
            )
        
        # Build prompt
        prompt = await self.prompt_builder.build_prompt_with_memory(
            context=context,
            tick=self.current_tick,
            style=self.config.prompt_style
        )
        
        # Call LLM
        self.state = AgentState.RESPONDING
        try:
            response = await self._llm_call(
                prompt,
                model=self.config.llm_model,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            self.state = AgentState.IDLE
            return f"[Error: {e}]"
        
        self.state = AgentState.IDLE
        self.total_responses += 1
        
        # Store interaction in memory
        if store_interaction and self.config.auto_memory:
            await self._store_interaction(input_text, response)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": input_text,
            "tick": self.current_tick
        })
        self.conversation_history.append({
            "role": "agent",
            "content": response,
            "tick": self.current_tick
        })
        
        # Keep history manageable
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        return response
    
    async def observe(
        self,
        event: str,
        importance: float = 0.5,
        emotional_tags: List[str] = None
    ) -> str:
        """
        Observe and remember an event without responding.
        
        Args:
            event: What happened
            importance: How important (0.0-1.0)
            emotional_tags: Emotions associated
        
        Returns:
            Memory ID
        """
        if not self.memory:
            raise RuntimeError("Agent memory not initialized")
        
        memory_id = store_event_memory(
            memory_system=self.memory,
            event=event,
            context=f"Observed at tick {self.current_tick}",
            importance=importance,
            emotional_tags=emotional_tags or [],
            tick=self.current_tick
        )
        
        logger.debug(f"Agent {self.identity.name} observed: {event[:50]}...")
        return memory_id
    
    async def reflect(
        self,
        topic: str = "",
        k_memories: int = 5
    ) -> str:
        """
        Reflect on past experiences and generate insights.
        
        Args:
            topic: What to reflect on (empty = recent events)
            k_memories: How many memories to consider
        
        Returns:
            Reflection text
        """
        if not self.memory or not self._llm_call:
            raise RuntimeError("Agent not fully initialized")
        
        self.state = AgentState.THINKING
        
        # Retrieve relevant memories
        memories = await self.memory.retrieve(
            query=topic or "recent events",
            k=k_memories,
            tick=self.current_tick
        )
        
        # Build reflection prompt
        memory_text = "\n".join([
            f"- {m.content} ({m.emotional_tags})"
            for m in memories
        ])
        
        reflection_prompt = f"""You are {self.identity.name}. Reflect on these experiences:

{memory_text}

What patterns do you notice? How do you feel about these events? What have you learned?

Speak as yourself, in first person."""
        
        # Generate reflection
        response = await self._llm_call(
            reflection_prompt,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
        
        self.state = AgentState.IDLE
        return response
    
    def advance_tick(self, ticks: int = 1) -> None:
        """Advance the simulation tick."""
        self.current_tick += ticks
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state for display."""
        return {
            "name": self.identity.name if self.identity else "Unknown",
            "state": self.state.value,
            "tick": self.current_tick,
            "total_interactions": self.total_interactions,
            "total_responses": self.total_responses,
            "memory_count": self.memory.get_memory_count() if self.memory else 0
        }
    
    def get_emotional_baseline(self) -> Dict[str, float]:
        """Get emotional baseline PAD values."""
        if self.identity:
            return self.identity.get_baseline_pad()
        return {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
    
    def _get_current_emotional_state(self) -> str:
        """Get current emotional state description."""
        pad = self.get_emotional_baseline()
        
        # Simplified emotional state from PAD
        if pad["valence"] > 0.3:
            if pad["arousal"] > 0.6:
                return "energetic and positive"
            return "calm and content"
        elif pad["valence"] < -0.3:
            if pad["arousal"] > 0.6:
                return "agitated and frustrated"
            return "down and withdrawn"
        else:
            if pad["arousal"] > 0.6:
                return "alert and engaged"
            return "neutral and composed"
    
    async def _store_interaction(self, input_text: str, response: str) -> None:
        """Store an interaction in memory."""
        if not self.memory:
            return
        
        # Store what was said to them
        store_event_memory(
            memory_system=self.memory,
            event=f"Someone said: '{input_text[:100]}'",
            context=f"I responded: '{response[:100]}'",
            importance=0.4,
            tick=self.current_tick
        )
        
        # Store what they said
        store_event_memory(
            memory_system=self.memory,
            event=f"I said: '{response[:100]}'",
            importance=0.5,
            tick=self.current_tick
        )
    
    def save_state(self, filepath: str) -> None:
        """Save agent state to file."""
        state = {
            "identity": self.identity.to_dict() if self.identity else None,
            "memory": self.memory.to_dict() if self.memory else None,
            "current_tick": self.current_tick,
            "conversation_history": self.conversation_history,
            "total_interactions": self.total_interactions,
            "total_responses": self.total_responses,
            "config": {
                "scenario_name": self.config.scenario_name,
                "prompt_style": self.config.prompt_style,
                "llm_model": self.config.llm_model
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Agent state saved to {filepath}")

    # BaseAgent Abstract Methods
    async def perceive(self, *args, **kwargs):
        pass

    async def deliberate(self, *args, **kwargs):
        pass

    async def act(self, *args, **kwargs):
        """Perform an action."""
        if self._paused:
            return
        pass

    def start(self):
        """Start agent lifecycle."""
        self._running = True
        self._paused = False
        logger.info(f"UniversalAgent {self.agent_id} started.")

    def pause(self):
        """Pause agent processing."""
        self._paused = True
        logger.info(f"UniversalAgent {self.agent_id} paused.")

    def resume(self):
        """Resume agent processing."""
        self._paused = False
        logger.info(f"UniversalAgent {self.agent_id} resumed.")

    def cleanup(self):
        """Clean up agent resources."""
        self._running = False
        logger.info(f"UniversalAgent {self.agent_id} cleaned up.")
    
    @classmethod
    def load_state(cls, filepath: str) -> 'UniversalAgent':
        """Load agent state from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config = AgentConfig(
            scenario_name=data.get("config", {}).get("scenario_name", "unknown"),
            prompt_style=data.get("config", {}).get("prompt_style", "full"),
            llm_model=data.get("config", {}).get("llm_model", "llama-3.3-70b-versatile")
        )
        
        agent = cls(config)
        
        if data.get("identity"):
            agent.identity = AgentIdentity.from_dict(data["identity"])
            agent.memory = LongTermMemory.from_dict(data.get("memory", {"agent_id": agent.identity.id}))
            agent.prompt_builder = ImmersivePromptBuilder(
                identity=agent.identity,
                memory_system=agent.memory,
                scenario_name=config.scenario_name
            )
        
        agent.current_tick = data.get("current_tick", 0)
        agent.conversation_history = data.get("conversation_history", [])
        agent.total_interactions = data.get("total_interactions", 0)
        agent.total_responses = data.get("total_responses", 0)
        
        logger.info(f"Agent state loaded from {filepath}")
        return agent


def create_agent(
    name: str,
    age: int,
    occupation: str,
    origin_story: str,
    core_values: List[Dict],
    defining_memories: List[Dict],
    personality: Dict,
    scenario_name: str = "unknown",
    **kwargs
) -> UniversalAgent:
    """
    Helper to create a fully configured agent.
    
    Args:
        name: Agent's name
        age: Agent's age
        occupation: Agent's job
        origin_story: Life history
        core_values: List of core value dicts
        defining_memories: List of defining memory dicts
        personality: Personality traits dict
        scenario_name: Current scenario
        **kwargs: Additional config
    
    Returns:
        Configured UniversalAgent
    """
    config = AgentConfig(
        scenario_name=scenario_name,
        **kwargs
    )
    
    agent = UniversalAgent(config)
    
    identity_dict = {
        "name": name,
        "age": age,
        "occupation": occupation,
        "origin_story": origin_story,
        "core_values": core_values,
        "defining_memories": defining_memories,
        "personality": personality
    }
    
    agent.load_identity(identity_dict=identity_dict)
    
    return agent


__all__ = [
    "AgentState",
    "AgentConfig",
    "UniversalAgent",
    "create_agent"
]