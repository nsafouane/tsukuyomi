"""
Jury Deliberation Scenario
=========================

12 Angry Men-style jury deliberation simulation.

This scenario simulates a jury deliberating on a criminal case.
Agents discuss evidence, argue, and eventually reach a verdict.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from .base import Scenario, ScenarioConfig

logger = logging.getLogger("JuryScenario")


class Vote(Enum):
    """Possible votes."""
    GUILTY = "guilty"
    NOT_GUILTY = "not guilty"


@dataclass
class JuryConfig(ScenarioConfig):
    """Configuration for jury deliberation."""
    # Case details
    case_name: str = "The People v. Defendant"
    case_description: str = ""
    evidence_list: List[str] = field(default_factory=list)
    
    # Deliberation settings
    initial_votes: Dict[str, str] = None  # agent_id -> vote
    discussion_rounds: int = 20
    min_votes_to_change: int = 1  # How many must change for another round
    
    # Vote change detection
    doubt_threshold: float = 0.5  # Doubt above this triggers vote change
    
    def __post_init__(self):
        if self.initial_votes is None:
            self.initial_votes = {}
        if self.name == "unknown":
            self.name = "jury_deliberation"


class JurorAgent:
    """A juror in the simulation."""
    
    def __init__(self, agent: Any, initial_vote: str):
        self.agent = agent
        self.initial_vote = initial_vote
        self.current_vote = initial_vote
        self.doubt_level = 0.0  # 0.0-1.0
        self.vote_history: List[Dict] = []
        
    def to_dict(self) -> Dict:
        return {
            "name": self.agent.identity.name if self.agent.identity else "Unknown",
            "initial_vote": self.initial_vote,
            "current_vote": self.current_vote,
            "doubt_level": self.doubt_level
        }


class JuryDeliberationScenario(Scenario):
    """
    A jury deliberation scenario based on 12 Angry Men.
    
    Features:
    - Multiple jurors with different backgrounds and personalities
    - Evidence discussion and argument
    - Dynamic vote changes based on persuasion
    - Real-time tension and drama tracking
    - Multiple deliberation rounds until verdict reached
    """
    
    def __init__(self, config: JuryConfig = None, llm_provider: Callable = None):
        super().__init__(config or JuryConfig())
        self.config: JuryConfig = self.config  # Type hint
        self.llm_provider = llm_provider
        
        self.jurors: List[JurorAgent] = []
        self.discussion_log: List[Dict] = []
        self.current_speaker_index = 0
        self.deliberation_round = 0
        self.tension_level = 0.0
        self.vote_counts = {"guilty": 0, "not guilty": 0}
        
    async def initialize(self) -> None:
        """Initialize the jury deliberation."""
        logger.info("Initializing jury deliberation...")
        
        # Load juror profiles if provided
        profiles_dir = self.config.agent_profiles_dir
        if profiles_dir:
            await self._load_juror_profiles(profiles_dir)
        else:
            # Use default profiles
            await self._create_default_jurors()
        
        # Record initial votes
        for juror in self.jurors:
            self._record_vote(juror)
        
        # Calculate initial vote counts
        self._update_vote_counts()
        
        # Store case info in memories
        await self._initialize_case_memories()
        
        logger.info(f"Jury initialized with {len(self.jurors)} jurors")
        logger.info(f"Initial votes: {self.vote_counts}")
    
    async def _load_juror_profiles(self, profiles_dir: str) -> None:
        """Load juror profiles from directory."""
        import os
        
        profile_files = sorted([
            f for f in os.listdir(profiles_dir)
            if f.endswith('.json')
        ])
        
        # Set initial votes
        initial_votes = self.config.initial_votes or {}
        
        for i, filename in enumerate(profile_files):
            profile_path = os.path.join(profiles_dir, filename)
            
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            # Create agent
            from ..universal_agent import UniversalAgent, AgentConfig
            
            agent_config = AgentConfig(
                scenario_name="jury deliberation",
                llm_provider=self.config.llm_provider,
                llm_model=self.config.llm_model,
                llm_temperature=self.config.llm_temperature,
                llm_max_tokens=self.config.llm_max_tokens
            )
            
            agent = UniversalAgent(agent_config)
            agent.load_identity(identity_dict=profile_data)
            
            # Set LLM if provider given
            if self.llm_provider:
                agent.set_llm(self.llm_provider)
            
            # Determine vote (use provided or default to guilty)
            agent_id = agent.identity.id
            vote = initial_votes.get(agent_id, "guilty")
            if i == 0 and "not guilty" in initial_votes.values():
                vote = "not guilty"  # First juror is usually the holdout
            
            juror = JurorAgent(agent, vote)
            self.jurors.append(juror)
    
    async def _create_default_jurors(self) -> None:
        """Create default juror profiles."""
        # This would create the 12 Angry Men style profiles
        # For now, create basic agents
        pass
    
    async def _initialize_case_memories(self) -> None:
        """Initialize case information in juror memories."""
        case_info = f"Case: {self.config.case_name}"
        if self.config.case_description:
            case_info += f"\n{self.config.case_description}"
        
        for juror in self.jurors:
            await juror.agent.observe(
                event=case_info,
                importance=0.9
            )
    
    async def step(self) -> bool:
        """Execute one deliberation step."""
        if self.is_complete():
            return False
        
        # Get current speaker
        if not self.jurors:
            return False
        
        speaker = self.jurors[self.current_speaker_index]
        
        # Build discussion context
        context = await self._build_discussion_context(speaker)
        
        # Generate response
        response = await speaker.agent.respond(
            input_text=context,
            store_interaction=True
        )
        
        # Process response for drama and vote changes
        await self._process_speaker_response(speaker, response)
        
        # Log the discussion
        self.discussion_log.append({
            "tick": self.current_tick,
            "round": self.deliberation_round,
            "speaker": speaker.agent.identity.name if speaker.agent.identity else "Unknown",
            "response": response[:200] + "..." if len(response) > 200 else response
        })
        
        # Move to next speaker
        self.current_speaker_index = (self.current_speaker_index + 1) % len(self.jurors)
        
        # Check if we've gone through all jurors
        if self.current_speaker_index == 0:
            self.deliberation_round += 1
            self._update_tension()
            
            # Check if verdict reached
            if self._check_verdict():
                return False
            
            # Check if deliberation should continue
            if self.deliberation_round >= self.config.discussion_rounds:
                return False
        
        return True
    
    async def _build_discussion_context(self, speaker: JurorAgent) -> str:
        """Build context for the speaker."""
        # Get recent discussion
        recent = self.discussion_log[-5:] if self.discussion_log else []
        recent_text = ""
        if recent:
            lines = [f"- {d['speaker']}: {d['response']}" for d in recent]
            recent_text = "Recent discussion:\n" + "\n".join(lines)
        
        # Get current votes
        votes_text = f"\nCurrent votes: {self.vote_counts['guilty']} guilty, {self.vote_counts['not guilty']} not guilty"
        
        # Evidence
        evidence_text = ""
        if self.config.evidence_list:
            evidence_text = "Evidence discussed:\n" + "\n".join(f"- {e}" for e in self.config.evidence_list[:5])
        
        # Build context
        context = f"""You are in a jury deliberation room.

