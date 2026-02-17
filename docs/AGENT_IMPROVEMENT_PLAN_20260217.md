# Agent Improvement Plan
## General Fixes for Universal Agent Capabilities

**Date:** February 17, 2026  
**Version:** 1.0  
**Status:** Draft  
**Author:** Tanit

---

## 1. Problem Statement

The Angry Men experiment revealed critical gaps in agent behavior:

| Issue | Observation | Root Cause |
|-------|-------------|------------|
| No vote changes | Positions remained static | No belief update mechanism |
| Limited memory | Didn't reference earlier statements | Memory not integrated into prompts |
| Static arguments | Repetitive reasoning | No decision tracking |
| No simulation integration | FateEngine disconnected | Missing proposal system |

**These issues are NOT specific to the Angry Men experiment** — they apply to ANY scenario where agents need to:
- Remember what happened
- Update their beliefs based on new information
- Make consistent decisions
- Interact with a simulation engine

---

## 2. Architecture Overview

### 2.1 Current State (Phases 1-5 Complete)

```
tsukuyomi/agent/
├── identity.py           ✅ AgentIdentity, CoreValue, DefiningMemory
├── memory_system.py      ✅ LongTermMemory with RAG retrieval
├── immersive_prompt.py   ✅ Prompt builder for immersion
├── universal_agent.py    ✅ Scenario-agnostic agent runtime
└── scenarios/
    ├── base.py           ✅ ScenarioContext base class
    └── jury.py           ✅ JuryDeliberationScenario
```

### 2.2 Missing Components (Phases 6-10)

```
tsukuyomi/agent/
├── belief_system.py      🆕 Belief tracking and updates
├── persuasion.py         🆕 Persuasion dynamics
├── decision_engine.py    🆕 Decision tracking and reasoning
├── context_manager.py    🆕 Cross-turn context management
└── proposal_handler.py   🆕 FateEngine integration
```

---

## 3. Phase 6: Belief Dynamics System

### 3.1 Goal
Agents should be able to:
- Track their beliefs with confidence levels
- Update beliefs based on new evidence
- Detect contradictions and resolve them

### 3.2 Data Model

```python
@dataclass
class Belief:
    """A belief held by an agent."""
    id: str
    statement: str              # What they believe
    confidence: float           # 0.0-1.0 (how certain)
    source: str                 # Where belief came from
    evidence: List[str]         # Supporting evidence
    counter_evidence: List[str] # Contradicting evidence
    mutable: bool = True        # Can this belief change?
    last_updated: int = 0       # Tick when last updated


class BeliefSystem:
    """
    Manages agent beliefs and updates.
    
    Key methods:
    - add_belief(statement, confidence, source)
    - update_belief(belief_id, new_confidence, evidence)
    - check_contradiction(statement) -> Optional[Belief]
    - get_beliefs_about(topic) -> List[Belief]
    """
    
    def evaluate_evidence(
        self,
        belief: Belief,
        new_evidence: str,
        source_reliability: float
    ) -> float:
        """
        Calculate new confidence based on evidence.
        
        Uses Bayesian-like update:
        P(B|E) = P(E|B) * P(B) / P(E)
        
        Simplified:
        new_confidence = old_confidence + (evidence_impact * reliability * (1 - old_confidence))
        """
        pass
```

### 3.3 Integration Points

| Method | Location | Action |
|--------|----------|--------|
| `respond()` | `UniversalAgent` | Check beliefs before responding |
| `observe()` | `UniversalAgent` | Update beliefs on new evidence |
| `reflect()` | `UniversalAgent` | Review and consolidate beliefs |

### 3.4 Tests Required

```python
def test_belief_creation():
    """Belief can be created and stored."""
    
def test_belief_update_positive_evidence():
    """Confidence increases with supporting evidence."""
    
def test_belief_update_negative_evidence():
    """Confidence decreases with contradicting evidence."""
    
def test_belief_contradiction_detection():
    """System detects contradictory beliefs."""
    
def test_belief_immutable():
    """Immutable beliefs don't change."""
```

---

## 4. Phase 7: Persuasion Engine

