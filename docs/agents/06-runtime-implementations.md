# Runtime Agent Implementations

**Path:** `tsukuyomi/agents/runtime/`

**Last Updated:** 2026-02-26

---

## Overview

The Runtime Agent Implementations provide the concrete implementations of the `BaseAgent` interface for both standalone and simulation modes. These are the **actual runnable agents** that use all the cognitive, emotional, and social components.

## Philosophy

Per the MVP v0.1 unified runtime architecture:
- **Same Core Logic**: Both modes use identical cognitive/emotional/social systems
- **Different Interfaces**: Simulation mode uses gRPC, Standalone mode uses direct LLM calls
- **Unified Lifecycle**: Both implement `start()`, `pause()`, `resume()`, `cleanup()`

---

## Component Structure

```
runtime/
├── standalone_agent.py    # UniversalAgent (direct LLM access)
├── simulation_agent.py    # AgentBrain (gRPC simulation mode)
├── context_manager.py     # Context management for agents
└── proposal_handler.py    # Proposal/action handling
```

---

## 1. UniversalAgent (`standalone_agent.py`)

**Location:** `tsukuyomi/agents/runtime/standalone_agent.py`

The complete, runnable agent for standalone mode with direct LLM access.

### AgentState

```python
class AgentState(Enum):
    """Current state of an agent."""
    IDLE = "idle"              # Not doing anything
    THINKING = "thinking"      # Processing input
    RESPONDING = "responding"   # Generating response
    ACTING = "acting"          # Performing an action
    RESTING = "resting"        # Taking a break
```

### AgentConfig

```python
@dataclass
class AgentConfig:
    """Configuration for an agent."""
    # Identity
    identity_file: str = ""          # Path to identity JSON
    identity_dict: Dict = None       # Or direct identity data

    # Memory
    max_memories: int = 10000
    memory_file: str = ""

    # LLM
    llm_provider: str = "groq"       # groq, openai, anthropic
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.8
    llm_max_tokens: int = 500

    # Behavior
    prompt_style: str = "full"       # full, concise, intense
    auto_memory: bool = True         # Automatically store experiences

    # Scenario
    scenario_name: str = "unknown"
    scenario_context: str = ""
```

### UniversalAgent Class

```python
class UniversalAgent(BaseAgent):
    """
    A complete, runnable agent for any scenario.

    This is the main entry point for creating Tsukuyomi agents in standalone mode.

    Usage:
        agent = UniversalAgent(config)
        agent.load_identity(identity_file="juror.json")
        agent.set_llm(llm_function)
        response = await agent.respond("What do you think?")
    """

    def __init__(self, config: AgentConfig = None)

    # Core Components
    identity: Optional[AgentIdentity]
    memory: Optional[LongTermMemory]
    prompt_builder: Optional[ImmersivePromptBuilder]
    deliberation_engine: Optional[DeliberationEngine]
    emotional_expression: Optional[EmotionalExpression]

    # State
    state: AgentState
    current_tick: int
    conversation_history: List[Dict[str, Any]]
```

### Key Methods

#### Identity and Configuration

```python
def load_identity(
    self,
    identity_file: str = None,
    identity_dict: Dict = None
) -> None:
    """
    Load agent identity from file or dict.

    Initializes:
    - Identity (who they are)
    - Memory (what they remember)
    - Prompt builder (how they express themselves)
    - Deliberation engine (how they think)
    - Emotional expression (how they feel)
    """

def set_llm(self, llm_call: Callable) -> None:
    """
    Set the LLM call function.

    Allows injecting any LLM provider (OpenAI, Groq, Anthropic, etc.)
    """
```

#### Core Interaction

```python
async def respond(
    self,
    input_text: str,
    context: PromptContext = None,
    store_interaction: bool = True
) -> str:
    """
    Generate a response to input.

    Process:
    1. Phase 1: Internal deliberation (thinking before speaking)
    2. Phase 2: Emotional expression (tone modifiers)
    3. Build prompt with memory retrieval
    4. Call LLM
    5. Store interaction in memory

    Returns:
        Agent's response
    """

async def observe(
    self,
    event: str,
    importance: float = 0.5,
    emotional_tags: List[str] = None
) -> str:
    """
    Observe and remember an event without responding.

    Returns:
        Memory ID
    """

async def reflect(
    self,
    topic: str = "",
    k_memories: int = 5
) -> str:
    """
    Reflect on past experiences and generate insights.

    Retrieves relevant memories and generates reflection text.
    """
```

#### State Management

```python
def advance_tick(self, ticks: int = 1) -> None:
    """Advance the simulation tick."""

def get_state(self) -> Dict[str, Any]:
    """Get current agent state for display."""

def get_emotional_baseline(self) -> Dict[str, float]:
    """Get emotional baseline PAD values."""

def save_state(self, filepath: str) -> None:
    """Save agent state to file."""

@classmethod
def load_state(cls, filepath: str) -> 'UniversalAgent':
    """Load agent state from file."""
```

#### BaseAgent Implementation

