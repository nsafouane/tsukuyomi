# Tsukuyomi Phase 2 Architectural Review Report

**Reviewer:** Senior Simulation Engineer & AI Architect (Gemini 3 Pro)
**Subject:** Rigorous Analysis of Technical Specification Opus 4.6
**Date:** 2026-02-08
**Status:** **APPROVED** (with critical performance refinements and clarifications required)

---

## Executive Summary

The Phase 2 specification (Opus 4.6) represents a sophisticated and well-architected evolution of the Tsukuyomi cognitive core. It directly addresses all five gaps identified in the Phase 1 experiment with concrete, implementable solutions. The architecture demonstrates strong logical coherence, with each module cleanly separated and integrated through well-defined interfaces.

**However**, the specification contains several feasibility risks that must be addressed before implementation to ensure the 20 TPS target is met. Additionally, some implementation details require clarification to prevent integration friction.

---

## 1. Feasibility Analysis — Can We Achieve 20 TPS?

### 1.1 Overall Assessment
**VERDICT:** **FEASIBLE** with careful implementation of specified mitigations, but there are critical bottlenecks that must be addressed.

The 20 TPS target (50ms per tick) is achievable with the current architecture for 4-6 agents, but the margin is thin. The spec identifies the correct risks but some mitigations need more specificity.

### 1.2 Critical Performance Bottlenecks

#### **Bottleneck 1: PerceptionPipeline with Emotional Modifiers**
**Risk:** O(A × P) where A = agents, P = percepts. The enhanced `process()` method runs every tick for every agent, applying emotional modifiers to all percepts.

```python
# From spec (lines 799-816):
def process(self, world_state, agent_internal_state, current_tick, 
            emotional_modifiers=None):
    # ... existing code ...
    if emotional_modifiers:
        max_percepts = emotional_modifiers.get("attention_width", 7)
        threat_boost = emotional_modifiers.get("threat_salience_boost", 0.0)
        for p in percepts:  # ← This loop runs for every agent, every tick
            if hasattr(p, 'event') and p.HasField('event'):
                if p.event.event_type in ("attack", "threat", "violence"):
                    p.salience = min(1.0, p.salience + threat_boost)
```

**Concern:** With 4 agents × ~10 percepts each = 40 iterations per tick. Acceptable now, but scales poorly.

**RECOMMENDATION:** Implement explicit **staggered perception** as mentioned in the roadmap but not detailed:
- Each agent gets "full perception" every 3 ticks (offset by agent ID)
- Off-ticks use cached percepts with minor decay
- This reduces perception load by 66% while maintaining acceptable fidelity

#### **Bottleneck 2: WorkingMemory.refresh() Relevance Scoring**
**Risk:** O(M) where M = episodic memories. Called every deliberation cycle.

```python
# From spec (lines 453-460):
def _score_episodic_memories(self, memories, topics, emotional_state):
    scored = []
    for mem in memories:  # ← Iterates ALL memories each refresh
        mem_text = str(mem.get("details", {}))
        topic_match = sum(1 for t in topics if t.lower() in mem_text.lower())
        # ...
```

**Concern:** With 4 agents deliberating every 50 ticks (staggered) = ~1 deliberation every 12 ticks. If each refresh scores 500 memories = 500 string operations per tick on average.

**RECOMMENDATION:** Two optimizations:
1. **Pre-index topics:** Extract and cache keywords from episodic memories during ingestion (not at query time)
2. **Cap candidate pool:** Only score top 50 most recent + top 20 highest-emotion memories

#### **Bottleneck 3: StateManager.update() Called Every Tick**
**Risk:** O(A × P) where A = agents, P = percepts. Iterates through all percepts to classify emotional events.

```python
# From spec (lines 137-159):
def update(self, percepts, list, current_tick):
    for percept in percepts:  # ← Called for every agent, every tick
        event_type = self._classify_event(percept)
        if event_type and event_type in EMOTIONAL_IMPACT_RULES:
            # Apply PAD deltas
```

**Concern:** Similar to PerceptionPipeline. The emotional inertia calculation adds volatility scaling per percept.

**RECOMMENDATION:** 
- Batch StateManager updates: Run every 2 ticks instead of every tick
- Cache `_classify_event()` results (same percept → same classification for all agents)
- Only process top-N salient percepts per agent (already done via WorkingMemory, but should be done earlier)

