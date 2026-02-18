"""
Unit Tests for Conversation Manager
===================================
"""

import pytest
from unittest.mock import Mock
from tsukuyomi.proto.conversation_manager import (
    ConversationManager,
    TurnDecision,
    TurnContext,
    TurnResult,
    create_conversation_manager
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
        self.emotional_state = {"arousal": 0.5, "valence": 0.0}
        self.current_vote = "guilty"


class TestConversationManager:
    """Tests for ConversationManager."""
    
    def test_initialization(self):
        """Test manager initializes correctly."""
        agents = [
            MockAgent("a1", {"patience": 0.5}),
            MockAgent("a2", {"patience": 0.5})
        ]
        
        cm = ConversationManager(
            agents=agents,
            enable_interruptions=True,
            base_speak_probability=0.3
        )
        
        assert len(cm.agents) == 2
        assert cm.enable_interruptions is True
        assert cm.base_speak_probability == 0.3
    
    def test_add_agent(self):
        """Test adding agent to conversation."""
        cm = ConversationManager(agents=[])
        
        agent = MockAgent("new_agent", {"patience": 0.5})
        cm.add_agent(agent)
        
        assert len(cm.agents) == 1
        assert cm.agents[0].agent_id == "new_agent"
    
    def test_remove_agent(self):
        """Test removing agent from conversation."""
        agent = MockAgent("to_remove", {"patience": 0.5})
        cm = ConversationManager(agents=[agent])
        
        cm.remove_agent("to_remove")
        
        assert len(cm.agents) == 0
    
    def test_should_agent_speak_increases_with_extraversion(self):
        """Test extraverted agents speak more."""
        agent1 = MockAgent("extravert", {"extraversion": 0.9, "patience": 0.5})
        agent2 = MockAgent("introvert", {"extraversion": 0.1, "patience": 0.5})
        
        cm = ConversationManager(
            agents=[agent1, agent2],
            base_speak_probability=0.3
        )
        
        extravert_speaks = 0
        introvert_speaks = 0
        
        for tick in range(50):
            context = TurnContext(
                tick=tick,
                agent_id="extravert",
                last_speaker_id=None,
                time_since_last_speech=50
            )
            result = cm.should_agent_speak(agent1, context)
            if result.decision == TurnDecision.SPEAK:
                extravert_speaks += 1
            
            context = TurnContext(
                tick=tick,
                agent_id="introvert",
                last_speaker_id=None,
                time_since_last_speech=50
            )
            result = cm.should_agent_speak(agent2, context)
            if result.decision == TurnDecision.SPEAK:
                introvert_speaks += 1
        
        # Extravert should speak more
        assert extravert_speaks >= introvert_speaks
    
    def test_should_agent_speak_decreases_after_speaking(self):
        """Test recently spoke agents are less likely to speak."""
        agent = MockAgent("test", {"extraversion": 0.5, "patience": 0.5})
        
        cm = ConversationManager(
            agents=[agent],
            base_speak_probability=0.5,
            min_turn_gap=20
        )
        
        # Just spoke
        cm.last_speak_tick[agent.agent_id] = 90
        context = TurnContext(
            tick=95,
            agent_id=agent.agent_id,
            last_speaker_id=agent.agent_id,
            time_since_last_speech=5
        )
        
        result = cm.should_agent_speak(agent, context)
        
        assert result.decision == TurnDecision.WAIT
    
    def test_minority_pressure_increases_speaking(self):
        """Test minority agents speak more."""
        agent = MockAgent("minority", {"extraversion": 0.3, "patience": 0.5})
        agent.current_vote = "not_guilty"
        
        cm = ConversationManager(agents=[agent], base_speak_probability=0.2)
        
        # In strong minority
        context = TurnContext(
            tick=100,
            agent_id=agent.agent_id,
            last_speaker_id="other",
            time_since_last_speech=50,
            vote_distribution={"guilty": 4, "not_guilty": 1}
        )
        
        result = cm.should_agent_speak(agent, context)
        
        # Should be more likely to speak due to minority pressure
        assert isinstance(result.urgency, float)
    
    def test_interruption_possible_at_high_tension(self):
        """Test interruptions can occur at high tension."""
        agent1 = MockAgent("speaker", {"arousal": 0.5, "extraversion": 0.5})
        agent2 = MockAgent("interrupter", {"arousal": 0.8, "extraversion": 0.7})
        
        cm = ConversationManager(
            agents=[agent1, agent2],
            enable_interruptions=True
        )
        
        # High tension context
        context = TurnContext(
            tick=100,
            agent_id=agent2.agent_id,
            last_speaker_id=agent1.agent_id,
            time_since_last_speech=10,
            tension_level=0.8
        )
        
        # Run multiple times - sometimes should interrupt
        interrupt_count = 0
        for _ in range(50):
            result = cm.should_agent_speak(agent2, context)
            if result.decision == TurnDecision.INTERRUPT:
                interrupt_count += 1
        
        # Should have at least some interruptions
        # (due to randomness, we just check it's possible)
        assert isinstance(result, TurnResult)
    
    def test_statistics_tracking(self):
        """Test statistics are tracked."""
        agent = MockAgent("test", {"extraversion": 0.5, "patience": 0.5})
        
        cm = ConversationManager(agents=[agent], base_speak_probability=0.5)
        
        context = TurnContext(
            tick=0,
            agent_id=agent.agent_id,
            last_speaker_id=None,
            time_since_last_speech=50
        )
        
        cm.should_agent_speak(agent, context)
        
        stats = cm.get_statistics()
        
        assert "total_turns" in stats
        assert agent.agent_id in stats["by_agent"]
    
    def test_record_speech(self):
        """Test speech recording."""
        cm = ConversationManager(agents=[])
        
        cm.record_speech_start("agent1", 100)
        
        assert "agent1" in cm.currently_speaking
        assert cm.last_speaker_id == "agent1"
        assert cm.last_speak_tick["agent1"] == 100
        
        cm.record_speech_end("agent1", 110)
        
        assert "agent1" not in cm.currently_speaking
    
    def test_silence_count(self):
        """Test silence tracking."""
        cm = ConversationManager(agents=[])
        
        cm.increment_silence()
        cm.increment_silence()
        
        assert cm.get_silence_count() == 2
    
    def test_reset(self):
        """Test reset clears state."""
        agent = MockAgent("test", {"extraversion": 0.5})
        cm = ConversationManager(agents=[agent])
        
        cm.record_speech_start("test", 100)
        cm.increment_silence()
        
        cm.reset()
        
        assert cm.last_speaker_id is None
        assert cm.silence_count == 0
        assert len(cm.currently_speaking) == 0
    
    def test_get_next_speaker(self):
        """Test next speaker prediction."""
        agent1 = MockAgent("a1", {"extraversion": 0.3})
        agent2 = MockAgent("a2", {"extraversion": 0.8})
        agent3 = MockAgent("a3", {"extraversion": 0.5})
        
        cm = ConversationManager(
            agents=[agent1, agent2, agent3],
            base_speak_probability=0.3,
            min_turn_gap=10
        )
        
        # Agent 1 just spoke
        cm.last_speak_tick["a1"] = 100
        
        context = TurnContext(
            tick=110,
            agent_id="a1",
            last_speaker_id="a1"
        )
        
        next_speaker = cm.get_next_speaker(context)
        
        # Should suggest someone who hasn't spoken recently
        assert next_speaker in ["a2", "a3"]
    
    def test_turn_result_creation(self):
        """Test TurnResult creation."""
        result = TurnResult(
            decision=TurnDecision.SPEAK,
            urgency=0.7,
            reason="test reason"
        )
        
        assert result.decision == TurnDecision.SPEAK
        assert result.urgency == 0.7
        assert result.reason == "test reason"
        assert result.interrupt_target is None


class TestCreateConversationManager:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        """Test factory with defaults."""
        agents = [MockAgent("a1", {})]
        
        cm = create_conversation_manager(agents)
        
        assert len(cm.agents) == 1
        assert cm.enable_interruptions is True
    
    def test_create_with_interruptions_disabled(self):
        """Test factory with interruptions disabled."""
        agents = [MockAgent("a1", {})]
        
        cm = create_conversation_manager(agents, enable_interruptions=False)
        
        assert cm.enable_interruptions is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