```python
async def perceive(self, *args, **kwargs):
    """Perceive environment (abstract method)."""

async def deliberate(self, *args, **kwargs):
    """Internal reasoning (abstract method)."""

async def act(self, *args, **kwargs):
    """Perform an action."""

def start(self):
    """Start agent lifecycle."""

def pause(self):
    """Pause agent processing."""

def resume(self):
    """Resume agent processing."""

def cleanup(self):
    """Clean up agent resources."""
```

### Helper Functions

```python
def create_agent(
    name: str,
    age: int,
    occupation: str,
    origin_story: str,
    core_values: List[Dict],
    defining_memories: List[Dict],
    personality: Dict,
    scenario_name: str = "unknown",
    **kwargs
) -> UniversalAgent:
    """
    Helper to create a fully configured agent.

    Returns:
        Configured UniversalAgent with identity loaded
    """
```

### Example Usage

```python
# Create configuration
config = AgentConfig(
    llm_provider="groq",
    llm_model="llama-3.3-70b-versatile",
    scenario_name="jury_deliberation"
)

# Create agent
agent = UniversalAgent(config)

# Load identity
agent.load_identity(identity_file="juror3.json")

# Set LLM
agent.set_llm(my_llm_function)

# Interact
response = await agent.respond("What's your verdict?")
print(response)

# Save state
agent.save_state("juror3_state.json")
```

---

## 2. AgentBrain / SimulationAgent (`simulation_agent.py`)

**Location:** `tsukuyomi/agents/runtime/simulation_agent.py`

The simulation-mode agent implementation with gRPC connectivity.

### AgentBrain Class

```python
class AgentBrain(BaseAgent):
    """
    Simulation-mode agent connected to FateEngine via gRPC.

    Also known as: SimulationAgent

    Features:
    - Receives TickState from engine
    - Perceives environment
    - Generates proposals
    - Handles resolutions
    - All cognitive/emotional/social systems intact
    - NeedsSystem for motivational drives
    - SpatialIndex integration for environmental awareness
    """

    def __init__(
        self,
        actor_id: str,
        identity: AgentIdentity,
        server_addr: str = "localhost:50051"
    )

    # Core Systems
    self.actor_id: str
    self.profile: Dict
    self.client: FateEngineClient
    self.memory: MemoryManager

    # Emotional System
    self.state_manager: StateManager          # PAD-based emotional state
    self.expression_layer: EmotionalExpression  # Tone generation

    # Belief System
    self.belief_manager: BeliefManager        # Evidence-based beliefs

    # Perception System
    self.perception: PerceptionPipeline        # Environmental perception
    self.working_memory: WorkingMemory        # Bounded cognitive context

    # Social System
    self.relationships: RelationshipManager

    # Motivational System (Needs)
    self.needs: NeedsSystem                    # Internal drives (hunger, fatigue, etc.)

    # Spatial Awareness (Phase 2)
    self.spatial_index: Optional[SpatialIndex] = None
    self.spatial_logic: Optional[SpatialLogic] = None
```

### Key Differences from UniversalAgent

| Feature | UniversalAgent | AgentBrain (Simulation) |
|---------|----------------|-------------------------|
| LLM Access | Direct function call | Via gRPC server |
| Environment | None (standalone) | WorldState from engine |
| Actions | Returns text | Generates Proposals |
| State | Local storage | Synced with engine |
| Use Case | Chat, interactive | Simulation, batch |

### Simulation-Specific Components

```python
# gRPC Connection
channel: grpc.aio.Channel
stub: core_pb2_grpc.FateEngineStub

# Tick Processing
async def process_tick(self, tick_state: core_pb2.TickState):
    """
    Process a simulation tick.

    1. Perceive environment from TickState
    2. Run deliberation
    3. Generate proposals
    4. Submit to engine
    """

# Proposal Generation
async def generate_proposal(
    self,
    context: Dict
) -> Proposal:
    """Generate a proposal for the current tick."""

# Resolution Handling
async def handle_resolution(
    self,
    resolution: Resolution
):
    """Handle outcome of previous proposal."""

# Spatial Integration (Phase 2)
def set_spatial_index(self, spatial_index):
    """
    Connect the agent to the SpatialIndex.

    Enables:
    - Efficient proximity queries
    - Nearby entity detection
    - Line-of-sight calculations

    The spatial_index is shared with the PerceptionPipeline.
    """

def set_spatial_logic(self, spatial_logic):
    """
    Connect the agent to SpatialLogic module.

    Enables:
    - Distance calculations
    - Range checks
    - Spatial relationship queries
    """

# Needs System Integration
def update_needs(self, dt: float = 1.0):
    """
    Update all internal needs.

    Needs increase over time based on decay_rate.
    Critical needs trigger autonomous behavior.
    """
```

---

## 3. Context Manager (`context_manager.py`)

**Location:** `tsukuyomi/agents/runtime/context_manager.py`

Manages context for agent decision-making.

### AgentContextManager

