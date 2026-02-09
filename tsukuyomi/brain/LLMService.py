import logging
import asyncio
from typing import Dict, List
import json
import os
import aiohttp

logger = logging.getLogger("LLMService")


class LLMService:
    """
    Bridge to Groq Cloud for Agent Deliberation.
    Optimized for Groq Free Tier limits.
    """

    # Groq Free Tier Limits (approx for Llama 3 70B):
    # RPM: 30 | TPM: 6000 | RPD: 14400
    # To stay safe with 5 concurrent agents, we use a global lock and 2.5s delay.
    _semaphore = asyncio.Semaphore(1)
    _last_request_time = 0
    _cooldown = 2.5

    # Groq API Configuration
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-3.3-70b-versatile"  # High-reasoning model for the experiment

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
        Enhanced LLM prompt with Phase 2 cognitive modules.
        """
        async with LLMService._semaphore:
            now = asyncio.get_event_loop().time()
            elapsed = now - LLMService._last_request_time
            if elapsed < LLMService._cooldown:
                await asyncio.sleep(LLMService._cooldown - elapsed)

            for attempt in range(3):
                try:
                    logger.info(
                        f"🧠 [Gemini] Requesting deliberation for {profile['name']} ({reason}, Attempt {attempt + 1})..."
                    )

                    prompt = f"""
                    CONTEXT:
                    You are simulating an AI agent in 'The Narrative Loom'.
                    Identity: {profile["name"]}
                    Backstory: {profile.get("backstory", "")}
                    
                    {beliefs}
                    
                    {relationships}
                    
                    {emotional_modifier}
                    
                    {working_memory}
                    
                    TASK:
                    Based on your beliefs, emotional state, relationships, and working memory, decide your next action.
                    Trigger: {reason}
                    
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
                    }}
                    """

                    proc = await asyncio.create_subprocess_exec(
                        "gemini",
                        "-m",
                        "gemini-3-flash-preview",
                        "-p",
                        prompt,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    LLMService._last_request_time = asyncio.get_event_loop().time()

                    if proc.returncode == 0:
                        raw_output = stdout.decode().strip()
                        if "```json" in raw_output:
                            raw_output = (
                                raw_output.split("```json")[1].split("```")[0].strip()
                            )
                        elif "```" in raw_output:
                            raw_output = (
                                raw_output.split("```")[1].split("```")[0].strip()
                            )

                        return json.loads(raw_output)

                    err_msg = stderr.decode()
                    if "429" in err_msg or "exhausted" in err_msg.lower():
                        wait_time = (attempt + 1) * 5
                        logger.warning(
                            f"⚠️ Gemini Rate Limited. Waiting {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    logger.error(f"Gemini CLI Error: {err_msg}")

                except Exception as e:
                    logger.error(f"Gemini Deliberation attempt {attempt} failed: {e}")
                    await asyncio.sleep(2)

            return {
                "thought": "I am processing environment carefully.",
                "action": "IDLE",
                "params": {"duration": "10"},
            }

    @staticmethod
    async def generate_plan(
        profile: Dict,
        memories: List[Dict],
        semantic_facts: List[str],
        world_state_summary: str,
    ) -> Dict:
        """
        Ask Gemini CLI to generate an action plan with rate limiting and backoff.
        """
        async with LLMService._semaphore:
            # Respect cooldown to avoid Gemini 429s
            now = asyncio.get_event_loop().time()
            elapsed = now - LLMService._last_request_time
            if elapsed < LLMService._cooldown:
                await asyncio.sleep(LLMService._cooldown - elapsed)

            for attempt in range(3):
                try:
                    logger.info(
                        f"🧠 [Gemini] Requesting deliberation for {profile['name']} (Attempt {attempt + 1})..."
                    )

                    prompt = f"""
                    CONTEXT:
                    You are simulating an AI agent in 'The Narrative Loom'.
                    Identity: {profile["name"]}
                    Backstory: {profile["backstory"]}
                    Current Stance: {profile["stance"]}
                    
                    WORLD KNOWLEDGE (Semantic):
                    {json.dumps(semantic_facts, indent=2)}
                    
                    ENVIRONMENT:
                    {world_state_summary}
                    
                    RECENT MEMORIES (Episodic):
                    {json.dumps(memories, indent=2)}
                    
                    TASK:
                    Based on your backstory and recent events, decide your next action.
                    Allowed Actions: 
                    - MOVE (params: destination)
                    - EMOTE (params: type="speak", message="your words") - Use this to talk to others.
                    - IDLE (params: duration)
                    
                    RESPONSE FORMAT (JSON only):
                    {{
                        "thought": "your internal reasoning",
                        "action": "MOVE|EMOTE|IDLE",
                        "params": {{"key": "value"}}
                    }}
                    """

                    # Call Gemini CLI
                    proc = await asyncio.create_subprocess_exec(
                        "gemini",
                        "-m",
                        "gemini-3-flash-preview",
                        "-p",
                        prompt,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    LLMService._last_request_time = asyncio.get_event_loop().time()

                    if proc.returncode == 0:
                        raw_output = stdout.decode().strip()
                        # Clean markdown if present
                        if "```json" in raw_output:
                            raw_output = (
                                raw_output.split("```json")[1].split("```")[0].strip()
                            )
                        elif "```" in raw_output:
                            raw_output = (
                                raw_output.split("```")[1].split("```")[0].strip()
                            )

                        return json.loads(raw_output)

                    err_msg = stderr.decode()
                    if "429" in err_msg or "exhausted" in err_msg.lower():
                        wait_time = (attempt + 1) * 5
                        logger.warning(
                            f"⚠️ Gemini Rate Limited. Waiting {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    logger.error(f"Gemini CLI Error: {err_msg}")

                except Exception as e:
                    logger.error(f"Gemini Deliberation attempt {attempt} failed: {e}")
                    await asyncio.sleep(2)

        # Fallback
        return {
            "thought": "I am processing the environment carefully.",
            "action": "IDLE",
            "params": {"duration": "10"},
        }
