"""
Unit Tests for Agent Identity System
====================================

Tests for CoreValue, DefiningMemory, PersonalityTraits, and AgentIdentity.
"""

import pytest
import json
from tsukuyomi.agents.core.identity import (
    CoreValue,
    DefiningMemory,
    PersonalityTraits,
    AgentIdentity,
    create_identity
)


class TestCoreValue:
    """Tests for CoreValue dataclass."""
    
    def test_create_core_value(self):
        """Test creating a basic core value."""
        cv = CoreValue(
            value="Justice must be served",
            source="My father was wrongly accused",
            intensity=0.9,
            non_negotiable=True
        )
        
        assert cv.value == "Justice must be served"
        assert cv.source == "My father was wrongly accused"
        assert cv.intensity == 0.9
        assert cv.non_negotiable is True
    
    def test_intensity_bounds(self):
        """Test intensity must be 0.0-1.0."""
        with pytest.raises(ValueError):
            CoreValue(value="test", source="test", intensity=1.5)
        
        with pytest.raises(ValueError):
            CoreValue(value="test", source="test", intensity=-0.5)
    
    def test_to_dict(self):
        """Test serialization to dict."""
        cv = CoreValue(
            value="Truth matters",
            source="Personal experience",
            intensity=0.7,
            non_negotiable=False
        )
        
        d = cv.to_dict()
        
        assert d["value"] == "Truth matters"
        assert d["source"] == "Personal experience"
        assert d["intensity"] == 0.7
        assert d["non_negotiable"] is False
    
    def test_default_intensity(self):
        """Test default intensity value."""
        cv = CoreValue(value="Test", source="Test source")
        assert cv.intensity == 0.8  # Default


class TestDefiningMemory:
    """Tests for DefiningMemory dataclass."""
    
    def test_create_defining_memory(self):
        """Test creating a defining memory."""
        dm = DefiningMemory(
            event="Father abandoned family",
            emotional_impact="Deep sense of betrayal and mistrust",
            lesson_learned="Never abandon those who depend on you",
            tags=["family", "betrayal", "trust"],
            importance=0.9,
            when_occurred="Age 12"
        )
        
        assert dm.event == "Father abandoned family"
        assert dm.emotional_impact == "Deep sense of betrayal and mistrust"
        assert "family" in dm.tags
        assert dm.importance == 0.9
        assert dm.when_occurred == "Age 12"
    
    def test_default_importance(self):
        """Test default importance."""
        dm = DefiningMemory(event="Test", emotional_impact="Test")
        assert dm.importance == 1.0
    
    def test_importance_bounds(self):
        """Test importance must be 0.0-1.0."""
        with pytest.raises(ValueError):
            DefiningMemory(event="test", importance=2.0)
    
    def test_to_dict(self):
        """Test serialization to dict."""
        dm = DefiningMemory(
            event="Won championship",
            emotional_impact="Pride and accomplishment",
            lesson_learned="Hard work pays off",
            tags=["sports", "success"],
            importance=0.8,
            when_occurred="Age 18"
        )
        
        d = dm.to_dict()
        
        assert d["event"] == "Won championship"
        assert d["emotional_impact"] == "Pride and accomplishment"
        assert d["tags"] == ["sports", "success"]
        assert d["importance"] == 0.8
        assert d["when_occurred"] == "Age 18"
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "event": "Test event",
            "emotional_impact": "Test impact",
            "lesson_learned": "Test lesson",
            "tags": ["tag1", "tag2"],
            "importance": 0.7,
            "when_occurred": "Age 20"
        }
        
        dm = DefiningMemory.from_dict(data)
        
        assert dm.event == "Test event"
        assert dm.lesson_learned == "Test lesson"
        assert dm.tags == ["tag1", "tag2"]
    
    def test_uuid_generation(self):
        """Test unique ID generation."""
        dm1 = DefiningMemory(event="Event 1", emotional_impact="Impact 1")
        dm2 = DefiningMemory(event="Event 2", emotional_impact="Impact 2")
        
        assert dm1.id != dm2.id


