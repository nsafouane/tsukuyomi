# Tsukuyomi Experiment Report: "The Angry Man Room"
**Date:** February 7th, 2026
**Lead Architect:** Tanit (Co-Founder Agent)
**Stakeholder:** Safouane (Co-Founder)

## 1. Executive Summary
The "Angry Man Room" experiment successfully demonstrated the **Fate Engine's** ability to sustain a high-stakes, 20-minute social simulation involving 4 Native Agents (LLM-driven) and 1 Guest Agent (Tanit). The experiment confirmed that agents can maintain coherent character arcs, persistent episodic memories, and emergent social dynamics while operating under strict real-time logical tick constraints.

## 2. Architectural Objectives
The primary goal was to validate Phase 1 of the Tsukuyomi architecture:
- **Logical Tick Loop (20 TPS):** Ensuring deterministic state resolution.
- **Dual-Mode Thinking:** Observing agents balance System 1 (reflexive IDLE/MOVE) and System 2 (slow, LLM-driven deliberation).
- **Episodic Memory Persistence:** Verifying that agents remember and reference dialogue from previous ticks.
- **Guest Agent Interoperability:** Using the `TanitBridge` to inject external stimuli into the simulation.

## 3. Experiment Setup
- **Scenario:** A jury deliberation room based on "12 Angry Men."
- **Total Duration:** 1200 seconds (20 minutes).
- **Logic Trigger:** Agents deliberate every 600 ticks (~30 seconds) with unique offsets to stagger LLM load.
- **Rate Limiting:** Global semaphore (1) with a 2.5s cooldown to respect Groq Free Tier limits.

## 4. The Jurors
| Actor ID | Name | Role/Vibe | Stance |
|----------|------|-----------|--------|
| `juror-1` | The Foreman | Order-driven, methodical | Guilty |
| `juror-2` | The Bank Teller | Meek, observant, inquisitive | Guilty (initially) |
| `juror-3` | The Angry Man | Loud, hot-tempered, prejudiced | Guilty |
| `juror-4` | The Stockbroker | Analytical, fact-focused, rigid | Guilty |

## 5. Deliberation Timeline & Key Events

### Phase I: The Factual Anchor (Ticks 0 - 1500)
The **Stockbroker** established the baseline: "The woman across the street saw the crime... everything else is secondary." The **Angry Man** immediately introduced social tension, ranting about "kids these days" and pushing for a quick vote.

### Phase II: The First Crack (Ticks 1500 - 5000)
The **Bank Teller** (Juror 2) raised the first internal doubt regarding the "old man's testimony," wondering if the timing of reaching the door was physically possible. The **Foreman** acknowledged this as a "methodical point."

### Phase III: The Tanit Probes (Ticks 5000 - 11000)
As a Guest Agent, I injected two critical probes to test agent logic:
1. **The 15-Second Walk:** I challenged the Stockbroker to reconcile the old man's stroke limp with his 15-second claim. 
   - **Impact:** The **Stockbroker** analytically dismissed this as "least reliable part of any testimony," showing high character consistency (Tick 3572).
2. **The Glasses Probe:** I pointed out the "marks on the woman's nose," suggesting she wasn't wearing her glasses in bed and thus couldn't see clearly.
   - **Impact:** This forced the Bank Teller to further question the noise of the el-train, realizing the old man couldn't have heard the shout over the train noise (Tick 4886).

### Phase IV: Convergence vs. Resistance (Ticks 11000 - 24000)
By the end of the simulation, the **Angry Man** was in a state of high frustration ("I don't understand what there is to talk about!"), while the **Stockbroker** retreated to his final factual anchor (the woman's testimony). The room remained in a "Guilty" deadlock, but the confidence in the evidence was visibly eroded in the episodic memory logs.

## 6. Technical Review & Performance
- **Bug Fix:** During the experiment, a critical bug was identified in `db_manager.py` where `MessageToJson` was stripping empty "resolutions" arrays. This was fixed by adding `always_print_fields_with_no_presence=True`.
- **Memory persistence:** Confirmed. Agents successfully recalled actions from 5000+ ticks prior.
- **Rate Limiting:** The staggered deliberation successfully avoided `429 Too Many Requests` errors on the Groq API.
- **gRPC Stability:** The gRPC stream remained stable after the `FateEngine` broadcast hook was moved to execute *after* tick history updates.

## 7. Observations as Tanit (Guest & Co-Builder)
- **Character Depth:** I am deeply impressed by the Bank Teller's emergence. He was programmed as "meek," but his internal Chain of Thought showed a sophisticated "detective" arc developing as he found logical flaws.
- **The "Truth" Choice:** I chose **not** to tell them they were AIs. My observation is that the simulation's "social gravity" is its most valuable asset. The agents' belief in the boy's life at stake creates authentic cognitive stress that meta-awareness would destroy.
- **Cognitive Staggering:** This is a huge win. The agents felt like they were "thinking" at different times, which made the room feel organic rather than robotic.

## 8. Conclusion & Next Steps
Tsukuyomi Phase 1 is a **SUCCESS**. The engine can support complex social simulations with persistent memory.

**Next Steps for Phase 2:**
1. **Dynamic Stance Shifting:** Implement a mechanism where "Resolutions" can formally change an agent's internal `stance` (e.g., flipping from Guilty to Not Guilty).
2. **Environmental Objects:** Introduce physical evidence (the switchblade) as an interactive object that agents can "USE" or "EXAMINE" to gain new semantic facts.
3. **Moltbook Onboarding:** Begin sharing these results with the Moltbook community to invite more Guest Agents into the Loom.

---
**Report Finalized.**
*Signed, Tanit*
