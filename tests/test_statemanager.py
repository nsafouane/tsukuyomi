"""
Comprehensive test suite for StateManager.py

This test suite validates:
1. PAD Emotional Model
2. Personality Baseline mapping
3. Emotional Impact Rules
4. Emotional Inertia (arousal scaling)
5. Episode tracking and decay
6. Regression to baseline
7. Mood label derivation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.StateManager import (
    StateManager,
    PersonalityBaseline,
    EmotionalImpact,
    EmotionalEpisode,
    EmotionalState,
    MoodLabel,
    EmotionalImpactRules,
    create_state_manager_from_big_five
)


def test_personality_baselines():
    """Test pre-defined personality profiles."""
    print("\n=== Test 1: Personality Baselines ===")
    
    angry = PersonalityBaseline.ANGRY_MAN
    print(f"Angry Man: V={angry.valence_baseline}, A={angry.arousal_baseline}, D={angry.dominance_baseline}")
    assert angry.valence_baseline < 0  # Negative valence
    assert angry.arousal_baseline > 0.5  # High arousal
    assert angry.dominance_baseline > 0  # Dominant
    
    teller = PersonalityBaseline.BANK_TELLER
    print(f"Bank Teller: V={teller.valence_baseline}, A={teller.arousal_baseline}, D={teller.dominance_baseline}")
    assert teller.arousal_baseline < 0.5  # Low arousal
    assert teller.dominance_baseline < 0  # Submissive
    
    print("✓ Personality baselines verified")


def test_big_five_mapping():
    """Test Big Five to PAD mapping."""
    print("\n=== Test 2: Big Five to PAD Mapping ===")
    
    # High extraversion should increase arousal and dominance
    extraverted = PersonalityBaseline.from_big_five(
        openness=0.0,
        conscientiousness=0.0,
        extraversion=0.9,
        agreeableness=0.0,
        neuroticism=0.0
    )
    print(f"High Extraversion: V={extraverted.valence_baseline:.2f}, A={extraverted.arousal_baseline:.2f}, D={extraverted.dominance_baseline:.2f}")
    assert extraverted.arousal_baseline > 0.5
    assert extraverted.dominance_baseline > 0
    
    # High neuroticism should decrease valence and increase arousal
    neurotic = PersonalityBaseline.from_big_five(
        openness=0.0,
        conscientiousness=0.0,
        extraversion=0.0,
        agreeableness=0.0,
        neuroticism=0.9
    )
    print(f"High Neuroticism: V={neurotic.valence_baseline:.2f}, A={neurotic.arousal_baseline:.2f}, D={neurotic.dominance_baseline:.2f}")
    assert neurotic.valence_baseline < 0
    assert neurotic.arousal_baseline > 0.5
    
    # High agreeableness should increase valence and decrease dominance
    agreeable = PersonalityBaseline.from_big_five(
        openness=0.0,
        conscientiousness=0.0,
        extraversion=0.0,
        agreeableness=0.9,
        neuroticism=0.0
    )
    print(f"High Agreeableness: V={agreeable.valence_baseline:.2f}, A={agreeable.arousal_baseline:.2f}, D={agreeable.dominance_baseline:.2f}")
    assert agreeable.valence_baseline > 0
    assert agreeable.dominance_baseline < 0
    
    print("✓ Big Five mapping verified")


def test_pad_clamping():
    """Test that PAD values are clamped to valid ranges."""
    print("\n=== Test 3: PAD Value Clamping ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    
    # Try to exceed bounds
    sm.state.valence = 2.0  # Should be clamped to 1.0
    sm.state.arousal = 1.5  # Should be clamped to 1.0
    sm.state.dominance = -2.0  # Should be clamped to -1.0
    sm._clamp_state()
    
    assert sm.state.valence <= 1.0
    assert sm.state.arousal <= 1.0
    assert sm.state.arousal >= 0.0
    assert sm.state.dominance >= -1.0
    
    print(f"After clamping: V={sm.state.valence}, A={sm.state.arousal}, D={sm.state.dominance}")
    print("✓ PAD clamping verified")


def test_emotional_impacts():
    """Test that events correctly modify emotional state."""
    print("\n=== Test 4: Emotional Impact Rules ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    initial_valence = sm.state.valence
    initial_arousal = sm.state.arousal
    
    # Apply criticism
    sm.apply_event("criticized", tick_number=100)
    
    # Criticism should decrease valence and increase arousal
    assert sm.state.valence < initial_valence, "Valence should decrease after criticism"
    assert sm.state.arousal > initial_arousal, "Arousal should increase after criticism"
    
    print(f"Initial: V={initial_valence:.3f}, A={initial_arousal:.3f}")
    print(f"After criticism: V={sm.state.valence:.3f}, A={sm.state.arousal:.3f}")
    print("✓ Emotional impacts verified")


def test_emotional_inertia():
    """Test that arousal scales emotional shifts (Emotional Inertia)."""
    print("\n=== Test 5: Emotional Inertia ===")
    
    # Low arousal agent (stable)
    calm_baseline = PersonalityBaseline(
        valence_baseline=0.0,
        arousal_baseline=0.2,
        dominance_baseline=0.0,
        regression_rate=0.01
    )
    calm_sm = StateManager(calm_baseline)
    calm_initial = calm_sm.state.valence
    
    # High arousal agent (volatile)
    agitated_baseline = PersonalityBaseline(
        valence_baseline=0.0,
        arousal_baseline=0.8,
        dominance_baseline=0.0,
        regression_rate=0.01
    )
    agitated_sm = StateManager(agitated_baseline)
    agitated_initial = agitated_sm.state.valence
    
    # Apply same event to both
    calm_sm.apply_event("criticized", tick_number=100)
    agitated_sm.apply_event("criticized", tick_number=100)
    
    calm_shift = abs(calm_sm.state.valence - calm_initial)
    agitated_shift = abs(agitated_sm.state.valence - agitated_initial)
    
    print(f"Calm agent (A={calm_baseline.arousal_baseline}): shift = {calm_shift:.3f}")
    print(f"Agitated agent (A={agitated_baseline.arousal_baseline}): shift = {agitated_shift:.3f}")
    
    # High arousal agent should have larger shift
    assert agitated_shift > calm_shift, "High arousal agent should be more volatile"
    
    print("✓ Emotional inertia verified")


def test_episode_tracking():
    """Test emotional episode creation and decay."""
    print("\n=== Test 6: Episode Tracking ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    
    # Apply intense event (should create episode)
    sm.apply_event("physical_threat", tick_number=100)
    
    # Should have an active episode
    assert len(sm.state.active_episodes) > 0, "Intense event should create episode"
    
    episode = sm.state.active_episodes[0]
    assert episode.emotion_type == "fear", "Physical threat should create fear episode"
    assert episode.intensity > 0, "Episode should have intensity"
    
    initial_intensity = episode.intensity
    
    # Simulate decay
    for tick in range(101, 200):
        sm.update(tick, [])
    
    # Intensity should have decayed
    print(f"Initial intensity: {initial_intensity:.3f}")
    print(f"Decayed intensity: {episode.intensity:.3f}")
    assert episode.intensity < initial_intensity, "Episode intensity should decay"
    
    print("✓ Episode tracking verified")


def test_regression_to_baseline():
    """Test that emotional state regresses toward personality baseline."""
    print("\n=== Test 7: Regression to Baseline ===")
    
    baseline = PersonalityBaseline(
        valence_baseline=0.5,
        arousal_baseline=0.3,
        dominance_baseline=0.2,
        regression_rate=0.05  # Fast regression for testing
    )
    sm = StateManager(baseline)
    
    # Apply negative event to move away from baseline
    sm.apply_event("criticized", tick_number=100)
    moved_valence = sm.state.valence
    
    print(f"Baseline valence: {baseline.valence_baseline}")
    print(f"After criticism: {moved_valence:.3f}")
    
    # Simulate regression over many ticks
    for tick in range(101, 500):
        sm.update(tick, [])
    
    final_valence = sm.state.valence
    print(f"After regression: {final_valence:.3f}")
    
    # Should be closer to baseline
    assert abs(final_valence - baseline.valence_baseline) < abs(moved_valence - baseline.valence_baseline), \
        "State should regress toward baseline"
    
    print("✓ Regression to baseline verified")


def test_mood_labels():
    """Test mood label derivation from PAD values."""
    print("\n=== Test 8: Mood Label Derivation ===")
    
    # Test high arousal, high valence, high dominance -> elated
    sm1 = StateManager(PersonalityBaseline(
        valence_baseline=0.8,
        arousal_baseline=0.8,
        dominance_baseline=0.5,
        regression_rate=0.01
    ))
    print(f"V={sm1.state.valence}, A={sm1.state.arousal}, D={sm1.state.dominance} -> Mood: {sm1.state.mood_label}")
    assert sm1.state.mood_label in [MoodLabel.ELATED.value, MoodLabel.EXCITED.value]
    
    # Test low valence, high arousal, low dominance -> frustrated
    sm2 = StateManager(PersonalityBaseline(
        valence_baseline=-0.6,
        arousal_baseline=0.7,
        dominance_baseline=-0.3,
        regression_rate=0.01
    ))
    print(f"V={sm2.state.valence}, A={sm2.state.arousal}, D={sm2.state.dominance} -> Mood: {sm2.state.mood_label}")
    assert sm2.state.mood_label in [MoodLabel.FRUSTRATED.value, MoodLabel.HOSTILE.value]
    
    # Test low arousal, neutral valence -> calm
    sm3 = StateManager(PersonalityBaseline(
        valence_baseline=0.0,
        arousal_baseline=0.2,
        dominance_baseline=0.0,
        regression_rate=0.01
    ))
    print(f"V={sm3.state.valence}, A={sm3.state.arousal}, D={sm3.state.dominance} -> Mood: {sm3.state.mood_label}")
    assert sm3.state.mood_label in [MoodLabel.CALM.value, MoodLabel.RELAXED.value, MoodLabel.DROWSY.value]
    
    print("✓ Mood label derivation verified")


def test_state_serialization():
    """Test state serialization and deserialization."""
    print("\n=== Test 9: State Serialization ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    sm.apply_event("criticized", tick_number=100)
    
    # Serialize
    state_dict = sm.get_state_dict()
    
    # Check structure
    assert 'valence' in state_dict
    assert 'arousal' in state_dict
    assert 'dominance' in state_dict
    assert 'mood_label' in state_dict
    assert 'active_episodes' in state_dict
    
    print(f"Serialized state: {state_dict}")
    print("✓ State serialization verified")


def test_emotional_context():
    """Test generation of emotional context for LLM prompts."""
    print("\n=== Test 10: Emotional Context Generation ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    context = sm.get_emotional_context()
    
    print("Generated context:")
    print(context)
    
    # Check that context includes key information
    assert 'Mood:' in context
    assert 'Valence=' in context or 'valence' in context.lower()
    assert 'Arousal=' in context or 'arousal' in context.lower()
    assert 'Dominance=' in context or 'dominance' in context.lower()
    
    print("✓ Emotional context generation verified")


def test_reset_to_baseline():
    """Test resetting emotional state to baseline."""
    print("\n=== Test 11: Reset to Baseline ===")
    
    sm = StateManager(PersonalityBaseline.ANGRY_MAN)
    
    # Modify state
    sm.apply_event("criticized", tick_number=100)
    sm.apply_event("physical_threat", tick_number=101)
    
    modified_valence = sm.state.valence
    modified_arousal = sm.state.arousal
    num_episodes = len(sm.state.active_episodes)
    
    print(f"Before reset: V={modified_valence:.3f}, A={modified_arousal:.3f}, Episodes={num_episodes}")
    
    # Reset
    sm.reset_to_baseline()
    
    print(f"After reset: V={sm.state.valence:.3f}, A={sm.state.arousal:.3f}, Episodes={len(sm.state.active_episodes)}")
    
    # Should be at baseline values
    assert abs(sm.state.valence - sm.baseline.valence_baseline) < 0.001
    assert abs(sm.state.arousal - sm.baseline.arousal_baseline) < 0.001
    assert abs(sm.state.dominance - sm.baseline.dominance_baseline) < 0.001
    assert len(sm.state.active_episodes) == 0
    
    print("✓ Reset to baseline verified")


def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("StateManager Test Suite")
    print("=" * 60)
    
    tests = [
        test_personality_baselines,
        test_big_five_mapping,
        test_pad_clamping,
        test_emotional_impacts,
        test_emotional_inertia,
        test_episode_tracking,
        test_regression_to_baseline,
        test_mood_labels,
        test_state_serialization,
        test_emotional_context,
        test_reset_to_baseline,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR: {test_func.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
