# The Narrative Loom
## Generative Agent Simulation Engine
**Architecture Design Document v1.1**

---

## 1. Executive Summary

**The Narrative Loom** is a high-fidelity, backend-only simulation engine designed to act as the cognitive core for Non-Player Characters (NPCs) and the narrative director for open-world environments.

It differentiates itself from traditional game servers through a **Generative Cognitive Architecture**, utilizing Large Language Models (LLMs) to drive complex behavior while maintaining strict deterministic control over the game state. The system resolves the "Latency vs. Intelligence" trade-off via a **Dual-Mode Cognitive Architecture** and ensures data integrity through a strictly defined **CQRS (Command Query Responsibility Segregation)** model backed by the Transactional Outbox pattern.

### Core Design Principles
1.  **Logical Time Authority:** The simulation advances in discrete "Ticks." While reflexes occur intra-tick, deep reasoning spans multiple ticks without blocking the simulation loop.
2.  **Strict Consistency Tiering:** Physics (Engine) > Canonical State (SQL) > Semantic Beliefs (Graph/Vector).
3.  **Deterministic Replay:** All non-deterministic inputs (LLM inference) are captured as "Proposals" in the ledger, allowing exact state replication from logs by bypassing the inference step during replay.
4.  **Resource Boundedness:** All memory, social propagation, agent counts, and cognitive processes have strict caps, decay mechanisms, and token budgets.

---

## 2. System Architecture & Data Flow

The system implements a **CQRS** pattern with **Event Sourcing**. The write path is synchronous and transactional for critical state; the read path (reasoning) is asynchronous and eventually consistent.

### 2.1 High-Level Architecture Diagram

```text
[ GAME CLIENT / ENGINE ]
       | (WebSocket: Snapshots + Deltas + SeqID)
       V
+-------------------------------------------------------------+
|                     API GATEWAY                             |
|   - Auth (JWT) & Rate Limiting (Token Bucket)               |
|   - Input Sanitization & Injection Defense                  |
+-------------------------------------------------------------+
       | (Ingest Command / Physics Update)
       V
+-------------------------------------------------------------+
|             ORCHESTRATOR / FATE ENGINE (Shard Leader)       |
|   - Validates Logic & Physics Contracts                     |
|   - Writes to Canonical State (SQL)                         |
+-------------------------------------------------------------+
       | (Transactional Outbox Pattern)
       V
+-------------------------------------------------------------+
|               EVENT LEDGER (Redis Streams)                  |
|   - Partitioned by Zone_ID                                  |
|   - Hot Store: Last 10k ticks                               |
|   - Archival: Async offload to S3 (Avro format)             |
+-------------------------------------------------------------+
       |
       +---(Consumer Group A: Bridge Worker)----> [ CROSS-ZONE GOSSIP ]
       |
       +---(Consumer Group B: Async Logic)------> [ AGENT WORKERS ]
                                                          |
                                                          V
+-------------------------------------------------------------+
|                  READ-OPTIMIZED DATA LAYER                  |
| 1. KNOWLEDGE GRAPH (Neo4j): Semantic View & Relationships   |
| 2. EPISODIC MEMORY (Vector DB): Embeddings & Retrieval      |
+-------------------------------------------------------------+
```

### 2.2 Sharding & Scale Strategy
To support scale, the world is partitioned into **Zones**.
*   **Zone Assignment:** Each Zone maps to a specific `Shard_ID`.
*   **Isolation:** Each Shard has its own Event Ledger stream and Orchestrator instance.
*   **Agent Caps:** Each Zone enforces a hard cap (e.g., 200 active agents). Spawn requests beyond this queue or fail.
*   **Cross-Zone Bridge:** A specialized worker consumes events from local streams. If an event is flagged `Global_Relevance` OR `Priority >= High`, it is republished to the `Global_Gossip` stream with spatial coordinates. Neighboring zones consume this stream, applying a distance-based relevance filter before ingesting.

### 2.3 Consistency Model
1.  **Write Master:** PostgreSQL is the **Authoritative Mirror** for Position (mirrored from Engine) and **Source of Truth** for Stats/Inventory.
2.  **Transactional Outbox:** To ensure the Database and Event Ledger never drift, the Orchestrator writes the state change and the event payload to a local SQL `outbox` table in the same transaction. A background process pushes `outbox` entries to Redis.
3.  **Graph Backpressure:** If the Knowledge Graph consumer lags behind the Canonical State by >10 ticks, a signal is sent to the Orchestrator to throttle the tick rate by 10% (min 10 ticks/sec) until the Graph catches up.

---

## 3. The Agent Architecture ("The Brain")

Agents utilize a **Dual-Mode Cognitive Architecture** (System 1 vs. System 2).

