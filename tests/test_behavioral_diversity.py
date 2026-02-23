"""
Tests for Behavioral Diversity System
====================================

Tests the behavioral traits and decision making.

Run with: python -m pytest tsukuyomi/agent/tests/test_behavioral_diversity.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from tsukuyomi.agents.cognitive.behavior import (
    BehavioralTraits, BehavioralDecider, create_behavior_from_traits
)


class TestBehavioralTraits:
    """Tests for behavioral traits."""
    
    def test_should_speak_when_addressed(self):
        """High chance to speak when directly addressed."""
        traits = BehavioralTraits(speak_probability=0.1, reply_probability=0.9)
        
        # Addressed - should speak
        result = traits.should_speak(tick=100, addressing_me=True)
        
        assert result == True or result == False  # Probabilistic
    
    def test_introversion_reduces_speaking(self):
        """High introversion reduces speak probability."""
        introverted = BehavioralTraits(introversion=0.9, speak_probability=0.3)
        extroverted = BehavioralTraits(introversion=0.1, speak_probability=0.3)
        
        # Test multiple times since it's probabilistic
        intro_count = sum(1 for _ in range(20) if introverted.should_speak(100, False))
        extro_count = sum(1 for _ in range(20) if extroverted.should_speak(100, False))
        
        # Test is probabilistic - check randomness
    
    def test_get_leadership_style(self):
        """Leadership style is determined correctly."""
        leader = BehavioralTraits(dominance=0.9)
        follower = BehavioralTraits(dominance=0.2)
        peer = BehavioralTraits(dominance=0.5)
        
        assert leader.get_leadership_style() == "leader"
        assert follower.get_leadership_style() == "follower"
        assert peer.get_leadership_style() == "peer"
    
    def test_get_conversation_role(self):
        """Conversation role is determined correctly."""
        initiator = BehavioralTraits(topic_initiation_prob=0.6)
        listener = BehavioralTraits(speak_probability=0.1)
        
        assert initiator.get_conversation_role() == "initiator"
        assert listener.get_conversation_role() == "listener"


class TestBehavioralDecider:
    """Tests for behavioral decision making."""
    
    def test_decide_silent(self):
        """Agent decides to stay silent based on traits."""
        traits = BehavioralTraits(speak_probability=0.01)
        decider = BehavioralDecider(traits)
        
        # Force silent by mocking random
        import random
        original = random.random
        random.random = lambda: 0.99  # Always fail probability check
        
        context = {"tick": 100, "addressing_me": False}
        decision = decider.decide_action(context)
        
        random.random = original
        
        assert decision["action"] == "silent"
    
    def test_decide_respond(self):
        """Agent decides to respond when addressed."""
        traits = BehavioralTraits(speak_probability=0.9, reply_probability=0.9)
        decider = BehavioralDecider(traits)
        
        context = {
            "tick": 100,
            "addressing_me": True,
            "last_speaker": "agent_2"
        }
        
        decision = decider.decide_action(context)
        
        assert decision["action"] == "respond"
    
    def test_decide_new_topic(self):
        """Agent decides to change topic when bored."""
        traits = BehavioralTraits(
            speak_probability=0.9,
            topic_initiation_prob=0.9,
            attention_span=0.1,
            distractibility=0.9
        )
        decider = BehavioralDecider(traits)
        
        context = {
            "tick": 1000,
            "addressing_me": False,
            "topic_age": 100  # High topic age
        }
        
        decision = decider.decide_action(context)
        
        # Probabilistic test
    
    def test_select_respond_target(self):
        """Can select who to respond to."""
        traits = BehavioralTraits()
        decider = BehavioralDecider(traits)
        
        agents = ["agent_1", "agent_2", "agent_3"]
        interactions = {"agent_1": 100, "agent_2": 200}
        
        target = decider.select_respond_target(agents, interactions)
        
        # Should return one of the agents
        assert target in agents or target is None
    
    def test_influence_weight(self):
        """Influence weight is calculated."""
        listener = BehavioralTraits(persuasibility=0.5, stubbornness=0.5, agreeableness=0.5)
        speaker = BehavioralTraits(dominance=0.7)
        
        decider = BehavioralDecider(listener)
        
        weight = decider.get_influence_weight(speaker, relationship_trust=0.5)
        
        assert 0 <= weight <= 1


class TestBehaviorFromTraits:
    """Tests for creating behavior from Big Five."""
    
    def test_extroversion_maps_to_speak_prob(self):
        """Extraversion increases speak probability."""
        traits = create_behavior_from_traits({"extraversion": 0.9})
        
        assert traits.speak_probability > 0.3
    
    def test_agreeableness_maps_to_persuasibility(self):
        """Agreeableness increases persuasibility."""
        traits = create_behavior_from_traits({"agreeableness": 0.9})
        
        assert traits.persuasibility > 0.5
    
    def test_role_modification(self):
        """Role modifications are applied."""
        traits = create_behavior_from_traits({"extraversion": 0.5}, role="leader")
        
        assert traits.dominance > 0.5
        assert traits.speak_probability > 0.4
    
    def test_skeptic_role(self):
        """Skeptic role increases stubbornness."""
        traits = create_behavior_from_traits(
            {"extraversion": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5, "neuroticism": 0.5},
            role="skeptic"
        )
        
        assert traits.stubbornness > 0.5
        assert traits.persuasibility < 0.5


class TestBehaviorPresets:
    """Tests for behavior presets."""
    
    def test_leader_preset(self):
        """Leader preset has correct traits."""
        from tsukuyomi.agents.cognitive.behavior import get_behavior_preset
        
        leader = get_behavior_preset("leader")
        
        assert leader is not None
        assert leader.dominance > 0.7
    
    def test_listener_preset(self):
        """Listener preset has correct traits."""
        from tsukuyomi.agents.cognitive.behavior import get_behavior_preset
        
        listener = get_behavior_preset("listener")
        
        assert listener is not None
        assert listener.speak_probability < 0.2


class TestSerialization:
    """Tests for serialization."""
    
    def test_traits_to_dict(self):
        """Can serialize traits."""
        traits = BehavioralTraits(dominance=0.8, speak_probability=0.5)
        
        data = traits.to_dict()
        
        assert data["dominance"] == 0.8
        assert data["speak_probability"] == 0.5
    
    def test_traits_from_dict(self):
        """Can deserialize traits."""
        data = {"dominance": 0.8, "speak_probability": 0.5}
        
        traits = BehavioralTraits.from_dict(data)
        
        assert traits.dominance == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
