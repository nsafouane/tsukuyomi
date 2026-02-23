"""
Unit Tests for Conversation Manager
===================================
"""

import pytest
from unittest.mock import Mock

from tsukuyomi.agents.social.conversation import (
    ConversationManager,
    TurnDecision,
    TurnContext,
    TurnResult,
    create_conversation_manager,
    ResponseHistory,
    ResponseRecord
)


class MockAgent:
    """Mock agent for testing."""
    def __init__(self, agent_id: str, traits: dict):
        self.agent_id = agent_id
        self.profile = {
            "personality": {
                "traits": traits,
                "big_five": {}
            }
        }


class TestTurnDecision:
    def test_turn_decision_enum(self):
        """Test turn decision enum values."""
        assert TurnDecision.CONTINUE.value == "continue"
        assert TurnDecision.YIELD.value == "yield"
        assert TurnDecision.INTERRUPT.value == "interrupt"
        assert TurnDecision.SILENT.value == "silent"


class TestTurnContext:
    def test_create_context(self):
        """Test creating turn context."""
        ctx = TurnContext(
            current_speaker="agent1",
            last_speaker="agent2",
            turn_count=5,
            time_since_last_speech=10
        )
        
        assert ctx.current_speaker == "agent1"
        assert ctx.last_speaker == "agent2"
        assert ctx.turn_count == 5
        assert ctx.time_since_last_speech == 10


class TestTurnResult:
    def test_create_result(self):
        """Test creating turn result."""
        result = TurnResult(
            decision=TurnDecision.CONTINUE,
            next_speaker="agent1",
            reason="Test"
        )
        
        assert result.decision == TurnDecision.CONTINUE
        assert result.next_speaker == "agent1"
        assert result.reason == "Test"


class TestConversationManager:
    def test_initialization(self):
        """Test manager initialization."""
        participants = ["agent1", "agent2", "agent3"]
        manager = ConversationManager(participants)
        
        assert len(manager.participants) == 3
        assert manager.current_speaker is None
        assert manager.total_turns == 0
    
    def test_request_turn_no_speaker(self):
        """Test requesting turn when no one is speaking."""
        manager = ConversationManager(["agent1", "agent2"])
        ctx = TurnContext(
            current_speaker="",
            last_speaker="",
            turn_count=0,
            time_since_last_speech=0
        )
        
        result = manager.request_turn("agent1", ctx)
        
        assert result.decision == TurnDecision.CONTINUE
        assert result.next_speaker == "agent1"
    
    def test_request_turn_non_participant(self):
        """Test requesting turn for non-participant."""
        manager = ConversationManager(["agent1", "agent2"])
        ctx = TurnContext(
            current_speaker="agent1",
            last_speaker="",
            turn_count=0,
            time_since_last_speech=0
        )
        
        result = manager.request_turn("agent3", ctx)
        
        assert result.decision == TurnDecision.SILENT
    
    def test_end_turn(self):
        """Test ending a turn."""
        manager = ConversationManager(["agent1", "agent2"])
        ctx = TurnContext(
            current_speaker="",
            last_speaker="",
            turn_count=0,
            time_since_last_speech=0
        )
        
        manager.request_turn("agent1", ctx)
        assert manager.current_speaker == "agent1"
        
        manager.end_turn("agent1")
        assert manager.current_speaker is None
    
    def test_tick_advances_silence(self):
        """Test that tick advances silence counter."""
        manager = ConversationManager(["agent1", "agent2"])
        
        assert manager.silence_ticks == 0
        manager.tick()
        assert manager.silence_ticks == 1
        manager.tick()
        assert manager.silence_ticks == 2
    
    def test_get_next_speaker(self):
        """Test getting next speaker."""
        manager = ConversationManager(["agent1", "agent2"])
        
        next_speaker = manager.get_next_speaker()
        assert next_speaker in ["agent1", "agent2"]
    
    def test_record_response(self):
        """Test recording a response."""
        manager = ConversationManager(["agent1", "agent2"])
        
        manager.record_response(
            agent_id="agent1",
            content="Hello world",
            tick=100,
            prompt_type="deliberation",
            tone="neutral"
        )
        
        history = manager.get_response_history("agent1")
        assert history is not None
        assert len(history.responses) == 1
    
    def test_reset_turn_counts(self):
        """Test resetting turn counts."""
        manager = ConversationManager(["agent1", "agent2"])
        ctx = TurnContext(
            current_speaker="",
            last_speaker="",
            turn_count=0,
            time_since_last_speech=0
        )
        
        manager.request_turn("agent1", ctx)
        manager.request_turn("agent1", ctx)
        
        assert manager.turn_counts["agent1"] == 2
        
        manager.reset_turn_counts()
        assert manager.turn_counts["agent1"] == 0
    
    def test_get_stats(self):
        """Test getting statistics."""
        manager = ConversationManager(["agent1", "agent2"])
        
        stats = manager.get_stats()
        
        assert "total_turns" in stats
        assert "current_speaker" in stats
        assert "turn_counts" in stats
        assert "participants" in stats


class TestCreateConversationManager:
    def test_factory_function(self):
        """Test factory function."""
        manager = create_conversation_manager(
            participants=["agent1", "agent2"],
            max_turns_per_speaker=5
        )
        
        assert len(manager.participants) == 2
        assert manager.max_turns_per_speaker == 5
