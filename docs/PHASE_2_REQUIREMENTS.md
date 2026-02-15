# 📋 Tsukuyomi V2 Phase 2 - World Dynamics Requirements Document

**Version:** 1.0
**Date:** 2026-02-15
**Status:** Active
**Phase:** Phase 2 - Interaction & Physics
**Duration:** Weeks 3-5

---

## 📋 Executive Summary

This document defines the complete requirements for Phase 2 of Tsukuyomi V2 development. Phase 2 focuses on making the world feel "Real" and responsive through spatial indexing, proposal windows for commitment phases, affordance systems, and visual perception with raycasting.

**Primary Goal:** Enable autonomous multi-agent interactions in a dynamic, spatially-aware environment with complex object interactions.

---

## 🎯 Phase 2 Objectives

1. **Spatial Indexing:** Replace O(N) proximity checks with O(1) or O(log N) queries to support 50+ agents
2. **Proposal Windows:** Implement commitment phases with conflict resolution for simultaneous actions
3. **Affordance System:** Complete the affordance system on EnvironmentObjects with runtime resolution
4. **Visual Perception:** Implement raycasting-based visual perception with occlusion handling

---

## 📊 Current Status Assessment

### ✅ Completed Components

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| SpatialIndex (Grid-based) | ✅ Implemented | `tsukuyomi/core/spatial_index.py` | Grid partitioning, insert/query/remove operations |
| Affordance Data Structures | ✅ Partial | `tsukuyomi/core/world_builder.py` | Affordance class, EnvironmentObject affordances |
| Proposal Window (Basic) | ✅ Partial | `tsukuyomi/proto/fate_engine.py` | Collects proposals, lacks full conflict resolution |
| Perception Pipeline | ✅ Partial | `tsukuyomi/brain/PerceptionPipeline.py` | Has occlusion placeholder, needs real raycasting |

### 🔧 Components Requiring Enhancement

| Component | Required Enhancement | Priority |
|-----------|---------------------|----------|
| SpatialIndex | Integration with FateEngine | High |
| Affordance System | Runtime resolution engine, condition evaluation | High |
| Proposal Window | Full commitment phase logic, conflict resolution | High |
| Visual Perception | Raycasting implementation, FOV tracking | Medium |

---

## 📝 Detailed Requirements

### Task 2.1: SpatialIndex Integration

#### 2.1.1 Requirements

**REQ-2.1.1:** Integrate SpatialIndex into FateEngine as the primary proximity query mechanism

- The FateEngine must use SpatialIndex for all proximity-based queries
- All actors and objects must be registered in the spatial index on world initialization
- Actor position updates must trigger spatial index updates in real-time

**REQ-2.1.2:** Performance Requirements

- Proximity queries must complete in < 1ms for 50+ agents
- Spatial index must handle world sizes up to 1000x1000 units
- Cell size must be configurable (default: 10 units)

**REQ-2.1.3:** Query API Integration

- Replace all O(N) proximity checks with `spatial_index.query()` calls
- Implement nearest-neighbor queries for AI decision-making
- Support radius queries for interaction validation

#### 2.1.2 Acceptance Criteria

**AC-2.1.1:** SpatialIndex is initialized in FateEngine constructor
- [ ] FateEngine creates SpatialIndex instance on init
- [ ] World dimensions are passed to SpatialIndex
- [ ] Default cell_size is 10.0

**AC-2.1.2:** All actors and objects registered on world load
- [ ] World initialization iterates through all actors and objects
- [ ] Each entity is inserted into spatial index
- [ ] Registration logged for debugging

**AC-2.1.3:** Position updates propagate to spatial index
- [ ] When actor moves, spatial_index.update_position() is called
- [ ] Object position changes update spatial index
- [ ] Failed updates are logged as warnings

