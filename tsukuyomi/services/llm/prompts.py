"""
Prompt Templates and Data Structures

This module contains the data structures and prompt templates used by the LLM service.
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger("LLMService")


# ============================================================================
# Data Structures
# ============================================================================

class ScenarioType(Enum):
    """Enumeration of supported scenario types for prompt templates."""
    SOCIAL = "social"
    COMBAT = "combat"
    STORYTELLING = "storytelling"
    DELIBERATION = "deliberation"
    REFLECTION = "reflection"


@dataclass
class LLMRequestContext:
    """Context object containing all information needed for LLM prompt generation."""
    agent_name: str
    agent_backstory: str
    agent_stance: Optional[str] = None
    working_memory: str = ""
    beliefs: str = ""
    relationships: str = ""
    emotional_modifier: str = ""
    semantic_facts: Optional[List[str]] = None
    world_state_summary: str = ""
    needs_context: str = ""  # V2: Internal needs driving agent behavior
    visual_context: str = ""  # Phase 2: Visual perception and spatial awareness
    rag_context: str = ""  # Phase 3: Long-term memory retrieval
    trigger_reason: str = "scheduled"

    def __post_init__(self):
        if self.semantic_facts is None:
            self.semantic_facts = []


@dataclass
class LLMResponse:
    """Structured response from the LLM service."""
    thought: str
    action: str
    params: Dict[str, Any]
    raw_response: Optional[str] = None
    provider: str = "unknown"
    tokens_used: Optional[int] = None


# ============================================================================
# Prompt Templates
# ============================================================================

def get_deliberation_template() -> str:
    """Template for agent deliberation scenarios."""
    return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}
{stance_section}

{needs}

{visual}

{rag}

{beliefs}

{relationships}

{emotional_modifier}

{working_memory}

{semantic_facts}

TASK:
Based on your internal needs, visual perception, beliefs, emotional state, relationships, and working memory, decide your next action.
IMPORTANT: If any need is above critical threshold (>80%), you MUST address it before other actions.
Your visual perception tells you what you can see around you (people, objects, obstacles).
Trigger: {trigger_reason}

Allowed Actions:
- MOVE (params: destination) - Move to a location. Use for exploration or finding food/items.
- EMOTE (params: type="speak", message="your words") - Speak to others.
- INTERACT (params: target_id) - Interact with an object (e.g., collect food, sit on chair).
- EXAMINE (params: target_id) - Look closely at an object or person.
- REFLECT (params: topic="defendant_guilt", position="for/against", weight=0.5, reasoning="...") - Update your beliefs
- IDLE (params: duration) - Wait and observe.

RESPONSE FORMAT (JSON only):
{{
    "thought": "your internal reasoning",
    "action": "MOVE|EMOTE|INTERACT|IDLE|EXAMINE|REFLECT",
    "params": {{"key": "value"}}
}}"""


def get_social_template() -> str:
    """Template for social interaction scenarios."""
    return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}

{relationships}

{emotional_modifier}

{working_memory}

TASK:
You are in a social situation. Respond appropriately to the conversation.
{trigger_reason}

Allowed Actions:
- EMOTE (params: type="speak", message="your words") - Speak to others.
- IDLE (params: duration) - Listen and observe.

RESPONSE FORMAT (JSON only):
{{
    "thought": "your internal reasoning about the social situation",
    "action": "EMOTE|IDLE",
    "params": {{"key": "value"}}
}}"""


def get_combat_template() -> str:
    """Template for combat scenarios."""
    return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}

{world_state_summary}

TASK:
You are in combat. Choose your tactical action carefully.

Allowed Actions:
- ATTACK (params: target_id)
- DEFEND (params: stance)
- MOVE (params: destination)
- IDLE (params: duration)

RESPONSE FORMAT (JSON only):
{{
    "thought": "your tactical analysis",
    "action": "ATTACK|DEFEND|MOVE|IDLE",
    "params": {{"key": "value"}}
}}"""


def get_storytelling_template() -> str:
    """Template for narrative/storytelling scenarios."""
    return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}

{working_memory}

TASK:
Advance the narrative in an engaging way.

Allowed Actions:
- EMOTE (params: type="speak", message="your words")
- MOVE (params: destination)
- IDLE (params: duration)

RESPONSE FORMAT (JSON only):
{{
    "thought": "your narrative reasoning",
    "action": "EMOTE|MOVE|IDLE",
    "params": {{"key": "value"}}
}}"""


def get_reflection_template() -> str:
    """Template for reflection/belief update scenarios."""
    return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}

{beliefs}

{emotional_modifier}

TASK:
Reflect on your beliefs and update them based on your reasoning.

Allowed Actions:
- REFLECT (params: topic="topic_name", position="for/against/neutral", weight=0.5, reasoning="...")
- IDLE (params: duration)

RESPONSE FORMAT (JSON only):
{{
    "thought": "your reflective reasoning",
    "action": "REFLECT|IDLE",
    "params": {{"key": "value"}}
}}"""


# ============================================================================
# Legacy Compatibility Functions
# ============================================================================

async def generate_plan_v2(
    profile: Dict,
    working_memory: str,
    beliefs: str,
    relationships: str,
    emotional_modifier: str,
    needs_context: str = "",  # V2: Add needs context
    visual_context: str = "",  # Phase 2: Add visual context
    rag_context: str = "",  # Phase 3: Add RAG context
    reason: str = "scheduled",
) -> Dict:
    """
    Legacy compatibility method for V2 deliberation with visual and RAG context.
    """
    from .service import LLMService

    service = LLMService()
    await service.initialize()

    context = LLMRequestContext(
        agent_name=profile.get("name", "Unknown"),
        agent_backstory=profile.get("backstory", ""),
        agent_stance=profile.get("stance"),
        working_memory=working_memory,
        beliefs=beliefs,
        relationships=relationships,
        emotional_modifier=emotional_modifier,
        needs_context=needs_context,
        visual_context=visual_context,
        rag_context=rag_context,
        trigger_reason=reason
    )

    response = await service.generate_agent_response(context, ScenarioType.DELIBERATION)

    return {
        "thought": response.thought,
        "action": response.action,
        "params": response.params
    }


async def generate_plan(
    profile: Dict,
    memories: List[Dict],
    semantic_facts: List[str],
    world_state_summary: str,
) -> Dict:
    """
    Legacy compatibility method for V1 deliberation.
    """
    from .service import LLMService

    service = LLMService()
    await service.initialize()

    context = LLMRequestContext(
        agent_name=profile.get("name", "Unknown"),
        agent_backstory=profile.get("backstory", ""),
        agent_stance=profile.get("stance"),
        semantic_facts=semantic_facts,
        world_state_summary=world_state_summary,
        working_memory=f"RECENT MEMORIES (Episodic):\n{json.dumps(memories, indent=2)}",
        trigger_reason="scheduled"
    )

    response = await service.generate_agent_response(context, ScenarioType.STORYTELLING)

    return {
        "thought": response.thought,
        "action": response.action,
        "params": response.params
    }
