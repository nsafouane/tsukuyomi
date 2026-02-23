"""
Tests for Belief Plasticity System
===================================

Tests the exponential decay, perturbation, and contradiction detection features.

Run with: python -m pytest tsukuyomi/agent/tests/test_belief_plasticity.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from tsukuyomi.agents.internal.beliefs import (
    BeliefSystem, Belief, BeliefType, DecayConfig
)


class TestExponentialDecay:
    """Tests for exponential decay of beliefs."""
    
    def test_decay_config_defaults(self):
        """DecayConfig has sensible defaults."""
        config = DecayConfig()
        assert config.base_rate == 0.005
        assert config.min_confidence == 0.1
        assert config.saturation_threshold == 0.85
    
    def test_exponential_decay_older_beliefs_decay_faster(self):
        """Older beliefs decay faster than newer ones."""
        system = BeliefSystem(agent_id="test")
        
        # Add belief with old timestamp
        b1_id = system.add_belief("Old belief", 0.9, tick=0)
        # Add belief with recent timestamp
        b2_id = system.add_belief("New belief", 0.9, tick=1000)
        
        # Apply decay at tick 1000
        changes = system.decay_beliefs(tick=1000)
        
        old_belief = system.beliefs[b1_id]
        new_belief = system.beliefs[b2_id]
        
        # Old belief should have decayed more
        assert old_belief.confidence < new_belief.confidence
    
    def test_decay_respects_min_confidence(self):
        """Decay doesn't go below minimum confidence."""
        system = BeliefSystem(agent_id="test")
        system.add_belief("Test belief", 0.15, tick=0)
        
        # Apply heavy decay
        config = DecayConfig(base_rate=1.0, time_factor=1.0, min_confidence=0.1)
        changes = system.decay_beliefs(tick=1000, config=config)
        
        belief = list(system.beliefs.values())[0]
        assert belief.confidence >= 0.1
    
    def test_no_decay_for_belows_min_confidence(self):
        """Beliefs already at min confidence don't decay further."""
        system = BeliefSystem(agent_id="test")
        system.add_belief("Test belief", 0.1, tick=0)
        
        changes = system.decay_beliefs(tick=1000)
        
        belief = list(system.beliefs.values())[0]
        assert belief.confidence == 0.1


class TestPerturbation:
    """Tests for belief perturbation."""
    
    def test_perturbation_only_affects_high_confidence(self):
        """Only saturated (high confidence) beliefs get perturbed."""
        system = BeliefSystem(agent_id="test")
        
        # Add high and low confidence beliefs
        high_id = system.add_belief("High confidence", 0.95, tick=0)
        low_id = system.add_belief("Low confidence", 0.5, tick=0)
        
        # Apply perturbation with mocked random
        import random
        original_random = random.random
        random.random = lambda: 0.01  # Force perturbation
        
        config = DecayConfig(perturbation_chance=1.0, perturbation_strength=0.3)
        changes = system.perturb_saturated_beliefs(tick=100, config=config)
        
        random.random = original_random
        
        # High confidence should be perturbed
        assert system.beliefs[high_id].confidence < 0.95
        # Low confidence should not be affected
        assert system.beliefs[low_id].confidence == 0.5
    
    def test_perturbation_respects_min_confidence(self):
        """Perturbation doesn't go below minimum."""
        system = BeliefSystem(agent_id="test")
        system.add_belief("Test", 0.2, tick=0)  # Below saturation threshold
        
        import random
        original_random = random.random
        random.random = lambda: 0.01
        
        config = DecayConfig(perturbation_chance=1.0, perturbation_strength=0.5)
        changes = system.perturb_saturated_beliefs(tick=100, config=config)
        
        random.random = original_random
        
        # No changes because below saturation threshold
        assert len(changes) == 0


class TestContradictionDetection:
    """Tests for contradiction detection."""
    
    def test_detect_contradiction(self):
        """Contradictory beliefs are detected."""
        system = BeliefSystem(agent_id="test")
        
        # Add contradictory beliefs
        system.add_belief("The defendant is guilty", confidence=0.9)
        system.add_belief("The defendant is not guilty", confidence=0.9)
        
        contradictions = system.detect_contradictions()
        
        assert len(contradictions) >= 1
        assert contradictions[0]["severity"] > 0.5
    
    def test_resolve_contradiction_reduce_both(self):
        """Contradiction resolution reduces both beliefs."""
        system = BeliefSystem(agent_id="test")
        
        b1_id = system.add_belief("The defendant is guilty", confidence=0.8)
        b2_id = system.add_belief("The defendant is not guilty", confidence=0.8)
        
        contradiction = {
            "belief_1": b1_id,
            "belief_2": b2_id,
            "severity": 0.8
        }
        
        changes = system.resolve_contradiction_advanced(contradiction, "reduce_both")
        
        assert system.beliefs[b1_id].confidence < 0.8
        assert system.beliefs[b2_id].confidence < 0.8
    
    def test_resolve_contradiction_keep_stronger(self):
        """Keep stronger belief, reduce weaker."""
        system = BeliefSystem(agent_id="test")
        
        b1_id = system.add_belief("The defendant is guilty", confidence=0.9)
        b2_id = system.add_belief("The defendant is not guilty", confidence=0.5)
        
        contradiction = {
            "belief_1": b1_id,
            "belief_2": b2_id,
            "severity": 0.7
        }
        
        changes = system.resolve_contradiction_advanced(contradiction, "keep_stronger")
        
        # b1 (0.9) should stay, b2 (0.5) should be reduced
        assert system.beliefs[b1_id].confidence == 0.9
        assert system.beliefs[b2_id].confidence < 0.5


class TestPlasticity:
    """Tests for context-dependent plasticity."""
    
    def test_plasticity_stress_modifier(self):
        """High stress increases plasticity."""
        system = BeliefSystem(agent_id="test")
        
        low_stress = system.get_plasticity({"stress": 0.2})
        high_stress = system.get_plasticity({"stress": 0.8})
        
        assert high_stress > low_stress
    
    def test_plasticity_contradiction_modifier(self):
        """Recent contradictions increase plasticity."""
        system = BeliefSystem(agent_id="test")
        
        no_contradicitions = system.get_plasticity({"recent_contradictions": 0})
        many_contradictions = system.get_plasticity({"recent_contradictions": 5})
        
        assert many_contradictions > no_contradicitions
    
    def test_plasticity_bounds(self):
        """Plasticity stays within reasonable bounds."""
        system = BeliefSystem(agent_id="test")
        
        plasticity = system.get_plasticity({
            "stress": 0.0,
            "arousal": 0.0,
            "recent_contradictions": 100
        })
        
        # Should be between 0.5 and 2.0
        assert 0.5 <= plasticity <= 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
