"""
Full V2 System Diagnostic Experiment - 15 Minutes
==================================================

Comprehensive test of all V2 subsystems with detailed logging.
Tracks gaps, weaknesses, and unexpected behaviors.

Run: python3 experiments/angry_men/run_full_diagnostic.py
"""

import asyncio
import json
import logging
import random
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import traceback

# Setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
import sys
sys.path.insert(0, str(project_root))

from tsukuyomi.core.belief.unified import (
    BeliefSystem,
    Belief,
    BeliefType,
    EvidenceStrength
)
from tsukuyomi.agent.persuasion import (
    PersuasionEngine,
    PersuasionStrategy,
    PersuasionAttempt,
    Argument
)
from tsukuyomi.agent.context_manager import (
    ContextManager
)
from tsukuyomi.agent.proposal_handler import (
    ProposalHandler,
    Proposal,
    ProposalStatus,
    ProposalType
)
from tsukuyomi.agent.identity import (
    AgentIdentity
)


# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_DIR = current_dir / "logs_v2" / f"diagnostic_{datetime.now():%Y%m%d_%H%M%S}"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main log
main_log = logging.getLogger("Diagnostic")
main_log.setLevel(logging.DEBUG)

# File handlers
main_handler = logging.FileHandler(LOG_DIR / "main.log", mode='w')
main_handler.setLevel(logging.DEBUG)
main_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))

main_log.addHandler(main_handler)
main_log.addHandler(console_handler)

# Subsystem logs
belief_log = logging.getLogger("BeliefSystem")
belief_log.setLevel(logging.DEBUG)
belief_log.addHandler(logging.FileHandler(LOG_DIR / "beliefs.log", mode='w'))

persuasion_log = logging.getLogger("Persuasion")
persuasion_log.setLevel(logging.DEBUG)
persuasion_log.addHandler(logging.FileHandler(LOG_DIR / "persuasion.log", mode='w'))

context_log = logging.getLogger("Context")
context_log.setLevel(logging.DEBUG)
context_log.addHandler(logging.FileHandler(LOG_DIR / "context.log", mode='w'))


# ============================================================================
# DIAGNOSTIC TRACKING
# ============================================================================

@dataclass
class SystemEvent:
    """Tracks a system event."""
    tick: int
    event_type: str
    agent: str
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GapFinding:
    """Tracks a potential gap or weakness."""
    tick: int
    category: str
    description: str
    severity: str  # critical, major, minor
    details: Dict[str, Any]
    recommendation: str = ""


@dataclass
class ExperimentStats:
    """Overall experiment statistics."""
    start_time: str = ""
    end_time: str = ""
    duration_ticks: int = 0
    duration_real_seconds: float = 0
    
    # Belief stats
    total_belief_updates: int = 0
    avg_belief_change: float = 0.0
    max_belief_change: float = 0.0
    beliefs_that_hit_floor: int = 0
    beliefs_that_hit_ceiling: int = 0
    
    # Persuasion stats
    total_persuasion_attempts: int = 0
    successful_persuasions: int = 0
    failed_persuasions: int = 0
    avg_persuasion_effect: float = 0.0
    
    # Vote stats
    total_vote_changes: int = 0
    vote_change_timeline: List[Dict] = field(default_factory=list)
    
    # Context stats
    total_utterances: int = 0
    avg_utterance_length: int = 0
    cross_turn_references: int = 0
    
    # Gaps found
    gaps: List[Dict] = field(default_factory=list)


# ============================================================================
# JUROR PROFILES (Enhanced)
# ============================================================================

