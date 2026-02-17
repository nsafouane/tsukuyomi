"""
Unit Tests for Belief Dynamics System
=====================================

Tests for Belief, Evidence, BeliefSystem, and related functions.
"""

import pytest
import json
from tsukuyomi.agent.belief_system import (
    BeliefType,
    EvidenceStrength,
    Evidence,
    Belief,
    BeliefUpdate,
    BeliefSystem,
    create_belief_from_core_value,
    belief_strength_category
)


class TestEvidence:
    """Tests for Evidence dataclass."""
    
    def test_create_evidence(self):
        """Test creating basic evidence."""
        e = Evidence(
            content="The defendant was seen at the scene",
            supports_belief=True,
            strength=0.8,
            source="eyewitness",
            source_reliability=0.7
        )
        
        assert e.content == "The defendant was seen at the scene"
        assert e.supports_belief is True
        assert e.strength == 0.8
        assert e.source_reliability == 0.7
        assert e.id is not None
    
    def test_evidence_strength_bounds(self):
        """Test evidence strength must be 0.0-1.0."""
        with pytest.raises(ValueError):
            Evidence(content="test", strength=1.5)
        
        with pytest.raises(ValueError):
            Evidence(content="test", strength=-0.5)
    
    def test_effective_strength(self):
        """Test effective strength calculation."""
        e = Evidence(
            content="test",
            strength=0.8,
            source_reliability=0.5
        )
        
        assert e.effective_strength == 0.4  # 0.8 * 0.5
    
    def test_evidence_serialization(self):
        """Test evidence to_dict/from_dict."""
        e = Evidence(
            content="Test evidence",
            supports_belief=False,
            strength=0.6,
            source="test_source",
            source_reliability=0.8,
            tick=100,
            emotional_weight=0.3
        )
        
        data = e.to_dict()
        restored = Evidence.from_dict(data)
        
        assert restored.content == e.content
        assert restored.supports_belief == e.supports_belief
        assert restored.strength == e.strength
        assert restored.tick == e.tick


class TestBelief:
    """Tests for Belief dataclass."""
    
    def test_create_belief(self):
        """Test creating a basic belief."""
        b = Belief(
            statement="The defendant is guilty",
            belief_type=BeliefType.OPINION,
            confidence=0.7
        )
        
        assert b.statement == "The defendant is guilty"
        assert b.belief_type == BeliefType.OPINION
        assert b.confidence == 0.7
        assert b.id is not None
    
    def test_confidence_bounds(self):
        """Test confidence must be 0.0-1.0."""
        with pytest.raises(ValueError):
            Belief(statement="test", confidence=1.5)
        
        with pytest.raises(ValueError):
            Belief(statement="test", confidence=-0.1)
    
    def test_is_certain(self):
        """Test is_certain property."""
        b = Belief(statement="test", confidence=0.9)
        assert b.is_certain is True
        
        b.confidence = 0.7
        assert b.is_certain is False
    
    def test_is_doubtful(self):
        """Test is_doubtful property."""
        b = Belief(statement="test", confidence=0.2)
        assert b.is_doubtful is True
        
        b.confidence = 0.5
        assert b.is_doubtful is False
    
    def test_evidence_count(self):
        """Test evidence count property."""
        b = Belief(
            statement="test",
            supporting_evidence=["e1", "e2"],
            contradicting_evidence=["e3"]
        )
        
        assert b.evidence_count == 3
    
    def test_record_confidence(self):
        """Test confidence history recording."""
        b = Belief(statement="test", confidence=0.5)
        
        b.record_confidence(100)
        b.record_confidence(200)
        
        assert len(b.confidence_history) == 2
        assert b.confidence_history[0] == (100, 0.5)
    
    def test_belief_serialization(self):
        """Test belief to_dict/from_dict."""
        b = Belief(
            statement="Test belief",
            belief_type=BeliefType.FACTUAL,
            confidence=0.8,
            initial_confidence=0.5,
            source="test",
            formed_tick=100,
            tags=["test", "important"],
            mutable=False,
            is_core_value=True
        )
        
        data = b.to_dict()
        restored = Belief.from_dict(data)
        
        assert restored.statement == b.statement
        assert restored.belief_type == b.belief_type
        assert restored.confidence == b.confidence
        assert restored.mutable == b.mutable
        assert restored.is_core_value == b.is_core_value