#### **Bottleneck 4: Memory Decay Ongoing**
**Risk:** The spec correctly identifies this and provides a mitigation (run every 10 ticks). However, the implementation detail is unclear.

```python
# From spec (lines 538-552):
def tick_decay(self):
    for i, mem in enumerate(self.episodic_memory):  # ← Linear iteration
        decay = mem.get("decay_rate", 0.001)
        mem["relevance_score"] = max(0.0, mem.get("relevance_score", 1.0) - decay)
```

**Concern:** 500 memories × 4 agents × 0.1 (every 10 ticks) = 200 operations/tick. Acceptable, but the "batch 10% of memories" suggestion from the previous review isn't incorporated.

**RECOMMENDATION:** Implement the batch approach:
```python
def tick_decay(self):
    # Decay only 10% of memories each tick (rotating subset)
    batch_size = max(1, len(self.episodic_memory) // 10)
    start_idx = (self.current_tick // 10) % len(self.episobic_memory)
    end_idx = (start_idx + batch_size) % len(self.episodic_memory)
    
    for i in range(start_idx, min(end_idx, len(self.episodic_memory))):
        # ... decay logic ...
```

### 1.3 LLM Rate Limiting — SOLVED ✓

The spec correctly preserves the existing semaphore (1) with 2.5s cooldown. Reactive deliberation simply enters the same queue. This is the right approach:
- **No race conditions:** LLM calls are serialized
- **Rate limit compliant:** Never exceeds API limits
- **Natural pacing:** 2-5 second response times feel organic

The one missing piece: **What happens when a reactive trigger arrives while LLM is deliberating?** The spec mentions preemption via `_cancel_current_deliberation` flag, but doesn't specify:
1. How the agent responds to the waiting user (acknowledge? ignore?)
2. Whether the pre-empted deliberation's results are discarded or queued for later

