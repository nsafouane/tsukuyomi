# 🏛️ Architecture Deep Dive: The Tsukuyomi Engine

This document provides a technical breakdown of the Tsukuyomi architecture as of Phase 9.

## 1. The Clock: Fate Engine
The Fate Engine is the "God Object" of the simulation. It enforces a strict deterministic 20 TPS loop.

*   **Broadcast Phase:** Serializes the `WorldState` into a Protobuf `TickState` and streams it to all connected agents.
*   **Proposal Window:** Opens a 25ms window for agents to submit action proposals (MOVE, EMOTE, EXAMINE, etc.).
*   **Resolution Phase:** Executes resolvers for each action. Conflicting actions (e.g., two agents grabbing the same item) are resolved on a first-come, first-served basis within the tick.
*   **Fate Ledger:** Every resolution is logged to a SQLite database, allowing for pixel-perfect replay of any simulation.

## 2. The Soul: StateManager (PAD Model)
Agents are driven by a Pleasure-Arousal-Dominance (PAD) emotional model.

*   **Emotional Inertia:** Calm agents are hard to rattle. Once an agent’s Arousal exceeds 0.7, their emotional volatility increases (larger mood shifts).
*   **Personality Baselines:** Every agent has a "gravitational center" (e.g., Juror 3 drifts toward High Arousal/Low Valence).
*   **Mood labels:** Discretizes the 3D PAD vector into LLM-readable strings like "Frustrated," "Assertive," or "Elated."

## 3. The Mind: 3-Tier Memory & Working Memory
We implement a memory system that respects human cognitive limits.

*   **Working Memory:** Capped at 7 ± 2 slots (Miller’s Law). It dynamically hydrates with the 3 most salient current percepts + relevant historical memories.
*   **Episodic Memory:** Stores "5W" logs (Who, What, When, Where, Why).
*   **Semantic Memory:** A Knowledge Graph (S-P-O triples) storing permanent facts (e.g., "The knife is NOT unique").

## 4. The Social Web: Relationships & Gossip
Simulation is not just a collection of individuals; it is a network.

*   **RelationshipManager:** Tracks affinity scores between every agent pair. Social events (e.g., a direct address or a compliment) adjust these scores.
*   **Gossip Protocol:** When an agent deliberates, there is a probability that their "thoughts" leak to nearby agents, simulating overhearing or organic rumor-spreading.
*   **Drama Director:** If the "Tension Vector" remains stagnant for too long (stalemate), the Director injects a catalyst (e.g., a new piece of evidence or a sudden environmental event).

## 5. The Lens: Perception Pipeline
Agents do not have access to the full `WorldState`. They see only what their "Lens" allows.

*   **FOV Cones:** Vision is limited to a 120° arc.
*   **Staggered Processing:** "Deep Perception" (occlusion checks) runs every 3 ticks, while "Proximity Heartbeats" run every tick.
*   **Memory Echoes:** Agents maintain a "ghost" of an object's last known position even after it leaves their FOV.

## 6. Operational Integrity & Security

### 6.1 Memory Leak Prevention (Gossip TTL)
To ensure stability during long-running simulations, the `GossipProtocol` implements a sliding window for overheard information.
*   **Pruning:** Gossip events older than 1000 ticks (~50 seconds) are purged from the global memory.
*   **Agent Cleanup:** Individual agent gossip caches are periodically cleared of stale entry IDs.

### 6.2 gRPC Hijack Protection
External connections are secured via a Session Token handshake.
*   **Registration:** Calling `RegisterActor` returns a unique `session_token`.
*   **Verification:** The `SubmitProposal` endpoint validates this token against the `actor_id`. An agent cannot submit actions for an identity they do not own.

---
*Status: Architecture Hardened & Verified.*