class TestBeliefSystem:
    """Tests for BeliefSystem class."""
    
    def test_create_belief_system(self):
        """Test creating a belief system."""
        bs = BeliefSystem(agent_id="test_agent")
        
        assert bs.agent_id == "test_agent"
        assert len(bs.beliefs) == 0
    
    def test_add_belief(self):
        """Test adding a belief."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(
            statement="The sky is blue",
            confidence=0.9,
            belief_type=BeliefType.FACTUAL
        )
        
        assert bid is not None
        assert len(bs.beliefs) == 1
        assert bs.get_belief(bid).statement == "The sky is blue"
    
    def test_add_duplicate_belief(self):
        """Test adding a duplicate belief returns existing ID."""
        bs = BeliefSystem(agent_id="test")
        
        id1 = bs.add_belief(statement="The sky is blue")
        id2 = bs.add_belief(statement="The sky is blue")
        
        assert id1 == id2
        assert len(bs.beliefs) == 1
    
    def test_find_belief(self):
        """Test finding a belief by statement."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="The defendant is guilty")
        
        found_id = bs.find_belief("The defendant is guilty")
        not_found = bs.find_belief("Something else")
        
        assert found_id is not None
        assert not_found is None
    
    def test_find_belief_case_insensitive(self):
        """Test finding belief is case-insensitive."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="The Defendant Is Guilty")
        
        found_id = bs.find_belief("the defendant is guilty")
        
        assert found_id is not None
    
    def test_get_beliefs_by_tag(self):
        """Test getting beliefs by tag."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="Belief 1", tags=["trial", "evidence"])
        bs.add_belief(statement="Belief 2", tags=["trial"])
        bs.add_belief(statement="Belief 3", tags=["personal"])
        
        trial_beliefs = bs.get_beliefs_by_tag("trial")
        
        assert len(trial_beliefs) == 2
    
    def test_get_beliefs_by_type(self):
        """Test getting beliefs by type."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="Fact 1", belief_type=BeliefType.FACTUAL)
        bs.add_belief(statement="Opinion 1", belief_type=BeliefType.OPINION)
        bs.add_belief(statement="Fact 2", belief_type=BeliefType.FACTUAL)
        
        facts = bs.get_beliefs_by_type(BeliefType.FACTUAL)
        
        assert len(facts) == 2
    
    def test_get_certain_beliefs(self):
        """Test getting beliefs with high certainty."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="Certain", confidence=0.9)
        bs.add_belief(statement="Uncertain", confidence=0.5)
        
        certain = bs.get_certain_beliefs()
        
        assert len(certain) == 1
        assert certain[0].statement == "Certain"
    
    def test_add_evidence(self):
        """Test adding evidence to a belief."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(statement="The defendant is guilty")
        eid = bs.add_evidence(
            belief_id=bid,
            content="Eyewitness saw him at the scene",
            supports_belief=True,
            strength=0.8
        )
        
        assert eid is not None
        belief = bs.get_belief(bid)
        assert len(belief.supporting_evidence) == 1
    
    def test_add_contradicting_evidence(self):
        """Test adding contradicting evidence."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(statement="The defendant is guilty")
        eid = bs.add_evidence(
            belief_id=bid,
            content="Alibi proves he was elsewhere",
            supports_belief=False,
            strength=0.9
        )
        
        belief = bs.get_belief(bid)
        assert len(belief.contradicting_evidence) == 1
    
    def test_get_belief_evidence(self):
        """Test retrieving belief evidence."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(statement="test")
        bs.add_evidence(bid, "Support 1", True, 0.7)
        bs.add_evidence(bid, "Support 2", True, 0.6)
        bs.add_evidence(bid, "Contradict 1", False, 0.5)
        
        supporting, contradicting = bs.get_belief_evidence(bid)
        
        assert len(supporting) == 2
        assert len(contradicting) == 1
    
    def test_update_belief_with_supporting_evidence(self):
        """Test belief confidence increases with supporting evidence."""
        bs = BeliefSystem(agent_id="test", openness=1.0, confirmation_bias=1.0)
        
        bid = bs.add_belief(statement="test", confidence=0.5)
        bs.add_evidence(bid, "Strong support", True, strength=0.9)
        
        update = bs.update_belief(bid, tick=100)
        
        assert update is not None
        assert update.new_confidence > update.old_confidence
    
    def test_update_belief_with_contradicting_evidence(self):
        """Test belief confidence decreases with contradicting evidence."""
        bs = BeliefSystem(agent_id="test", openness=1.0, confirmation_bias=1.0)
        
        bid = bs.add_belief(statement="test", confidence=0.5)
        bs.add_evidence(bid, "Strong contradiction", False, strength=0.9)
        
        update = bs.update_belief(bid, tick=100)
        
        assert update is not None
        assert update.new_confidence < update.old_confidence
    
    def test_immutable_belief_cannot_update(self):
        """Test immutable beliefs cannot be updated."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(statement="test", confidence=0.5, mutable=False)
        bs.add_evidence(bid, "Evidence", True, strength=0.9)
        
        update = bs.update_belief(bid)
        
        assert update is None
    
    def test_confirmation_bias_supporting(self):
        """Test confirmation bias amplifies supporting evidence for certain beliefs."""
        bs = BeliefSystem(agent_id="test", confirmation_bias=1.5, openness=1.0)
        
        bid = bs.add_belief(statement="test", confidence=0.8)
        bs.add_evidence(bid, "Support", True, strength=0.5)
        
        update = bs.update_belief(bid, tick=100)
        
        assert update.new_confidence > update.old_confidence
    
    def test_openness_affects_change_magnitude(self):
        """Test that openness affects how much beliefs change."""
        bs_closed = BeliefSystem(agent_id="closed", openness=0.1)
        bs_open = BeliefSystem(agent_id="open", openness=1.0)
        
        bid1 = bs_closed.add_belief(statement="test", confidence=0.5)
        bs_closed.add_evidence(bid1, "Evidence", True, strength=0.9)
        
        bid2 = bs_open.add_belief(statement="test", confidence=0.5)
        bs_open.add_evidence(bid2, "Evidence", True, strength=0.9)
        
        update1 = bs_closed.update_belief(bid1, tick=100)
        update2 = bs_open.update_belief(bid2, tick=100)
        
        assert update2.change > update1.change
    
    def test_evaluate_single_evidence(self):
        """Test evaluating a single piece of evidence."""
        bs = BeliefSystem(agent_id="test", openness=1.0)
        
        bid = bs.add_belief(statement="test", confidence=0.5)
        eid = bs.add_evidence(bid, "Evidence", True, strength=0.8)
        
        update = bs.evaluate_evidence(bid, eid, tick=100)
        
        assert update is not None
        assert update.evidence_id == eid
    
    def test_find_contradictions(self):
        """Test finding contradictory beliefs."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="The defendant is guilty", confidence=0.9)
        bs.add_belief(statement="The defendant is not guilty", confidence=0.9)
        
        contradictions = bs.find_contradictions()
        
        assert len(contradictions) == 1
    
    def test_resolve_contradiction(self):
        """Test resolving contradictions."""
        bs = BeliefSystem(agent_id="test")
        
        bid1 = bs.add_belief(statement="The defendant is guilty", confidence=0.9)
        bs.add_evidence(bid1, "Evidence 1", True, strength=0.7)
        
        bid2 = bs.add_belief(statement="The defendant is not guilty", confidence=0.9)
        bs.add_evidence(bid2, "Evidence 2", True, strength=0.5)
        
        b1 = bs.get_belief(bid1)
        b2 = bs.get_belief(bid2)
        
        bs.resolve_contradiction(b1, b2, tick=100)
        
        assert b1.confidence < 0.9 or b2.confidence < 0.9
    
    def test_format_beliefs(self):
        """Test formatting beliefs for prompt."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="Fact A", confidence=0.9, tags=["trial"])
        bs.add_belief(statement="Fact B", confidence=0.5, tags=["trial"])
        
        formatted = bs.format_beliefs()
        
        assert "CURRENT BELIEFS:" in formatted
        assert "Fact A" in formatted
    
    def test_format_beliefs_by_topic(self):
        """Test formatting beliefs filtered by topic."""
        bs = BeliefSystem(agent_id="test")
        
        bs.add_belief(statement="Trial fact", confidence=0.8, tags=["trial"])
        bs.add_belief(statement="Personal belief", confidence=0.8, tags=["personal"])
        
        formatted = bs.format_beliefs(topics=["trial"])
        
        assert "Trial fact" in formatted
        assert "Personal belief" not in formatted
    
    def test_belief_summary(self):
        """Test getting detailed belief summary."""
        bs = BeliefSystem(agent_id="test")
        
        bid = bs.add_belief(
            statement="Test belief",
            confidence=0.7,
            belief_type=BeliefType.OPINION
        )
        bs.add_evidence(bid, "Support", True, strength=0.6)
        bs.add_evidence(bid, "Contradict", False, strength=0.4)
        
        summary = bs.get_belief_summary(bid)
        
        assert "Test belief" in summary
        assert "OPINION" in summary
    
    def test_serialization(self):
        """Test full belief system serialization."""
        bs = BeliefSystem(agent_id="test", openness=0.7)
        
        bid = bs.add_belief(statement="Test", confidence=0.6)
        bs.add_evidence(bid, "Evidence", True, strength=0.8)
        bs.update_belief(bid, tick=100)
        
        data = bs.to_dict()
        restored = BeliefSystem.from_dict(data)
        
        assert restored.agent_id == bs.agent_id
        assert restored.openness == bs.openness
        assert len(restored.beliefs) == len(bs.beliefs)
    
    def test_prune(self):
        """Test pruning removes low-importance beliefs."""
        bs = BeliefSystem(agent_id="test")
        
        for i in range(150):
            bs.add_belief(
                statement=f"Belief {i}",
                confidence=0.3 + (i % 5) * 0.1,
                tags=[f"tag_{i % 10}"]
            )
        
        bs.prune(max_beliefs=100)
        
        assert len(bs.beliefs) <= 100


