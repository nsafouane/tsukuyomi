# Agent Identity & Memory System Overhaul
## Tsukuyomi V2 - Technical Specification

**Date:** February 17, 2026  
**Version:** 1.0  
**Status:** Draft  
**Author:** Tanit

---

## 1. Overview

This specification defines a comprehensive overhaul of the Tsukuyomi agent system to create:
- **Deep agent identity** - Agents with genuine personal histories, values, and memories
- **Long-term memory** - Persistent episodic memory with RAG-based retrieval
- **Immersive prompts** - System prompts that make the LLM truly believe it IS the character
- **Isolated runtime** - Scenario-agnostic agents that work in ANY context

---

## 2. Problem Statement

### 2.1 Current Issues

| Issue | Current State | Impact |
|-------|---------------|--------|
| Memory | 3-turn window, no RAG | Agents forget everything |
| Identity | Generic prompts | LLM "plays" not "is" |
| Consistency | No belief tracking | Contradictory behavior |
| Isolation | Shared global state | Cross-contamination |
| Robustness | Hardcoded experiment logic | Only works for Angry Men |

### 2.2 Goals

1. Agents should remember everything that matters to them
2. Agents should believe they are real beings with lived experiences
3. Agents should be consistent across interactions
4. The same agent system should work for any scenario (jury, combat, social, etc.)

---

## 3. Architecture

### 3.1 Core Components

```
tsukuyomi/agent/
├── __init__.py
├── identity.py           # AgentIdentity, CoreValue, DefiningMemory
├── memory_system.py     # LongTermMemory with RAG retrieval
├── immersive_prompt.py  # Prompt builder for immersion
├── universal_agent.py   # Scenario-agnostic agent runtime
├── decision_engine.py   # Think → Feel → Reason → Act loop
├── exceptions.py        # Custom exceptions
└── scenarios/
    ├── __init__.py
    ├── base.py         # ScenarioContext base class
    ├── jury.py         # Jury deliberation scenario
    ├── combat.py       # Combat scenario
    └── social.py        # Social interaction scenario
```

---

## 4. Phase 1: Agent Identity System

### 4.1 Data Models

```python
@dataclass
class CoreValue:
    """A belief the agent will NOT compromise on."""
    value: str                    # The core belief
    source: str                   # Why they believe this
    intensity: float              # 0.0-1.0 (how absolute)
    non_negotiable: bool = True   # Can they ever change?


@dataclass
class DefiningMemory:
    """A pivotal memory that shaped who the agent is."""
    id: str
    event: str                    # What happened
    emotional_impact: str         # How it made them feel
    lesson_learned: str          # What they learned
    tags: List[str]              # For retrieval
    importance: float = 1.0       # 0.0-1.0


@dataclass  
class PersonalityTraits:
    """Detailed personality beyond Big Five."""
    big_five: Dict[str, float]   # OCEAN scores
    specific_traits: Dict[str, float]  # Specific traits
    communication_style: Dict[str, Any]  # How they speak
    triggers: List[str]          # Emotional triggers


@dataclass
class AgentIdentity:
    """
    Immutable core identity - WHO the agent IS.
    This never changes throughout the agent's life.
    """
    id: str
    name: str
    age: int
    occupation: str
    
    # Origin and history
    origin_story: str             # 2-3 paragraphs of life history
    current_location: str          # Where they are now
    
    # Core identity
    core_values: List[CoreValue]
    defining_memories: List[DefiningMemory]
    personality: PersonalityTraits
    
    # Physical/emotional baseline
    baseline_emotion: Dict[str, float]  # PAD baseline
    
    def get_immersive_description(self) -> str:
        """Generate a rich description of who this agent is."""
        pass
```

### 4.2 Requirements

- [ ] CoreValue dataclass with all fields
- [ ] DefiningMemory dataclass with all fields
- [ ] PersonalityTraits dataclass with all fields
- [ ] AgentIdentity dataclass with all fields
- [ ] AgentIdentity.get_immersive_description() method
- [ ] Unit tests for all dataclasses
- [ ] Unit tests for get_immersive_description()

---

## 5. Phase 2: Long-Term Memory System

### 5.1 Memory Architecture

```python
class MemoryType(Enum):
    EPISODIC = "episodic"    # Specific events with context
    SEMANTIC = "semantic"    # Facts and knowledge
    EMOTIONAL = "emotional"  # Emotional associations


@dataclass
class Memory:
    """A single memory unit."""
    id: str
    memory_type: MemoryType
    content: str              # What happened/is true
    context: str              # Circumstances around it
    emotional_tags: List[str]  # Emotions attached
    importance: float         # 0.0-1.0
    created_at: int           # Tick when created
    last_accessed: int        # Last retrieval tick
    
    # For RAG
    embedding: Optional[List[float]] = None


class LongTermMemory:
    """
    Persistent memory system with RAG retrieval.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: Dict[str, Memory] = {}
        self.vector_store = InMemoryVectorStore()  # or Qdrant
        
    async def store(self, memory: Memory) -> str:
        """Store a new memory."""
        pass
        
    async def retrieve(self, query: str, k: int = 10) -> List[Memory]:
        """Retrieve relevant memories using RAG."""
        pass
        
    async def get_recent(self, count: int = 10) -> List[Memory]:
        """Get most recent memories."""
        pass
        
    async def consolidate(self) -> None:
        """Periodically consolidate and summarize old memories."""
        pass
```

### 5.2 Requirements

