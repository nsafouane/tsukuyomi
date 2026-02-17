"""
Groq LLM Configuration for Angry Men Experiment
================================================

Handles rate limiting and batching for Groq free tier.
"""

import os
import asyncio
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("GroqLLM")

# Load environment
from dotenv import load_dotenv
load_dotenv()


@dataclass
class GroqConfig:
    """Groq free tier configuration."""
    api_key: str = os.getenv("LLM_API_KEY", "")
    base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "512"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))
    
    # Rate limits (free tier)
    requests_per_minute: int = int(os.getenv("GROQ_RPM", "30"))
    tokens_per_minute: int = int(os.getenv("GROQ_TPM", "30000"))
    batch_size: int = int(os.getenv("GROQ_BATCH_SIZE", "5"))


class GroqRateLimiter:
    """Rate limiter for Groq API."""
    
    def __init__(self, config: GroqConfig):
        self.config = config
        self.request_times: List[float] = []
        self.token_counts: List[int] = []
        self.min_interval = 60.0 / config.requests_per_minute
    
    async def acquire(self, tokens: int = 100):
        """Acquire permission to make a request."""
        now = time.time()
        
        # Clean old entries (older than 1 minute)
        self.request_times = [t for t in self.request_times if now - t < 60]
        self.token_counts = self.token_counts[-len(self.request_times):]
        
        # Check if we need to wait
        if len(self.request_times) >= self.config.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0])
            if wait_time > 0:
                logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Check token limit
        total_tokens = sum(self.token_counts)
        if total_tokens + tokens > self.config.tokens_per_minute:
            wait_time = 60 - (now - self.request_times[0]) if self.request_times else 0
            if wait_time > 0:
                logger.debug(f"Token limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self.request_times.append(time.time())
        self.token_counts.append(tokens)


class GroqLLMClient:
    """
    Groq LLM client with rate limiting for free tier.
    """
    
    def __init__(self, config: GroqConfig = None):
        self.config = config or GroqConfig()
        self.rate_limiter = GroqRateLimiter(self.config)
        self._session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """
        Generate text with rate limiting.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Override default max tokens
            temperature: Override default temperature
        
        Returns:
            Generated text
        """
        # Estimate tokens (rough: ~4 chars per token)
        estimated_tokens = len(prompt) // 4 + (len(system_prompt) // 4 if system_prompt else 0)
        estimated_tokens = max(100, min(estimated_tokens, self.config.max_tokens))
        
        # Wait for rate limit
        await self.rate_limiter.acquire(estimated_tokens)
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Make request
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature
        }
        
        try:
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            ) as response:
                if response.status == 429:
                    # Rate limited - wait and retry
                    logger.warning("Rate limited, waiting 60s...")
                    await asyncio.sleep(60)
                    return await self.generate(prompt, system_prompt, max_tokens, temperature)
                
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"Groq API error: {response.status} - {error}")
                    return f"[Error: {response.status}]"
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
        
        except asyncio.TimeoutError:
            logger.error("Groq API timeout")
            return "[Timeout]"
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"[Error: {e}]"
    
    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: str = None
    ) -> List[str]:
        """
        Generate multiple responses with proper spacing.
        
        Args:
            prompts: List of prompts
            system_prompt: Shared system prompt
        
        Returns:
            List of generated texts
        """
        results = []
        
        # Process in batches
        for i in range(0, len(prompts), self.config.batch_size):
            batch = prompts[i:i + self.config.batch_size]
            batch_results = await asyncio.gather(*[
                self.generate(p, system_prompt)
                for p in batch
            ])
            results.extend(batch_results)
            
            # Small delay between batches
            if i + self.config.batch_size < len(prompts):
                await asyncio.sleep(2)
        
        return results
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None


# Prompts for deliberation
DELIBERATION_PROMPTS = {
    "initial_position": """You are {name}, a juror in a murder trial.

Your personality: {personality}

The case: A 19-year-old from the slums is accused of murdering his father. The prosecution claims:
1. He bought a switchblade the night of the murder
2. An old man heard him shout "I'm going to kill you" and saw him running
3. A woman saw the stabbing through a passing train's windows

Your current position: {stance} (confidence: {confidence}/10)

Respond briefly (2-3 sentences) with your initial position. Stay in character.""",

    "respond_to_argument": """You are {name}, a juror in a murder trial.

Your personality: {personality}
Your current position: {stance} (confidence: {confidence}/10)

Another juror just said: "{other_juror_argument}"

Consider your beliefs and respond in character. Keep it brief (2-3 sentences).
Focus on evidence and reasoning, not personal attacks.""",

    "vote_change": """You are {name}.

After hearing the discussion, you're reconsidering your position.
Current position: {stance} (confidence: {confidence}/10)
New evidence to consider: {evidence}

Should you change your vote? If yes, explain why briefly.
If no, explain what would need to change your mind.""",

    "emotional_outburst": """You are {name}.

The discussion has become heated. Your emotional triggers are: {triggers}
Your son walked out on you two years ago. The defendant reminds you of him.

Express your emotional state in character. Let your personal pain surface.
(2-3 sentences, raw and emotional)"""
}


def build_juror_prompt(
    juror,
    prompt_type: str,
    context: Dict = None
) -> tuple:
    """Build a prompt for a juror."""
    context = context or {}
    
    prompt_template = DELIBERATION_PROMPTS.get(prompt_type, "")
    
    prompt = prompt_template.format(
        name=juror.profile["name"],
        personality=juror.get_personality_summary(),
        stance=juror.current_vote,
        confidence=int(juror.profile.get("beliefs", {}).get("stance_confidence", 0.5) * 10),
        other_juror_argument=context.get("argument", ""),
        evidence=context.get("evidence", ""),
        triggers=", ".join(juror.profile.get("memories", {}).get("episodic", [{}])[0].get("tags", ["unknown"]))
    )
    
    system_prompt = f"You are roleplaying as {juror.profile['name']}, a {juror.profile['age']}-year-old {juror.profile['occupation']} on a jury. Stay completely in character. Be concise."
    
    return prompt, system_prompt


# Export
__all__ = [
    "GroqConfig",
    "GroqRateLimiter", 
    "GroqLLMClient",
    "DELIBERATION_PROMPTS",
    "build_juror_prompt"
]