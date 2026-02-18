"""
Unit Tests for Personality-Weighted Persuasion
============================================
"""

import pytest
from tsukuyomi.agent.persuasion import (
    PersuasionEngine,
    PersuasionStrategy,
    Argument,
    calculate_persuasion_effectiveness_by_personality,
    calculate_persuasion_resistance_by_personality,
    get_personality_persuasion_summary,
    apply_personality_to_persuasion_engine,
    ARGUMENT_EFFECTIVENESS_BY_PERSONALITY
)


class TestPersonalityWeightedPersuasion:
    """Tests for personality-weighted persuasion functions."""
    
    def test_argument_effectiveness_mapping_exists(self):
        """Test that all strategies have effectiveness mappings."""
        for strategy in PersuasionStrategy:
            assert strategy.value in ARGUMENT_EFFECTIVENESS_BY_PERSONALITY
    
    def test_logic_effectiveness_high_openness(self):
        """Test logic is more effective on open agents."""
        personality = {"openness": 0.9, "conscientiousness": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.LOGIC
        )
        
        # High openness = more susceptible to logic
        assert effectiveness > 0.5
    
    def test_logic_effectiveness_low_openness(self):
        """Test logic is less effective on closed agents."""
        personality = {"openness": 0.1, "conscientiousness": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.LOGIC
        )
        
        # Low openness = less susceptible to logic
        assert effectiveness < 0.5
    
    def test_emotion_effectiveness_high_neuroticism(self):
        """Test emotion is more effective on neurotic agents."""
        personality = {"neuroticism": 0.9, "agreeableness": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.EMOTION
        )
        
        # High neuroticism = more emotional, more susceptible
        assert effectiveness > 0.5
    
    def test_emotion_effectiveness_low_neuroticism(self):
        """Test emotion is less effective on stable agents."""
        personality = {"neuroticism": 0.1, "agreeableness": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.EMOTION
        )
        
        # Low neuroticism = less emotional
        assert effectiveness < 0.5
    
    def test_authority_effectiveness_low_openness(self):
        """Test authority is more effective on closed agents."""
        personality = {"openness": 0.1, "conscientiousness": 0.8}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.AUTHORITY
        )
        
        # Low openness + high conscientiousness = more deferential to authority
        assert effectiveness > 0.4
    
    def test_social_proof_effectiveness_agreeableness(self):
        """Test social proof is effective on agreeable agents."""
        personality = {"agreeableness": 0.9, "extraversion": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.SOCIAL_PROOF
        )
        
        # High agreeableness = follows group
        assert effectiveness > 0.5
    
    def test_liking_effectiveness_agreeableness(self):
        """Test liking is effective on agreeable agents."""
        personality = {"agreeableness": 0.9, "extraversion": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.LIKING
        )
        
        # High agreeableness = values relationships
        assert effectiveness > 0.5
    
    def test_scarcity_effectiveness_neuroticism(self):
        """Test scarcity is effective on neurotic agents."""
        personality = {"neuroticism": 0.9, "conscientiousness": 0.5}
        
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            personality, PersuasionStrategy.SCARCITY
        )
        
        # High neuroticism = fears missing out
        assert effectiveness > 0.5
    
    def test_effectiveness_bounds(self):
        """Test effectiveness is always in valid range."""
        personality = {"openness": 0.5, "conscientiousness": 0.5}
        
        for strategy in PersuasionStrategy:
            effectiveness = calculate_persuasion_effectiveness_by_personality(
                personality, strategy
            )
            
            assert 0.1 <= effectiveness <= 0.9, f"{strategy} out of bounds: {effectiveness}"
    
    def test_resistance_bounds(self):
        """Test resistance is always in valid range."""
        personality = {"openness": 0.5, "conscientiousness": 0.5}
        
        for strategy in PersuasionStrategy:
            resistance = calculate_persuasion_resistance_by_personality(
                personality, strategy
            )
            
            assert 0.1 <= resistance <= 0.9, f"{strategy} resistance out of bounds: {resistance}"
    
    def test_resistance_cynicism(self):
        """Test cynicism increases resistance to scarcity."""
        personality_cynical = {"cynicism": 0.9, "conscientiousness": 0.5}
        personality_naive = {"cynicism": 0.1, "conscientiousness": 0.5}
        
        res_cynical = calculate_persuasion_resistance_by_personality(
            personality_cynical, PersuasionStrategy.SCARCITY
        )
        res_naive = calculate_persuasion_resistance_by_personality(
            personality_naive, PersuasionStrategy.SCARCITY
        )
        
        # Cynical should be more resistant
        assert res_cynical > res_naive
    
    def test_resistance_stubbornness(self):
        """Test stubbornness increases resistance to social proof."""
        personality_stubborn = {"stubbornness": 0.9, "agreeableness": 0.5}
        personality_flexible = {"stubbornness": 0.1, "agreeableness": 0.5}
        
        res_stubborn = calculate_persuasion_resistance_by_personality(
            personality_stubborn, PersuasionStrategy.SOCIAL_PROOF
        )
        res_flexible = calculate_persuasion_resistance_by_personality(
            personality_flexible, PersuasionStrategy.SOCIAL_PROOF
        )
        
        # Stubborn should be more resistant
        assert res_stubborn > res_flexible