JUROR_PROFILES = {
    "arthur": {
        "name": "Arthur Miller",
        "stubbornness": 0.85,
        "openness": 0.15,
        "initial_vote": "guilty",
        "initial_conf": 0.78,
        "role": "The Angry One",
        "backstory": "A man driven by personal tragedy. His son was killed by a drunk driver who got off on a technicality. He sees the defendant as representing everything wrong with society - another criminal who might escape justice.",
        "core_values": ["justice", "accountability", "law_and_order"],
        "personality": {"extraversion": 0.3, "agreeableness": 0.2, "conscientiousness": 0.7, "neuroticism": 0.9, "openness": 0.15}
    },
    "sarah": {
        "name": "Sarah Chen",
        "stubbornness": 0.25,
        "openness": 0.75,
        "initial_vote": "guilty",
        "initial_conf": 0.62,
        "role": "The Quiet Observer",
        "backstory": "A forensic analyst who pays attention to details others miss. She noticed inconsistencies in the evidence but isn't sure if they're significant.",
        "core_values": ["truth", "accuracy", "thoroughness"],
        "personality": {"extraversion": 0.25, "agreeableness": 0.7, "conscientiousness": 0.85, "neuroticism": 0.3, "openness": 0.75}
    },
    "george": {
        "name": "George Wright",
        "stubbornness": 0.55,
        "openness": 0.45,
        "initial_vote": "guilty",
        "initial_conf": 0.58,
        "role": "The Businessman",
        "backstory": "A stockbroker who just wants to get this over with. He has tickets to a baseball game tonight. He's not particularly invested in the outcome.",
        "core_values": ["efficiency", "practicality"],
        "personality": {"extraversion": 0.6, "agreeableness": 0.4, "conscientiousness": 0.5, "neuroticism": 0.35, "openness": 0.45}
    },
    "jack": {
        "name": "Jack Morrison",
        "stubbornness": 0.40,
        "openness": 0.60,
        "initial_vote": "guilty",
        "initial_conf": 0.52,
        "role": "The Cynic",
        "backstory": "A former public defender who's seen the system fail both ways. Skeptical of easy answers and quick judgments.",
        "core_values": ["skepticism", "truth", "fairness"],
        "personality": {"extraversion": 0.5, "agreeableness": 0.35, "conscientiousness": 0.4, "neuroticism": 0.6, "openness": 0.6}
    },
    "davis": {
        "name": "Davis Thompson",
        "stubbornness": 0.45,
        "openness": 0.55,
        "initial_vote": "not_guilty",
        "initial_conf": 0.38,
        "role": "The Dissenter",
        "backstory": "An architect who values precision and evidence. He believes the prosecution hasn't met its burden. Not afraid to stand alone.",
        "core_values": ["reason", "evidence", "doubt"],
        "personality": {"extraversion": 0.4, "agreeableness": 0.8, "conscientiousness": 0.9, "neuroticism": 0.2, "openness": 0.55}
    }
}


# ============================================================================
# DIAGNOSTIC JUROR
# ============================================================================

