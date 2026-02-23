"""
Full V2 Agent Experiment - Working Version
==========================================

Run: python3 experiments/angry_men/run_full_v2.py
"""

import asyncio
import json
import logging
import random
from pathlib import Path
from datetime import datetime

# Setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
import sys
sys.path.insert(0, str(project_root))

from tsukuyomi.core.belief.unified import (
    BeliefSystem,
    Belief,
    BeliefType
)
from tsukuyomi.agents.social import (
    PersuasionEngine,
    PersuasionStrategy,
    Argument
)
from tsukuyomi.agents.runtime import (
    ContextManager
)
from tsukuyomi.agents.core import (
    AgentIdentity
)


# Logging
LOG_DIR = current_dir / "logs_v2"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"full_{datetime.now():%Y%m%d_%H%M%S}.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FullV2")


# ============================================================================
# JUROR PROFILES
# ============================================================================

JUROR_PROFILES = {
    "arthur": {"name": "Arthur Miller", "stubbornness": 0.85, "openness": 0.15,
                "initial_vote": "guilty", "initial_conf": 0.78,
                "role": "The Angry One",
                "backstory": "A man driven by personal tragedy. Sees the defendant as representing everything wrong."},
    "sarah": {"name": "Sarah Chen", "stubbornness": 0.25, "openness": 0.75,
              "initial_vote": "guilty", "initial_conf": 0.62,
              "role": "The Quiet Observer",
              "backstory": "An analytical thinker who pays attention to details others miss."},
    "george": {"name": "George Wright", "stubbornness": 0.55, "openness": 0.45,
               "initial_vote": "guilty", "initial_conf": 0.58,
               "role": "The Businessman",
               "backstory": "A practical man who wants to get this over with."},
    "jack": {"name": "Jack Morrison", "stubbornness": 0.40, "openness": 0.60,
             "initial_vote": "guilty", "initial_conf": 0.52,
             "role": "The Cynic",
             "backstory": "A man who's seen the system fail. Skeptical of easy answers."},
    "davis": {"name": "Davis Thompson", "stubbornness": 0.45, "openness": 0.55,
              "initial_vote": "not_guilty", "initial_conf": 0.38,
              "role": "The Dissenter",
              "backstory": "An architect who believes in reasonable doubt. Not afraid to stand alone."}
}


# ============================================================================
# JUROR CLASS
# ============================================================================