**AC-2.1.4:** Proximity queries use spatial index
- [ ] `get_nearby_actors()` uses `spatial_index.query()`
- [ ] `get_nearby_objects()` uses `spatial_index.query()`
- [ ] Query results exclude self when appropriate

**AC-2.1.5:** Performance benchmarks met
- [ ] 50 agents: query latency < 1ms (average)
- [ ] 100 agents: query latency < 2ms (average)
- [ ] Memory usage < 10MB for 1000 entities

#### 2.1.3 Implementation Notes

- File: `tsukuyomi/proto/fate_engine.py`
- Methods to modify:
  - `__init__()`: Initialize SpatialIndex
  - `initialize_world()`: Register all entities
  - `_update_actor_position()`: Propagate updates
  - `get_nearby_actors()`: Use spatial queries

---

### Task 2.2: Proposal Window Enhancement

#### 2.2.1 Requirements

**REQ-2.2.1:** Implement Full Commitment Phase Logic

- Proposal window must have configurable duration (default: 25ms)
- Agents submit proposals within the window
- Window closes automatically after duration or when all agents respond
- Late proposals are queued for next tick

**REQ-2.2.2:** Conflict Resolution System

- Implement action priority system: EMOTE > INTERACT > MOVE
- Implement stamina-based conflict resolution for physical actions
- Add randomness factor (5-10%) to prevent stalemates
- Support simultaneous action handling with explicit conflict rules

**REQ-2.2.3:** Proposal Validation

- Pre-validate proposals before resolution
- Check target existence and reachability
- Validate action parameters
- Reject invalid proposals with clear error messages

**REQ-2.2.4:** Deterministic Resolution

- Proposals must be resolved in deterministic order
- Timestamp-based ordering for simultaneous proposals
- Conflict resolution must be reproducible across runs

#### 2.2.2 Acceptance Criteria

**AC-2.2.1:** Proposal window respects time constraints
- [ ] Window opens at start of proposal phase
- [ ] Window closes after timeout or all agents respond
- [ ] Late proposals are queued, not lost

**AC-2.2.2:** Action priority system works
- [ ] EMOTE actions resolve before INTERACT
- [ ] INTERACT actions resolve before MOVE
- [ ] Priority is documented and testable

**AC-2.2.3:** Stamina-based conflict resolution
- [ ] Higher stamina wins physical conflicts
- [ ] Ties broken by randomness (5-10% factor)
- [ ] Conflict outcomes logged with reasoning

**AC-2.2.4:** Proposal validation prevents invalid actions
- [ ] Target existence checked before resolution
- [ ] Distance/range validation performed
- [ ] Invalid proposals rejected with error codes

**AC-2.2.5:** Deterministic resolution achieved
- [ ] Same inputs produce same outputs
- [ ] Random seed controlled for reproducibility
- [ ] Timestamp ordering consistent

**AC-2.2.6:** Simultaneous action handling
- [ ] Multiple agents can target same object
- [ ] First-come-first-served for COLLECT actions
- [ ] Combat actions allow simultaneous engagement

#### 2.2.3 Implementation Notes

- File: `tsukuyomi/proto/fate_engine.py`
- New classes to create:
  - `ConflictResolver`: Handles priority and stamina logic
  - `ProposalValidator`: Pre-validates proposals
- Methods to enhance:
  - `_phase_proposal_window()`: Add timing logic
  - `_phase_fate_resolution()`: Add conflict resolution
  - `resolve_proposal()`: Per-proposal resolution logic

---

### Task 2.3: Affordance System Completion

#### 2.3.1 Requirements

**REQ-2.3.1:** Runtime Affordance Resolution

- Implement affordance condition evaluation engine
- Support basic operators: AND, OR, <, >, ==, !=
- Evaluate conditions against world state and agent state
- Return detailed error messages for failed conditions

**REQ-2.3.2:** Effect Execution

- Implement effect description execution
- Support inventory modifications
- Support world state changes
- Support agent state modifications

**REQ-2.3.3:** Affordance Discovery

