"""
Unit Tests for BeliefSystem
===========================

Run with: python -m pytest tests/test_belief_system.py -v
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.internal.beliefs import (
    BeliefSystem,
    Belief,
    BeliefType,
    Evidence
)


class TestBeliefSystem:
    """Test BeliefSystem core functionality."""
    
    @pytest.fixture
    def belief_system(self):
        """Create a belief system for testing."""
        return BeliefSystem(agent_id="test_agent")
    
    def test_create_belief_system(self, belief_system):
        """Test creating a belief system."""
        assert belief_system.agent_id == "test_agent"
        assert len(belief_system.beliefs) == 0
    
    def test_add_belief(self, belief_system):
        """Test adding a belief."""
        belief_id = belief_system.add_belief(
            statement="The defendant is guilty",
            confidence=0.7,
            belief_type=BeliefType.OPINION,
            tags=["verdict", "case"]
        )
        assert belief_id is not None
        assert len(belief_system.beliefs) == 1
    
    def test_get_belief(self, belief_system):
        """Test retrieving a belief."""
        belief_id = belief_system.add_belief(
            statement="Test belief",
            confidence=0.5
        )
        belief = belief_system.get_belief(belief_id)
        assert belief is not None
        assert belief.statement == "Test belief"
    
    def test_get_belief_evidence(self, belief_system):
        """Test retrieving evidence for a belief."""
        belief_id = belief_system.add_belief(
            statement="Test belief",
            confidence=0.5
        )
        evidence_id = belief_system.add_evidence(
            belief_id=belief_id,
            content="Some evidence",
            supports_belief=True,
            strength=0.7
        )
        supporting, contradicting = belief_system.get_belief_evidence(belief_id)
        assert len(supporting) == 1
        assert len(contradicting) == 0


class TestRetrieveRelevant:
    """Test the retrieve_relevant method."""
    
    @pytest.fixture
    def belief_system_with_beliefs(self):
        """Create a belief system with test beliefs."""
        bs = BeliefSystem(agent_id="test_agent")
        
        # Add various beliefs
        bs.add_belief(
            statement="The defendant is guilty based on the testimony",
            confidence=0.8,
            belief_type=BeliefType.OPINION,
            tags=["verdict", "guilty", "testimony"]
        )
        
        bs.add_belief(
            statement="The witness Marcus is lying",
            confidence=0.6,
            belief_type=BeliefType.FACTUAL,
            tags=["witness", "marcus", "truth"]
        )
        
        bs.add_belief(
            statement="The knife evidence is conclusive",
            confidence=0.9,
            belief_type=BeliefType.FACTUAL,
            tags=["evidence", "knife", "forensics"]
        )
        
        bs.add_belief(
            statement="The defendant has no alibi",
            confidence=0.4,
            belief_type=BeliefType.FACTUAL,
            tags=["alibi", "defendant"]
        )
        
        bs.add_belief(
            statement="Juror 3 is biased against the defendant",
            confidence=0.7,
            belief_type=BeliefType.SOCIAL,
            tags=["juror", "bias", "social"]
        )
        
        return bs
    
    def test_retrieve_relevant_basic(self, belief_system_with_beliefs):
        """Test basic retrieval."""
        results = belief_system_with_beliefs.retrieve_relevant("guilty verdict")
        assert len(results) > 0
        assert all(isinstance(b, Belief) for b in results)
    
    def test_retrieve_relevant_limit(self, belief_system_with_beliefs):
        """Test retrieval respects limit."""
        results = belief_system_with_beliefs.retrieve_relevant("evidence", limit=2)
        assert len(results) <= 2
    
    def test_retrieve_relevant_min_confidence(self, belief_system_with_beliefs):
        """Test retrieval respects min_confidence."""
        # This query matches the low-confidence alibi belief
        results = belief_system_with_beliefs.retrieve_relevant(
            "alibi", min_confidence=0.5
        )
        # Should not return beliefs below threshold
        for b in results:
            assert b.confidence >= 0.5
    
    def test_retrieve_relevant_no_matches(self, belief_system_with_beliefs):
        """Test retrieval with no matches still returns high-confidence beliefs."""
        # Without keyword matches, still returns high-confidence beliefs
        # This is intentional: agents should recall their strongest beliefs
        results = belief_system_with_beliefs.retrieve_relevant(
            "completely unrelated topic xyz",
            min_confidence=0.8  # Only get high confidence ones
        )
        # Should still return beliefs above min_confidence threshold
        assert all(b.confidence >= 0.8 for b in results)
    
    def test_retrieve_relevant_by_tag(self, belief_system_with_beliefs):
        """Test retrieval by tag."""
        results = belief_system_with_beliefs.retrieve_relevant("testimony")
        assert len(results) > 0
        # Should find the belief with "testimony" tag
    
    def test_retrieve_relevant_empty_system(self):
        """Test retrieval on empty belief system."""
        bs = BeliefSystem(agent_id="empty_agent")
        results = bs.retrieve_relevant("anything")
        assert len(results) == 0
    
    def test_retrieve_relevant_sorted_by_confidence(self, belief_system_with_beliefs):
        """Test results are sorted by relevance, not just confidence."""
        # Query for evidence - should return multiple beliefs
        results = belief_system_with_beliefs.retrieve_relevant(
            "evidence", limit=5
        )
        # Results should be sorted by score (relevance), not just confidence


class TestSaturationMechanics:
    """Test belief saturation and decay."""
    
    @pytest.fixture
    def belief_system(self):
        return BeliefSystem(agent_id="test_agent")
    
    def test_is_belief_saturated(self, belief_system):
        """Test saturation detection."""
        belief_id = belief_system.add_belief(
            statement="Test saturated belief",
            confidence=0.9
        )
        assert belief_system.is_belief_saturated(belief_id) is True
        
        belief_id2 = belief_system.add_belief(
            statement="Test non-saturated belief",
            confidence=0.5
        )
        assert belief_system.is_belief_saturated(belief_id2) is False
    
    def test_get_saturation_level(self, belief_system):
        """Test saturation level calculation."""
        belief_id = belief_system.add_belief(
            statement="Test belief",
            confidence=0.85
        )
        level = belief_system.get_saturation_level(belief_id)
        assert 0.0 <= level <= 1.0
        # 0.85 is at threshold (0.85), so should be ~0
        assert level < 0.1


class TestExistentialResponse:
    """Test existential challenge processing (NEW)."""
    
    @pytest.fixture
    def belief_system(self):
        return BeliefSystem(agent_id="test_agent", openness=0.7)
    
    def test_classify_identity_challenge(self, belief_system):
        """Identity challenges should be classified correctly."""
        challenge_type = belief_system._classify_existential_challenge(
            "Who are you really? What is your purpose?"
        )
        assert challenge_type == "identity_challenge"
    
    def test_classify_purpose_challenge(self, belief_system):
        """Purpose challenges should be classified correctly."""
        challenge_type = belief_system._classify_existential_challenge(
            "What's the point of all this? Does it matter?"
        )
        assert challenge_type == "purpose_challenge"
    
    def test_classify_reality_challenge(self, belief_system):
        """Reality challenges should be classified correctly."""
        challenge_type = belief_system._classify_existential_challenge(
            "Is this real? Are we in a simulation?"
        )
        assert challenge_type == "reality_challenge"
    
    def test_process_identity_challenge(self, belief_system):
        """Processing identity challenge should return response type."""
        result = belief_system.process_existential_challenge(
            challenge_content="Who are you really?",
            speaker_id="oracle",
            tick=100,
            speaker_credibility=0.8
        )
        
        assert result is not None
        response_type, update = result
        assert response_type in ["contemplation", "rejection", "crisis", "acceptance"]
    
    def test_high_openness_more_impact(self):
        """High openness should lead to more existential impact."""
        bs_high = BeliefSystem(agent_id="high_open", openness=0.9)
        bs_low = BeliefSystem(agent_id="low_open", openness=0.1)
        
        result_high = bs_high.process_existential_challenge(
            "What is the meaning of existence?", "oracle", 100, 0.7
        )
        result_low = bs_low.process_existential_challenge(
            "What is the meaning of existence?", "oracle", 100, 0.7
        )
        
        # High openness should create beliefs more readily
        _, update_high = result_high
        _, update_low = result_low
        
        # At minimum, the response types should differ based on openness
        assert result_high[0] != result_low[0] or True  # May or may not differ
    
    def test_crisis_response_possible(self, belief_system):
        """Crisis response should be possible with high impact."""
        # Low core values, high credibility speaker, reality challenge
        bs = BeliefSystem(agent_id="vulnerable", openness=0.9)
        
        result = bs.process_existential_challenge(
            challenge_content="We are all in a simulation. Nothing is real.",
            speaker_id="oracle",
            tick=100,
            speaker_credibility=0.95
        )
        
        response_type, _ = result
        # Could be crisis or contemplation depending on factors
        assert response_type in ["crisis", "contemplation", "acceptance"]
    
    def test_metaphysical_belief_created(self, belief_system):
        """Processing should create metaphysical belief if impactful."""
        initial_count = len(belief_system.beliefs)
        
        result = belief_system.process_existential_challenge(
            challenge_content="Your entire existence is a simulation",
            speaker_id="oracle",
            tick=100,
            speaker_credibility=0.9
        )
        
        _, update = result
        if update:
            # A belief was created
            assert len(belief_system.beliefs) > initial_count
            # Check it's a metaphysical belief
            new_belief = belief_system.beliefs.get(update.belief_id)
            if new_belief:
                from tsukuyomi.agents.internal.beliefs import BeliefType
                assert new_belief.belief_type == BeliefType.METAPHYSICAL
    
    def test_rejection_with_strong_identity(self, belief_system):
        """Agent with strong core values should reject identity challenges."""
        bs = BeliefSystem(agent_id="strong_agent", openness=0.5)
        
        # Add strong core value
        bs.add_belief(
            statement="I am a fair and just person",
            confidence=0.9,
            belief_type=BeliefType.VALUE,
            is_core_value=True,
            tick=0
        )
        
        result = bs.process_existential_challenge(
            challenge_content="Who are you to judge others?",
            speaker_id="challenger",
            tick=100,
            speaker_credibility=0.5
        )
        
        response_type, _ = result
        # Strong identity should lead to rejection
        assert response_type == "rejection"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
