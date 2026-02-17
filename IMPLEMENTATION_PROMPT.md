# Tsukuyomi V2 - Agent Quality Implementation

## Mission

You are the **Lead Engineer** of a multi-agent engineering team implementing the Agent Quality Specification. Your team will build **5 agents that feel ALIVE** - with stable personalities, deep memory, natural conversations, visible reasoning, and narrative-driven behavior.

## Project Context

### Directory Structure
```
/root/.openclaw/workspace/tsukuyomi/
├── tsukuyomi/
│   ├── brain/           # Agent cognition (AgentBrain, LLMService, MemoryManager, etc.)
│   ├── core/            # Server-side systems (FateEngine, SpatialIndex, etc.)
│   ├── proto/           # gRPC definitions
│   └── dev_artifacts/   # Spec files (READ THESE FIRST)
├── docs/                # Documentation
├── experiments/         # Test scenarios
└── IMPLEMENTATION_PROMPT.md  # This file
```

### Key Spec Files (READ THESE FIRST)
1. `tsukuyomi/dev_artifacts/AGENT_QUALITY_SPEC_2026-02-16.md` - THE SPEC TO IMPLEMENT
2. `tsukuyomi/dev_artifacts/ARCHITECTURE_ANALYSIS_2026-02-16.md` - Current architecture
3. `tsukuyomi/dev_artifacts/COGNITIVE_SYSTEMS_ANALYSIS_2026-02-16.md` - Brain systems
4. `tsukuyomi/dev_artifacts/SOCIAL_SYSTEMS_ANALYSIS_2026-02-16.md` - Social dynamics
5. `tsukuyomi/dev_artifacts/INFRASTRUCTURE_ANALYSIS_2026-02-16.md` - gRPC, spatial, etc.

### Existing Codebase (UNDERSTAND BEFORE MODIFYING)
- `tsukuyomi/brain/AgentBrain.py` - Main agent controller (has NeedsSystem, MemoryManager, BeliefManager, RelationshipManager)
- `tsukuyomi/brain/LLMService.py` - LLM integration (Groq/OpenAI)
- `tsukuyomi/brain/MemoryManager.py` - Episodic/semantic memory
- `tsukuyomi/brain/StateManager.py` - PAD emotional model
- `tsukuyomi/brain/BeliefManager.py` - Evidence-based beliefs
- `tsukuyomi/brain/RelationshipManager.py` - Social affinity
- `tsukuyomi/proto/fate_engine.py` - Server-authoritative tick loop
- `tsukuyomi/core/spatial_index.py` - O(1) proximity queries

## Implementation Strategy: Vertical Slice First

### Phase 0: Validation (DO THIS FIRST)
Before full implementation, validate the architecture with a minimal test:

1. Create `experiments/vertical_slice_test.py`
2. Implement minimal versions for 2 agents:
   - Simplified PersonalityProfile (name + 3 traits)
   - Basic memory decay (no consolidation yet)
   - Simple conversation tracking (no sentiment yet)
3. Run 100-tick simulation
4. Verify outputs in `simulation_output/`:
   - `transcript.md` shows coherent dialogue
   - `thoughts.md` shows distinct personalities
   - Memory system stores and retrieves correctly

**If vertical slice fails, STOP and report issues. Do not proceed to full implementation.**

## Phase Implementation Order

### Phase 14: Personality Integrity System
**Goal:** Ensure agents have stable, consistent personalities.

**Files to create/modify:**
- `tsukuyomi/brain/personality/` (new directory)
  - `profile.py` - PersonalityProfile dataclass
  - `constraint_sampler.py` - Pre-generation validation
  - `drift_monitor.py` - Post-generation drift detection
  - `evolution_manager.py` - Intentional personality changes
- `tsukuyomi/brain/AgentBrain.py` - Integrate personality enforcement

**Key Features:**
1. PersonalityProfile with Big Five traits
2. Pre-generation validation (forbidden patterns, action filters)
3. Drift detection with EMA tracking
4. Personality evolution for intentional changes

**Success Criteria:**
- 90%+ personality consistency
- 80%+ drift detection accuracy
- 70%+ prevention effectiveness

### Phase 15: Deep Memory Architecture
**Goal:** Agents remember experiences meaningfully.

**Files to create/modify:**
- `tsukuyomi/brain/memory/` (new directory)
  - `memory_types.py` - Memory dataclass with full schema
  - `decay_calculator.py` - Memory decay function
  - `consolidation.py` - Memory consolidation
  - `retrieval.py` - Context-aware retrieval
- `tsukuyomi/brain/MemoryManager.py` - Enhance existing

**Key Features:**
1. Memory types (Episodic, Semantic, Emotional, Social, Procedural)
2. Decay function with emotional resistance
3. Memory consolidation for generalizations
4. Context-aware retrieval with participant matching

**Success Criteria:**
- 80%+ retrieval relevance
- 90%+ decay accuracy
- Memory bounded to <500 entries/agent

### Phase 16: Natural Conversation System
**Goal:** Real conversations with sentiment and reputation.