**RECOMMENDATION:** Specify the preemption UX:
- Direct address → Send "wait..." acknowledgment via EMOTE if thinking
- Cancelled deliberation → Results discarded (don't resubmit)

### 1.4 Token Budget — WITHIN LIMITS ✓

The spec estimates ~1000 input tokens, which is comfortably within limits. The WorkingMemory 7±2 slot cap ensures this bound is enforced.

### 1.5 Feasibility Summary

| Component | Complexity | TPS Risk | Mitigation Status |
|-----------|-----------|----------|-------------------|
| PerceptionPipeline | Medium | Medium | Staggered perception needs detail |
| StateManager | Low | Medium | Batch/caching recommended |
| WorkingMemory | Medium | Medium | Pre-index topics needed |
| BeliefManager | Low | Low | Capped evidence (20/side) ✓ |
| Fate Engine | Low | Low | New resolvers are O(1) ✓ |
| Memory Decay | Low | Medium | Batch approach recommended |

---

## 2. Logical Coherence Analysis

### 2.1 Overall Assessment
**VERDICT:** **STRONGLY COHERENT** with minor integration gaps.

The architecture demonstrates excellent separation of concerns:
- **StateManager** handles emotional state
- **BeliefManager** handles belief/stance
- **WorkingMemory** handles attention/cognitive load
- **PerceptionPipeline** handles sensory input
- **Fate Engine** handles world state arbitration

Each module has a single responsibility and clean interfaces. The data flow is clear and well-documented.

### 2.2 Strengths of Coherence

#### **1. Three-Tier Memory Architecture**
The WorkingMemory → Episodic → Semantic hierarchy with consolidation flows is psychologically grounded and mechanically sound:
- Miller's Law bounds prevent context overflow
- Emotional tagging differentiates important vs. mundane memories
- Relevance-based scoring makes recall cognitively plausible

#### **2. PAD Emotional Model**
The PAD (Pleasure-Arousal-Dominance) model is well-established in affective computing. The spec's implementation includes:
- Personality baselines (emotional "homeostasis")
- Regression to baseline over time (emotional inertia)
- Derived mood labels for LLM context
- Mechanical effects (perception narrowing, memory decay variation)

This creates a feedback loop where emotions both influence and are influenced by perception and reasoning.

#### **3. Evidence-Based Belief System**
Replacing hardcoded stance strings with evidence-weighted calculation is architecturally sound:
- Beliefs emerge from accumulated evidence
- Personality biases modulate evidence weighting
- Stance shifts are explicit, trackable events
- Social pressure is a first-class evidence type

This enables genuine cognitive change, not just scripted "flip the flag."

#### **4. Reactive vs. Proactive Deliberation**
The dual-mode deliberation model (scheduled + reactive) is well-designed:
- Proactive: Every 50 ticks (existing, unchanged)
- Reactive: Triggered by direct address, high salience, stance shifts
- Preemption: High-priority reactive triggers interrupt scheduled deliberation

This balances thoughtful planning with responsiveness to stimuli.

### 2.3 Identified Contradictions & Gaps

#### **Contradiction 1: Staggered Perception Frequency**

**Issue:** The spec contains two conflicting statements about when enhanced perception runs:
1. Line 763: "Each agent's emotions evolve based on perceived events and regress towards their personality baseline over time" (implies every tick)
2. Line 799: The `process()` signature includes `emotional_modifiers` but doesn't specify when to call it
3. Line 1095 in roadmap: "Staggered Perception Schedule. We will not calculate full vision for every agent on every tick."

**Resolution Required:** Explicitly define the perception schedule:
```python
# Recommended approach:
tick % 3 == 0:  Full perception with emotional modifiers
tick % 3 != 0:  Cached percepts from last full tick
```

#### **Gap 1: Conflict Resolution for TAKE/GIVE**

**Issue:** The spec doesn't define what happens when two agents simultaneously try to TAKE the same object, or when GIVE is sent to an agent who just DROPPED the item in the same tick.

**Spec Reference:** Line 1130-1148 shows TAKE resolution with ownership check, but doesn't mention simultaneous submissions.

**Resolution Required:** Add to Fate Engine conflict resolution:
- Two agents TAKE same object → First-come-first-served (already implemented via proposal queue)
- Agent A gives to B while B is taking → Define priority: TAKE wins (possession over transfer)

#### **Gap 2: Emotional State to Belief Bias Coupling**

**Issue:** StateManager and BeliefManager operate independently. The spec shows personality biases are static in BeliefManager, but emotions are dynamic in StateManager.

**Question:** Should high arousal increase confirmation bias? Should low dominance increase social pressure susceptibility?

**Resolution Required:** Add a method to BeliefManager that accepts emotional modifiers:
```python
def get_effective_bias(self, emotional_state):
    # Scale biases by emotional state
    confirmation_bias = self.bias.confirmation_bias * (1.0 + emotional_state.arousal * 0.3)
    social_pressure_immunity = self.bias.social_pressure_immunity * (1.0 + emotional_state.dominance * 0.2)
    return PersonalityBias(
        confirmation_bias=confirmation_bias,
        disconfirmation_resistance=self.bias.disconfirmation_resistance,
        social_pressure_immunity=social_pressure_immunity
    )
```

#### **Gap 3: Stance Shift Cascade Mechanics**

**Issue:** The spec mentions "social contagion" (line 727) but doesn't define how belief propagation works:
- When Agent A shifts stance, do other agents automatically learn the reason?
- Or do they only perceive "Agent A changed their mind" and must infer?

**Resolution Required:** Define the cascade semantics:
```
StanceShiftEvent broadcast includes:
  - agent_id, old_stance, new_stance (visible to all)
  - trigger_evidence.description (visible only to those in FOV)
  - internal_reasoning (private, not broadcast)
```

Agents seeing the shift may add "social_pressure" evidence but don't automatically inherit the triggering evidence.

#### **Gap 4: Preemption State Machine**

**Issue:** The spec mentions `_cancel_current_deliberation` flag but doesn't define the full state machine for deliberation states:
- What states can an agent be in? (idle, thinking, preempting, recovering?)
- What happens to the LLM request if mid-stream when cancelled?
- How does the agent know when it's safe to start new deliberation?

**Resolution Required:** Define state diagram:
```
States: IDLE → THINKING → PREEMPTED → IDLE

Transitions:
IDLE → THINKING:  When proactive or reactive trigger fires
THINKING → PREEMPTED:  When higher-priority trigger arrives
PREEMPTED → IDLE:  When cancelled deliberation completes (results discarded)
THINKING → IDLE:  When deliberation completes naturally
```

### 2.4 Logical Coherence Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Module separation | ✓ Excellent | Clean interfaces, single responsibility |
| Data flow | ✓ Clear | Well-documented in §2.2 |
| Integration points | ✓ Good | Line-level specificity |
| Contradictions | ⚠ 2 minor | Staggered perception, conflict resolution |
| Gaps | ⚠ 3 moderate | Emotion-belief coupling, cascade mechanics, preemption |

---

## 3. Completeness Analysis

### 3.1 Overall Assessment
**VERDICT:** **90% COMPLETE** — All core components are specified, but some implementation details need elaboration.

The spec is impressive in its detail. For a 2167-line document, it includes:
- Complete class definitions with methods
- Protobuf schema diffs
- Integration map with line numbers
- Implementation roadmap with milestones
- Risk analysis and mitigations
- Validation criteria

### 3.2 What IS Complete ✓

#### **Fully Specified Components:**

1. **StateManager Module** (§3) — COMPLETE
   - Class definition with all methods
   - PAD model with emotional impact rules
   - Personality baselines for test agents
   - Integration with perception and memory

2. **BeliefManager Module** (§7) — COMPLETE
   - Evidence-based belief graph
   - Stance calculation from evidence
   - Personality bias profiles
   - Stance shift event generation
   - LLM prompt formatting

3. **Protobuf Schema Changes** (§11) — COMPLETE
   - ActionType enum extensions
   - EnvironmentObject enhancements
   - Affordance message definition
   - New belief.proto file

4. **Agent Profile Schema v2** (§12) — COMPLETE
   - Eliminates static stance
   - Adds personality_baseline, personality_bias
   - Adds initial_beliefs structure
   - Includes sensory_profile

5. **LLM Prompt Architecture** (§13) — COMPLETE
   - Full prompt template
   - Token budget analysis
   - Action JSON schema
   - REFLECT instruction formatting

6. **Fate Engine Modifications** (§9) — MOSTLY COMPLETE
   - Resolution methods for all new actions
   - EXAMINE with distance checks and property reveal
   - TAKE with ownership validation
   - REFLECT as internal action

7. **Implementation Roadmap** (§15) — COMPLETE
   - 6 phases over 7 weeks
   - Milestones and tests per task
   - Clear file ownership

### 3.3 What IS Missing or Incomplete ✗

#### **Missing 1: Staggered Perception Implementation Details**

**Spec References:**
- Line 1095: "Staggered Perception Schedule. We will not calculate full vision for every agent on every tick."
- Line 1098: "Agents will rotate through 'Deep Perception' ticks while performing lightweight 'Proximity Heartbeats' on others."

**Missing:**
- What is a "Proximity Heartbeat"?
- How do you determine which agents get deep perception on which tick?
- How does emotional modifier application work during off-ticks?
- Code example showing the schedule logic

**Required Addition:**
```python
# In AgentBrain._process_tick():
perception_mode = (tick_state.tick_number + self.tick_offset) % 3
if perception_mode == 0:
    # Deep perception: full FOV + occlusion + emotional modifiers
    percepts = self.perception.process(
        world_state, self._get_internal_state(), tick_state.tick_number,
        emotional_modifiers=self.state_manager.get_perception_modifiers()
    )
    self._cached_percepts = percepts
else:
    # Proximity heartbeat: only nearby actors/objects
    percepts = self.perception.process_heartbeat(
        world_state, self._get_internal_state(), tick_state.tick_number
    )
    # Apply cached emotional modifiers from last deep tick
    # (or skip emotional processing during off-ticks)
```

#### **Missing 2: Memory Decay Batching Algorithm**

**Spec References:**
- Line 540: "Run memory pruning asynchronously or in batches (e.g., process 10% of memories per tick)"
- Risk R3 mitigation: "Decouple decay from the main loop. Run memory pruning asynchronously or in batches"

**Missing:**
- Concrete algorithm for batch decay
- How to handle the rotating subset (circular buffer?)
- Whether `tick_decay()` should still be called every 10 ticks or every tick

**Required Addition:** (See recommendation in §1.2)

#### **Missing 3: WorkingMemory Pre-Indexing**

**Spec References:**
- Line 453-460: `_score_episodic_memories()` does topic matching by iterating through all memories
- No mention of keyword extraction during ingestion

**Missing:**
- When/how to extract keywords from episodic memories
- How to cache keyword lists for fast matching
- How to handle topic updates (add/remove topics dynamically)

**Required Addition:**
```python
# In MemoryManager.ingest_tick():
memory_entry = {
    # ... existing fields ...
    "keywords": self._extract_keywords(res.outcome.get("message", "")),  # NEW
    "topics_extracted": topics  # NEW
}

def _extract_keywords(self, text):
    # Simple keyword extraction (could use NLP library)
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {'the', 'a', 'an', 'is', 'was', 'at', 'on', 'in', ...}
    return [w for w in words if w not in stop_words and len(w) > 3]

# In WorkingMemory._score_episodic_memories():
# Use cached keywords instead of full text search
mem_keywords = mem.get("keywords", [])
topic_score = sum(1 for t in topics if t.lower() in mem_keywords)
```

#### **Missing 4: Error Handling Strategies**

**Spec References:**
- Risk R4: "LLM produces invalid action JSON" → "Existing JSON extraction + fallback to IDLE"
- No other error handling discussed

**Missing:**
- What happens if BeliefManager.add_evidence() fails?
- What happens if PerceptionPipeline.process() throws exception?
- How does the system recover from protobuf serialization errors?
- Graceful degradation when modules fail

**Required Addition:**
```python
# In AgentBrain._process_tick():
try:
    percepts = self.perception.process(...)
except Exception as e:
    logger.error(f"Perception failed for {self.profile['name']}: {e}")
    percepts = []  # Graceful degradation: no perception this tick
    self.state_manager.update([], current_tick)  # Still run StateManager

try:
    self.working_memory.refresh(...)
except Exception as e:
    logger.error(f"WorkingMemory failed: {e}")
    self.working_memory.slots = []  # Use empty working memory
```

#### **Missing 5: Performance Metrics & Observability**

**Spec References:**
- Line 2071: "Optimistic Conflict Rate < 1%" (in ARCHITECTURE.md)
- No metrics specified for Phase 2 modules

**Missing:**
- How to measure perception latency per tick
- How to profile WorkingMemory.refresh() performance
- What metrics to emit for stance shift events
- How to detect 20 TPS violations in production

**Required Addition:**
```python
# In fate_engine.py main loop:
tick_start = time.time()
# ... tick processing ...
tick_duration = time.time() - tick_start
if tick_duration > 0.05:  # 50ms budget
    logger.warning(f"Tick {tick_number} exceeded budget: {tick_duration*1000:.1f}ms")

# In AgentBrain:
self.metrics["deliberation_duration_ms"] = deliberation_duration
self.metrics["working_memory_slot_count"] = len(self.working_memory.slots)
self.metrics["last_perception_count"] = len(percepts)
```

#### **Missing 6: Test Coverage Specification**

**Spec References:**
- Roadmap mentions "Unit test" and "Integration" for each task
- No explicit test framework or coverage targets

**Missing:**
- Which testing framework (pytest, unittest)?
- Minimum coverage percentage?
- How to test stochastic behavior (emotional inertia)?
- Integration test scenarios (multi-agent interactions)?

**Required Addition:**
```markdown
## Testing Requirements

### Framework
- Unit tests: `pytest` with `pytest-asyncio`
- Integration tests: Custom scenario runner in `tests/integration/`

### Coverage Targets
- StateManager: 90% coverage
- BeliefManager: 90% coverage
- WorkingMemory: 85% coverage (heuristic scoring)
- AgentBrain: 70% coverage (complex async logic)

### Stochastic Testing
For emotional inertia and belief shifts, use:
- Monte Carlo simulation: Run 100 iterations with same inputs, verify distribution
- Deterministic seeding: `random.seed(42)` for reproducible unit tests
```

### 3.4 Completeness Summary

| Component | Completeness | Missing Elements |
|-----------|--------------|------------------|
| StateManager | 95% | Stochastic testing strategy |
| WorkingMemory | 80% | Pre-indexing algorithm |
| BeliefManager | 90% | Error handling |
| PerceptionPipeline | 85% | Staggered perception details |
| Fate Engine | 90% | Conflict resolution edge cases |
| LLM Prompt | 100% | — |
| Protobuf | 100% | — |
| Testing | 40% | Framework, coverage, scenarios |
| Observability | 30% | Metrics, profiling |

---

## 4. Recommendations & Improvements

### 4.1 Performance Optimizations (Priority: HIGH)

#### **Optimization 1: Explicit Staggered Perception**
**Impact:** Reduces perception load by 66%
**Effort:** LOW
**Implementation:** See §3.3 Missing 1

#### **Optimization 2: WorkingMemory Pre-Indexing**
**Impact:** Reduces string operations by ~90%
**Effort:** LOW
**Implementation:** See §3.3 Missing 3

#### **Optimization 3: Batch Memory Decay**
**Impact:** Spreads memory pruning load evenly
**Effort:** LOW
**Implementation:** See §1.2 Bottleneck 4

#### **Optimization 4: Cache Event Classifications**
**Impact:** Reduces redundant percept processing
**Effort:** MEDIUM
```python
# In PerceptionPipeline or StateManager:
_event_classification_cache = {}  # {percept_id: event_type}

def _classify_event(self, percept):
    percept_id = getattr(percept, 'percept_id', str(hash(percept)))
    if percept_id in self._event_classification_cache:
        return self._event_classification_cache[percept_id]
    
    event_type = self._classify_event_uncached(percept)
    self._event_classification_cache[percept_id] = event_type
    return event_type
```

#### **Optimization 5: Lazy Emotional State Updates**
**Impact:** Skips StateManager for idle agents
**Effort:** LOW
```python
# In AgentBrain._process_tick():
# Only update emotional state if there are percepts
if percepts:
    self.state_manager.update(percepts, current_tick)
# Decay still runs regardless (regression to baseline)
self.state_manager.decay_episodes(current_tick)  # NEW: Decay episodes
```

### 4.2 Architectural Refinements (Priority: MEDIUM)

#### **Refinement 1: Emotion-to-Bias Coupling**
**Rationale:** Emotional state should influence cognitive biases
**Implementation:** See §2.3 Gap 2

#### **Refinement 2: Surprise Event Type**
**Rationale:** Surprise is a fundamental perceptual driver
**Implementation:**
```python
# In PerceptionPipeline:
def _calculate_surprise(self, percept, agent_state):
    """Calculate surprise based on memory echoes."""
    percept_hash = self._hash_percept(percept)
    recent_hash = agent_state.get('last_percept_hash', '')
    
    if recent_hash == percept_hash:
        return 0.0  # Not surprising if recently seen
    
    # Check semantic memory for contradictory facts
    if self._contradicts_semantic_memory(percept):
        return 0.8  # High surprise for contradictions
    
    return 0.1  # Baseline surprise for novel events
```

#### **Refinement 3: Stance Shift Visualization**
**Rationale:** Debugging cascades requires visualization
**Implementation:**
```python
class StanceShiftVisualizer:
    def render_graph(self, history):
        """Render stance shift timeline as ASCII graph."""
        # Example output:
        # juror-2:  [FOR]----------[NEUTRAL]---[AGAINST]
        # juror-3:  [FOR]==================================
        # juror-4:  [FOR]------[NEUTRAL]
        #          tick 1000      5000      8000
        pass
```

#### **Refinement 4: Partial Examine Reveal**
**Rationale:** Prevents instant information dump
**Implementation:**
```python
# In FateEngine._resolve_examine():
# Instead of revealing all hidden_properties:
revealed_count = min(3, len(hidden_properties))
revealed_subset = dict(list(hidden_properties.items())[:revealed_count])

# Store which properties have been revealed per agent
if not hasattr(obj, 'revealed_to'):
    obj.revealed_to = {}
obj.revealed_to[actor.id] = obj.revealed_to.get(actor.id, []) + list(revealed_subset.keys())
```

### 4.3 New Features (Priority: LOW)

#### **Feature 1: Emotional Episodes with Duration**
**Rationale:** Some emotions (e.g., trauma) have longer-lasting effects
**Implementation:**
```python
# In StateManager:
@dataclass
class EmotionalEpisode:
    trigger_event_id: str
    emotion_type: str
    intensity: float
    onset_tick: int
    duration_ticks: int = 100  # NEW: Episode duration
    decay_curve: str = "linear"  # "linear", "exponential", "step"

def update(self, ...):
    for ep in self.state.active_episodes:
        age = current_tick - ep.onset_tick
        if age > ep.duration_ticks:
            continue  # Episode over
        # Apply intensity based on decay curve
        current_intensity = self._calculate_intensity(ep, age)
```

#### **Feature 2: Evidence Source Trust Weighting**
**Rationale:** Agents trust some sources more than others
**Implementation:**
```python
# In BeliefManager:
SOURCE_TRUST_WEIGHTS = {
    "testimony": 1.0,
    "observation": 1.2,  # Direct observation is more trusted
    "reasoning": 0.9,
    "social_pressure": 0.7,
    "hearsay": 0.5
}

def add_evidence(self, ...):
    # Apply source trust weighting
    evidence.weight *= SOURCE_TRUST_WEIGHTS.get(evidence.source_type, 1.0)
```

#### **Feature 3: Memory Consolidation Triggers**
**Rationale:** Some events trigger automatic semantic memory formation
**Implementation:**
```python
# In MemoryManager.ingest_tick():
if emotional_intensity > 0.7 or salience > 0.9:
    # High-emotion events automatically create semantic facts
    self._consolidate_to_semantic(memory_entry, emotional_intensity)
```

### 4.4 Testing & Validation Improvements

#### **Improvement 1: Deterministic Fuzzing**
**Rationale:** Test edge cases in async deliberation
**Implementation:**
```python
# In tests/integration/test_async_deliberation.py:
@pytest.mark.fuzz
@pytest.mark.parametrize("tick_offset", range(0, 50))
def test_concurrent_reactive_triggers(tick_offset):
    """Inject multiple reactive triggers and verify no deadlock."""
    pass
```

#### **Improvement 2: Stance Shift Regression Tests**
**Rationale:** Ensure stance shifts don't regress in future changes
**Implementation:**
```python
# In tests/regression/test_stance_shifts.py:
def test_bank_teller_should_shift_on_knife_examine():
    """This test documents expected behavior and catches regressions."""
    # Setup: Bank Teller with initial FOR stance
    # Action: EXAMINE switchblade (reveals "NOT unique")
    # Assert: Stance shifts to NEUTRAL or LEANING_AGAINST
    pass
```

#### **Improvement 3: Performance Benchmark Suite**
**Rationale:** Continuous monitoring of 20 TPS target
**Implementation:**
```python
# In tests/performance/benchmarks.py:
@pytest.mark.benchmark
def test_perception_latency_with_10_agents(benchmark):
    """Ensure perception stays under 5ms with 10 agents."""
    # Benchmark perception.process() with 10 agents, 50 objects
    pass
```

---

## 5. Critical Path Items for Implementation

Before starting implementation, the following must be clarified or resolved:

### **MUST RESOLVE (Blocking):**

1. **Staggered Perception Schedule** — Define concrete algorithm for alternating deep/heartbeat perception
2. **Memory Decay Batching** — Specify exact batching algorithm
3. **Conflict Resolution for Concurrent TAKE/GIVE** — Define priority rules
4. **Preemption State Machine** — Define full state diagram and transitions

### **SHOULD RESOLVE (Recommended):**

1. **Emotion-to-Bias Coupling** — Add method to scale biases by emotional state
2. **Stance Shift Cascade Semantics** — Define what information propagates when stance shifts
3. **Error Handling Strategy** — Define graceful degradation patterns
4. **Testing Framework** — Choose pytest, define coverage targets

### **CAN RESOLVE (Optional):**

1. **Partial Examine Reveal** — Prevents instant info dump
2. **Evidence Source Trust Weighting** — Adds nuance to belief formation
3. **Stance Shift Visualization** — Debugging tool

---

## 6. Comparison with Previous Review (Gemini 2.5 Pro)

The previous review (PHASE_2_REVIEW_SUMMARY.md) identified similar concerns:

| Concern | Previous Review | This Review | Status |
|---------|------------------|-------------|--------|
| Perception O(A²) bottleneck | ✓ Identified | ✓ Confirmed | Need staggered perception details |
| Memory decay O(M) | ✓ Identified | ✓ Confirmed | Batch algorithm specified |
| Conflicting actions | ⚠ Mentioned | ✓ Detailed | TAKE/GIVE priority needed |
| Emotional inertia | ✓ Suggested | ✓ Included | Volatility scaling in spec ✓ |
| Surprise factor | ✓ Suggested | ✗ Missing | Recommend adding |
| WorkingMemory bounds | ✓ Suggested | ✓ Included | 7±2 slots ✓ |
| Preemption | ⚠ Mentioned | ⚠ Incomplete | State machine needed |

This spec (Opus 4.6) is significantly more detailed than the original v1.0 mentioned in the preface. Most concerns from the previous review have been addressed, but implementation details for the mitigations need elaboration.

---

## 7. Final Verdict

### **RECOMMENDATION: APPROVE with Clarifications**

**Strengths:**
- Architecturally sound with excellent separation of concerns
- Directly addresses all Phase 1 gaps
- Comprehensive specification (2167 lines with code examples)
- Clear integration map with line-level specificity
- Realistic token budget and LLM rate limiting

**Critical Clarifications Required:**
1. Concrete staggered perception algorithm
2. Batch memory decay implementation
3. TAKE/GIVE conflict resolution rules
4. Preemption state machine definition

**Implementation Priorities:**
1. **Week 1:** Clarify blocking items (staggered perception, memory decay batching)
2. **Week 2-3:** Implement StateManager + BeliefManager (low risk)
3. **Week 4:** Implement WorkingMemory with pre-indexing
4. **Week 5:** Implement perception enhancements
5. **Week 6:** Integration testing + performance profiling

**Confidence in 20 TPS Target:**
- With specified mitigations: **85%**
- With recommended optimizations: **95%**

---

## Appendix: Summary Tables

### Table A1: Performance Budget Allocation (50ms per tick)

| Component | Per Agent | 4 Agents | Buffer |
|-----------|-----------|----------|--------|
| Fate Engine (tick processing) | 5ms | 5ms | — |
| Perception Pipeline (staggered) | 3ms | 12ms | 3ms |
| StateManager (batched) | 1ms | 4ms | 1ms |
| WorkingMemory (deliberation only) | 5ms | 5ms* | 2ms |
| BeliefManager (deliberation only) | 2ms | 2ms* | 1ms |
| LLM Deliberation (async, not in budget) | — | — | — |
| Memory Decay (async) | — | — | — |
| **Total** | — | **28ms** | **22ms** |

\* WorkingMemory and BeliefManager only run during deliberation (~1 agent per 12 ticks on average)

### Table A2: Risk Priority Matrix

| Risk | Likelihood | Impact | Priority | Mitigation |
|------|------------|--------|----------|------------|
| Perception bottleneck | Medium | High | **P1** | Staggered perception (needs detail) |
| LLM context overflow | Low | High | P2 | WorkingMemory 7±2 caps ✓ |
| Memory decay kills budget | Medium | Medium | **P1** | Batch decay (needs algorithm) |
| LLM invalid JSON | High | Medium | P2 | Fallback to IDLE ✓ |
| Emotional oscillation | Medium | Low | P3 | Regression to baseline ✓ |
| Stance shifts never happen | Medium | High | P2 | REFLECT instructions ✓ |
| Preemption deadlock | Low | High | P3 | State machine (needed) |
| Protobuf breakage | Low | Medium | P3 | Phase 2.4 task ✓ |

### Table A3: Module Complexity vs. Risk

| Module | Lines of Code | Complexity | TPS Risk | Integration Risk | Testability |
|--------|---------------|------------|----------|-----------------|-------------|
| StateManager | ~250 | Low | Medium | Low | High |
| WorkingMemory | ~200 | Medium | Medium | Medium | Medium |
| BeliefManager | ~300 | Low | Low | Low | High |
| PerceptionPipeline (enhanced) | +30 | Medium | Medium | Medium | Medium |
| AgentBrain (modified) | ~60% rewrite | High | Low | High | Low |
| Fate Engine (new resolvers) | ~200 | Low | Low | Medium | High |

---

**Review Completed.**
**Reviewer:** Gemini 3 Pro (Senior Simulation Engineer & AI Architect)
**Date:** 2026-02-08
**Status:** Approved with critical clarifications required before implementation.