You voted: {speaker.current_vote.upper()}
Your doubt level: {speaker.doubt_level:.0%}

{recent_text}
{votes_text}
{evidence_text}

What do you say to the other jurors? Express your genuine opinions."""
        
        return context
    
    async def _process_speaker_response(self, speaker: JurorAgent, response: str) -> None:
        """Process speaker's response for drama and vote changes."""
        response_lower = response.lower()
        
        # Detect doubt in their own position
        doubt_keywords = ["maybe", "possibly", "i'm not sure", "could be", 
                        "reasonable doubt", "not certain", "i doubt"]
        for keyword in doubt_keywords:
            if keyword in response_lower:
                speaker.doubt_level += 0.1
        
        # Cap doubt at 1.0
        speaker.doubt_level = min(1.0, speaker.doubt_level)
        
        # Detect if they're convincing others
        convincing_keywords = ["evidence shows", "proof", "certain", "definitely",
                            "witness was lying", "couldn't have", "impossible"]
        for keyword in convincing_keywords:
            if keyword in response_lower:
                # Other jurors might gain doubt
                for other in self.jurors:
                    if other != speaker and other.current_vote != speaker.current_vote:
                        other.doubt_level += 0.05
        
        # Check for vote change
        if speaker.doubt_level >= self.config.doubt_threshold:
            old_vote = speaker.current_vote
            speaker.current_vote = "not guilty" if speaker.current_vote == "guilty" else "guilty"
            
            if old_vote != speaker.current_vote:
                self._record_vote(speaker, reason="doubt")
                logger.info(f"{speaker.agent.identity.name} changed vote to {speaker.current_vote}")
    
    def _record_vote(self, juror: JurorAgent, reason: str = "initial") -> None:
        """Record a vote in history."""
        juror.vote_history.append({
            "tick": self.current_tick,
            "vote": juror.current_vote,
            "doubt": juror.doubt_level,
            "reason": reason
        })
    
    def _update_vote_counts(self) -> None:
        """Update vote counts."""
        self.vote_counts = {"guilty": 0, "not guilty": 0}
        for juror in self.jurors:
            self.vote_counts[juror.current_vote] += 1
    
    def _update_tension(self) -> None:
        """Update tension level based on deliberation."""
        if not self.jurors:
            return
        
        # Tension based on vote split
        total = len(self.jurors)
        split = abs(self.vote_counts["guilty"] - self.vote_counts["not guilty"]) / total
        self.tension_level = 1.0 - split
        
        # Increase with deliberation rounds
        self.tension_level = min(1.0, self.tension_level + (self.deliberation_round * 0.05))
    
    def _check_verdict(self) -> bool:
        """Check if a verdict has been reached."""
        # Unanimous verdict required
        if self.vote_counts["guilty"] == len(self.jurors):
            self.results["verdict"] = "guilty"
            self.results["unanimous"] = True
            return True
        
        if self.vote_counts["not guilty"] == len(self.jurors):
            self.results["verdict"] = "not guilty"
            self.results["unanimous"] = True
            return True
        
        return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get current scenario state."""
        return {
            "scenario": self.config.name,
            "case": self.config.case_name,
            "current_tick": self.current_tick,
            "deliberation_round": self.deliberation_round,
            "tension_level": self.tension_level,
            "vote_counts": self.vote_counts,
            "jurors": [j.to_dict() for j in self.jurors],
            "discussion_turns": len(self.discussion_log),
            "is_complete": self.is_complete()
        }
    
    def is_complete(self) -> bool:
        """Check if deliberation is complete."""
        # Check for verdict
        if self._check_verdict():
            return True
        
        # Check max rounds
        if self.deliberation_round >= self.config.discussion_rounds:
            self.results["verdict"] = "hung"
            self.results["unanimous"] = False
            return True
        
        return False
    
    def get_transcript(self) -> str:
        """Get full discussion transcript."""
        lines = [f"# {self.config.case_name} - Deliberation Transcript"]
        lines.append(f"Date: {datetime.now().isoformat()}")
        lines.append(f"Rounds: {self.deliberation_round}")
        lines.append(f"Final Votes: {self.vote_counts['guilty']} G / {self.vote_counts['not guilty']} NG\n")
        
        for entry in self.discussion_log:
            lines.append(f"**{entry['speaker']}**: {entry['response']}")
            lines.append("")
        
        return "\n".join(lines)


async def create_jury_scenario(
    profiles_dir: str,
    case_name: str,
    case_description: str,
    evidence_list: List[str],
    llm_provider: Callable = None,
    initial_not_guilty: str = None  # Agent ID who votes not guilty
) -> JuryDeliberationScenario:
    """
    Factory function to create a jury scenario.
    
    Args:
        profiles_dir: Directory with juror JSON profiles
        case_name: Name of the case
        case_description: Description of the case
        evidence_list: List of evidence items
        llm_provider: LLM function
        initial_not_guilty: Agent ID that starts as not guilty
    
    Returns:
        Configured JuryDeliberationScenario
    """
    config = JuryConfig(
        name="jury_deliberation",
        case_name=case_name,
        case_description=case_description,
        evidence_list=evidence_list,
        agent_profiles_dir=profiles_dir,
        discussion_rounds=20
    )
    
    scenario = JuryDeliberationScenario(config, llm_provider)
    
    # Set initial votes
    if initial_not_guilty:
        config.initial_votes = {initial_not_guilty: "not guilty"}
    
    return scenario


__all__ = [
    "JuryConfig",
    "JurorAgent",
    "Vote",
    "JuryDeliberationScenario",
    "create_jury_scenario"
]