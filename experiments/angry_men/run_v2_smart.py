"""
Enhanced Angry Men Experiment - V2 with Smart Simulation
========================================================

Demonstrates the new agent architecture with realistic deliberation dynamics.

Run: python run_v2_smart.py
"""

import asyncio
import json
import logging
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
import sys
sys.path.insert(0, str(project_root))

from tsukuyomi.agent import (
    BeliefSystem, BeliefType, PersuasionEngine, PersuasionStrategy,
    DecisionEngine, DecisionType, ContextManager, ProposalHandler
)

# Logging
LOG_DIR = current_dir / "logs_v2"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"smart_{datetime.now():%Y%m%d_%H%M%S}.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmartV2")


class SmartJuror:
    """Juror with intelligent deliberation behavior."""
    
    def __init__(self, name: str, initial_vote: str, stubbornness: float, profile: dict):
        self.name = name
        self.agent_id = f"juror_{name.lower().replace(' ', '_')}"
        self.profile = profile
        
        # Initialize subsystems
        self.beliefs = BeliefSystem(
            agent_id=self.agent_id,
            openness=1.0 - stubbornness,
            confirmation_bias=stubbornness
        )
        
        self.persuasion = PersuasionEngine(agent_id=self.agent_id)
        self.decisions = DecisionEngine(agent_id=self.agent_id)
        self.context = ContextManager(agent_id=self.agent_id)
        
        # Initial belief
        self.current_vote = initial_vote
        initial_conf = random.uniform(0.55, 0.85) if initial_vote == "guilty" else random.uniform(0.15, 0.45)
        
        self.beliefs.add_belief(
            statement=f"The defendant is {initial_vote}",
            confidence=initial_conf,
            belief_type=BeliefType.OPINION,
            tags=["verdict"]
        )
        
        self.vote_history = [(0, initial_vote, initial_conf)]
        self.tick = 0
        
        logger.info(f"👤 {self.name}: Initial vote {initial_vote} (conf: {initial_conf:.0%}, stubborn: {stubbornness:.0%})")
    
    async def speak(self, tick: int) -> dict:
        """Generate a statement."""
        self.tick = tick
        
        # Get belief
        belief_id = self.beliefs.find_belief("defendant")
        belief = self.beliefs.get_belief(belief_id) if belief_id else None
        conf = belief.confidence if belief else 0.5
        
        # Generate statement based on confidence
        if conf > 0.7:
            statements = [
                f"The evidence clearly shows guilt. I'm firmly convinced.",
                f"There's no reasonable doubt here. The facts speak for themselves.",
                f"I've carefully reviewed everything. Guilty is the only logical verdict."
            ]
            strategy = PersuasionStrategy.LOGIC
        elif conf < 0.3:
            statements = [
                f"I have serious doubts about the prosecution's case.",
                f"The evidence just doesn't add up. I can't vote guilty.",
                f"There are too many inconsistencies. Reasonable doubt exists."
            ]
            strategy = PersuasionStrategy.LOGIC
        else:
            statements = [
                f"I'm torn on this case. Can someone explain the timeline?",
                f"I see valid points on both sides. Help me understand.",
                f"The witness testimony troubles me. What do others think?"
            ]
            strategy = PersuasionStrategy.SOCIAL_PROOF
        
        content = random.choice(statements)
        
        # Create argument
        arg = self.persuasion.create_argument(
            claim=content,
            strategy=strategy,
            strength_score=conf,
            tick=tick
        )
        
        # Store in context
        self.context.add_utterance(
            speaker_id=self.agent_id,
            content=content,
            tick=tick
        )
        
        return {"speaker": self.name, "content": content, "arg_id": arg.id, "confidence": conf}
    
    async def listen(self, speaker_name: str, statement: dict, tick: int):
        """Process another juror's statement."""
        self.tick = tick
        
        # Store observation
        self.context.add_utterance(
            speaker_id=speaker_name,
            content=statement["content"],
            tick=tick
        )
        
        # Find our verdict belief
        belief_id = self.beliefs.find_belief("defendant")
        if not belief_id:
            return
        
        belief = self.beliefs.get_belief(belief_id)
        if not belief:
            return
        
        # Determine if statement supports or contradicts our belief
        supports_guilty = "guilt" in statement["content"].lower() or "evidence" in statement["content"].lower()
        supports_not_guilty = "doubt" in statement["content"].lower() or "doesn't add up" in statement["content"].lower()
        
        # Only process if relevant
        if not (supports_guilty or supports_not_guilty):
            return
        
        # Create argument from their statement
        arg = self.persuasion.create_argument(
            claim=statement["content"][:80],
            strategy=PersuasionStrategy.LOGIC,
            strength_score=statement.get("confidence", 0.5),
            tick=tick
        )
        
        # Set relationship (same for all in this simple version)
        self.persuasion.update_relationship(speaker_name, 0.1)
        
        # Calculate persuasion effect
        new_conf, attempt = self.persuasion.calculate_persuasion_effect(
            argument=arg,
            listener_id=self.agent_id,
            belief_confidence=belief.confidence,
            belief_is_core=False,
            tick=tick
        )
        
        # Apply change if significant
        if abs(attempt.change) > 0.005:
            # Directly modify belief confidence (simulating evidence processing)
            belief.confidence = new_conf
            belief.update_count += 1
            belief.record_confidence(tick)
            
            # Record in history
            self.beliefs.update_history.append(attempt)
            
            logger.info(f"  📊 {self.name}: Belief {'↑' if attempt.change > 0 else '↓'} {abs(attempt.change):.1%} from {speaker_name} (now {new_conf:.0%})")
    
    async def update_vote(self, tick: int) -> str:
        """Update vote based on belief confidence."""
        self.tick = tick
        
        belief_id = self.beliefs.find_belief("defendant")
        if not belief_id:
            return self.current_vote
        
        belief = self.beliefs.get_belief(belief_id)
        if not belief:
            return self.current_vote
        
        # Determine vote from confidence
        if belief.confidence > 0.55:
            new_vote = "guilty"
        elif belief.confidence < 0.45:
            new_vote = "not_guilty"
        else:
            new_vote = self.current_vote  # Undecided
        
        # Check for change
        if new_vote != self.current_vote:
            old = self.current_vote
            self.current_vote = new_vote
            self.vote_history.append((tick, new_vote, belief.confidence))
            logger.info(f"  🎯 {self.name}: VOTE CHANGED! {old} → {new_vote} (conf: {belief.confidence:.0%})")
        
        return self.current_vote
    
    def get_summary(self) -> dict:
        belief_id = self.beliefs.find_belief("defendant")
        belief = self.beliefs.get_belief(belief_id) if belief_id else None
        
        return {
            "name": self.name,
            "final_vote": self.current_vote,
            "confidence": belief.confidence if belief else 0.5,
            "vote_changes": len(self.vote_history) - 1,
            "belief_updates": len(self.beliefs.update_history),
            "persuasion_attempts": len(self.persuasion.attempts)
        }