class TestPersonalityTraits:
    """Tests for PersonalityTraits dataclass."""
    
    def test_create_personality(self):
        """Test creating personality traits."""
        pt = PersonalityTraits(
            openness=0.5,
            conscientiousness=0.3,
            extraversion=-0.2,
            agreeableness=0.4,
            neuroticism=0.6,
            stubbornness=0.8,
            empathy=0.4,
            triggers=["injustice", "betrayal"]
        )
        
        assert pt.openness == 0.5
        assert pt.stubbornness == 0.8
        assert "injustice" in pt.triggers
    
    def test_big_five_bounds(self):
        """Test Big Five scores must be -1.0 to 1.0."""
        with pytest.raises(ValueError):
            PersonalityTraits(openness=2.0)
        
        with pytest.raises(ValueError):
            PersonalityTraits(conscientiousness=-2.0)
    
    def test_specific_trait_bounds(self):
        """Test specific traits must be 0.0 to 1.0."""
        with pytest.raises(ValueError):
            PersonalityTraits(stubbornness=1.5)
        
        with pytest.raises(ValueError):
            PersonalityTraits(empathy=-0.5)
    
    def test_get_big_five_dict(self):
        """Test Big Five dictionary generation."""
        pt = PersonalityTraits(
            openness=0.5,
            conscientiousness=0.3,
            extraversion=-0.2,
            agreeableness=0.4,
            neuroticism=0.6
        )
        
        d = pt.get_big_five_dict()
        
        assert d["openness"] == 0.5
        assert d["conscientiousness"] == 0.3
        assert d["extraversion"] == -0.2
    
    def test_get_summary(self):
        """Test personality summary generation."""
        pt = PersonalityTraits(
            openness=0.5,
            agreeableness=-0.4,
            neuroticism=0.5,
            stubbornness=0.8,
            cynicism=0.7
        )
        
        summary = pt.get_summary()
        
        assert "open-minded" in summary
        assert "competitive" in summary
        assert "emotional" in summary
        assert "stubborn" in summary
        assert "cynical" in summary
    
    def test_default_values(self):
        """Test default trait values."""
        pt = PersonalityTraits()
        
        assert pt.openness == 0.0
        assert pt.stubbornness == 0.5
        assert pt.empathy == 0.5
        assert pt.humor_style == "dry"
    
    def test_to_dict(self):
        """Test serialization to dict."""
        pt = PersonalityTraits(
            openness=0.3,
            stubbornness=0.7,
            triggers=["pain", "loss"]
        )
        
        d = pt.to_dict()
        
        assert d["big_five"]["openness"] == 0.3
        assert d["specific_traits"]["stubbornness"] == 0.7
        assert "pain" in d["triggers"]
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "big_five": {"openness": 0.5, "neuroticism": 0.3},
            "specific_traits": {"stubbornness": 0.8},
            "triggers": ["test_trigger"]
        }
        
        pt = PersonalityTraits.from_dict(data)
        
        assert pt.openness == 0.5
        assert pt.neuroticism == 0.3
        assert pt.stubbornness == 0.8
        assert "test_trigger" in pt.triggers


class TestAgentIdentity:
    """Tests for AgentIdentity dataclass."""
    
    def test_create_identity(self):
        """Test creating a full agent identity."""
        cv = CoreValue(value="Test value", source="Test source")
        dm = DefiningMemory(
            event="Test event",
            emotional_impact="Test impact",
            lesson_learned="Test lesson"
        )
        pt = PersonalityTraits(stubbornness=0.8)
        
        identity = AgentIdentity(
            name="John Doe",
            age=45,
            occupation="Lawyer",
            origin_story="Born in small town, worked hard...",
            core_values=[cv],
            defining_memories=[dm],
            personality=pt
        )
        
        assert identity.name == "John Doe"
        assert identity.age == 45
        assert identity.occupation == "Lawyer"
        assert len(identity.core_values) == 1
        assert len(identity.defining_memories) == 1
    
    def test_default_personality(self):
        """Test default personality is created."""
        identity = AgentIdentity(name="Test")
        
        assert identity.agents.internal.personality is not None
        assert isinstance(identity.agents.internal.personality, PersonalityTraits)
    
    def test_get_baseline_pad(self):
        """Test PAD baseline retrieval."""
        identity = AgentIdentity(
            name="Test",
            baseline_valence=0.3,
            baseline_arousal=0.6,
            baseline_dominance=-0.2
        )
        
        pad = identity.get_baseline_pad()
        
        assert pad["valence"] == 0.3
        assert pad["arousal"] == 0.6
        assert pad["dominance"] == -0.2
    
    def test_get_core_values_summary(self):
        """Test core values summary."""
        identity = AgentIdentity(
            name="Test",
            core_values=[
                CoreValue(value="Justice", source="Test", intensity=0.9),
                CoreValue(value="Truth", source="Test", intensity=0.5)
            ]
        )
        
        summary = identity.get_core_values_summary()
        
        assert "Justice" in summary
        assert "Truth" in summary
    
    def test_get_defining_memories_summary(self):
        """Test defining memories summary."""
        identity = AgentIdentity(
            name="Test",
            defining_memories=[
                DefiningMemory(
                    event="Father died",
                    emotional_impact="Sad",
                    lesson_learned="Life is short",
                    when_occurred="Age 20"
                )
            ]
        )
        
        summary = identity.get_defining_memories_summary()
        
        assert "Father died" in summary
        assert "Age 20" in summary
    
    def test_get_immersive_description(self):
        """Test immersive description generation."""
        identity = AgentIdentity(
            name="Arthur Miller",
            age=58,
            occupation="Retired Factory Worker",
            origin_story="Grew up in the slums. Worked 40 years in the steel mill.",
            core_values=[
                CoreValue(
                    value="Personal responsibility",
                    source="My father taught me",
                    intensity=0.9
                )
            ],
            defining_memories=[
                DefiningMemory(
                    event="Son walked out",
                    emotional_impact="Abandoned, angry",
                    lesson_learned="Kids these days",
                    when_occurred="2 years ago"
                )
            ]
        )
        
        desc = identity.get_immersive_description()
        
        assert "Arthur Miller" in desc
        assert "58" in desc
        assert "Personal responsibility" in desc
        assert "Son walked out" in desc
    
    def test_to_dict(self):
        """Test serialization to dict."""
        identity = AgentIdentity(
            name="Test",
            age=30,
            core_values=[CoreValue(value="Test", source="Test")],
            defining_memories=[DefiningMemory(
                event="Test",
                emotional_impact="Test"
            )]
        )
        
        d = identity.to_dict()
        
        assert d["name"] == "Test"
        assert d["age"] == 30
        assert len(d["core_values"]) == 1
        assert len(d["defining_memories"]) == 1
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "name": "Test Agent",
            "age": 40,
            "occupation": "Teacher",
            "origin_story": "Test story",
            "core_values": [
                {"value": "Value 1", "source": "Source 1", "intensity": 0.8, "non_negotiable": True}
            ],
            "defining_memories": [
                {"event": "Event 1", "emotional_impact": "Impact 1", "lesson_learned": "Lesson 1"}
            ],
            "personality": {
                "big_five": {"openness": 0.5},
                "specific_traits": {"stubbornness": 0.6},
                "triggers": ["trigger1"]
            },
            "baseline_pad": {"valence": 0.2, "arousal": 0.5, "dominance": 0.1}
        }
        
        identity = AgentIdentity.from_dict(data)
        
        assert identity.name == "Test Agent"
        assert identity.age == 40
        assert identity.occupation == "Teacher"
        assert len(identity.core_values) == 1
        assert identity.core_values[0].value == "Value 1"
        assert identity.agents.internal.personality.openness == 0.5
        assert identity.baseline_valence == 0.2


