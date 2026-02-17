"""
Enhanced Angry Men Experiment - V2
==================================

Uses the new agent architecture with:
- BeliefSystem for evidence-based belief updates
- PersuasionEngine for persuasion dynamics
- DecisionEngine for reasoning chains
- ContextManager for cross-turn memory
- ProposalHandler for voting

Run: python run_v2_experiment.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import random

# Ensure tsukuyomi is in path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import new architecture
from tsukuyomi.agent import (
    # Identity
    AgentIdentity, CoreValue, DefiningMemory, PersonalityTraits, create_identity,
    # Memory
    LongTermMemory, MemoryType, MemoryImportance, store_event_memory,
    # Beliefs
    BeliefSystem, BeliefType,
    # Persuasion
    PersuasionEngine, PersuasionStrategy,
    # Decision
    DecisionEngine, DecisionType, DecisionPriority,
    # Context
    ContextManager,
    # Proposal
    ProposalHandler, ProposalType
)

# Configure logging
LOG_DIR = current_dir / "logs_v2"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"experiment_v2_{datetime.now():%Y%m%d_%H%M%S}.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AngryMenV2")


class MockLLMClient:
    """Mock LLM for testing."""
    def __init__(self):
        self.call_count = 0
    
    async def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        prompt_lower = prompt.lower()
        
        if "vote" in prompt_lower:
            return random.choice(["I vote GUILTY.", "I vote NOT GUILTY."])
        
        responses = [
            "Looking at the evidence, I have concerns about the timeline.",
            "The witness testimony seems inconsistent.",
            "I'm troubled by the lack of physical evidence.",
            "The prosecution made some strong points.",
            "We need to discuss the alibi more thoroughly.",
            "I'm starting to see reasonable doubt here.",
            "The evidence points clearly to guilt in my view."
        ]
        return random.choice(responses)


class EnhancedJuror:
    """Juror with full V2 architecture."""
    
    def __init__(self, profile_path: str, llm_client=None):
        self.profile = self._load_profile(profile_path)
        self.agent_id = self.profile["id"]
        self.name = self.profile["name"]
        
        # Initialize subsystems
        self.beliefs = BeliefSystem(
            agent_id=self.agent_id,
            openness=1.0 - self.profile.get("personality", {}).get("traits", {}).get("stubbornness", 0.5),
            confirmation_bias=self.profile.get("personality", {}).get("traits", {}).get("stubbornness", 0.5)
        )
        self.persuasion = PersuasionEngine(agent_id=self.agent_id)
        self.decisions = DecisionEngine(agent_id=self.agent_id)
        self.context = ContextManager(agent_id=self.agent_id)
        self.proposals = ProposalHandler(agent_id=self.agent_id)
        
        self.llm_client = llm_client or MockLLMClient()
        
        # State
        belief_data = self.profile.get("beliefs", {})
        self.current_vote = belief_data.get("initial_stance", "guilty")
        self.vote_history = [(0, self.current_vote)]
        self.tick = 0
        
        # Add initial belief
        self.beliefs.add_belief(
            statement=f"The defendant is {self.current_vote}",
            confidence=belief_data.get("confidence", 0.7),
            belief_type=BeliefType.OPINION,
            tags=["verdict"]
        )
        
        logger.info(f"Initialized: {self.name} ({self.agent_id}) - Initial vote: {self.current_vote}")
    
    def _load_profile(self, path: str) -> dict:
        with open(path) as f:
            return json.load(f)
    
    async def observe(self, speaker_id: str, content: str, tick: int):
        """Observe another juror's statement."""
        self.tick = tick
        self.context.add_utterance(speaker_id=speaker_id, content=content, tick=tick)
    
    async def deliberate(self, tick: int) -> str:
        """Generate deliberation statement."""
        self.tick = tick
        
        # Get context
        recent = self.context.get_recent_utterances(n=3)
        context_text = "\n".join([f"{u.speaker_id}: {u.content}" for u in recent])
        
        # Get belief
        belief_id = self.beliefs.find_belief("defendant")
        belief = self.beliefs.get_belief(belief_id) if belief_id else None
        belief_conf = belief.confidence if belief else 0.5
        
        # Build prompt
        prompt = f"""You are {self.name}. Belief confidence: {belief_conf:.0%}.
Recent: {context_text}
Current vote: {self.current_vote}. Brief thought:"""
        
        response = await self.llm_client.generate(prompt)
        
        # Store own utterance
        self.context.add_utterance(speaker_id=self.agent_id, content=response, tick=tick)
        
        return response
    
    async def consider_argument(self, speaker_id: str, argument: str, tick: int):
        """Consider another juror's argument."""
        self.tick = tick
        belief_id = self.beliefs.find_belief("defendant")
        if not belief_id:
            return
        
        belief = self.beliefs.get_belief(belief_id)
        if not belief:
            return
        
        # Create argument
        arg = self.persuasion.create_argument(
            claim=argument[:100],
            strategy=PersuasionStrategy.LOGIC,
            strength_score=0.5,
            tick=tick
        )
        
        # Calculate effect
        new_conf, attempt = self.persuasion.calculate_persuasion_effect(
            argument=arg,
            listener_id=self.agent_id,
            belief_confidence=belief.confidence,
            belief_is_core=belief.is_core_value,
            tick=tick
        )
        
        # Add some randomness for more dynamic behavior
        if random.random() < 0.1:  # 10% chance of random shift
            random_shift = random.uniform(-0.05, 0.05)
            new_conf = max(0.1, min(0.9, new_conf + random_shift))
        
        # Update if significant change
        if abs(attempt.change) > 0.02:
            self.beliefs.add_evidence(
                belief_id=belief_id,
                content=argument[:50],
                supports_belief="guilty" in argument.lower(),
                strength=0.5,
                source=speaker_id
            )
            self.beliefs.update_belief(belief_id, tick=tick)
            logger.info(f"{self.name}: Belief {'↑' if attempt.change > 0 else '↓'} {abs(attempt.change):.2f} from {speaker_id}")
    
    async def vote(self, tick: int) -> str:
        """Cast vote based on beliefs."""
        self.tick = tick
        belief_id = self.beliefs.find_belief("defendant")
        
        if belief_id:
            belief = self.beliefs.get_belief(belief_id)
            if belief:
                if belief.confidence > 0.6:
                    new_vote = "guilty"
                elif belief.confidence < 0.4:
                    new_vote = "not guilty"
                else:
                    new_vote = self.current_vote
                
                if new_vote != self.current_vote:
                    old = self.current_vote
                    self.current_vote = new_vote
                    self.vote_history.append((tick, new_vote))
                    logger.info(f"🎯 {self.name}: VOTE CHANGED! {old} -> {new_vote}")
        
        return self.current_vote
    
    def get_summary(self) -> dict:
        return {
            "name": self.name,
            "vote": self.current_vote,
            "vote_changes": len(self.vote_history) - 1,
            "belief_count": len(self.beliefs.beliefs),
            "persuasion_attempts": len(self.persuasion.attempts)
        }


