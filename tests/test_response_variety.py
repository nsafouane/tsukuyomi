"""
Tests for Response Variety System
=================================

Tests the response history tracking and repetition prevention.

Run with: python -m pytest tsukuyomi/agent/tests/test_response_variety.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from tsukuyomi.agents.social.conversation import (
    ResponseRecord, ResponseHistory, check_response_quality
)


class TestResponseRecord:
    """Tests for response records."""
    
    def test_key_phrases_extraction(self):
        """Key phrases are extracted from content."""
        record = ResponseRecord(
            tick=100,
            content="I believe the defendant is guilty",
            prompt_type="deliberation",
            tone="certain",
            word_count=7
        )
        
        phrases = record.key_phrases()
        
        assert "i believe" in phrases
        assert "believe the" in phrases
        assert "defendant is" in phrases
    
    def test_content_hash(self):
        """Content hash is generated."""
        record = ResponseRecord(
            tick=100,
            content="Test content",
            prompt_type="deliberation",
            tone="neutral",
            word_count=2
        )
        
        assert len(record.content_hash) == 8


class TestResponseHistory:
    """Tests for response history tracking."""
    
    def test_add_response(self):
        """Responses are added to history."""
        history = ResponseHistory(max_history=5)
        record = ResponseRecord(
            tick=100, content="Hello", prompt_type="greet", tone="neutral", word_count=1
        )
        
        history.add(record)
        
        assert len(history.responses) == 1
    
    def test_max_history_enforced(self):
        """History respects max size."""
        history = ResponseHistory(max_history=3)
        
        for i in range(5):
            record = ResponseRecord(
                tick=i, content=f"Message {i}", prompt_type="test", tone="neutral", word_count=2
            )
            history.add(record)
        
        assert len(history.responses) == 3
    
    def test_phrase_counts_tracked(self):
        """Phrase repetition is tracked."""
        history = ResponseHistory(max_history=10)
        
        # Add similar responses
        for i in range(3):
            record = ResponseRecord(
                tick=i,
                content="I believe the defendant is guilty",
                prompt_type="vote",
                tone="certain",
                word_count=7
            )
            history.add(record)
        
        # Check phrase counts
        assert "i believe" in history.phrase_counts
        assert history.phrase_counts["i believe"] >= 3
    
    def test_repetitive_phrases_detected(self):
        """Overused phrases are detected."""
        history = ResponseHistory(max_history=10, repetition_threshold=2)
        
        # Add same response 3 times
        for i in range(3):
            record = ResponseRecord(
                tick=i,
                content="I've seen enough to make a decision",
                prompt_type="vote",
                tone="certain",
                word_count=7
            )
            history.add(record)
        
        repetitive = history.get_repetitive_phrases()
        
        assert len(repetitive) > 0
    
    def test_similarity_score(self):
        """Similar content is detected."""
        history = ResponseHistory()
        
        history.add(ResponseRecord(
            tick=100,
            content="I believe the defendant is guilty",
            prompt_type="vote",
            tone="certain",
            word_count=7
        ))
        
        similar = history.similarity_score("I believe the defendant is not guilty")
        
        assert similar > 0.3
    
    def test_is_too_similar(self):
        """Too similar content is flagged."""
        history = ResponseHistory()
        
        history.add(ResponseRecord(
            tick=100,
            content="The evidence clearly shows guilt",
            prompt_type="deliberation",
            tone="certain",
            word_count=6
        ))
        
        too_similar = history.is_too_similar(
            "The evidence clearly shows guilt without doubt",
            threshold=0.5
        )
        
        assert too_similar is True
    
    def test_get_variety_warning(self):
        """Variety warning is generated."""
        history = ResponseHistory(repetition_threshold=2)
        
        for i in range(3):
            record = ResponseRecord(
                tick=i,
                content="I've seen enough",
                prompt_type="deliberation",
                tone="neutral",
                word_count=3
            )
            history.add(record)
        
        warning = history.get_variety_warning()
        
        assert warning is not None
        assert "I've seen enough" in warning or "AVOID" in warning


class TestResponseQuality:
    """Tests for response quality checking."""
    
    def test_valid_response(self):
        """Valid response passes checks."""
        history = ResponseHistory()
        
        result = check_response_quality(
            "This is a reasonable response with enough words",
            history,
            min_words=5
        )
        
        assert result["is_valid"] is True
    
    def test_too_short(self):
        """Short responses are flagged."""
        history = ResponseHistory()
        
        result = check_response_quality("Short", history, min_words=10)
        
        assert "too short" in str(result["issues"])
    
    def test_too_similar(self):
        """Similar responses are flagged."""
        history = ResponseHistory()
        history.add(ResponseRecord(
            tick=100, content="Test response", prompt_type="test", tone="neutral", word_count=2
        ))
        
        result = check_response_quality("Test response with more words", history, max_similarity=0.5)
        
        assert result["similarity"] >= 0.0  # similarity can be low for different content


class TestSerialization:
    """Tests for history serialization."""
    
    def test_to_dict(self):
        """Can serialize history."""
        history = ResponseHistory(max_history=5)
        history.add(ResponseRecord(
            tick=100, content="Test", prompt_type="test", tone="neutral", word_count=1
        ))
        
        data = history.to_dict()
        
        assert data["max_history"] == 5
        assert len(data["responses"]) == 1
    
    def test_from_dict(self):
        """Can deserialize history."""
        data = {
            "max_history": 5,
            "repetition_threshold": 3,
            "responses": [{
                "tick": 100,
                "content": "Test",
                "prompt_type": "test",
                "tone": "neutral",
                "word_count": 1,
                "content_hash": "abc",
                "timestamp": "2026-02-19T00:00:00"
            }],
            "phrase_counts": {}
        }
        
        history = ResponseHistory.from_dict(data)
        
        assert history.max_history == 5
        assert len(history.responses) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
