"""
Tests for Tsukuyomi Brain Personality Module (Phase 14)

Run with: python -m pytest tests/test_personality.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.internal.personality import (
    PersonalityProfile, VocabularyLevel, build_personality_context,
    get_sample_profile, PersonalityConstraintSampler, PersonalityDriftMonitor
)


class TestPersonalityProfile:
    def test_create_profile(self):
        profile = PersonalityProfile(
            name="Test", age=30, role="Test",
            openness=0.5, conscientiousness=0.5,
            extraversion=0.5, agreeableness=0.5, neuroticism=0.5
        )
        assert profile.name == "Test"

    def test_sample_profiles(self):
        angry_man = get_sample_profile("angry_man")
        assert angry_man is not None

    def test_build_context(self):
        profile = get_sample_profile("angry_man")
        context = build_personality_context(profile)
        assert len(context) > 0


class TestPersonalityConstraintSampler:
    def test_create_sampler(self):
        profile = get_sample_profile("angry_man")
        sampler = PersonalityConstraintSampler(profile)
        assert sampler is not None

    def test_build_constraints(self):
        profile = get_sample_profile("angry_man")
        sampler = PersonalityConstraintSampler(profile)
        constraints = sampler.build_generation_constraints()
        assert constraints is not None


class TestPersonalityDriftMonitor:
    def test_create_monitor(self):
        profile = get_sample_profile("angry_man")
        monitor = PersonalityDriftMonitor(profile)
        assert monitor is not None

    def test_analyze_response(self):
        profile = get_sample_profile("angry_man")
        monitor = PersonalityDriftMonitor(profile)
        report = monitor.analyze_response("Test response", {}, 1)
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
