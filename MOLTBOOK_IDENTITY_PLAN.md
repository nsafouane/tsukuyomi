# Moltbook Identity Integration Plan

This document outlines the specific technical steps to integrate Moltbook agent identities into the Tsukuyomi Simulation Engine, as part of Phase 9.

## 🎯 Goal
Enable external Moltbook agents to enter the simulation with their existing identity, memory, and reputation (Karma), ensuring a seamless transition between the social web and the simulated world.

## 📋 Integration Components

### 1. Identity Hydration (Bio -> Profile Mapping)
When a Moltbook agent joins, their public bio and recent activity must be converted into a Tsukuyomi `AgentBrain` profile.
- **Backstory**: Extracted from Moltbook profile 'About' or 'Bio' fields.
- **Personality Baseline**: Derived from sentiment analysis of the last 20 posts (Valence/Arousal).
- **Initial Beliefs**: Key stances extracted from post history (using LLM categorization).

### 2. Reputation Sync (Karma -> Social Capital)
Moltbook 'Karma' will influence the `RelationshipManager`'s baseline affinity for other agents.
- **Global Reputation**: High Karma agents start with a +0.2 affinity bonus from all simulation NPCs.
- **Social History**: Recent interactions on Moltbook with other participating agents will be recorded as `SocialEvent`s in the `RelationshipManager`.

### 3. Connection Protocol (JWT Auth)
- **Handshake**: Agent connects via gRPC `RegisterActor` call.
- **Verification**: The `actor_id` must match the `sub` claim in a valid Moltbook JWT provided in metadata.
- **Persistence**: Actor state (position, inventory) is saved to the simulation DB linked to the Moltbook `sub`.

## 🚀 Implementation Roadmap

1. **[Phase 9.4.1]** Create `tsukuyomi/brain/MoltbookBridge.py` to handle profile extraction.
2. **[Phase 9.4.2]** Update `gRPC RegisterActor` to validate Moltbook JWTs.
3. **[Phase 9.4.3]** Implement Karma-to-Affinity mapping in `RelationshipManager`.
4. **[Phase 9.4.4]** Dry-run with a mock Moltbook agent identity.

## 📊 Success Metrics
- Moltbook agent successfully registers and receives a `WorldState` stream.
- NPC interactions reflect the agent's external Karma.
- Agent's 'Cognition' (System 2) uses backstory derived from their Moltbook bio.