- Agents must be able to discover available affordances
- Affordances must be filtered by agent capabilities
- Hidden affordances (e.g., secret passages) have visibility rules

**REQ-2.3.4:** Standard Affordance Library

- Define standard affordance types: OPEN, CLOSE, LOCK, UNLOCK, COLLECT, DROP, USE, EXAMINE
- Document expected parameters for each type
- Provide example affordances

#### 2.3.2 Acceptance Criteria

**AC-2.3.1:** Condition evaluation engine works
- [ ] Simple conditions evaluate correctly (distance < 2.0)
- [ ] Compound conditions evaluate correctly (distance < 2.0 AND has_key)
- [ ] Variables resolve from world/agent state
- [ ] Syntax errors reported clearly

**AC-2.3.2:** Effect execution works
- [ ] Inventory effects modify agent inventory
- [ ] World state effects modify object properties
- [ ] Agent state effects modify agent properties
- [ ] Effects are transactional (all or nothing)

**AC-2.3.3:** Affordance discovery API
- [ ] `get_available_affordances(agent_id, object_id)` returns list
- [ ] Results filtered by agent capabilities
- [ ] Hidden affordances excluded unless agent meets criteria
- [ ] Discovery results logged

**AC-2.3.4:** Standard affordance library exists
- [ ] OPEN affordance defined with parameters
- [ ] CLOSE affordance defined with parameters
- [ ] COLLECT affordance defined with parameters
- [ ] Each type has documentation and examples

**AC-2.3.5:** Affordance integration with INTERACT actions
- [ ] INTERACT actions check affordances
- [ ] Invalid affordance attempts rejected
- [ ] Valid affordance attempts executed
- [ ] Results include effect outcomes

#### 2.3.3 Implementation Notes

- File: `tsukuyomi/core/affordance_system.py` (new)
- Classes to create:
  - `ConditionEvaluator`: Parses and evaluates conditions
  - `EffectExecutor`: Executes effect descriptions
  - `AffordanceManager`: Manages affordance discovery and resolution
- Integration points:
  - FateEngine: Check affordances during INTERACT resolution
  - WorldBuilder: Add affordances to objects
  - AgentBrain: Discover affordances for decision-making

---

### Task 2.4: Visual Perception with Raycasting

#### 2.4.1 Requirements

**REQ-2.4.1:** Raycasting Engine

- Implement 2D raycasting for line-of-sight checks
- Support multiple rays per agent (vision cone)
- Detect occlusion by objects with `blocks_vision` property
- Calculate visibility percentage for partial occlusion

**REQ-2.4.2:** Field of View (FOV) Tracking

- Track agent facing direction (heading angle)
- Calculate vision cone based on FOV angle and range
- Update facing direction on MOVE and ROTATE actions
- Support different FOV configurations per agent type

**REQ-2.4.3:** Visual Certainty Calculation

- Certainty decreases with distance
- Certainty reduced by occlusion
- Certainty affected by lighting conditions (future)
- Certainty affects position blurring

**REQ-2.4.4:** Vision Cone Optimization

- Use spatial index to limit raycast checks
- Only cast rays in occupied cells
- Cache vision results when agent is stationary
- Adaptive ray count based on performance

#### 2.4.2 Acceptance Criteria

**AC-2.4.1:** Raycasting detects occlusion
- [ ] Raycast returns true if path blocked
- [ ] Identifies blocking object
- [ ] Handles multiple blocking objects
- [ ] Performance: < 0.5ms per raycast

**AC-2.4.2:** FOV cone works correctly
- [ ] Agents only see within FOV angle
- [ ] FOV range respected
- [ ] Facing direction tracked correctly
- [ ] FOV updates on rotation

**AC-2.4.3:** Visual certainty calculated properly
- [ ] Certainty = 1.0 at distance 0
- [ ] Certainty decreases linearly with distance
- [ ] Occlusion reduces certainty to 0.0
- [ ] Low certainty triggers position blurring