class ExperimentRunner:
    """Main experiment runner."""
    
    def __init__(self, jurors_dir: str, case_file: str, duration_ticks: int = 500):
        self.jurors_dir = Path(jurors_dir)
        self.case_file = Path(case_file)
        self.duration_ticks = duration_ticks
        self.jurors: List[EnhancedJuror] = []
        self.vote_history: List[Dict] = []
        self.utterances: List[Dict] = []
        self.current_tick = 0
    
    def load(self):
        """Load case and jurors."""
        profiles = list(self.jurors_dir.glob("*.json"))
        for path in profiles[:5]:
            self.jurors.append(EnhancedJuror(str(path)))
        logger.info(f"Loaded {len(self.jurors)} jurors")
    
    async def run(self):
        """Run experiment."""
        self.load()
        logger.info(f"Starting {self.duration_ticks} tick experiment")
        
        for tick in range(self.duration_ticks):
            self.current_tick = tick
            
            # Active juror speaks
            juror = self.jurors[tick % len(self.jurors)]
            statement = await juror.deliberate(tick)
            
            self.utterances.append({
                "tick": tick, "speaker": juror.name, "content": statement
            })
            
            # Others observe and consider
            for other in self.jurors:
                if other.agent_id != juror.agent_id:
                    await other.observe(juror.agent_id, statement, tick)
                    await other.consider_argument(juror.agent_id, statement, tick)
            
            # Periodic votes
            if tick % 100 == 0 and tick > 0:
                votes = {}
                for j in self.jurors:
                    v = await j.vote(tick)
                    votes[j.name] = v
                
                self.vote_history.append({"tick": tick, "votes": votes})
                logger.info(f"Tick {tick}: {votes}")
                
                # Check consensus
                vote_counts = {}
                for v in votes.values():
                    vote_counts[v] = vote_counts.get(v, 0) + 1
                
                for vote, count in vote_counts.items():
                    if count >= len(self.jurors):  # Unanimous consensus
                        logger.info(f"✅ Consensus: {vote} ({count}/{len(self.jurors)})")
                        return
        
        # Final vote
        final_votes = {}
        for j in self.jurors:
            final_votes[j.name] = await j.vote(self.duration_ticks)
        
        logger.info(f"\n=== FINAL RESULTS ===")
        logger.info(f"Votes: {final_votes}")
        
        for j in self.jurors:
            s = j.get_summary()
            logger.info(f"  {s['name']}: {s['vote']} (changed {s['vote_changes']}x)")
        
        # Save results
        self._save_results(final_votes)
    
    def _save_results(self, final_votes: Dict):
        """Save experiment results."""
        results = {
            "duration_ticks": self.duration_ticks,
            "final_votes": final_votes,
            "vote_history": self.vote_history,
            "utterance_count": len(self.utterances),
            "juror_summaries": [j.get_summary() for j in self.jurors]
        }
        
        output_path = LOG_DIR / f"results_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path}")


async def main():
    """Run the experiment."""
    runner = ExperimentRunner(
        jurors_dir=str(Path(__file__).parent / "profiles"),
        case_file=str(Path(__file__).parent / "scenarios" / "case_definition.json"),
        duration_ticks=500  # 500 ticks for more deliberation
    )
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
