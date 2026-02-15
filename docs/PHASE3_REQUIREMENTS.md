# Phase 3 Requirements: Persistence & Scale
## Tsukuyomi V2 Development

**Version:** 1.0
**Status:** Draft
**Start Date:** 2026-02-15
**Phase Duration:** Weeks 6-8

---

## 📋 Document Overview

This document defines the technical requirements, acceptance criteria, and implementation priorities for **Phase 3: Persistence & Scale** of Tsukuyomi V2. This phase focuses on transforming Tsukuyomi from a session-based prototype into a robust, long-running service capable of persistent world states and multi-node federation.

---

## 🎯 Phase Objectives

### Primary Goals
1. **Persistent World State**: Enable world snapshots and restoration across sessions
2. **Database Integration**: Migrate from in-memory to PostgreSQL-based storage
3. **Federation Architecture**: Lay foundation for multi-world simulations
4. **Scalability**: Support 50+ agents with <200ms tick time

### Success Metrics
- [ ] World state can be saved and restored without data loss
- [ ] Database queries complete in <50ms (per agent operation)
- [ ] Support for simultaneous SaveWorld/LoadWorld operations
- [ ] Federation prototype enables inter-node agent travel

---

## 🗄️ Task 1: Database Schema Design (PostgreSQL)

### 1.1 Overview
Design and implement a PostgreSQL database schema to persist all Tsukuyomi core data structures (WorldState, Actors, Objects, Interactions).

### 1.2 Technical Requirements

#### 1.2.1 Core Tables

**Table: `worlds`**
```sql
CREATE TABLE worlds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_tick BIGINT DEFAULT 0,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'active' -- active, paused, archived
);
```

**Table: `world_snapshots`**
```sql
CREATE TABLE world_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    tick_number BIGINT NOT NULL,
    snapshot_data JSONB NOT NULL, -- Complete WorldState as JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    compressed_size_bytes INTEGER,
    UNIQUE(world_id, tick_number)
);
```