### 4.1 Goal
Agents should be able to:
- Be persuaded by convincing arguments
- Persuade others with their arguments
- Track persuasion history

### 4.2 Data Model

```python
@dataclass
class Argument:
    """An argument presented to the agent."""
    id: str
    claim: str                  # The claim being made
    evidence: List[str]         # Supporting evidence
    source_agent: str           # Who made the argument
    source_credibility: float   # How trustworthy the source is
    emotional_appeal: float     # 0.0-1.0 emotional vs logical
    tick: int                   # When it was presented


@dataclass
class PersuasionResult:
    """Result of a persuasion attempt."""
    argument_id: str
    agent_id: str
    initial_confidence: float
    final_confidence: float
    change: float               # How much confidence changed
    reason: str                 # Why it changed (or didn't)
    persuasive: bool            # Did it change belief?


class PersuasionEngine:
    """
    Models how agents are persuaded.
    
    Factors:
    1. Source credibility (trust in speaker)
    2. Evidence strength
    3. Emotional resonance
    4. Cognitive bias (confirmation bias, etc.)
    5. Personality traits (openness, stubbornness)
    """
    
    def evaluate_argument(
        self,
        agent: UniversalAgent,
        argument: Argument
    ) -> PersuasionResult:
        """
        Evaluate how persuasive an argument is for this agent.
        
        Formula:
        persuasion_strength = (
            source_credibility *
            evidence_strength *
            (1 + emotional_appeal * agent.emotional_susceptibility) *
            (1 - agent.stubbornness)
        )
        
        if argument aligns with existing beliefs:
            persuasion_strength *= (1 + confirmation_bias)
        else:
            persuasion_strength *= (1 - confirmation_bias)
        """
        pass
```

### 4.3 Integration Points

| Method | Location | Action |
|--------|----------|--------|
| `hear_argument()` | `UniversalAgent` | Process argument, update beliefs |
| `make_argument()` | `UniversalAgent` | Generate persuasive argument |
| `get_persuasion_history()` | `UniversalAgent` | Review past persuasions |

### 4.4 Tests Required

```python
def test_argument_evaluation():
    """Arguments are evaluated correctly."""
    
def test_credibility_factor():
    """Higher credibility sources are more persuasive."""
    
def test_confirmation_bias():
    """Agents prefer arguments that match beliefs."""
    
def test_stubbornness_factor():
    """Stubborn agents are harder to persuade."""
    
def test_emotional_appeal():
    """Emotional appeals work on susceptible agents."""
```

---

## 5. Phase 8: Decision Engine

### 5.1 Goal
Agents should be able to:
- Make decisions with explicit reasoning
- Track decision history
- Maintain decision consistency

### 5.2 Data Model

```python
@dataclass
class Decision:
    """A decision made by an agent."""
    id: str
    decision_type: str          # "vote", "action", "stance"
    choice: str                 # What they decided
    confidence: float           # How confident in decision
    reasoning: List[str]        # Why they decided this
    supporting_beliefs: List[str]  # Beliefs that support this
    contradicting_beliefs: List[str]  # Beliefs against this
    tick: int                   # When decided
    mutable: bool = True        # Can this decision change?


class DecisionEngine:
    """
    Manages agent decisions and consistency.
    
    Key methods:
    - make_decision(type, options, context) -> Decision
    - reconsider_decision(decision_id, new_evidence) -> Decision
    - get_decision_history(type) -> List[Decision]
    - check_consistency(new_decision) -> bool
    """
    
    def make_decision(
        self,
        decision_type: str,
        options: List[str],
        context: str,
        agent: UniversalAgent
    ) -> Decision:
        """
        Make a decision based on beliefs and context.
        
        Process:
        1. Retrieve relevant beliefs
        2. Evaluate each option against beliefs
        3. Generate reasoning
        4. Record decision
        """
        pass
    
    def reconsider(
        self,
        decision: Decision,
        new_evidence: str,
        agent: UniversalAgent
    ) -> Decision:
        """
        Reconsider a decision in light of new evidence.
        
        Only possible if decision.mutable = True
        """
        pass
```

### 5.3 Integration Points