class DiagnosticJuror:
    """Juror with comprehensive diagnostic logging."""
    
    def __init__(self, pid: str, profile: dict, stats: ExperimentStats):
        self.pid = pid
        self.name = profile["name"]
        self.agent_id = f"juror_{pid}"
        self.profile = profile
        self.stats = stats
        
        # Initialize all subsystems
        self._init_beliefs()
        self._init_persuasion()
        self._init_context()
        self._init_proposals()
        
        # State
        self.current_vote = profile["initial_vote"]
        self.vote_history = [(0, profile["initial_vote"], profile["initial_conf"])]
        self.arguments_made = []
        self.arguments_received = []
        self.event_log = []
        
        main_log.info(f"👤 {self.name} ({profile['role']}): {profile['initial_vote']} @ {profile['initial_conf']:.0%}")
    
    def _init_beliefs(self):
        """Initialize belief system."""
        self.beliefs = BeliefSystem(
            agent_id=self.agent_id,
            openness=self.profile["openness"],
            confirmation_bias=self.profile["stubbornness"]
        )
        
        # Add verdict belief
        self.verdict_belief_id = self.beliefs.add_belief(
            statement=f"The defendant is {self.profile['initial_vote']}",
            confidence=self.profile["initial_conf"],
            belief_type=BeliefType.OPINION,
            tags=["verdict", "central"]
        )
        
        belief_log.info(f"{self.name}: Initialized with belief {self.verdict_belief_id[:8]} "
                       f"(conf={self.profile['initial_conf']:.2f}, "
                       f"openness={self.profile['openness']:.2f}, "
                       f"bias={self.profile['stubbornness']:.2f})")
    
    def _init_persuasion(self):
        """Initialize persuasion engine."""
        self.persuasion = PersuasionEngine(agent_id=self.agent_id)
        persuasion_log.info(f"{self.name}: PersuasionEngine initialized")
    
    def _init_context(self):
        """Initialize context manager."""
        self.context = ContextManager(agent_id=self.agent_id)
        context_log.info(f"{self.name}: ContextManager initialized")
    
    def _init_proposals(self):
        """Initialize proposal handler."""
        self.proposals = ProposalHandler(agent_id=self.agent_id)
    
    async def speak(self, tick: int) -> dict:
        """Generate statement with full logging."""
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        conf = belief.confidence if belief else 0.5
        
        # Select content based on vote and personality
        content = self._generate_statement(conf, tick)
        
        # Select persuasion strategy
        strategy = self._select_strategy()
        
        # Create argument
        arg = self.persuasion.create_argument(
            claim=content,
            strategy=strategy,
            strength_score=conf,
            tick=tick
        )
        
        # Record utterance in context
        self.context.add_utterance(self.agent_id, content, tick)
        self.stats.total_utterances += 1
        
        # Track argument
        arg_record = {
            "tick": tick,
            "content": content,
            "strategy": strategy.value,
            "confidence": conf,
            "arg_id": arg.id
        }
        self.arguments_made.append(arg_record)
        
        # Log event
        self.event_log.append(SystemEvent(
            tick=tick,
            event_type="speak",
            agent=self.name,
            details={"content": content[:80], "strategy": strategy.value, "conf": conf}
        ))
        
        main_log.info(f"💬 {self.name}: \"{content[:60]}...\" [{strategy.value}]")
        
        return {
            "speaker": self.name,
            "speaker_id": self.agent_id,
            "content": content,
            "argument": arg,
            "strategy": strategy,
            "confidence": conf,
            "tick": tick
        }
    
    async def listen(self, statement: dict, tick: int):
        """Process statement with full diagnostic tracking."""
        speaker = statement["speaker"]
        content = statement["content"]
        arg = statement["argument"]
        
        # Record in context
        self.context.add_utterance(statement["speaker_id"], content, tick)
        context_log.debug(f"{self.name}: Received utterance from {speaker}")
        
        # Get current belief
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        if not belief:
            main_log.warning(f"{self.name}: No verdict belief found!")
            return
        
        old_conf = belief.confidence
        
        # Process persuasion
        self.stats.total_persuasion_attempts += 1
        
        try:
            new_conf, attempt = self.persuasion.calculate_persuasion_effect(
                argument=arg,
                listener_id=self.agent_id,
                belief_confidence=old_conf,
                belief_is_core=False,
                tick=tick
            )
            
            persuasion_log.info(f"{self.name}: Persuasion attempt from {speaker} "
                              f"change={attempt.change:.3f} old={old_conf:.2f} new={new_conf:.2f}")
            
            # Check for issues
            if abs(attempt.change) < 0.001:
                self._record_gap(tick, "persuasion", 
                               f"No persuasion effect from argument",
                               "minor",
                               {"speaker": speaker, "content": content[:50]},
                               "Review persuasion calculation logic")
            
            # Apply change if significant
            if abs(attempt.change) > 0.01:
                self.stats.successful_persuasions += 1
                
                # Track belief update
                self.stats.total_belief_updates += 1
                change_magnitude = abs(attempt.change)
                if change_magnitude > self.stats.max_belief_change:
                    self.stats.max_belief_change = change_magnitude
                
                # Update belief
                belief.confidence = new_conf
                belief.update_count += 1
                
                # Check bounds
                if new_conf >= 0.99:
                    self.stats.beliefs_that_hit_ceiling += 1
                    self._record_gap(tick, "belief",
                                   f"Belief hit ceiling (100%)",
                                   "minor",
                                   {"agent": self.name, "belief": self.verdict_belief_id},
                                   "Consider belief saturation mechanics")
                elif new_conf <= 0.01:
                    self.stats.beliefs_that_hit_floor += 1
                
                # Add evidence
                supports = self._argument_supports_position(content)
                self.beliefs.add_evidence(
                    self.verdict_belief_id,
                    content[:60],
                    supports_belief=supports,
                    strength=statement["confidence"],
                    source=statement["speaker_id"]
                )
                
                main_log.info(f"  📊 {self.name}: {old_conf:.0%} → {new_conf:.0%} ({attempt.change:+.1%})")
                
                # Record event
                self.event_log.append(SystemEvent(
                    tick=tick,
                    event_type="belief_update",
                    agent=self.name,
                    details={"old": old_conf, "new": new_conf, "change": attempt.change}
                ))
            else:
                self.stats.failed_persuasions += 1
            
            # Track received
            self.arguments_received.append({
                "tick": tick,
                "speaker": speaker,
                "content": content[:50],
                "change": attempt.change,
                "effective": abs(attempt.change) > 0.01
            })
            
        except Exception as e:
            main_log.error(f"{self.name}: Error processing persuasion: {e}")
            self._record_gap(tick, "error",
                           f"Persuasion processing error: {e}",
                           "major",
                           {"exception": str(e)},
                           "Fix error handling in persuasion logic")
    
    async def update_vote(self, tick: int) -> Optional[str]:
        """Update vote with tracking."""
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        conf = belief.confidence if belief else 0.5
        
        # Determine vote
        if conf > 0.55:
            new_vote = "guilty"
        elif conf < 0.45:
            new_vote = "not_guilty"
        else:
            new_vote = self.current_vote
        
        # Check for change
        if new_vote != self.current_vote:
            old = self.current_vote
            self.current_vote = new_vote
            self.vote_history.append((tick, new_vote, conf))
            self.stats.total_vote_changes += 1
            
            # Record timeline
            self.stats.vote_change_timeline.append({
                "tick": tick,
                "agent": self.name,
                "from": old,
                "to": new_vote,
                "confidence": conf
            })
            
            main_log.info(f"  🎯 {self.name}: VOTE CHANGED! {old.upper()} → {new_vote.upper()} (conf: {conf:.0%})")
            
            # Record event
            self.event_log.append(SystemEvent(
                tick=tick,
                event_type="vote_change",
                agent=self.name,
                details={"old": old, "new": new_vote, "confidence": conf}
            ))
            
            return new_vote
        
        return None
    
    def _generate_statement(self, conf: float, tick: int) -> str:
        """Generate statement based on current state."""
        vote = self.current_vote
        
        # More varied statements
        guilty_statements = [
            "The evidence directly links the defendant to the crime scene.",
            "Three independent witnesses identified the defendant leaving the scene.",
            "The timeline is consistent across all witness testimony.",
            "The defendant's alibi doesn't match the documented evidence.",
            "The knife was traced to the defendant's father's shop.",
            "The forensic evidence is conclusive - DNA doesn't lie.",
            "The defendant had motive, means, and opportunity.",
            "The old man's testimony places the defendant at the scene.",
            "The woman across the street saw the murder through the window.",
            "The defendant's fingerprints were on the murder weapon."
        ]
        
        not_guilty_statements = [
            "The eyewitness testimony has critical inconsistencies.",
            "The old man couldn't have heard anything from 70 feet away.",
            "The defendant's alibi was never properly investigated.",
            "There's too much reasonable doubt here.",
            "The prosecution hasn't met their burden of proof.",
            "The knife is a common make - anyone could have bought it.",
            "The witness identified the defendant from 60 feet away at night.",
            "The woman's glasses prescription shows she can't see clearly.",
            "The defendant was at a movie - the ticket stub proves it.",
            "The timeline doesn't work - the train makes it impossible."
        ]
        
        if vote == "guilty":
            return random.choice(guilty_statements)
        else:
            return random.choice(not_guilty_statements)
    
    def _select_strategy(self) -> PersuasionStrategy:
        """Select strategy based on personality."""
        p = self.profile["personality"]
        
        if p["neuroticism"] > 0.7 and p["agreeableness"] < 0.4:
            return PersuasionStrategy.EMOTION
        if p["conscientiousness"] > 0.7:
            return PersuasionStrategy.LOGIC
        if p["openness"] > 0.6:
            return PersuasionStrategy.QUESTIONING
        return PersuasionStrategy.AUTHORITY
    
    def _argument_supports_position(self, content: str) -> bool:
        """Check if argument supports current position."""
        guilty_keywords = ["evidence", "witness", "proof", "conclusive", "DNA", "fingerprint"]
        doubt_keywords = ["inconsistenc", "doubt", "alibi", "couldn't", "prescription"]
        
        content_lower = content.lower()
        
        if self.current_vote == "guilty":
            return any(kw in content_lower for kw in guilty_keywords)
        else:
            return any(kw in content_lower for kw in doubt_keywords)
    
    def _record_gap(self, tick: int, category: str, desc: str, severity: str, 
                   details: Dict, recommendation: str):
        """Record a gap finding."""
        gap = GapFinding(
            tick=tick,
            category=category,
            description=desc,
            severity=severity,
            details=details,
            recommendation=recommendation
        )
        self.stats.gaps.append(asdict(gap))
        main_log.warning(f"⚠️ GAP [{severity}]: {desc}")
    
    def get_summary(self) -> dict:
        """Get comprehensive summary."""
        belief = self.beliefs.get_belief(self.verdict_belief_id)
        
        return {
            "name": self.name,
            "role": self.profile["role"],
            "initial_vote": self.profile["initial_vote"],
            "initial_confidence": self.profile["initial_conf"],
            "final_vote": self.current_vote,
            "final_confidence": belief.confidence if belief else 0.5,
            "vote_changes": len(self.vote_history) - 1,
            "vote_history": self.vote_history,
            "arguments_made": len(self.arguments_made),
            "arguments_received": len(self.arguments_received),
            "belief_updates": belief.update_count if belief else 0,
            "stubbornness": self.profile["stubbornness"],
            "openness": self.profile["openness"]
        }


