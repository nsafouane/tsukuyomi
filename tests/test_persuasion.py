"""
Unit Tests for Persuasion Engine
=================================

Tests for Argument, PersuasionProfile, PersuasionEngine.
"""

import pytest
from tsukuyomi.agents.social.persuasion import (
    PersuasionStrategy,
    ArgumentStrength,
    Argument,
    PersuasionAttempt,
    PersuasionProfile,
    PersuasionEngine,
    create_persuasion_profile_from_personality,
    argument_strength_category
)


class TestArgument:
    """Tests for Argument dataclass."""
    
    def test_create_argument(self):
        """Test creating a basic argument."""
        arg = Argument(
            claim="The defendant is guilty",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="juror_01"
        )
        
        assert arg.claim == "The defendant is guilty"
        assert arg.strategy == PersuasionStrategy.LOGIC
        assert arg.speaker_id == "juror_01"
        assert arg.id is not None
    
    def test_argument_serialization(self):
        """Test argument to_dict/from_dict."""
        arg = Argument(
            claim="Test claim",
            strategy=PersuasionStrategy.EMOTION,
            evidence_ids=["e1", "e2"],
            target_belief_id="b1",
            speaker_id="s1",
            tick=100,
            strength_score=0.7,
            confidence=0.8
        )
        
        data = arg.to_dict()
        restored = Argument.from_dict(data)
        
        assert restored.claim == arg.claim
        assert restored.strategy == arg.strategy
        assert restored.evidence_ids == arg.evidence_ids
        assert restored.strength_score == arg.strength_score


class TestPersuasionAttempt:
    """Tests for PersuasionAttempt dataclass."""
    
    def test_persuasion_attempt_effective(self):
        """Test was_effective property."""
        attempt = PersuasionAttempt(
            initial_confidence=0.5,
            final_confidence=0.7,
            change=0.2  # Explicitly set change
        )
        
        assert attempt.was_effective is True
        assert attempt.direction == "strengthened"
    
    def test_persuasion_attempt_ineffective(self):
        """Test ineffective attempt."""
        attempt = PersuasionAttempt(
            initial_confidence=0.5,
            final_confidence=0.52,
            change=0.005  # Small change
        )
        
        assert attempt.was_effective is False
        assert attempt.direction == "unchanged"
    
    def test_persuasion_attempt_weakened(self):
        """Test weakened direction."""
        attempt = PersuasionAttempt(
            initial_confidence=0.7,
            final_confidence=0.5,
            change=-0.2  # Negative change
        )
        
        assert attempt.direction == "weakened"


class TestPersuasionProfile:
    """Tests for PersuasionProfile."""
    
    def test_create_profile(self):
        """Test creating a profile."""
        profile = PersuasionProfile(agent_id="test")
        
        assert profile.agent_id == "test"
        assert len(profile.strategy_preferences) == 8
        assert profile.base_resistance == 0.5
    
    def test_get_preferred_strategy(self):
        """Test getting preferred strategy."""
        profile = PersuasionProfile(agent_id="test")
        profile.strategy_preferences[PersuasionStrategy.EMOTION] = 0.9
        
        assert profile.get_preferred_strategy() == PersuasionStrategy.EMOTION
    
    def test_get_weakest_resistance(self):
        """Test getting weakest resistance strategy."""
        profile = PersuasionProfile(agent_id="test")
        profile.strategy_resistance[PersuasionStrategy.LOGIC] = 0.1
        
        assert profile.get_weakest_resistance() == PersuasionStrategy.LOGIC
    
    def test_success_rate(self):
        """Test persuasion success rate."""
        profile = PersuasionProfile()
        profile.successful_persuasions = 7
        profile.failed_persuasions = 3
        
        assert abs(profile.agents.social.persuasion_success_rate - 0.7) < 0.001
    
    def test_resistance_rate(self):
        """Test resistance rate."""
        profile = PersuasionProfile()
        profile.times_persuaded = 2
        profile.times_resisted = 8
        
        assert abs(profile.resistance_rate - 0.8) < 0.001
    
    def test_profile_serialization(self):
        """Test profile serialization."""
        profile = PersuasionProfile(agent_id="test")
        profile.base_resistance = 0.7
        profile.successful_persuasions = 5
        
        data = profile.to_dict()
        restored = PersuasionProfile.from_dict(data)
        
        assert restored.agent_id == profile.agent_id
        assert restored.base_resistance == profile.base_resistance
        assert restored.successful_persuasions == profile.successful_persuasions


