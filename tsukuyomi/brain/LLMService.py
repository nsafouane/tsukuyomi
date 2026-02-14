"""
Tsukuyomi LLM Service - V1.0 Implementation

This module provides the production-ready service for managing external AI connections,
prompt generation, and response streaming as defined in the V1.0 LLM Integration spec.

Key Features:
- Abstract base class for LLM providers
- Provider abstraction supporting OpenAI-compatible APIs
- Streaming response support
- Prompt template management for different scenario types
- Rate limiting and error handling
- Integration with AgentBrain for external directive generation
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv()

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
# Abstract Provider Interface
# ============================================================================

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All concrete implementations must inherit from this class and implement
    the required methods for generating responses and streaming.
    """
    
    def __init__(self, api_key: str, model: str, timeout: int = 30):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for authentication
            model: Model identifier to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(5)  # Concurrent request limit
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Generate a complete response from the LLM.
        
        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse containing parsed action and thought
        """
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream a response token by token.
        
        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            
        Yields:
            Individual tokens as they arrive
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider API is accessible."""
        pass


# ============================================================================
# OpenAI-Compatible Provider Implementation
# ============================================================================

class OpenAICompatibleProvider(LLMProvider):
    """
    Concrete implementation for OpenAI-compatible APIs.
    
    Supports:
    - OpenAI (GPT-3.5, GPT-4)
    - Groq (Llama models via OpenAI-compatible API)
    - Other providers with OpenAI-compatible endpoints
    """
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30
    ):
        super().__init__(api_key, model, timeout)
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/chat/completions"
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """Generate a response using OpenAI-compatible API."""
        async with self._semaphore:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API error {response.status}: {error_text}")
                            raise Exception(f"API returned status {response.status}: {error_text}")
                        
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data.get("usage", {}).get("total_tokens")
                        
                        # Parse JSON response
                        parsed = self._parse_json_response(content)
                        
                        return LLMResponse(
                            thought=parsed.get("thought", ""),
                            action=parsed.get("action", "IDLE"),
                            params=parsed.get("params", {}),
                            raw_response=content,
                            provider=self.__class__.__name__,
                            tokens_used=tokens_used
                        )
            
            except asyncio.TimeoutError:
                logger.error(f"Request timed out after {self.timeout}s")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise
    
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""
        async with self._semaphore:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API error {response.status}: {error_text}")
                            raise Exception(f"API returned status {response.status}")
                        
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    token = delta.get("content", "")
                                    if token:
                                        yield token
                                except json.JSONDecodeError:
                                    continue
            
            except asyncio.TimeoutError:
                logger.error(f"Stream timed out after {self.timeout}s")
                raise
    
    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

class GroqProvider(OpenAICompatibleProvider):
    """Concrete implementation for Groq API."""
    def __init__(self, api_key: str, model: str, timeout: int = 30):
        super().__init__(api_key, model, "https://api.groq.com/openai/v1", timeout)
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from content: {content[:200]}")
            return {
                "thought": "I am processing the environment carefully.",
                "action": "IDLE",
                "params": {"duration": 10}
            }


# ============================================================================
# Main LLM Service Class
# ============================================================================

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

    @staticmethod
    async def generate_plan_v2(
        profile: Dict,
        working_memory: str,
        beliefs: str,
        relationships: str,
        emotional_modifier: str,
        reason: str,
    ) -> Dict:
        """
        Legacy compatibility method for V2 deliberation.
        """
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
            trigger_reason=reason
        )
        
        response = await service.generate_agent_response(context, ScenarioType.DELIBERATION)
        
        return {
            "thought": response.thought,
            "action": response.action,
            "params": response.params
        }

    @staticmethod
    async def generate_plan(
        profile: Dict,
        memories: List[Dict],
        semantic_facts: List[str],
        world_state_summary: str,
    ) -> Dict:
        """
        Legacy compatibility method for V1 deliberation.
        """
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
            ScenarioType.DELIBERATION: self._get_deliberation_template(),
            ScenarioType.SOCIAL: self._get_social_template(),
            ScenarioType.COMBAT: self._get_combat_template(),
            ScenarioType.STORYTELLING: self._get_storytelling_template(),
            ScenarioType.REFLECTION: self._get_reflection_template(),
        }
    
    def _get_deliberation_template(self) -> str:
        """Template for agent deliberation scenarios."""
        return """CONTEXT:
You are simulating an AI agent in 'The Narrative Loom'.
Identity: {agent_name}
Backstory: {agent_backstory}
{stance_section}

{beliefs}

{relationships}

{emotional_modifier}

{working_memory}

{semantic_facts}

TASK:
Based on your beliefs, emotional state, relationships, and working memory, decide your next action.
Trigger: {trigger_reason}

Allowed Actions:
- MOVE (params: destination)
- EMOTE (params: type="speak", message="your words") - Use this to talk to others.
- EXAMINE (params: target_id) - Look closely at an object or person
- REFLECT (params: topic="defendant_guilt", position="for/against", weight=0.5, reasoning="...") - Update your beliefs
- IDLE (params: duration)

RESPONSE FORMAT (JSON only):
{{
    "thought": "your internal reasoning",
    "action": "MOVE|EMOTE|IDLE|EXAMINE|REFLECT",
    "params": {{"key": "value"}}
}}"""
    
    def _get_social_template(self) -> str:
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
    
    def _get_combat_template(self) -> str:
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
    
    def _get_storytelling_template(self) -> str:
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
    
    def _get_reflection_template(self) -> str:
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
        template = self._prompt_templates.get(scenario_type, self._get_deliberation_template())
        
        stance_section = f"Current Stance: {context.agent_stance}" if context.agent_stance else ""
        
        semantic_facts = ""
        if context.semantic_facts:
            semantic_facts = f"WORLD KNOWLEDGE (Semantic):\n{json.dumps(context.semantic_facts, indent=2)}"
        
        return template.format(
            agent_name=context.agent_name,
            agent_backstory=context.agent_backstory,
            stance_section=stance_section,
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


# ============================================================================
# Legacy Compatibility Functions (for backward compatibility)
# ============================================================================

async def generate_plan_v2(*args, **kwargs):
    return await LLMService.generate_plan_v2(*args, **kwargs)

async def generate_plan(*args, **kwargs):
    return await LLMService.generate_plan(*args, **kwargs)