class TestBeliefUpdate:
    """Tests for BeliefUpdate dataclass."""
    
    def test_change_property(self):
        """Test change property."""
        update = BeliefUpdate(
            belief_id="b1",
            old_confidence=0.5,
            new_confidence=0.8,
            evidence_id="e1",
            reason="test",
            tick=100
        )
        
        assert abs(update.change - 0.3) < 0.001
    
    def test_direction_increased(self):
        """Test direction when increased."""
        update = BeliefUpdate(
            belief_id="b1",
            old_confidence=0.5,
            new_confidence=0.8,
            evidence_id="e1",
            reason="test",
            tick=100
        )
        
        assert update.direction == "increased"
    
    def test_direction_decreased(self):
        """Test direction when decreased."""
        update = BeliefUpdate(
            belief_id="b1",
            old_confidence=0.8,
            new_confidence=0.5,
            evidence_id="e1",
            reason="test",
            tick=100
        )
        
        assert update.direction == "decreased"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_belief_from_core_value(self):
        """Test creating belief from core value."""
        belief = create_belief_from_core_value(
            value="Justice must be served",
            source="My father was wrongly accused",
            intensity=0.8
        )
        
        assert belief.statement == "Justice must be served"
        assert belief.belief_type == BeliefType.VALUE
        assert belief.mutable is False
        assert belief.is_core_value is True
    
    def test_belief_strength_category(self):
        """Test belief strength categorization."""
        assert belief_strength_category(0.95) == "ABSOLUTE"
        assert belief_strength_category(0.7) == "STRONG"
        assert belief_strength_category(0.5) == "MODERATE"
        assert belief_strength_category(0.3) == "WEAK"
        assert belief_strength_category(0.1) == "DOUBTFUL"
