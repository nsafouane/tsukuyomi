"""
WorkingMemory — Cognitively-bounded active context.
Phase 2 Module 2

Implements Miller's Law: 7 ± 2 chunks.
Refreshed each deliberation cycle from percepts + episodic + semantic.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("WorkingMemory")


@dataclass
class MemoryChunk:
    """A single item in working memory."""

    source: str
    content: Any
    relevance: float

    def to_text(self) -> str:
        """Format for LLM context."""
        if self.source == "percept":
            return self._format_percept()
        elif self.source == "episodic":
            return self._format_episodic()
        else:
            return str(self.content)

    def _format_percept(self) -> str:
        p = self.content
        if hasattr(p, "actor") and p.HasField("actor"):
            return f"[NOW] {p.actor.name} is {p.actor.visible_action_state} ({p.actor.visible_emotional_cue})"
        if hasattr(p, "speech") and p.HasField("speech"):
            addr = " (to you)" if p.speech.is_direct_address else ""
            return f'[NOW] {p.speech.speaker_name} says{addr}: "{p.speech.content}"'
        if hasattr(p, "object") and p.HasField("object"):
            return f"[NOW] You see: {p.object.apparent_type} ({', '.join(p.object.visible_affordances)})"
        return f"[NOW] Percept: {self.content}"

    def _format_episodic(self) -> str:
        mem = self.content
        who = mem.get("who", "someone")
        what = mem.get("what", "did something")
        when = mem.get("when", "?")
        details = mem.get("details", {})
        msg = details.get("message", "")
        if msg:
            return f'[MEMORY tick {when}] {who}: "{msg}"'
        return f"[MEMORY tick {when}] {who} {what}"


class WorkingMemory:
    """
    Active cognitive context. Bounded by Miller's Law.

    Usage:
        wm = WorkingMemory()
        wm.refresh(percepts, episodic_memory, semantic_memory, emotional_state)
        context = wm.to_llm_context()
    """

    MAX_SLOTS = 7

    def __init__(self):
        self.slots: List[MemoryChunk] = []

    @property
    def slot_count(self) -> int:
        return len(self.slots)

    def refresh(
        self,
        percepts: list,
        episodic_memories: list,
        semantic_memory: dict,
        emotional_state: Any,
        current_topics: Optional[List[str]] = None,
    ):
        """
        Select the most relevant items for current working memory.
        Called each deliberation cycle.
        """
        candidates = []
        topics = current_topics or []

        for p in sorted(percepts, key=lambda x: x.salience, reverse=True)[:3]:
            candidates.append(
                MemoryChunk(source="percept", content=p, relevance=p.salience)
            )

        scored_memories = self._score_episodic_memories(
            episodic_memories, topics, emotional_state
        )
        for score, mem in scored_memories[:5]:
            candidates.append(
                MemoryChunk(source="episodic", content=mem, relevance=score)
            )

        perceived_subjects = set()
        for p in percepts:
            if hasattr(p, "actor") and p.HasField("actor"):
                perceived_subjects.add(p.actor.actor_id)
                perceived_subjects.add(p.actor.name)
            if hasattr(p, "speech") and p.HasField("speech"):
                perceived_subjects.add(p.speech.speaker_id)

        for subject in perceived_subjects:
            if subject in semantic_memory:
                for predicate, facts in semantic_memory[subject].items():
                    for fact in facts[:2]:
                        candidates.append(
                            MemoryChunk(
                                source="semantic",
                                content=f"{subject} {predicate} {fact['object']}",
                                relevance=0.4,
                            )
                        )

        candidates.sort(key=lambda c: c.relevance, reverse=True)
        self.slots = candidates[: self.MAX_SLOTS]

    def to_llm_context(self) -> str:
        """Format working memory for LLM prompt."""
        sections = {"percept": [], "episodic": [], "semantic": []}
        for chunk in self.slots:
            sections[chunk.source].append(chunk.to_text())

        parts = [f"WORKING MEMORY ({len(self.slots)}/{self.MAX_SLOTS} active items):"]

        if sections["percept"]:
            parts.append("\n[IMMEDIATE AWARENESS]")
            parts.extend(f"  {line}" for line in sections["percept"])

        if sections["episodic"]:
            parts.append("\n[RELEVANT MEMORIES]")
            parts.extend(f"  {line}" for line in sections["episodic"])

        if sections["semantic"]:
            parts.append("\n[KNOWN FACTS]")
            parts.extend(f"  {line}" for line in sections["semantic"])

        if not any(sections.values()):
            parts.append("  (Mind is blank)")

        return "\n".join(parts)

    def _score_episodic_memories(
        self, memories: list, topics: List[str], emotional_state: Any
    ) -> List[tuple]:
        """Score episodic memories by relevance to current context."""
        scored = []
        for mem in memories:
            mem_text = str(mem.get("details", {}))
            topic_match = sum(1 for t in topics if t.lower() in mem_text.lower())
            topic_score = min(topic_match / max(len(topics), 1), 1.0)

            recency_score = 0.3

            emotion_score = mem.get("emotional_intensity", 0.0) * 0.3

            total = (topic_score * 0.5) + (recency_score * 0.2) + (emotion_score * 0.3)
            scored.append((total, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