**AC-2.4.4:** Vision optimization implemented
- [ ] Spatial index limits raycast targets
- [ ] Only occupied cells checked
- [ ] Cache used when agent stationary
- [ ] Ray count adapts to performance needs

**AC-2.4.5:** Perception pipeline integrated
- [ ] Raycasting used in `_process_vision_deep()`
- [ ] FOV checks in `_in_vision_cone()`
- [ ] Occlusion checks in `_is_occluded()`
- [ ] Certainty used in percept generation

#### 2.4.3 Implementation Notes

- File: `tsukuyomi/core/vision_system.py` (new)
- Classes to create:
  - `Raycaster`: 2D raycasting implementation
  - `VisionCone`: FOV calculation and tracking
  - `VisionSystem`: High-level vision management
- Integration points:
  - PerceptionPipeline: Use raycasting for occlusion
  - FateEngine: Track agent facing direction
  - SpatialIndex: Query for vision optimization

---

## 🗓️ Task Breakdown & Prioritization

### Sprint 1 (Week 3): Foundation

| Priority | Task | Estimated Effort | Dependencies |
|----------|------|------------------|--------------|
| P0 | Task 2.1: SpatialIndex Integration | 2 days | None |
| P0 | Task 2.2.1: Proposal Window Timing | 1 day | None |
| P0 | Task 2.3.1: Condition Evaluation | 2 days | None |

### Sprint 2 (Week 4): Core Mechanics

| Priority | Task | Estimated Effort | Dependencies |
|----------|------|------------------|--------------|
| P0 | Task 2.2.2: Conflict Resolution | 2 days | Sprint 1 |
| P0 | Task 2.3.2: Effect Execution | 1 day | Sprint 1 |
| P1 | Task 2.4.1: Raycasting Engine | 2 days | Sprint 1 |
| P1 | Task 2.2.3: Proposal Validation | 1 day | Sprint 1 |

### Sprint 3 (Week 5): Integration & Polish

| Priority | Task | Estimated Effort | Dependencies |
|----------|------|------------------|--------------|
| P0 | Task 2.3.3: Affordance Discovery | 1 day | Sprint 2 |
| P1 | Task 2.4.2: FOV Tracking | 1 day | Sprint 2 |
| P1 | Task 2.4.3: Visual Certainty | 1 day | Sprint 2 |
| P2 | Task 2.4.4: Vision Optimization | 1 day | Sprint 2 |
| P0 | Integration Testing | 2 days | All above |
| P0 | Documentation & Examples | 1 day | All above |

### Critical Path

1. **SpatialIndex Integration** (Foundation for everything else)
2. **Condition Evaluation** (Required for affordances)
3. **Conflict Resolution** (Required for proposal windows)
4. **Raycasting Engine** (Required for vision)
5. **Integration Testing** (Validate everything works together)

---

## 🧪 Testing Strategy

### Unit Tests

**2.1 SpatialIndex Tests**
- [ ] Test insert/remove/update operations
- [ ] Test query radius accuracy
- [ ] Test nearest-neighbor queries
- [ ] Test edge cases (boundary positions, duplicate IDs)
- [ ] Performance benchmarks (50, 100, 500 entities)

**2.2 Proposal Window Tests**
- [ ] Test window timing (timeout, early close)
- [ ] Test late proposal queuing
- [ ] Test action priority ordering
- [ ] Test stamina-based conflicts
- [ ] Test deterministic resolution

**2.3 Affordance System Tests**
- [ ] Test condition evaluation (simple, compound)
- [ ] Test effect execution (inventory, world state)
- [ ] Test affordance discovery
- [ ] Test standard affordance library
- [ ] Test transaction rollback on failure

**2.4 Visual Perception Tests**
- [ ] Test raycasting accuracy
- [ ] Test FOV cone calculation
- [ ] Test occlusion detection
- [ ] Test visual certainty calculation
- [ ] Test vision optimization

