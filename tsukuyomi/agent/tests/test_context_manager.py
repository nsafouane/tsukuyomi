"""
Unit Tests for Context Manager
=============================

Tests for Utterance, KeyPoint, ContextManager.
"""

import pytest
from tsukuyomi.agent.context_manager import (
    ContextType, Utterance, KeyPoint, Turn, ContextManager,
    extract_topics, extract_keywords
)


class TestUtterance:
    """Tests for Utterance."""
    
    def test_create_utterance(self):
        """Test creating an utterance."""
        utt = Utterance(
            speaker_id="juror_01",
            content="I think he's guilty",
            context_type=ContextType.STATEMENT,
            tick=100
        )
        
        assert utt.speaker_id == "juror_01"
        assert utt.content == "I think he's guilty"
        assert utt.tick == 100
    
    def test_utterance_serialization(self):
        """Test utterance serialization."""
        utt = Utterance(
            speaker_id="s1",
            content="Test",
            tick=100,
            topics=["topic1"]
        )
        
        data = utt.to_dict()
        restored = Utterance.from_dict(data)
        
        assert restored.speaker_id == utt.speaker_id
        assert restored.topics == utt.topics


class TestKeyPoint:
    """Tests for KeyPoint."""
    
    def test_create_key_point(self):
        """Test creating a key point."""
        kp = KeyPoint(
            content="The witness was lying",
            speakers=["juror_01", "juror_02"],
            importance=0.8
        )
        
        assert kp.content == "The witness was lying"
        assert len(kp.speakers) == 2
    
    def test_key_point_serialization(self):
        """Test key point serialization."""
        kp = KeyPoint(content="Test", importance=0.5)
        
        data = kp.to_dict()
        restored = KeyPoint.from_dict(data)
        
        assert restored.content == kp.content


