"""
Unit Tests for Immersive Prompt Builder
======================================
"""

import pytest
from tsukuyomi.agents.prompts.immersive_prompt import (
    PromptContext,
    ImmersivePromptBuilder,
    create_prompt_context
)
from tsukuyomi.agents.core.identity import (
    AgentIdentity,
    CoreValue,
    DefiningMemory,
    PersonalityTraits,
    create_identity
)
from tsukuyomi.agents.cognitive.memory.memory_system import LongTermMemory


class TestPromptContext:
    """Tests for PromptContext."""
    
    def test_create_context(self):
        """Test creating basic context."""
        ctx = PromptContext(
            current_situation="You are in a jury room discussing a murder case.",
            recent_events=["Heard testimony", "Saw evidence"],
            present_characters=["Sarah", "Jack", "Arthur"],
            current_goal="Decide the verdict",
            emotional_state="Frustrated"
        )
        
        assert "jury room" in ctx.current_situation
        assert len(ctx.recent_events) == 2
        assert "Sarah" in ctx.present_characters
        assert ctx.emotional_state == "Frustrated"
    
    def test_default_lists(self):
        """Test default empty lists."""
        ctx = PromptContext(current_situation="Test")
        
        assert ctx.recent_events == []
        assert ctx.present_characters == []
    
    def test_helper_function(self):
        """Test create_prompt_context helper."""
        ctx = create_prompt_context(
            situation="Test situation",
            recent_events=["Event 1"],
            emotional_state="Calm"
        )
        
        assert ctx.current_situation == "Test situation"
        assert ctx.emotional_state == "Calm"