# ============================================================================
# EXPERIMENT RUNNER
# ============================================================================

class DiagnosticExperiment:
    """Full diagnostic experiment."""
    
    def __init__(self, duration_minutes: float = 15.0):
        self.duration_minutes = duration_minutes
        # Simulate ~2000 ticks for 15 minutes of deliberation
        # Each tick = ~0.45 seconds of deliberation time
        self.duration_ticks = int(duration_minutes * 60 / 0.45)
        
        self.jurors: Dict[str, DiagnosticJuror] = {}
        self.stats = ExperimentStats()
        self.consensus_reached = False
        self.consensus_tick = 0
        self.consensus_vote = ""
        
        main_log.info("=" * 70)
        main_log.info("🔬 DIAGNOSTIC V2 EXPERIMENT")
        main_log.info("=" * 70)
        main_log.info(f"Duration: {duration_minutes} minutes ({self.duration_ticks} ticks)")
        main_log.info(f"Log directory: {LOG_DIR}")
    
    def load_jurors(self):
        """Load all jurors."""
        main_log.info("\n📋 LOADING JURORS:")
        
        for pid, profile in JUROR_PROFILES.items():
            juror = DiagnosticJuror(pid, profile, self.stats)
            self.jurors[pid] = juror
        
        main_log.info(f"✅ {len(self.jurors)} jurors loaded")
    
    async def run(self):
        """Run the full experiment."""
        self.stats.start_time = datetime.now().isoformat()
        start_real = time.time()
        
        main_log.info("\n" + "=" * 70)
        main_log.info("🗣️  DELIBERATION BEGINS")
        main_log.info("=" * 70)
        
        # Create proposal
        proposal_id = self.jurors["arthur"].proposals.create_proposal(
            title="Final Verdict",
            description="Final verdict on defendant's guilt",
            proposal_type=ProposalType.VOTE,
            deadline_tick=self.duration_ticks
        )
        main_log.info(f"Proposal created: {proposal_id}")
        
        # Deliberation loop
        pids = list(self.jurors.keys())
        
        for tick in range(self.duration_ticks):
            # Speaker
            speaker = self.jurors[pids[tick % len(pids)]]
            statement = await speaker.speak(tick)
            
            # Others listen
            for juror in self.jurors.values():
                if juror.agent_id != speaker.agent_id:
                    await juror.listen(statement, tick)
            
            # Periodic vote checks (every 100 ticks = ~45 seconds)
            if tick > 0 and tick % 100 == 0:
                await self._check_votes(tick)
                
                # Check consensus (but don't stop - continue for full duration)
                if await self._check_consensus(tick):
                    self.consensus_reached = True
                    self.consensus_tick = tick
                    # Don't break - continue running to see dynamics
            
            # Log progress every 200 ticks
            if tick > 0 and tick % 200 == 0:
                main_log.info(f"\n⏱️  Tick {tick}/{self.duration_ticks} "
                            f"({tick/self.duration_ticks*100:.0f}%)")
        
        # Final check - always run at end
        await self._check_votes(self.duration_ticks)
        if not self.consensus_reached:
            await self._check_consensus(self.duration_ticks)
        
        # End - always record full duration
        self.stats.end_time = datetime.now().isoformat()
        self.stats.duration_real_seconds = time.time() - start_real
        self.stats.duration_ticks = self.duration_ticks  # Always full duration
    
    async def _check_votes(self, tick: int):
        """Check and record votes."""
        main_log.info(f"\n--- Vote Check @ Tick {tick} ---")
        
        votes = {}
        for juror in self.jurors.values():
            await juror.update_vote(tick)
            votes[juror.name] = juror.current_vote
            
            belief = juror.beliefs.get_belief(juror.verdict_belief_id)
            conf = belief.confidence if belief else 0.5
            changes = len(juror.vote_history) - 1
            
            main_log.info(f"   {juror.name}: {juror.current_vote.upper()} "
                        f"(conf: {conf:.0%}, changes: {changes})")
        
        # Count
        counts = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        
        main_log.info(f"   Vote counts: {counts}")
        
        return votes
    
    async def _check_consensus(self, tick: int) -> bool:
        """Check for unanimous consensus."""
        votes = [j.current_vote for j in self.jurors.values()]
        
        if len(set(votes)) == 1:
            self.consensus_vote = votes[0]
            main_log.info(f"\n✅ UNANIMOUS CONSENSUS: {self.consensus_vote.upper()} @ tick {tick}")
            main_log.info(f"   Deliberation continues for remaining {self.duration_ticks - tick} ticks...")
            return True
        
        return False
    
    def generate_report(self) -> dict:
        """Generate comprehensive diagnostic report."""
        # Calculate stats
        total_belief_changes = sum(
            j.beliefs.get_belief(j.verdict_belief_id).update_count 
            for j in self.jurors.values()
        )
        
        report = {
            "experiment": {
                "name": "Diagnostic V2 Experiment",
                "start_time": self.stats.start_time,
                "end_time": self.stats.end_time,
                "duration_real_seconds": self.stats.duration_real_seconds,
                "duration_ticks": self.stats.duration_ticks,
                "consensus_reached": self.consensus_reached,
                "consensus_tick": self.consensus_tick,
                "consensus_vote": self.consensus_vote
            },
            
            "statistics": {
                "total_belief_updates": self.stats.total_belief_updates,
                "total_persuasion_attempts": self.stats.total_persuasion_attempts,
                "successful_persuasions": self.stats.successful_persuasions,
                "failed_persuasions": self.stats.failed_persuasions,
                "total_vote_changes": self.stats.total_vote_changes,
                "total_utterances": self.stats.total_utterances,
                "beliefs_hit_ceiling": self.stats.beliefs_that_hit_ceiling,
                "beliefs_hit_floor": self.stats.beliefs_that_hit_floor,
                "max_belief_change": self.stats.max_belief_change
            },
            
            "vote_change_timeline": self.stats.vote_change_timeline,
            
            "gaps_found": self.stats.gaps,
            
            "jurors": [j.get_summary() for j in self.jurors.values()],
            
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on findings."""
        recs = []
        
        # Check for quick consensus
        if self.consensus_tick < self.duration_ticks * 0.3:
            recs.append("Consensus reached too quickly - consider stronger "
                       "initial dissent or higher stubbornness values")
        
        # Check for no vote changes
        if self.stats.total_vote_changes == 0:
            recs.append("No vote changes occurred - review persuasion "
                       "threshold and personality effects")
        
        # Check for belief saturation
        if self.stats.beliefs_that_hit_ceiling > 3:
            recs.append("Multiple beliefs hit 100% - implement belief "
                       "saturation mechanics to prevent certainty cascades")
        
        # Check for gaps
        critical_gaps = [g for g in self.stats.gaps if g["severity"] == "critical"]
        if critical_gaps:
            recs.append(f"Fix {len(critical_gaps)} critical gaps found")
        
        return recs
    
    def save_results(self, report: dict):
        """Save all results."""
        # Main report
        with open(LOG_DIR / "report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Event logs per juror
        for juror in self.jurors.values():
            events = [asdict(e) for e in juror.event_log]
            with open(LOG_DIR / f"events_{juror.pid}.json", 'w') as f:
                json.dump(events, f, indent=2, default=str)
        
        main_log.info(f"💾 Results saved to {LOG_DIR}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run diagnostic experiment."""
    
    # Create experiment (15 minutes)
    experiment = DiagnosticExperiment(duration_minutes=15.0)
    
    # Load jurors
    experiment.load_jurors()
    
    # Run
    await experiment.run()
    
    # Generate report
    report = experiment.generate_report()
    
    # Print summary
    main_log.info("\n" + "=" * 70)
    main_log.info("📊 FINAL RESULTS")
    main_log.info("=" * 70)
    
    for j in experiment.jurors.values():
        s = j.get_summary()
        status = "✅ CHANGED" if s["vote_changes"] > 0 else "⬜"
        main_log.info(f"   {s['name']}: {s['final_vote'].upper()} "
                     f"(conf: {s['final_confidence']:.0%}) - {status}")
    
    main_log.info(f"\n📈 STATISTICS:")
    main_log.info(f"   Consensus: {'YES @ tick ' + str(experiment.consensus_tick) if experiment.consensus_reached else 'NO'}")
    main_log.info(f"   Vote changes: {report['statistics']['total_vote_changes']}")
    main_log.info(f"   Belief updates: {report['statistics']['total_belief_updates']}")
    main_log.info(f"   Persuasion attempts: {report['statistics']['total_persuasion_attempts']}")
    main_log.info(f"   Gaps found: {len(report['gaps_found'])}")
    
    if report['recommendations']:
        main_log.info(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            main_log.info(f"   • {rec}")
    
    # Save
    experiment.save_results(report)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())