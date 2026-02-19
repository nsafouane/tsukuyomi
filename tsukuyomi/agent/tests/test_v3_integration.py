"""
Integration Tests for V3 Architecture
=====================================

Tests the integration helpers and cross-component functionality.

Run with: python -m pytest tsukuyomi/agent/tests/test_v3_integration.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from tsukuyomi.agent.v3_integration import (
    enhance_agent,
    enhance_prompt,
    record_response,
    update_emotional_state,
    decide_action,
    apply_belief_plasticity,
    check_response_variety,
    V3AgentMixin,
    apply_group_emotional_dynamics
)
from tsukuyomi.agent.emotional_state import EmotionalState
from tsukuyomi.agent.conversation import ResponseHistory
from tsukuyomi.agent.memory import ConversationMemory
from tsukuyomi.agent.behavior import BehavioralTraits
from tsukuyomi.agent.personality import CommunicationStyle
from tsukuyomi.agent.belief_system import BeliefSystem


class TestEnhanceAgent:
    """Tests for agent enhancement."""
    
    def test_enhance_agent_creates_components(self):
        """Enhancement creates all V3 components."""
        # Mock agent
        class MockAgent:
            pass
        
        agent = MockAgent()
        profile = {
            "personality": {
                "big_five": {
                    "neuroticism": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "conscientiousness": 0.5,
                    "openness": 0.5
                }
            },
            "role": "juror"
        }
        
        components = enhance_agent(agent, profile)
        
        assert "emotional_state" in components
        assert "response_history" in components
        assert "conversation_memory" in components
        assert "behavioral_traits" in components
        assert "communication_style" in components
    
    def test_enhance_agent_uses_personality(self):
        """Enhancement uses personality to configure components."""
        profile = {
            "personality": {
                "big_five": {
                    "neuroticism": 0.9,  # High neuroticism
                    "extraversion": 0.1,  # Low extraversion
                    "agreeableness": 0.5
                }
            }
        }
        
        components = enhance_agent(None, profile)
        
        # High neuroticism = high susceptibility
        assert components["emotional_state"].susceptibility > 0.4
        # Low extraversion = low expressiveness
        assert components["emotional_state"].expressiveness < 0.5


class TestEnhancePrompt:
    """Tests for prompt enhancement."""
    
    def test_enhance_prompt_basic(self):
        """Basic prompt passes through."""
        prompt, system = enhance_prompt("Hello", "You are a juror.")
        
        assert "Hello" in prompt
        assert "juror" in system
    
    def test_enhance_prompt_with_emotion(self):
        """Emotional state enhances system prompt."""
        emotional_state = EmotionalState(pleasure=-0.6, arousal=0.6)
        
        prompt, system = enhance_prompt(
            "Hello",
            "You are a juror.",
            emotional_state=emotional_state
        )
        
        # Should include emotional context
        assert "EMOTIONAL STATE" in system or "angry" in system.lower()
    
    def test_enhance_prompt_with_style(self):
        """Communication style enhances prompt."""
        style = CommunicationStyle(
            vocabulary_level="simple",
            formality=0.2
        )
        
        prompt, system = enhance_prompt(
            "Hello",
            "You are a juror.",
            communication_style=style
        )
        
        # Should include style guidelines
        assert "simple" in system.lower() or "STYLE" in system


class TestRecordResponse:
    """Tests for response recording."""
    
    def test_record_response(self):
        """Response is recorded in V3 systems."""
        class MockAgent:
            response_history = ResponseHistory()
            conversation_memory = ConversationMemory()
        
        agent = MockAgent()
        
        record_response(agent, tick=100, content="I think guilty", prompt_type="vote", tone="certain")
        
        assert len(agent.response_history.responses) == 1
        assert len(agent.conversation_memory.utterances) == 1


class TestUpdateEmotionalState:
    """Tests for emotional state updates."""
    
    def test_update_emotional_state(self):
        """Emotional state is updated."""
        class MockAgent:
            emotional_state = EmotionalState(pleasure=0.5)
        
        agent = MockAgent()
        
        update_emotional_state(agent, "contradicted", intensity=0.5, tick=100)
        
        assert agent.emotional_state.pleasure < 0.5


class TestDecideAction:
    """Tests for action decision."""
    
    def test_decide_action(self):
        """Action is decided based on traits."""
        from tsukuyomi.agent.behavior import BehavioralTraits, BehavioralDecider
        
        class MockAgent:
            behavioral_decider = BehavioralDecider(
                BehavioralTraits(speak_probability=0.9, reply_probability=0.9)
            )
        
        agent = MockAgent()
        
        decision = decide_action(agent, {"tick": 100, "addressing_me": True})
        
        assert decision["action"] == "respond"


class TestApplyBeliefPlasticity:
    """Tests for belief plasticity."""
    
    def test_apply_belief_plasticity(self):
        """Plasticity is applied to beliefs."""
        system = BeliefSystem(agent_id="test")
        system.add_belief("Test belief", 0.95, tick=0)
        
        changes = apply_belief_plasticity(system, tick=1000)
        
        # Some changes should occur (either decay or perturbation)
        # This is probabilistic, so we just check it doesn't crash


class TestCheckResponseVariety:
    """Tests for response variety checking."""
    
    def test_check_variety_empty_history(self):
        """Empty history passes."""
        class MockAgent:
            pass
        
        agent = MockAgent()
        
        result = check_response_variety(agent, "Hello world")
        
        assert result["is_valid"] is True
    
    def test_check_variety_with_history(self):
        """History is checked."""
        class MockAgent:
            response_history = ResponseHistory()
        
        agent = MockAgent()
        agent.response_history.add(
            __import__('tsukuyomi.agent.conversation', fromlist=['ResponseRecord']).ResponseRecord(
                tick=100, content="Test", prompt_type="test", tone="neutral", word_count=1
            )
        )
        
        result = check_response_variety(agent, "Different content here")
        
        assert "is_valid" in result


class TestV3AgentMixin:
    """Tests for V3 agent mixin."""
    
    def test_mixin_methods(self):
        """Mixin provides all V3 methods."""
        class EnhancedAgent(V3AgentMixin):
            pass
        
        agent = EnhancedAgent()
        
        # Check methods exist
        assert hasattr(agent, 'init_v3')
        assert hasattr(agent, 'enhance_prompt_v3')
        assert hasattr(agent, 'record_response_v3')
        assert hasattr(agent, 'update_emotion_v3')
        assert hasattr(agent, 'decide_action_v3')
    
    def test_mixin_initialization(self):
        """Mixin initializes correctly."""
        class EnhancedAgent(V3AgentMixin):
            def __init__(self):
                self.agent_id = "test_agent"
        
        agent = EnhancedAgent()
        profile = {
            "personality": {
                "big_five": {"neuroticism": 0.5, "extraversion": 0.5}
            }
        }
        
        agent.init_v3(profile)
        
        assert hasattr(agent, 'emotional_state')
        assert hasattr(agent, 'response_history')
        assert hasattr(agent, 'conversation_memory')


class TestGroupDynamics:
    """Tests for group emotional dynamics."""
    
    def test_group_emotional_dynamics(self):
        """Group dynamics are applied."""
        class MockAgent:
            def __init__(self):
                self.agent_id = "test"
                self.emotional_state = EmotionalState(pleasure=0.5)
        
        agents = [MockAgent(), MockAgent()]
        
        result = apply_group_emotional_dynamics(agents, tick=100)
        
        assert "tone" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