async def run_experiment():
    """Run the enhanced experiment."""
    
    # Create jurors with varied personalities
    jurors = [
        SmartJuror("Arthur", "guilty", stubbornness=0.8, profile={}),      # Very stubborn
        SmartJuror("Sarah", "guilty", stubbornness=0.3, profile={}),       # Open-minded
        SmartJuror("George", "guilty", stubbornness=0.6, profile={}),      # Moderately stubborn
        SmartJuror("Jack", "guilty", stubbornness=0.4, profile={}),        # Somewhat open
        SmartJuror("Davis", "not_guilty", stubbornness=0.5, profile={}),   # Dissenter, moderate
    ]
    
    logger.info("=" * 60)
    logger.info("🚀 ENHANCED ANGRY MEN EXPERIMENT - V2")
    logger.info("=" * 60)
    logger.info(f"Jurors: {', '.join(j.name for j in jurors)}")
    
    duration = 400
    vote_interval = 80
    
    for tick in range(duration):
        # Active juror speaks
        speaker = jurors[tick % len(jurors)]
        statement = await speaker.speak(tick)
        
        # Others listen and process
        for juror in jurors:
            if juror.agent_id != speaker.agent_id:
                await juror.listen(speaker.name, statement, tick)
        
        # Periodic vote check
        if tick > 0 and tick % vote_interval == 0:
            logger.info(f"\n--- Tick {tick} Vote Check ---")
            
            votes = {}
            for juror in jurors:
                vote = await juror.update_vote(tick)
                votes[juror.name] = vote
            
            # Count votes
            counts = {}
            for v in votes.values():
                counts[v] = counts.get(v, 0) + 1
            
            logger.info(f"Votes: {votes}")
            logger.info(f"Counts: {counts}")
            
            # Check for unanimous consensus
            for vote, count in counts.items():
                if count == len(jurors):
                    logger.info(f"\n✅ UNANIMOUS CONSENSUS: {vote.upper()}")
                    return votes
    
    # Final results
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL RESULTS")
    logger.info("=" * 60)
    
    final_votes = {}
    for juror in jurors:
        await juror.update_vote(duration)
        final_votes[juror.name] = juror.current_vote
        summary = juror.get_summary()
        
        changes_str = f"changed {summary['vote_changes']}x" if summary['vote_changes'] > 0 else "no changes"
        logger.info(f"  {summary['name']}: {summary['final_vote'].upper()} "
                   f"(conf: {summary['confidence']:.0%}, {changes_str})")
    
    # Summary stats
    total_changes = sum(j.get_summary()['vote_changes'] for j in jurors)
    total_belief_updates = sum(len(j.beliefs.update_history) for j in jurors)
    
    logger.info(f"\n📈 Experiment Statistics:")
    logger.info(f"  Total vote changes: {total_changes}")
    logger.info(f"  Total belief updates: {total_belief_updates}")
    logger.info(f"  Duration: {duration} ticks")
    
    # Save results
    results = {
        "experiment": "Enhanced Angry Men V2",
        "timestamp": datetime.now().isoformat(),
        "duration_ticks": duration,
        "final_votes": final_votes,
        "vote_counts": {v: list(final_votes.values()).count(v) for v in set(final_votes.values())},
        "total_vote_changes": total_changes,
        "total_belief_updates": total_belief_updates,
        "juror_summaries": [j.get_summary() for j in jurors]
    }
    
    output = LOG_DIR / f"smart_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to {output}")
    
    return final_votes


if __name__ == "__main__":
    asyncio.run(run_experiment())