| Method | Location | Action |
|--------|----------|--------|
| `decide()` | `UniversalAgent` | Make a decision |
| `reconsider()` | `UniversalAgent` | Reconsider past decision |
| `get_stance()` | `UniversalAgent` | Get current stance on topic |

### 5.4 Tests Required

```python
def test_decision_creation():
    """Decisions can be created and stored."""
    
def test_decision_reasoning():
    """Decisions include reasoning chains."""
    
def test_decision_consistency():
    """Inconsistent decisions are flagged."""
    
def test_decision_reconsideration():
    """Decisions can be reconsidered with new evidence."""
    
def test_immutable_decision():
    """Immutable decisions cannot be reconsidered."""
```

---

## 6. Phase 9: Context Manager

### 6.1 Goal
Agents should be able to:
- Remember what others said
- Track conversation history
- Maintain cross-turn context

### 6.2 Data Model

```python
@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    tick: int
    speaker: str
    content: str
    topic: str
    sentiment: float           # Positive/negative
    key_claims: List[str]      # Important claims made


class ContextManager:
    """
    Manages cross-turn context for agents.
    
    Key methods:
    - record_turn(speaker, content, tick)
    - get_context(topic, k_turns) -> List[ConversationTurn]
    - get_statements_by(agent_id) -> List[ConversationTurn]
    - get_key_claims(topic) -> List[str]
    - summarize_context() -> str
    """
    
    def extract_key_claims(self, content: str) -> List[str]:
        """
        Extract key claims from a statement.
        
        Uses LLM to identify:
        - Facts stated
        - Opinions expressed
        - Arguments made
        """
        pass
    
    def build_context_prompt(
        self,
        current_topic: str,
        k_turns: int = 10
    ) -> str:
        """
        Build a context summary for prompts.
        
        Format:
        "Previously in the discussion:
        - [Speaker A] said X about [topic]
        - [Speaker B] argued Y
        - [Speaker A] responded with Z"
        """
        pass
```

### 6.3 Integration Points

| Method | Location | Action |
|--------|----------|--------|
| `hear()` | `UniversalAgent` | Record what another agent said |
| `get_discussion_context()` | `UniversalAgent` | Get context for response |
| `recall_statement()` | `UniversalAgent` | Recall specific statement |

### 6.4 Tests Required

```python
def test_turn_recording():
    """Conversation turns are recorded."""
    
def test_context_retrieval():
    """Context can be retrieved by topic."""
    
def test_statement_recall():
    """Specific statements can be recalled."""
    
def test_key_claim_extraction():
    """Key claims are extracted from statements."""
    
def test_context_summary():
    """Context can be summarized for prompts."""
```

---

## 7. Phase 10: Proposal Handler

### 7.1 Goal
Agents should be able to:
- Submit proposals to the simulation
- React to proposals from others
- Track proposal outcomes

### 7.2 Data Model

```python
@dataclass
class Proposal:
    """A proposal submitted to the simulation."""
    id: str
    agent_id: str
    action: str                 # What action to take
    parameters: Dict[str, Any]  # Action parameters
    reasoning: str              # Why this action
    tick: int                   # When submitted
    priority: float = 0.5       # Importance


@dataclass
class ProposalOutcome:
    """Outcome of a submitted proposal."""
    proposal_id: str
    accepted: bool
    result: str                 # What happened
    tick: int                   # When resolved


class ProposalHandler:
    """
    Handles proposal submission and tracking.
    
    Key methods:
    - submit_proposal(action, params, reasoning) -> Proposal
    - get_pending_proposals() -> List[Proposal]
    - get_outcome(proposal_id) -> ProposalOutcome
    - react_to_proposal(proposal) -> str
    """
    
    async def submit_to_engine(
        self,
        proposal: Proposal,
        engine: "FateEngine"
    ) -> ProposalOutcome:
        """
        Submit proposal to FateEngine.
        
        Uses gRPC to communicate with engine.
        """
        pass
```

### 7.3 Integration Points

| Method | Location | Action |
|--------|----------|--------|
| `propose()` | `UniversalAgent` | Submit proposal |
| `react()` | `UniversalAgent` | React to proposal |
| `get_my_proposals()` | `UniversalAgent` | Get agent's proposals |