```python
class AgentContextManager:
    """
    Manages the context for agent cognitive processing.

    Provides:
    - Current situation awareness
    - Recent event history
    - Emotional state integration
    - Memory retrieval context
    """

    def __init__(self, agent_id: str)

    def build_context(
        self,
        world_state: WorldState,
        current_tick: int,
        emotional_state: EmotionalState
    ) -> AgentContext:
        """Build complete context for cognitive processing."""

    def update_context(
        self,
        context: AgentContext,
        new_events: List[Event]
    ) -> AgentContext:
        """Update context with new events."""
```

---

## 4. Proposal Handler (`proposal_handler.py`)

**Location:** `tsukuyomi/agents/runtime/proposal_handler.py`

Handles proposal generation and resolution handling.

### ProposalHandler

```python
class ProposalHandler:
    """
    Handles proposal generation for simulation agents.

    Process:
    1. Analyze current situation
    2. Generate action proposals
    3. Format for engine
    4. Handle resolution feedback
    """

    def __init__(self, agent_id: str)

    async def generate_proposal(
        self,
        context: AgentContext,
        available_actions: List[Action]
    ) -> Proposal:
        """Generate a proposal for the current tick."""

    async def handle_resolution(
        self,
        resolution: Resolution,
        context: AgentContext
    ):
        """Process resolution and update agent state."""
```

---

## Architecture Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    BaseAgent (Abstract)                        │
│  + perceive()  + deliberate()  + act()                          │
│  + start()  + pause()  + resume()  + cleanup()                 │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                     ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│      UniversalAgent        │   │      AgentBrain            │
│   (Standalone Mode)        │   │   (Simulation Mode)        │
│                           │   │                           │
│ - Direct LLM calls         │   │ - gRPC to FateEngine      │
│ - Local state              │   │ - WorldState from engine  │
│ - Text responses          │   │ - Proposal submission     │
│ - Chat/interactive        │   │ - Simulation/batch        │
└───────────────────────────┘   └───────────────────────────┘
```

---

## Common Components

Both implementations share:

```python
# Identity System
from tsukuyomi.agents.core.identity import AgentIdentity

# Memory System
from tsukuyomi.agents.cognitive.memory.memory_system import LongTermMemory

# Deliberation
from tsukuyomi.agents.cognitive.deliberation import DeliberationEngine

# Emotional Expression
from tsukuyomi.agents.internal.emotional_expression import EmotionalExpression

# Prompt Building
from tsukuyomi.agents.prompts.immersive_prompt import ImmersivePromptBuilder

# Needs System (Motivational Drives)
from tsukuyomi.agents.internal.needs.needs_system import NeedsSystem, NeedType

# Belief System
from tsukuyomi.agents.internal.beliefs.unified import BeliefManager

# Working Memory
from tsukuyomi.agents.cognitive.working_memory import WorkingMemory
```

### Component Usage Summary

| Component | UniversalAgent | AgentBrain | Purpose |
|-----------|----------------|------------|---------|
| NeedsSystem | ✅ | ✅ | Prevents static behavior, drives autonomous action |
| SpatialIndex | ❌ | ✅ | Environmental awareness for simulation mode |
| WorkingMemory | ✅ | ✅ | Bounded cognitive context (7±2 items) |
| BeliefManager | ✅ | ✅ | Evidence-based belief tracking |
| DeliberationEngine | ✅ | ✅ | Internal reasoning before action |

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_universal_agent.py` | UniversalAgent lifecycle, respond, observe |
| `test_agent_brain.py` | AgentBrain gRPC, tick processing |
| `test_context_manager.py` | Context building |
| `test_proposal_handler.py` | Proposal generation |

---

## Dependencies

**Internal:**
- `tsukuyomi.agents.core.base_agent` - BaseAgent abstract class
- `tsukuyomi.agents.core.identity` - AgentIdentity
- `tsukuyomi.agents.cognitive.memory.memory_system` - LongTermMemory
- `tsukuyomi.agents.cognitive.deliberation` - DeliberationEngine
- `tsukuyomi.agents.prompts.immersive_prompt` - ImmersivePromptBuilder
- `tsukuyomi.agents.internal.emotional_expression` - EmotionalExpression
- `tsukuyomi.transport.proto.core_pb2` - gRPC protocol (simulation mode)

**External:**
- `asyncio` - Async operations
- `dataclasses` - Data structures
- `enum` - Enumerations
- `json` - Serialization
- `logging` - Logging
- `typing` - Type hints

**Simulation Mode Only:**
- `grpc.aio` - Async gRPC
- `grpc.aio.Channel` - gRPC channel

---

## Design Principles

1. **Unified Base**: Both inherit from BaseAgent
2. **Same Cognitive Core**: Identical deliberation, emotion, memory systems
3. **Different Interface**: LLM vs gRPC
4. **Lifecycle Management**: All agents support start/pause/resume/cleanup
5. **State Persistence**: Both can save/load state
6. **Scenario Agnostic**: Works with any scenario (jury, marketplace, etc.)