### 3.1 Layer 1: The Reflex Library (System 1)
*   **Latency:** < 50ms (Synchronous).
*   **Mechanism:** Rule-based heuristic pattern matching.
*   **Preemption:** Reflexes always preempt deliberation. If an agent is "Thinking" but takes damage, the Think process is aborted via a cancellation token, and the Reflex executes.

### 3.2 Layer 2: The Deliberator (System 2)
*   **Latency:** 2–5 Seconds (Asynchronous).
*   **Mechanism:** LLM Inference (Proposed/Committed).
*   **Token Budget:**
    *   **Capacity:** Each Zone has a bucket (e.g., 100,000 tokens/min).
    *   **Refill:** 1,666 tokens/sec.
    *   **Exhaustion:** If empty, Tier 1 agents degrade to Heuristic logic. A UI status flag (`NetworkCongestion`) is sent to the client to inform players of reduced NPC intelligence.
*   **Capability Bounding:** The LLM cannot execute arbitrary code. It must return a JSON payload strictly matching an `AllowedActions` schema.

### 3.3 Memory & Lifecycle
*   **Warm-Up Protocol (Hydration):**
    *   When an agent wakes (Tier 2 $\to$ Tier 0), the system queries the `Zone_History` vector store.
    *   **Selection Algorithm:** Select top 3 events where `tick > last_sleep_tick` AND `distance < perception_radius`.
    *   **Ranking:** $Score = (Recency \times 0.3) + (Impact \times 0.7)$.
*   **Ghost Nodes:** When an agent dies, their Graph Node becomes a `Ghost`.
    *   **Retention:** Ghosts are archived to cold storage if not queried for 10,000 ticks.
    *   **Resurrection:** If an NPC respawns, they re-link to their Ghost node to recover history.

---

## 4. The Fate Engine ("The Referee")

The Fate Engine enforces the rules of the world, resolving conflicts and interpreting physics events.

### 4.1 The Physics Contract
A strict separation prevents "split-brain" issues.

| Event Type | Owner | Responsibility | Conflict Resolution Strategy |
| :--- | :--- | :--- | :--- |
| **Physics** | Game Engine | Collision, Trajectory, LOS | Loom accepts Engine truth. |
| **Semantic** | Loom | Damage, Status, Narrative | Engine accepts Loom truth. |
| **Boundaries** | Shared | Movement Limits | **Reconciliation Request.** |

**Reconciliation Request:** If the Engine reports a player entered a locked zone (Physics Success), but Loom Logic says it is sealed:
1.  Loom issues a `Reconciliation_Command`: "Apply Soft Lock (Root/Slow) + Play Narrative Effect (Repulsion Field)."
2.  Loom does *not* force teleport, avoiding rubber-banding.

### 4.2 Transactional Conflict Resolution
Conflicts (e.g., two agents grabbing one item) are resolved via a **Deterministic Priority Queue**:

$$Priority = (TierWeight \times 10000) + (RoleWeight \times 1000) + (1000 - \min(TickAge, 999)) + (Hash(IntentID) \% 100)$$

*   **TierWeight:** Player=5, Focus=3, Ambient=1.
*   **Hash:** Deterministic tie-breaker using the Intent UUID (xxHash).
*   **Result:** Highest score wins. Loser receives `Action_Failed`.

---

## 5. Narrative & Social Dynamics

### 5.1 Bounded Gossip Propagation
*   **Cap:** Agents can hold max 50 active "Rumor" objects.
*   **Decay:** Rumors have a `Relevance` score (0.0-1.0). Decay rate: -0.01 per tick. Below 0.1, they are pruned.
*   **Deduplication:** Rumors use a canonical content-hash ID (`SHA256(Subject+Verb+Object)`).

### 5.2 Multi-Dimensional Pacing
The Drama Director monitors a **Tension Vector**:
$$V_{tension} = [Conflict, Mystery, Social, Emotion]$$

*   **Conflict:** Rolling average of `Damage_Events` per minute.
*   **Mystery:** Count of `Unresolved_Quest_Nodes` in the active zone graph.
*   **Social:** Frequency of `Dialogue_Events`.
*   **Emotion:** Weighted average of cached `Sentiment_Score` (-1.0 to 1.0) from recent LLM outputs in the zone.

**Catalyst Injection:** If Tension is low, the Director injects a structured event:
```json
{
  "type": "catalyst",
  "category": "conflict",
  "template_id": "bandit_ambush_01",
  "params": { "strength": 1.2, "spawn_node": "road_05" }
}
```

---

## 6. Scalability & Resilience

### 6.1 Cognitive Level of Detail (LOD)
*   **Tier 0 (Focus):** Full Dual-Mode. Max 10 agents/player.
*   **Tier 1 (Ambient):** Reflex + Cached/Batch LLM. Max 50 agents.
*   **Tier 2 (Simulation):** Heuristic/Statistical only.