class TestImmersivePromptBuilder:
    """Tests for ImmersivePromptBuilder."""
    
    @pytest.fixture
    def simple_identity(self):
        """Create a simple identity for testing."""
        return create_identity(
            name="John Doe",
            age=45,
            occupation="Factory Worker",
            origin_story="Born and raised in Detroit. Worked 20 years at the auto plant. Just an ordinary guy trying to do right.",
            core_values=[
                {"value": "Hard work pays off", "source": "My father taught me", "intensity": 0.8}
            ],
            defining_memories=[
                {
                    "event": "Plant closed down",
                    "emotional_impact": "Lost and angry",
                    "lesson_learned": "Nothing is guaranteed",
                    "when_occurred": "Age 40"
                }
            ],
            personality={
                "big_five": {"conscientiousness": 0.5, "agreeableness": -0.3},
                "specific_traits": {"stubbornness": 0.7},
                "triggers": ["lazy people"]
            }
        )
    
    @pytest.fixture
    def builder(self, simple_identity):
        """Create builder with simple identity."""
        return ImmersivePromptBuilder(
            identity=simple_identity,
            scenario_name="jury deliberation"
        )
    
    @pytest.fixture
    def context(self):
        """Create test context."""
        return PromptContext(
            current_situation="You are in a jury room. Eleven people have voted guilty. You are the only one who voted not guilty.",
            recent_events=["Heard the evidence", "First vote taken"],
            present_characters=["Eleven other jurors"],
            current_goal="Convince others to reconsider",
            emotional_state="Confident but pressured"
        )
    
    def test_builder_initialization(self, simple_identity):
        """Test builder initialization."""
        builder = ImmersivePromptBuilder(
            identity=simple_identity,
            scenario_name="test_scenario"
        )
        
        assert builder.agents.core.identity.name == "John Doe"
        assert builder.scenario_name == "test_scenario"
    
    def test_build_full_prompt(self, builder, context):
        """Test full prompt generation."""
        prompt = builder.build_system_prompt(context, style="full")
        
        # Check identity appears (uppercase in header)
        assert "JOHN DOE" in prompt or "John Doe" in prompt
        assert "45" in prompt
        assert "Factory Worker" in prompt
        
        # Check core values appear
        assert "Hard work pays off" in prompt
        
        # Check memories appear
        assert "Plant closed down" in prompt
        
        # Check situation appears
        assert "jury room" in prompt
        
        # Check rules appear - prompt says "not an AI assistant"
        assert "ai assistant" in prompt.lower()
    
    def test_build_concise_prompt(self, builder, context):
        """Test concise prompt generation."""
        prompt = builder.build_system_prompt(context, style="concise")
        
        # Should be much shorter
        assert len(prompt) < len(builder.build_system_prompt(context, style="full"))
        
        # Should still have identity
        assert "John Doe" in prompt
        
        # Should have situation
        assert "Right now" in prompt or "jury" in prompt
    
    def test_build_intense_prompt(self, builder, context):
        """Test intense prompt generation."""
        prompt = builder.build_system_prompt(context, style="intense")
        
        # Should have identity (uppercase in header)
        assert "JOHN DOE" in prompt
        
        # Should have intense framing
        assert "NOT PLAYING A ROLE" in prompt or "YOU ARE" in prompt
        
        # Should have emotional state
        assert "CONFIDENT" in prompt.upper() or "pressured" in prompt.lower()
    
    def test_identity_section(self, builder):
        """Test identity section generation."""
        section = builder._identity_section()
        
        assert "JOHN DOE" in section
        assert "45" in section
        assert "Factory Worker" in section
        assert "Detroit" in section
    
    def test_emotional_baseline_section(self, builder):
        """Test emotional baseline section."""
        section = builder._emotional_baseline_section()
        
        assert "EMOTIONAL BASELINE" in section
        assert "mood" in section.lower() or "tendency" in section.lower()
        assert "trigger" in section.lower()
    
    def test_personality_section(self, builder):
        """Test personality section."""
        section = builder._personality_section()
        
        assert "PERSONALITY" in section
        # Should describe traits - check for various trait indicators
        assert "stubborn" in section.lower() or "organized" in section.lower() or "disciplined" in section.lower()
    
    def test_memories_section(self, builder):
        """Test memories section."""
        section = builder._memories_section()
        
        assert "DEFINING MOMENTS" in section or "CORE VALUES" in section
        assert "Plant closed down" in section
        assert "Hard work pays off" in section
    
    def test_current_state_section(self, builder, context):
        """Test current state section."""
        section = builder._current_state_section(context)
        
        assert "RIGHT NOW" in section
        assert "Confident" in section or "pressured" in section
        assert "jurors" in section.lower() or "people present" in section.lower()
    
    def test_situation_section(self, builder, context):
        """Test situation section."""
        section = builder._situation_section(context)
        
        assert "SITUATION" in section
        assert "jury room" in section.lower()
    
    def test_rules_section(self, builder):
        """Test rules section."""
        section = builder._rules_section(PromptContext(current_situation="Test"))
        
        assert "HOW TO RESPOND" in section or "not an AI" in section.lower()
        assert "Stay true" in section or "consistent" in section.lower()
    
    def test_valence_description(self, builder):
        """Test valence to description conversion."""
        assert "positive" in builder._valence_description(0.7).lower()
        assert "pessimistic" in builder._valence_description(-0.7).lower()
        assert "balanced" in builder._valence_description(0.0).lower()
    
    def test_arousal_description(self, builder):
        """Test arousal to description conversion."""
        assert "high energy" in builder._arousal_description(0.9).lower()
        assert "low energy" in builder._arousal_description(0.1).lower()
        assert "moderate" in builder._arousal_description(0.5).lower()
    
    def test_dominance_description(self, builder):
        """Test dominance to description conversion."""
        assert "assertive" in builder._dominance_description(0.7).lower()
        assert "submissive" in builder._dominance_description(-0.7).lower()
        assert "flexible" in builder._dominance_description(0.0).lower()


class TestImmersivePromptBuilderWithMemory:
    """Tests with memory integration."""
    
    @pytest.fixture
    def identity_with_memory(self):
        """Create identity and memory system."""
        identity = create_identity(
            name="Sarah Chen",
            age=35,
            occupation="Nurse",
            origin_story="Worked in emergency rooms for 10 years. Seen life and death up close.",
            core_values=[
                {"value": "Every life matters", "source": "ER experience", "intensity": 0.9}
            ],
            defining_memories=[],
            personality={"big_five": {"agreeableness": 0.7}, "specific_traits": {"empathy": 0.9}}
        )
        
        memory = LongTermMemory(agent_id="sarah_test")
        
        return identity, memory
    
    @pytest.mark.asyncio
    async def test_build_with_memory(self, identity_with_memory):
        """Test prompt building with memory retrieval."""
        identity, memory = identity_with_memory
        
        # Store some memories
        memory.store(
            content="Patient died on my shift last week",
            keywords=["patient", "death", "emergency"],
            importance=0.8,
            tick=100
        )
        
        builder = ImmersivePromptBuilder(
            identity=identity,
            memory_system=memory,
            scenario_name="jury"
        )
        
        context = PromptContext(
            current_situation="Discussing a life-and-death decision in the jury room",
            emotional_state="Conflicted"
        )
        
        prompt = await builder.build_prompt_with_memory(
            context=context,
            tick=200,
            style="full"
        )
        
        # Should have identity (uppercase in header)
        assert "SARAH CHEN" in prompt or "Sarah Chen" in prompt
        
        # Should have situation
        assert "jury" in prompt.lower()


