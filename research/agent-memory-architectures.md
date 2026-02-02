# Agent Memory Architectures for Persistent AI Simulations

**Research Date:** 2026-01-31  
**Relevance:** Direct application to The Narrative Loom's agent cognition system

---

## Executive Summary

This research explores memory architectures for game AI agents, comparing episodic, semantic, and procedural memory systems. Key findings reveal that modern game AI is moving toward cognitively-inspired architectures that mirror human memory, with notable implementations in games like Dwarf Fortress and academic research like Stanford's Generative Agents.

---

## 1. Memory Types in AI Agents

### 1.1 Semantic Memory
**Definition:** Factual and conceptual knowledge - the "what" of the world.

- Stores facts, relationships, and general knowledge
- In LLM agents: embedded in training data or knowledge bases
- Example: "Fire is hot" or "The blacksmith lives in the market district"

**Implementation approaches:**
- Knowledge graphs (Neo4j, property graphs)
- Vector embeddings with semantic search
- Structured databases with ontologies

### 1.2 Episodic Memory  
**Definition:** Personal experiences and events - the "when/where/who" of interactions.

- Records specific interactions, events, and contexts
- Enables agents to reference past experiences
- Critical for continuity and relationship building

**Key research:** "Who, What, When, Where, Why: A Narrative Episodic Memory Framework for Generative AI NPCs in Games" (ResearchGate, 2024)
- Proposes 5W framework for structuring NPC memories
- Focuses on narrative-relevant memory formation

**Implementation approaches:**
- Time-stamped event logs with retrieval mechanisms
- Memory streams (as in Stanford Generative Agents)
- Importance-weighted storage with decay/consolidation

### 1.3 Procedural Memory
**Definition:** Learned skills and behavioral adaptations - the "how" of actions.

- Encodes habits, skills, and automated responses
- Enables agents to improve over time
- Often implicit in behavior trees or state machines

---

## 2. Real-World Implementations

### 2.1 Dwarf Fortress
**Architecture:** Deterministic state machines with emergent complexity

Key characteristics:
- Each dwarf has 500+ interlocking needs, skills, and memories
- Complexity emerges from rigid system interactions, not AI planning
- Drama arises organically through environmental pressure
- No LLM - pure emergent behavior from rule interactions

**Contrast with LLM approaches:**
- Dwarf Fortress: Bottom-up emergence from simple rules
- Generative Agents: Top-down planning via LLM reasoning
- DF yields drama through cause-and-effect granularity

### 2.2 Stanford Generative Agents (2023)
**Architecture:** LLM-driven memory streams with reflection

Key components:
- **Memory Stream:** Chronological record of experiences
- **Retrieval:** Recency + importance + relevance scoring
- **Reflection:** Periodic synthesis of higher-level insights
- **Planning:** Day planning based on character traits and memories

**Strengths:** Natural language reasoning, flexible behavior
**Weaknesses:** Computational cost, potential for hallucination

### 2.3 Talk of the Town (Game AI Pro 3)
**Focus:** Character knowledge and belief simulation

Key innovations:
- Knowledge exchange during NPC interactions
- Simulation of memory fallibility (forgetting, misremembering)
- Belief propagation through social networks
- Gossip mechanics that spread (and distort) information

**Relevance to Narrative Loom:** Direct inspiration for our gossip/rumor system

### 2.4 Knowledge Graphs for NPCs (Neo4j/Unreal Engine)
**Architecture:** Graph database integrated with game engine

Benefits:
- Real-time querying of complex relationships
- Natural representation of beliefs and knowledge
- Efficient traversal for social network queries
- Integration with Unreal Engine via plugin

---

## 3. Architectural Tradeoffs

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Pure Rule Systems** (Dwarf Fortress) | Emergent complexity, deterministic replay, low compute | Hard to author, limited reasoning | Simulation-heavy games |
| **LLM Memory Streams** (Generative Agents) | Natural language, flexible reasoning | High compute, non-deterministic | Narrative/social games |
| **Knowledge Graphs** | Structured queries, explicit relationships | Schema rigidity, authoring overhead | RPGs with complex lore |
| **Hybrid (Our Approach)** | Best of both worlds | Implementation complexity | Persistent world simulations |

---

## 4. Recommendations for The Narrative Loom

Based on this research, our tiered memory architecture aligns well with current best practices:

### Immediate Implementation Priorities:

1. **Episodic Memory (Buffer → Long-term)**
   - Use the 5W framework for memory encoding
   - Implement importance scoring for consolidation
   - Add decay/forgetting mechanics for realism

2. **Semantic Memory (Knowledge Graph)**
   - Neo4j or similar for relationship storage
   - Embed facts about world, relationships, locations
   - Enable efficient belief queries

3. **Memory Fallibility**
   - Implement from Talk of the Town research
   - Memories can degrade, merge, or distort over time
   - Gossip spreads imperfect information

4. **Deterministic Replay**
   - Capture all LLM outputs as "proposals" (per our architecture)
   - Enable replay without re-calling LLMs
   - Critical for debugging and testing

---

## 5. Key Sources

1. **"Who, What, When, Where, Why: A Narrative Episodic Memory Framework"** - ResearchGate (2024)
   - https://www.researchgate.net/publication/389418767

2. **"Cognitively-Inspired Episodic Memory Architectures"** - arXiv (2024)
   - https://arxiv.org/abs/2511.10652

3. **"Simulating Character Knowledge Phenomena in Talk of the Town"** - Game AI Pro 3
   - http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter37

4. **"Real-Time Knowledge Graphs for NPC Gaming AI"** - Neo4j NODES 2022
   - https://neo4j.com/videos/018-towards-real-time-knowledge-graphs

5. **"Dwarf Fortress: The Nexus of Emergent Complexity"** - Genezi Research
   - https://research.genezi.io/p/dwarf-fortress-the-nexus-of-emergent

6. **"Memory Systems in AI Agents: Episodic vs. Semantic"** - CTOI Substack
   - https://ctoi.substack.com/p/memory-systems-in-ai-agents-episodic

7. **"Semantic vs Episodic vs Procedural Memory in AI Agents"** - Medium
   - https://medium.com/womenintechnology/semantic-vs-episodic-vs-procedural-memory-in-ai-agents

---

## 6. Next Research Topics

- [ ] Deep dive into Stanford Generative Agents implementation details
- [ ] Neo4j + Unreal Engine integration specifics
- [ ] Memory consolidation algorithms (sleep cycles for agents?)
- [ ] Belief revision and contradiction handling
- [ ] Performance benchmarks for different memory backends