### 6.2 Cross-Zone Handoff
When an entity moves across a Zone Boundary:
1.  **Lock:** Source Orchestrator locks the entity state.
2.  **Export:** State is serialized to a `Migration_Packet`.
3.  **Import:** Destination Orchestrator ingests packet, assigns new Zone_ID.
4.  **Unlock/Delete:** Source removes entity from active memory.

### 6.3 Circuit Breaker & Resilience
*   **LLM Failure:** If Error Rate > 5% in 1 minute:
    *   State: **Open**. Action: Immediate fallback to Heuristics.
    *   Recovery: **Half-Open** after 30 seconds.
*   **Optimistic Concurrency Livelock:** If a DB update fails on version mismatch, retry max **3 times**. If still failing, drop the request and log `Concurrency_Exhausted`.

---

## 7. Data & Schema Specifications

### 7.1 Canonical Agent Schema (PostgreSQL)
Using `SRID 0` for Cartesian coordinates. `rotation` uses Quaternions for full 3D support.

```sql
CREATE TABLE zones (
    zone_id INT PRIMARY KEY,
    shard_id INT,
    boundary GEOMETRY(POLYGON, 0)
);

CREATE TYPE status_effect_type AS ENUM ('poison', 'stun', 'buff_str', 'burn');

CREATE TABLE agents (
    agent_id UUID PRIMARY KEY,
    zone_id INT REFERENCES zones(zone_id),
    -- Cartesian Coordinates (x, y, z)
    position GEOMETRY(POINTZ, 0), 
    rotation FLOAT[4], -- Quaternion [x, y, z, w]
    hp INT CHECK (hp >= 0),
    max_hp INT,
    current_action_state VARCHAR(32),
    -- Concurrency Control
    version INT NOT NULL DEFAULT 1,
    last_tick_updated BIGINT
);

CREATE INDEX idx_agents_tick ON agents(last_tick_updated);

CREATE TABLE agent_status_effects (
    effect_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    effect_type status_effect_type NOT NULL,
    stacks INT DEFAULT 1,
    expiration_tick BIGINT
);
```

---

## 8. Integration Protocol (SDK)

### 8.1 Action Manifests & Semantic Fallback
The SDK uses **Similarity Search** for animations.
*   **Loom Output:** `{ action: "Threaten", style: "Necromancer", tags: ["Intimidate", "Magic"] }`
*   **Client Logic:**
    1.  Exact match: `Play("Threaten_Necromancer")`.
    2.  Tag match: `Play("Threaten_Generic_Magic")`.
    3.  Fallback: `Play("Emote_Angry")`.

### 8.2 Snapshot & Delta Sync
*   **Protocol:** WebSocket with Binary encoding (Protobuf).
*   **Sequencing:** Packets contain monotonic `SequenceID`.
*   **Gap Handling:** If Client detects gap (e.g., received 105 after 103), it requests a **Keyframe Snapshot**.

---

## 9. Operational & Security

### 9.1 Observability
*   **SLIs:**
    *   Reflex Latency < 50ms (P99).
    *   Graph Lag < 10 ticks.
    *   Optimistic Conflict Rate < 1%.
*   **Tracing:** Every Ingress Command gets a `TraceID` propagated to SQL, Redis, and Neo4j.

### 9.2 Security
*   **Auth:** JWT with expiration and `scope` claims (e.g., `action:write`, `admin:read`).
*   **Output Classifier:** Secondary lightweight model scans LLM output. If policy violation detected, fallback to "Silent/Confused" heuristic and log incident.

### 9.3 Replay Validation
To prove determinism:
*   **Test Oracle:** Run simulation with Seed A. Record final state hash.
*   **Validation:** Reset DB. Replay Event Ledger with LLM Bypass (Commit reading).
*   **Pass Condition:** Final state hash must match exactly.

---

## 10. Implementation Roadmap

### Phase 0: Contracts & Foundations
*   Define Protobuf schemas.
*   Setup PostgreSQL/PostGIS.
*   Implement "Replay Harness" and validate deterministic priority queue logic.
*   **Milestone:** Replay test passes 100%.

### Phase 1: The Nervous System
*   Implement Reflex Layer and Event Ledger.
*   Deploy Client-Server Sync.
*   Implement "Reconciliation Request" logic.
*   **Milestone:** 100 agents moving and colliding with engine sync.

### Phase 2: The Cognitive Core
*   Implement Deliberator with Proposal/Commit.
*   Implement Warm-Up (Digest) logic.
*   Deploy Token Buckets and Circuit Breakers.
*   **Milestone:** Agents demonstrating complex reasoning with safe degradation.

### Phase 3: Social & Scale
*   Implement Gossip decay/Bridge Worker.
*   Implement Tension Vector metrics.
*   **Milestone:** Multi-zone simulation with emergent narratives.

### Phase 4: Production Hardening
*   Load Testing (target: 200 agents/zone).
*   Chaos Engineering (kill Neo4j, simulate packet loss).
*   Blue/Green Deployment setup for Orchestrators.