"""
Unit Tests for Decision Engine
==============================

Tests for Decision, DecisionFactor, ReasoningStep, DecisionEngine.
"""

import pytest
from tsukuyomi.agents.cognitive.decision_engine import (
    DecisionType,
    DecisionPriority,
    DecisionOutcome,
    DecisionFactor,
    ReasoningStep,
    Decision,
    DecisionEngine,
    create_verdict_decision,
    create_action_decision
)


class TestDecisionFactor:
    """Tests for DecisionFactor."""
    
    def test_create_factor(self):
        """Test creating a factor."""
        factor = DecisionFactor(
            description="Evidence supports guilt",
            weight=0.8,
            belief_id="b1"
        )
        
        assert factor.description == "Evidence supports guilt"
        assert factor.weight == 0.8
        assert factor.belief_id == "b1"
    
    def test_factor_serialization(self):
        """Test factor serialization."""
        factor = DecisionFactor(
            description="Test",
            weight=0.5,
            source="test"
        )
        
        data = factor.to_dict()
        restored = DecisionFactor.from_dict(data)
        
        assert restored.description == factor.description
        assert restored.weight == factor.weight


class TestReasoningStep:
    """Tests for ReasoningStep."""
    
    def test_create_step(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(
            step_number=1,
            premise="The witness saw the defendant",
            inference="The witness was at the scene",
            confidence=0.7
        )
        
        assert step.step_number == 1
        assert step.inference == "The witness was at the scene"
    
    def test_step_serialization(self):
        """Test step serialization."""
        step = ReasoningStep(
            premise="Test premise",
            inference="Test inference",
            evidence_ids=["e1", "e2"]
        )
        
        data = step.to_dict()
        restored = ReasoningStep.from_dict(data)
        
        assert restored.premise == step.premise
        assert restored.evidence_ids == step.evidence_ids


class TestDecision:
    """Tests for Decision."""
    
    def test_create_decision(self):
        """Test creating a decision."""
        decision = Decision(
            question="Is the defendant guilty?",
            decision_type=DecisionType.VERDICT,
            alternatives=["guilty", "not guilty"]
        )
        
        assert decision.question == "Is the defendant guilty?"
        assert decision.decision_type == DecisionType.VERDICT
        assert len(decision.alternatives) == 2
    
    def test_reasoning_text(self):
        """Test reasoning text property."""
        decision = Decision()
        decision.reasoning_chain = [
            ReasoningStep(step_number=1, premise="P1", inference="I1"),
            ReasoningStep(step_number=2, premise="P2", inference="I2")
        ]
        
        text = decision.reasoning_text
        assert "1. P1" in text
        assert "2. P2" in text
    
    def test_decision_serialization(self):
        """Test decision serialization."""
        decision = Decision(
            question="Test?",
            choice="choice_a",
            tick=100
        )
        decision.factors = [DecisionFactor(description="Factor 1", weight=0.5)]
        decision.reasoning_chain = [ReasoningStep(step_number=1, premise="P", inference="I")]
        
        data = decision.to_dict()
        restored = Decision.from_dict(data)
        
        assert restored.question == decision.question
        assert restored.choice == decision.choice
        assert len(restored.factors) == 1
        assert len(restored.reasoning_chain) == 1


class TestDecisionEngine:
    """Tests for DecisionEngine."""
    
    def test_create_engine(self):
        """Test creating an engine."""
        engine = DecisionEngine(agent_id="test")
        
        assert engine.agent_id == "test"
        assert len(engine.decisions) == 0
    
    def test_create_decision(self):
        """Test creating a decision."""
        engine = DecisionEngine(agent_id="test")
        
        decision = engine.create_decision(
            question="What to do?",
            decision_type=DecisionType.ACTION,
            alternatives=["A", "B"]
        )
        
        assert decision.id in engine.decisions
        assert decision.id in engine.pending_decisions
    
    def test_add_reasoning_step(self):
        """Test adding reasoning steps."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(question="Test?")
        
        step1 = engine.add_reasoning_step(
            decision_id=decision.id,
            premise="P1",
            inference="I1"
        )
        
        assert len(decision.reasoning_chain) == 1
        assert step1.step_number == 1
    
    def test_add_factor(self):
        """Test adding factors."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(question="Test?")
        
        factor = engine.add_factor(
            decision_id=decision.id,
            description="Important factor",
            weight=0.8
        )
        
        assert len(decision.factors) == 1
        assert factor.weight == 0.8
    
    def test_make_decision(self):
        """Test making a decision."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(
            question="Test?",
            alternatives=["A", "B"]
        )
        
        result = engine.make_decision(
            decision_id=decision.id,
            choice="A",
            confidence=0.8,
            tick=100
        )
        
        assert result.choice == "A"
        assert result.id not in engine.pending_decisions
        assert result.id in engine.completed_decisions
    
    def test_evaluate_decision(self):
        """Test evaluating a decision."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(question="Test?")
        engine.make_decision(decision.id, "A", tick=100)
        
        engine.evaluate_decision(
            decision_id=decision.id,
            outcome=DecisionOutcome.SUCCESS,
            evaluation="Choice was correct",
            tick=200
        )
        
        assert decision.outcome == DecisionOutcome.SUCCESS
        assert decision.evaluation == "Choice was correct"
    
    def test_score_alternatives(self):
        """Test scoring alternatives."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(
            question="Which?",
            alternatives=["A", "B"]
        )
        
        # Add factors
        engine.add_factor(decision.id, "Factor1", weight=0.6)
        engine.add_factor(decision.id, "Factor2", weight=0.4)
        
        # Score functions
        def score_factor1(alt):
            return 0.8 if alt == "A" else 0.3
        
        def score_factor2(alt):
            return 0.5 if alt == "B" else 0.5
        
        scores = engine.score_alternatives(decision.id, {
            "Factor1": score_factor1,
            "Factor2": score_factor2
        })
        
        assert "A" in scores
        assert "B" in scores
    
    def test_recommend_choice(self):
        """Test recommendation."""
        engine = DecisionEngine(agent_id="test")
        decision = engine.create_decision(
            question="Which?",
            alternatives=["A", "B"]
        )
        
        def score(alt):
            return 0.9 if alt == "A" else 0.3
        
        choice, score_val = engine.recommend_choice(decision.id, {"score": score})
        
        assert choice == "A"
        assert score_val > 0
    
    def test_get_pending(self):
        """Test getting pending decisions."""
        engine = DecisionEngine(agent_id="test")
        d1 = engine.create_decision(question="Q1")
        d2 = engine.create_decision(question="Q2")
        
        pending = engine.get_pending_decisions()
        
        assert len(pending) == 2
    
    def test_get_completed(self):
        """Test getting completed decisions."""
        engine = DecisionEngine(agent_id="test")
        d1 = engine.create_decision(question="Q1")
        engine.make_decision(d1.id, "A")
        
        completed = engine.get_completed_decisions()
        
        assert len(completed) == 1
    
    def test_success_rate(self):
        """Test success rate calculation."""
        engine = DecisionEngine(agent_id="test")
        
        d1 = engine.create_decision(question="Q1")
        engine.make_decision(d1.id, "A", tick=100)
        engine.evaluate_decision(d1.id, DecisionOutcome.SUCCESS, "Good", tick=200)
        
        d2 = engine.create_decision(question="Q2")
        engine.make_decision(d2.id, "B", tick=100)
        engine.evaluate_decision(d2.id, DecisionOutcome.FAILURE, "Bad", tick=200)
        
        rate = engine.get_success_rate()
        
        assert rate == 0.5
    
    def test_decision_summary(self):
        """Test decision summary."""
        engine = DecisionEngine(agent_id="test_agent")
        engine.create_decision(question="Q1")
        
        summary = engine.get_decision_summary()
        
        assert "test_agent" in summary
        assert "PENDING DECISIONS" in summary
    
    def test_serialization(self):
        """Test engine serialization."""
        engine = DecisionEngine(agent_id="test")
        d1 = engine.create_decision(question="Q1")
        engine.make_decision(d1.id, "A", tick=100)
        
        data = engine.to_dict()
        restored = DecisionEngine.from_dict(data)
        
        assert restored.agent_id == engine.agent_id
        assert len(restored.decisions) == len(engine.decisions)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_verdict_decision(self):
        """Test creating verdict decision."""
        engine = DecisionEngine(agent_id="test")
        
        decision = create_verdict_decision(
            engine=engine,
            case="The murder of John Doe",
            factors=[
                {"description": "DNA evidence", "weight": 0.9},
                {"description": "Motive", "weight": 0.7}
            ],
            tick=100
        )
        
        assert decision.decision_type == DecisionType.VERDICT
        assert len(decision.factors) == 2
    
    def test_create_action_decision(self):
        """Test creating action decision."""
        engine = DecisionEngine(agent_id="test")
        
        decision = create_action_decision(
            engine=engine,
            action="interviewing the witness",
            alternatives=["interview_now", "wait", "skip"],
            tick=100
        )
        
        assert decision.decision_type == DecisionType.ACTION
        assert len(decision.alternatives) == 3