### Integration Tests

**Scenario 1: Marketplace Interaction**
- 4 agents (Merchant, Guard, Peasant, Thief)
- Multiple interactive objects (stalls, doors, items)
- Verify agents discover and use affordances
- Verify conflicts resolved correctly
- Verify spatial queries work under load

**Scenario 2: Combat Encounter**
- 2 agents in combat
- Simultaneous attack proposals
- Verify stamina-based conflict resolution
- Verify action priorities respected
- Verify combat flows naturally

**Scenario 3: Stealth Scenario**
- 1 agent hiding behind obstacle
- 1 agent searching
- Verify occlusion works correctly
- Verify FOV constraints respected
- Verify vision cone accuracy

### Performance Tests

- **TPS (Ticks Per Second):** Target > 10 TPS with 50 agents
- **Query Latency:** Average < 1ms for proximity queries
- **Memory Usage:** < 50MB for 50 agents, 100 objects
- **Stability:** Run for 1 hour without memory leaks

---

## 📊 Success Metrics

### Phase 2 Completion Criteria

Phase 2 is considered complete when ALL of the following are met:

1. ✅ **Autonomy:** >95% of agent actions are autonomous (no user prompts)
2. ✅ **Spatial Performance:** 50 agents run with < 200ms tick time
3. ✅ **Affordance Usage:** Agents successfully use affordances in >80% of interactions
4. ✅ **Conflict Resolution:** Zero logic errors in simultaneous action handling
5. ✅ **Vision Accuracy:** Occlusion and FOV constraints work correctly in all test scenarios
6. ✅ **Test Coverage:** >90% code coverage for new Phase 2 components

### Performance Targets

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Tick Time (50 agents) | < 200ms | TBD | TBD |
| Spatial Query Latency | < 1ms | TBD | TBD |
| TPS (Throughput) | > 10 | TBD | TBD |
| Memory Usage (50 agents) | < 50MB | TBD | TBD |
| Test Coverage | > 90% | TBD | TBD |

### Quality Gates

Before Phase 2 is marked complete:

- [ ] All P0 tasks completed and tested
- [ ] All acceptance criteria met
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Code review approved

---

## 🔧 Technical Specifications

### Data Structures

**Proposal Window State**
```python
@dataclass
class ProposalWindowState:
    window_start: float
    window_duration: float
    proposals: List[Proposal]
    pending_agents: Set[str]
    late_proposals: List[Proposal]
    is_closed: bool
```

**Conflict Resolution Result**
```python
@dataclass
class ConflictResult:
    winning_proposal_id: str
    losing_proposal_ids: List[str]
    resolution_reason: str  # "priority", "stamina", "random"
    random_seed: int
```

**Affordance Resolution Context**
```python
@dataclass
class AffordanceContext:
    agent_id: str
    object_id: str
    affordance: Affordance
    world_state: WorldState
    agent_state: ActorState
```

### API Contracts

**SpatialIndex API**
```python
def insert(object_id: str, position: Tuple[float, float]) -> None
def remove(object_id: str) -> bool
def update_position(object_id: str, new_position: Tuple[float, float]) -> None
def query(position: Tuple[float, float], radius: float, exclude_self: Optional[str]) -> List[Tuple[str, Tuple[float, float]]]
def query_nearest(position: Tuple[float, float], limit: int) -> List[Tuple[str, Tuple[float, float], float]]
```

**Affordance API**
```python
def evaluate_condition(condition: str, context: AffordanceContext) -> bool
def execute_effect(effect: str, context: AffordanceContext) -> bool
def discover_affordances(agent_id: str, object_id: str) -> List[Affordance]
```