class Juror:
    def __init__(self, pid: str, profile: dict):
        self.pid = pid
        self.name = profile["name"]
        self.agent_id = f"juror_{pid}"
        self.profile = profile
        
        # Belief System
        self.beliefs = BeliefSystem(
            agent_id=self.agent_id,
            openness=profile["openness"],
            confirmation_bias=profile["stubbornness"]
        )
        
        # Add verdict belief
        vote = profile["initial_vote"]
        conf = profile["initial_conf"]
        self.verdict_belief_id = self.beliefs.add_belief(
            statement=f"The defendant is {vote}",
            confidence=conf,
            belief_type=BeliefType.OPINION,
            tags=["verdict", "central"]
        )
        
        # Persuasion Engine
        self.persuasion = PersuasionEngine(agent_id=self.agent_id)
        
        # Context Manager
        self.context = ContextManager(agent_id=self.agent_id)
        
        # State
        self.current_vote = vote
        self.vote_history = [(0, vote, conf)]
        
        logger.info(f"👤 {self.name} ({profile['role']}): {vote} @ {conf:.0%}")
    
    async def speak(self, tick: int) -> dict:
        """Generate statement."""
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        conf = belief.confidence if belief else 0.5
        
        # Select strategy based on vote
        if self.current_vote == "guilty":
            statements = [
                "The evidence is clear - guilty beyond reasonable doubt.",
                "Three witnesses saw him leave. That's conclusive.",
                "The defendant's story doesn't add up.",
                "The knife was traced to his father's shop.",
                "Forensic evidence links him directly to the scene."
            ]
        else:
            statements = [
                "The eyewitness testimony is full of inconsistencies.",
                "The old man couldn't have heard anything from 70 feet.",
                "The defendant's alibi was never properly investigated.",
                "There's too much reasonable doubt here.",
                "The prosecution hasn't met their burden of proof."
            ]
        
        content = random.choice(statements)
        
        # Create argument
        arg = self.persuasion.create_argument(
            claim=content,
            strategy=PersuasionStrategy.LOGIC,
            strength_score=conf,
            tick=tick
        )
        
        # Record
        self.context.add_utterance(self.agent_id, content, tick)
        
        logger.info(f"💬 {self.name}: \"{content[:50]}...\"")
        
        return {"speaker": self.name, "speaker_id": self.agent_id, 
                "content": content, "argument": arg, "confidence": conf}
    
    async def listen(self, statement: dict, tick: int):
        """Process another juror's statement."""
        # Record
        self.context.add_utterance(statement["speaker_id"], statement["content"], tick)
        
        # Get belief
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        if not belief:
            return
        
        # Process persuasion
        new_conf, attempt = self.persuasion.calculate_persuasion_effect(
            argument=statement["argument"],
            listener_id=self.agent_id,
            belief_confidence=belief.confidence,
            belief_is_core=False,
            tick=tick
        )
        
        # Apply if significant
        if abs(attempt.change) > 0.01:
            old_conf = belief.confidence
            belief.confidence = new_conf
            
            # Add evidence
            supports = "guilty" in statement["content"].lower()
            self.beliefs.add_evidence(
                self.verdict_belief_id,
                statement["content"][:60],
                supports_belief=supports,
                strength=statement["confidence"],
                source=statement["speaker_id"]
            )
            
            logger.info(f"  📊 {self.name}: {old_conf:.0%} → {new_conf:.0%} ({attempt.change:+.1%})")
    
    async def update_vote(self, tick: int) -> str:
        """Update vote based on belief."""
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        conf = belief.confidence if belief else 0.5
        
        if conf > 0.55:
            new_vote = "guilty"
        elif conf < 0.45:
            new_vote = "not_guilty"
        else:
            new_vote = self.current_vote
        
        if new_vote != self.current_vote:
            old = self.current_vote
            self.current_vote = new_vote
            self.vote_history.append((tick, new_vote, conf))
            logger.info(f"  🎯 {self.name}: VOTE CHANGED! {old} → {new_vote}")
        
        return self.current_vote
    
    def get_summary(self) -> dict:
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        return {
            "name": self.name,
            "role": self.profile["role"],
            "initial": self.profile["initial_vote"],
            "final": self.current_vote,
            "confidence": belief.confidence if belief else 0.5,
            "changes": len(self.vote_history) - 1
        }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    logger.info("=" * 60)
    logger.info("🎬 FULL V2 AGENT EXPERIMENT")
    logger.info("=" * 60)
    
    # Create jurors
    jurors = {pid: Juror(pid, prof) for pid, prof in JUROR_PROFILES.items()}
    
    logger.info("\n📋 INITIAL STATE:")
    for j in jurors.values():
        print(f"  {j.name}: {j.current_vote} @ {j.profile['initial_conf']:.0%}")
    
    # Deliberation loop
    logger.info("\n🗣️  DELIBERATION:")
    
    tick = 0
    pids = list(jurors.keys())
    
    while tick < 500:
        # Speaker speaks
        speaker = jurors[pids[tick % len(pids)]]
        statement = await speaker.speak(tick)
        
        # Others listen
        for juror in jurors.values():
            if juror.agent_id != speaker.agent_id:
                await juror.listen(statement, tick)
        
        # Vote check every 50 ticks
        if tick > 0 and tick % 50 == 0:
            logger.info(f"\n--- Tick {tick} ---")
            votes = {}
            for j in jurors.values():
                v = await j.update_vote(tick)
                votes[j.name] = v
            logger.info(f"Votes: {dict(sorted(votes.items()))}")
            
            # Check consensus
            if len(set(votes.values())) == 1:
                logger.info(f"\n✅ CONSENSUS: {list(votes.values())[0].upper()}")
                break
        
        tick += 1
    
    # Final results
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL RESULTS:")
    logger.info("=" * 60)
    
    results = {}
    for j in jurors.values():
        await j.update_vote(tick)
        s = j.get_summary()
        status = "✅" if s["changes"] > 0 else "⬜"
        logger.info(f"  {s['name']}: {s['final'].upper()} ({s['confidence']:.0%}) {status}")
        results[s['name']] = s
    
    # Save
    output = LOG_DIR / f"full_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\n💾 Saved to {output}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
