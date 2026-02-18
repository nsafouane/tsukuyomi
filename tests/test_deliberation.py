"""
Unit Tests for Deliberation Engine
==================================
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from tsukuyomi.brain.deliberation import (
    DeliberationEngine,
    DeliberationResult,
    DeliberationType,
    create_deliberation_engine
)


class TestDeliberationEngine:
    """Tests for DeliberationEngine."""

    def test_initialization(self):
        """Test deliberation engine initializes correctly."""
        engine = DeliberationEngine(
            agent_id="test_agent",
            belief_system=None,
            emotional_state={"valence": 0.2, "arousal": 0.6, "dominance": 0.3},
            personality={"patience": 0.7, "extraversion": 0.3}
        )

        assert engine.agent_id == "test_agent"
        assert engine.emotional_state["valence"] == 0.2
        assert engine.deliberation_history == []

    def test_update_emotional_state(self):
        """Test updating emotional state."""
        engine = DeliberationEngine(agent_id="test")

        new_state = {"valence": -0.5, "arousal": 0.8, "dominance": 0.1}
        engine.update_emotional_state(new_state)

        assert engine.emotional_state == new_state

    def test_template_deliberation(self):
        """Test template-based deliberation without LLM."""
        engine = DeliberationEngine(
            agent_id="test",
            emotional_state={"valence": -0.3, "arousal": 0.5, "dominance": 0.0},
            llm_call=None
        )

        context = {
            "stimulus": "Someone made a good point",
            "others_votes": {"guilty": 3, "not_guilty": 2},
            "my_vote": "guilty"
        }

        result = engine._template_deliberation(context)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_determine_emotional_reaction(self):
        """Test emotional reaction detection."""
        engine = DeliberationEngine(
            agent_id="test",
            emotional_state={"valence": 0.0, "arousal": 0.7, "dominance": 0.0}
        )

        # Test negative trigger
        reaction = engine._determine_emotional_reaction("That's completely wrong")
        assert reaction in ["frustrated", "defensive"]

        # Test positive trigger
        reaction = engine._determine_emotional_reaction("reasonable doubt")
        assert reaction == "receptive"

    def test_calculate_speak_urgency(self):
        """Test speak urgency calculation."""
        engine = DeliberationEngine(
            agent_id="test",
            emotional_state={"valence": 0.0, "arousal": 0.8, "dominance": 0.0},
            personality={"patience": 0.3}
        )

        # Minority context
        context = {
            "others_votes": {"guilty": 4, "not_guilty": 1},
            "my_vote": "not_guilty"
        }

        should_speak, urgency = engine._calculate_speak_urgency(context, "test")

        assert isinstance(should_speak, bool)
        assert isinstance(urgency, float)
        assert 0 <= urgency <= 1
        # High arousal + minority should = high urgency
        assert urgency > 0.4

    def test_deliberation_history(self):
        """Test deliberation history tracking."""
        engine = DeliberationEngine(
            agent_id="test",
            llm_call=None
        )

        # Add some mock deliberations
        for i in range(3):
            engine.deliberation_history.append(
                DeliberationResult(
                    deliberation_type=DeliberationType.EVALUATION,
                    content=f"Thought {i}",
                    confidence=0.5
                )
            )

        recent = engine.get_recent_deliberations(k=2)

        assert len(recent) == 2
        assert recent[0].content == "Thought 1"
        assert recent[1].content == "Thought 2"

    def test_serialization(self):
        """Test to_dict serialization."""
        engine = DeliberationEngine(
            agent_id="test_agent",
            emotional_state={"valence": 0.1, "arousal": 0.5, "dominance": 0.2}
        )

        # Add some history
        engine.deliberation_history.append(
            DeliberationResult(
                deliberation_type=DeliberationType.REFLECTION,
                content="Test deliberation",
                confidence=0.7
            )
        )

        data = engine.to_dict()

        assert data["agent_id"] == "test_agent"
        assert data["deliberation_count"] == 1
        assert "recent_deliberations" in data

    @pytest.mark.asyncio
    async def test_deliberate_with_mock_llm(self):
        """Test deliberate method with mock LLM."""
        mock_llm = AsyncMock(return_value="I think this is important...")

        engine = DeliberationEngine(
            agent_id="test",
            emotional_state={"valence": 0.0, "arousal": 0.5, "dominance": 0.0},
            llm_call=mock_llm
        )

        context = {"stimulus": "Test stimulus"}

        result = await engine.deliberate(context, tick=100)

        assert isinstance(result, DeliberationResult)
        assert result.deliberation_type == DeliberationType.EVALUATION
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliberate_fallback_to_template(self):
        """Test deliberate falls back to template on LLM failure."""
        mock_llm = Mock(side_effect=Exception("LLM failed"))

        engine = DeliberationEngine(
            agent_id="test",
            emotional_state={"valence": 0.0, "arousal": 0.5, "dominance": 0.0},
            llm_call=mock_llm
        )

        context = {"stimulus": "Test stimulus"}

        result = await engine.deliberate(context, tick=100)

        assert isinstance(result, DeliberationResult)
        # Should have fallback content
        assert len(result.content) > 0


class TestCreateDeliberationEngine:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        """Test factory with default values."""
        engine = create_deliberation_engine(agent_id="test")
        
        assert engine.agent_id == "test"
        # Default values are set in factory
        assert "valence" in engine.emotional_state
        assert "arousal" in engine.emotional_state

    def test_create_with_custom_values(self):
        """Test factory with custom values."""
        engine = create_deliberation_engine(
            agent_id="custom",
            emotional_state={"valence": 0.5, "arousal": 0.8, "dominance": 0.3},
            personality={"extraversion": 0.7}
        )

        assert engine.agent_id == "custom"
        assert engine.emotional_state["valence"] == 0.5
        assert engine.personality["extraversion"] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
