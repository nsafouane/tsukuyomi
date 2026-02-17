# Integration Experiment Gap Fixes

**Date:** 2026-02-17
**Status:** IN PROGRESS

## Issues Identified

### 1. Vote Persistence Bug (CRITICAL)
**Problem:** Vote changes are logged but not persisted to agent state files.
**Evidence:** Log shows Davis and George flipping to not_guilty, but agent/*.json shows all guilty.
**Fix:** Update `save_agent_states()` to read from runtime vote state, not from initial profile.

### 2. Memory Decay Missing (HIGH)
**Problem:** Beliefs don't decay over time without reinforcement.
**Evidence:** 3,600 "belief_saturation" gaps - beliefs hitting 95% and staying there.
**Fix:** Implement `decay_beliefs()` method in BeliefSystem that reduces confidence by small amount per tick.

### 3. Social Pressure Missing (HIGH)
**Problem:** Agents in minority don't feel pressure to conform.
**Evidence:** Arthur Miller stayed at 95% guilty despite being in minority (G=2/N=3).
**Fix:** Add `apply_social_pressure()` that increases doubt when in minority.

### 4. Narrative Progression (MEDIUM)
**Problem:** Narrative never reaches CLIMAX or RESOLUTION acts.
**Evidence:** Final act is CONFRONTATION, tension stuck at 0.02.
**Fix:** Add vote threshold triggers for act transitions:
  - CLIMAX: When votes are 3-2 (close to consensus)
  - RESOLUTION: When votes are 4-1 or 5-0

### 5. Emotional Peaks (LOW)
**Problem:** No emotional peaks tracked (count: 0).
**Evidence:** narrative_summary shows emotional_peaks: 0.
**Fix:** Track when agent arousal exceeds threshold and log as emotional peak.

## Implementation Plan

### Phase 1: Fix Vote Persistence (5 min)
```python
# In save_agent_states()
# Read from self.agent_votes dict, not from agent.profile
agent_data["current_vote"] = self.agent_votes[agent_id]
```

### Phase 2: Add Memory Decay (15 min)
```python
# In BeliefSystem
DECAY_RATE = 0.0001  # Per tick

def decay_beliefs(self, tick: int):
    """Reduce confidence of beliefs over time."""
    for belief in self.beliefs.values():
        if belief.mutable and belief.confidence > 0.3:
            belief.confidence -= DECAY_RATE
            belief.confidence = max(0.3, belief.confidence)
```

### Phase 3: Add Social Pressure (15 min)
```python
# In BeliefSystem
def apply_social_pressure(self, my_vote: str, vote_distribution: dict, tick: int):
    """Apply pressure when in minority."""
    my_count = vote_distribution.get(my_vote, 0)
    total = sum(vote_distribution.values())
    minority_ratio = my_count / total if total > 0 else 1.0
    
    if minority_ratio < 0.4:  # In significant minority
        # Reduce confidence in beliefs
        for belief in self.beliefs.values():
            if belief.mutable:
                pressure_factor = (0.4 - minority_ratio) * 0.05
                belief.confidence -= pressure_factor
```

### Phase 4: Narrative Progression (10 min)
```python
# In DramaDirector
def check_act_transition(self, votes: dict, tension: float) -> str:
    total = sum(votes.values())
    max_vote = max(votes.values())
    
    if max_vote >= 4:  # Near consensus
        return "RESOLUTION"
    elif max_vote == 3 and tension > 0.3:
        return "CLIMAX"
    return self.current_act
```

### Phase 5: Emotional Peaks (10 min)
```python
# In IntegratedAgent
def check_emotional_peak(self) -> bool:
    if self.emotional_state.aroussal > 0.8:
        self.log_emotional_peak()
        return True
    return False
```

## Expected Improvements

| Metric | Before | After |
|--------|--------|-------|
| Vote state accuracy | 0% (wrong) | 100% (correct) |
| Belief flexibility | Static | Decays naturally |
| Minority behavior | No change | Feels pressure |
| Narrative depth | 2 acts | 4 acts |
| Emotional tracking | None | Peaks logged |

## Files to Modify

1. `experiments/angry_men/run_full_integration.py` - Fix vote persistence, add social pressure
2. `tsukuyomi/agent/belief_system.py` - Add decay_beliefs()
3. `experiments/angry_men/drama/director.py` - Add act transitions