### 7.4 Tests Required

```python
def test_proposal_creation():
    """Proposals can be created."""
    
def test_proposal_submission():
    """Proposals can be submitted to engine."""
    
def test_proposal_outcome():
    """Outcomes are tracked."""
    
def test_proposal_reaction():
    """Agents can react to proposals."""
```

---

## 8. Implementation Order

### Phase Dependencies

```
Phase 6 (Beliefs) ──┬──> Phase 7 (Persuasion) ──> Phase 8 (Decisions)
                    │
                    └──> Phase 9 (Context) ──> Phase 10 (Proposals)
```

### Recommended Order

1. **Phase 6: Belief System** (Foundation for everything else)
   - 5 files to create/modify
   - ~15 tests

2. **Phase 9: Context Manager** (Enables memory integration)
   - 3 files to create/modify
   - ~10 tests

3. **Phase 7: Persuasion Engine** (Depends on beliefs)
   - 4 files to create/modify
   - ~12 tests

4. **Phase 8: Decision Engine** (Depends on beliefs + persuasion)
   - 4 files to create/modify
   - ~12 tests

5. **Phase 10: Proposal Handler** (Integration layer)
   - 3 files to create/modify
   - ~8 tests

---

## 9. Integration with UniversalAgent

After all phases, `UniversalAgent` will have:

```python
class UniversalAgent:
    # Existing (Phases 1-5)
    identity: AgentIdentity
    memory: LongTermMemory
    prompt_builder: ImmersivePromptBuilder
    
    # New (Phases 6-10)
    beliefs: BeliefSystem
    persuasion: PersuasionEngine
    decisions: DecisionEngine
    context: ContextManager
    proposals: ProposalHandler
    
    # New methods
    async def hear(self, speaker: str, content: str) -> None:
        """Hear and process what another agent said."""
        # Record in context
        await self.context.record_turn(speaker, content, self.current_tick)
        
        # Extract claims
        claims = await self.context.extract_key_claims(content)
        
        # Update beliefs based on claims
        for claim in claims:
            await self.beliefs.evaluate_claim(claim, source=speaker)
    
    async def decide(
        self,
        decision_type: str,
        options: List[str],
        context: str
    ) -> Decision:
        """Make a decision with reasoning."""
        decision = await self.decisions.make_decision(
            decision_type, options, context, self
        )
        return decision
    
    async def reconsider(
        self,
        decision_id: str,
        new_evidence: str
    ) -> Decision:
        """Reconsider a past decision."""
        return await self.decisions.reconsider(
            decision_id, new_evidence, self
        )
    
    async def propose(
        self,
        action: str,
        parameters: Dict,
        reasoning: str
    ) -> Proposal:
        """Submit a proposal to the simulation."""
        return await self.proposals.submit_proposal(
            action, parameters, reasoning, self.agent_id
        )
```

---

## 10. Success Metrics

After implementation, agents should:

| Metric | Before | After |
|--------|--------|-------|
| Vote changes | 0 | 2-4 per deliberation |
| Cross-turn references | 0 | 5+ per agent |
| Decision reasoning depth | 1 sentence | 3-5 sentences |
| Belief updates | 0 | 5-10 per session |
| Proposal submissions | 0 | 2-5 per agent |

---

## 11. Files to Create

```
tsukuyomi/agent/
├── belief_system.py      (~500 lines)
├── persuasion.py         (~400 lines)
├── decision_engine.py    (~450 lines)
├── context_manager.py    (~350 lines)
├── proposal_handler.py   (~300 lines)
└── tests/
    ├── test_belief_system.py     (~300 lines)
    ├── test_persuasion.py        (~250 lines)
    ├── test_decision_engine.py   (~280 lines)
    ├── test_context_manager.py   (~220 lines)
    └── test_proposal_handler.py  (~180 lines)
```

**Total:** ~2,000 lines of code + ~1,230 lines of tests

---

## 12. Next Steps

1. Review and approve this plan
2. Implement Phase 6 (Belief System) first
3. Write tests before implementation
4. Integrate with UniversalAgent incrementally
5. Run Angry Men experiment again to validate

---

*End of Plan*