class TestPersuasionEngine:
    """Tests for PersuasionEngine."""
    
    def test_create_engine(self):
        """Test creating an engine."""
        engine = PersuasionEngine(agent_id="test")
        
        assert engine.agent_id == "test"
        assert len(engine.arguments) == 0
    
    def test_create_argument(self):
        """Test creating an argument."""
        engine = PersuasionEngine(agent_id="speaker")
        
        arg = engine.create_argument(
            claim="Test claim",
            strategy=PersuasionStrategy.LOGIC,
            tick=100
        )
        
        assert arg.id in engine.arguments
        assert len(engine.profile.arguments_made) == 1
    
    def test_calculate_persuasion_effect_supporting(self):
        """Test persuasion effect with supporting argument."""
        engine = PersuasionEngine(agent_id="listener")
        engine.profile.base_resistance = 0.1  # Low resistance
        
        arg = Argument(
            claim="Support",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="speaker",
            strength_score=0.8,
            confidence=0.8
        )
        
        new_conf, attempt = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.5,
            tick=100
        )
        
        assert new_conf >= 0.5  # Should increase
        assert attempt.was_effective
    
    def test_calculate_persuasion_effect_resisted(self):
        """Test persuasion effect with high resistance."""
        engine = PersuasionEngine(agent_id="listener")
        engine.profile.base_resistance = 1.0  # Maximum resistance
        engine.profile.strategy_resistance[PersuasionStrategy.LOGIC] = 1.0
        
        arg = Argument(
            claim="Support",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="speaker",
            strength_score=0.3,
            confidence=0.3
        )
        
        new_conf, attempt = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.5,
            tick=100
        )
        
        # With maximum resistance and weak argument, should have minimal effect
        assert abs(new_conf - 0.5) < 0.15  # Less than 15% change
    
    def test_core_belief_resistance(self):
        """Test that core beliefs are harder to change."""
        engine = PersuasionEngine(agent_id="listener")
        engine.profile.base_resistance = 0.3
        
        arg = Argument(
            claim="Challenge",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="speaker",
            strength_score=0.7,
            confidence=0.7
        )
        
        # Normal belief
        _, attempt1 = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.7,
            belief_is_core=False,
            tick=100
        )
        
        # Core belief
        _, attempt2 = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.7,
            belief_is_core=True,
            tick=100
        )
        
        assert abs(attempt2.change) < abs(attempt1.change)
    
    def test_strong_belief_resistance(self):
        """Test that strong beliefs are harder to change."""
        engine = PersuasionEngine(agent_id="listener")
        
        arg = Argument(
            claim="Challenge",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="speaker",
            strength_score=0.6,
            confidence=0.6
        )
        
        # Moderate belief
        _, attempt1 = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.5,
            tick=100
        )
        
        # Strong belief
        _, attempt2 = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="listener",
            belief_confidence=0.9,
            tick=100
        )
        
        # Strong belief should have less relative change
        assert "strong_belief" in attempt2.resistance_factors
    
    def test_select_best_strategy(self):
        """Test strategy selection."""
        engine = PersuasionEngine(agent_id="test")
        engine.profile.strategy_preferences[PersuasionStrategy.EMOTION] = 0.9
        engine.profile.strategy_resistance[PersuasionStrategy.EMOTION] = 0.1
        
        best = engine.select_best_strategy(
            listener_id="other",
            belief_confidence=0.5
        )
        
        # Should prefer emotion due to high preference and low resistance
        assert best == PersuasionStrategy.EMOTION
    
    def test_relationship_effect(self):
        """Test that relationships affect persuasion."""
        engine = PersuasionEngine(agent_id="listener")
        
        # High trust relationship
        engine.update_relationship("trusted_speaker", 0.5)  # 0.5 + 0.5 = 1.0
        
        arg_trusted = Argument(
            claim="Trust me",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="trusted_speaker",
            strength_score=0.7,
            confidence=0.7
        )
        
        arg_stranger = Argument(
            claim="Trust me",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="stranger",
            strength_score=0.7,
            confidence=0.7
        )
        
        _, attempt_trusted = engine.calculate_persuasion_effect(
            argument=arg_trusted,
            listener_id="listener",
            belief_confidence=0.5,
            tick=100
        )
        
        _, attempt_stranger = engine.calculate_persuasion_effect(
            argument=arg_stranger,
            listener_id="listener",
            belief_confidence=0.5,
            tick=100
        )
        
        # Trusted should be more effective
        assert abs(attempt_trusted.change) >= abs(attempt_stranger.change)
    
    def test_update_relationship(self):
        """Test relationship updates."""
        engine = PersuasionEngine(agent_id="test")
        
        engine.update_relationship("other", 0.3)
        assert abs(engine.get_relationship("other") - 0.8) < 0.001
        
        engine.update_relationship("other", -0.5)
        assert abs(engine.get_relationship("other") - 0.3) < 0.001
    
    def test_get_statistics(self):
        """Test statistics generation."""
        engine = PersuasionEngine(agent_id="test")
        engine.profile.successful_persuasions = 5
        engine.profile.failed_persuasions = 5
        
        stats = engine.get_statistics()
        
        assert stats["agent_id"] == "test"
        assert abs(stats["persuasion_success_rate"] - 0.5) < 0.001
    
    def test_effectiveness_report(self):
        """Test effectiveness report generation."""
        engine = PersuasionEngine(agent_id="test_agent")
        
        report = engine.get_argument_effectiveness_report()
        
        assert "test_agent" in report
        assert "STRATEGY PREFERENCES" in report
    
    def test_serialization(self):
        """Test engine serialization."""
        engine = PersuasionEngine(agent_id="test")
        engine.profile.base_resistance = 0.7
        engine.update_relationship("other", 0.3)
        
        engine.create_argument(
            claim="Test",
            strategy=PersuasionStrategy.LOGIC,
            tick=100
        )
        
        data = engine.to_dict()
        restored = PersuasionEngine.from_dict(data)
        
        assert restored.agent_id == engine.agent_id
        assert restored.profile.base_resistance == engine.profile.base_resistance
        assert len(restored.arguments) == len(engine.arguments)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_profile_from_personality(self):
        """Test creating profile from personality traits."""
        profile = create_persuasion_profile_from_personality({
            "neuroticism": 0.8,
            "agreeableness": 0.3,
            "conscientiousness": 0.7,
            "openness": 0.5
        })
        
        # High neuroticism + low agreeableness = higher resistance
        assert profile.base_resistance > 0.4
        
        # High conscientiousness = prefers logic
        assert profile.strategy_preferences[PersuasionStrategy.LOGIC] > 0.5
    
    def test_argument_strength_category(self):
        """Test argument strength categorization."""
        assert argument_strength_category(0.9) == ArgumentStrength.VERY_STRONG
        assert argument_strength_category(0.7) == ArgumentStrength.STRONG
        assert argument_strength_category(0.5) == ArgumentStrength.MODERATE
        assert argument_strength_category(0.3) == ArgumentStrength.WEAK
        assert argument_strength_category(0.1) == ArgumentStrength.VERY_WEAK