**Vision API**
```python
def cast_ray(start: Vector2, end: Vector2, world_state: WorldState) -> Optional[str]  # Returns blocking object_id
def is_in_fov(agent_pos: Vector2, agent_facing: float, target_pos: Vector2, fov_angle: float, fov_range: float) -> bool
def calculate_visual_certainty(distance: float, occlusion: bool) -> float
```

---

## 📚 Documentation Requirements

### Code Documentation

- All new classes must have docstrings
- All public methods must have docstrings
- Complex algorithms must have inline comments
- Type hints required for all functions

### User Documentation

- **Affordance System Guide:** How to define and use affordances
- **Proposal Window Guide:** How commitment phases work
- **Visual Perception Guide:** How vision and occlusion work
- **API Reference:** Complete API documentation

### Examples

- **Marketplace Scenario:** Complete example with affordances
- **Combat Scenario:** Example with conflict resolution
- **Stealth Scenario:** Example with vision and occlusion

---

## 🚨 Risks & Mitigations

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SpatialIndex performance degrades with 100+ agents | Medium | High | Implement adaptive cell sizing, quadtree fallback |
| Raycasting too slow for real-time | Medium | High | Use spatial index optimization, adaptive ray count |
| Condition evaluation security vulnerability | Low | High | Use sandboxed expression evaluator, validate inputs |
| Conflict resolution non-deterministic | Medium | Medium | Use seeded random, fix ordering logic |

### Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Phase 2 scope creep | High | Medium | Strict change control, defer features to Phase 3 |
| Integration complexity underestimated | Medium | High | Early integration testing, buffer time |
| Team knowledge gaps | Low | Medium | Pair programming, code reviews, documentation |

---

## 📞 Coordination & Communication

### Team Roles

| Role | Responsibilities |
|------|------------------|
| Product Manager (This role) | Requirements definition, prioritization, acceptance criteria |
| Backend Engineer | SpatialIndex, Proposal Window, Affordance System |
| AI Engineer | Visual Perception, Raycasting, Perception Pipeline |
| QA Engineer | Test planning, execution, quality gates |
| Tech Lead | Architecture review, code review, technical decisions |

### Communication Channels

- **Daily Standup:** Progress updates, blockers
- **Sprint Planning:** Task breakdown, estimation
- **Code Review:** Pull request reviews
- **Weekly Review:** Demo progress, adjust plans

### Artifacts

- **Requirements:** This document (PHASE_2_REQUIREMENTS.md)
- **Design:** TSUKUYOMI_V2_ARCHITECTURE.md
- **Progress:** PROJECT_TREE.md (task tracking)
- **Tests:** tests/ directory

---

## 📝 Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Product Manager | Initial requirements document |

---

## ✅ Sign-Off

**Approval Required:**

- [ ] Product Manager: _________________ Date: _______
- [ ] Tech Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______

---

## 📎 Appendix

### A. Affordance Examples

**Door Affordance**
```python
Affordance(
    action_type="OPEN",
    precondition="distance < 2.0 AND (agent.inventory.contains('key') OR object.properties['locked'] == false)",
    effect="object.properties['open'] = true"
)
```

**Stall Affordance**
```python
Affordance(
    action_type="BUY",
    precondition="distance < 2.0 AND agent.inventory.money >= 5",
    effect="agent.inventory.money -= 5; agent.inventory.add('apple')"
)
```

### B. Conflict Resolution Example

**Scenario:** Two agents try to grab the same coin simultaneously.

**Resolution Process:**
1. Check action priority: Both are COLLECT (same priority)
2. Check stamina: Agent A stamina = 0.8, Agent B stamina = 0.6
3. Apply randomness: Random seed 12345 → Agent A wins
4. Result: Agent A gets coin, Agent B receives "failed" resolution

### C. Vision Cone Diagram

```
        ← FOV Range →
        ───────────────
       /              \
      /    Vision      \
     /      Cone        \
    /                    \
   ←──── FOV Angle ────→
    (e.g., 120 degrees)
```

---

**End of Phase 2 Requirements Document**
