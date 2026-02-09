# PHASE 9 PLAN: Advanced Social Dynamics & Drama Direction

## 🎯 Goal
Implement the high-level narrative and social dynamics systems described in `ARCHITECTURE.md`, enabling the simulation to self-regulate its pacing and deepen agent interactions.

## 📋 Components

### 1. The Drama Director (Tension Vector)
Implement a background service that monitors the "Tension" of a zone across four dimensions:
- **Conflict**: Damage events per minute.
- **Mystery**: Unresolved world states or information gaps.
- **Social**: Frequency and quality of agent-to-agent dialogue/gossip.
- **Emotion**: Aggregate sentiment of agent deliberations.

### 2. Catalyst Injection System
Create a system to inject structured events when tension falls below a threshold:
- Template-driven events (e.g., "The Straggler Arrives", "Sudden Scarcity").
- Parameterized difficulty and location.

### 3. Relationship Graph (Affinity & Reputation)
Expand the simple Gossip Protocol into a persistent Relationship Graph:
- **Affinity**: Numeric value (-1.0 to 1.0) between agent pairs.
- **Reputation**: Aggregate of how an agent is perceived by others based on gossip content.
- **Social Memory**: Agents remember who lied to them or helped them.

### 4. Moltbook Identity Integration
Enable external agents from the Moltbook community to "port" into the simulation:
- Standardized character schema mapping.
- Memory hydration from Moltbook bios/history.

## 🚀 Execution Steps

1.  **[TODO]** Create `tsukuyomi/brain/DramaDirector.py` to compute Tension Vector.
2.  **[TODO]** Implement `tsukuyomi/brain/RelationshipManager.py` for affinity tracking.
3.  **[TODO]** Update `GossipProtocol.py` to affect Affinity scores.
4.  **[TODO]** Create `tsukuyomi/brain/CatalystSystem.py` for event injection.
5.  **[TODO]** Integration test with 12-agent benchmark (Phase 8 baseline).

## 📊 Success Metrics
- Drama Director successfully detects "Boredom" (Low Tension).
- Catalyst events successfully increase Tension metrics.
- Agent actions show correlation with Affinity scores.
