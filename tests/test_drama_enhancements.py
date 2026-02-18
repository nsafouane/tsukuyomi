"""
Tests for Drama Director Enhancements
=====================================

Tests for:
- Dynamic Tension Calculation
- Time-Based Act Fallback
- Dynamic Drama Beats Generation
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiments.angry_men.drama.director import (
    DramaDirector,
    DramaBeat,
    NarrativeState,
    Act
)


class TestDynamicTension:
    """Test enhanced tension calculation."""
    
    @pytest.fixture
    def director(self):
        """Create a drama director for testing."""
        case_config = {"drama_beats": []}
        return DramaDirector(case_config)
    
    def test_tension_time_floor_rises(self, director):
        """Time floor should rise as progress increases."""
        # At start (tick 0)
        tension_0 = director.update_tension(
            {"agent1": {"arousal": 0.3, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 5, "not_guilty": 0},
            tick=0,
            total_ticks=1000
        )
        
        # At 75% progress (tick 750)
        tension_75 = director.update_tension(
            {"agent1": {"arousal": 0.3, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 5, "not_guilty": 0},
            tick=750,
            total_ticks=1000
        )
        
        # Floor should be higher at 75%
        assert tension_75 >= tension_0
    
    def test_tension_with_existential_events(self, director):
        """Existential events should add to tension."""
        # Without existential events
        tension_no_exist = director.update_tension(
            {"agent1": {"arousal": 0.5, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 3, "not_guilty": 2},
            tick=500,
            total_ticks=1000
        )
        
        # With existential events
        existential_events = [
            {"type": "existential", "impact": 0.8, "recency": 1.0}
        ]
        tension_exist = director.update_tension(
            {"agent1": {"arousal": 0.5, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 3, "not_guilty": 2},
            tick=500,
            total_ticks=1000,
            existential_events=existential_events
        )
        
        assert tension_exist >= tension_no_exist
    
    def test_tension_doesnt_flatline_at_unanimous(self, director):
        """Tension should not flatline after unanimous vote."""
        # Unanimous vote - traditionally would give 0 vote tension
        tension = director.update_tension(
            {"agent1": {"arousal": 0.3, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 5, "not_guilty": 0},  # Unanimous guilty
            tick=800,
            total_ticks=1000
        )
        
        # Despite unanimous, tension should still be present due to time floor
        assert tension > 0.1
    
    def test_emotional_intensity_adds_tension(self, director):
        """High arousal should add intensity bonus."""
        # Low arousal
        tension_low = director.update_tension(
            {"agent1": {"arousal": 0.3, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 3, "not_guilty": 2},
            tick=500,
            total_ticks=1000
        )
        
        # High arousal
        tension_high = director.update_tension(
            {"agent1": {"arousal": 0.9, "valence": 0.0, "dominance": 0.5}},
            vote_state={"guilty": 3, "not_guilty": 2},
            tick=500,
            total_ticks=1000
        )
        
        assert tension_high > tension_low


class TestActTransitions:
    """Test time-based act transition fallback."""
    
    @pytest.fixture
    def director(self):
        case_config = {"drama_beats": []}
        return DramaDirector(case_config)
    
    def test_confrontation_to_climax_time_fallback(self, director):
        """CLIMAX should trigger at 70% even with low tension."""
        director.state.current_act = Act.CONFRONTATION
        director.state.tension_level = 0.1  # Low tension
        
        # At 70% progress
        transition = director.get_act_transition(tick=700, total_ticks=1000)
        
        assert transition == Act.CLIMAX
    
    def test_climax_to_resolution_at_85_percent(self, director):
        """RESOLUTION should trigger at 85%."""
        director.state.current_act = Act.CLIMAX
        director.state.tension_level = 0.3
        
        # At 85% progress
        transition = director.get_act_transition(tick=850, total_ticks=1000)
        
        assert transition == Act.RESOLUTION


class TestDynamicDramaBeats:
    """Test dynamic beat generation."""
    
    @pytest.fixture
    def director(self):
        case_config = {"drama_beats": []}
        return DramaDirector(case_config)
    
    def test_generate_beat_on_stalemate(self, director):
        """Should generate beat when debate is stuck."""
        # Create stalemate (same vote for last 6 votes - minimum required)
        director.state.vote_history = [
            {"not_guilty": 3},
            {"not_guilty": 3},
            {"not_guilty": 3},
            {"not_guilty": 3},
            {"not_guilty": 3},
            {"not_guilty": 3},
        ]
        
        # Also set last_dramatic_moment to older tick to allow triggering
        director.state.last_dramatic_moment = 50
        
        beat = director.generate_dynamic_beat(
            tick=200,
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={"agent1": {"arousal": 0.4, "valence": 0.0, "dominance": 0.5}},
            recent_events=[]
        )
        
        assert beat is not None
    
    def test_generate_beat_on_vote_shift(self, director):
        """Should generate beat on vote shift."""
        director.state.vote_history = [
            {"not_guilty": 2},
            {"not_guilty": 3},  # Shift!
        ]
        
        beat = director.generate_dynamic_beat(
            tick=200,
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={"agent1": {"arousal": 0.4, "valence": 0.0, "dominance": 0.5}},
            recent_events=[]
        )
        
        assert beat is not None
        assert "vote" in beat.name.lower() or "shift" in beat.name.lower()
    
    def test_generate_beat_on_existential(self, director):
        """Should generate beat on existential events."""
        recent_events = [
            {"type": "existential", "content": "Nothing is real", "impact": 0.9}
        ]
        
        beat = director.generate_dynamic_beat(
            tick=200,
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={"agent1": {"arousal": 0.4, "valence": 0.0, "dominance": 0.5}},
            recent_events=recent_events
        )
        
        assert beat is not None
        assert "existential" in beat.name.lower()
    
    def test_no_beat_too_soon(self, director):
        """Should not generate beat if one was just triggered."""
        director.state.last_dramatic_moment = 100  # Just triggered at tick 100
        
        beat = director.generate_dynamic_beat(
            tick=120,  # Only 20 ticks later
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={"agent1": {"arousal": 0.4, "valence": 0.0, "dominance": 0.5}},
            recent_events=[]
        )
        
        assert beat is None
    
    def test_beat_type_determination(self, director):
        """Test beat type determination logic."""
        # Test existential detection
        beat_type = director._determine_beat_type(
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={},
            recent_events=[{"type": "existential"}]
        )
        assert beat_type == "existential_response"
        
        # Test stalemate detection
        director.state.vote_history = [{"not_guilty": 3}] * 6
        beat_type = director._determine_beat_type(
            vote_state={"guilty": 2, "not_guilty": 3},
            agent_emotions={},
            recent_events=[]
        )
        assert beat_type == "break_stalemate"


class TestBeatContentGeneration:
    """Test beat content templates."""
    
    @pytest.fixture
    def director(self):
        case_config = {"drama_beats": []}
        return DramaDirector(case_config)
    
    def test_beat_content_has_required_fields(self, director):
        """Generated beat content should have all required fields."""
        content = director._generate_beat_content(
            "vote_shift",
            {"guilty": 2, "not_guilty": 3},
            {"agent1": {"arousal": 0.5}}
        )
        
        assert "name" in content
        assert "description" in content
        assert "emotion" in content
        assert "instruction" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