class TestCreateIdentity:
    """Tests for create_identity helper function."""
    
    def test_create_complete_identity(self):
        """Test creating identity via helper."""
        identity = create_identity(
            name="Sarah Chen",
            age=35,
            occupation="Nurse",
            origin_story="Came from a family of healers...",
            core_values=[
                {"value": "Compassion above all", "source": "Mother", "intensity": 0.9}
            ],
            defining_memories=[
                {
                    "event": "Saved a child's life",
                    "emotional_impact": "Pride",
                    "lesson_learned": "This is my purpose",
                    "tags": ["medical", "purpose"],
                    "when_occurred": "Age 25"
                }
            ],
            personality={
                "big_five": {"agreeableness": 0.8},
                "specific_traits": {"empathy": 0.9},
                "triggers": ["child endangerment"]
            }
        )
        
        assert identity.name == "Sarah Chen"
        assert identity.age == 35
        assert identity.occupation == "Nurse"
        assert len(identity.core_values) == 1
        assert identity.agents.internal.personality.empathy == 0.9
    
    def test_create_identity_with_defaults(self):
        """Test creating minimal identity."""
        identity = create_identity(
            name="Minimal",
            age=25,
            occupation="Student",
            origin_story="Just a student.",
            core_values=[],
            defining_memories=[],
            personality={}
        )
        
        assert identity.name == "Minimal"
        assert identity.agents.internal.personality is not None


class TestRoundTripSerialization:
    """Test full serialization round trip."""
    
    def test_full_round_trip(self):
        """Test identity can be serialized and deserialized."""
        original = create_identity(
            name="Test Round Trip",
            age=50,
            occupation="Detective",
            origin_story="30 years on the force.",
            core_values=[
                {"value": "The truth matters", "source": "First case", "intensity": 1.0}
            ],
            defining_memories=[
                {
                    "event": "Cold case solved",
                    "emotional_impact": "Satisfaction",
                    "lesson_learned": "Never give up",
                    "tags": ["justice"],
                    "when_occurred": "Age 40"
                }
            ],
            personality={
                "big_five": {"neuroticism": 0.3},
                "specific_traits": {"cynicism": 0.7},
                "triggers": ["incompetence"]
            }
        )
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = AgentIdentity.from_dict(data)
        
        # Verify
        assert restored.name == original.name
        assert restored.age == original.age
        assert restored.core_values[0].value == original.core_values[0].value
        assert restored.defining_memories[0].event == original.defining_memories[0].event
        assert restored.agents.internal.personality.cynicism == original.agents.internal.personality.cynicism


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