**Files to create/modify:**
- `tsukuyomi/brain/conversation/` (new directory)
  - `conversation_state.py` - ConversationState, ConversationTurn
  - `sentiment_analyzer.py` - Rule-based sentiment
  - `reputation_manager.py` - Trust tracking
  - `conversation_manager.py` - Flow management
- `tsukuyomi/brain/logging/` (new directory)
  - `narrative_logger.py` - Human-readable outputs

**Key Features:**
1. Sentiment analysis for speech
2. Reputation tracking (trustworthiness, prediction accuracy)
3. Heat level tracking with sentiment integration
4. Narrative logger (transcript.md, thoughts.md, narrative.md)

**Success Criteria:**
- 85%+ conversation naturalness
- 75%+ sentiment accuracy
- 70%+ trust prediction accuracy

### Phase 17: Reasoning Transparency
**Goal:** Visible and understandable agent reasoning.

**Files to create/modify:**
- `tsukuyomi/brain/reasoning/` (new directory)
  - `decision_record.py` - Complete decision context
  - `confidence_calibration.py` - Historical accuracy tracking
  - `reasoning_validator.py` - Consistency checks
  - `reasoning_logger.py` - Structured logging

**Key Features:**
1. DecisionRecord with full context
2. Confidence calibration with EMA
3. Reasoning validation (trait, belief, needs consistency)
4. Structured output for dashboard

**Success Criteria:**
- 100% decisions logged
- Confidence gap < 0.15
- 85%+ trait consistency

### Phase 18: Scenario-Driven Narrative
**Goal:** Story orchestration with branching narratives.

**Files to create/modify:**
- `tsukuyomi/scenarios/` (new directory)
  - `scenario_loader.py` - YAML parser
  - `scenario_schema.py` - Validation
- `tsukuyomi/core/drama/` (new directory)
  - `context_aware_director.py` - Enhanced DramaDirector
  - `event_library.py` - Context-matched events
  - `branch_manager.py` - Narrative branching

**Key Features:**
1. YAML scenario format with branching
2. Context-aware event injection
3. Branch evaluation and selection
4. End condition detection

**Success Criteria:**
- 90%+ beat trigger accuracy
- 85%+ branch selection
- 80%+ context-aware relevance

### Phase 19: Simulation Runner
**Goal:** Simple command to run simulations.

**Files to create:**
- `tsukuyomi/cli/` (new directory)
  - `runner.py` - Main CLI entry point
  - `output_manager.py` - Standardized outputs

**CLI Interface:**
```bash
python -m tsukuyomi run scenarios/jury_deliberation.yaml --ticks 5000 --output ./simulation_output/
```

**Output Structure:**
```
simulation_output/jury_deliberation_2026-02-16_23-00/
├── transcript.md        # Dialogue log
├── thoughts.md          # Agent thoughts
├── reasoning.md         # Decision records
├── narrative.md         # Narrative summary
├── events.json          # Raw event log
├── agent_states.json    # Final agent states
└── summary.md           # Simulation summary
```

## Code Quality Standards

### Python Style
- Use Python 3.10+ type hints
- Follow PEP 8 (use `black` formatter)
- Docstrings for all public classes/methods
- Maximum line length: 100 characters

### Testing
- Create `tests/` directory with unit tests
- Use `pytest` framework
- Minimum 80% coverage for new code
- Integration tests in `experiments/tests/`

### Documentation
- Update `docs/` with implementation details
- Create `docs/API_REFERENCE.md` for new modules
- Keep `README.md` updated

### File Organization
```
tsukuyomi/
├── brain/
│   ├── personality/     # Phase 14
│   ├── memory/          # Phase 15
│   ├── conversation/    # Phase 16
│   ├── reasoning/       # Phase 17
│   └── logging/         # Phase 16
├── core/
│   └── drama/           # Phase 18
├── scenarios/           # Phase 18
├── cli/                 # Phase 19
└── tests/               # All phases
```

## Implementation Workflow

1. **READ** the spec files first - understand what you're building
2. **UNDERSTAND** the existing codebase - don't break working systems
3. **IMPLEMENT** Phase 0 (vertical slice) - validate architecture
4. **PROCEED** through phases 14-19 in order
5. **TEST** each phase before moving to next
6. **DOCUMENT** as you go
7. **CLEANUP** - remove dead code, organize imports, format files

## Critical Rules

1. **DO NOT** modify files outside `tsukuyomi/` directory
2. **DO NOT** break existing functionality - run tests before committing
3. **DO** maintain backward compatibility with existing scenarios
4. **DO** follow the existing code style patterns
5. **DO** keep the codebase clean and professional for public publishing
6. **DO** create comprehensive docstrings and type hints
7. **DO** add tests for all new functionality

## Success Definition

We succeed when:
1. Run a 5-agent simulation for 30 minutes
2. Read `transcript.md` and see coherent conversation
3. Read `thoughts.md` and understand each agent's internal state
4. Read `narrative.md` and see a story that makes sense
5. Each agent has a distinct, consistent personality
6. Agents reference past events in their reasoning
7. The narrative flows naturally without manual intervention

## Start Here

Begin by reading the spec files, then implement Phase 0 (vertical slice) to validate the architecture. Report any issues found during validation before proceeding.

Good luck, team! 🏛️