**Table: `actors`**
```sql
CREATE TABLE actors (
    id UUID PRIMARY KEY,
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    state VARCHAR(100) NOT NULL,
    current_location VARCHAR(255),
    inventory JSONB DEFAULT '[]',
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Table: `actor_states`** (Historical tracking)
```sql
CREATE TABLE actor_states (
    id BIGSERIAL PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    tick_number BIGINT NOT NULL,
    state JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Table: `environment_objects`**
```sql
CREATE TABLE environment_objects (
    id UUID PRIMARY KEY,
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    interactive BOOLEAN DEFAULT true,
    properties JSONB DEFAULT '{}',
    hidden_properties JSONB DEFAULT '{}',
    state VARCHAR(100),
    owner_id UUID REFERENCES actors(id),
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Table: `affordances`**
```sql
CREATE TABLE affordances (
    id BIGSERIAL PRIMARY KEY,
    object_id UUID NOT NULL REFERENCES environment_objects(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    precondition TEXT,
    effect_description TEXT,
    semantic_tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Table: `interactions`**
```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES actors(id),
    target_id UUID NOT NULL,
    interaction_type VARCHAR(100) NOT NULL,
    tick_number BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

**Table: `proposals`**
```sql
CREATE TABLE proposals (
    id UUID PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actors(id),
    action_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    tick_number BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending' -- pending, resolved, rejected
);
```

**Table: `resolutions`**
```sql
CREATE TABLE resolutions (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES proposals(id),
    success BOOLEAN NOT NULL,
    outcome JSONB DEFAULT '{}',
    reason TEXT,
    modified_action JSONB,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 1.2.2 Federation Tables (Foundation)

**Table: `nodes`**
```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    endpoint_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'online', -- online, offline, maintenance
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

**Table: `portals`**
```sql
CREATE TABLE portals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_world_id UUID NOT NULL REFERENCES worlds(id),
    destination_node_id UUID NOT NULL REFERENCES nodes(id),
    destination_world_id UUID,
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    activation_conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 1.2.3 Indexes & Performance

```sql
-- Performance indexes
CREATE INDEX idx_world_snapshots_tick ON world_snapshots(world_id, tick_number DESC);
CREATE INDEX idx_actors_world ON actors(world_id);
CREATE INDEX idx_actors_position ON actors(world_id, position_x, position_y);
CREATE INDEX idx_objects_world ON environment_objects(world_id);
CREATE INDEX idx_interactions_actor ON interactions(actor_id);
CREATE INDEX idx_interactions_tick ON interactions(tick_number);
CREATE INDEX idx_proposals_tick ON proposals(tick_number);
CREATE INDEX idx_proposals_status ON proposals(status);

-- Full-text search for affordances
CREATE INDEX idx_affordances_tags ON affordances USING GIN(semantic_tags);

-- Spatial queries (PostGIS optional, or basic bounding box)
CREATE INDEX idx_actors_spatial ON actors(world_id, position_x, position_y);
CREATE INDEX idx_objects_spatial ON environment_objects(world_id, position_x, position_y);
```

### 1.3 Acceptance Criteria

- [ ] **AC-1.1**: All tables created with proper foreign keys and constraints
- [ ] **AC-1.2**: Migration script (`migrations/001_initial_schema.sql`) passes without errors
- [ ] **AC-1.3**: `pgbench` test shows <10ms read latency for single actor lookup
- [ ] **AC-1.4**: Bulk insert of 1000 actors completes in <500ms
- [ ] **AC-1.5**: JSONB queries (e.g., `inventory @> '[gold_coin]'`) are indexed
- [ ] **AC-1.6**: Federation tables support multi-node topology queries

### 1.4 Implementation Dependencies
- PostgreSQL 15+
- `asyncpg` for async Python connections
- Alembic for database migrations (optional, recommended)

---

## 🔌 Task 2: SaveWorld/LoadWorld gRPC Methods

### 2.1 Overview
Extend the `FateEngineService` with persistence operations to save world snapshots and restore from saved states.

### 2.2 Technical Requirements

#### 2.2.1 Proto Definitions

Add to `fate_engine_service.proto`:

```protobuf
// Persistence operations
service FateEngineService {
  // ... existing methods ...

  // Save current world state to database
  rpc SaveWorld (SaveWorldRequest) returns (SaveWorldResponse);

  // Load world state from database (resume simulation)
  rpc LoadWorld (LoadWorldRequest) returns (LoadWorldResponse);

  // List available world snapshots
  rpc ListSnapshots (ListSnapshotsRequest) returns (ListSnapshotsResponse);

  // Delete a world snapshot
  rpc DeleteSnapshot (DeleteSnapshotRequest) returns (DeleteSnapshotResponse);
}

// SaveWorld request
message SaveWorldRequest {
  string world_id = 1; // Optional: uses current world if not specified
  string description = 2; // Optional snapshot description
  bool include_actor_states = 3; // Whether to save per-actor historical states
}

// SaveWorld response
message SaveWorldResponse {
  bool success = 1;
  string message = 2;
  int64 tick_number = 3;
  string snapshot_id = 4;
  int64 size_bytes = 5;
}

// LoadWorld request
message LoadWorldRequest {
  string world_id = 1;
  int64 tick_number = 2; // Optional: loads latest if not specified
  bool reset_actors = 3; // Reset all actors to saved state (vs merge)
}

// LoadWorld response
message LoadWorldResponse {
  bool success = 1;
  string message = 2;
  int64 tick_number = 3;
  int32 actors_restored = 4;
  int32 objects_restored = 5;
  tsukuyomi.common.Timestamp timestamp = 6;
}

// ListSnapshots request
message ListSnapshotsRequest {
  string world_id = 1;
  int32 limit = 2; // Optional: default 50
  int64 after_tick = 3; // Optional: pagination cursor
}

// ListSnapshots response
message ListSnapshotsResponse {
  repeated SnapshotMetadata snapshots = 1;
  string next_cursor = 2;
}

message SnapshotMetadata {
  string snapshot_id = 1;
  int64 tick_number = 2;
  tsukuyomi.common.Timestamp timestamp = 3;
  int64 size_bytes = 4;
  string description = 5;
}

// DeleteSnapshot request
message DeleteSnapshotRequest {
  string snapshot_id = 1;
}

// DeleteSnapshot response
message DeleteSnapshotResponse {
  bool success = 1;
  string message = 2;
}
```

#### 2.2.2 Implementation Requirements

**SaveWorld Logic:**
1. Serialize current `WorldState` to JSON
2. Apply compression (gzip/zstd) if size > 1MB
3. Insert into `world_snapshots` table
4. Optionally save individual actor states to `actor_states`
5. Return snapshot metadata

**LoadWorld Logic:**
1. Query `world_snapshots` for specified tick (or latest)
2. Decompress and deserialize JSON
3. Clear current in-memory world state (if `reset_actors=true`)
4. Reconstruct Actors, Objects, Locations from data
5. Restore simulation tick counter
6. Resume simulation (pause for client reconnection)

#### 2.2.3 Backend Implementation Structure

```
tsukuyomi/core/
├── fate_engine.py          # Extend with persistence methods
├── persistence/
│   ├── __init__.py
│   ├── database.py        # PostgreSQL connection pool
│   ├── repository.py      # Data access layer
│   └── serializers.py     # Protobuf ↔ Database mapping
```

### 2.3 Acceptance Criteria

- [ ] **AC-2.1**: `SaveWorld` creates a valid snapshot with all data preserved
- [ ] **AC-2.2**: `LoadWorld` restores world to exact state at specified tick
- [ ] **AC-2.3**: Save operation for 50 agents completes in <1000ms
- [ ] **AC-2.4**: Load operation completes in <2000ms (including decompression)
- [ ] **AC-2.5**: Snapshots are compressed (ratio > 3:1 for text-heavy data)
- [ ] **AC-2.6**: `ListSnapshots` supports pagination with cursor
- [ ] **AC-2.7**: Save/Load operations are atomic (no partial writes/reads)
- [ ] **AC-2.8**: Concurrent `SaveWorld` requests don't corrupt data

### 2.4 Implementation Dependencies
- Task 1 (Database Schema) must be completed first
- Existing `WorldState` proto structure
- Connection pooling (asyncpg.SAConnection)

---

## 🧠 Task 3: Long-Term Memory (RAG) Integration

### 3.1 Overview
Integrate a vector database for agent long-term memory retrieval, enabling agents to recall past events, relationships, and contextual information across sessions.

> **Note**: This task is originally in Phase 4 but included here per product requirement for Phase 3.

### 3.2 Technical Requirements

#### 3.2.1 Vector Database Schema

**Table: `agent_memories`** (PostgreSQL + pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- The memory text
    embedding vector(1536), -- OpenAI embedding dimension (adjustable)
    metadata JSONB DEFAULT '{}', -- {tick: 5000, type: "conversation", tags: ["trade"]}
    memory_type VARCHAR(50) NOT NULL, -- observation, reflection, social, factual
    importance_score FLOAT DEFAULT 0.5, -- 0.0-1.0
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_memories_actor ON agent_memories(actor_id);
CREATE INDEX idx_memories_type ON agent_memories(memory_type);
```

#### 3.2.2 Memory Types

| Memory Type | Description | Example |
|-------------|-------------|---------|
| `observation` | Agent witnessed an event | "Marcus overcharged the peasant for bread" |
| `reflection` | Agent's internal thought | "I feel guilty about the unfair trade" |
| `social` | Relationship data | "The guard seems friendly toward travelers" |
| `factual` | Learned information | "The tavern opens at 6 PM daily" |
| `spatial` | Location knowledge | "The shortcut through the alley saves 2 minutes" |

#### 3.2.3 Proto Extensions

Add to `core.proto`:

```protobuf
// Memory-related messages
message MemoryQuery {
  string actor_id = 1;
  string query_text = 2; // Semantic query
  repeated string memory_types = 3; // Filter by type
  int32 limit = 4; // Default: 5
  float min_relevance = 5; // Default: 0.7
  int64 after_tick = 6; // Optional time filter
}

message Memory {
  string memory_id = 1;
  string actor_id = 2;
  string content = 3;
  string memory_type = 4;
  float relevance_score = 5;
  int64 tick_number = 6;
  tsukuyomi.common.Timestamp timestamp = 7;
  map<string, string> metadata = 8;
}

message StoreMemoryRequest {
  string actor_id = 1;
  string content = 2;
  string memory_type = 3;
  float importance = 4;
  map<string, string> metadata = 5;
}

message StoreMemoryResponse {
  bool success = 1;
  string memory_id = 2;
}
```

Add to `fate_engine_service.proto`:

```protobuf
service FateEngineService {
  // ... existing methods ...

  // Query agent's long-term memory
  rpc QueryMemory (MemoryQuery) returns (stream Memory);

  // Store a new memory for an agent
  rpc StoreMemory (StoreMemoryRequest) returns (StoreMemoryResponse);

  // Update memory importance/access tracking
  rpc UpdateMemory (UpdateMemoryRequest) returns (UpdateMemoryResponse);

  // Delete a memory
  rpc DeleteMemory (DeleteMemoryRequest) returns (DeleteMemoryResponse);
}

message UpdateMemoryRequest {
  string memory_id = 1;
  float importance_delta = 2; // Increment/decrement
}

message UpdateMemoryResponse {
  bool success = 1;
}

message DeleteMemoryRequest {
  string memory_id = 1;
}

message DeleteMemoryResponse {
  bool success = 1;
}
```

#### 3.2.4 Implementation Architecture

```
tsukuyomi/brain/
├── memory/
│   ├── __init__.py
│   ├── vector_db.py         # Vector database client (pgvector/Qdrant)
│   ├── embedding_client.py  # OpenAI/Cohere embedding API
│   ├── memory_manager.py    # High-level memory operations
│   └── relevance_scorer.py  # Semantic similarity + time decay
```

**Memory Manager Interface:**

```python
class MemoryManager:
    async def query(
        self,
        actor_id: str,
        query_text: str,
        memory_types: List[str] = None,
        limit: int = 5,
        min_relevance: float = 0.7
    ) -> List[Memory]

    async def store(
        self,
        actor_id: str,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        metadata: Dict = None
    ) -> str

    async def update_importance(
        self,
        memory_id: str,
        delta: float
    ) -> bool

    async def consolidate(self, actor_id: str) -> int:
        """Merge similar memories, prune low-importance ones"""
```

#### 3.2.5 Integration with AgentBrain

**Agent Prompt Template Extension:**

```
{{ agent_name }}, consider the following:

CURRENT CONTEXT:
{{ current_percepts }}

RELEVANT MEMORIES:
{% for memory in relevant_memories %}
- [{{ memory.tick_number }}] {{ memory.content }} (relevance: {{ memory.relevance }})
{% endfor %}

Based on these memories and current context, what would you do?
```

**Memory Injection Strategy:**
- Query memories with agent's current percept context
- Filter by relevance (>0.7) and recency (last 1000 ticks)
- Include up to 5 memories in LLM prompt
- Track which memories influenced each action

### 3.3 Acceptance Criteria

- [ ] **AC-3.1**: Vector database schema supports efficient similarity search
- [ ] **AC-3.2**: Memory query returns relevant memories in <50ms (up to 1000 memories)
- [ ] **AC-3.3**: Memory storage completes in <100ms (including embedding generation)
- [ ] **AC-3.4**: AgentBrain successfully injects memories into prompts
- [ ] **AC-3.5**: Memory consolidation reduces memory count by >30% (removing duplicates)
- [ ] **AC-3.6**: Importance scores adjust based on access frequency
- [ ] **AC-3.7**: RAG queries support semantic similarity across time (e.g., "where did I see Marcus?")
- [ ] **AC-3.8**: Per-agent memory limit enforced (default: 1000 memories, auto-prune)

### 3.4 Implementation Dependencies
- Task 1 (Database Schema) with pgvector extension
- Embedding API (OpenAI/Cohere/Local models)
- AgentBrain prompt template system

---

## 🌐 Task 4: Multi-Node Federation Foundation

### 4.1 Overview
Design and implement the foundation for multi-node Tsukuyomi deployments, enabling agents to travel between worlds and share events across nodes.

### 4.2 Technical Requirements

#### 4.2.1 Federation Architecture

```
┌─────────────────┐
│  Federation API │
└────────┬────────┘
         │
    ┌────┴────┬─────────────────────┬────────────┐
    │         │                     │            │
┌───▼────┐ ┌─▼──────┐       ┌──────▼─────┐ ┌────▼─────┐
│ Node A │ │ Node B │  ...  │   Node N   │ │ Discovery│
│ Town   │ │ Forest │       │ Dungeon    │ │ Service  │
└────────┘ └────────┘       └────────────┘ └──────────┘
```

#### 4.2.2 Proto Extensions

Add to `fate_engine_service.proto`:

```protobuf
// Federation operations
service FateEngineService {
  // ... existing methods ...

  // Register this node with federation
  rpc RegisterNode (RegisterNodeRequest) returns (RegisterNodeResponse);

  // Discover other nodes in federation
  rpc DiscoverNodes (DiscoverNodesRequest) returns (DiscoverNodesResponse);

  // Transfer agent to another node
  rpc TransferAgent (TransferAgentRequest) returns (TransferAgentResponse);

  // Receive agent from another node
  rpc ReceiveAgent (ReceiveAgentRequest) returns (ReceiveAgentResponse);

  // Sync events across nodes (optional, for real-time sharing)
  rpc SyncEvents (stream SyncEventMessage) returns (stream SyncEventAck);
}

// RegisterNode request
message RegisterNodeRequest {
  string node_id = 1;
  string node_name = 2;
  string endpoint_url = 3; // gRPC endpoint
  map<string, string> metadata = 4;
}

// RegisterNode response
message RegisterNodeResponse {
  bool success = 1;
  string federation_id = 2;
  repeated NodeInfo known_nodes = 3;
}

// DiscoverNodes request
message DiscoverNodesRequest {
  string node_id = 1;
  string federation_id = 2;
}

// DiscoverNodes response
message DiscoverNodesResponse {
  repeated NodeInfo nodes = 1;
  int64 federation_timestamp = 2;
}

// Node information
message NodeInfo {
  string node_id = 1;
  string node_name = 2;
  string endpoint_url = 3;
  string status = 4; // online, offline, maintenance
  tsukuyomi.common.Timestamp last_heartbeat = 5;
  map<string, string> metadata = 6;
}

// TransferAgent request (outgoing)
message TransferAgentRequest {
  string actor_id = 1;
  string destination_node_id = 2;
  string destination_world_id = 3;
  string portal_id = 4;
  bool include_memories = 5;
}

// TransferAgent response
message TransferAgentResponse {
  bool success = 1;
  string message = 2;
  string transfer_token = 3; // For verification at destination
}

// ReceiveAgent request (incoming)
message ReceiveAgentRequest {
  string actor_id = 1;
  string source_node_id = 2;
  tsukuyomi.core.Actor actor_data = 3;
  string transfer_token = 4;
  map<string, string> actor_memories = 5; // Optional: embed memory content
}

// ReceiveAgent response
message ReceiveAgentResponse {
  bool success = 1;
  string new_actor_id = 2; // If ID collision, new ID generated
  string message = 3;
}

// Event synchronization
message SyncEventMessage {
  string source_node_id = 1;
  string source_world_id = 2;
  string event_type = 3; // chat, trade, combat, etc.
  string event_data = 4; // JSON payload
  int64 tick_number = 5;
}

message SyncEventAck {
  string event_id = 1;
  bool processed = 2;
}
```

#### 4.2.3 Portal System

**Portal Logic:**
1. Agent enters portal zone (position-based trigger)
2. FateEngine validates portal conditions
3. Generate `TransferAgentRequest` to destination node
4. Serialize agent state (including memories if configured)
5. Remove actor from local world
6. Destination node validates and reconstitutes agent
7. Agent spawns at designated portal location

**Portal Activation Conditions (Examples):**
```json
{
  "type": "travel",
  "conditions": {
    "has_ticket": true,
    "time_of_day": ["06:00-22:00"],
    "not_wanted": false
  },
  "cost": {
    "gold": 10,
    "stamina": 5
  },
  "destination": {
    "node_id": "forest-node",
    "world_id": "deep-forest",
    "portal_id": "entrance"
  }
}
```

#### 4.2.4 Implementation Structure

```
tsukuyomi/core/
├── federation/
│   ├── __init__.py
│   ├── node.py           # Local node representation
│   ├── discovery.py      # Node discovery & heartbeats
│   ├── agent_transfer.py # Agent serialization/deserialization
│   └── portal.py         # Portal management
```

#### 4.2.5 Discovery Service

**Options:**
1. **Static Configuration**: Hardcode node list in config (simple, MVP)
2. **Central Registry**: Single discovery server (easier coordination)
3. **Consul/etcd**: Service discovery system (production-ready)
4. **P2P Gossip**: Nodes discover each other dynamically

**MVP Approach (Static + Heartbeats):**
```python
# config/federation.yaml
nodes:
  - id: "town-node"
    name: "Town Square"
    endpoint: "localhost:50051"
  - id: "forest-node"
    name: "Forest Outpost"
    endpoint: "localhost:50052"

# Heartbeat: every 30s
# Status timeout: 90s
```

#### 4.2.6 Agent Transfer Flow

```
[Node A: Town]                [Node B: Forest]
     |                               |
Agent enters portal              |
     |                               |
Validate portal conditions         |
     |                               |
Serialize agent state              |
     |                               |
Generate transfer token            |
     | ----------TransferRequest-----> |
     |                               |
     |                               Validate token
     |                               |
     |                               Deserialize agent
     |                               |
     |                               Spawn at destination portal
     |                               |
Remove from Node A              |
     | <------TransferResponse------- |
     |                               |
[Agent now on Node B]        [Agent now on Node B]
```

### 4.3 Acceptance Criteria

- [ ] **AC-4.1**: Two nodes can register with each other and exchange node info
- [ ] **AC-4.2**: Agent successfully transfers from Node A to Node B via portal
- [ ] **AC-4.3**: Agent state (inventory, position, memories) preserved across transfer
- [ ] **AC-4.4**: Transfer completes in <500ms (excluding network latency)
- [ ] **AC-4.5**: Invalid transfer tokens are rejected
- [ ] **AC-4.6**: Node status updates (online/offline) propagate within 90s
- [ ] **AC-4.7**: Portal conditions correctly block/prevent transfers
- [ ] **AC-4.8**: Duplicate actor IDs handled (collision resolution generates new ID)

### 4.4 Implementation Dependencies
- Task 1 (Database Schema) - nodes/portals tables
- Task 2 (Persistence) - actor state serialization
- Network connectivity between nodes (gRPC)

---

## 📊 Task Prioritization & Dependencies

### Dependency Graph

```
Task 1: Database Schema Design
    |
    +---> Task 2: SaveWorld/LoadWorld gRPC Methods
    |
    +---> Task 3: Long-Term Memory (RAG) Integration
    |
    +---> Task 4: Multi-Node Federation Foundation
            |
            +---> Requires Task 2 (agent transfer uses serialization)
```

### Sprint Breakdown (3 Weeks)

**Week 6: Database Core**
- Day 1-2: Task 1.1-1.2 (Core tables design + implementation)
- Day 3-4: Task 1.2.3 (Indexes + performance testing)
- Day 5: Task 1.3 (Acceptance testing)
- Day 6-7: Buffer / Documentation

**Week 7: Persistence Implementation**
- Day 1-2: Task 2.1-2.2 (Proto definitions + backend structure)
- Day 3-4: Task 2.2.2-2.2.3 (SaveWorld/LoadWorld implementation)
- Day 5: Task 2.3 (Performance testing + optimization)
- Day 6-7: Buffer / Documentation

**Week 8: Memory & Federation**
- Day 1-2: Task 3.1-3.2 (Vector DB setup + MemoryManager)
- Day 3: Task 3.3 (AgentBrain integration)
- Day 4: Task 4.1-4.2 (Federation proto + Node registration)
- Day 5: Task 4.2.6 (Agent transfer implementation)
- Day 6-7: Full integration testing + Phase review

---

## 🧪 Testing Strategy

### Unit Tests
- Database repository operations (CRUD)
- Serialization/deserialization logic
- Memory similarity scoring
- Portal condition evaluation

### Integration Tests
- SaveWorld → LoadWorld roundtrip
- Agent transfer across nodes
- Memory query → prompt injection
- Multi-node event propagation

### Load Tests
- 50+ agents with simultaneous SaveWorld
- 1000 memories per agent, query performance
- Node federation with 5+ nodes

### End-to-End Tests
- Scenario: Agent travels between 3 worlds, retains memories, and resumes
- Scenario: World snapshot restored after 1-hour simulation
- Scenario: Long-term memory influences agent decisions

---

## 📝 Deliverables

### Documentation
1. **Database Schema Document** (`docs/database_schema.md`)
   - ER Diagram
   - Table definitions
   - Index strategy
   - Query patterns

2. **Federation Architecture** (`docs/federation_architecture.md`)
   - Node communication protocol
   - Security model (transfer tokens)
   - Portal system design
   - Failure handling

3. **Memory System Guide** (`docs/memory_system.md`)
   - Memory types and lifecycle
   - Embedding configuration
   - Prompt injection patterns
   - Consolidation strategy

### Code Artifacts
1. PostgreSQL migration scripts
2. Updated proto files (`*.proto`)
3. FateEngine extensions (`persistence/`, `federation/`)
4. AgentBrain memory integration (`brain/memory/`)
5. Test suites (unit + integration)

### Configuration
1. Database connection config
2. Federation node registry
3. Vector database settings
4. Embedding API credentials

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PostgreSQL scaling bottleneck | High | Benchmark early; consider read replicas for queries |
| Vector search latency > 100ms | Medium | Use pgvector with ivfflat index; partition memories per actor |
| Agent transfer data loss | High | Implement validation + rollback; test edge cases |
| Network partitions between nodes | Medium | Heartbeat detection; queue events for replay |
| Memory bloat (unlimited growth) | Medium | Auto-prune based on importance; per-actor limits |
| Snapshot corruption | High | Checksum validation; keep multiple recent snapshots |

---

## 🔄 Handoff Criteria

Phase 3 is considered **complete** when:

1. ✅ All acceptance criteria for Tasks 1-4 are met
2. ✅ Load tests pass (50 agents, <200ms tick time)
3. ✅ End-to-end scenario runs successfully:
   - Start simulation
   - Run for 1000 ticks
   - Save world snapshot
   - Resume from snapshot
   - Agent travels to another node
   - Agent uses long-term memory in decision
4. ✅ Documentation is complete and reviewed
5. ✅ Code reviewed and merged to main branch

**Next Phase**: Phase 4 - Advanced Intelligence (Drama Director, Enhanced RAG)

---

## 👥 Team Coordination

### Roles & Responsibilities

| Role | Tasks |
|------|-------|
| **Backend Engineer** | Database schema, FateEngine extensions, gRPC services |
| **AI Engineer** | Memory system, embedding integration, AgentBrain prompts |
| **DevOps Engineer** | PostgreSQL setup, vector DB, node deployment |
| **QA Engineer** | Test suite, load testing, acceptance validation |

### Communication Channels
- Daily standup: Progress/blockers
- Weekly demo: Feature showcase
- Async: GitHub issues, Discord for quick questions

### Review Process
1. **Code Review**: All PRs require 2 approvals
2. **Design Review**: Architecture changes reviewed by all engineers
3. **Acceptance Review**: Product owner verifies ACs before signoff

---

**Document Version**: 1.0
**Last Updated**: 2026-02-15
**Next Review**: Week 6 Day 1 (Kickoff meeting)