class TestContextManager:
    """Tests for ContextManager."""
    
    def test_create_manager(self):
        """Test creating a context manager."""
        cm = ContextManager(agent_id="test")
        
        assert cm.agent_id == "test"
        assert len(cm.utterances) == 0
    
    def test_add_utterance(self):
        """Test adding an utterance."""
        cm = ContextManager(agent_id="test")
        
        utt = cm.add_utterance(
            speaker_id="juror_01",
            content="I agree",
            tick=100
        )
        
        assert utt.id in cm.utterances
        assert len(cm.speaker_history["juror_01"]) == 1
    
    def test_add_utterance_with_topics(self):
        """Test adding utterance with topics."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(
            speaker_id="s1",
            content="The evidence shows he's guilty",
            topics=["evidence", "guilt"],
            tick=100
        )
        
        assert "evidence" in cm.topic_utterances
        assert "guilt" in cm.topic_utterances
    
    def test_get_recent_utterances(self):
        """Test getting recent utterances."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="First", tick=100)
        cm.add_utterance(speaker_id="s2", content="Second", tick=200)
        cm.add_utterance(speaker_id="s1", content="Third", tick=300)
        
        recent = cm.get_recent_utterances(n=2)
        
        assert len(recent) == 2
        assert recent[0].content == "Third"
    
    def test_get_speaker_utterances(self):
        """Test getting speaker's utterances."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="juror_01", content="A", tick=100)
        cm.add_utterance(speaker_id="juror_02", content="B", tick=200)
        cm.add_utterance(speaker_id="juror_01", content="C", tick=300)
        
        utts = cm.get_speaker_utterances("juror_01")
        
        assert len(utts) == 2
    
    def test_get_topic_utterances(self):
        """Test getting topic utterances."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="About evidence", topics=["evidence"], tick=100)
        cm.add_utterance(speaker_id="s2", content="More evidence", topics=["evidence"], tick=200)
        cm.add_utterance(speaker_id="s3", content="Something else", topics=["other"], tick=300)
        
        utts = cm.get_topic_utterances("evidence")
        
        assert len(utts) == 2
    
    def test_add_key_point(self):
        """Test adding key point."""
        cm = ContextManager(agent_id="test")
        
        utt = cm.add_utterance(speaker_id="s1", content="Key point", tick=100)
        
        kp = cm.add_key_point(
            content="Key point",
            speaker_id="s1",
            utterance_id=utt.id,
            importance=0.8
        )
        
        assert len(cm.key_points) == 1
        assert kp.speakers == ["s1"]
    
    def test_duplicate_key_point(self):
        """Test that duplicate key points update existing."""
        cm = ContextManager(agent_id="test")
        
        utt1 = cm.add_utterance(speaker_id="s1", content="Same point", tick=100)
        utt2 = cm.add_utterance(speaker_id="s2", content="Same point", tick=200)
        
        kp1 = cm.add_key_point(content="Same point", speaker_id="s1", utterance_id=utt1.id)
        kp2 = cm.add_key_point(content="Same point", speaker_id="s2", utterance_id=utt2.id)
        
        # Should be same key point
        assert kp1.id == kp2.id
        assert len(cm.key_points) == 1
        assert len(kp1.speakers) == 2
    
    def test_get_key_points(self):
        """Test getting key points."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="Point 1", tick=100)
        cm.add_key_point(content="Point 1", speaker_id="s1", utterance_id="x", importance=0.5)
        
        cm.add_utterance(speaker_id="s2", content="Point 2", tick=200)
        cm.add_key_point(content="Point 2", speaker_id="s2", utterance_id="y", importance=0.9)
        
        points = cm.get_key_points()
        
        assert len(points) == 2
        assert points[0].content == "Point 2"  # Higher importance first
    
    def test_search_utterances(self):
        """Test searching utterances."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="The evidence is clear", tick=100)
        cm.add_utterance(speaker_id="s2", content="I disagree", tick=200)
        
        results = cm.search_utterances("evidence")
        
        assert len(results) == 1
        assert "evidence" in results[0].content.lower()
    
    def test_get_utterances_since(self):
        """Test getting utterances since tick."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="Before", tick=100)
        cm.add_utterance(speaker_id="s2", content="After", tick=200)
        
        results = cm.get_utterances_since(150)
        
        assert len(results) == 1
        assert results[0].content == "After"
    
    def test_turn_management(self):
        """Test turn management."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="Turn 1", tick=100)
        cm.next_turn()
        cm.add_utterance(speaker_id="s2", content="Turn 2", tick=200)
        
        assert cm.current_turn == 1
    
    def test_round_management(self):
        """Test round management."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="Round 1", tick=100)
        cm.next_round()
        
        assert cm.current_round == 1
        assert cm.current_turn == 0
    
    def test_conversation_summary(self):
        """Test conversation summary."""
        cm = ContextManager(agent_id="test_agent")
        
        cm.add_utterance(speaker_id="s1", content="First", tick=100)
        cm.add_utterance(speaker_id="s2", content="Second", tick=200)
        
        summary = cm.get_conversation_summary()
        
        assert "CONVERSATION SUMMARY" in summary
        assert "Total utterances" in summary
    
    def test_participant_summary(self):
        """Test participant summary."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="juror_01", content="My argument", tick=100)
        
        summary = cm.get_participant_summary("juror_01")
        
        assert "juror_01" in summary
    
    def test_serialization(self):
        """Test serialization."""
        cm = ContextManager(agent_id="test")
        
        cm.add_utterance(speaker_id="s1", content="Test", tick=100)
        
        data = cm.to_dict()
        restored = ContextManager.from_dict(data)
        
        assert restored.agent_id == cm.agent_id
        assert len(restored.utterances) == len(cm.utterances)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        keywords = extract_keywords("The defendant John Smith was at the scene")
        
        assert "John" in keywords or "Smith" in keywords
    
    def test_extract_topics(self):
        """Test topic extraction."""
        topics = extract_topics("The evidence proves he's guilty of murder")
        
        assert "evidence" in topics
        assert "guilt" in topics
    
    def test_extract_topics_no_match(self):
        """Test topic extraction with no matches."""
        topics = extract_topics("Hello world")
        
        assert len(topics) == 0