class TestPersonalityPersuasionSummary:
    """Tests for personality persuasion summary."""
    
    def test_summary_contains_all_strategies(self):
        """Test summary contains all strategies."""
        personality = {"openness": 0.5, "conscientiousness": 0.5}
        
        summary = get_personality_persuasion_summary(personality)
        
        assert len(summary) == len(PersuasionStrategy)
    
    def test_summary_contains_effectiveness(self):
        """Test summary contains effectiveness."""
        personality = {"openness": 0.5}
        
        summary = get_personality_persuasion_summary(personality)
        
        for strategy_data in summary.values():
            assert "effectiveness" in strategy_data
    
    def test_summary_contains_resistance(self):
        """Test summary contains resistance."""
        personality = {"openness": 0.5}
        
        summary = get_personality_persuasion_summary(personality)
        
        for strategy_data in summary.values():
            assert "resistance" in strategy_data
    
    def test_summary_contains_net_impact(self):
        """Test summary contains net impact."""
        personality = {"openness": 0.5}
        
        summary = get_personality_persuasion_summary(personality)
        
        for strategy_data in summary.values():
            assert "net_impact" in strategy_data
            # Net impact = effectiveness - resistance
            assert strategy_data["net_impact"] == pytest.approx(
                strategy_data["effectiveness"] - strategy_data["resistance"]
            )


class TestApplyPersonalityToEngine:
    """Tests for applying personality to persuasion engine."""
    
    def test_apply_personality(self):
        """Test applying personality modifies engine."""
        engine = PersuasionEngine(agent_id="test")
        
        # Store original resistance
        original_logic_res = engine.profile.strategy_resistance[PersuasionStrategy.LOGIC]
        
        # Apply personality that should increase logic resistance
        personality = {"openness": 0.1}  # Low openness = resistant to logic
        
        apply_personality_to_persuasion_engine(engine, personality)
        
        new_logic_res = engine.profile.strategy_resistance[PersuasionStrategy.LOGIC]
        
        # Resistance should have changed
        assert new_logic_res != original_logic_res
    
    def test_apply_personality_preserves_engine(self):
        """Test applying personality doesn't break engine."""
        engine = PersuasionEngine(agent_id="test")
        
        # Add an argument
        arg = Argument(
            claim="Test claim",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="other",
            tick=0
        )
        
        # Apply personality
        personality = {"openness": 0.5}
        apply_personality_to_persuasion_engine(engine, personality)
        
        # Engine should still work
        new_confidence, attempt = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="test",
            belief_confidence=0.5,
            tick=0
        )
        
        assert 0 <= new_confidence <= 1
        assert attempt is not None
    
    def test_different_personalities_different_resistances(self):
        """Test different personalities result in different resistances."""
        engine1 = PersuasionEngine(agent_id="test1")
        engine2 = PersuasionEngine(agent_id="test2")
        
        personality1 = {"openness": 0.9, "neuroticism": 0.1}
        personality2 = {"openness": 0.1, "neuroticism": 0.9}
        
        apply_personality_to_persuasion_engine(engine1, personality1)
        apply_personality_to_persuasion_engine(engine2, personality2)
        
        # Compare logic resistance (affected by openness)
        res1 = engine1.profile.strategy_resistance[PersuasionStrategy.LOGIC]
        res2 = engine2.profile.strategy_resistance[PersuasionStrategy.LOGIC]
        
        # Should be different due to different personalities
        assert res1 != res2


class TestPersuasionWithPersonality:
    """Integration tests for persuasion with personality weighting."""
    
    def test_high_openness_vulnerable_to_logic(self):
        """Test open agents are more vulnerable to logic."""
        engine = PersuasionEngine(agent_id="test")
        
        # Apply high openness
        apply_personality_to_persuasion_engine(
            engine, {"openness": 0.9, "conscientiousness": 0.5}
        )
        
        # Create logic argument
        arg = Argument(
            claim="Evidence shows X",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="other",
            tick=0,
            strength_score=0.7,
            confidence=0.7
        )
        
        # Calculate persuasion
        new_confidence, _ = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="test",
            belief_confidence=0.5,
            tick=0
        )
        
        # Should increase confidence (persuasion worked)
        assert new_confidence > 0.5
    
    def test_low_openness_resistant_to_logic(self):
        """Test closed agents are resistant to logic."""
        engine = PersuasionEngine(agent_id="test")
        
        # Apply low openness - makes them resistant to logic
        apply_personality_to_persuasion_engine(
            engine, {"openness": 0.1, "conscientiousness": 0.5}
        )
        
        # Same logic argument
        arg = Argument(
            claim="Evidence shows X",
            strategy=PersuasionStrategy.LOGIC,
            speaker_id="other",
            tick=0,
            strength_score=0.7,
            confidence=0.7
        )
        
        # Calculate persuasion
        new_confidence, _ = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="test",
            belief_confidence=0.5,
            tick=0
        )
        
        # The new confidence should be less than or equal to 0.61 (just slightly above baseline)
        # or the change should be minimal compared to high openness
        assert new_confidence <= 0.61
    
    def test_emotional_appeal_on_neurotic(self):
        """Test emotional appeals work on neurotic agents."""
        engine = PersuasionEngine(agent_id="test")
        
        # Apply high neuroticism
        apply_personality_to_persuasion_engine(
            engine, {"neuroticism": 0.9, "agreeableness": 0.5}
        )
        
        # Create emotional argument
        arg = Argument(
            claim="Think about his family",
            strategy=PersuasionStrategy.EMOTION,
            speaker_id="other",
            tick=0,
            strength_score=0.7,
            confidence=0.7
        )
        
        new_confidence, attempt = engine.calculate_persuasion_effect(
            argument=arg,
            listener_id="test",
            belief_confidence=0.5,
            tick=0
        )
        
        # Should be more susceptible to emotion
        assert new_confidence > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
