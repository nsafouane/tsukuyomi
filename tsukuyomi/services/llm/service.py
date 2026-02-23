"""
Main LLM Service Class

This module provides the main service class for LLM integration in Tsukuyomi.
It manages provider instances, prompt templates, and handles response generation.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Optional, AsyncIterator

from dotenv import load_dotenv

from .provider import LLMProvider
from .openai_provider import OpenAICompatibleProvider, GroqProvider
from .prompts import (
    ScenarioType,
    LLMRequestContext,
    LLMResponse,
    get_deliberation_template,
    get_social_template,
    get_combat_template,
    get_storytelling_template,
    get_reflection_template,
)

# Load environment variables for API keys
load_dotenv()

logger = logging.getLogger("LLMService")


class LLMService:
    """
    Main service class for LLM integration in Tsukuyomi.

    This class serves as the bridge between the AgentBrain and external LLM providers.
    It manages provider instances, prompt templates, and handles response generation.

    Usage:
        # Initialize with default provider
        service = LLMService()
        await service.initialize()

        # Generate a response
        response = await service.generate_agent_response(context)
        print(response.thought, response.action, response.params)

        # Stream a response
        async for token in service.stream_agent_response(context):
            print(token, end='')
    """

    # Default configuration
    DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    DEFAULT_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))

    # Rate limiting configuration
    _rate_limit_lock = asyncio.Lock()
    _min_request_interval = 2.1  # seconds between requests (for Groq 30 RPM limit)
    _last_request_time = 0

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the LLM Service.

        Args:
            provider: Custom LLM provider instance (optional)
            api_key: API key for authentication (optional, reads from env)
            model: Model identifier (optional, reads from env)
            base_url: Base URL for API (optional, reads from env)
        """
        self._provider = provider
        self._api_key = api_key or os.getenv("LLM_API_KEY", "")
        self._model = model or self._api_key and self.DEFAULT_MODEL
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._initialized = False
        self._prompt_templates = self._load_prompt_templates()

    async def initialize(self) -> bool:
        """
        Initialize the LLM service and verify connectivity.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        # Create default provider if not provided
        if self._provider is None:
            if not self._api_key:
                logger.error("No API key provided. Set LLM_API_KEY environment variable.")
                return False

            provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
            if provider_type == "groq" or "groq" in self._base_url:
                self._provider = GroqProvider(
                    api_key=self._api_key,
                    model=self._model,
                    timeout=self.DEFAULT_TIMEOUT
                )
            else:
                self._provider = OpenAICompatibleProvider(
                    api_key=self._api_key,
                    model=self._model,
                    base_url=self._base_url,
                    timeout=self.DEFAULT_TIMEOUT
                )

        # Health check
        if await self._provider.health_check():
            self._initialized = True
            logger.info(f"LLM Service initialized with provider: {self._provider.__class__.__name__}")
            return True

        logger.error("LLM Service health check failed")
        return False

    async def generate_agent_response(
        self,
        context: LLMRequestContext,
        scenario_type: ScenarioType = ScenarioType.DELIBERATION
    ) -> LLMResponse:
        """
        Generate a complete agent response based on the provided context.

        Args:
            context: LLMRequestContext containing agent state and world information
            scenario_type: Type of scenario for prompt template selection

        Returns:
            LLMResponse with thought, action, and params
        """
        if not self._initialized:
            await self.initialize()

        # Apply rate limiting
        await self._respect_rate_limit()

        # Build prompts
        system_prompt = self._build_system_prompt(scenario_type)
        user_prompt = self._build_user_prompt(context, scenario_type)

        # Generate response
        try:
            response = await self._provider.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            logger.debug(
                f"Generated response for {context.agent_name}: "
                f"{response.action} with params {response.params}"
            )
            return response

        except Exception as e:
            logger.error(f"Failed to generate response for {context.agent_name}: {e}")
            # Return fallback idle action
            return LLMResponse(
                thought="I am processing the environment carefully.",
                action="IDLE",
                params={"duration": 10},
                provider="fallback"
            )

    async def stream_agent_response(
        self,
        context: LLMRequestContext,
        scenario_type: ScenarioType = ScenarioType.DELIBERATION
    ) -> AsyncIterator[str]:
        """
        Stream an agent response token by token.

        Args:
            context: LLMRequestContext containing agent state and world information
            scenario_type: Type of scenario for prompt template selection

        Yields:
            Individual tokens as they arrive
        """
        if not self._initialized:
            await self.initialize()

        # Apply rate limiting
        await self._respect_rate_limit()

        # Build prompts
        system_prompt = self._build_system_prompt(scenario_type)
        user_prompt = self._build_user_prompt(context, scenario_type)

        try:
            async for token in self._provider.stream_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            ):
                yield token

        except Exception as e:
            logger.error(f"Failed to stream response for {context.agent_name}: {e}")
            yield "Error generating response."

    # ========================================================================
    # Prompt Template Management
    # ========================================================================

    def _load_prompt_templates(self) -> Dict[ScenarioType, str]:
        """Load prompt templates for different scenario types."""
        return {
            ScenarioType.DELIBERATION: get_deliberation_template(),
            ScenarioType.SOCIAL: get_social_template(),
            ScenarioType.COMBAT: get_combat_template(),
            ScenarioType.STORYTELLING: get_storytelling_template(),
            ScenarioType.REFLECTION: get_reflection_template(),
        }

    def _build_system_prompt(self, scenario_type: ScenarioType) -> str:
        """Build system prompt based on scenario type."""
        base_prompt = (
            "You are an AI agent in a simulation engine called 'The Narrative Loom'. "
            "Generate realistic, in-character responses that advance the narrative naturally."
        )

        scenario_guidance = {
            ScenarioType.SOCIAL: "Focus on dialogue and social dynamics.",
            ScenarioType.COMBAT: "Focus on tactical decision-making.",
            ScenarioType.STORYTELLING: "Focus on narrative advancement.",
            ScenarioType.DELIBERATION: "Focus on character-driven decision making.",
            ScenarioType.REFLECTION: "Focus on internal reasoning and belief updates.",
        }

        return f"{base_prompt}\n{scenario_guidance.get(scenario_type, '')}"

    def _build_user_prompt(self, context: LLMRequestContext, scenario_type: ScenarioType) -> str:
        """Build user prompt from context and scenario template."""
        template = self._prompt_templates.get(scenario_type, get_deliberation_template())

        stance_section = f"Current Stance: {context.agent_stance}" if context.agent_stance else ""

        semantic_facts = ""
        if context.semantic_facts:
            semantic_facts = f"WORLD KNOWLEDGE (Semantic):\n{json.dumps(context.semantic_facts, indent=2)}"

        visual_section = f"VISUAL PERCEPTION:\n{context.visual_context}" if context.visual_context else "VISUAL PERCEPTION:\nYour vision is unobstructed."

        rag_section = f"RELEVANT MEMORIES (RAG):\n{context.rag_context}" if context.rag_context else ""

        return template.format(
            agent_name=context.agent_name,
            agent_backstory=context.agent_backstory,
            stance_section=stance_section,
            needs=context.needs_context,  # V2: Add needs context
            visual=visual_section,  # Phase 2: Add visual context
            rag=rag_section,  # Phase 3: Add RAG context
            beliefs=context.beliefs,
            relationships=context.relationships,
            emotional_modifier=context.emotional_modifier,
            working_memory=context.working_memory,
            semantic_facts=semantic_facts,
            trigger_reason=context.trigger_reason,
            world_state_summary=context.world_state_summary
        )

    async def _respect_rate_limit(self):
        """Apply rate limiting between requests."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()
