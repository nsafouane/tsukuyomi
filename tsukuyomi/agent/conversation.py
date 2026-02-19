"""
Conversation Response Tracking
==============================

Tracks agent responses to prevent repetition and ensure variety.
This is a GENERAL system applicable to any social simulation.

Location: tsukuyomi/agent/conversation.py
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger("ResponseHistory")


@dataclass
class ResponseRecord:
    """
    Record of a single agent response.
    
    Tracks content, timing, and characteristics for repetition detection.
    """
    tick: int
    content: str
    prompt_type: str  # "deliberation", "vote", "reaction", etc.
    tone: str
    word_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def content_hash(self) -> str:
        """Hash of content for quick comparison."""
        return hashlib.md5(self.content.lower().encode()).hexdigest()[:8]
    
    def key_phrases(self) -> List[str]:
        """
        Extract key phrases for similarity checking.
        
        Returns 2-3 word n-grams.
        """
        words = self.content.lower().split()
        phrases = []
        
        # Extract 2-word phrases
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")
        
        # Extract 3-word phrases
        for i in range(len(words) - 2):
            phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases
    
    def to_dict(self) -> Dict:
        return {
            "tick": self.tick,
            "content": self.content,
            "content_hash": self.content_hash,
            "prompt_type": self.prompt_type,
            "tone": self.tone,
            "word_count": self.word_count,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ResponseHistory:
    """
    Tracks an agent's recent responses to prevent repetition.
    
    This is a GENERAL system for ensuring response variety in any
    conversational simulation (jury, marketplace, debate, social).
    
    Features:
    - Tracks recent responses with rolling window
    - Detects repetitive phrases
    - Calculates similarity scores
    - Provides warnings for prompt modification
    """
    max_history: int = 10
    repetition_threshold: int = 3  # Max times a phrase can appear
    
    responses: List[ResponseRecord] = field(default_factory=list)
    phrase_counts: Dict[str, int] = field(default_factory=dict)
    
    def add(self, response: ResponseRecord):
        """
        Add a response to history.
        
        Updates phrase counts and trims old responses.
        """
        self.responses.append(response)
        
        # Update phrase counts
        for phrase in response.key_phrases():
            self.phrase_counts[phrase] = self.phrase_counts.get(phrase, 0) + 1
        
        # Trim old responses
        while len(self.responses) > self.max_history:
            removed = self.responses.pop(0)
            # Update phrase counts for removed response
            for phrase in removed.key_phrases():
                if phrase in self.phrase_counts:
                    self.phrase_counts[phrase] -= 1
                    if self.phrase_counts[phrase] <= 0:
                        del self.phrase_counts[phrase]
        
        logger.debug(
            f"Response added: tick={response.tick}, hash={response.content_hash}, "
            f"history_size={len(self.responses)}"
        )
    
    def get_repetitive_phrases(self) -> List[str]:
        """
        Get phrases that have been used too often.
        
        Returns phrases with count >= repetition_threshold.
        """
        return [
            phrase for phrase, count in self.phrase_counts.items()
            if count >= self.repetition_threshold
        ]
    
    def similarity_score(self, new_content: str) -> float:
        """
        Calculate how similar new content is to recent responses.
        
        Returns value 0.0-1.0 where 1.0 = identical to a recent response.
        """
        if not self.responses:
            return 0.0
        
        # Extract phrases from new content
        new_phrases = set()
        words = new_content.lower().split()
        for i in range(len(words) - 1):
            new_phrases.add(f"{words[i]} {words[i+1]}")
        for i in range(len(words) - 2):
            new_phrases.add(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Check overlap with recent responses
        overlaps = []
        for resp in self.responses[-5:]:  # Check last 5
            resp_phrases = set(resp.key_phrases())
            overlap = len(new_phrases & resp_phrases)
            total = len(new_phrases | resp_phrases)
            similarity = overlap / total if total > 0 else 0
            overlaps.append(similarity)
        
        return max(overlaps) if overlaps else 0.0
    
    def is_too_similar(self, new_content: str, threshold: float = 0.6) -> bool:
        """
        Check if new content is too similar to recent responses.
        
        Args:
            new_content: Proposed new response
            threshold: Similarity threshold (0.0-1.0)
        
        Returns:
            True if too similar, False if sufficiently different
        """
        return self.similarity_score(new_content) > threshold
    
    def get_variety_warning(self) -> Optional[str]:
        """
        Get a warning about repetitive phrases for prompt injection.
        
        Returns None if no repetition detected.
        """
        repetitive = self.get_repetitive_phrases()
        if not repetitive:
            return None
        
        # Get top 3 most repetitive
        sorted_phrases = sorted(
            repetitive,
            key=lambda p: self.phrase_counts.get(p, 0),
            reverse=True
        )[:3]
        
        return (
            f"AVOID these overused phrases: {', '.join(sorted_phrases)}. "
            "Express the same ideas with different wording."
        )
    
    def clear(self):
        """Clear history and phrase counts."""
        self.responses.clear()
        self.phrase_counts.clear()
    
    def to_dict(self) -> Dict:
        """Serialize for persistence."""
        return {
            "max_history": self.max_history,
            "repetition_threshold": self.repetition_threshold,
            "responses": [r.to_dict() for r in self.responses],
            "phrase_counts": dict(self.phrase_counts)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ResponseHistory':
        """Deserialize from dict."""
        history = cls(
            max_history=data.get("max_history", 10),
            repetition_threshold=data.get("repetition_threshold", 3)
        )
        
        for resp_data in data.get("responses", []):
            resp = ResponseRecord(
                tick=resp_data["tick"],
                content=resp_data["content"],
                prompt_type=resp_data["prompt_type"],
                tone=resp_data["tone"],
                word_count=resp_data["word_count"]
            )
            history.responses.append(resp)
        
        history.phrase_counts = data.get("phrase_counts", {})
        
        return history


# ========================
# Repetition Prevention
# ========================

def generate_variety_prompt_modifier(
    history: ResponseHistory,
    style_guidelines: Optional[str] = None
) -> str:
    """
    Generate prompt modifier to encourage response variety.
    
    This injects warnings about repetition and suggestions for variety.
    
    Args:
        history: Response history to analyze
        style_guidelines: Optional style guidelines to include
    
    Returns:
        Prompt modifier string
    """
    parts = []
    
    # Add repetition warning
    warning = history.get_variety_warning()
    if warning:
        parts.append(f"\n## VARIETY WARNING\n{warning}")
    
    # Add variety encouragement
    if len(history.responses) > 3:
        parts.append(
            "\n## RESPONSE VARIETY\n"
            "You've already spoken several times. Try to:\n"
            "- Use different sentence structures\n"
            "- Vary your vocabulary\n"
            "- Bring up new points rather than repeating old ones\n"
            "- Reference what others have said to build on the conversation"
        )
    
    if style_guidelines:
        parts.append(f"\n## STYLE GUIDELINES\n{style_guidelines}")
    
    return "\n".join(parts)


def check_response_quality(
    content: str,
    history: ResponseHistory,
    min_words: int = 5,
    max_similarity: float = 0.7
) -> Dict:
    """
    Check if a response meets quality standards.
    
    Returns dict with:
    - is_valid: bool
    - issues: List[str]
    - similarity: float
    """
    issues = []
    
    # Check length
    word_count = len(content.split())
    if word_count < min_words:
        issues.append(f"Response too short ({word_count} words, min {min_words})")
    
    # Check similarity
    similarity = history.similarity_score(content)
    if similarity > max_similarity:
        issues.append(f"Response too similar to recent responses ({similarity:.0%})")
    
    # Check for empty content
    if not content.strip():
        issues.append("Response is empty")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "similarity": similarity,
        "word_count": word_count
    }