- [ ] MemoryType enum
- [ ] Memory dataclass
- [ ] LongTermMemory class with store/retrieve/get_recent
- [ ] RAG integration for semantic retrieval
- [ ] Memory consolidation for long sessions
- [ ] Unit tests for memory operations

---

## 6. Phase 3: Immersive Prompt Builder

### 6.1 System Prompt Architecture

```python
class ImmersivePromptBuilder:
    """
    Builds prompts that create genuine agent identity.
    The LLM should believe it IS the character, not playing one.
    """
    
    def build_system_prompt(
        self, 
        identity: AgentIdentity,
        current_situation: str
    ) -> str:
        """
        Build the core system prompt that establishes identity.
        """
        pass
        
    def build_situation_prompt(
        self,
        memory_context: List[Memory],
        emotional_state: Dict,
        conversation_history: List[Dict],
        other_agents: List[str]
    ) -> str:
        """
        Build prompt for current situation context.
        """
        pass
        
    def build_action_prompt(
        self,
        available_actions: List[str],
        goals: List[str]
    ) -> str:
        """
        Build prompt for action selection.
        """
        pass
```

### 6.2 Prompt Templates

**Bad (Current):**
```
You are roleplaying as Arthur Miller, a juror...
```

**Good (New):**
```
You ARE Arthur Miller. You are not pretending, acting, or simulating.
You have 58 years of lived experience. Your memories are real to you.
Your emotions are genuine. Your beliefs have been shaped by your life.

WHO YOU ARE (at the core):
[Origin story]
[Core values]
[Defining memories]

RIGHT NOW:
[Current situation]
[What you're feeling]
[What you remember about this]
```

### 6.3 Requirements

- [ ] ImmersivePromptBuilder class
- [ ] build_system_prompt() method
- [ ] build_situation_prompt() method  
- [ ] build_action_prompt() method
- [ ] Unit tests for prompt generation

---

## 7. Phase 4: Universal Agent Runtime

### 7.1 Agent Architecture

```python
class UniversalAgent:
    """
    A scenario-agnostic agent that works in ANY context.
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        scenario: 'ScenarioContext'
    ):
        self.identity = identity
        self.scenario = scenario
        self.memory = LongTermMemory(identity.id)
        self.emotions = StateManager(identity.baseline_emotion)
        self.beliefs = BeliefSystem(identity.core_values)
        
    async def perceive(self, stimulus: Dict) -> Perception:
        """Process incoming stimulus."""
        pass
        
    async def remember(self, query: str) -> List[Memory]:
        """Retrieve relevant memories."""
        pass
        
    async def feel(self, perception: Perception) -> EmotionalState:
        """Process emotions from perception."""
        pass
        
    async def reason(
        self,
        perception: Perception,
        memories: List[Memory],
        emotion: EmotionalState
    ) -> Reasoning:
        """Deliberate about what to do."""
        pass
        
    async def act(self, reasoning: Reasoning) -> Action:
        """Execute the decided action."""
        pass
        
    async def respond(self, stimulus: Dict) -> Action:
        """Main response loop: Perceive → Remember → Feel → Reason → Act"""
        pass
```

### 7.2 Scenario System

```python
class ScenarioContext:
    """Base class for all scenarios."""
    
    @abstractmethod
    def get_available_actions(self) -> List[str]:
        pass
        
    @abstractmethod
    def get_other_agents(self) -> List[AgentIdentity]:
        pass
        
    @abstractmethod
    def get_current_situation(self) -> str:
        pass
        
    @abstractmethod
    def get_goals(self) -> List[str]:
        pass


class JuryDeliberationScenario(ScenarioContext):
    """Specific scenario for jury deliberation."""
    
    def __init__(self, case: Dict, jurors: List[AgentIdentity]):
        self.case = case
        self.jurors = jurors
        self.current_votes = {}
        
    def get_available_actions(self) -> List[str]:
        return ["SPEAK", "VOTE", "EXAMINE_EVIDENCE", "REFLECT", "IDLE"]
        
    def get_other_agents(self) -> List[AgentIdentity]:
        return [j for j in self.jurors if j.id != self.identity.id]
```

### 7.3 Requirements

- [ ] ScenarioContext abstract class
- [ ] UniversalAgent class
- [ ] respond() main loop
- [ ] JuryDeliberationScenario class
- [ ] Integration with existing LLMService
- [ ] Unit tests for agent loop
- [ ] Integration tests with LLM

---

## 8. Implementation Order

| Phase | Files | Tests | Days |
|-------|-------|-------|------|
| 1: Identity | identity.py, identity_test.py | 15 tests | 1 |
| 2: Memory | memory_system.py, memory_test.py | 20 tests | 1.5 |
| 3: Prompts | immersive_prompt.py, prompt_test.py | 10 tests | 1 |
| 4: Agent | universal_agent.py, agent_test.py | 15 tests | 2 |
| 5: Integration | Scenarios + integration tests | 10 tests | 1.5 |

**Total: ~7 days**

---

## 9. Acceptance Criteria

After implementation, the system must:

1. **Identity**: Agents have rich backstories that inform all responses
2. **Memory**: Agents can recall relevant memories from hours of simulation
3. **Consistency**: Agents maintain consistent beliefs and personality
4. **Immersion**: LLM generates responses that feel like a real person speaking
5. **Reusability**: Same agent code works for jury, combat, social scenarios
6. **Tests**: >90% test coverage, all tests passing

---

## 10. Backward Compatibility

The new agent system must:
- Integrate with existing FateEngine
- Work with existing gRPC interface
- Support existing profile JSON format (with extensions)
- Not break existing experiments

---

*End of Specification*