class TestPromptStyles:
    """Test different prompt styles."""
    
    @pytest.fixture
    def builder(self):
        """Create builder."""
        identity = create_identity(
            name="Arthur Miller",
            age=58,
            occupation="Retired Factory Worker",
            origin_story="Worked hard all my life. My son walked out on me two years ago.",
            core_values=[
                {"value": "Personal responsibility", "source": "Life experience", "intensity": 1.0}
            ],
            defining_memories=[{
                "event": "Son abandoned me",
                "emotional_impact": "Anger, betrayal",
                "lesson_learned": "Kids these days have no respect",
                "when_occurred": "2 years ago"
            }],
            personality={
                "big_five": {"neuroticism": 0.5, "agreeableness": -0.4},
                "specific_traits": {"stubbornness": 0.9, "cynicism": 0.8},
                "triggers": ["disrespect", "lazy excuses"]
            }
        )
        
        return ImmersivePromptBuilder(identity=identity, scenario_name="12 Angry Men")
    
    @pytest.fixture
    def context(self):
        """Create context."""
        return PromptContext(
            current_situation="Someone is questioning your motives. They think you're biased.",
            emotional_state="Angry and defensive",
            recent_events=["Your past was brought up", "People are looking at you"]
        )
    
    def test_full_vs_concise_length(self, builder, context):
        """Test that full is longer than concise."""
        full = builder.build_system_prompt(context, "full")
        concise = builder.build_system_prompt(context, "concise")
        
        assert len(full) > len(concise)
    
    def test_intense_has_strong_framing(self, builder, context):
        """Test intense style has strong psychological framing."""
        intense = builder.build_system_prompt(context, "intense")
        
        # Should have identity (uppercase in header)
        assert "ARTHUR MILLER" in intense or "Arthur Miller" in intense
        
        # Should have intense framing
        assert "NOT PLAYING A ROLE" in intense or "YOU ARE THIS PERSON" in intense.upper() or "YOU ARE" in intense
        
        # Should have emotional state emphasized
        assert "ANGRY" in intense.upper() or "defensive" in intense.lower()
    
    def test_all_styles_have_identity(self, builder, context):
        """Test all styles include basic identity."""
        for style in ["full", "concise", "intense"]:
            prompt = builder.build_system_prompt(context, style)
            assert "ARTHUR MILLER" in prompt or "Arthur Miller" in prompt, f"Style {style} missing identity"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_identity(self):
        """Test with minimal identity."""
        identity = AgentIdentity(name="Minimal")
        builder = ImmersivePromptBuilder(identity=identity)
        
        context = PromptContext(current_situation="Test")
        prompt = builder.build_system_prompt(context)
        
        # Should have uppercase header with name
        assert "MINIMAL" in prompt or "Minimal" in prompt
    
    def test_empty_context(self):
        """Test with minimal context."""
        identity = AgentIdentity(name="Test")
        builder = ImmersivePromptBuilder(identity=identity)
        
        context = PromptContext(current_situation="")
        prompt = builder.build_system_prompt(context)
        
        # Should still generate valid prompt with uppercase header
        assert "TEST" in prompt or "Test" in prompt
    
    def test_unknown_style_falls_back(self):
        """Test unknown style falls back to full."""
        identity = AgentIdentity(name="Test")
        builder = ImmersivePromptBuilder(identity=identity)
        
        context = PromptContext(current_situation="Test")
        prompt = builder.build_system_prompt(context, style="unknown")
        
        # Should still work
        assert "Test" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])