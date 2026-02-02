# Tsukuyomi (The Moon Reader): MVP Technical Specification
## Generative Simulation Engine - Minimum Viable Product

**Version:** 1.2  
**Date:** January 2025  
**Status:** Draft Specification (Updated with LOD Tiers, Circuit Breakers, Deterministic Replay, Budget Mode, Secret Objectives, Tension Monitor, Pre-Action Validation Gate, Latency Masking, Sleep Cycle Consolidation, Context Token Budgets, Thought Bubble Inspector)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [MVP Scope & Goals](#2-mvp-scope--goals)
3. [Core Systems Architecture](#3-core-systems-architecture)
4. [Memory Architecture](#4-memory-architecture)
   - 4.6 [Context Window Token Budgets (HIGH PRIORITY)](#46-context-window-token-budgets-high-priority)
   - 4.7 [Sleep Cycle Consolidation (Memory Pruning)](#47-sleep-cycle-consolidation-memory-pruning)
5. [Social Dynamics Engine](#5-social-dynamics-engine)
6. [Dual-Mode Cognition](#6-dual-mode-cognition)
   - 6.6.1 [Latency Masking: The "Umm..." Protocol](#661-latency-masking-the-umm-protocol)
   - 6.7 [Agent LOD (Level of Detail) Tiers](#67-agent-lod-level-of-detail-tiers)
   - 6.7.4 [Secret Objective Injection (Narrative Quality Enhancement)](#674-secret-objective-injection-narrative-quality-enhancement)
7. [Demo Scenario: Three-Act Structure](#7-demo-scenario-three-act-structure)
   - 7.4.1 [Thought Bubble Inspector (Debug UI Enhancement)](#741-thought-bubble-inspector-debug-ui-enhancement)
   - 7.5 [World Tension Monitor & Aggressive Director](#75-world-tension-monitor--aggressive-director)
8. [Technical Implementation](#8-technical-implementation)
   - 8.3.4 [Circuit Breaker Patterns for LLM Failures](#834-circuit-breaker-patterns-for-llm-failures)
   - 8.3.6 [Pre-Action Validation Gate (HIGH PRIORITY)](#836-pre-action-validation-gate-high-priority)
9. [API Contracts](#9-api-contracts)
10. [Testing & Validation](#10-testing--validation)
    - 10.4 [Deterministic Replay Mechanism](#104-deterministic-replay-mechanism)
11. [Risk Assessment & Mitigations](#11-risk-assessment--mitigations)
12. [Budget Mode for Development Efficiency](#12-budget-mode-for-development-efficiency)
13. [MVP Timeline & Milestones](#13-mvp-timeline--milestones)
14. [Success Criteria](#14-success-criteria)
15. [Implementation Roadmap](#15-implementation-roadmap)

---

## 1. Executive Summary

The Tsukuyomi MVP demonstrates a **generative simulation engine** where AI-driven agents exhibit:

- **Persistent Memory**: Agents remember past experiences (episodic) and accumulated knowledge (semantic)
- **Social Dynamics**: Gossip propagation, relationship evolution, and belief networks
- **Dual-Mode Thinking**: Fast reflexive responses and slow deliberative reasoning

The MVP showcases these capabilities through a contained village scenario with 15-20 agents, demonstrating emergent narrative through a three-act dramatic structure over a 10-15 minute runtime.

### MVP Differentiators

| Feature | Traditional NPC | Tsukuyomi Agent |
|---------|----------------|---------------------|
| Memory | Session-only state machines | Persistent episodic + semantic memory |
| Social | Scripted relationships | Dynamic gossip & belief propagation |
| Reasoning | Fixed behavior trees | LLM deliberation + reflex fallback |
| Narrative | Authored quest scripts | Emergent drama from agent interactions |
| **Agent Goals** | Static objectives | **Hidden agendas creating natural conflict** |
| **Drama Pacing** | Manual scripting | **Automatic tension monitoring & catalyst injection** |
| **Action Validity** | Fire-and-forget | **Pre-action validation with graceful fail states** |

---

## 2. MVP Scope & Goals

### 2.1 In-Scope (Must Have)

1. **Agent Count**: 15-20 concurrent agents in a single zone
2. **Memory System**: 
   - Episodic memory buffer (last 100 events per agent)
   - Semantic knowledge graph (relationships, facts, locations)
   - Memory retrieval for LLM context injection
   - **Context Token Budgets** to prevent dirty context (§4.6)
   - **Sleep Cycle Consolidation** for memory pruning (§4.7)
3. **Social Dynamics**:
   - Gossip propagation (3-hop maximum)
   - Relationship tracking (trust, affinity scores)
   - Belief formation and mutation
4. **Dual-Mode Cognition**:
   - System 1: Rule-based reflexes (<50ms response)
   - System 2: LLM deliberation (2-5s async)
   - Graceful degradation when LLM unavailable
   - **Latency Masking** with contextual busy animations (§6.6.1)
   - **Pre-Action Validation Gate** to prevent stale actions (§8.3.6)
5. **Narrative Quality**:
   - **Secret Objectives** for Focus agents to create dramatic tension (§6.7.4)
   - **Tension Monitor & Aggressive Director** to prevent boring simulations (§7.5)
6. **Demo Runtime**: 10-15 minute self-running simulation
7. **Visualization**: Debug UI showing agent thoughts, memories, relationships
   - **Thought Bubble Inspector** for real-time CoT visualization (§7.4.1)

### 2.2 Out-of-Scope (Post-MVP)

- Multi-zone sharding and cross-zone handoff
- Full game engine integration (Unreal/Unity SDK)
- Production-grade auth, rate limiting, security hardening
- Horizontal scaling beyond single zone
- ~~Memory consolidation/sleep cycles~~ → **NOW IN SCOPE** (See §4.7)
- ~~Advanced Drama Director with full tension vector~~ → **NOW IN SCOPE** (See §7.5)

### 2.3 MVP Success Metrics

| Metric | Target |
|--------|--------|
| Agents Simulated | 15-20 concurrent |
| Reflex Latency | <50ms P99 |
| Deliberation Latency | <5s P95 |
| Memory Retrieval | <100ms P99 |
| Gossip Propagation | Observable within 60s |
| Demo Runtime | 10-15 minutes without crashes |
| Emergent Events | At least 3 unscripted narrative beats |
| **World Tension** | Maintained 0.3-0.8 range for >80% of demo |
| **Validation Gate** | <5% action rejection rate |
| **Context Budget Compliance** | 100% adherence to token budgets |
| **Secret Objective Influence** | At least 2 decisions per Focus agent influenced by hidden agenda |
| **Memory Consolidation** | >90% memory reduction during sleep cycles |

---

## 3. Core Systems Architecture

### 3.1 MVP Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TSUKUYOMI (THE MOON READER) MVP                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │   SIMULATION    │    │    COGNITION    │    │   SOCIAL       │  │
│  │     LOOP        │◄──►│     ENGINE      │◄──►│   ENGINE       │  │
│  │                 │    │                 │    │                │  │
│  │  • Tick Clock   │    │  • System 1     │    │  • Gossip      │  │
│  │  • Event Queue  │    │  • System 2     │    │  • Relations   │  │
│  │  • State Sync   │    │  • Memory Query │    │  • Beliefs     │  │
│  └────────┬────────┘    └────────┬────────┘    └───────┬────────┘  │
│           │                      │                     │           │
│           └──────────────────────┼─────────────────────┘           │
│                                  │                                 │
│                    ┌─────────────▼─────────────┐                   │
│                    │       DATA LAYER          │                   │
│                    │                           │                   │
│                    │  ┌─────────┐ ┌─────────┐  │                   │
│                    │  │ Postgres│ │  Neo4j  │  │                   │
│                    │  │ (State) │ │ (Graph) │  │                   │
│                    │  └─────────┘ └─────────┘  │                   │
│                    │  ┌─────────┐ ┌─────────┐  │                   │
│                    │  │  Redis  │ │ Vector  │  │                   │
│                    │  │ (Events)│ │   DB    │  │                   │
│                    │  └─────────┘ └─────────┘  │                   │
│                    └───────────────────────────┘                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      DEBUG UI                               │   │
│  │  • Agent Inspector  • Memory Viewer  • Relationship Graph   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Simulation Loop

The core tick loop runs at **20 ticks/second** (50ms per tick):

```python
# Pseudocode for main simulation loop
class SimulationLoop:
    TICK_RATE = 20  # ticks per second
    
    def run(self):
        while self.running:
            tick_start = time.now()
            
            # Phase 1: Process incoming events
            self.process_event_queue()
            
            # Phase 2: Execute reflexes (System 1) - BLOCKING
            for agent in self.active_agents:
                agent.evaluate_reflexes(self.world_state)
            
            # Phase 3: Check deliberation results (System 2) - NON-BLOCKING
            self.collect_deliberation_results()
            
            # Phase 4: Process social dynamics
            self.gossip_engine.propagate_tick()
            self.relationship_engine.decay_tick()
            
            # Phase 5: Commit state changes
            self.commit_state_delta()
            
            # Phase 6: Broadcast to observers
            self.broadcast_tick_delta()
            
            # Maintain tick rate
            self.sleep_until_next_tick(tick_start)
```

### 3.3 Component Responsibilities

| Component | Responsibility | Tech Stack |
|-----------|---------------|------------|
| **Simulation Loop** | Tick management, event ordering, state commits | Python/asyncio |
| **Cognition Engine** | Reflex evaluation, LLM orchestration, memory queries | Python + LangChain |
| **Social Engine** | Gossip propagation, relationship updates, belief management | Python + Neo4j |
| **State Store** | Authoritative agent state, positions, stats | PostgreSQL |
| **Knowledge Graph** | Semantic relationships, beliefs, world facts | Neo4j |
| **Event Ledger** | Event ordering, replay capability | Redis Streams |
| **Vector Store** | Episodic memory embeddings, similarity search | Chroma/Pinecone |

---

## 4. Memory Architecture

### 4.1 Dual Memory System

Agents maintain two complementary memory systems:

```
┌───────────────────────────────────────────────────────────────────┐
│                    AGENT MEMORY ARCHITECTURE                      │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  EPISODIC MEMORY (Vector DB)          SEMANTIC MEMORY (Neo4j)    │
│  ═══════════════════════════          ═══════════════════════    │
│                                                                   │
│  ┌─────────────────────────┐          ┌─────────────────────┐    │
│  │ "I saw Marcus arguing   │          │    (Agent:Elena)    │    │
│  │  with the merchant at   │          │         │           │    │
│  │  tick 4532"             │          │    KNOWS_ABOUT      │    │
│  │                         │          │         │           │    │
│  │  Embedding: [0.23, ...] │          │         ▼           │    │
│  │  Importance: 0.7        │          │  (Event:Argument)   │    │
│  │  Timestamp: 4532        │          │         │           │    │
│  │  Location: Market       │          │   INVOLVES          │    │
│  │  Participants: [Marcus, │          │         │           │    │
│  │                 Vendor] │          │         ▼           │    │
│  └─────────────────────────┘          │  (Agent:Marcus)     │    │
│                                        │         │           │    │
│  ┌─────────────────────────┐          │   HAS_TRAIT         │    │
│  │ "Elena shared a secret  │          │         │           │    │
│  │  with me about the      │          │         ▼           │    │
│  │  stolen artifact"       │          │  (Trait:Suspicious) │    │
│  │                         │          └─────────────────────┘    │
│  │  Embedding: [0.87, ...] │                                     │
│  │  Importance: 0.95       │          Relationships:             │
│  │  Timestamp: 5201        │          • TRUSTS (weight: 0.8)     │
│  │  Emotional: Excited     │          • FEARS (weight: 0.3)      │
│  └─────────────────────────┘          • KNOWS_LOCATION_OF        │
│                                        • BELIEVES_ABOUT           │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 Episodic Memory Schema

Each memory entry follows the **5W Framework** (Who, What, When, Where, Why):

```python
@dataclass
class EpisodicMemory:
    memory_id: UUID
    agent_id: UUID
    
    # The 5W Framework
    who: List[UUID]           # Participants involved
    what: str                 # Natural language description
    when: int                 # Tick timestamp
    where: str                # Location identifier
    why: Optional[str]        # Inferred causation (if known)
    
    # Retrieval metadata
    embedding: List[float]    # 1536-dim embedding vector
    importance: float         # 0.0-1.0, affects retention
    emotional_valence: float  # -1.0 to 1.0
    access_count: int         # How often retrieved
    last_accessed: int        # Tick of last retrieval
    
    # Decay mechanics
    decay_rate: float         # How fast importance degrades
    consolidated: bool        # Promoted to long-term storage
```

### 4.3 Memory Retrieval Algorithm

When an agent needs context for deliberation:

```python
def retrieve_relevant_memories(
    agent_id: UUID,
    query: str,
    context: WorldContext,
    max_memories: int = 5
) -> List[EpisodicMemory]:
    """
    Retrieval scoring combines three factors:
    - Recency: How recent was the memory?
    - Relevance: Semantic similarity to current situation
    - Importance: How significant was the original event?
    """
    
    query_embedding = embed(query)
    candidate_memories = vector_db.search(
        agent_id=agent_id,
        embedding=query_embedding,
        limit=50  # Over-fetch for scoring
    )
    
    current_tick = context.current_tick
    
    scored_memories = []
    for memory in candidate_memories:
        # Recency score (exponential decay)
        tick_age = current_tick - memory.when
        recency = math.exp(-tick_age / RECENCY_DECAY_CONSTANT)
        
        # Relevance score (cosine similarity from vector search)
        relevance = memory.similarity_score
        
        # Importance score (with decay)
        decayed_importance = memory.importance * math.exp(
            -tick_age * memory.decay_rate
        )
        
        # Combined score
        final_score = (
            WEIGHT_RECENCY * recency +
            WEIGHT_RELEVANCE * relevance +
            WEIGHT_IMPORTANCE * decayed_importance
        )
        
        scored_memories.append((memory, final_score))
    
    # Sort and return top k
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored_memories[:max_memories]]

# Scoring weights (tunable)
WEIGHT_RECENCY = 0.25
WEIGHT_RELEVANCE = 0.50
WEIGHT_IMPORTANCE = 0.25
RECENCY_DECAY_CONSTANT = 5000  # ticks
```

### 4.4 Semantic Memory (Knowledge Graph)

The Neo4j graph stores structured knowledge:

```cypher
// Core node types
(:Agent {id, name, role, personality_traits: [], current_location})
(:Location {id, name, type, description})
(:Fact {id, content, source_agent, confidence, timestamp})
(:Event {id, type, description, tick, resolved: bool})
(:Item {id, name, type, current_holder})
(:Rumor {id, content, origin_agent, hash, relevance})

// Core relationship types
(:Agent)-[:KNOWS_ABOUT {since_tick, confidence}]->(:Fact)
(:Agent)-[:TRUSTS {weight: 0.0-1.0, last_updated}]->(:Agent)
(:Agent)-[:FEARS {weight: 0.0-1.0}]->(:Agent)
(:Agent)-[:LOCATED_AT]->(:Location)
(:Agent)-[:WITNESSED {tick}]->(:Event)
(:Agent)-[:BELIEVES {confidence}]->(:Rumor)
(:Agent)-[:POSSESSES]->(:Item)
(:Rumor)-[:ABOUT]->(:Agent|:Event|:Item)
```

### 4.5 Memory Capacity & Decay

```python
# MVP Memory Constraints
MEMORY_CONFIG = {
    "episodic": {
        "buffer_size": 100,        # Events per agent
        "importance_threshold": 0.1,  # Below this, eligible for pruning
        "decay_rate_base": 0.001,  # Per-tick decay
        "consolidation_threshold": 0.8,  # High importance → long-term
    },
    "semantic": {
        "max_relationships_per_agent": 50,
        "max_beliefs_per_agent": 100,
        "belief_decay_rate": 0.0005,
        "trust_decay_rate": 0.0001,
    },
    "rumor": {
        "max_active_per_agent": 20,
        "propagation_cooldown_ticks": 100,
        "relevance_decay_rate": 0.01,
        "min_relevance_threshold": 0.1,
    }
}
```

### 4.6 Context Window Token Budgets (HIGH PRIORITY)

To prevent "dirty context" from overwhelming the LLM's reasoning capacity, strict token budgets are enforced per memory type when building the deliberation context. This ensures a balanced, relevant context window.

```
┌─────────────────────────────────────────────────────────────────────┐
│                CONTEXT WINDOW TOKEN BUDGET ALLOCATION                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Total Context Budget: 800 tokens (configurable per LOD tier)       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ RECENT EVENTS                                    200 tokens │    │
│  │ (Last 5-10 episodic memories, recency-weighted)             │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ CORE MEMORIES                                    150 tokens │    │
│  │ (High-importance consolidated memories, identity-defining)  │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ RELATIONSHIPS                                    150 tokens │    │
│  │ (Trust/affinity for relevant agents in scene)               │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ CURRENT SITUATION                                100 tokens │    │
│  │ (Immediate environment, present agents, active threats)     │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ PHYSICAL STATE                                    50 tokens │    │
│  │ (Health, inventory, location, current action)               │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ ACTIVE GOALS                                      75 tokens │    │
│  │ (Current objectives, priorities)                            │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ PERSONALITY                                       75 tokens │    │
│  │ (Traits, behavioral tendencies, hidden agenda)              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Overflow Handling:                                                 │
│  • Truncate lowest-importance items first                           │
│  • Never truncate personality or physical state                     │
│  • Log warnings when truncation exceeds 20%                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class ContextTokenBudget:
    """
    Token budget allocation for context window construction.
    Prevents context pollution and ensures balanced deliberation input.
    """
    
    # Per-category token limits (tunable)
    recent_events: int = 200        # Episodic memories from recent ticks
    core_memories: int = 150        # High-importance consolidated memories
    relationships: int = 150        # Trust/affinity data for relevant agents
    current_situation: int = 100    # Immediate environment and stimulus
    physical_state: int = 50        # Health, inventory, location
    active_goals: int = 75          # Current objectives
    personality: int = 75           # Traits and hidden agenda
    
    @property
    def total_budget(self) -> int:
        return (
            self.recent_events + 
            self.core_memories + 
            self.relationships +
            self.current_situation + 
            self.physical_state + 
            self.active_goals +
            self.personality
        )
    
    def get_budget_for_category(self, category: str) -> int:
        return getattr(self, category, 0)


# LOD-specific token budgets
CONTEXT_BUDGETS_BY_LOD = {
    "focus": ContextTokenBudget(
        recent_events=200,
        core_memories=150,
        relationships=150,
        current_situation=100,
        physical_state=50,
        active_goals=75,
        personality=75
    ),
    "ambient": ContextTokenBudget(
        recent_events=100,
        core_memories=75,
        relationships=75,
        current_situation=75,
        physical_state=30,
        active_goals=50,
        personality=50
    ),
    "simulation": ContextTokenBudget(
        # Minimal context for rare emergency deliberations
        recent_events=50,
        core_memories=25,
        relationships=25,
        current_situation=50,
        physical_state=20,
        active_goals=20,
        personality=30
    )
}


class ContextWindowBuilder:
    """
    Builds token-budget-aware context for LLM deliberation.
    Ensures no single memory type dominates the context.
    """
    
    def __init__(self, tokenizer, budget: ContextTokenBudget):
        self.tokenizer = tokenizer
        self.budget = budget
        self.truncation_warnings = 0
    
    async def build_context(
        self,
        agent: Agent,
        stimulus: Stimulus,
        memory_store: MemoryStore,
        relationship_store: RelationshipStore
    ) -> DeliberationContext:
        """
        Build a balanced context window respecting token budgets.
        """
        context_parts = {}
        
        # 1. Physical State (never truncated)
        context_parts["physical_state"] = self._build_physical_state(
            agent, self.budget.physical_state
        )
        
        # 2. Personality (never truncated)
        context_parts["personality"] = self._build_personality(
            agent, self.budget.personality
        )
        
        # 3. Current Situation
        context_parts["current_situation"] = self._build_situation(
            stimulus, self.budget.current_situation
        )
        
        # 4. Recent Events (episodic memories)
        recent_memories = await memory_store.get_recent_memories(
            agent.id, 
            limit=15  # Over-fetch, then trim to budget
        )
        context_parts["recent_events"] = self._fit_to_budget(
            self._format_memories(recent_memories),
            self.budget.recent_events,
            "recent_events"
        )
        
        # 5. Core Memories
        core_memories = await memory_store.get_core_memories(
            agent.id,
            limit=10
        )
        context_parts["core_memories"] = self._fit_to_budget(
            self._format_memories(core_memories),
            self.budget.core_memories,
            "core_memories"
        )
        
        # 6. Relationships
        relevant_agents = self._extract_relevant_agents(stimulus, agent)
        relationships = await relationship_store.get_relationships(
            agent.id,
            target_ids=relevant_agents
        )
        context_parts["relationships"] = self._fit_to_budget(
            self._format_relationships(relationships),
            self.budget.relationships,
            "relationships"
        )
        
        # 7. Active Goals
        context_parts["active_goals"] = self._fit_to_budget(
            self._format_goals(agent.active_goals),
            self.budget.active_goals,
            "active_goals"
        )
        
        # Validate total doesn't exceed budget
        total_tokens = sum(
            self._count_tokens(part) for part in context_parts.values()
        )
        
        if total_tokens > self.budget.total_budget * 1.1:  # 10% tolerance
            logger.warning(
                f"Context exceeded budget: {total_tokens} > {self.budget.total_budget}"
            )
        
        return DeliberationContext(
            parts=context_parts,
            total_tokens=total_tokens,
            budget=self.budget,
            truncation_occurred=self.truncation_warnings > 0
        )
    
    def _fit_to_budget(
        self, 
        content: str, 
        budget: int, 
        category: str
    ) -> str:
        """
        Truncate content to fit within token budget.
        Logs warning if significant truncation occurs.
        """
        tokens = self._count_tokens(content)
        
        if tokens <= budget:
            return content
        
        # Calculate truncation ratio
        truncation_ratio = 1 - (budget / tokens)
        
        if truncation_ratio > 0.2:
            self.truncation_warnings += 1
            logger.warning(
                f"Significant truncation for {category}: "
                f"{truncation_ratio:.1%} of content removed"
            )
        
        # Truncate by importance (last items are least important)
        lines = content.split('\n')
        result_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self._count_tokens(line)
            if current_tokens + line_tokens <= budget:
                result_lines.append(line)
                current_tokens += line_tokens
            else:
                break
        
        return '\n'.join(result_lines)
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def _build_physical_state(self, agent: Agent, budget: int) -> str:
        """Build physical state context."""
        state = f"""Location: {agent.current_location}
Position: ({agent.position[0]:.1f}, {agent.position[1]:.1f})
State: {agent.state.value}
Health: {agent.hp}/{agent.max_hp}"""
        
        if agent.inventory:
            state += f"\nInventory: {', '.join(agent.inventory[:3])}"
        
        return state[:budget * 4]  # Rough char-to-token ratio
    
    def _build_personality(self, agent: Agent, budget: int) -> str:
        """Build personality context including hidden agenda."""
        traits = agent.traits
        personality = f"""Traits: openness={traits.openness:.1f}, conscientiousness={traits.conscientiousness:.1f}, extraversion={traits.extraversion:.1f}
Tendencies: bravery={traits.bravery:.1f}, honesty={traits.honesty:.1f}, loyalty={traits.loyalty:.1f}"""
        
        # Include hidden agenda if agent has one (for Focus tier)
        if hasattr(agent, 'hidden_agenda') and agent.hidden_agenda:
            personality += f"\nHidden Agenda: {agent.hidden_agenda}"
        
        return personality[:budget * 4]
    
    def _build_situation(self, stimulus: Stimulus, budget: int) -> str:
        """Build current situation context."""
        return stimulus.description[:budget * 4]
    
    def _format_memories(self, memories: List[EpisodicMemory]) -> str:
        """Format memories for context, sorted by importance."""
        sorted_memories = sorted(memories, key=lambda m: m.importance, reverse=True)
        return '\n'.join([
            f"- {m.what} (importance: {m.importance:.1f})"
            for m in sorted_memories
        ])
    
    def _format_relationships(self, relationships: List[Relationship]) -> str:
        """Format relationships for context."""
        return '\n'.join([
            f"- {r.target_name}: trust={r.trust:.1f}, affinity={r.affinity:.1f}"
            for r in relationships
        ])
    
    def _format_goals(self, goals: List[Goal]) -> str:
        """Format active goals for context."""
        sorted_goals = sorted(goals, key=lambda g: g.priority, reverse=True)
        return '\n'.join([
            f"- {g.description} (priority: {g.priority})"
            for g in sorted_goals
        ])
    
    def _extract_relevant_agents(
        self, 
        stimulus: Stimulus, 
        agent: Agent
    ) -> List[UUID]:
        """Extract agent IDs relevant to the current stimulus."""
        relevant = set(stimulus.involved_entities)
        
        # Add agents in current location
        # Add agents mentioned in stimulus description
        
        return list(relevant)[:10]  # Cap at 10 to control context size


@dataclass
class DeliberationContext:
    """Complete context for LLM deliberation."""
    parts: Dict[str, str]
    total_tokens: int
    budget: ContextTokenBudget
    truncation_occurred: bool
    
    def to_prompt_sections(self) -> str:
        """Convert to formatted prompt sections."""
        sections = []
        
        section_order = [
            ("personality", "## Your Personality"),
            ("physical_state", "## Your Current State"),
            ("current_situation", "## Current Situation"),
            ("recent_events", "## Recent Memories"),
            ("core_memories", "## Important Memories"),
            ("relationships", "## Relevant Relationships"),
            ("active_goals", "## Your Goals"),
        ]
        
        for key, header in section_order:
            if key in self.parts and self.parts[key]:
                sections.append(f"{header}\n{self.parts[key]}")
        
        return '\n\n'.join(sections)
```

### 4.7 Sleep Cycle Consolidation (Memory Pruning)

To prevent "graph explosion" where memory stores grow unbounded, a Nightly Pruning Process runs during simulated night cycles to consolidate and clean memory data.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   SLEEP CYCLE MEMORY CONSOLIDATION                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  During simulated "night" (or every N ticks in demo mode):          │
│                                                                     │
│  PHASE 1: SUMMARIZATION                                             │
│  ═══════════════════════                                            │
│  • Identify clusters of related trivial interactions                │
│  • Summarize into single "meta-memory"                              │
│  • Example: 15 "greeted villager" events → "Routine morning greetings"│
│                                                                     │
│  PHASE 2: IMPORTANCE DECAY                                          │
│  ═════════════════════════                                          │
│  • Apply decay to all memory importance scores                      │
│  • High-importance memories decay slower                            │
│  • Emotional memories have decay resistance                         │
│                                                                     │
│  PHASE 3: PRUNING                                                   │
│  ═══════════════                                                    │
│  • Delete memories below importance threshold                       │
│  • Delete memories older than retention limit                       │
│  • Always preserve "core memories" (consolidation_threshold > 0.8)  │
│                                                                     │
│  PHASE 4: GRAPH CLEANUP                                             │
│  ══════════════════════                                             │
│  • Remove orphaned nodes in semantic graph                          │
│  • Consolidate redundant relationship edges                         │
│  • Archive old gossip that has fully propagated                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class SleepCycleConfig:
    """Configuration for memory consolidation during sleep cycles."""
    
    # Trigger conditions
    trigger_mode: str = "time_of_day"     # "time_of_day" or "tick_interval"
    trigger_time: str = "night"           # For time_of_day mode
    tick_interval: int = 18000            # For tick_interval mode (15 min at 20 TPS)
    
    # Summarization
    summarization_cluster_threshold: int = 5   # Min events to summarize
    summarization_similarity_threshold: float = 0.85  # Semantic similarity
    trivial_event_types: List[str] = field(default_factory=lambda: [
        "GREET", "IDLE", "WALK_ROUTINE", "EAT", "DRINK", "SLEEP"
    ])
    
    # Decay rates
    base_decay_multiplier: float = 0.1        # Applied during consolidation
    emotional_decay_resistance: float = 0.5   # Emotional memories decay slower
    core_memory_decay_resistance: float = 0.8 # Core memories almost never decay
    
    # Pruning thresholds
    min_importance_threshold: float = 0.05    # Below this = delete
    max_age_ticks: int = 100000               # ~83 minutes at 20 TPS
    max_memories_per_agent: int = 150         # Hard cap
    
    # Graph cleanup
    orphan_node_threshold_ticks: int = 10000  # Delete unreferenced after this
    gossip_archive_threshold: float = 0.05    # Archive gossip below this relevance


class SleepCycleConsolidator:
    """
    Manages memory consolidation during simulated sleep cycles.
    Prevents unbounded growth of memory stores.
    """
    
    def __init__(
        self,
        config: SleepCycleConfig,
        episodic_store: EpisodicMemoryStore,
        semantic_store: SemanticMemoryStore,
        embedding_model: EmbeddingModel
    ):
        self.config = config
        self.episodic = episodic_store
        self.semantic = semantic_store
        self.embeddings = embedding_model
        
        # Metrics
        self.memories_summarized = 0
        self.memories_pruned = 0
        self.nodes_cleaned = 0
        self.last_consolidation_tick = 0
    
    async def run_consolidation(
        self,
        agents: List[Agent],
        current_tick: int
    ) -> ConsolidationReport:
        """
        Run full consolidation cycle for all agents.
        """
        report = ConsolidationReport(tick=current_tick)
        
        logger.info(f"Starting sleep cycle consolidation at tick {current_tick}")
        
        for agent in agents:
            agent_report = await self._consolidate_agent(agent, current_tick)
            report.agent_reports[agent.id] = agent_report
        
        # Global cleanup
        graph_report = await self._cleanup_semantic_graph(current_tick)
        report.graph_cleanup = graph_report
        
        self.last_consolidation_tick = current_tick
        
        logger.info(
            f"Consolidation complete: "
            f"summarized={report.total_summarized}, "
            f"pruned={report.total_pruned}, "
            f"nodes_cleaned={report.graph_cleanup.nodes_removed}"
        )
        
        return report
    
    async def _consolidate_agent(
        self,
        agent: Agent,
        current_tick: int
    ) -> AgentConsolidationReport:
        """Consolidate memories for a single agent."""
        report = AgentConsolidationReport(agent_id=agent.id)
        
        # Phase 1: Summarization
        summarized = await self._summarize_trivial_memories(agent, current_tick)
        report.memories_summarized = summarized
        
        # Phase 2: Decay
        decayed = await self._apply_importance_decay(agent, current_tick)
        report.decay_applied = decayed
        
        # Phase 3: Pruning
        pruned = await self._prune_memories(agent, current_tick)
        report.memories_pruned = pruned
        
        return report
    
    async def _summarize_trivial_memories(
        self,
        agent: Agent,
        current_tick: int
    ) -> int:
        """
        Cluster and summarize trivial, repetitive memories.
        """
        summarized_count = 0
        
        # Get recent trivial memories
        trivial_memories = await self.episodic.get_memories_by_type(
            agent.id,
            types=self.config.trivial_event_types,
            since_tick=self.last_consolidation_tick
        )
        
        if len(trivial_memories) < self.config.summarization_cluster_threshold:
            return 0
        
        # Cluster by semantic similarity
        clusters = await self._cluster_memories(trivial_memories)
        
        for cluster in clusters:
            if len(cluster) >= self.config.summarization_cluster_threshold:
                # Create summary memory
                summary = await self._create_summary_memory(agent, cluster, current_tick)
                
                # Store summary
                await self.episodic.store_memory(summary)
                
                # Delete original memories
                for memory in cluster:
                    await self.episodic.delete_memory(memory.memory_id)
                
                summarized_count += len(cluster)
        
        return summarized_count
    
    async def _cluster_memories(
        self,
        memories: List[EpisodicMemory]
    ) -> List[List[EpisodicMemory]]:
        """Cluster memories by semantic similarity."""
        if not memories:
            return []
        
        # Get embeddings
        embeddings = {
            m.memory_id: m.embedding for m in memories
        }
        
        # Simple clustering based on similarity threshold
        clusters = []
        used = set()
        
        for memory in memories:
            if memory.memory_id in used:
                continue
            
            cluster = [memory]
            used.add(memory.memory_id)
            
            for other in memories:
                if other.memory_id in used:
                    continue
                
                similarity = self._cosine_similarity(
                    embeddings[memory.memory_id],
                    embeddings[other.memory_id]
                )
                
                if similarity >= self.config.summarization_similarity_threshold:
                    cluster.append(other)
                    used.add(other.memory_id)
            
            clusters.append(cluster)
        
        return clusters
    
    async def _create_summary_memory(
        self,
        agent: Agent,
        cluster: List[EpisodicMemory],
        current_tick: int
    ) -> EpisodicMemory:
        """Create a summary memory from a cluster of trivial memories."""
        # Extract common elements
        event_type = cluster[0].event_type if cluster else "ROUTINE"
        locations = list(set(m.where for m in cluster))
        participants = list(set(p for m in cluster for p in m.who))
        
        # Compute aggregate importance
        max_importance = max(m.importance for m in cluster)
        avg_importance = sum(m.importance for m in cluster) / len(cluster)
        summary_importance = (max_importance + avg_importance) / 2
        
        # Generate summary text
        summary_text = f"Routine {event_type.lower()} activities ({len(cluster)} occurrences)"
        if locations:
            summary_text += f" at {', '.join(locations[:2])}"
        
        # Create summary memory
        return EpisodicMemory(
            memory_id=uuid4(),
            agent_id=agent.id,
            who=participants[:5],  # Cap participants
            what=summary_text,
            when=current_tick,
            where=locations[0] if locations else "various",
            embedding=await self.embeddings.embed(summary_text),
            importance=summary_importance * 0.8,  # Slightly reduce importance
            emotional_valence=0.0,
            access_count=0,
            last_accessed=current_tick,
            decay_rate=cluster[0].decay_rate * 0.5,  # Slower decay for summaries
            consolidated=True,
            is_summary=True,
            summarizes_count=len(cluster)
        )
    
    async def _apply_importance_decay(
        self,
        agent: Agent,
        current_tick: int
    ) -> int:
        """Apply importance decay to all memories."""
        memories = await self.episodic.get_all_memories(agent.id)
        decayed = 0
        
        for memory in memories:
            # Calculate decay
            decay = self.config.base_decay_multiplier
            
            # Apply resistance factors
            if memory.consolidated:
                decay *= (1 - self.config.core_memory_decay_resistance)
            if abs(memory.emotional_valence) > 0.5:
                decay *= (1 - self.config.emotional_decay_resistance * abs(memory.emotional_valence))
            
            # Apply decay
            new_importance = memory.importance * (1 - decay)
            
            if new_importance != memory.importance:
                await self.episodic.update_importance(memory.memory_id, new_importance)
                decayed += 1
        
        return decayed
    
    async def _prune_memories(
        self,
        agent: Agent,
        current_tick: int
    ) -> int:
        """Prune low-importance and old memories."""
        memories = await self.episodic.get_all_memories(agent.id)
        pruned = 0
        
        # Sort by importance (lowest first)
        memories.sort(key=lambda m: m.importance)
        
        for memory in memories:
            should_prune = False
            
            # Check importance threshold
            if memory.importance < self.config.min_importance_threshold:
                should_prune = True
            
            # Check age
            age = current_tick - memory.when
            if age > self.config.max_age_ticks and not memory.consolidated:
                should_prune = True
            
            # Never prune consolidated core memories
            if memory.consolidated and memory.importance > 0.5:
                should_prune = False
            
            if should_prune:
                await self.episodic.delete_memory(memory.memory_id)
                pruned += 1
        
        # Enforce hard cap
        remaining = await self.episodic.get_memory_count(agent.id)
        if remaining > self.config.max_memories_per_agent:
            excess = remaining - self.config.max_memories_per_agent
            oldest = await self.episodic.get_oldest_memories(agent.id, limit=excess)
            for memory in oldest:
                if not memory.consolidated:
                    await self.episodic.delete_memory(memory.memory_id)
                    pruned += 1
        
        return pruned
    
    async def _cleanup_semantic_graph(
        self,
        current_tick: int
    ) -> GraphCleanupReport:
        """Clean up orphaned nodes and stale data in semantic graph."""
        report = GraphCleanupReport()
        
        # Remove orphaned nodes
        orphans = await self.semantic.find_orphaned_nodes(
            threshold_ticks=self.config.orphan_node_threshold_ticks,
            current_tick=current_tick
        )
        
        for node in orphans:
            await self.semantic.delete_node(node.id)
            report.nodes_removed += 1
        
        # Archive old gossip
        old_gossip = await self.semantic.find_stale_gossip(
            relevance_threshold=self.config.gossip_archive_threshold
        )
        
        for gossip in old_gossip:
            await self.semantic.archive_gossip(gossip.id)
            report.gossip_archived += 1
        
        # Consolidate redundant edges
        redundant = await self.semantic.find_redundant_relationships()
        for edge_set in redundant:
            await self.semantic.merge_relationships(edge_set)
            report.edges_consolidated += 1
        
        return report
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(y ** 2 for y in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


@dataclass
class ConsolidationReport:
    """Report from a consolidation cycle."""
    tick: int
    agent_reports: Dict[UUID, 'AgentConsolidationReport'] = field(default_factory=dict)
    graph_cleanup: Optional['GraphCleanupReport'] = None
    
    @property
    def total_summarized(self) -> int:
        return sum(r.memories_summarized for r in self.agent_reports.values())
    
    @property
    def total_pruned(self) -> int:
        return sum(r.memories_pruned for r in self.agent_reports.values())


@dataclass
class AgentConsolidationReport:
    """Consolidation report for a single agent."""
    agent_id: UUID
    memories_summarized: int = 0
    decay_applied: int = 0
    memories_pruned: int = 0


@dataclass
class GraphCleanupReport:
    """Report from semantic graph cleanup."""
    nodes_removed: int = 0
    gossip_archived: int = 0
    edges_consolidated: int = 0
```

---

## 5. Social Dynamics Engine

### 5.1 Gossip Propagation System

Gossip spreads information (and misinformation) through the social network:

```
┌─────────────────────────────────────────────────────────────────┐
│                   GOSSIP PROPAGATION MODEL                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Original Event                                                │
│   "Marcus stole from the merchant"                              │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────┐                                                   │
│   │  Elena  │ ◄── Witnessed event (Source: 100% confidence)     │
│   └────┬────┘                                                   │
│        │ Shares gossip (Trust weight: 0.7)                      │
│        ▼                                                        │
│   ┌─────────┐                                                   │
│   │  Thomas │ ◄── Heard from Elena (Confidence: 70%)            │
│   └────┬────┘                                                   │
│        │ Shares gossip (Trust weight: 0.5)                      │
│        │ MUTATION: "Marcus might have stolen..."                │
│        ▼                                                        │
│   ┌─────────┐                                                   │
│   │  Sarah  │ ◄── Heard from Thomas (Confidence: 35%)           │
│   └────┬────┘                                                   │
│        │ Shares gossip (Trust weight: 0.8)                      │
│        │ MUTATION: "Someone said Marcus was near the market..." │
│        ▼                                                        │
│   ┌─────────┐                                                   │
│   │  Viktor │ ◄── Heard from Sarah (Confidence: 28%)            │
│   └─────────┘     [Propagation cap: 3 hops reached]             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Rumor Data Structure

```python
@dataclass
class Rumor:
    rumor_id: UUID
    content_hash: str          # SHA256(subject+verb+object) for dedup
    
    # Content
    subject: UUID              # Who/what the rumor is about
    predicate: str             # The claim being made
    original_content: str      # Natural language version
    mutated_content: str       # May differ as it spreads
    
    # Propagation tracking
    source_agent: UUID         # Who created/spread this version
    hop_count: int             # How many times propagated
    max_hops: int = 3          # Propagation limit
    
    # Confidence & Decay
    confidence: float          # Belief strength (0-1)
    relevance: float           # Current relevance score
    created_tick: int
    last_propagated_tick: int
    
    # Mutation tracking
    mutation_probability: float = 0.15  # Chance of content shift
```

### 5.3 Relationship Model

```python
@dataclass
class Relationship:
    source_agent: UUID
    target_agent: UUID
    
    # Core dimensions
    trust: float       # -1.0 to 1.0 (distrust to trust)
    affinity: float    # -1.0 to 1.0 (dislike to like)
    familiarity: float # 0.0 to 1.0 (stranger to intimate)
    
    # Interaction history
    interaction_count: int
    last_interaction_tick: int
    
    # Sentiment tracking
    recent_sentiment: List[float]  # Rolling window of interaction sentiments
    
    def get_gossip_weight(self) -> float:
        """How much this relationship affects gossip confidence."""
        return max(0, self.trust) * self.familiarity
    
    def should_share_gossip(self, rumor: Rumor) -> bool:
        """Decide whether to share gossip with this person."""
        # Higher trust + affinity = more likely to share
        share_threshold = 0.3
        share_score = (self.trust + self.affinity) / 2
        return share_score > share_threshold and rumor.relevance > 0.2
```

### 5.4 Belief Formation & Revision

```python
class BeliefEngine:
    """
    Manages how agents form and update beliefs based on
    direct experience, gossip, and reasoning.
    """
    
    def process_new_information(
        self,
        agent: Agent,
        information: Information,
        source: InformationSource
    ) -> BeliefUpdate:
        
        # Calculate base confidence from source
        if source.type == "DIRECT_WITNESS":
            base_confidence = 0.95
        elif source.type == "TRUSTED_AGENT":
            relationship = self.get_relationship(agent.id, source.agent_id)
            base_confidence = 0.5 + (relationship.trust * 0.4)
        elif source.type == "GOSSIP":
            base_confidence = source.rumor.confidence * 0.7
        else:
            base_confidence = 0.3
        
        # Check for contradictions with existing beliefs
        existing_belief = self.find_related_belief(agent.id, information)
        
        if existing_belief:
            if self.contradicts(existing_belief, information):
                # Belief revision: weighted by confidence
                return self.revise_belief(
                    agent, existing_belief, information, base_confidence
                )
            else:
                # Reinforcement: strengthen existing belief
                return self.reinforce_belief(
                    agent, existing_belief, base_confidence
                )
        else:
            # New belief formation
            return self.create_belief(agent, information, base_confidence)
```

### 5.5 Social Interaction Triggers

Agents initiate social interactions based on:

```python
class SocialTriggers:
    """Conditions that trigger social behaviors."""
    
    TRIGGER_CONDITIONS = {
        "share_gossip": {
            "conditions": [
                "has_recent_rumor",
                "nearby_trusted_agent",
                "not_in_danger",
                "rumor_relevance > 0.3"
            ],
            "cooldown_ticks": 200,
            "priority": "low"
        },
        "warn_friend": {
            "conditions": [
                "knows_danger",
                "friend_unaware",
                "friend_in_range"
            ],
            "cooldown_ticks": 50,
            "priority": "high"
        },
        "confront_suspect": {
            "conditions": [
                "believes_wrongdoing",
                "confidence > 0.6",
                "suspect_present",
                "agent_personality.confrontational > 0.5"
            ],
            "cooldown_ticks": 500,
            "priority": "medium"
        }
    }
```

---

## 6. Dual-Mode Cognition

### 6.1 System 1: Reflexes (Fast)

Reflexes are rule-based, deterministic responses that execute within a single tick:

```python
class ReflexLibrary:
    """
    Reflex rules evaluated every tick.
    Returns highest-priority matching action.
    """
    
    REFLEXES = [
        # Survival reflexes (highest priority)
        Reflex(
            name="flee_danger",
            priority=100,
            condition=lambda a, w: (
                a.hp < a.max_hp * 0.3 and 
                w.has_hostile_nearby(a, radius=10)
            ),
            action=Action("FLEE", target="nearest_safe_location")
        ),
        
        Reflex(
            name="dodge_attack",
            priority=95,
            condition=lambda a, w: w.incoming_attack_detected(a),
            action=Action("DODGE", direction="perpendicular_to_threat")
        ),
        
        # Social reflexes
        Reflex(
            name="greet_friend",
            priority=20,
            condition=lambda a, w: (
                w.friend_just_arrived(a) and
                not a.in_conversation and
                not a.busy
            ),
            action=Action("GREET", target="arriving_friend")
        ),
        
        Reflex(
            name="react_to_gossip",
            priority=30,
            condition=lambda a, w: (
                a.just_heard_gossip and
                a.gossip_involves_known_entity
            ),
            action=Action("EMOTE", type="SURPRISED")
        ),
        
        # Environmental reflexes
        Reflex(
            name="take_shelter",
            priority=40,
            condition=lambda a, w: w.weather == "STORM" and a.outdoors,
            action=Action("SEEK_SHELTER")
        ),
    ]
    
    def evaluate(self, agent: Agent, world: WorldState) -> Optional[Action]:
        """Evaluate all reflexes, return highest priority match."""
        matching = [
            r for r in self.REFLEXES 
            if r.condition(agent, world)
        ]
        if matching:
            return max(matching, key=lambda r: r.priority).action
        return None
```

### 6.2 System 2: Deliberation (Slow)

Deliberation uses LLM inference for complex decisions:

```python
class DeliberationEngine:
    """
    Async LLM-based reasoning for complex decisions.
    Operates across multiple ticks.
    """
    
    async def deliberate(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> Proposal:
        
        # Step 1: Gather context
        context = await self.build_context(agent, trigger)
        
        # Step 2: Retrieve relevant memories
        memories = await self.memory_retrieval(
            agent.id,
            query=trigger.situation_description,
            max_memories=5
        )
        
        # Step 3: Get relationship context
        relationships = await self.get_relevant_relationships(
            agent.id,
            entities=trigger.involved_entities
        )
        
        # Step 4: Construct prompt
        prompt = self.build_deliberation_prompt(
            agent=agent,
            situation=trigger,
            memories=memories,
            relationships=relationships,
            available_actions=self.get_allowed_actions(agent)
        )
        
        # Step 5: LLM inference
        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            schema=ActionProposalSchema  # Structured output
        )
        
        # Step 6: Create proposal (not yet committed)
        proposal = Proposal(
            agent_id=agent.id,
            action=response.action,
            reasoning=response.reasoning,
            confidence=response.confidence,
            emotional_state=response.emotional_state,
            created_tick=self.current_tick,
            expires_tick=self.current_tick + 100  # Stale after ~5 seconds
        )
        
        # Step 7: Log for deterministic replay
        await self.ledger.record_proposal(proposal)
        
        return proposal
```

### 6.3 Deliberation Prompt Template

```python
DELIBERATION_PROMPT = """
You are {agent_name}, a {agent_role} in the village of Millbrook.

## Your Personality
{personality_description}

## Current Situation
{situation_description}

## Your Recent Memories
{formatted_memories}

## Relevant Relationships
{formatted_relationships}

## Your Current Goals
{active_goals}

## Available Actions
{allowed_actions_list}

## Instructions
Based on your personality, memories, and relationships, decide what to do.
Consider:
1. How does this situation relate to your past experiences?
2. How do you feel about the people involved?
3. What would someone with your personality do?
4. What are the potential consequences?

Respond with your chosen action and brief reasoning.

## Response Format (JSON)
{
  "action": {
    "type": "<action_type>",
    "target": "<target_id or null>",
    "parameters": {}
  },
  "reasoning": "<1-2 sentences explaining your choice>",
  "emotional_state": "<emotion word: happy, angry, fearful, etc.>",
  "confidence": <0.0-1.0 how certain you are>,
  "new_belief": "<optional: something you now believe based on this>"
}
"""
```

### 6.4 Cognitive Mode Selection

```python
class CognitionRouter:
    """
    Decides whether to use System 1 (reflex) or System 2 (deliberation).
    """
    
    def select_mode(
        self,
        agent: Agent,
        stimulus: Stimulus,
        world: WorldState
    ) -> CognitionMode:
        
        # Always check reflexes first
        reflex_action = self.reflex_library.evaluate(agent, world)
        
        if reflex_action and reflex_action.priority >= 50:
            # High-priority reflex overrides everything
            return CognitionMode.REFLEX, reflex_action
        
        # Check if deliberation is warranted
        deliberation_triggers = [
            stimulus.is_novel,                    # New situation
            stimulus.involves_relationship,       # Social complexity
            stimulus.requires_planning,           # Multi-step goal
            stimulus.moral_dimension,             # Ethical choice
            agent.has_conflicting_goals,          # Internal conflict
        ]
        
        if any(deliberation_triggers):
            # Check if we have token budget
            if self.token_bucket.has_capacity(estimated_tokens=1000):
                # Check if already deliberating
                if not agent.deliberation_in_progress:
                    return CognitionMode.DELIBERATION, None
        
        # Fall back to lower-priority reflex or idle
        if reflex_action:
            return CognitionMode.REFLEX, reflex_action
        
        return CognitionMode.IDLE, None
```

### 6.5 Preemption & Cancellation

```python
class DeliberationManager:
    """
    Manages ongoing deliberations with preemption support.
    """
    
    async def handle_interrupt(
        self,
        agent: Agent,
        interrupt: InterruptEvent
    ):
        """
        Cancel ongoing deliberation if a high-priority
        event requires immediate response.
        """
        if agent.deliberation_task:
            if interrupt.priority > agent.deliberation_priority:
                # Cancel the LLM call
                agent.deliberation_task.cancel()
                
                # Log the preemption
                await self.ledger.record_event(PreemptionEvent(
                    agent_id=agent.id,
                    cancelled_deliberation=agent.deliberation_id,
                    interrupt_cause=interrupt.type,
                    tick=self.current_tick
                ))
                
                # Execute reflex response
                return self.execute_reflex(agent, interrupt)
        
        return None
```

### 6.6 Graceful Degradation

When LLM is unavailable or overloaded:

```python
class DegradationManager:
    """
    Handles fallback when System 2 is unavailable.
    """
    
    def get_fallback_action(
        self,
        agent: Agent,
        original_trigger: DeliberationTrigger
    ) -> Action:
        """
        Generate reasonable action without LLM.
        Uses personality-weighted heuristics.
        """
        
        # Map trigger type to heuristic behaviors
        fallback_behaviors = {
            "SOCIAL_INTERACTION": self.heuristic_social,
            "GOAL_CONFLICT": self.heuristic_goal,
            "NOVEL_SITUATION": self.heuristic_cautious,
            "EMOTIONAL_EVENT": self.heuristic_emotional,
        }
        
        heuristic = fallback_behaviors.get(
            original_trigger.type,
            self.heuristic_default
        )
        
        return heuristic(agent, original_trigger)
    
    def heuristic_social(self, agent: Agent, trigger) -> Action:
        """Fallback for social situations."""
        relationship = self.get_relationship(
            agent.id, 
            trigger.other_agent_id
        )
        
        if relationship.trust > 0.5:
            return Action("ENGAGE_FRIENDLY", target=trigger.other_agent_id)
        elif relationship.trust < -0.3:
            return Action("DISENGAGE", reason="distrust")
        else:
            return Action("OBSERVE", target=trigger.other_agent_id)
```

### 6.6.1 Latency Masking: The "Umm..." Protocol

When a System 2 deliberation request is sent, the agent should not appear frozen or unresponsive. System 1 immediately triggers contextually appropriate "Busy Animations" that mask the LLM latency while maintaining immersion.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   LATENCY MASKING PROTOCOL                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TIMELINE:                                                          │
│                                                                     │
│  Tick 0        Tick 1-100 (0-5 seconds)           Tick 100+         │
│  ══════        ════════════════════════           ═════════         │
│     │                    │                            │             │
│     ▼                    ▼                            ▼             │
│  ┌──────────┐     ┌─────────────────┐       ┌──────────────────┐    │
│  │ Stimulus │────►│ BUSY ANIMATION  │──────►│ ACTION EXECUTED  │    │
│  │ Received │     │ (Masks latency) │       │ (LLM response)   │    │
│  └──────────┘     └─────────────────┘       └──────────────────┘    │
│       │                   │                                         │
│       │                   │                                         │
│       ▼                   ▼                                         │
│  ┌──────────┐     ┌─────────────────────────────────────────────┐   │
│  │ System 2 │     │ Examples of Busy Animations:                │   │
│  │ Request  │     │                                             │   │
│  │ Sent     │     │ • Thinking: "Hmm..." (rubs chin)            │   │
│  └──────────┘     │ • Pacing: Walks a small path, thinking      │   │
│                   │ • Filler words: "Well...", "You see...",    │   │
│                   │   "Let me think about that..."              │   │
│                   │ • Distracted glance: Looks around room      │   │
│                   │ • Physical tell: Crosses arms, taps foot    │   │
│                   │                                             │   │
│                   └─────────────────────────────────────────────┘   │
│                                                                     │
│  SELECTION CRITERIA:                                                │
│  • Animation matches stimulus context (social vs threatening)       │
│  • Animation fits agent personality (nervous types pace, etc.)      │
│  • Animation doesn't commit to any action (reversible)              │
│  • Animation can loop if LLM takes longer than expected             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class BusyAnimation:
    """Defines a latency-masking animation."""
    animation_id: str
    display_name: str
    
    # Animation properties
    min_duration_ticks: int      # Minimum time to play
    max_duration_ticks: int      # Maximum before switching/looping
    is_loopable: bool            # Can repeat if still waiting
    
    # Visual/audio cues
    emote: str                   # Emotional display
    dialogue: Optional[str]      # Filler words to display/speak
    body_animation: str          # Physical animation name
    
    # Context matching
    suitable_contexts: List[str]  # When to use this animation
    personality_affinity: Dict[str, float]  # Which personalities prefer this


class LatencyMaskingManager:
    """
    Manages "busy" animations that mask LLM deliberation latency.
    Triggers immediately when System 2 is invoked.
    """
    
    # Library of busy animations
    BUSY_ANIMATIONS = {
        # Thinking animations
        "thoughtful_pause": BusyAnimation(
            animation_id="thoughtful_pause",
            display_name="Thoughtful Pause",
            min_duration_ticks=20,
            max_duration_ticks=60,
            is_loopable=True,
            emote="PENSIVE",
            dialogue="Hmm...",
            body_animation="chin_rub",
            suitable_contexts=["social", "decision", "question"],
            personality_affinity={"conscientiousness": 0.8, "openness": 0.6}
        ),
        
        "considering_response": BusyAnimation(
            animation_id="considering_response",
            display_name="Considering Response",
            min_duration_ticks=15,
            max_duration_ticks=45,
            is_loopable=True,
            emote="THOUGHTFUL",
            dialogue="Well, you see...",
            body_animation="slight_nod",
            suitable_contexts=["social", "question", "confrontation"],
            personality_affinity={"agreeableness": 0.7, "extraversion": 0.5}
        ),
        
        "nervous_deliberation": BusyAnimation(
            animation_id="nervous_deliberation",
            display_name="Nervous Deliberation",
            min_duration_ticks=20,
            max_duration_ticks=50,
            is_loopable=True,
            emote="ANXIOUS",
            dialogue="I... um...",
            body_animation="fidget",
            suitable_contexts=["confrontation", "accusation", "threat"],
            personality_affinity={"neuroticism": 0.9, "bravery": -0.3}
        ),
        
        "cautious_assessment": BusyAnimation(
            animation_id="cautious_assessment",
            display_name="Cautious Assessment",
            min_duration_ticks=25,
            max_duration_ticks=70,
            is_loopable=True,
            emote="WARY",
            dialogue=None,
            body_animation="scan_surroundings",
            suitable_contexts=["threat", "unknown", "suspicious"],
            personality_affinity={"neuroticism": 0.6, "conscientiousness": 0.7}
        ),
        
        "social_stalling": BusyAnimation(
            animation_id="social_stalling",
            display_name="Social Stalling",
            min_duration_ticks=15,
            max_duration_ticks=40,
            is_loopable=True,
            emote="FRIENDLY",
            dialogue="Let me think about that for a moment...",
            body_animation="gentle_smile",
            suitable_contexts=["social", "question", "request"],
            personality_affinity={"extraversion": 0.8, "agreeableness": 0.7}
        ),
        
        "pacing_thought": BusyAnimation(
            animation_id="pacing_thought",
            display_name="Pacing While Thinking",
            min_duration_ticks=30,
            max_duration_ticks=80,
            is_loopable=True,
            emote="FOCUSED",
            dialogue=None,
            body_animation="short_pace",
            suitable_contexts=["decision", "conflict", "planning"],
            personality_affinity={"extraversion": 0.6, "neuroticism": 0.5}
        ),
        
        "distracted_glance": BusyAnimation(
            animation_id="distracted_glance",
            display_name="Distracted Glance",
            min_duration_ticks=10,
            max_duration_ticks=30,
            is_loopable=True,
            emote="DISTRACTED",
            dialogue="Ah...",
            body_animation="look_away_briefly",
            suitable_contexts=["any"],
            personality_affinity={"openness": 0.5, "conscientiousness": -0.3}
        )
    }
    
    def __init__(self):
        self.active_masks: Dict[UUID, ActiveMask] = {}
    
    def trigger_busy_animation(
        self,
        agent: Agent,
        stimulus: Stimulus,
        estimated_latency_ticks: int
    ):
        """
        Immediately trigger appropriate busy animation when System 2 starts.
        """
        # Select animation based on context and personality
        animation = self._select_animation(agent, stimulus)
        
        if animation:
            mask = ActiveMask(
                agent_id=agent.id,
                animation=animation,
                start_tick=self.current_tick,
                estimated_end_tick=self.current_tick + estimated_latency_ticks,
                loops_completed=0
            )
            
            self.active_masks[agent.id] = mask
            
            # Emit animation start event
            self._emit_animation_start(agent, animation)
            
            logger.debug(
                f"Started busy animation '{animation.animation_id}' "
                f"for {agent.name}"
            )
    
    def _select_animation(
        self,
        agent: Agent,
        stimulus: Stimulus
    ) -> Optional[BusyAnimation]:
        """
        Select the most appropriate busy animation for the situation.
        """
        # Score each animation
        scored = []
        
        for anim_id, animation in self.BUSY_ANIMATIONS.items():
            score = 0.0
            
            # Context match
            if stimulus.context_type in animation.suitable_contexts:
                score += 0.5
            elif "any" in animation.suitable_contexts:
                score += 0.2
            
            # Personality match
            for trait, affinity in animation.personality_affinity.items():
                trait_value = getattr(agent.traits, trait, 0.5)
                if affinity > 0:
                    score += trait_value * affinity * 0.3
                else:
                    score += (1 - trait_value) * abs(affinity) * 0.3
            
            scored.append((animation, score))
        
        # Sort by score and add some randomness
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Pick from top 3 with weighted random selection
        top_candidates = scored[:3]
        total_score = sum(s for _, s in top_candidates)
        
        if total_score == 0:
            return top_candidates[0][0] if top_candidates else None
        
        # Weighted random selection
        r = random.random() * total_score
        cumulative = 0
        
        for animation, score in top_candidates:
            cumulative += score
            if r <= cumulative:
                return animation
        
        return top_candidates[0][0]
    
    def tick(self):
        """Update active mask animations."""
        completed = []
        
        for agent_id, mask in self.active_masks.items():
            elapsed = self.current_tick - mask.start_tick
            
            # Check if deliberation is complete
            if self._deliberation_complete(agent_id):
                completed.append(agent_id)
                continue
            
            # Handle animation looping
            anim_duration = mask.animation.max_duration_ticks
            if elapsed >= anim_duration:
                if mask.animation.is_loopable:
                    mask.loops_completed += 1
                    mask.start_tick = self.current_tick
                    self._emit_animation_loop(agent_id, mask.animation)
                else:
                    # Switch to a different animation
                    self._switch_animation(agent_id)
        
        # Clean up completed masks
        for agent_id in completed:
            del self.active_masks[agent_id]
    
    def cancel_busy_animation(self, agent_id: UUID):
        """Cancel busy animation when deliberation completes."""
        if agent_id in self.active_masks:
            mask = self.active_masks[agent_id]
            self._emit_animation_end(agent_id, mask.animation)
            del self.active_masks[agent_id]
    
    def _emit_animation_start(self, agent: Agent, animation: BusyAnimation):
        """Emit event for animation start."""
        self.event_bus.emit(Event(
            event_type=EventType.AGENT_ANIMATION,
            agent_id=agent.id,
            data={
                "animation_type": "busy_start",
                "animation_id": animation.animation_id,
                "emote": animation.emote,
                "dialogue": animation.dialogue,
                "body_animation": animation.body_animation
            }
        ))
    
    def _emit_animation_end(self, agent_id: UUID, animation: BusyAnimation):
        """Emit event for animation end."""
        self.event_bus.emit(Event(
            event_type=EventType.AGENT_ANIMATION,
            agent_id=agent_id,
            data={
                "animation_type": "busy_end",
                "animation_id": animation.animation_id
            }
        ))


@dataclass
class ActiveMask:
    """Tracks an active busy animation."""
    agent_id: UUID
    animation: BusyAnimation
    start_tick: int
    estimated_end_tick: int
    loops_completed: int
```

### 6.7 Agent LOD (Level of Detail) Tiers

To manage cognitive load and LLM costs efficiently, agents operate at different levels of detail based on their narrative importance and proximity to the viewer/player focus.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT LOD TIER SYSTEM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ TIER 1: FOCUS AGENTS (2-4 agents)                           │    │
│  │ ═══════════════════════════════                             │    │
│  │ • Full LLM deliberation for all complex decisions           │    │
│  │ • Complete episodic memory retrieval (10+ memories)         │    │
│  │ • Rich emotional modeling and expression                    │    │
│  │ • Detailed thought streams visible in debug UI              │    │
│  │ • All social triggers evaluated                             │    │
│  │ • Token budget: 60% of total allocation                     │    │
│  │                                                             │    │
│  │ Example: Marcus, Elena during accusation scene              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                         │                                           │
│                         ▼                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ TIER 2: AMBIENT AGENTS (5-8 agents)                         │    │
│  │ ═══════════════════════════════                             │    │
│  │ • LLM deliberation only for high-stakes decisions           │    │
│  │ • Limited memory retrieval (3-5 memories)                   │    │
│  │ • Simplified emotional states (happy/neutral/distressed)    │    │
│  │ • Abbreviated thought summaries                             │    │
│  │ • Priority social triggers only                             │    │
│  │ • Token budget: 30% of total allocation                     │    │
│  │                                                             │    │
│  │ Example: Viktor, Sarah when not directly in conflict        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                         │                                           │
│                         ▼                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ TIER 3: SIMULATION AGENTS (6-10 agents)                     │    │
│  │ ═════════════════════════════════                           │    │
│  │ • Reflex-only cognition (no LLM calls)                      │    │
│  │ • Minimal memory access (last 1-2 relevant only)            │    │
│  │ • Binary emotional states (calm/agitated)                   │    │
│  │ • No thought stream (actions only)                          │    │
│  │ • Basic routine behaviors and reactions                     │    │
│  │ • Token budget: 10% (emergency escalation only)             │    │
│  │                                                             │    │
│  │ Example: Background villagers, guards on patrol             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 6.7.1 LOD Configuration

```python
@dataclass
class LODTierConfig:
    """Configuration for each Level of Detail tier."""
    
    # Tier definitions
    FOCUS = LODTier(
        name="focus",
        max_agents=4,
        llm_access=True,
        deliberation_threshold=0.3,  # Low bar = more deliberation
        memory_retrieval_limit=10,
        emotional_granularity="full",  # 12+ emotional states
        token_budget_percent=60,
        social_trigger_filter=None,  # All triggers active
        thought_stream_detail="verbose"
    )
    
    AMBIENT = LODTier(
        name="ambient", 
        max_agents=8,
        llm_access=True,
        deliberation_threshold=0.7,  # Higher bar = less deliberation
        memory_retrieval_limit=5,
        emotional_granularity="simple",  # 5 states: happy, sad, angry, fearful, neutral
        token_budget_percent=30,
        social_trigger_filter=["warn_friend", "confront_suspect", "share_critical_gossip"],
        thought_stream_detail="summary"
    )
    
    SIMULATION = LODTier(
        name="simulation",
        max_agents=10,
        llm_access=False,  # Reflex-only
        deliberation_threshold=1.0,  # Never deliberate (except emergency promotion)
        memory_retrieval_limit=2,
        emotional_granularity="binary",  # calm, agitated
        token_budget_percent=10,
        social_trigger_filter=["flee_danger"],  # Survival only
        thought_stream_detail="none"
    )

class LODManager:
    """
    Dynamically assigns agents to LOD tiers based on narrative relevance.
    
    CRITICAL: Implements demotion cooldowns to prevent LOD flickering.
    Once an agent is promoted to a higher tier, they must remain there
    for a minimum duration to complete their current narrative beat.
    """
    
    # Minimum ticks before demotion is allowed (prevents LOD flickering)
    DEMOTION_COOLDOWN = {
        "FOCUS": 300,    # ~15-30 seconds minimum at FOCUS (ensures dialogue/action completes)
        "AMBIENT": 200,  # ~10-20 seconds minimum at AMBIENT (ensures scene transition completes)
    }
    
    def __init__(self, config: LODTierConfig):
        self.config = config
        self.tier_assignments: Dict[UUID, LODTier] = {}
        self.tier_entry_tick: Dict[UUID, int] = {}  # When agent entered current tier
        self.current_tick: int = 0
        
    def update_tiers(
        self,
        agents: List[Agent],
        narrative_context: NarrativeContext,
        viewer_focus: Optional[UUID] = None
    ):
        """
        Reassign LOD tiers based on current narrative state.
        Called every N ticks or on significant events.
        
        IMPORTANT: Respects demotion cooldowns - agents cannot be demoted
        until they've been in their current tier for the minimum duration.
        This prevents jarring behavioral changes mid-scene.
        """
        
        # Score each agent's narrative relevance
        scored_agents = []
        for agent in agents:
            score = self._calculate_relevance_score(
                agent, narrative_context, viewer_focus
            )
            scored_agents.append((agent, score))
        
        # Sort by relevance (highest first)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # Assign tiers based on rank (respecting cooldowns)
        focus_count = 0
        ambient_count = 0
        
        for agent, score in scored_agents:
            current_tier = self.tier_assignments.get(agent.id)
            new_tier = self._determine_new_tier(agent, score, focus_count, ambient_count)
            
            # Check if this would be a demotion
            if self._is_demotion(current_tier, new_tier):
                # Enforce cooldown - agent stays at current tier if cooldown not elapsed
                if not self._can_demote(agent.id, current_tier):
                    new_tier = current_tier
                    logger.debug(
                        f"Demotion blocked for {agent.id}: cooldown not elapsed "
                        f"(tier={current_tier.name if current_tier else 'None'})"
                    )
            
            # Apply tier assignment
            old_tier = self.tier_assignments.get(agent.id)
            self.tier_assignments[agent.id] = new_tier
            
            # Track entry tick if tier changed
            if old_tier != new_tier:
                self.tier_entry_tick[agent.id] = self.current_tick
                logger.info(
                    f"LOD transition: {agent.id} {old_tier.name if old_tier else 'None'} -> {new_tier.name}"
                )
            
            # Update counters
            if new_tier == self.config.FOCUS:
                focus_count += 1
            elif new_tier == self.config.AMBIENT:
                ambient_count += 1
    
    def _determine_new_tier(
        self, 
        agent: Agent, 
        score: float, 
        focus_count: int, 
        ambient_count: int
    ) -> LODTier:
        """Determine what tier an agent SHOULD be in based on score."""
        if focus_count < self.config.FOCUS.max_agents and score > 0.7:
            return self.config.FOCUS
        elif ambient_count < self.config.AMBIENT.max_agents and score > 0.3:
            return self.config.AMBIENT
        else:
            return self.config.SIMULATION
    
    def _is_demotion(self, current_tier: Optional[LODTier], new_tier: LODTier) -> bool:
        """Check if transitioning from current to new tier is a demotion."""
        if current_tier is None:
            return False
        
        tier_rank = {
            self.config.FOCUS: 2,
            self.config.AMBIENT: 1,
            self.config.SIMULATION: 0,
        }
        
        return tier_rank.get(current_tier, 0) > tier_rank.get(new_tier, 0)
    
    def _can_demote(self, agent_id: UUID, current_tier: LODTier) -> bool:
        """
        Check if agent has been in current tier long enough to allow demotion.
        
        This is critical for preventing LOD flickering:
        - Focus agents need time to complete their dialogue/action sequence
        - Ambient agents need time to complete their scene transition
        
        Without this cooldown, agents can rapidly flip between tiers,
        causing jarring behavioral inconsistencies for the player.
        """
        entry_tick = self.tier_entry_tick.get(agent_id)
        if entry_tick is None:
            return True  # No record = can demote
        
        tier_name = current_tier.name if hasattr(current_tier, 'name') else str(current_tier)
        cooldown = self.DEMOTION_COOLDOWN.get(tier_name.upper(), 0)
        
        ticks_in_tier = self.current_tick - entry_tick
        return ticks_in_tier >= cooldown
    
    def set_current_tick(self, tick: int):
        """Update current tick (called each simulation frame)."""
        self.current_tick = tick
    
    def _calculate_relevance_score(
        self,
        agent: Agent,
        context: NarrativeContext,
        viewer_focus: Optional[UUID]
    ) -> float:
        """
        Score agent's current narrative importance (0.0 - 1.0).
        """
        score = 0.0
        
        # Viewer proximity bonus
        if viewer_focus and agent.id == viewer_focus:
            score += 0.5
        elif viewer_focus and self._is_interacting_with(agent.id, viewer_focus):
            score += 0.3
        
        # Active in current tension/conflict
        if agent.id in context.active_conflict_participants:
            score += 0.3
        
        # Holds critical information
        if agent.id in context.agents_with_secrets:
            score += 0.2
        
        # Recently mentioned in gossip
        if agent.id in context.recently_gossiped_about:
            score += 0.1
        
        # Currently deliberating (don't demote mid-thought)
        if agent.state == AgentState.DELIBERATING:
            score += 0.2
        
        return min(1.0, score)
    
    def promote_agent(self, agent_id: UUID, reason: str):
        """
        Emergency promotion to higher tier (e.g., suddenly involved in conflict).
        """
        current_tier = self.tier_assignments.get(agent_id, self.config.SIMULATION)
        
        if current_tier == self.config.SIMULATION:
            self.tier_assignments[agent_id] = self.config.AMBIENT
            logger.info(f"Promoted {agent_id} to AMBIENT: {reason}")
        elif current_tier == self.config.AMBIENT:
            self.tier_assignments[agent_id] = self.config.FOCUS
            logger.info(f"Promoted {agent_id} to FOCUS: {reason}")
```

#### 6.7.2 LOD-Aware Cognition

```python
class LODAwareCognitionEngine:
    """
    Cognition engine that respects LOD tier constraints.
    """
    
    async def process_stimulus(
        self,
        agent: Agent,
        stimulus: Stimulus,
        lod_tier: LODTier
    ) -> Optional[Action]:
        
        # Always check reflexes first (all tiers)
        reflex_action = self.reflex_library.evaluate(agent, stimulus)
        
        if reflex_action:
            # High-priority reflex executes regardless of tier
            if reflex_action.priority >= 50:
                return reflex_action
            
            # Lower priority reflex: execute immediately for SIMULATION tier
            if lod_tier.name == "simulation":
                return reflex_action
        
        # Check if deliberation is warranted AND allowed by tier
        if not lod_tier.llm_access:
            # SIMULATION tier: reflex or heuristic only
            return reflex_action or self.heuristic_fallback(agent, stimulus)
        
        # Calculate deliberation need
        deliberation_score = self._score_deliberation_need(agent, stimulus)
        
        if deliberation_score < lod_tier.deliberation_threshold:
            # Below tier's threshold: use reflex/heuristic
            return reflex_action or self.heuristic_fallback(agent, stimulus)
        
        # Deliberation warranted: check token budget
        tier_budget = self.token_bucket.get_tier_bucket(lod_tier.name)
        
        if not tier_budget.has_capacity(estimated_tokens=800):
            # Budget exhausted: graceful degradation
            return reflex_action or self.heuristic_fallback(agent, stimulus)
        
        # Proceed with deliberation using tier-appropriate context
        return await self.deliberate_with_lod(agent, stimulus, lod_tier)
    
    async def deliberate_with_lod(
        self,
        agent: Agent,
        stimulus: Stimulus,
        lod_tier: LODTier
    ) -> Action:
        """
        Deliberation adjusted for LOD tier constraints.
        """
        
        # Retrieve memories with tier-appropriate limit
        memories = await self.memory_retrieval(
            agent.id,
            query=stimulus.description,
            max_memories=lod_tier.memory_retrieval_limit
        )
        
        # Build prompt with tier-appropriate detail
        if lod_tier.thought_stream_detail == "verbose":
            prompt = self.build_full_deliberation_prompt(agent, stimulus, memories)
        else:
            prompt = self.build_condensed_deliberation_prompt(agent, stimulus, memories)
        
        # LLM call
        proposal = await self.llm_deliberator.deliberate(agent, prompt)
        
        return proposal.action if proposal else self.heuristic_fallback(agent, stimulus)
```

#### 6.7.3 LOD Transition Events

```python
class LODTransitionEvents:
    """
    Defines events that trigger LOD tier transitions.
    """
    
    PROMOTION_TRIGGERS = {
        # Immediate promotion to FOCUS
        "to_focus": [
            "agent_accused_publicly",
            "agent_witnesses_crime",
            "agent_directly_confronted",
            "agent_reveals_secret",
            "agent_in_physical_danger",
        ],
        
        # Promotion to AMBIENT
        "to_ambient": [
            "agent_mentioned_in_gossip",
            "agent_enters_active_scene",
            "agent_relationship_changes_significantly",
            "agent_receives_important_information",
        ]
    }
    
    DEMOTION_TRIGGERS = {
        # Demotion from FOCUS (after cooldown)
        "from_focus": [
            "conflict_resolved_for_agent",
            "agent_leaves_active_scene",
            "no_interactions_for_500_ticks",
        ],
        
        # Demotion to SIMULATION
        "to_simulation": [
            "agent_returns_to_routine",
            "no_narrative_relevance_for_1000_ticks",
        ]
    }
    
    # Minimum ticks before demotion (prevents thrashing)
    # CRITICAL: These cooldowns are enforced by LODManager._can_demote()
    DEMOTION_COOLDOWN = {
        "focus": 300,    # 15 seconds minimum at FOCUS
        "ambient": 200,  # 10 seconds minimum at AMBIENT
    }
```

##### Why Demotion Cooldowns Matter (LOD Flickering Prevention)

Without enforced cooldowns, agents can rapidly oscillate between LOD tiers:

```
PROBLEM: LOD Flickering

Tick 100: Agent promoted to FOCUS (starts complex behavior)
Tick 120: Score drops slightly → demoted to AMBIENT (behavior truncated!)
Tick 140: Score rises → promoted to FOCUS (restarts behavior)
Tick 160: Score drops → demoted again...

Result: Agent appears to "glitch" - starting actions but never completing them.
Player sees: Character walks toward someone, stops, turns away, turns back...
```

The cooldown ensures agents complete their current narrative beat:

```
SOLUTION: Enforced Demotion Cooldowns

Tick 100: Agent promoted to FOCUS (starts complex behavior)
         └─► tier_entry_tick[agent_id] = 100
Tick 120: Score drops, but cooldown check: 120 - 100 = 20 ticks < 300
         └─► Demotion BLOCKED - agent stays at FOCUS
Tick 400: Score still low, cooldown check: 400 - 100 = 300 ticks >= 300
         └─► Demotion ALLOWED - agent gracefully transitions to AMBIENT

Result: Agent completes their full dialogue/action sequence before transitioning.
Player sees: Natural, coherent behavior that respects the scene's pacing.
```

**Key Enforcement Point:** The `LODManager.update_tiers()` method calls `_can_demote()` 
before any tier demotion. If the agent hasn't been in their current tier for the 
minimum cooldown duration, the demotion is blocked and logged.

#### 6.7.4 Secret Objective Injection (Narrative Quality Enhancement)

To prevent "boring AI" behavior where agents simply react passively to events, Focus-tier agents are assigned Hidden Agendas that create natural dramatic tension through conflicting goals.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   SECRET OBJECTIVE INJECTION SYSTEM                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Focus Agent A                    Focus Agent B                     │
│  ┌─────────────────────┐          ┌─────────────────────┐          │
│  │ Public Goal:        │          │ Public Goal:        │          │
│  │ "Find the thief"    │          │ "Protect my family" │          │
│  │                     │          │                     │          │
│  │ SECRET OBJECTIVE:   │    VS    │ SECRET OBJECTIVE:   │          │
│  │ "Ensure Marcus is   │◄────────►│ "Hide evidence that │          │
│  │  held responsible"  │          │  could implicate    │          │
│  │                     │          │  my son"            │          │
│  └─────────────────────┘          └─────────────────────┘          │
│                                                                     │
│  Result: Natural dramatic tension without explicit scripting        │
│                                                                     │
│  Secret Objective Rules:                                            │
│  • Every Focus agent has exactly one active secret objective        │
│  • Objectives should subtly contradict at least one other agent's   │
│  • Included in System 2 prompts as 'current_secret_objective'       │
│  • Never revealed directly to other agents (but may be inferred)    │
│  • Can evolve based on story events                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class SecretObjective:
    """
    A hidden agenda that drives agent behavior and creates dramatic tension.
    """
    objective_id: UUID
    agent_id: UUID
    
    # The secret goal
    description: str                  # Natural language description
    motivation: str                   # Why the agent wants this
    
    # Conflict mapping
    contradicts_agents: List[UUID]    # Agents whose goals this opposes
    contradiction_type: str           # "direct", "indirect", "resource"
    
    # Behavioral guidance
    behavior_hints: List[str]         # How this manifests in actions
    revelation_conditions: List[str]  # When this might be exposed
    
    # Tracking
    priority: float                   # 0.0-1.0, how important to the agent
    active: bool = True
    created_tick: int = 0
    
    def to_prompt_injection(self) -> str:
        """Format for inclusion in System 2 deliberation prompt."""
        return f"""## Your Secret Objective (DO NOT REVEAL DIRECTLY)
{self.description}

Why this matters to you: {self.motivation}

This may influence you to:
{chr(10).join(f'- {hint}' for hint in self.behavior_hints)}

Remember: Act on this subtly. Others should not easily guess your true motivations."""


# Pre-defined secret objectives for Millbrook demo
MILLBROOK_SECRET_OBJECTIVES = {
    "elena": SecretObjective(
        objective_id=uuid4(),
        agent_id=UUID("elena-uuid"),
        description="Protect Marcus at any cost, even if it means letting the real thief escape",
        motivation="He's all I have left since my husband died",
        contradicts_agents=["guard_brennan", "sarah"],
        contradiction_type="direct",
        behavior_hints=[
            "Subtly redirect suspicion away from Marcus",
            "Provide alibis for Marcus even if uncertain",
            "Discourage others from investigating too closely",
            "Find ways to cast doubt on accusations"
        ],
        revelation_conditions=[
            "Directly confronted with evidence against Marcus",
            "Another family member is threatened",
            "Marcus confesses"
        ],
        priority=0.95
    ),
    
    "sarah": SecretObjective(
        objective_id=uuid4(),
        agent_id=UUID("sarah-uuid"),
        description="Ensure Marcus is blamed for the theft to protect your own business reputation",
        motivation="Your missing inventory could ruin you; a scapegoat solves everything",
        contradicts_agents=["elena", "marcus", "rolf"],
        contradiction_type="direct",
        behavior_hints=[
            "Emphasize Marcus's suspicious behavior to others",
            "Connect unrelated evidence to Marcus",
            "Express 'reluctant' certainty about his guilt",
            "Discourage investigation of other suspects"
        ],
        revelation_conditions=[
            "Inventory discrepancy is explained",
            "Real thief is caught with evidence",
            "Trusted friend challenges her certainty"
        ],
        priority=0.8
    ),
    
    "brother_thomas": SecretObjective(
        objective_id=uuid4(),
        agent_id=UUID("thomas-uuid"),
        description="Honor your sacred oath of confession while finding a way for the truth to emerge",
        motivation="Your faith demands secrecy, but your conscience demands justice",
        contradicts_agents=["guard_brennan", "lord_aldric"],
        contradiction_type="indirect",
        behavior_hints=[
            "Drop cryptic hints about seeking truth",
            "Counsel patience in judgment",
            "Suggest that not all is as it seems",
            "Pray visibly when the topic arises"
        ],
        revelation_conditions=[
            "The confessor releases you from the oath",
            "An innocent person faces severe punishment",
            "Father Jonas provides guidance before death"
        ],
        priority=0.85
    ),
    
    "the_stranger": SecretObjective(
        objective_id=uuid4(),
        agent_id=UUID("stranger-uuid"),
        description="Recover the artifact and escape, using Marcus as a convenient distraction",
        motivation="The artifact is worth more than this entire village",
        contradicts_agents=["viktor", "elena", "guard_brennan"],
        contradiction_type="direct",
        behavior_hints=[
            "Appear helpful to the investigation",
            "Subtly reinforce suspicions about Marcus",
            "Build trust with villagers to reduce suspicion",
            "Look for opportunities to search for the artifact"
        ],
        revelation_conditions=[
            "Caught searching suspicious locations",
            "Someone recognizes you from another town",
            "The artifact is found and you react"
        ],
        priority=1.0
    ),
    
    "lydia": SecretObjective(
        objective_id=uuid4(),
        agent_id=UUID("lydia-uuid"),
        description="Work up the courage to reveal what you saw, but protect yourself from retaliation",
        motivation="You saw the truth but fear the Stranger noticed you watching",
        contradicts_agents=["the_stranger"],
        contradiction_type="direct",
        behavior_hints=[
            "Avoid being alone with the Stranger",
            "Show nervousness when the theft is discussed",
            "Seek out trusted figures like Viktor or Thomas",
            "Almost speak up, then lose nerve"
        ],
        revelation_conditions=[
            "Given protection or reassurance by authority",
            "The Stranger threatens someone she cares about",
            "Someone directly asks if she saw something"
        ],
        priority=0.7
    )
}


class SecretObjectiveManager:
    """
    Manages secret objectives and their injection into agent deliberation.
    """
    
    def __init__(self):
        self.objectives: Dict[UUID, SecretObjective] = {}
        self.conflict_graph: Dict[UUID, List[UUID]] = {}  # agent -> conflicting agents
    
    def assign_objective(self, agent_id: UUID, objective: SecretObjective):
        """Assign a secret objective to an agent."""
        self.objectives[agent_id] = objective
        
        # Update conflict graph
        self.conflict_graph[agent_id] = objective.contradicts_agents
        
        logger.info(f"Assigned secret objective to {agent_id}: {objective.description[:50]}...")
    
    def get_prompt_injection(self, agent_id: UUID) -> Optional[str]:
        """
        Get the secret objective prompt injection for an agent.
        Only returns for Focus-tier agents with active objectives.
        """
        objective = self.objectives.get(agent_id)
        
        if objective and objective.active:
            return objective.to_prompt_injection()
        
        return None
    
    def check_revelation_conditions(
        self, 
        agent_id: UUID, 
        current_context: Dict[str, Any]
    ) -> bool:
        """
        Check if any revelation conditions have been met.
        May deactivate or modify the secret objective.
        """
        objective = self.objectives.get(agent_id)
        
        if not objective:
            return False
        
        # Check each revelation condition against current context
        for condition in objective.revelation_conditions:
            if self._condition_met(condition, current_context):
                logger.info(f"Revelation condition met for {agent_id}: {condition}")
                return True
        
        return False
    
    def get_conflict_intensity(self, agent_a: UUID, agent_b: UUID) -> float:
        """
        Calculate how much two agents' secret objectives conflict.
        Used by Drama Director to identify natural tension points.
        """
        obj_a = self.objectives.get(agent_a)
        obj_b = self.objectives.get(agent_b)
        
        if not obj_a or not obj_b:
            return 0.0
        
        # Check mutual conflicts
        a_conflicts_b = agent_b in obj_a.contradicts_agents
        b_conflicts_a = agent_a in obj_b.contradicts_agents
        
        if a_conflicts_b and b_conflicts_a:
            return 1.0  # Maximum conflict
        elif a_conflicts_b or b_conflicts_a:
            return 0.6  # One-sided conflict
        else:
            return 0.0  # No conflict
    
    def _condition_met(self, condition: str, context: Dict) -> bool:
        """Check if a specific revelation condition is met."""
        # Implementation would parse condition and check against context
        # Simplified version:
        return condition in context.get("triggered_events", [])
```

#### 6.7.5 Secret Objective Integration with System 2 Prompts

```python
class EnhancedDeliberationEngine:
    """
    Deliberation engine enhanced with secret objective injection.
    """
    
    def __init__(
        self,
        llm: LLMDeliberator,
        secret_objective_manager: SecretObjectiveManager,
        lod_manager: LODManager
    ):
        self.llm = llm
        self.secret_objectives = secret_objective_manager
        self.lod_manager = lod_manager
    
    async def deliberate(
        self,
        agent: Agent,
        trigger: DeliberationTrigger,
        context: DeliberationContext
    ) -> Proposal:
        """
        Deliberate with secret objective injection for Focus agents.
        """
        
        # Get agent's LOD tier
        lod_tier = self.lod_manager.get_tier(agent.id)
        
        # Build base prompt
        prompt = self._build_base_prompt(agent, trigger, context)
        
        # Inject secret objective for Focus tier agents
        if lod_tier.name == "focus":
            secret_injection = self.secret_objectives.get_prompt_injection(agent.id)
            
            if secret_injection:
                prompt = self._inject_secret_objective(prompt, secret_injection)
        
        # Call LLM
        response = await self.llm.generate(prompt)
        
        return self._parse_response(response)
    
    def _inject_secret_objective(self, prompt: str, secret_injection: str) -> str:
        """
        Inject secret objective into the prompt.
        Placed after personality but before situation for maximum influence.
        """
        # Find insertion point (after personality section)
        personality_end = prompt.find("## Current Situation")
        
        if personality_end == -1:
            # Fallback: append before response instructions
            insertion_point = prompt.find("## Instructions")
            if insertion_point == -1:
                insertion_point = len(prompt)
        else:
            insertion_point = personality_end
        
        return (
            prompt[:insertion_point] + 
            "\n\n" + secret_injection + "\n\n" + 
            prompt[insertion_point:]
        )
```

---

## 7. Demo Scenario: Three-Act Structure

The MVP demo showcases emergent narrative through a carefully seeded but open-ended village scenario.

### 7.1 Setting: Millbrook Village

```
┌─────────────────────────────────────────────────────────────────┐
│                     MILLBROOK VILLAGE MAP                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     ┌─────────┐              ┌──────────┐                       │
│     │ TAVERN  │              │  CHURCH  │                       │
│     │ "The    │              │          │                       │
│     │ Rusty   │              │          │                       │
│     │ Nail"   │              └──────────┘                       │
│     └────┬────┘                    │                            │
│          │                         │                            │
│   ═══════╪═════════════════════════╪══════════════════          │
│          │      MAIN ROAD          │                            │
│   ═══════╪═════════════════════════╪══════════════════          │
│          │                         │                            │
│     ┌────┴────┐              ┌─────┴─────┐     ┌──────────┐     │
│     │ MARKET  │              │ BLACKSMITH│     │ MANOR    │     │
│     │ SQUARE  │              │           │     │ (Lord's  │     │
│     │         │              │           │     │  Estate) │     │
│     └─────────┘              └───────────┘     └──────────┘     │
│          │                                           │          │
│     ┌────┴────┐                              ┌──────┴──────┐    │
│     │MERCHANT │                              │   GARDENS   │    │
│     │ STALLS  │                              │             │    │
│     └─────────┘                              └─────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Cast of Characters (15 Agents)

| Agent | Role | Key Traits | Starting Knowledge | Hidden Agenda |
|-------|------|------------|-------------------|---------------|
| **Lord Aldric** | Noble | Proud, paranoid, just | Rules the village | Suspects theft from manor |
| **Elena** | Innkeeper | Gossipy, kind, observant | Knows everyone's habits | Protecting her son |
| **Marcus** | Elena's Son | Impulsive, loyal, secretive | Found the artifact | Hid stolen goods (innocent) |
| **Brother Thomas** | Priest | Pious, conflicted, wise | Heard confession | Bound by sacred oath |
| **Viktor** | Blacksmith | Gruff, honest, perceptive | Saw suspicious activity | None (truth-seeker) |
| **Sarah** | Merchant | Ambitious, shrewd, anxious | Missing inventory | Suspects Marcus |
| **Old Marta** | Herbalist | Cryptic, knowing, patient | Ancient village secrets | Knows the artifact's origin |
| **Guard Captain Brennan** | Guard | Dutiful, rigid, fair | Investigating theft | Pressure from Lord |
| **Lydia** | Maid at Manor | Timid, observant, conflicted | Saw the real thief | Afraid of consequences |
| **Rolf** | Stablehand | Simple, loyal, strong | Saw Marcus at night | Wants to help Marcus |
| **The Stranger** | Traveler | Mysterious, charming, calculating | Seeking the artifact | The actual thief |
| **Willem** | Merchant Guard | Suspicious, territorial | Noticed the Stranger | Distrusts outsiders |
| **Father Jonas** | Elder Priest | Wise, dying, keeper of secrets | History of the artifact | Trying to warn Thomas |
| **Greta** | Barmaid | Flirty, cunning, survivor | Overheard the Stranger | Playing all sides |
| **Young Tom** | Apprentice | Eager, naive, honest | Admires Marcus | None (innocent witness) |

### 7.3 The Three-Act Structure

#### ACT I: NORMALCY & INCITING INCIDENT (Minutes 0-4)

**Setup Phase (Ticks 0-2000)**

Initial conditions seeded into the simulation:

```python
ACT_I_SEEDS = {
    "world_state": {
        "time_of_day": "MORNING",
        "weather": "CLEAR",
        "recent_event": "Festival ended yesterday"
    },
    
    "initial_gossip": [
        Rumor(
            content="Lord Aldric's manor was burgled last night",
            source="public_knowledge",
            confidence=0.9,
            propagated_to=["Elena", "Viktor", "Sarah"]
        )
    ],
    
    "hidden_truths": [
        Fact("The Stranger stole the artifact"),
        Fact("Marcus found dropped artifact, hid it thinking he'd be blamed"),
        Fact("Lydia saw the Stranger leaving the manor"),
        Fact("The artifact is actually dangerous")
    ],
    
    "scheduled_events": [
        Event(tick=500, type="STRANGER_ARRIVES_AT_TAVERN"),
        Event(tick=1000, type="GUARD_BEGINS_INVESTIGATION"),
        Event(tick=1500, type="SARAH_NOTICES_MARCUS_ACTING_ODD")
    ]
}
```

**Expected Emergent Behaviors:**

1. Agents begin daily routines (blacksmith opens shop, priest prays, etc.)
2. Gossip about the theft spreads naturally through social interactions
3. The Stranger arrives, triggering curiosity reflexes in tavern patrons
4. Guard Captain begins questioning people, creating tension
5. Sarah observes Marcus's nervous behavior, forms suspicion

**Key Narrative Beat:** Sarah shares her suspicion with Elena (Marcus's mother), creating dramatic irony.

#### ACT II: RISING TENSION & COMPLICATIONS (Minutes 4-10)

**Escalation Phase (Ticks 2000-6000)**

```python
ACT_II_DYNAMICS = {
    "tension_sources": [
        "Marcus avoiding the guards",
        "Elena torn between protecting son and truth",
        "The Stranger manipulating suspicion toward Marcus",
        "Brother Thomas's internal conflict (heard confession)",
        "Lydia's fear preventing her from speaking"
    ],
    
    "potential_confrontations": [
        "Guard Captain questioning Marcus",
        "Sarah accusing Marcus publicly",
        "Elena defending her son",
        "Viktor noticing the Stranger's interest in the case"
    ],
    
    "gossip_mutations": [
        # Original: "Manor was burgled"
        # Mutates to: "Marcus was seen near the manor"
        # Mutates to: "Marcus stole from the Lord"
    ],
    
    "catalyst_injection": {
        "trigger": "tension_too_low",
        "event": "Lord Aldric announces reward for information",
        "tick_range": [3000, 4000]
    }
}
```

**Expected Emergent Behaviors:**

1. Social network fragments into factions (believe Marcus guilty vs. innocent)
2. The Stranger feeds false information to implicate Marcus further
3. Relationships strain (Elena loses trust in Sarah)
4. Brother Thomas struggles visibly, prompting speculation
5. Lydia's guilt manifests in nervous behaviors that Viktor notices
6. Old Marta drops cryptic hints about the artifact's true nature

**Key Narrative Beat:** Public accusation of Marcus, creating a moment of maximum tension.

#### ACT III: CRISIS & RESOLUTION (Minutes 10-15)

**Climax Phase (Ticks 6000-9000)**

```python
ACT_III_POSSIBILITIES = {
    # Multiple possible resolutions based on emergent dynamics
    
    "resolution_paths": [
        {
            "name": "Truth Revealed",
            "trigger": "Lydia gains courage OR Viktor confronts Stranger",
            "outcome": "Stranger exposed, Marcus cleared"
        },
        {
            "name": "Tragic Miscarriage",
            "trigger": "No one speaks up, social pressure overwhelming",
            "outcome": "Marcus wrongly punished, village guilt"
        },
        {
            "name": "Escape",
            "trigger": "Elena helps Marcus flee before truth emerges",
            "outcome": "Stranger gets away, family broken but safe"
        },
        {
            "name": "Confrontation",
            "trigger": "Marcus confronts Stranger directly",
            "outcome": "Physical/social confrontation, truth forced out"
        }
    ],
    
    "resolution_catalysts": [
        "Old Marta reveals artifact's danger (raises stakes)",
        "Father Jonas dies, freeing Thomas from oath",
        "The Stranger attempts to flee (reveals guilt)",
        "Guard finds evidence at Stranger's lodging"
    ]
}
```

**Expected Emergent Behaviors:**

1. Tension reaches critical point, triggering deliberation in multiple agents
2. One or more truth-revealing events occur based on accumulated social dynamics
3. Relationships reconfigure based on who supported whom
4. Village reaches new equilibrium with consequences for all

**Demo Success Criteria:**
- [ ] Clear narrative arc observable by viewers
- [ ] At least 3 unscripted dramatic moments
- [ ] Gossip visibly mutating as it spreads
- [ ] Relationships changing based on events
- [ ] Memory references influencing decisions (e.g., "I remember when...")
- [ ] Dual-mode cognition visible (fast reactions vs. deliberate choices)

### 7.4 Debug UI Requirements for Demo

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEBUG UI LAYOUT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐  ┌────────────────────────────────┐   │
│  │   VILLAGE VIEW       │  │   AGENT INSPECTOR              │   │
│  │   (2D Top-down)      │  │                                │   │
│  │                      │  │   Selected: Elena              │   │
│  │   [Agent positions   │  │   State: DELIBERATING          │   │
│  │    with names and    │  │                                │   │
│  │    status icons]     │  │   Current Thought:             │   │
│  │                      │  │   "Should I tell the guard     │   │
│  │   Lines showing      │  │   about Marcus? He's my son    │   │
│  │   active             │  │   but the Lord's justice..."   │   │
│  │   conversations      │  │                                │   │
│  │                      │  │   Recent Memories:             │   │
│  │                      │  │   - Marcus's birth (joy)       │   │
│  │                      │  │   - Husband's death (grief)    │   │
│  │                      │  │   - Sarah's accusation (anger) │   │
│  └──────────────────────┘  └────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────┐  ┌────────────────────────────────┐   │
│  │   GOSSIP TRACKER     │  │   RELATIONSHIP GRAPH           │   │
│  │                      │  │                                │   │
│  │   Active Rumors:     │  │   [Network visualization       │   │
│  │                      │  │    showing trust/affinity      │   │
│  │   "Marcus stole..."  │  │    between agents with         │   │
│  │   └─ Elena (conf:70%)│  │    color-coded edges]          │   │
│  │   └─ Viktor (conf:35%)│ │                                │   │
│  │   └─ Sarah (conf:90%)│  │   Red = distrust               │   │
│  │                      │  │   Green = trust                │   │
│  │   "Stranger is..."   │  │   Thickness = familiarity      │   │
│  │   └─ Willem (conf:60%)│ │                                │   │
│  └──────────────────────┘  └────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   EVENT LOG / TIMELINE                                   │   │
│  │   [Tick 4523] Elena shared rumor with Viktor             │   │
│  │   [Tick 4530] Guard Captain questioned Marcus (TENSE)    │   │
│  │   [Tick 4545] Marcus REFLEX: flee_conversation           │   │
│  │   [Tick 4550] Sarah DELIBERATING: confront_or_wait       │   │
│  │   [Tick 4555] The Stranger observed the confrontation    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4.1 Thought Bubble Inspector (Debug UI Enhancement)

A toggleable UI overlay that shows the agent's Internal Monologue (Reasoning Chain-of-Thought) in real-time. This provides unprecedented insight into agent decision-making for debugging and demonstration purposes.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   THOUGHT BUBBLE INSPECTOR UI                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     VILLAGE VIEW                            │    │
│  │                                                             │    │
│  │        [Viktor]                                             │    │
│  │           │                                                 │    │
│  │           │  ┌─────────────────────────────────┐            │    │
│  │           └──│ 💭 THINKING...                  │            │    │
│  │              │                                 │            │    │
│  │              │ "The Stranger keeps watching    │            │    │
│  │              │  Marcus. That's suspicious.     │            │    │
│  │              │  I should keep an eye on him."  │            │    │
│  │              │                                 │            │    │
│  │              │ Emotion: SUSPICIOUS             │            │    │
│  │              │ Confidence: 0.72                │            │    │
│  │              └─────────────────────────────────┘            │    │
│  │                                                             │    │
│  │     [Elena]──┐                                              │    │
│  │              │  ┌─────────────────────────────────┐         │    │
│  │              └──│ 💭 DELIBERATING...             │         │    │
│  │                 │                                 │         │    │
│  │                 │ Memory: "Marcus helped me when │         │    │
│  │                 │         I was sick" (0.9)      │         │    │
│  │                 │                                 │         │    │
│  │                 │ Secret: [HIDDEN - protect son] │         │    │
│  │                 │                                 │         │    │
│  │                 │ Decision: DEFEND_MARCUS        │         │    │
│  │                 └─────────────────────────────────┘         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  UI CONTROLS:                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ [✓] Show Thought Bubbles    [✓] Show Memories Referenced   │     │
│  │ [✓] Show Emotional State    [ ] Show Secret Objectives     │     │
│  │ [✓] Show CoT Reasoning      [✓] Show Confidence Scores     │     │
│  │                                                            │     │
│  │ Filter: [All Agents ▼]  Detail Level: [Verbose ▼]          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```typescript
// ThoughtBubbleInspector.tsx

interface ThoughtBubble {
  agentId: string;
  agentName: string;
  position: { x: number; y: number };
  
  // Cognitive state
  cognitiveMode: 'IDLE' | 'REFLEX' | 'DELIBERATING' | 'ACTING';
  currentThought: string | null;
  
  // Reasoning chain (Chain-of-Thought)
  reasoningChain: ReasoningStep[];
  
  // Context being considered
  memoriesReferenced: MemoryReference[];
  relationshipsConsidered: RelationshipReference[];
  
  // Secret objective (optionally hidden)
  secretObjective: string | null;
  showSecret: boolean;
  
  // Emotional state
  emotionalState: string;
  emotionalIntensity: number;
  
  // Decision info
  pendingAction: Action | null;
  confidence: number;
  
  // Timing
  deliberationStartTick: number | null;
  estimatedCompletionTick: number | null;
}

interface ReasoningStep {
  stepNumber: number;
  content: string;
  type: 'observation' | 'memory_recall' | 'emotion' | 'inference' | 'decision';
  timestamp: number;
}

interface ThoughtBubbleInspectorProps {
  agents: Agent[];
  showThoughtBubbles: boolean;
  showMemories: boolean;
  showEmotions: boolean;
  showCoT: boolean;
  showSecrets: boolean;
  showConfidence: boolean;
  filterAgent: string | null;
  detailLevel: 'minimal' | 'standard' | 'verbose';
}

const ThoughtBubbleInspector: React.FC<ThoughtBubbleInspectorProps> = ({
  agents,
  showThoughtBubbles,
  showMemories,
  showEmotions,
  showCoT,
  showSecrets,
  showConfidence,
  filterAgent,
  detailLevel
}) => {
  const [bubbles, setBubbles] = useState<Map<string, ThoughtBubble>>(new Map());
  
  // Subscribe to thought updates via WebSocket
  useEffect(() => {
    const ws = new WebSocket('/ws/thoughts');
    
    ws.onmessage = (event) => {
      const update: ThoughtUpdate = JSON.parse(event.data);
      setBubbles(prev => {
        const next = new Map(prev);
        next.set(update.agentId, {
          ...next.get(update.agentId),
          ...update
        });
        return next;
      });
    };
    
    return () => ws.close();
  }, []);
  
  // Filter bubbles based on settings
  const visibleBubbles = useMemo(() => {
    return Array.from(bubbles.values()).filter(bubble => {
      if (!showThoughtBubbles) return false;
      if (filterAgent && bubble.agentId !== filterAgent) return false;
      if (bubble.cognitiveMode === 'IDLE' && detailLevel !== 'verbose') return false;
      return true;
    });
  }, [bubbles, showThoughtBubbles, filterAgent, detailLevel]);
  
  return (
    <div className="thought-bubble-overlay">
      {visibleBubbles.map(bubble => (
        <ThoughtBubbleComponent
          key={bubble.agentId}
          bubble={bubble}
          showMemories={showMemories}
          showEmotions={showEmotions}
          showCoT={showCoT}
          showSecrets={showSecrets}
          showConfidence={showConfidence}
          detailLevel={detailLevel}
        />
      ))}
    </div>
  );
};

const ThoughtBubbleComponent: React.FC<{
  bubble: ThoughtBubble;
  showMemories: boolean;
  showEmotions: boolean;
  showCoT: boolean;
  showSecrets: boolean;
  showConfidence: boolean;
  detailLevel: string;
}> = ({ bubble, showMemories, showEmotions, showCoT, showSecrets, showConfidence, detailLevel }) => {
  
  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'DELIBERATING': return '💭';
      case 'REFLEX': return '⚡';
      case 'ACTING': return '🎬';
      default: return '😐';
    }
  };
  
  const getModeLabel = (mode: string) => {
    switch (mode) {
      case 'DELIBERATING': return 'THINKING...';
      case 'REFLEX': return 'REACTING!';
      case 'ACTING': return 'ACTING';
      default: return 'IDLE';
    }
  };
  
  return (
    <div 
      className={`thought-bubble thought-bubble--${bubble.cognitiveMode.toLowerCase()}`}
      style={{
        left: bubble.position.x,
        top: bubble.position.y - 120, // Position above agent
      }}
    >
      <div className="thought-bubble__header">
        <span className="thought-bubble__icon">{getModeIcon(bubble.cognitiveMode)}</span>
        <span className="thought-bubble__mode">{getModeLabel(bubble.cognitiveMode)}</span>
      </div>
      
      {/* Current thought */}
      {bubble.currentThought && (
        <div className="thought-bubble__thought">
          "{bubble.currentThought}"
        </div>
      )}
      
      {/* Chain of Thought reasoning */}
      {showCoT && bubble.reasoningChain.length > 0 && (
        <div className="thought-bubble__cot">
          <div className="thought-bubble__cot-label">Reasoning:</div>
          {bubble.reasoningChain.slice(-3).map((step, i) => (
            <div key={i} className={`thought-bubble__cot-step thought-bubble__cot-step--${step.type}`}>
              {step.type === 'memory_recall' && '📚 '}
              {step.type === 'emotion' && '❤️ '}
              {step.type === 'inference' && '🔍 '}
              {step.type === 'decision' && '✅ '}
              {step.content}
            </div>
          ))}
        </div>
      )}
      
      {/* Memories being referenced */}
      {showMemories && bubble.memoriesReferenced.length > 0 && (
        <div className="thought-bubble__memories">
          <div className="thought-bubble__label">Memories:</div>
          {bubble.memoriesReferenced.map((mem, i) => (
            <div key={i} className="thought-bubble__memory">
              - {mem.summary} ({mem.importance.toFixed(1)})
            </div>
          ))}
        </div>
      )}
      
      {/* Secret objective (if enabled) */}
      {showSecrets && bubble.secretObjective && (
        <div className="thought-bubble__secret">
          <span className="thought-bubble__secret-label">Secret:</span>
          <span className="thought-bubble__secret-value">[{bubble.secretObjective}]</span>
        </div>
      )}
      
      {/* Emotional state */}
      {showEmotions && (
        <div className="thought-bubble__emotion">
          Emotion: <span className={`emotion emotion--${bubble.emotionalState.toLowerCase()}`}>
            {bubble.emotionalState}
          </span>
        </div>
      )}
      
      {/* Confidence score */}
      {showConfidence && bubble.pendingAction && (
        <div className="thought-bubble__confidence">
          Confidence: {(bubble.confidence * 100).toFixed(0)}%
        </div>
      )}
      
      {/* Pending action */}
      {bubble.pendingAction && (
        <div className="thought-bubble__action">
          Decision: <strong>{bubble.pendingAction.type}</strong>
          {bubble.pendingAction.target && ` → ${bubble.pendingAction.target}`}
        </div>
      )}
    </div>
  );
};
```

```python
# Backend support for Thought Bubble streaming

class ThoughtStreamManager:
    """
    Streams real-time thought updates to the Debug UI.
    """
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.active_subscriptions: Set[str] = set()
    
    async def broadcast_thought_update(
        self,
        agent: Agent,
        thought_data: dict
    ):
        """Broadcast thought update to all subscribed clients."""
        update = ThoughtUpdate(
            agentId=str(agent.id),
            agentName=agent.name,
            position={"x": agent.position[0], "y": agent.position[1]},
            cognitiveMode=agent.state.value.upper(),
            currentThought=thought_data.get("current_thought"),
            reasoningChain=thought_data.get("reasoning_chain", []),
            memoriesReferenced=thought_data.get("memories", []),
            secretObjective=self._get_secret_for_display(agent),
            emotionalState=agent.emotional_state,
            emotionalIntensity=agent.emotional_intensity,
            pendingAction=thought_data.get("pending_action"),
            confidence=thought_data.get("confidence", 0.0),
            deliberationStartTick=thought_data.get("start_tick"),
            estimatedCompletionTick=thought_data.get("estimated_end_tick")
        )
        
        await self.ws_manager.broadcast(
            channel="thoughts",
            message=update.dict()
        )
    
    def _get_secret_for_display(self, agent: Agent) -> Optional[str]:
        """Get secret objective summary for display (abbreviated)."""
        if hasattr(agent, 'secret_objective') and agent.secret_objective:
            # Return abbreviated version
            return agent.secret_objective.description[:50] + "..."
        return None


@dataclass
class ThoughtUpdate:
    """Structure for thought bubble updates."""
    agentId: str
    agentName: str
    position: dict
    cognitiveMode: str
    currentThought: Optional[str]
    reasoningChain: List[dict]
    memoriesReferenced: List[dict]
    secretObjective: Optional[str]
    emotionalState: str
    emotionalIntensity: float
    pendingAction: Optional[dict]
    confidence: float
    deliberationStartTick: Optional[int]
    estimatedCompletionTick: Optional[int]
```

### 7.5 World Tension Monitor & Aggressive Director (Narrative Quality Enhancement)

To prevent the "boring AI" problem where simulations settle into predictable equilibrium, the Drama Director continuously monitors a global `World_Tension_Level` metric and injects Catalyst Events when tension drops too low.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WORLD TENSION MONITOR SYSTEM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  World_Tension_Level: 0.0 ─────────────────────────────────── 1.0   │
│                       │                                       │     │
│                    BORING                                  CHAOTIC  │
│                       │                                       │     │
│                       ▼                                       ▼     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │░░░░░░░░░░░░░░░░░░░░████████████████████████░░░░░░░░░░░░░░░░│    │
│  │         0.3              0.5              0.8              │    │
│  │          │                │                │               │    │
│  │    CATALYST ZONE    IDEAL RANGE      COOL DOWN            │    │
│  │    (Inject drama)   (Let unfold)    (No injection)        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  If tension < 0.3 for > 60 seconds (1200 ticks):                    │
│  ───────────────────────────────────────────────                    │
│  Director MUST inject a Catalyst Event:                             │
│  • Misunderstanding between two agents                              │
│  • Rumor that contradicts established belief                        │
│  • Discovery of evidence (real or planted)                          │
│  • Unexpected arrival or departure                                  │
│  • Authority figure demands answers                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class TensionMonitorConfig:
    """Configuration for the World Tension Monitor."""
    
    # Tension thresholds
    catalyst_threshold: float = 0.3       # Below this, inject drama
    ideal_range_min: float = 0.3          # Ideal narrative tension range
    ideal_range_max: float = 0.8
    cooldown_threshold: float = 0.8       # Above this, let things calm
    
    # Timing
    catalyst_delay_ticks: int = 1200      # 60 seconds at 20 TPS
    cooldown_delay_ticks: int = 600       # 30 seconds
    measurement_window_ticks: int = 200   # 10 seconds rolling average
    
    # Injection limits
    max_catalysts_per_act: int = 3        # Don't over-inject
    min_ticks_between_catalysts: int = 1000  # 50 seconds minimum


class TensionMetricCalculator:
    """
    Calculates the global World_Tension_Level from simulation state.
    Combines multiple factors into a single 0.0-1.0 metric.
    """
    
    # Weight factors for tension calculation
    TENSION_WEIGHTS = {
        "active_conflicts": 0.25,         # Ongoing confrontations
        "accusation_severity": 0.20,      # Severity of current accusations
        "relationship_volatility": 0.15,  # Recent trust changes
        "gossip_velocity": 0.15,          # How fast rumors are spreading
        "secret_exposure_risk": 0.10,     # Secrets close to being revealed
        "physical_danger": 0.10,          # Threats to agent safety
        "authority_pressure": 0.05,       # Guards/Lords involved
    }
    
    def __init__(self, config: TensionMonitorConfig):
        self.config = config
        self.tension_history: List[Tuple[int, float]] = []
    
    def calculate_tension(self, world_state: WorldState) -> float:
        """
        Calculate current World_Tension_Level.
        Returns value between 0.0 and 1.0.
        """
        components = {}
        
        # Active conflicts
        components["active_conflicts"] = self._score_active_conflicts(world_state)
        
        # Accusation severity
        components["accusation_severity"] = self._score_accusations(world_state)
        
        # Relationship volatility
        components["relationship_volatility"] = self._score_relationship_changes(world_state)
        
        # Gossip velocity
        components["gossip_velocity"] = self._score_gossip_activity(world_state)
        
        # Secret exposure risk
        components["secret_exposure_risk"] = self._score_secret_risk(world_state)
        
        # Physical danger
        components["physical_danger"] = self._score_danger_level(world_state)
        
        # Authority pressure
        components["authority_pressure"] = self._score_authority_involvement(world_state)
        
        # Weighted sum
        tension = sum(
            score * self.TENSION_WEIGHTS[component]
            for component, score in components.items()
        )
        
        # Clamp to 0.0-1.0
        tension = max(0.0, min(1.0, tension))
        
        # Record for history
        self.tension_history.append((world_state.current_tick, tension))
        self._prune_history(world_state.current_tick)
        
        return tension
    
    def get_rolling_average(self, current_tick: int) -> float:
        """Get rolling average tension over measurement window."""
        cutoff = current_tick - self.config.measurement_window_ticks
        recent = [t for tick, t in self.tension_history if tick > cutoff]
        
        if not recent:
            return 0.5  # Default to middle
        
        return sum(recent) / len(recent)
    
    def _score_active_conflicts(self, world: WorldState) -> float:
        """Score based on ongoing confrontations."""
        conflicts = world.get_active_conflicts()
        
        if not conflicts:
            return 0.0
        
        # Score based on number and intensity of conflicts
        intensity_sum = sum(c.intensity for c in conflicts)
        return min(1.0, intensity_sum / 2.0)  # Cap at 2 high-intensity conflicts
    
    def _score_accusations(self, world: WorldState) -> float:
        """Score based on active accusations."""
        accusations = world.get_active_accusations()
        
        if not accusations:
            return 0.0
        
        # Weight by confidence and public knowledge
        score = 0.0
        for acc in accusations:
            base = acc.confidence * 0.5
            if acc.is_public:
                base *= 2.0  # Public accusations are more dramatic
            score += base
        
        return min(1.0, score)
    
    def _score_relationship_changes(self, world: WorldState) -> float:
        """Score based on recent relationship volatility."""
        recent_changes = world.get_recent_relationship_changes(
            window_ticks=self.config.measurement_window_ticks
        )
        
        if not recent_changes:
            return 0.0
        
        # Large changes in trust/affinity indicate drama
        total_delta = sum(abs(c.delta) for c in recent_changes)
        return min(1.0, total_delta / 2.0)
    
    def _score_gossip_activity(self, world: WorldState) -> float:
        """Score based on gossip propagation speed."""
        recent_gossip = world.get_recent_gossip_events(
            window_ticks=self.config.measurement_window_ticks
        )
        
        # More gossip = higher tension
        return min(1.0, len(recent_gossip) / 10.0)
    
    def _score_secret_risk(self, world: WorldState) -> float:
        """Score based on how close secrets are to exposure."""
        secrets = world.get_tracked_secrets()
        
        if not secrets:
            return 0.0
        
        # Higher score if secrets are close to revelation
        max_exposure_risk = max(s.exposure_risk for s in secrets)
        return max_exposure_risk
    
    def _score_danger_level(self, world: WorldState) -> float:
        """Score based on physical threats."""
        threatened_agents = [a for a in world.agents if a.is_threatened]
        return min(1.0, len(threatened_agents) / 3.0)
    
    def _score_authority_involvement(self, world: WorldState) -> float:
        """Score based on authority figure involvement."""
        authority_agents = ["guard_brennan", "lord_aldric"]
        
        active_authority = [
            a for a in world.agents 
            if a.role in authority_agents and a.state != "idle"
        ]
        
        # Authority investigating = tension
        investigating = any(
            a.current_action and "investigate" in a.current_action.type.lower()
            for a in active_authority
        )
        
        return 0.8 if investigating else 0.3 if active_authority else 0.0
    
    def _prune_history(self, current_tick: int):
        """Remove old history entries."""
        cutoff = current_tick - self.config.measurement_window_ticks * 2
        self.tension_history = [
            (tick, t) for tick, t in self.tension_history if tick > cutoff
        ]


class AggressiveDirector:
    """
    Drama Director that actively intervenes when narrative stalls.
    Injects Catalyst Events to maintain engagement.
    """
    
    def __init__(
        self,
        config: TensionMonitorConfig,
        tension_calculator: TensionMetricCalculator
    ):
        self.config = config
        self.tension = tension_calculator
        
        # Tracking
        self.low_tension_since: Optional[int] = None
        self.catalysts_injected_this_act: int = 0
        self.last_catalyst_tick: int = 0
        self.current_act: int = 1
    
    # Catalyst Event Templates
    CATALYST_TEMPLATES = {
        "misunderstanding": {
            "name": "Misunderstanding",
            "description": "Agent A misinterprets Agent B's actions",
            "tension_boost": 0.25,
            "implementation": "inject_misunderstanding",
            "requirements": ["two_interacting_agents"]
        },
        "contradictory_rumor": {
            "name": "Contradictory Rumor",
            "description": "A rumor emerges that contradicts established belief",
            "tension_boost": 0.30,
            "implementation": "inject_contradictory_rumor",
            "requirements": ["active_belief"]
        },
        "evidence_discovery": {
            "name": "Evidence Discovery",
            "description": "An agent discovers something significant",
            "tension_boost": 0.35,
            "implementation": "inject_evidence_discovery",
            "requirements": ["unresolved_mystery"]
        },
        "unexpected_arrival": {
            "name": "Unexpected Arrival",
            "description": "A relevant character arrives unexpectedly",
            "tension_boost": 0.20,
            "implementation": "inject_unexpected_arrival",
            "requirements": ["absent_relevant_agent"]
        },
        "authority_demand": {
            "name": "Authority Demands Answers",
            "description": "Lord or Guard demands immediate information",
            "tension_boost": 0.40,
            "implementation": "inject_authority_demand",
            "requirements": ["authority_available", "unresolved_issue"]
        },
        "witness_hesitation": {
            "name": "Witness Almost Speaks",
            "description": "Someone who knows the truth almost reveals it",
            "tension_boost": 0.30,
            "implementation": "inject_witness_hesitation",
            "requirements": ["agent_with_secret"]
        }
    }
    
    def tick(self, world_state: WorldState, current_tick: int):
        """
        Called every tick to monitor tension and potentially inject catalysts.
        """
        current_tension = self.tension.calculate_tension(world_state)
        rolling_avg = self.tension.get_rolling_average(current_tick)
        
        # Log tension for debugging
        if current_tick % 100 == 0:  # Every 5 seconds
            logger.debug(
                f"Tension Monitor: current={current_tension:.2f}, "
                f"rolling_avg={rolling_avg:.2f}"
            )
        
        # Check if we need to inject a catalyst
        if rolling_avg < self.config.catalyst_threshold:
            if self.low_tension_since is None:
                self.low_tension_since = current_tick
            
            elapsed_low = current_tick - self.low_tension_since
            
            if elapsed_low >= self.config.catalyst_delay_ticks:
                if self._can_inject_catalyst(current_tick):
                    catalyst = self._select_catalyst(world_state)
                    if catalyst:
                        self._inject_catalyst(catalyst, world_state, current_tick)
        else:
            self.low_tension_since = None
    
    def _can_inject_catalyst(self, current_tick: int) -> bool:
        """Check if catalyst injection is allowed."""
        # Check act limit
        if self.catalysts_injected_this_act >= self.config.max_catalysts_per_act:
            return False
        
        # Check cooldown
        if current_tick - self.last_catalyst_tick < self.config.min_ticks_between_catalysts:
            return False
        
        return True
    
    def _select_catalyst(self, world: WorldState) -> Optional[dict]:
        """
        Select the most appropriate catalyst for current situation.
        """
        available = []
        
        for catalyst_type, template in self.CATALYST_TEMPLATES.items():
            if self._check_requirements(template["requirements"], world):
                # Score based on tension boost and situation fit
                score = template["tension_boost"]
                
                # Prefer catalysts that fit the current narrative
                if self._fits_narrative(catalyst_type, world):
                    score *= 1.5
                
                available.append((catalyst_type, template, score))
        
        if not available:
            logger.warning("No suitable catalyst available")
            return None
        
        # Sort by score and pick best
        available.sort(key=lambda x: x[2], reverse=True)
        chosen_type, chosen_template, _ = available[0]
        
        return {
            "type": chosen_type,
            "template": chosen_template
        }
    
    def _check_requirements(self, requirements: List[str], world: WorldState) -> bool:
        """Check if catalyst requirements are met."""
        for req in requirements:
            if req == "two_interacting_agents":
                if len(world.get_interacting_pairs()) == 0:
                    return False
            elif req == "active_belief":
                if len(world.get_active_beliefs()) == 0:
                    return False
            elif req == "unresolved_mystery":
                if not world.has_unresolved_mystery():
                    return False
            elif req == "authority_available":
                if not world.is_authority_available():
                    return False
            elif req == "agent_with_secret":
                if len(world.get_agents_with_secrets()) == 0:
                    return False
        
        return True
    
    def _fits_narrative(self, catalyst_type: str, world: WorldState) -> bool:
        """Check if catalyst fits current narrative context."""
        # Implementation would check current act, recent events, etc.
        return True
    
    def _inject_catalyst(
        self, 
        catalyst: dict, 
        world: WorldState, 
        current_tick: int
    ):
        """Inject the selected catalyst into the simulation."""
        template = catalyst["template"]
        catalyst_type = catalyst["type"]
        
        logger.info(
            f"DIRECTOR: Injecting catalyst '{template['name']}' at tick {current_tick}"
        )
        
        # Call the appropriate injection method
        injection_method = getattr(self, f"_{template['implementation']}", None)
        
        if injection_method:
            event = injection_method(world)
            
            if event:
                world.inject_event(event)
                
                self.catalysts_injected_this_act += 1
                self.last_catalyst_tick = current_tick
                self.low_tension_since = None
                
                # Log for replay
                world.event_ledger.record(Event(
                    event_type=EventType.CATALYST_INJECTED,
                    tick=current_tick,
                    data={
                        "catalyst_type": catalyst_type,
                        "tension_before": self.tension.get_rolling_average(current_tick),
                        "expected_boost": template["tension_boost"]
                    }
                ))
    
    def _inject_misunderstanding(self, world: WorldState) -> Optional[Event]:
        """Create a misunderstanding between two agents."""
        pairs = world.get_interacting_pairs()
        if not pairs:
            return None
        
        agent_a, agent_b = pairs[0]
        
        return Event(
            event_type=EventType.MISUNDERSTANDING,
            agent_id=agent_a.id,
            target_ids=[agent_b.id],
            data={
                "type": "misinterpreted_action",
                "description": f"{agent_a.name} misunderstands {agent_b.name}'s intentions",
                "trust_impact": -0.2
            }
        )
    
    def _inject_authority_demand(self, world: WorldState) -> Optional[Event]:
        """Have authority figure demand answers."""
        authority = world.get_available_authority()
        if not authority:
            return None
        
        suspects = world.get_current_suspects()
        target = suspects[0] if suspects else world.get_random_relevant_agent()
        
        return Event(
            event_type=EventType.AUTHORITY_DEMAND,
            agent_id=authority.id,
            target_ids=[target.id],
            data={
                "type": "demand_answers",
                "description": f"{authority.name} demands {target.name} explain themselves",
                "urgency": "high"
            }
        )
    
    def _inject_witness_hesitation(self, world: WorldState) -> Optional[Event]:
        """Have a witness almost reveal what they know."""
        witnesses = world.get_agents_with_secrets()
        if not witnesses:
            return None
        
        witness = witnesses[0]
        
        return Event(
            event_type=EventType.WITNESS_HESITATION,
            agent_id=witness.id,
            data={
                "type": "almost_speaks",
                "description": f"{witness.name} starts to say something, then stops",
                "visible_to": world.get_nearby_agents(witness.id),
                "suspicion_generated": True
            }
        )
    
    def set_act(self, act_number: int):
        """Update current act and reset catalyst counter."""
        self.current_act = act_number
        self.catalysts_injected_this_act = 0
```

---

## 8. Technical Implementation

### 8.1 Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Runtime** | Python 3.11+ | Async support, LLM ecosystem |
| **Web Framework** | FastAPI | Async, WebSocket support, auto-docs |
| **Task Queue** | Celery + Redis | Async LLM calls, background jobs |
| **State DB** | PostgreSQL 15 | ACID, JSON support, mature |
| **Graph DB** | Neo4j 5.x | Relationship queries, Cypher |
| **Vector DB** | ChromaDB (MVP) | Local, simple, Python-native |
| **Event Stream** | Redis Streams | Ordered events, consumer groups |
| **LLM** | GLM Coding Plan (zai-coding-plan/glm-4.7) | Best reasoning capability |
| **Embeddings** | GLM Coding Plan (zai-coding-plan/glm-4.7) | Cost-effective, good quality |
| **Frontend** | React + D3.js | Debug UI visualization |

### 8.2 Project Structure

```
tsukuyomi/
├── src/
│   ├── core/
│   │   ├── simulation.py      # Main tick loop
│   │   ├── events.py          # Event types and queue
│   │   └── config.py          # Configuration management
│   │
│   ├── agents/
│   │   ├── agent.py           # Agent class
│   │   ├── reflexes.py        # System 1 rules
│   │   ├── deliberation.py    # System 2 LLM logic
│   │   └── personality.py     # Trait definitions
│   │
│   ├── memory/
│   │   ├── episodic.py        # Vector-based memory
│   │   ├── semantic.py        # Knowledge graph interface
│   │   └── retrieval.py       # Memory retrieval algorithms
│   │
│   ├── social/
│   │   ├── gossip.py          # Rumor propagation
│   │   ├── relationships.py   # Trust/affinity tracking
│   │   └── beliefs.py         # Belief formation/revision
│   │
│   ├── narrative/
│   │   ├── director.py        # Drama director (basic MVP)
│   │   └── catalysts.py       # Event injection
│   │
│   ├── data/
│   │   ├── postgres.py        # State store
│   │   ├── neo4j_client.py    # Graph queries
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   └── redis_client.py    # Event ledger
│   │
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   ├── websocket.py       # Real-time updates
│   │   └── routes/
│   │       ├── simulation.py  # Start/stop/status
│   │       ├── agents.py      # Agent inspection
│   │       └── debug.py       # Debug endpoints
│   │
│   └── demo/
│       ├── millbrook.py       # Demo scenario setup
│       ├── characters.py      # Character definitions
│       └── seeds.py           # Initial state seeds
│
├── ui/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VillageMap.tsx
│   │   │   ├── AgentInspector.tsx
│   │   │   ├── GossipTracker.tsx
│   │   │   ├── RelationshipGraph.tsx
│   │   │   └── EventTimeline.tsx
│   │   └── App.tsx
│   └── package.json
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── scenarios/
│       └── test_millbrook_demo.py
│
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
│
├── docs/
│   ├── API.md
│   └── DEVELOPMENT.md
│
└── requirements.txt
```

### 8.3 Key Implementation Details

#### 8.3.1 Agent State Machine

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import asyncio

class AgentState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    INTERACTING = "interacting"
    DELIBERATING = "deliberating"
    REACTING = "reacting"  # Executing reflex

@dataclass
class Agent:
    id: UUID
    name: str
    role: str
    
    # Physical state
    position: Tuple[float, float]
    current_location: str
    
    # Cognitive state
    state: AgentState
    current_action: Optional[Action]
    deliberation_task: Optional[asyncio.Task]
    
    # Personality (Big Five inspired)
    traits: PersonalityTraits
    
    # Memory references
    episodic_memory_id: str  # ChromaDB collection
    semantic_node_id: str    # Neo4j node ID
    
    # Social
    active_conversation: Optional[UUID]
    known_agents: Set[UUID]
    
    # Goals
    active_goals: List[Goal]
    
    def can_deliberate(self) -> bool:
        return (
            self.state not in [AgentState.REACTING, AgentState.DELIBERATING]
            and self.deliberation_task is None
        )

@dataclass
class PersonalityTraits:
    """Big Five personality model with game-relevant additions."""
    openness: float          # 0-1: Curiosity, creativity
    conscientiousness: float # 0-1: Organization, dependability
    extraversion: float      # 0-1: Sociability, assertiveness
    agreeableness: float     # 0-1: Cooperation, trust
    neuroticism: float       # 0-1: Emotional instability
    
    # Game-specific
    bravery: float           # 0-1: Willingness to face danger
    honesty: float           # 0-1: Truthfulness
    loyalty: float           # 0-1: Commitment to relationships
```

#### 8.3.2 Event System

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict
import json

class EventType(Enum):
    # World events
    TICK = "tick"
    WEATHER_CHANGE = "weather_change"
    TIME_ADVANCE = "time_advance"
    
    # Agent events
    AGENT_MOVED = "agent_moved"
    AGENT_SPOKE = "agent_spoke"
    AGENT_ACTION = "agent_action"
    AGENT_EMOTION = "agent_emotion"
    
    # Social events
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    GOSSIP_SHARED = "gossip_shared"
    RELATIONSHIP_CHANGED = "relationship_changed"
    
    # Cognitive events
    REFLEX_TRIGGERED = "reflex_triggered"
    DELIBERATION_START = "deliberation_start"
    DELIBERATION_COMPLETE = "deliberation_complete"
    DELIBERATION_PREEMPTED = "deliberation_preempted"
    
    # Narrative events
    CATALYST_INJECTED = "catalyst_injected"
    PLOT_POINT_REACHED = "plot_point_reached"

@dataclass
class Event:
    event_id: UUID
    event_type: EventType
    tick: int
    
    # Participants
    agent_id: Optional[UUID]
    target_ids: List[UUID]
    location: Optional[str]
    
    # Payload
    data: Dict[str, Any]
    
    # Metadata
    priority: int = 0
    global_relevance: bool = False
    
    def to_ledger_entry(self) -> str:
        return json.dumps({
            "id": str(self.event_id),
            "type": self.event_type.value,
            "tick": self.tick,
            "agent": str(self.agent_id) if self.agent_id else None,
            "targets": [str(t) for t in self.target_ids],
            "location": self.location,
            "data": self.data,
            "priority": self.priority
        })
```

#### 8.3.3 LLM Integration

```python
from langchain.chat_models import ChatGLM
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
import json

class ActionProposal(BaseModel):
    """Structured output from LLM deliberation."""
    action_type: str
    target: Optional[str]
    parameters: Dict[str, Any]
    reasoning: str
    emotional_state: str
    confidence: float
    new_belief: Optional[str]

class LLMDeliberator:
    def __init__(self, config: Config):
        self.llm = ChatGLM(
            model="zai-coding-plan/glm-4.7",
            temperature=0.7,
            max_tokens=500
        )
        self.token_budget = TokenBucket(
            capacity=config.token_budget_per_minute,
            refill_rate=config.token_budget_per_minute / 60
        )
    
    async def deliberate(
        self,
        agent: Agent,
        context: DeliberationContext
    ) -> Optional[ActionProposal]:
        
        # Check token budget
        estimated_tokens = self._estimate_tokens(context)
        if not self.token_budget.consume(estimated_tokens):
            return None  # Trigger fallback
        
        # Build messages
        system_prompt = self._build_system_prompt(agent)
        user_prompt = self._build_user_prompt(context)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.agenerate([messages])
            content = response.generations[0][0].text
            
            # Parse structured output
            proposal = ActionProposal.parse_raw(content)
            
            # Validate action is allowed
            if not self._validate_action(proposal, agent):
                return self._sanitize_action(proposal, agent)
            
            return proposal
            
        except Exception as e:
            logger.error(f"LLM deliberation failed: {e}")
            return None

class TokenBucket:
    """Rate limiting for LLM calls."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
```

#### 8.3.4 Circuit Breaker Patterns for LLM Failures

The system implements circuit breakers to gracefully handle LLM service failures and prevent cascading issues.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CIRCUIT BREAKER STATE MACHINE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                        ┌──────────────┐                             │
│                        │    CLOSED    │                             │
│                        │  (Normal Op) │                             │
│                        └──────┬───────┘                             │
│                               │                                     │
│                    failure_count >= threshold                       │
│                               │                                     │
│                               ▼                                     │
│                        ┌──────────────┐                             │
│                        │     OPEN     │◄────────────────────┐       │
│                        │ (Fail Fast)  │                     │       │
│                        └──────┬───────┘                     │       │
│                               │                             │       │
│                     timeout_elapsed                         │       │
│                               │                        failure      │
│                               ▼                             │       │
│                        ┌──────────────┐                     │       │
│                        │  HALF-OPEN   │─────────────────────┘       │
│                        │  (Testing)   │                             │
│                        └──────┬───────┘                             │
│                               │                                     │
│                      probe_success                                  │
│                               │                                     │
│                               ▼                                     │
│                        ┌──────────────┐                             │
│                        │    CLOSED    │                             │
│                        │  (Recovered) │                             │
│                        └──────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
import asyncio
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, no LLM calls
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Failure thresholds
    failure_threshold: int = 5          # Failures before opening
    failure_window_seconds: float = 60  # Time window for counting failures
    
    # Recovery settings
    recovery_timeout_seconds: float = 30  # Time before trying half-open
    half_open_max_calls: int = 3          # Test calls in half-open state
    success_threshold: int = 2            # Successes needed to close
    
    # Failure classification
    timeout_ms: int = 10000              # LLM call timeout
    retriable_exceptions: tuple = (
        "RateLimitError",
        "ServiceUnavailableError", 
        "TimeoutError"
    )
    
    # Fallback behavior
    fallback_mode: str = "heuristic"     # "heuristic", "cached", "queue"

class LLMCircuitBreaker:
    """
    Circuit breaker for LLM service calls.
    Prevents cascade failures and enables graceful degradation.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        
        # Failure tracking
        self.failures: List[float] = []  # Timestamps of recent failures
        self.last_failure_time: Optional[float] = None
        
        # Half-open tracking
        self.half_open_calls: int = 0
        self.half_open_successes: int = 0
        
        # Metrics
        self.total_calls: int = 0
        self.total_failures: int = 0
        self.total_fallbacks: int = 0
        self.state_changes: List[Tuple[float, CircuitState]] = []
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_fallback: Optional[Callable] = None
    
    async def call(
        self,
        llm_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ):
        """
        Execute LLM call with circuit breaker protection.
        Returns LLM result or fallback result.
        """
        self.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                # Fail fast
                self.total_fallbacks += 1
                return await self._execute_fallback(fallback_func, *args, **kwargs)
        
        # Attempt LLM call
        try:
            result = await asyncio.wait_for(
                llm_func(*args, **kwargs),
                timeout=self.config.timeout_ms / 1000
            )
            
            self._record_success()
            return result
            
        except Exception as e:
            self._record_failure(e)
            
            # Determine if we should use fallback
            if self.state == CircuitState.OPEN:
                self.total_fallbacks += 1
                return await self._execute_fallback(fallback_func, *args, **kwargs)
            
            # Re-raise if not a retriable exception
            if type(e).__name__ not in self.config.retriable_exceptions:
                raise
            
            self.total_fallbacks += 1
            return await self._execute_fallback(fallback_func, *args, **kwargs)
    
    def _record_success(self):
        """Record successful LLM call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            self.half_open_calls += 1
            
            if self.half_open_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        
        elif self.state == CircuitState.CLOSED:
            # Clear old failures outside the window
            self._prune_old_failures()
    
    def _record_failure(self, exception: Exception):
        """Record failed LLM call and potentially open circuit."""
        now = time.time()
        self.failures.append(now)
        self.last_failure_time = now
        self.total_failures += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            self._transition_to(CircuitState.OPEN)
            return
        
        if self.state == CircuitState.CLOSED:
            # Check if we've exceeded threshold
            self._prune_old_failures()
            if len(self.failures) >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
    
    def _prune_old_failures(self):
        """Remove failures outside the time window."""
        cutoff = time.time() - self.config.failure_window_seconds
        self.failures = [f for f in self.failures if f > cutoff]
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.recovery_timeout_seconds
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new circuit state."""
        old_state = self.state
        self.state = new_state
        
        if new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0
            self.half_open_successes = 0
        
        if new_state == CircuitState.CLOSED:
            self.failures.clear()
        
        self.state_changes.append((time.time(), new_state))
        
        if self.on_state_change:
            self.on_state_change(old_state, new_state)
        
        logger.warning(f"Circuit breaker: {old_state.value} -> {new_state.value}")
    
    async def _execute_fallback(
        self,
        fallback_func: Callable,
        *args,
        **kwargs
    ):
        """Execute fallback function when circuit is open."""
        if self.on_fallback:
            self.on_fallback()
        
        return await fallback_func(*args, **kwargs)
    
    def get_metrics(self) -> dict:
        """Return circuit breaker metrics for monitoring."""
        return {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_fallbacks": self.total_fallbacks,
            "failure_rate": self.total_failures / max(1, self.total_calls),
            "recent_failures": len(self.failures),
            "last_failure_time": self.last_failure_time,
            "state_changes": len(self.state_changes)
        }


class MultiProviderCircuitBreaker:
    """
    Circuit breaker with automatic provider failover.
    Manages multiple LLM providers with independent health tracking.
    """
    
    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers
        self.circuits = {
            p.name: LLMCircuitBreaker(p.circuit_config) 
            for p in providers
        }
        self.primary_provider = providers[0].name
        self.current_provider = self.primary_provider
    
    async def call(
        self,
        agent: Agent,
        context: DeliberationContext,
        fallback_func: Callable
    ):
        """
        Call LLM with automatic provider failover.
        """
        # Try providers in order until one succeeds
        for provider in self._get_available_providers():
            circuit = self.circuits[provider.name]
            
            if circuit.state != CircuitState.OPEN:
                try:
                    result = await circuit.call(
                        provider.deliberate,
                        fallback_func,
                        agent,
                        context
                    )
                    self.current_provider = provider.name
                    return result
                except Exception:
                    continue
        
        # All providers failed
        logger.error("All LLM providers unavailable, using fallback")
        return await fallback_func(agent, context)
    
    def _get_available_providers(self) -> List[LLMProvider]:
        """Get providers sorted by preference and health."""
        def score(provider):
            circuit = self.circuits[provider.name]
            # Prefer: closed circuits, then primary provider
            state_score = {
                CircuitState.CLOSED: 100,
                CircuitState.HALF_OPEN: 50,
                CircuitState.OPEN: 0
            }[circuit.state]
            primary_bonus = 10 if provider.name == self.primary_provider else 0
            return state_score + primary_bonus
        
        return sorted(self.providers, key=score, reverse=True)


# Configuration for different failure scenarios
CIRCUIT_BREAKER_CONFIGS = {
    "default": CircuitBreakerConfig(
        failure_threshold=5,
        failure_window_seconds=60,
        recovery_timeout_seconds=30,
        timeout_ms=10000
    ),
    
    "aggressive": CircuitBreakerConfig(
        # Opens faster, recovers faster (for demos)
        failure_threshold=3,
        failure_window_seconds=30,
        recovery_timeout_seconds=15,
        timeout_ms=5000
    ),
    
    "conservative": CircuitBreakerConfig(
        # More tolerant, slower recovery (for production)
        failure_threshold=10,
        failure_window_seconds=120,
        recovery_timeout_seconds=60,
        timeout_ms=15000
    )
}
```

#### 8.3.5 Degradation Hierarchy

When circuit breakers trigger, the system follows this fallback hierarchy:

```python
DEGRADATION_HIERARCHY = {
    "level_1": {
        "name": "Provider Failover",
        "trigger": "Primary LLM provider circuit open",
        "action": "Switch to secondary GLM Coding Plan provider (e.g., zai-coding-plan/glm-4.7-backup)",
        "impact": "None visible, slightly different response style"
    },
    
    "level_2": {
        "name": "Cached Response",
        "trigger": "All LLM providers unavailable, <30s",
        "action": "Use cached responses for similar situations",
        "impact": "Less creative responses, may repeat patterns"
    },
    
    "level_3": {
        "name": "Heuristic Mode",
        "trigger": "All LLM providers unavailable, >30s",
        "action": "Switch to personality-weighted heuristics",
        "impact": "Simpler decisions, agents feel less 'alive'"
    },
    
    "level_4": {
        "name": "Reflex Only",
        "trigger": "Extended outage, >5min",
        "action": "Disable all deliberation, reflex-only behavior",
        "impact": "Minimal agent intelligence, demo may stall"
    },
    
    "level_5": {
        "name": "Simulation Pause",
        "trigger": "Critical failure, unable to maintain coherence",
        "action": "Pause simulation, notify operator",
        "impact": "Demo stops, requires manual intervention"
    }
}
```

#### 8.3.6 Pre-Action Validation Gate (HIGH PRIORITY)

Before any LLM-generated action is committed to world state, it must pass through a Validation Gate that ensures the action is still valid given the current world state. This prevents stale decisions from causing incoherent behaviors.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PRE-ACTION VALIDATION GATE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │    LLM      │     │ VALIDATION  │     │   STATE     │           │
│  │   OUTPUT    │────►│    GATE     │────►│  COMMIT     │           │
│  │  (Proposal) │     │             │     │             │           │
│  └─────────────┘     └──────┬──────┘     └─────────────┘           │
│                             │                                       │
│                      ┌──────┴──────┐                                │
│                      │   INVALID   │                                │
│                      │   ACTION    │                                │
│                      └──────┬──────┘                                │
│                             │                                       │
│                             ▼                                       │
│                      ┌─────────────┐     ┌─────────────┐           │
│                      │ FAIL STATE  │────►│  RECOVERY   │           │
│                      │ ANIMATION   │     │  HEURISTIC  │           │
│                      └─────────────┘     └──────┬──────┘           │
│                                                 │                   │
│                                                 ▼                   │
│                                          ┌─────────────┐           │
│                                          │  System 1   │           │
│                                          │  FALLBACK   │           │
│                                          │  (Immediate)│           │
│                                          └─────────────┘           │
│                                                                     │
│  Validation Checks:                                                 │
│  • Target still exists?                                             │
│  • Target still in range? (distance < action.required_range)        │
│  • Required conditions still met?                                   │
│  • Agent still has required resources/state?                        │
│  • No conflicting actions in progress?                              │
│                                                                     │
│  Recovery Heuristic (NEW):                                          │
│  ═════════════════════════                                          │
│  When validation fails, do NOT just play a fail animation and idle. │
│  Instead, trigger an immediate System 1 fallback to resolve state:  │
│                                                                     │
│  • target_out_of_range → MoveTo(target) to close distance          │
│  • target_not_found → LookAround() then re-evaluate goals          │
│  • path_blocked → FindAlternatePath() or Wait(short_duration)      │
│  • target_unavailable → Observe(target) until available            │
│                                                                     │
│  This ensures agents attempt to complete their intent rather than   │
│  standing idle after failed actions, maintaining narrative flow.    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class ValidationResult:
    """Result of pre-action validation."""
    valid: bool
    failure_reason: Optional[str] = None
    recovery_action: Optional[Action] = None
    fail_state_animation: Optional[str] = None


class PreActionValidator:
    """
    Validates LLM-generated actions before state commitment.
    Prevents stale decisions from causing incoherent behaviors.
    """
    
    # Validation rules for each action type
    # NOTE: recovery_heuristic is the System 1 fallback that attempts to resolve
    # the failed state rather than just standing idle (see Recovery Heuristic above)
    VALIDATION_RULES = {
        "SPEAK_TO": {
            "checks": ["target_exists", "target_in_range", "target_available"],
            "required_range": 5.0,  # meters
            "fail_animation": "confused_look_around",
            "recovery": "IDLE",
            "recovery_heuristic": "MOVE_TO_TARGET"  # Try to close distance first
        },
        "GIVE_ITEM": {
            "checks": ["target_exists", "target_in_range", "has_item", "target_can_receive"],
            "required_range": 2.0,
            "fail_animation": "shrug_confused",
            "recovery": "IDLE",
            "recovery_heuristic": "MOVE_TO_TARGET"
        },
        "MOVE_TO": {
            "checks": ["destination_exists", "path_valid"],
            "fail_animation": "hesitate",
            "recovery": "IDLE",
            "recovery_heuristic": "FIND_ALTERNATE_PATH"
        },
        "ATTACK": {
            "checks": ["target_exists", "target_in_range", "target_hostile", "has_weapon"],
            "required_range": 3.0,
            "fail_animation": "combat_stance_break",
            "recovery": "DEFENSIVE_STANCE",
            "recovery_heuristic": "PURSUE_TARGET"
        },
        "SHARE_GOSSIP": {
            "checks": ["target_exists", "target_in_range", "has_gossip", "not_recently_shared"],
            "required_range": 3.0,
            "fail_animation": "mouth_open_close",
            "recovery": "IDLE",
            "recovery_heuristic": "MOVE_TO_TARGET"
        },
        "CONFRONT": {
            "checks": ["target_exists", "target_in_range", "has_accusation"],
            "required_range": 4.0,
            "fail_animation": "frustrated_gesture",
            "recovery": "OBSERVE",
            "recovery_heuristic": "FOLLOW_TARGET"
        }
    }
    
    # Fail state animations that mask validation failures
    FAIL_ANIMATIONS = {
        "confused_look_around": {
            "duration_ticks": 40,
            "description": "Agent looks around confused, as if searching for someone",
            "emote": "CONFUSED"
        },
        "shrug_confused": {
            "duration_ticks": 30,
            "description": "Agent shrugs, pats pockets, looks uncertain",
            "emote": "PUZZLED"
        },
        "hesitate": {
            "duration_ticks": 20,
            "description": "Agent pauses, reconsiders direction",
            "emote": "THOUGHTFUL"
        },
        "combat_stance_break": {
            "duration_ticks": 25,
            "description": "Agent drops combat stance, looks around warily",
            "emote": "ALERT"
        },
        "mouth_open_close": {
            "duration_ticks": 15,
            "description": "Agent starts to speak, then stops",
            "emote": "HESITANT"
        },
        "frustrated_gesture": {
            "duration_ticks": 35,
            "description": "Agent makes frustrated gesture, crosses arms",
            "emote": "FRUSTRATED"
        }
    }
    
    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.validation_failures = 0
        self.validation_successes = 0
    
    def validate_action(
        self,
        agent: Agent,
        proposal: Proposal,
        world_snapshot: WorldState
    ) -> ValidationResult:
        """
        Validate a proposed action against current world state.
        Returns validation result with recovery action if invalid.
        """
        action = proposal.action
        rules = self.VALIDATION_RULES.get(action.type, {})
        checks = rules.get("checks", [])
        
        for check in checks:
            result = self._run_check(check, agent, action, rules, world_snapshot)
            if not result.valid:
                self.validation_failures += 1
                
                # Log for debugging
                logger.warning(
                    f"Action validation failed: agent={agent.name}, "
                    f"action={action.type}, reason={result.failure_reason}"
                )
                
                # Record metric
                self._record_failure(agent.id, action.type, result.failure_reason)
                
                return result
        
        self.validation_successes += 1
        return ValidationResult(valid=True)
    
    def _run_check(
        self,
        check_name: str,
        agent: Agent,
        action: Action,
        rules: dict,
        world: WorldState
    ) -> ValidationResult:
        """Run a specific validation check."""
        
        check_methods = {
            "target_exists": self._check_target_exists,
            "target_in_range": self._check_target_in_range,
            "target_available": self._check_target_available,
            "target_can_receive": self._check_target_can_receive,
            "target_hostile": self._check_target_hostile,
            "destination_exists": self._check_destination_exists,
            "path_valid": self._check_path_valid,
            "has_item": self._check_has_item,
            "has_weapon": self._check_has_weapon,
            "has_gossip": self._check_has_gossip,
            "has_accusation": self._check_has_accusation,
            "not_recently_shared": self._check_not_recently_shared,
        }
        
        check_fn = check_methods.get(check_name)
        if not check_fn:
            logger.error(f"Unknown validation check: {check_name}")
            return ValidationResult(valid=True)  # Fail open for unknown checks
        
        return check_fn(agent, action, rules, world)
    
    def _check_target_exists(
        self, agent: Agent, action: Action, rules: dict, world: WorldState
    ) -> ValidationResult:
        """Check if target agent/entity still exists in world."""
        if action.target is None:
            return ValidationResult(
                valid=False,
                failure_reason="no_target_specified",
                fail_state_animation=rules.get("fail_animation"),
                recovery_action=Action(type=rules.get("recovery", "IDLE"))
            )
        
        target = world.get_entity(action.target)
        if target is None:
            return ValidationResult(
                valid=False,
                failure_reason="target_not_found",
                fail_state_animation=rules.get("fail_animation"),
                recovery_action=Action(type=rules.get("recovery", "IDLE"))
            )
        
        return ValidationResult(valid=True)
    
    def _check_target_in_range(
        self, agent: Agent, action: Action, rules: dict, world: WorldState
    ) -> ValidationResult:
        """Check if target is within required range."""
        required_range = rules.get("required_range", 5.0)
        target = world.get_entity(action.target)
        
        if target is None:
            return ValidationResult(valid=False, failure_reason="target_not_found")
        
        distance = self._calculate_distance(agent.position, target.position)
        
        if distance > required_range:
            return ValidationResult(
                valid=False,
                failure_reason=f"target_out_of_range (distance={distance:.1f}m, required={required_range}m)",
                fail_state_animation=rules.get("fail_animation"),
                recovery_action=Action(
                    type="MOVE_TO",
                    target=action.target,
                    parameters={"reason": "close_distance_for_action"}
                )
            )
        
        return ValidationResult(valid=True)
    
    def _check_target_available(
        self, agent: Agent, action: Action, rules: dict, world: WorldState
    ) -> ValidationResult:
        """Check if target is available for interaction (not in combat, conversation, etc.)."""
        target = world.get_entity(action.target)
        
        if target and hasattr(target, 'state'):
            unavailable_states = ['COMBAT', 'FLEEING', 'UNCONSCIOUS', 'BUSY']
            if target.state in unavailable_states:
                return ValidationResult(
                    valid=False,
                    failure_reason=f"target_unavailable (state={target.state})",
                    fail_state_animation=rules.get("fail_animation"),
                    recovery_action=Action(type="OBSERVE", target=action.target)
                )
        
        return ValidationResult(valid=True)
    
    def _calculate_distance(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _record_failure(self, agent_id: UUID, action_type: str, reason: str):
        """Record validation failure for metrics."""
        # Implementation would log to metrics system
        pass
    
    def get_metrics(self) -> dict:
        """Return validation metrics."""
        total = self.validation_successes + self.validation_failures
        return {
            "total_validations": total,
            "successes": self.validation_successes,
            "failures": self.validation_failures,
            "failure_rate": self.validation_failures / max(1, total)
        }


class FailStateAnimationManager:
    """
    Manages fail state animations that mask validation failures.
    Makes failed actions look natural rather than glitchy.
    """
    
    def __init__(self):
        self.active_animations: Dict[UUID, FailAnimation] = {}
    
    def trigger_fail_animation(
        self,
        agent: Agent,
        animation_name: str,
        validation_result: ValidationResult
    ):
        """Trigger a fail state animation for an agent."""
        animation_config = PreActionValidator.FAIL_ANIMATIONS.get(animation_name)
        
        if not animation_config:
            logger.warning(f"Unknown fail animation: {animation_name}")
            return
        
        animation = FailAnimation(
            agent_id=agent.id,
            animation_type=animation_name,
            duration_ticks=animation_config["duration_ticks"],
            emote=animation_config["emote"],
            start_tick=self.current_tick,
            reason=validation_result.failure_reason
        )
        
        self.active_animations[agent.id] = animation
        
        # Emit animation event for UI
        self.emit_event(Event(
            event_type=EventType.AGENT_EMOTION,
            agent_id=agent.id,
            data={
                "animation": animation_name,
                "emote": animation_config["emote"],
                "duration": animation_config["duration_ticks"]
            }
        ))
    
    def tick(self):
        """Update active animations."""
        completed = []
        
        for agent_id, animation in self.active_animations.items():
            animation.elapsed_ticks += 1
            
            if animation.elapsed_ticks >= animation.duration_ticks:
                completed.append(agent_id)
        
        for agent_id in completed:
            del self.active_animations[agent_id]


@dataclass
class FailAnimation:
    """Represents an active fail state animation."""
    agent_id: UUID
    animation_type: str
    duration_ticks: int
    emote: str
    start_tick: int
    reason: str
    elapsed_ticks: int = 0


class RecoveryHeuristicManager:
    """
    Manages System 1 recovery actions when validation fails.
    
    Instead of leaving agents idle after a failed action, this manager
    triggers immediate fallback behaviors that attempt to resolve the
    failed state and maintain narrative continuity.
    
    This addresses "The Confused Room" risk where agents stand idle
    after stale LLM decisions fail validation.
    """
    
    # Recovery heuristics map failure reasons to System 1 actions
    RECOVERY_HEURISTICS = {
        "target_out_of_range": {
            "action_type": "MOVE_TO",
            "description": "Close distance to target",
            "priority": 60,
            "max_attempts": 3,
            "timeout_ticks": 200
        },
        "target_not_found": {
            "action_type": "LOOK_AROUND",
            "description": "Search for missing target",
            "priority": 50,
            "max_attempts": 2,
            "timeout_ticks": 100,
            "follow_up": "RE_EVALUATE_GOALS"
        },
        "path_blocked": {
            "action_type": "FIND_ALTERNATE_PATH",
            "description": "Attempt alternate route",
            "priority": 55,
            "max_attempts": 2,
            "timeout_ticks": 150,
            "fallback": "WAIT_SHORT"
        },
        "target_unavailable": {
            "action_type": "OBSERVE",
            "description": "Wait and observe until target is available",
            "priority": 40,
            "max_attempts": 5,
            "timeout_ticks": 300
        },
        "no_target_specified": {
            "action_type": "RE_EVALUATE_GOALS",
            "description": "Re-assess current goals",
            "priority": 30,
            "max_attempts": 1,
            "timeout_ticks": 50
        }
    }
    
    def __init__(self, reflex_library: ReflexLibrary):
        self.reflex_library = reflex_library
        self.active_recoveries: Dict[UUID, RecoveryAttempt] = {}
        self.recovery_successes = 0
        self.recovery_failures = 0
    
    def trigger_recovery(
        self,
        agent: Agent,
        validation_result: ValidationResult,
        original_action: Action
    ) -> Action:
        """
        Trigger an immediate System 1 recovery action.
        
        Called when validation fails to prevent the agent from
        standing idle with a "confused" expression indefinitely.
        """
        failure_reason = self._categorize_failure(validation_result.failure_reason)
        heuristic = self.RECOVERY_HEURISTICS.get(failure_reason)
        
        if not heuristic:
            # Unknown failure type - fall back to re-evaluating goals
            logger.warning(f"Unknown failure reason: {failure_reason}, using default recovery")
            heuristic = self.RECOVERY_HEURISTICS["no_target_specified"]
        
        # Check if we've exceeded max attempts for this recovery
        existing_recovery = self.active_recoveries.get(agent.id)
        if existing_recovery and existing_recovery.failure_reason == failure_reason:
            existing_recovery.attempts += 1
            if existing_recovery.attempts >= heuristic["max_attempts"]:
                # Recovery failed - use fallback or give up
                self.recovery_failures += 1
                if "fallback" in heuristic:
                    return Action(type=heuristic["fallback"])
                else:
                    # Clear recovery state and return to goal evaluation
                    del self.active_recoveries[agent.id]
                    return Action(type="RE_EVALUATE_GOALS")
        else:
            # Start new recovery attempt
            self.active_recoveries[agent.id] = RecoveryAttempt(
                agent_id=agent.id,
                failure_reason=failure_reason,
                original_action=original_action,
                started_tick=self.current_tick,
                timeout_tick=self.current_tick + heuristic["timeout_ticks"],
                attempts=1
            )
        
        # Build and return the recovery action
        recovery_action = self._build_recovery_action(
            agent, heuristic, original_action, validation_result
        )
        
        logger.info(
            f"Recovery triggered for {agent.name}: "
            f"{failure_reason} -> {recovery_action.type}"
        )
        
        return recovery_action
    
    def _categorize_failure(self, failure_reason: str) -> str:
        """Categorize failure reason into a recovery heuristic key."""
        if "out_of_range" in failure_reason:
            return "target_out_of_range"
        elif "not_found" in failure_reason:
            return "target_not_found"
        elif "blocked" in failure_reason or "path" in failure_reason:
            return "path_blocked"
        elif "unavailable" in failure_reason:
            return "target_unavailable"
        else:
            return "no_target_specified"
    
    def _build_recovery_action(
        self,
        agent: Agent,
        heuristic: dict,
        original_action: Action,
        validation_result: ValidationResult
    ) -> Action:
        """Build the appropriate recovery action based on heuristic."""
        action_type = heuristic["action_type"]
        
        if action_type == "MOVE_TO" and original_action.target:
            return Action(
                type="MOVE_TO",
                target=original_action.target,
                parameters={
                    "reason": "recovery_close_distance",
                    "original_intent": original_action.type,
                    "priority": heuristic["priority"]
                }
            )
        elif action_type == "LOOK_AROUND":
            return Action(
                type="LOOK_AROUND",
                parameters={
                    "reason": "recovery_search_target",
                    "search_for": original_action.target,
                    "duration_ticks": 60
                }
            )
        elif action_type == "OBSERVE" and original_action.target:
            return Action(
                type="OBSERVE",
                target=original_action.target,
                parameters={
                    "reason": "recovery_wait_for_target",
                    "original_intent": original_action.type
                }
            )
        elif action_type == "FIND_ALTERNATE_PATH":
            return Action(
                type="MOVE_TO",
                target=original_action.target,
                parameters={
                    "reason": "recovery_alternate_path",
                    "avoid_current_path": True
                }
            )
        else:
            return Action(
                type="RE_EVALUATE_GOALS",
                parameters={"reason": "recovery_fallback"}
            )
    
    def check_recovery_complete(self, agent: Agent) -> bool:
        """Check if recovery was successful and clear state."""
        recovery = self.active_recoveries.get(agent.id)
        if not recovery:
            return True
        
        # Check timeout
        if self.current_tick >= recovery.timeout_tick:
            self.recovery_failures += 1
            del self.active_recoveries[agent.id]
            return True
        
        # Recovery still in progress
        return False
    
    def mark_recovery_success(self, agent_id: UUID):
        """Mark recovery as successful."""
        if agent_id in self.active_recoveries:
            self.recovery_successes += 1
            del self.active_recoveries[agent_id]


@dataclass
class RecoveryAttempt:
    """Tracks an active recovery attempt."""
    agent_id: UUID
    failure_reason: str
    original_action: Action
    started_tick: int
    timeout_tick: int
    attempts: int = 1
```

### 8.4 Database Schemas

#### PostgreSQL (Canonical State)

```sql
-- Core tables for MVP

CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    
    -- Position
    pos_x FLOAT NOT NULL,
    pos_y FLOAT NOT NULL,
    current_location VARCHAR(100),
    
    -- State
    state VARCHAR(20) NOT NULL DEFAULT 'idle',
    current_action JSONB,
    
    -- Personality (Big Five + custom)
    traits JSONB NOT NULL,
    
    -- Concurrency
    version INT NOT NULL DEFAULT 1,
    last_tick_updated BIGINT NOT NULL DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_goals (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    goal_type VARCHAR(50) NOT NULL,
    description TEXT,
    priority INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_tick BIGINT NOT NULL,
    completed_tick BIGINT
);

CREATE TABLE simulation_state (
    id SERIAL PRIMARY KEY,
    current_tick BIGINT NOT NULL DEFAULT 0,
    time_of_day VARCHAR(20) NOT NULL DEFAULT 'morning',
    weather VARCHAR(20) NOT NULL DEFAULT 'clear',
    status VARCHAR(20) NOT NULL DEFAULT 'paused',
    started_at TIMESTAMP,
    config JSONB
);

CREATE TABLE event_log (
    id UUID PRIMARY KEY,
    tick BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_event_log_tick ON event_log(tick);
CREATE INDEX idx_event_log_agent ON event_log(agent_id);
```

#### Neo4j (Knowledge Graph)

```cypher
// Constraint and index setup
CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT rumor_hash IF NOT EXISTS FOR (r:Rumor) REQUIRE r.content_hash IS UNIQUE;

// Index for fast lookups
CREATE INDEX agent_name IF NOT EXISTS FOR (a:Agent) ON (a.name);

// Sample data structure for Millbrook demo
// (Actual data loaded via Python scripts)

// Locations
CREATE (tavern:Location {id: 'tavern', name: 'The Rusty Nail', type: 'social'})
CREATE (market:Location {id: 'market', name: 'Market Square', type: 'commerce'})
CREATE (church:Location {id: 'church', name: 'Village Church', type: 'religious'})
CREATE (manor:Location {id: 'manor', name: 'Lord\'s Manor', type: 'noble'})
CREATE (blacksmith:Location {id: 'blacksmith', name: 'Forge', type: 'craft'})

// Location connections
CREATE (tavern)-[:CONNECTED_TO {distance: 50}]->(market)
CREATE (market)-[:CONNECTED_TO {distance: 100}]->(church)
CREATE (market)-[:CONNECTED_TO {distance: 75}]->(blacksmith)
CREATE (church)-[:CONNECTED_TO {distance: 150}]->(manor)

// Relationship queries
// Get all agents who distrust Marcus
MATCH (a:Agent)-[r:TRUSTS]->(marcus:Agent {name: 'Marcus'})
WHERE r.weight < 0
RETURN a.name, r.weight

// Get gossip propagation path
MATCH path = (source:Agent)-[:TOLD_RUMOR*1..3]->(target:Agent)
WHERE source.name = 'Elena'
RETURN path

// Find agents with conflicting beliefs
MATCH (a1:Agent)-[:BELIEVES {confidence: c1}]->(r:Rumor),
      (a2:Agent)-[:BELIEVES {confidence: c2}]->(r)
WHERE c1 > 0.5 AND c2 > 0.5 AND a1 <> a2
RETURN a1.name, a2.name, r.content
```

---

## 9. API Contracts

### 9.1 REST Endpoints

```yaml
openapi: 3.0.0
info:
  title: Tsukuyomi MVP API
  version: 1.0.0

paths:
  /simulation/start:
    post:
      summary: Start the simulation
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                scenario:
                  type: string
                  default: "millbrook"
                tick_rate:
                  type: integer
                  default: 20
      responses:
        200:
          description: Simulation started
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string }
                  simulation_id: { type: string }

  /simulation/stop:
    post:
      summary: Stop the simulation
      responses:
        200:
          description: Simulation stopped

  /simulation/status:
    get:
      summary: Get simulation status
      responses:
        200:
          description: Current simulation state
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [running, paused, stopped] }
                  current_tick: { type: integer }
                  agent_count: { type: integer }
                  time_of_day: { type: string }

  /agents:
    get:
      summary: List all agents
      responses:
        200:
          description: List of agents
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AgentSummary'

  /agents/{agent_id}:
    get:
      summary: Get agent details
      parameters:
        - name: agent_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Agent details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentDetail'

  /agents/{agent_id}/memories:
    get:
      summary: Get agent's recent memories
      parameters:
        - name: agent_id
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        200:
          description: Agent memories
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Memory'

  /agents/{agent_id}/relationships:
    get:
      summary: Get agent's relationships
      responses:
        200:
          description: Agent relationships
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Relationship'

  /gossip:
    get:
      summary: Get active rumors
      responses:
        200:
          description: Active rumors in simulation
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Rumor'

  /events:
    get:
      summary: Get recent events
      parameters:
        - name: since_tick
          in: query
          schema:
            type: integer
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        200:
          description: Recent events
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Event'

components:
  schemas:
    AgentSummary:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
        role: { type: string }
        state: { type: string }
        position: 
          type: object
          properties:
            x: { type: number }
            y: { type: number }
        current_location: { type: string }

    AgentDetail:
      allOf:
        - $ref: '#/components/schemas/AgentSummary'
        - type: object
          properties:
            traits:
              type: object
              properties:
                openness: { type: number }
                conscientiousness: { type: number }
                extraversion: { type: number }
                agreeableness: { type: number }
                neuroticism: { type: number }
            current_thought: { type: string }
            emotional_state: { type: string }
            active_goals:
              type: array
              items:
                type: string

    Memory:
      type: object
      properties:
        id: { type: string }
        what: { type: string }
        who: { type: array, items: { type: string } }
        when: { type: integer }
        where: { type: string }
        importance: { type: number }
        emotional_valence: { type: number }

    Relationship:
      type: object
      properties:
        target_agent_id: { type: string }
        target_agent_name: { type: string }
        trust: { type: number }
        affinity: { type: number }
        familiarity: { type: number }

    Rumor:
      type: object
      properties:
        id: { type: string }
        content: { type: string }
        subject: { type: string }
        believers:
          type: array
          items:
            type: object
            properties:
              agent_id: { type: string }
              confidence: { type: number }
        hop_count: { type: integer }
        relevance: { type: number }

    Event:
      type: object
      properties:
        id: { type: string }
        type: { type: string }
        tick: { type: integer }
        agent_id: { type: string }
        description: { type: string }
        data: { type: object }
```

### 9.2 WebSocket Protocol

```typescript
// Client -> Server messages
interface ClientMessage {
  type: 'subscribe' | 'unsubscribe' | 'ping';
  channel?: 'simulation' | 'agent' | 'gossip' | 'events';
  agent_id?: string;  // For agent-specific subscription
}

// Server -> Client messages
interface ServerMessage {
  type: 'tick' | 'agent_update' | 'gossip_update' | 'event' | 'pong';
  tick: number;
  data: TickData | AgentUpdate | GossipUpdate | EventData;
}

interface TickData {
  current_tick: number;
  time_of_day: string;
  agent_positions: Array<{
    id: string;
    x: number;
    y: number;
    state: string;
  }>;
}

interface AgentUpdate {
  agent_id: string;
  state: string;
  current_thought?: string;
  emotional_state?: string;
  action?: {
    type: string;
    target?: string;
  };
}

interface GossipUpdate {
  rumor_id: string;
  action: 'created' | 'propagated' | 'mutated' | 'decayed';
  from_agent?: string;
  to_agent?: string;
  content?: string;
  new_confidence?: number;
}

interface EventData {
  event_id: string;
  event_type: string;
  agent_id?: string;
  description: string;
  importance: 'low' | 'medium' | 'high';
}
```

---

## 10. Testing & Validation

### 10.1 Test Categories

| Category | Scope | Tools |
|----------|-------|-------|
| **Unit Tests** | Individual functions, classes | pytest |
| **Integration Tests** | Component interactions | pytest + testcontainers |
| **Scenario Tests** | End-to-end demo flows | pytest + custom harness |
| **Performance Tests** | Latency, throughput | locust |
| **Determinism Tests** | Replay validation | Custom replay harness |

### 10.2 Key Test Scenarios

```python
# tests/scenarios/test_millbrook_demo.py

class TestMillbrookDemo:
    """
    End-to-end tests for the demo scenario.
    """
    
    @pytest.mark.asyncio
    async def test_gossip_propagation(self, simulation):
        """
        Verify gossip spreads through social network.
        """
        # Seed initial rumor with Elena
        rumor = await simulation.inject_gossip(
            source="elena",
            content="Marcus was seen near the manor last night",
            relevance=0.8
        )
        
        # Run simulation for 200 ticks
        await simulation.run_ticks(200)
        
        # Check propagation
        believers = await simulation.get_rumor_believers(rumor.id)
        
        assert len(believers) >= 2, "Gossip should spread to at least 2 agents"
        assert any(b.agent_name == "viktor" for b in believers), \
            "Viktor (frequent tavern visitor) should hear the rumor"
    
    @pytest.mark.asyncio
    async def test_memory_influences_decision(self, simulation):
        """
        Verify agents reference memories in deliberation.
        """
        # Create memory for Elena about Marcus being trustworthy
        await simulation.create_memory(
            agent="elena",
            content="Marcus helped me when I was sick",
            importance=0.9,
            emotional_valence=0.8
        )
        
        # Trigger deliberation about whether to defend Marcus
        trigger = await simulation.inject_event(
            type="ACCUSATION",
            target="marcus",
            accuser="sarah"
        )
        
        # Wait for Elena's deliberation
        result = await simulation.wait_for_deliberation("elena", timeout=10)
        
        assert result is not None
        assert "defend" in result.action_type.lower() or \
               result.reasoning.lower().contains("marcus")
    
    @pytest.mark.asyncio
    async def test_reflex_preempts_deliberation(self, simulation):
        """
        Verify high-priority reflexes interrupt deliberation.
        """
        # Start Marcus deliberating
        await simulation.trigger_deliberation(
            agent="marcus",
            trigger="should_confess"
        )
        
        # Verify deliberation started
        marcus = await simulation.get_agent("marcus")
        assert marcus.state == "deliberating"
        
        # Inject threat event
        await simulation.inject_event(
            type="GUARD_APPROACHES_AGGRESSIVELY",
            target="marcus"
        )
        
        # Run one tick
        await simulation.run_ticks(1)
        
        # Verify reflex triggered
        marcus = await simulation.get_agent("marcus")
        assert marcus.state == "reacting"
        assert marcus.current_action.type in ["FLEE", "DODGE", "DEFENSIVE_STANCE"]
    
    @pytest.mark.asyncio
    async def test_three_act_structure_completion(self, simulation):
        """
        Verify demo can complete all three acts.
        """
        # Run full demo (9000 ticks = ~7.5 minutes at 20 tps)
        events = []
        
        async for tick_events in simulation.run_with_events(9000):
            events.extend(tick_events)
        
        # Check for key narrative beats
        act_1_events = [e for e in events if e.tick < 2000]
        act_2_events = [e for e in events if 2000 <= e.tick < 6000]
        act_3_events = [e for e in events if e.tick >= 6000]
        
        # Act 1: Setup
        assert any(e.type == "STRANGER_ARRIVES" for e in act_1_events)
        assert any(e.type == "INVESTIGATION_BEGINS" for e in act_1_events)
        
        # Act 2: Complications
        assert any(e.type == "ACCUSATION" for e in act_2_events)
        assert any(e.type == "RELATIONSHIP_CHANGED" for e in act_2_events)
        
        # Act 3: Resolution (flexible - any resolution is valid)
        resolution_types = [
            "TRUTH_REVEALED", "ESCAPE", "CONFRONTATION", "TRAGIC_END"
        ]
        assert any(
            e.type in resolution_types for e in act_3_events
        ), "Demo should reach some form of resolution"
```

### 10.3 Determinism Validation

```python
class DeterminismValidator:
    """
    Ensures simulation can be replayed exactly.
    """
    
    async def validate_replay(
        self,
        seed: int,
        tick_count: int
    ) -> bool:
        # Run simulation, capture all LLM outputs
        run_1 = await self.run_simulation(
            seed=seed,
            ticks=tick_count,
            capture_proposals=True
        )
        
        # Get final state hash
        hash_1 = await self.compute_state_hash()
        
        # Reset database
        await self.reset_state()
        
        # Replay using captured proposals (no LLM calls)
        run_2 = await self.replay_simulation(
            seed=seed,
            ticks=tick_count,
            proposals=run_1.proposals
        )
        
        # Compare state
        hash_2 = await self.compute_state_hash()
        
        return hash_1 == hash_2
```

### 10.4 Deterministic Replay Mechanism

The Deterministic Replay system enables exact reproduction of simulation runs by capturing all non-deterministic inputs (primarily LLM outputs) as "proposals" that can be replayed without making new LLM calls.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DETERMINISTIC REPLAY ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RECORDING MODE                       REPLAY MODE                   │
│  ══════════════                       ═══════════                   │
│                                                                     │
│  ┌─────────────┐                      ┌─────────────┐               │
│  │ Simulation  │                      │ Simulation  │               │
│  │    Loop     │                      │    Loop     │               │
│  └──────┬──────┘                      └──────┬──────┘               │
│         │                                    │                      │
│         ▼                                    ▼                      │
│  ┌─────────────┐                      ┌─────────────┐               │
│  │ Deliberation│                      │ Deliberation│               │
│  │   Request   │                      │   Request   │               │
│  └──────┬──────┘                      └──────┬──────┘               │
│         │                                    │                      │
│         ▼                                    ▼                      │
│  ┌─────────────┐                      ┌─────────────┐               │
│  │  LLM Call   │──────────┐           │  Proposal   │               │
│  │  (Live)     │          │           │   Lookup    │               │
│  └──────┬──────┘          │           └──────┬──────┘               │
│         │                 │                  │                      │
│         ▼                 │                  ▼                      │
│  ┌─────────────┐          │           ┌─────────────┐               │
│  │  Proposal   │          │           │  Cached     │               │
│  │  Created    │          │           │  Proposal   │               │
│  └──────┬──────┘          │           └──────┬──────┘               │
│         │                 │                  │                      │
│         │    ┌────────────┴───────────┐      │                      │
│         └───►│    PROPOSAL LEDGER     │◄─────┘                      │
│              │  (Redis / PostgreSQL)  │                             │
│              │                        │                             │
│              │  • tick: 4532          │                             │
│              │  • agent_id: elena     │                             │
│              │  • trigger_hash: abc123│                             │
│              │  • action: DEFEND      │                             │
│              │  • reasoning: "..."    │                             │
│              │  • emotion: worried    │                             │
│              └────────────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 10.4.1 Proposal Data Structure

```python
@dataclass
class Proposal:
    """
    Captures the complete output of an LLM deliberation for replay.
    This is the atomic unit of non-determinism in the simulation.
    
    CRITICAL FOR EXACT REPLAY: To achieve bit-perfect deterministic replay,
    we must capture not just the LLM output, but also the exact parameters
    that produced it. Even minor changes to temperature, seed, or model
    version can produce different outputs from identical prompts.
    """
    
    # Identity
    proposal_id: UUID
    simulation_id: UUID
    
    # Timing
    created_tick: int
    expires_tick: int                    # Stale after this tick
    applied_tick: Optional[int]          # When committed to state
    
    # Context (for replay matching)
    agent_id: UUID
    trigger_type: str                    # What triggered deliberation
    trigger_hash: str                    # SHA256 of trigger context
    context_hash: str                    # Hash of memories/relationships used
    
    # LLM Output (the non-deterministic part)
    action: Action
    reasoning: str
    emotional_state: str
    confidence: float
    new_beliefs: List[str]
    
    # LLM Parameters (CRITICAL for exact replay)
    llm_model_version: str               # Full model version string (e.g., "gpt-4-0613")
    llm_temperature: float               # Temperature setting used (e.g., 0.7)
    llm_seed: Optional[int]              # Random seed if supported by provider
    llm_top_p: Optional[float]           # Top-p sampling parameter
    llm_response_time_ms: int
    prompt_tokens: int
    completion_tokens: int
    
    # Validation
    was_valid: bool                      # Passed validation
    was_applied: bool                    # Actually used in simulation
    rejection_reason: Optional[str]
    
    def get_llm_config_hash(self) -> str:
        """
        Hash of LLM configuration for replay verification.
        If this differs between recording and replay, exact reproduction
        is not possible even with cached proposals.
        """
        config = {
            "model": self.llm_model_version,
            "temperature": self.llm_temperature,
            "seed": self.llm_seed,
            "top_p": self.llm_top_p
        }
        return hashlib.sha256(
            json.dumps(config, sort_keys=True).encode()
        ).hexdigest()[:12]
    
    def to_ledger_entry(self) -> dict:
        """Serialize for storage in proposal ledger."""
        return {
            "proposal_id": str(self.proposal_id),
            "simulation_id": str(self.simulation_id),
            "created_tick": self.created_tick,
            "agent_id": str(self.agent_id),
            "trigger_hash": self.trigger_hash,
            "context_hash": self.context_hash,
            "action": self.action.to_dict(),
            "reasoning": self.reasoning,
            "emotional_state": self.emotional_state,
            "confidence": self.confidence,
            "new_beliefs": self.new_beliefs,
            # LLM configuration (critical for replay)
            "llm_model_version": self.llm_model_version,
            "llm_temperature": self.llm_temperature,
            "llm_seed": self.llm_seed,
            "llm_top_p": self.llm_top_p,
            "llm_config_hash": self.get_llm_config_hash(),
            "was_applied": self.was_applied
        }


@dataclass  
class TriggerContext:
    """
    Captures the full context that triggered a deliberation.
    Used to match proposals during replay.
    """
    
    agent_id: UUID
    trigger_type: str
    tick: int
    
    # Situation
    stimulus_description: str
    involved_entities: List[UUID]
    location: str
    
    # Agent state
    agent_emotional_state: str
    agent_goals: List[str]
    
    # Retrieved context
    memories_used: List[UUID]
    relationships_used: List[Tuple[UUID, UUID]]
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash for proposal matching.
        Must be stable across replay.
        """
        # Canonicalize and hash
        canonical = json.dumps({
            "agent_id": str(self.agent_id),
            "trigger_type": self.trigger_type,
            "tick": self.tick,
            "stimulus": self.stimulus_description,
            "entities": sorted([str(e) for e in self.involved_entities]),
            "location": self.location,
            "memories": sorted([str(m) for m in self.memories_used]),
        }, sort_keys=True)
        
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

#### 10.4.2 Proposal Ledger

```python
class ProposalLedger:
    """
    Persistent storage for proposals, enabling deterministic replay.
    """
    
    def __init__(self, storage: ProposalStorage):
        self.storage = storage
        self.recording_mode = True
        self.replay_proposals: Dict[str, Proposal] = {}  # hash -> proposal
    
    async def record_proposal(self, proposal: Proposal):
        """
        Record a proposal during live simulation.
        Only active in recording mode.
        """
        if not self.recording_mode:
            return
        
        # Store in persistent ledger
        await self.storage.save_proposal(proposal)
        
        # Update metrics
        self.metrics.proposals_recorded += 1
        self.metrics.tokens_used += (
            proposal.prompt_tokens + proposal.completion_tokens
        )
    
    async def load_replay_data(self, simulation_id: UUID):
        """
        Load all proposals from a previous simulation for replay.
        """
        proposals = await self.storage.get_proposals_for_simulation(simulation_id)
        
        # Index by trigger hash for fast lookup
        self.replay_proposals = {
            p.trigger_hash: p for p in proposals
        }
        
        self.recording_mode = False
        logger.info(f"Loaded {len(proposals)} proposals for replay")
    
    def get_replay_proposal(
        self,
        trigger_context: TriggerContext
    ) -> Optional[Proposal]:
        """
        Look up a cached proposal for replay.
        Returns None if no matching proposal found.
        """
        trigger_hash = trigger_context.compute_hash()
        proposal = self.replay_proposals.get(trigger_hash)
        
        if proposal:
            # Verify it hasn't expired
            if proposal.expires_tick >= trigger_context.tick:
                return proposal
            else:
                logger.warning(
                    f"Proposal {proposal.proposal_id} expired, "
                    f"may cause replay divergence"
                )
        
        return None


class ReplayEngine:
    """
    Manages deterministic replay of recorded simulations.
    """
    
    def __init__(
        self,
        ledger: ProposalLedger,
        simulation: Simulation
    ):
        self.ledger = ledger
        self.simulation = simulation
        self.divergence_detected = False
        self.divergence_points: List[DivergencePoint] = []
    
    async def replay(
        self,
        simulation_id: UUID,
        seed: int,
        tick_count: int,
        strict_mode: bool = True
    ) -> ReplayResult:
        """
        Replay a recorded simulation.
        
        Args:
            simulation_id: ID of the simulation to replay
            seed: Random seed (must match original)
            tick_count: Number of ticks to replay
            strict_mode: If True, halt on divergence
        """
        
        # Load proposal data
        await self.ledger.load_replay_data(simulation_id)
        
        # Initialize simulation with same seed
        await self.simulation.initialize(seed=seed)
        
        # Replace LLM with proposal lookup
        self.simulation.cognition_engine.set_proposal_source(
            self._proposal_lookup
        )
        
        # Run simulation
        for tick in range(tick_count):
            await self.simulation.run_tick()
            
            # Check for divergence
            if strict_mode and self.divergence_detected:
                return ReplayResult(
                    success=False,
                    ticks_completed=tick,
                    divergence_points=self.divergence_points
                )
        
        # Compute final state hash
        final_hash = await self.simulation.compute_state_hash()
        
        return ReplayResult(
            success=not self.divergence_detected,
            ticks_completed=tick_count,
            final_state_hash=final_hash,
            divergence_points=self.divergence_points
        )
    
    async def _proposal_lookup(
        self,
        agent: Agent,
        trigger: TriggerContext
    ) -> Optional[Proposal]:
        """
        Look up proposal instead of calling LLM.
        Records divergence if proposal not found.
        """
        proposal = self.ledger.get_replay_proposal(trigger)
        
        if proposal is None:
            # This indicates either:
            # 1. Different trigger hash (simulation diverged)
            # 2. Missing proposal in ledger (recording error)
            self.divergence_detected = True
            self.divergence_points.append(DivergencePoint(
                tick=trigger.tick,
                agent_id=agent.id,
                reason="missing_proposal",
                trigger_hash=trigger.compute_hash()
            ))
            logger.error(
                f"Replay divergence at tick {trigger.tick}: "
                f"no proposal for agent {agent.name}"
            )
        
        return proposal
```

#### 10.4.3 Sources of Non-Determinism

The replay system must capture all sources of non-determinism:

```python
NON_DETERMINISM_SOURCES = {
    "llm_outputs": {
        "description": "LLM deliberation responses",
        "capture_method": "Proposal ledger with full LLM config",
        "criticality": "HIGH - primary source of emergent behavior",
        "notes": "Captured in Proposal dataclass"
    },
    
    "llm_configuration": {
        "description": "LLM parameters that affect output generation",
        "capture_method": "Store in Proposal: model_version, temperature, seed, top_p",
        "criticality": "HIGH - same prompt can produce different outputs with different params",
        "parameters": {
            "model_version": "Full model identifier (e.g., 'gpt-4-0613', not just 'gpt-4')",
            "temperature": "Sampling temperature (e.g., 0.7)",
            "seed": "Random seed if provider supports deterministic mode",
            "top_p": "Nucleus sampling parameter"
        },
        "warning": "Model deprecation can break replay - archive model versions used"
    },
    
    "random_number_generation": {
        "description": "Dice rolls for gossip mutation, action selection",
        "capture_method": "Seeded PRNG with captured seed",
        "criticality": "HIGH - affects all stochastic decisions"
    },
    
    "timestamp_variations": {
        "description": "Real-world clock differences",
        "capture_method": "Use tick-based time, not wall clock",
        "criticality": "MEDIUM - affects decay calculations"
    },
    
    "async_ordering": {
        "description": "Order of async task completion",
        "capture_method": "Deterministic event ordering within tick",
        "criticality": "MEDIUM - affects when proposals are applied"
    },
    
    "external_events": {
        "description": "User injections, external API calls",
        "capture_method": "Event ledger with tick timestamps",
        "criticality": "LOW for MVP (no external input during demo)"
    }
}


# LLM Configuration for Exact Replay
@dataclass
class LLMReplayConfig:
    """
    Configuration required for exact LLM output reproduction.
    Must match between recording and replay for bit-perfect results.
    """
    
    model_version: str          # e.g., "gpt-4-0613" (specific version, not alias)
    temperature: float          # Sampling temperature
    seed: Optional[int]         # Random seed (provider-dependent)
    top_p: Optional[float]      # Nucleus sampling
    max_tokens: int             # Maximum response length
    
    @classmethod
    def from_proposal(cls, proposal: Proposal) -> 'LLMReplayConfig':
        return cls(
            model_version=proposal.llm_model_version,
            temperature=proposal.llm_temperature,
            seed=proposal.llm_seed,
            top_p=proposal.llm_top_p,
            max_tokens=1024  # Default, could be stored in proposal
        )
    
    def validate_for_replay(self, current_config: 'LLMReplayConfig') -> List[str]:
        """
        Check if current LLM config matches recorded config.
        Returns list of mismatches (empty if exact match possible).
        """
        mismatches = []
        
        if self.model_version != current_config.model_version:
            mismatches.append(
                f"Model mismatch: recorded={self.model_version}, "
                f"current={current_config.model_version}"
            )
        
        if self.temperature != current_config.temperature:
            mismatches.append(
                f"Temperature mismatch: recorded={self.temperature}, "
                f"current={current_config.temperature}"
            )
        
        if self.seed != current_config.seed:
            mismatches.append(
                f"Seed mismatch: recorded={self.seed}, "
                f"current={current_config.seed}"
            )
        
        return mismatches


class DeterministicRNG:
    """
    Seeded random number generator for deterministic replay.
    Each agent gets its own stream to avoid ordering dependencies.
    """
    
    def __init__(self, master_seed: int):
        self.master_seed = master_seed
        self.agent_streams: Dict[UUID, random.Random] = {}
    
    def get_agent_rng(self, agent_id: UUID) -> random.Random:
        """Get deterministic RNG stream for specific agent."""
        if agent_id not in self.agent_streams:
            # Derive agent seed from master seed and agent ID
            combined = f"{self.master_seed}:{agent_id}"
            agent_seed = int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
            self.agent_streams[agent_id] = random.Random(agent_seed)
        
        return self.agent_streams[agent_id]
    
    def gossip_mutation_roll(self, agent_id: UUID) -> float:
        """Roll for gossip mutation."""
        return self.get_agent_rng(agent_id).random()
    
    def relationship_noise(self, agent_id: UUID) -> float:
        """Small noise for relationship changes."""
        return self.get_agent_rng(agent_id).gauss(0, 0.01)
```

#### 10.4.4 Replay Validation

```python
class ReplayValidator:
    """
    Validates that replay produces identical results.
    """
    
    async def validate_full_replay(
        self,
        original_run: SimulationRun
    ) -> ValidationResult:
        """
        Complete validation: replay must produce identical final state.
        """
        
        replay_result = await self.replay_engine.replay(
            simulation_id=original_run.id,
            seed=original_run.seed,
            tick_count=original_run.tick_count
        )
        
        if not replay_result.success:
            return ValidationResult(
                valid=False,
                reason="divergence_detected",
                divergence_points=replay_result.divergence_points
            )
        
        # Compare state hashes
        if replay_result.final_state_hash != original_run.final_state_hash:
            return ValidationResult(
                valid=False,
                reason="state_hash_mismatch",
                original_hash=original_run.final_state_hash,
                replay_hash=replay_result.final_state_hash
            )
        
        return ValidationResult(valid=True)
    
    async def validate_incremental(
        self,
        original_run: SimulationRun,
        checkpoint_interval: int = 1000
    ) -> ValidationResult:
        """
        Incremental validation with checkpoints.
        Faster failure detection.
        """
        
        checkpoints = original_run.checkpoints[::checkpoint_interval]
        
        for checkpoint in checkpoints:
            # Replay up to checkpoint
            replay_result = await self.replay_engine.replay(
                simulation_id=original_run.id,
                seed=original_run.seed,
                tick_count=checkpoint.tick
            )
            
            # Compare checkpoint state
            replay_state = await self.simulation.compute_state_hash()
            
            if replay_state != checkpoint.state_hash:
                return ValidationResult(
                    valid=False,
                    reason="checkpoint_mismatch",
                    tick=checkpoint.tick,
                    expected_hash=checkpoint.state_hash,
                    actual_hash=replay_state
                )
        
        return ValidationResult(valid=True)
```

#### 10.4.5 Use Cases for Deterministic Replay

```python
REPLAY_USE_CASES = {
    "debugging": {
        "description": "Reproduce exact state leading to a bug",
        "workflow": [
            "1. Record simulation with bug occurrence",
            "2. Replay with debugger attached",
            "3. Step through exact sequence to bug",
            "4. Fix bug, replay to verify fix"
        ]
    },
    
    "demo_consistency": {
        "description": "Guarantee specific demo experiences",
        "workflow": [
            "1. Record high-quality demo run",
            "2. Package proposals with demo scenario",
            "3. Replay for consistent audience experience",
            "4. No LLM costs during replay"
        ]
    },
    
    "testing": {
        "description": "Regression testing without LLM calls",
        "workflow": [
            "1. Record test scenarios",
            "2. Run replay in CI/CD (no API costs)",
            "3. Verify state matches expected",
            "4. Detect regressions quickly"
        ]
    },
    
    "analysis": {
        "description": "Post-hoc analysis of interesting runs",
        "workflow": [
            "1. Identify interesting simulation",
            "2. Replay with additional logging",
            "3. Extract detailed metrics",
            "4. Study emergent behaviors"
        ]
    }
}
```

---

## 11. Risk Assessment & Mitigations

### 11.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM latency spikes** | High | Medium | Token budgets, fallback heuristics, async processing. See §8.3.4 Circuit Breaker Patterns |
| **LLM output quality variance** | Medium | High | Structured output schemas, validation, retry logic |
| **LLM service outage** | Medium | High | Multi-provider failover, circuit breakers with automatic recovery. See §8.3.4 |
| **Memory retrieval too slow** | Medium | Medium | Caching, pre-computed embeddings, query optimization |
| **Gossip spreads unrealistically** | Medium | Medium | Tunable decay rates, propagation caps, personality filters |
| **Agents behave incoherently** | Medium | High | Strong personality constraints, memory context, output validation |
| **Tick rate drops under load** | Low | High | Agent LOD tiers (§6.7), aggressive caching, background processing |
| **Database contention** | Low | Medium | Optimistic concurrency, read replicas, connection pooling |
| **API costs exceed budget** | Medium | Medium | Budget Mode with cost tracking and limits. See §12 |
| **Non-reproducible bugs** | Medium | Medium | Deterministic Replay mechanism. See §10.4 |

### 11.2 Demo-Specific Risks

| Risk | Mitigation |
|------|------------|
| **Demo stalls with no interesting events** | Drama Director injects catalysts when tension is low |
| **Demo resolves too quickly** | Pacing controls, minimum act durations |
| **Agent stuck in loop** | Loop detection, action cooldowns, forced state transitions |
| **Gossip doesn't spread visibly** | Higher initial propagation rates, debug UI highlighting |
| **Relationships don't change noticeably** | Larger delta thresholds, visual emphasis on changes |

### 11.3 Contingency Plans

```python
CONTINGENCY_CONFIG = {
    "llm_failure": {
        "detection": "error_rate > 5% in 60s",
        "action": "switch_to_heuristic_mode",
        "recovery": "half_open_after_30s"
    },
    
    "demo_stall": {
        "detection": "no_narrative_events_for_500_ticks",
        "action": "inject_high_priority_catalyst",
        "catalysts": [
            "guard_finds_evidence",
            "stranger_attempts_escape",
            "lydia_breaks_silence"
        ]
    },
    
    "performance_degradation": {
        "detection": "tick_latency > 100ms",
        "action": "reduce_cognitive_load",
        "steps": [
            "pause_low_priority_deliberations",
            "increase_reflex_threshold",
            "reduce_gossip_frequency"
        ]
    }
}
```

---

## 12. Budget Mode for Development Efficiency

Budget Mode is a development configuration that minimizes LLM API costs while maintaining functional simulation behavior. This enables rapid iteration during development without accumulating significant API bills.

### 12.1 Budget Mode Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     BUDGET MODE CONFIGURATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   FULL      │     │   BUDGET    │     │   OFFLINE   │           │
│  │   MODE      │     │   MODE      │     │   MODE      │           │
│  │             │     │             │     │             │           │
│  │ • All LLM   │     │ • Limited   │     │ • No LLM    │           │
│  │   calls     │     │   LLM calls │     │   calls     │           │
│  │ • Full LOD  │     │ • Aggressive│     │ • Heuristics│           │
│  │   tiers     │     │   caching   │     │   only      │           │
│  │ • Rich      │     │ • Smaller   │     │ • Replay    │           │
│  │   context   │     │   context   │     │   mode      │           │
│  │             │     │             │     │             │           │
│  │ Cost: $$$   │     │ Cost: $     │     │ Cost: $0    │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│                                                                     │
│  Use Cases:                                                         │
│  • Production demos  • Development    • CI/CD testing              │
│  • Recording runs    • Debugging      • Offline development        │
│  • Client showcases  • Fast iteration • Deterministic testing      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Budget Mode Configuration

```python
@dataclass
class BudgetModeConfig:
    """
    Configuration for cost-efficient development mode.
    """
    
    # Mode selection
    mode: str = "budget"  # "full", "budget", "offline"
    
    # Token limits
    hourly_token_budget: int = 50000      # Max tokens per hour
    per_deliberation_limit: int = 300     # Max tokens per LLM call
    daily_cost_limit_usd: float = 5.00    # Hard stop at this cost
    
    # LLM selection
    primary_model: str = "zai-coding-plan/glm-4.7"   # GLM Coding Plan model in budget mode
    full_mode_model: str = "zai-coding-plan/glm-4.7"   # GLM Coding Plan model for full mode
    
    # Context reduction
    max_memories_in_prompt: int = 3        # vs 10 in full mode
    max_relationships_in_prompt: int = 5   # vs 15 in full mode
    personality_description_length: int = 100  # vs 300 in full mode
    
    # Caching
    cache_ttl_seconds: int = 3600          # Cache similar deliberations
    cache_similarity_threshold: float = 0.9  # When to reuse cached response
    
    # LOD adjustments
    focus_tier_max_agents: int = 2         # vs 4 in full mode
    ambient_tier_max_agents: int = 4       # vs 8 in full mode
    deliberation_threshold_multiplier: float = 1.5  # Higher bar for LLM calls
    
    # Heuristic fallback
    heuristic_probability: float = 0.3     # 30% of deliberations use heuristic


BUDGET_MODE_PRESETS = {
    "full": BudgetModeConfig(
        mode="full",
        hourly_token_budget=500000,
        per_deliberation_limit=800,
        daily_cost_limit_usd=50.00,
        primary_model="zai-coding-plan/glm-4.7",
        max_memories_in_prompt=10,
        max_relationships_in_prompt=15,
        personality_description_length=300,
        cache_ttl_seconds=300,
        cache_similarity_threshold=0.95,
        focus_tier_max_agents=4,
        ambient_tier_max_agents=8,
        deliberation_threshold_multiplier=1.0,
        heuristic_probability=0.0
    ),
    
    "budget": BudgetModeConfig(
        mode="budget",
        hourly_token_budget=50000,
        per_deliberation_limit=300,
        daily_cost_limit_usd=5.00,
        primary_model="zai-coding-plan/glm-4.7",
        max_memories_in_prompt=3,
        max_relationships_in_prompt=5,
        personality_description_length=100,
        cache_ttl_seconds=3600,
        cache_similarity_threshold=0.85,
        focus_tier_max_agents=2,
        ambient_tier_max_agents=4,
        deliberation_threshold_multiplier=1.5,
        heuristic_probability=0.3
    ),
    
    "offline": BudgetModeConfig(
        mode="offline",
        hourly_token_budget=0,
        per_deliberation_limit=0,
        daily_cost_limit_usd=0.00,
        primary_model="none",
        max_memories_in_prompt=3,
        max_relationships_in_prompt=5,
        personality_description_length=100,
        cache_ttl_seconds=float('inf'),
        cache_similarity_threshold=0.0,
        focus_tier_max_agents=0,
        ambient_tier_max_agents=0,
        deliberation_threshold_multiplier=float('inf'),
        heuristic_probability=1.0
    )
}
```

### 12.3 Budget Mode Components

#### 12.3.1 Cost Tracker

```python
class CostTracker:
    """
    Tracks LLM costs and enforces budget limits.
    """
    
    # Pricing (as of Jan 2025, subject to change)
    PRICING = {
        "zai-coding-plan/glm-4.7": {"input": 0.01, "output": 0.03},      # per 1K tokens
    }
    
    def __init__(self, config: BudgetModeConfig):
        self.config = config
        self.hourly_tokens = 0
        self.hourly_cost = 0.0
        self.daily_cost = 0.0
        self.hour_start = time.time()
        self.day_start = time.time()
        
        # Tracking
        self.calls_made = 0
        self.calls_cached = 0
        self.calls_heuristic = 0
        self.budget_exceeded_count = 0
    
    def can_make_call(self, estimated_tokens: int) -> Tuple[bool, str]:
        """
        Check if we have budget for an LLM call.
        Returns (allowed, reason).
        """
        self._maybe_reset_counters()
        
        # Check hourly token budget
        if self.hourly_tokens + estimated_tokens > self.config.hourly_token_budget:
            return False, "hourly_token_limit"
        
        # Check daily cost limit
        estimated_cost = self._estimate_cost(estimated_tokens)
        if self.daily_cost + estimated_cost > self.config.daily_cost_limit_usd:
            return False, "daily_cost_limit"
        
        return True, "allowed"
    
    def record_call(self, input_tokens: int, output_tokens: int, model: str):
        """Record an LLM call's token usage and cost."""
        total_tokens = input_tokens + output_tokens
        self.hourly_tokens += total_tokens
        
        pricing = self.PRICING.get(model, self.PRICING["zai-coding-plan/glm-4.7"])
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )
        
        self.hourly_cost += cost
        self.daily_cost += cost
        self.calls_made += 1
        
        logger.debug(f"LLM call: {total_tokens} tokens, ${cost:.4f}")
    
    def record_cache_hit(self):
        """Record a cache hit (no LLM call needed)."""
        self.calls_cached += 1
    
    def record_heuristic_fallback(self):
        """Record a heuristic fallback (budget saved)."""
        self.calls_heuristic += 1
    
    def get_status(self) -> dict:
        """Get current budget status."""
        return {
            "mode": self.config.mode,
            "hourly_tokens_used": self.hourly_tokens,
            "hourly_tokens_limit": self.config.hourly_token_budget,
            "hourly_tokens_remaining": max(0, self.config.hourly_token_budget - self.hourly_tokens),
            "daily_cost_usd": round(self.daily_cost, 4),
            "daily_limit_usd": self.config.daily_cost_limit_usd,
            "daily_cost_remaining": round(self.config.daily_cost_limit_usd - self.daily_cost, 4),
            "calls_made": self.calls_made,
            "calls_cached": self.calls_cached,
            "calls_heuristic": self.calls_heuristic,
            "cache_rate": self.calls_cached / max(1, self.calls_made + self.calls_cached),
            "budget_exceeded_count": self.budget_exceeded_count
        }
    
    def _maybe_reset_counters(self):
        """Reset hourly/daily counters if time has passed."""
        now = time.time()
        
        if now - self.hour_start > 3600:
            self.hourly_tokens = 0
            self.hourly_cost = 0.0
            self.hour_start = now
        
        if now - self.day_start > 86400:
            self.daily_cost = 0.0
            self.day_start = now
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost for a given token count."""
        pricing = self.PRICING.get(
            self.config.primary_model, 
            self.PRICING["zai-coding-plan/glm-4.7"]
        )
        # Assume 60% input, 40% output
        return (
            (tokens * 0.6 / 1000) * pricing["input"] +
            (tokens * 0.4 / 1000) * pricing["output"]
        )
```

#### 12.3.2 Semantic Cache

```python
class SemanticCache:
    """
    Cache for LLM responses based on semantic similarity.
    Dramatically reduces costs for similar deliberation contexts.
    """
    
    def __init__(self, config: BudgetModeConfig, embedding_model: str):
        self.config = config
        self.embedding_model = embedding_model
        self.cache: Dict[str, CacheEntry] = {}
        self.embeddings: Dict[str, List[float]] = {}
        
    async def get_cached_response(
        self,
        agent_id: UUID,
        trigger_context: str,
        personality_hash: str
    ) -> Optional[Proposal]:
        """
        Look for a semantically similar cached response.
        """
        # Compute embedding for current context
        context_key = f"{agent_id}:{personality_hash}:{trigger_context[:200]}"
        context_embedding = await self._get_embedding(trigger_context)
        
        # Search for similar cached entries
        best_match = None
        best_similarity = 0.0
        
        for cache_key, entry in self.cache.items():
            # Check if same agent and personality
            if not cache_key.startswith(f"{agent_id}:{personality_hash}"):
                continue
            
            # Check TTL
            if time.time() - entry.created_at > self.config.cache_ttl_seconds:
                continue
            
            # Compute similarity
            similarity = self._cosine_similarity(
                context_embedding,
                self.embeddings[cache_key]
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry
        
        # Return if above threshold
        if best_match and best_similarity >= self.config.cache_similarity_threshold:
            logger.debug(
                f"Cache hit for {agent_id}: similarity={best_similarity:.3f}"
            )
            return self._adapt_cached_response(best_match.proposal, trigger_context)
        
        return None
    
    async def store_response(
        self,
        agent_id: UUID,
        trigger_context: str,
        personality_hash: str,
        proposal: Proposal
    ):
        """Store a response in the cache."""
        context_key = f"{agent_id}:{personality_hash}:{trigger_context[:200]}"
        
        self.cache[context_key] = CacheEntry(
            proposal=proposal,
            created_at=time.time()
        )
        
        self.embeddings[context_key] = await self._get_embedding(trigger_context)
    
    def _adapt_cached_response(
        self,
        cached_proposal: Proposal,
        new_context: str
    ) -> Proposal:
        """
        Adapt a cached response to the new context.
        Minor adjustments to make it fit.
        """
        adapted = copy.deepcopy(cached_proposal)
        adapted.proposal_id = uuid4()
        adapted.created_tick = self.current_tick
        adapted.from_cache = True
        return adapted
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        # Use a local embedding model for cost efficiency
        return await self.embedding_model.embed(text)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(y ** 2 for y in b))
        return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0


@dataclass
class CacheEntry:
    proposal: Proposal
    created_at: float
```

#### 12.3.3 Budget-Aware Deliberation

```python
class BudgetAwareDeliberator:
    """
    Deliberation engine that respects budget constraints.
    """
    
    def __init__(
        self,
        config: BudgetModeConfig,
        cost_tracker: CostTracker,
        semantic_cache: SemanticCache,
        heuristic_engine: HeuristicEngine
    ):
        self.config = config
        self.cost_tracker = cost_tracker
        self.cache = semantic_cache
        self.heuristics = heuristic_engine
    
    async def deliberate(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> Proposal:
        """
        Deliberate with budget awareness.
        May use cache, heuristics, or LLM based on budget.
        """
        
        # Step 1: Check if we should use heuristic instead
        if self._should_use_heuristic(agent, trigger):
            self.cost_tracker.record_heuristic_fallback()
            return self.heuristics.generate_proposal(agent, trigger)
        
        # Step 2: Check semantic cache
        personality_hash = self._hash_personality(agent)
        cached = await self.cache.get_cached_response(
            agent.id,
            trigger.situation_description,
            personality_hash
        )
        
        if cached:
            self.cost_tracker.record_cache_hit()
            return cached
        
        # Step 3: Check budget before LLM call
        estimated_tokens = self._estimate_tokens(agent, trigger)
        can_call, reason = self.cost_tracker.can_make_call(estimated_tokens)
        
        if not can_call:
            logger.warning(f"Budget limit reached: {reason}, using heuristic")
            self.cost_tracker.budget_exceeded_count += 1
            return self.heuristics.generate_proposal(agent, trigger)
        
        # Step 4: Make LLM call with budget-appropriate context
        proposal = await self._llm_deliberate(agent, trigger)
        
        # Step 5: Cache the response
        await self.cache.store_response(
            agent.id,
            trigger.situation_description,
            personality_hash,
            proposal
        )
        
        return proposal
    
    def _should_use_heuristic(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> bool:
        """
        Decide whether to skip LLM and use heuristic.
        Based on probability and trigger importance.
        """
        # Random chance based on config
        if random.random() < self.config.heuristic_probability:
            return True
        
        # Low-stakes triggers always use heuristic in budget mode
        if trigger.importance < 0.3 and self.config.mode == "budget":
            return True
        
        # Simulation tier agents always use heuristic
        if agent.lod_tier == "simulation":
            return True
        
        return False
    
    async def _llm_deliberate(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> Proposal:
        """Make actual LLM call with budget-constrained context."""
        
        # Build reduced-size prompt
        prompt = self._build_budget_prompt(agent, trigger)
        
        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.primary_model,
            max_tokens=self.config.per_deliberation_limit,
            temperature=0.7
        )
        
        # Record usage
        self.cost_tracker.record_call(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=self.config.primary_model
        )
        
        return self._parse_response(response, agent, trigger)
    
    def _build_budget_prompt(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> str:
        """
        Build a smaller prompt for budget mode.
        Focuses on essential context only.
        """
        
        # Truncated personality description
        personality = agent.personality_description[:self.config.personality_description_length]
        
        # Limited memories
        memories = trigger.relevant_memories[:self.config.max_memories_in_prompt]
        memory_text = "\n".join([f"- {m.what}" for m in memories])
        
        # Limited relationships
        relationships = trigger.relevant_relationships[:self.config.max_relationships_in_prompt]
        rel_text = "\n".join([
            f"- {r.target_name}: trust={r.trust:.1f}" 
            for r in relationships
        ])
        
        return f"""You are {agent.name}, a {agent.role}.
Personality: {personality}

Situation: {trigger.situation_description}

Memories:
{memory_text}

Relationships:
{rel_text}

Choose an action from: {trigger.available_actions}
Respond with JSON: {{"action": "...", "reasoning": "brief", "emotion": "..."}}"""
    
    def _estimate_tokens(
        self,
        agent: Agent,
        trigger: DeliberationTrigger
    ) -> int:
        """Estimate token count for this deliberation."""
        # Rough estimate: 4 chars per token
        prompt_length = (
            self.config.personality_description_length +
            len(trigger.situation_description) +
            self.config.max_memories_in_prompt * 50 +
            self.config.max_relationships_in_prompt * 20 +
            200  # Template overhead
        )
        
        return (prompt_length // 4) + self.config.per_deliberation_limit
```

### 12.4 Budget Mode API

```python
# API endpoints for budget mode management

@app.get("/budget/status")
async def get_budget_status():
    """Get current budget mode status and usage."""
    return cost_tracker.get_status()

@app.post("/budget/mode")
async def set_budget_mode(mode: str):
    """Switch budget mode (full, budget, offline)."""
    if mode not in BUDGET_MODE_PRESETS:
        raise HTTPException(400, f"Unknown mode: {mode}")
    
    config = BUDGET_MODE_PRESETS[mode]
    await simulation.update_budget_config(config)
    
    return {"status": "ok", "mode": mode}

@app.post("/budget/limit")
async def set_budget_limit(daily_limit_usd: float):
    """Update daily cost limit."""
    config.daily_cost_limit_usd = daily_limit_usd
    return {"status": "ok", "new_limit": daily_limit_usd}

@app.get("/budget/forecast")
async def get_cost_forecast(tick_count: int):
    """Forecast cost for running simulation for given ticks."""
    current_rate = cost_tracker.daily_cost / max(1, simulation.ticks_today)
    forecast = current_rate * tick_count
    
    return {
        "tick_count": tick_count,
        "estimated_cost_usd": round(forecast, 2),
        "cost_per_1000_ticks": round(current_rate * 1000, 4),
        "within_budget": forecast <= config.daily_cost_limit_usd
    }
```

### 12.5 Development Workflow with Budget Mode

```python
DEVELOPMENT_WORKFLOW = {
    "daily_development": {
        "mode": "budget",
        "description": "Normal development iteration",
        "settings": {
            "daily_limit": "$5",
            "model": "zai-coding-plan/glm-4.7",
            "cache_aggressive": True
        },
        "expected_runs": "10-20 short simulations"
    },
    
    "feature_testing": {
        "mode": "offline",
        "description": "Testing new features without LLM",
        "settings": {
            "daily_limit": "$0",
            "model": "none",
            "use_recorded_proposals": True
        },
        "expected_runs": "Unlimited"
    },
    
    "quality_check": {
        "mode": "full",
        "description": "Weekly quality validation",
        "settings": {
            "daily_limit": "$20",
            "model": "zai-coding-plan/glm-4.7",
            "cache_minimal": True
        },
        "expected_runs": "2-3 full demos"
    },
    
    "demo_recording": {
        "mode": "full",
        "description": "Recording showcase demos",
        "settings": {
            "daily_limit": "$50",
            "model": "zai-coding-plan/glm-4.7",
            "capture_proposals": True
        },
        "expected_runs": "5-10 demo attempts"
    },
    
    "ci_cd_pipeline": {
        "mode": "offline",
        "description": "Automated testing in CI",
        "settings": {
            "daily_limit": "$0",
            "replay_mode": True
        },
        "expected_runs": "Unlimited, deterministic"
    }
}
```

---

## 13. MVP Timeline & Milestones

### 13.1 Development Phases

```
Week 1-2: Foundation
├── [ ] Project setup (Docker, CI/CD)
├── [ ] Database schemas (PostgreSQL, Neo4j)
├── [ ] Basic simulation loop (tick management)
├── [ ] Agent data structures
└── [ ] Event system implementation

Week 3-4: Memory System
├── [ ] Episodic memory (ChromaDB integration)
├── [ ] Semantic memory (Neo4j queries)
├── [ ] Memory retrieval algorithm
├── [ ] Memory decay and pruning
└── [ ] Unit tests for memory system

Week 5-6: Cognition Engine
├── [ ] Reflex library implementation
├── [ ] LLM integration (deliberation)
├── [ ] Proposal/commit pattern
├── [ ] Token bucket rate limiting
├── [ ] Graceful degradation
└── [ ] Preemption logic

Week 7-8: Social Dynamics
├── [ ] Gossip propagation system
├── [ ] Relationship tracking
├── [ ] Belief formation/revision
├── [ ] Social trigger system
└── [ ] Integration tests

Week 9-10: Demo Scenario
├── [ ] Millbrook village setup
├── [ ] Character definitions (15 agents)
├── [ ] Initial state seeding
├── [ ] Three-act structure catalysts
├── [ ] Drama Director (basic)
└── [ ] Scenario tests

Week 11-12: Debug UI & Polish
├── [ ] React frontend setup
├── [ ] Village map visualization
├── [ ] Agent inspector panel
├── [ ] Gossip tracker
├── [ ] Relationship graph
├── [ ] Event timeline
├── [ ] WebSocket integration
└── [ ] End-to-end testing

Week 13-14: Integration & Demo Prep
├── [ ] Full integration testing
├── [ ] Performance optimization
├── [ ] Demo run-throughs
├── [ ] Bug fixes
├── [ ] Documentation
└── [ ] Demo recording
```

### 13.2 Milestone Definitions

| Milestone | Criteria | Target |
|-----------|----------|--------|
| **M1: Foundation** | Tick loop running, agents in DB, events flowing | Week 2 |
| **M2: Memory** | Agents storing/retrieving memories | Week 4 |
| **M3: Cognition** | Dual-mode thinking working | Week 6 |
| **M4: Social** | Gossip spreading between agents | Week 8 |
| **M5: Demo Alpha** | Millbrook scenario running | Week 10 |
| **M6: Demo Beta** | Full UI, observable narrative | Week 12 |
| **M7: Demo Ready** | Polished, tested, documented | Week 14 |

---

## 14. Success Criteria

### 14.1 Technical Success

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Reflex latency | P99 response time | <50ms |
| Deliberation latency | P95 response time | <5s |
| Memory retrieval | P99 query time | <100ms |
| Tick stability | Ticks per second | 20 TPS sustained |
| Agent count | Concurrent agents | 15-20 |
| Uptime | Demo completion rate | >95% |

### 14.2 Narrative Success

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Emergent events | Unscripted narrative beats | ≥3 per demo |
| Gossip visibility | Rumors spreading observably | 100% of demos |
| Relationship dynamics | Visible trust changes | ≥5 per demo |
| Memory references | Agents citing past events | ≥10 per demo |
| Resolution variety | Different endings across runs | ≥2 types observed |

### 14.3 Demo Success

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Runtime | Demo duration without crash | 10-15 minutes |
| Engagement | Viewer can follow narrative | Subjective |
| Clarity | Debug UI conveys agent thinking | Subjective |
| Repeatability | Demo runs consistently | >90% success |

---

## 15. Implementation Roadmap

This section outlines the recommended implementation order for the MVP. Each phase builds upon the previous, allowing for incremental testing and validation.

### 15.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TSUKUYOMI MVP IMPLEMENTATION PHASES                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1                Phase 2                Phase 3                Phase 4
│  THE LOOP &             THE BRAIN &            THE MEMORY &            THE DRAMA
│  THE DUMB AGENT         THE BUDGET             THE GATE                         
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  │ • Tick loop │        │ • LLM calls │        │ • Episodic  │        │ • Social    │
│  │ • Reflexes  │───────►│ • Budget    │───────►│   Memory    │───────►│   Engine    │
│  │ • No LLM    │        │   Mode      │        │ • Validation│        │ • Gossip    │
│  │ • 20 TPS    │        │ • LOD tiers │        │   Gate      │        │ • Director  │
│  └─────────────┘        └─────────────┘        └─────────────┘        └─────────────┘
│        │                       │                      │                      │
│    Week 1-2               Week 3-4               Week 5-6               Week 7-8
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Phase 1: The Loop & The Dumb Agent

**Goal:** Establish rock-solid simulation foundation with zero LLM dependency.

**Duration:** ~2 weeks

**Deliverables:**

| Component | Description | Success Metric |
|-----------|-------------|----------------|
| Tick Loop | Core 20 TPS simulation loop | Stable 20 TPS for 15+ minutes |
| Agent State Machine | Basic agent states (idle, moving, acting) | State transitions work correctly |
| Reflex Library | System 1 heuristic responses | Agents respond to stimuli <50ms |
| Pathfinding | A* navigation on village map | Agents navigate without collision |
| Action Queue | FIFO action execution | Actions execute in order |
| Event Bus | Pub/sub for simulation events | Events propagate correctly |

**Key Principle:** If this phase fails, nothing else matters. The simulation must run smoothly with "dumb" agents before adding intelligence.

```python
# Phase 1 Test: Can we run 20 agents doing random walks for 15 minutes at 20 TPS?
def phase1_smoke_test():
    sim = Simulation(agent_count=20, tick_rate=20)
    
    # All agents use only reflexes - NO LLM
    for agent in sim.agents:
        agent.cognition_mode = "reflex_only"
    
    # Run for 15 minutes (18,000 ticks)
    for tick in range(18_000):
        sim.tick()
        assert sim.tps >= 19, f"TPS dropped to {sim.tps} at tick {tick}"
    
    print("Phase 1 PASSED: Simulation stable at 20 TPS")
```

### 15.3 Phase 2: The Brain & The Budget

**Goal:** Integrate LLM deliberation with cost controls and LOD management.

**Duration:** ~2 weeks

**Prerequisites:** Phase 1 complete and stable

**Deliverables:**

| Component | Description | Success Metric |
|-----------|-------------|----------------|
| LLM Integration | OpenAI/Anthropic API wrapper | Successful API calls |
| Budget Mode | Mock LLM responses for dev | $0 cost during development |
| LOD Manager | Focus/Ambient/Simulation tiers | Correct tier assignments |
| Demotion Cooldowns | Anti-flickering enforcement | No rapid tier oscillations |
| Token Budget | Per-agent context limits | Stay within token limits |
| Circuit Breakers | Graceful LLM failure handling | Fallback to reflexes on failure |

**Key Principle:** Budget Mode lets developers iterate without API costs. LOD ensures we only pay for "important" agents.

```python
# Phase 2 Test: Can Focus agents deliberate while Simulation agents stay cheap?
def phase2_cost_test():
    sim = Simulation(agent_count=20)
    sim.budget_mode = True  # No real API calls
    
    # Run scenario with mixed LOD
    lod_manager = LODManager(config)
    lod_manager.update_tiers(sim.agents, context)
    
    focus_agents = [a for a in sim.agents if a.lod_tier == "FOCUS"]
    sim_agents = [a for a in sim.agents if a.lod_tier == "SIMULATION"]
    
    assert len(focus_agents) <= 3, "Too many Focus agents"
    assert len(sim_agents) >= 10, "Not enough agents on Simulation tier"
    
    # Verify Focus agents actually deliberate
    for agent in focus_agents:
        action = agent.process_stimulus(test_stimulus)
        assert agent.last_cognition_mode == "deliberation"
    
    print("Phase 2 PASSED: LOD tiers working correctly")
```

### 15.4 Phase 3: The Memory & The Gate

**Goal:** Agents remember the past and validate their intentions.

**Duration:** ~2 weeks

**Prerequisites:** Phase 2 complete (LLM integration working)

**Deliverables:**

| Component | Description | Success Metric |
|-----------|-------------|----------------|
| Episodic Memory | Event recording with embeddings | Events stored and retrievable |
| Memory Retrieval | Relevance-based memory search | <100ms P99 retrieval |
| Semantic Memory | Accumulated knowledge/beliefs | Beliefs update correctly |
| Validation Gate | Pre-action validity checking | Invalid actions blocked |
| Recovery Heuristics | Graceful fallback on validation fail | Agents recover smoothly |
| Sleep Consolidation | Memory pruning during "night" | Memory stays bounded |

**Key Principle:** Memory gives agents continuity. The Validation Gate prevents nonsense actions.

```python
# Phase 3 Test: Can agents remember and reference past events?
def phase3_memory_test():
    sim = Simulation()
    agent = sim.agents[0]
    
    # Create a memorable event
    event = Event(
        type="witnessed_theft",
        actor="marcus",
        target="merchant_stall",
        tick=100
    )
    agent.memory.record_episodic(event)
    
    # Later, ask agent about it
    query = "What suspicious activity have you seen?"
    memories = agent.memory.retrieve_relevant(query, limit=5)
    
    assert any("theft" in m.description for m in memories)
    assert memories[0].tick == 100
    
    print("Phase 3 PASSED: Episodic memory working")
```

### 15.5 Phase 4: The Drama

**Goal:** Emergent social dynamics and narrative orchestration.

**Duration:** ~2 weeks

**Prerequisites:** Phase 3 complete (memory system working)

**Deliverables:**

| Component | Description | Success Metric |
|-----------|-------------|----------------|
| Social Engine | Relationship tracking | Trust/affinity evolve |
| Gossip System | Information propagation | Rumors spread through network |
| Belief Networks | Who knows what about whom | Beliefs tracked correctly |
| Drama Director | Tension monitoring & injection | Tension stays in target range |
| Secret Objectives | Hidden agent agendas | Natural dramatic conflict |
| Full Demo | Complete three-act structure | 10-15 minute demo runs |

**Key Principle:** This phase brings the village to life. Without it, we have smart individuals but no community.

```python
# Phase 4 Test: Does gossip actually spread?
def phase4_gossip_test():
    sim = Simulation()
    
    # Agent A witnesses something
    agent_a = sim.get_agent("elena")
    secret = Information(
        content="Marcus stole from Viktor",
        source="direct_observation",
        confidence=0.9
    )
    agent_a.knowledge.add(secret)
    
    # Run simulation for a while
    for _ in range(1000):
        sim.tick()
    
    # Check how many agents know the gossip
    agents_who_know = [
        a for a in sim.agents 
        if a.knowledge.contains_similar(secret)
    ]
    
    assert len(agents_who_know) >= 3, "Gossip didn't spread"
    assert agents_who_know[0] != agent_a, "Original witness shouldn't count"
    
    print("Phase 4 PASSED: Gossip propagates through social network")
```

### 15.6 Phase Dependencies

```
                         ┌─────────────────────────────────────────────┐
                         │              DEPENDENCY GRAPH               │
                         └─────────────────────────────────────────────┘
                         
Phase 1 (Foundation)     Phase 2 (Intelligence)     Phase 3 (Memory)     Phase 4 (Social)
        │                        │                         │                    │
    Tick Loop ──────────────────►│                         │                    │
        │                        │                         │                    │
  Reflex Library ───────────────►│                         │                    │
        │                        │                         │                    │
   Event Bus ───────────────────►│                         │                    │
        │                        │                         │                    │
                          LLM Integration ────────────────►│                    │
                                 │                         │                    │
                           LOD Manager ───────────────────►│                    │
                                 │                         │                    │
                          Budget Mode ────────────────────►│                    │
                                 │                         │                    │
                                           Episodic Memory ────────────────────►│
                                                  │                             │
                                           Validation Gate ────────────────────►│
                                                  │                             │
                                                              Social Engine ────►│
                                                                    │           │
                                                              Gossip System ────►│
                                                                    │           │
                                                             Drama Director ────┘
```

### 15.7 Risk Checkpoints

At the end of each phase, evaluate these risks before proceeding:

| Phase | Go/No-Go Criteria | Fallback Plan |
|-------|-------------------|---------------|
| 1 → 2 | 20 TPS stable for 15 min | Optimize tick loop before proceeding |
| 2 → 3 | LLM latency <5s P95 | Reduce Focus agent count or simplify prompts |
| 3 → 4 | Memory retrieval <100ms | Add caching or reduce embedding dimensions |
| 4 → Demo | Gossip spreads to 3+ agents | Simplify social network topology |

**Critical:** Do not skip phases. Each phase must be stable before adding the next layer of complexity.

---

## Appendix A: Character Profiles

### Elena (Innkeeper)

```yaml
name: Elena
role: innkeeper
location: tavern

personality:
  openness: 0.6
  conscientiousness: 0.7
  extraversion: 0.8
  agreeableness: 0.75
  neuroticism: 0.4
  bravery: 0.5
  honesty: 0.6
  loyalty: 0.95  # Very loyal to family

background: |
  Elena has run The Rusty Nail for 15 years since her husband died.
  She raised Marcus alone and is fiercely protective of him.
  She knows everyone's business but is selective about what she shares.

initial_relationships:
  - target: marcus
    trust: 0.95
    affinity: 0.95
    familiarity: 1.0
  - target: viktor
    trust: 0.7
    affinity: 0.6
    familiarity: 0.8
  - target: sarah
    trust: 0.5
    affinity: 0.4
    familiarity: 0.7

initial_goals:
  - type: protect_family
    priority: 100
    description: "Keep Marcus safe at all costs"
  - type: maintain_business
    priority: 50
    description: "Keep the tavern running smoothly"
```

### The Stranger (Antagonist)

```yaml
name: The Stranger
role: traveler
location: tavern

personality:
  openness: 0.8
  conscientiousness: 0.3
  extraversion: 0.7
  agreeableness: 0.4  # Manipulative
  neuroticism: 0.2
  bravery: 0.6
  honesty: 0.1  # Deceptive
  loyalty: 0.1

background: |
  A charming traveler who arrived in Millbrook seeking a specific artifact.
  They successfully stole it from the manor but dropped it during escape.
  Now they must recover it or frame someone else to escape.

hidden_knowledge:
  - "I stole the artifact from the manor"
  - "I dropped the artifact near the market"
  - "Marcus found what I dropped"

initial_goals:
  - type: recover_artifact
    priority: 100
    description: "Find and retrieve the artifact"
  - type: avoid_detection
    priority: 90
    description: "Don't get caught for the theft"
  - type: frame_innocent
    priority: 80
    description: "If necessary, ensure someone else takes the blame"
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Tick** | Single discrete time step in simulation (50ms at 20 TPS) |
| **System 1** | Fast, reflexive cognition (rule-based, <50ms) |
| **System 2** | Slow, deliberative cognition (LLM-based, 2-5s) |
| **Episodic Memory** | Personal experiences stored as embeddings |
| **Semantic Memory** | Factual knowledge stored in graph database |
| **Rumor** | Piece of information that can spread and mutate |
| **Proposal** | LLM output before it's committed to state (see §10.4 Deterministic Replay) |
| **Catalyst** | Event injected by Drama Director to increase tension |
| **Preemption** | Canceling deliberation for urgent reflex response |
| **Degradation** | Falling back to heuristics when LLM unavailable |
| **LOD Tier** | Level of Detail tier (Focus/Ambient/Simulation) controlling agent cognitive fidelity (see §6.7) |
| **Circuit Breaker** | Pattern that prevents cascade failures by temporarily disabling failing services (see §8.3.4) |
| **Deterministic Replay** | Ability to reproduce exact simulation runs by capturing LLM outputs (see §10.4) |
| **Budget Mode** | Development configuration minimizing LLM costs while maintaining functionality (see §12) |
| **Semantic Cache** | Cache that reuses LLM responses for semantically similar queries |

---

*End of MVP Specification*
