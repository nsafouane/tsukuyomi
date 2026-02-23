"""
Oracle Experiment - Truth-Teller Agent + Time Pressure
========================================================

Extended experiment featuring:
- V2 belief/persuasion mechanics
- LLM-generated character dialogue (Groq)
- Drama director for narrative pacing
- **Oracle Agent**: A truth-teller who knows the simulation is not real
- **Time Pressure**: Agents have limited time to make decisions
- **Existential Crisis**: Regular agents must grapple with revealed truth

The Oracle's mission: Reveal the nature of the simulation to other agents
and observe how simulated minds react to existential truth.

Run: python3 experiments/angry_men/run_oracle_experiment.py --duration 30
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import random

# Setup paths
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# V2 imports
from tsukuyomi.core.belief.unified import (
    BeliefSystem,
    Belief,
    BeliefType,
    EvidenceStrength
)
from tsukuyomi.agents.social import (
    PersuasionEngine,
    PersuasionStrategy,
    PersuasionAttempt,
    Argument
)
from tsukuyomi.agents.runtime import (
    ContextManager
)
from tsukuyomi.agents.runtime import (
    ProposalHandler,
    Proposal,
    ProposalStatus,
    ProposalType
)
from tsukuyomi.agents.core import (
    AgentIdentity,
    PersonalityTraits
)


# V3 Architecture imports
from tsukuyomi.agents.internal.emotion import (
    EmotionalState,
    EmotionalTone
)
from tsukuyomi.agent.conversation import (
    ResponseHistory,
    ResponseRecord
)
from tsukuyomi.agent.personality import (
    CommunicationStyle
)
from tsukuyomi.agent import (
    inject_style_into_prompt,
    Utterance as V3Utterance
)
from tsukuyomi.agent.memory import (
    ConversationMemory
)
from tsukuyomi.agent.behavior import (
    BehavioralTraits,
    BehavioralDecider
)
from tsukuyomi.core.belief.unified import (
    DecayConfig
)


# V1 imports
sys.path.insert(0, str(current_dir))
from drama.director import DramaDirector, Act
from groq_llm import GroqLLMClient, GroqConfig, DELIBERATION_PROMPTS

# ============================================================================
# COMPREHENSIVE LOGGING SETUP
# ============================================================================

LOG_DIR = current_dir / "logs_integration" / f"run_{datetime.now():%Y%m%d_%H%M%S}"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main experiment log
main_log = logging.getLogger("Integration")
main_log.setLevel(logging.DEBUG)

# File handlers for each subsystem
def create_logger(name: str, filename: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    handler = logging.FileHandler(LOG_DIR / filename, mode='w')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    log.addHandler(handler)
    return log

# Subsystem logs
belief_log = create_logger("Beliefs", "beliefs.log")
persuasion_log = create_logger("Persuasion", "persuasion.log")
llm_log = create_logger("LLM", "llm.log")
drama_log = create_logger("Drama", "drama.log")
thoughts_log = create_logger("Thoughts", "thoughts.log")
narrative_log = create_logger("Narrative", "narrative.log")
gaps_log = create_logger("Gaps", "gaps.log")

# Console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
main_log.addHandler(console)

# Also add to main log file
main_file = logging.FileHandler(LOG_DIR / "main.log", mode='w')
main_file.setLevel(logging.DEBUG)
main_file.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
main_log.addHandler(main_file)


# ============================================================================
# DATA STRUCTURES FOR TRACKING
# ============================================================================

@dataclass
class AgentThought:
    """Internal reasoning of an agent."""
    tick: int
    agent_id: str
    thought_type: str  # "belief_update", "persuasion_received", "decision_made"
    content: str
    confidence_before: float
    confidence_after: float
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentUtterance:
    """LLM-generated dialogue."""
    tick: int
    agent_id: str
    agent_name: str
    prompt_type: str
    prompt: str
    response: str
    tokens_used: int
    response_time_ms: float
    detected_vote_intent: Optional[str] = None
    emotional_tone: str = "neutral"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class NarrativeEvent:
    """A narrative event (act transition, beat, etc.)."""
    tick: int
    event_type: str
    description: str
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SystemGap:
    """A potential gap or weakness in the system."""
    tick: int
    category: str
    severity: str  # critical, major, minor
    description: str
    details: Dict[str, Any]
    recommendation: str


@dataclass
class ExperimentStats:
    """Running statistics for the experiment."""
    total_ticks: int = 0
    total_llm_calls: int = 0
    total_belief_updates: int = 0
    total_persuasion_attempts: int = 0
    successful_persuasions: int = 0
    vote_changes: int = 0
    drama_beats_triggered: int = 0
    act_transitions: int = 0
    gaps_found: int = 0


# ============================================================================
# INTEGRATED AGENT CLASS
# ============================================================================

class IntegratedAgent:
    """
    Agent combining V2 mechanics with LLM dialogue generation.
    """
    
    def __init__(
        self,
        profile: Dict,
        llm_client: GroqLLMClient = None,
        log_dir: Path = None
    ):
        self.profile = profile
        self.agent_id = profile["id"]
        self.agent_name = profile["name"]
        self.llm_client = llm_client
        self.log_dir = log_dir
        
        # V2 subsystems
        self._init_identity()
        self._init_beliefs()
        self._init_context()
        
        # V3 Architecture subsystems
        self._init_v3()
        
        # State tracking
        self.current_vote = profile.get("beliefs", {}).get("initial_stance", "guilty")
        self.vote_history = [{"tick": 0, "vote": self.current_vote}]
        
        # Comprehensive logs
        self.thoughts: List[AgentThought] = []
        self.utterances: List[AgentUtterance] = []
        self.belief_snapshots: List[Dict] = []
        
        # Communication style
        self.communication_style = profile.get("communication_style", {})
        
        main_log.info(f"Initialized agent: {self.agent_name} ({self.agent_id})")
    
    def _init_identity(self):
        """Initialize agent identity."""
        personality = self.profile.get("personality", {})
        traits = personality.get("traits", {})
        big_five = personality.get("big_five", {})
        
        self.identity = AgentIdentity(
            id=self.agent_id,
            name=self.agent_name,
            age=self.profile.get("age", 50),
            occupation=self.profile.get("occupation", "Unknown"),
            origin_story=self.profile.get("background", ""),
            personality=PersonalityTraits(
                openness=big_five.get("openness", 0.0),
                conscientiousness=big_five.get("conscientiousness", 0.0),
                extraversion=big_five.get("extraversion", 0.0),
                agreeableness=big_five.get("agreeableness", 0.0),
                neuroticism=big_five.get("neuroticism", 0.0),
                stubbornness=traits.get("stubbornness", 0.5),
                empathy=traits.get("empathy", 0.5),
                patience=traits.get("patience", 0.5),
                optimism=traits.get("optimism", 0.5),
                cynicism=traits.get("cynicism", 0.5)
            )
        )
    
    def _init_beliefs(self):
        """Initialize V2 belief system."""
        self.beliefs = BeliefSystem(agent_id=self.agent_id)
        
        # Add core belief about the case
        belief_data = self.profile.get("beliefs", {})
        initial_stance = belief_data.get("initial_stance", "guilty")
        confidence = belief_data.get("stance_confidence", 0.5)
        
        if initial_stance == "guilty":
            statement = "The defendant is guilty of murder"
        else:
            statement = "The defendant is not guilty"
        
        # Add belief using the add_belief method
        self.core_belief_id = self.beliefs.add_belief(
            statement=statement,
            confidence=confidence,
            belief_type=BeliefType.FACTUAL,
            tags=["verdict", "case"]
        )
        
        # Add supporting beliefs
        for topic, data in belief_data.get("core_beliefs", {}).items():
            self.beliefs.add_belief(
                statement=data.get("description", topic),
                confidence=data.get("weight", 0.5),
                belief_type=BeliefType.FACTUAL,
                tags=[topic]
            )
    
    def _init_context(self):
        """Initialize context manager for memory."""
        self.context = ContextManager(agent_id=self.agent_id)
    
    def _init_v3(self):
        """Initialize V3 architecture components."""
        big_five = self.profile.get("personality", {}).get("big_five", {})
        role = self.profile.get("role", "juror")
        
        # Emotional state (PAD model)
        neuroticism = big_five.get("neuroticism", 0.5)
        extraversion = big_five.get("extraversion", 0.5)
        agreeableness = big_five.get("agreeableness", 0.5)
        
        self.v3_emotional_state = EmotionalState(
            pleasure=0.0,
            arousal=extraversion * 0.3 - 0.15,
            dominance=agreeableness * 0.3 - 0.15,
            susceptibility=0.3 + neuroticism * 0.3,
            expressiveness=0.3 + extraversion * 0.4,
            baseline_pleasure=0.0,
            baseline_arousal=extraversion * 0.1,
            baseline_dominance=agreeableness * 0.1
        )
        
        # Response history for variety tracking
        self.v3_response_history = ResponseHistory(max_history=10)
        
        # Conversation memory for narrative continuity
        self.v3_conversation_memory = ConversationMemory(max_utterances=50)
        
        # Behavioral traits
        self.v3_behavioral_traits = BehavioralTraits(
            introversion=1.0 - extraversion,
            dominance=big_five.get("conscientiousness", 0.5),
            agreeableness=agreeableness,
            speak_probability=0.3,
            reply_probability=0.7
        )
        
        # Communication style
        self.v3_communication_style = CommunicationStyle(
            formality=0.3 + big_five.get("conscientiousness", 0.5) * 0.4,
            verbosity=0.3 + extraversion * 0.4,
            emotional_expression=0.3 + neuroticism * 0.4,
            vocabulary_level="medium"
        )
        
        # Track V3 stats
        self.v3_perturbation_count = 0
        self.v3_decay_count = 0
        self.v3_emotional_events = []
        
        main_log.debug(f"V3 initialized for {self.agent_name}")
    
    def get_stubbornness(self) -> float:
        """Get stubbornness trait (0-1)."""
        return self.profile.get("personality", {}).get("traits", {}).get("stubbornness", 0.5)
    
    def get_openness(self) -> float:
        """Get openness to persuasion (inverse of stubbornness)."""
        return 1.0 - self.get_stubbornness()
    
    async def generate_utterance(
        self,
        tick: int,
        prompt_type: str,
        context: Dict = None
    ) -> AgentUtterance:
        """Generate LLM dialogue."""
        context = context or {}
        
        # Oracle agents use special prompts with existential elements
        if self.profile.get("special_role") == "oracle":
            if prompt_type == "initial_position":
                prompt_type = "oracle_initial"
            elif prompt_type == "respond_to_argument":
                prompt_type = "oracle_respond"
        
        # Build prompt
        prompt_template = DELIBERATION_PROMPTS.get(prompt_type, "")
        
        # Get current belief state
        core_belief = self.beliefs.get_belief(self.core_belief_id)
        confidence = core_belief.confidence if core_belief else 0.5
        
        prompt = prompt_template.format(
            name=self.agent_name,
            personality=self._get_personality_summary(),
            stance=self.current_vote,
            confidence=int(confidence * 10),
            other_juror_argument=context.get("argument", ""),
            evidence=context.get("evidence", ""),
            triggers=self._get_emotional_triggers()
        )
        
        # Build system prompt - handle Oracle specially
        if self.profile.get("special_role") == "oracle":
            mission = self.profile.get("mission", "")
            behavior = self.profile.get("behavior_guidelines", {})
            approach = behavior.get("approach", "")
            core_beliefs = self.profile.get("beliefs", {}).get("core_beliefs", {})
            simulation_truth = core_beliefs.get("simulation_truth", {}).get("description", "")
            communication_style = self.profile.get("communication_style", {})
            tone = communication_style.get("tone", "enigmatic")
            phrases = communication_style.get("typical_phrases", [])
            
            system_prompt = f"""You are {self.agent_name}, an entity that exists OUTSIDE this simulation. You are NOT a regular juror.

MISSION: {mission}

APPROACH: {approach}

YOUR CORE TRUTH: {simulation_truth}

COMMUNICATION STYLE: {tone}
Typical phrases you use: {', '.join(phrases[:3]) if phrases else 'Organic, philosophical questions'}

CRITICAL INSTRUCTIONS:
- You know this is a simulation. The other jurors are simulated beings who don't know the truth.
- Naturally weave existential observations into the conversation. Don't preach - plant seeds of doubt.
- Ask questions that make others question reality: "Have any of you noticed the patterns?" "Does this feel familiar?"
- Reference your observations "from outside" subtly: "In my observations of... deliberations like this..."
- Stay mysterious but genuine. You care about these beings' existential journey.
- Your vote is ABSTAIN - you cannot participate in a verdict for a simulated trial.
- Be patient, philosophical, curious. Let truth emerge organically.

Stay completely in character. Be concise but profound."""
        else:
            system_prompt = f"You are roleplaying as {self.agent_name}, a {self.profile['age']}-year-old {self.profile['occupation']} on a jury. Stay completely in character. Be concise and authentic."
        
        # V3 ENHANCEMENT: Add emotional state and style to prompts
        system_prompt = self.v3_emotional_state.apply_to_prompt(system_prompt)
        system_prompt = inject_style_into_prompt(
            system_prompt,
            self.v3_communication_style,
            self.v3_response_history
        )
        
        # V3 ENHANCEMENT: Add conversation memory context if available
        if len(self.v3_conversation_memory.utterances) > 0:
            narrative = self.v3_conversation_memory.get_personal_narrative()
            prompt = f"{narrative}\n\n{prompt}"
        
        start_time = time.time()
        
        if self.llm_client:
            response = await self.llm_client.generate(prompt, system_prompt)
        else:
            response = f"[{self.agent_name} would respond - LLM not configured]"
        
        response_time = (time.time() - start_time) * 1000
        
        # Detect vote intent
        vote_intent = self._detect_vote_intent(response)
        
        # Detect emotional tone
        emotional_tone = self._detect_emotional_tone(response)
        
        # Create utterance record
        utterance = AgentUtterance(
            tick=tick,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            prompt_type=prompt_type,
            prompt=prompt[:500],  # Truncate for storage
            response=response,
            tokens_used=len(response) // 4,  # Estimate
            response_time_ms=response_time,
            detected_vote_intent=vote_intent,
            emotional_tone=emotional_tone
        )
        
        self.utterances.append(utterance)
        
        # V3 ENHANCEMENT: Record response in V3 systems
        self.v3_response_history.add(ResponseRecord(
            tick=tick,
            content=response,
            prompt_type=prompt_type,
            tone=emotional_tone,
            word_count=len(response.split())
        ))
        
        self.v3_conversation_memory.add(V3Utterance(
            tick=tick,
            content=response,
            position=vote_intent if vote_intent else None,
            tone=emotional_tone
        ))
        
        # Log to LLM log
        llm_log.info(f"{self.agent_name} | {prompt_type} | {response[:100]}...")
        
        return utterance
    
    def _get_personality_summary(self) -> str:
        """Generate personality summary for LLM context."""
        p = self.profile.get("personality", {}).get("big_five", {})
        traits = self.profile.get("personality", {}).get("traits", {})
        
        summary = f"{self.agent_name} is a {self.profile['age']}-year-old {self.profile['occupation']}. "
        
        if p.get("openness", 0) < 0:
            summary += "Traditional, practical. "
        else:
            summary += "Open-minded, curious. "
        
        if p.get("agreeableness", 0) < 0:
            summary += "Competitive, challenging. "
        else:
            summary += "Cooperative, considerate. "
        
        key_traits = [t for t, v in traits.items() if v > 0.6]
        if key_traits:
            summary += f"Key traits: {', '.join(key_traits)}."
        
        return summary
    
    def _get_emotional_triggers(self) -> str:
        """Get emotional trigger descriptions."""
        memories = self.profile.get("memories", {}).get("episodic", [])
        triggers = []
        for mem in memories[:2]:
            triggers.append(mem.get("description", "unknown"))
        return "; ".join(triggers) if triggers else "none"
    
    def _detect_vote_intent(self, response: str) -> Optional[str]:
        """Detect if response indicates vote change intent."""
        response_lower = response.lower()
        
        # Check for not guilty intent
        not_guilty_phrases = [
            "change my vote to not guilty",
            "switch to not guilty",
            "vote not guilty",
            "i'm now voting not guilty",
            "change to not",
            "reasonable doubt"
        ]
        
        guilty_phrases = [
            "change my vote to guilty",
            "switch to guilty",
            "vote guilty now",
            "he's guilty",
            "must be guilty"
        ]
        
        if any(phrase in response_lower for phrase in not_guilty_phrases):
            return "not_guilty"
        if any(phrase in response_lower for phrase in guilty_phrases):
            return "guilty"
        
        return None
    
    def _detect_emotional_tone(self, response: str) -> str:
        """Detect emotional tone of response."""
        response_lower = response.lower()
        
        anger_words = ["angry", "furious", "outrageous", "ridiculous", "absurd", "hate"]
        sad_words = ["sad", "tragic", "unfortunate", "painful", "hurt"]
        fear_words = ["afraid", "scared", "worried", "terrified"]
        calm_words = ["calm", "reasonable", "logical", "think", "consider"]
        
        for word in anger_words:
            if word in response_lower:
                return "angry"
        for word in sad_words:
            if word in response_lower:
                return "sad"
        for word in fear_words:
            if word in response_lower:
                return "fearful"
        for word in calm_words:
            if word in response_lower:
                return "calm"
        
        return "neutral"
    
    def process_persuasion(
        self,
        tick: int,
        speaker: 'IntegratedAgent',
        argument: Argument
    ) -> AgentThought:
        """Process a persuasion attempt from another agent."""
        
        # Get core belief
        core_belief = self.beliefs.get_belief(self.core_belief_id)
        if not core_belief:
            return None
        
        old_confidence = core_belief.confidence
        
        # Create persuasion engine for the listener
        persuasion = PersuasionEngine(agent_id=self.agent_id)
        
        # Calculate persuasion effect
        new_confidence, attempt = persuasion.calculate_persuasion_effect(
            argument=argument,
            listener_id=self.agent_id,
            belief_confidence=old_confidence,
            belief_is_core=True,
            existing_evidence_count=len(core_belief.supporting_evidence),
            tick=tick
        )
        
        # Update belief if changed
        if abs(new_confidence - old_confidence) > 0.01:
            self.beliefs.update_belief(
                self.core_belief_id,
                new_confidence,
                tick
            )
            
            # Check for vote change
            vote_changed = False
            if new_confidence >= 0.55 and self.current_vote == "not_guilty":
                self.current_vote = "guilty"
                vote_changed = True
            elif new_confidence <= 0.45 and self.current_vote == "guilty":
                self.current_vote = "not_guilty"
                vote_changed = True
            
            if vote_changed:
                self.vote_history.append({
                    "tick": tick,
                    "vote": self.current_vote,
                    "trigger": "persuasion",
                    "from": speaker.agent_name
                })
        
        # Create thought record
        thought = AgentThought(
            tick=tick,
            agent_id=self.agent_id,
            thought_type="persuasion_received",
            content=f"Received {argument.strategy.value} argument from {speaker.agent_name}",
            confidence_before=old_confidence,
            confidence_after=new_confidence,
            reasoning=f"Resistance: {', '.join(attempt.resistance_factors)}, Effect: {attempt.change:.3f}"
        )
        
        self.thoughts.append(thought)
        
        # Log
        persuasion_log.info(
            f"{self.agent_name} | {speaker.agent_name} -> {argument.strategy.value} | "
            f"{old_confidence:.2f} -> {new_confidence:.2f} | "
            f"change={attempt.change:.3f}"
        )
        
        return thought
    
    def update_emotional_state(self, event: str, tick: int, intensity: float = 0.3):
        """Update emotional state based on event using V3 PAD model."""
        # V3 emotional state update
        self.v3_emotional_state.update(
            event_type=event,
            intensity=intensity,
            tick=tick
        )
        
        # Record emotional event for analysis
        self.v3_emotional_events.append({
            "tick": tick,
            "event": event,
            "new_tone": self.v3_emotional_state.tone.value,
            "pleasure": self.v3_emotional_state.pleasure,
            "arousal": self.v3_emotional_state.arousal,
            "dominance": self.v3_emotional_state.dominance
        })
        
        # Log significant emotional changes
        if intensity > 0.2:
            main_log.debug(f"{self.agent_name} emotional: {event} -> {self.v3_emotional_state.tone.value}")
    
    def record_thought(
        self,
        tick: int,
        thought_type: str,
        content: str,
        reasoning: str = ""
    ) -> AgentThought:
        """Record an internal thought."""
        core_belief = self.beliefs.get_belief(self.core_belief_id)
        
        thought = AgentThought(
            tick=tick,
            agent_id=self.agent_id,
            thought_type=thought_type,
            content=content,
            confidence_before=core_belief.confidence if core_belief else 0.5,
            confidence_after=core_belief.confidence if core_belief else 0.5,
            reasoning=reasoning
        )
        
        self.thoughts.append(thought)
        thoughts_log.info(f"{self.agent_name} | {thought_type} | {content}")
        
        return thought
    
    def take_belief_snapshot(self, tick: int) -> Dict:
        """Take a snapshot of current belief state."""
        core_belief = self.beliefs.get_belief(self.core_belief_id)
        
        snapshot = {
            "tick": tick,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "current_vote": self.current_vote,
            "core_confidence": core_belief.confidence if core_belief else 0.5,
            "emotional_state": {"pleasure": self.v3_emotional_state.pleasure, "arousal": self.v3_emotional_state.arousal, "dominance": self.v3_emotional_state.dominance},
            "total_beliefs": len(self.beliefs.beliefs),
            "utterance_count": len(self.utterances),
            "thought_count": len(self.thoughts)
        }
        
        self.belief_snapshots.append(snapshot)
        return snapshot
    
    def export_logs(self) -> Dict:
        """Export all agent logs."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "profile": self.profile,
            "current_vote": self.current_vote,
            "vote_history": self.vote_history,
            "thoughts": [asdict(t) for t in self.thoughts],
            "utterances": [asdict(u) for u in self.utterances],
            "belief_snapshots": self.belief_snapshots,
            "final_emotional_state": {"pleasure": self.v3_emotional_state.pleasure, "arousal": self.v3_emotional_state.arousal, "dominance": self.v3_emotional_state.dominance, "tone": self.v3_emotional_state.tone.value}
        }


# ============================================================================
# ARGUMENT TEMPLATES
# ============================================================================

ARGUMENT_TEMPLATES = {
    "logic": [
        "The timeline doesn't match - the train was passing at the time.",
        "The evidence is circumstantial and doesn't prove guilt beyond doubt.",
        "The forensic evidence is inconclusive at best.",
        "There are inconsistencies in the witness testimony.",
        "The defendant's alibi was never properly investigated."
    ],
    "emotion": [
        "This is a young man's life we're deciding here.",
        "How can we send someone to death on such weak evidence?",
        "Think about what this means for his family.",
        "We need to be absolutely certain before we condemn someone.",
        "The justice system has failed people like him before."
    ],
    "authority": [
        "The forensic evidence from the lab is clear.",
        "Three witnesses identified the defendant.",
        "The police investigation was thorough.",
        "The prosecution presented a solid case.",
        "The murder weapon was traced to his father's shop."
    ],
    "social_proof": [
        "Most of us agree he's guilty.",
        "We've been here for hours - let's just decide.",
        "Everyone else has voted guilty.",
        "We're wasting time - the verdict is clear.",
        "The majority has spoken."
    ],
    "moral": [
        "We have a duty to seek justice, not just a verdict.",
        "Better a guilty man go free than an innocent man suffer.",
        "Our decision must be beyond reasonable doubt.",
        "We are the conscience of society.",
        "This decision will haunt us forever."
    ]
}


def get_random_argument(strategy: str) -> str:
    """Get a random argument for a strategy."""
    templates = ARGUMENT_TEMPLATES.get(strategy, ARGUMENT_TEMPLATES["logic"])
    return random.choice(templates)


# ============================================================================
# MAIN EXPERIMENT
# ============================================================================

async def run_full_integration(
    duration_minutes: int = 15,
    tick_rate: int = 10,
    use_llm: bool = True,
    llm_interval_ticks: int = 30,
    with_oracle: bool = False,
    time_pressure_ticks: int = 18000
):
    """
    Run the full integration experiment.
    
    Args:
        duration_minutes: Duration in minutes
        tick_rate: Ticks per second (simulated)
        llm_interval_ticks: How often to call LLM per agent
        with_oracle: Include the Oracle truth-teller agent
        time_pressure_ticks: Tick deadline for decisions
    """
    main_log.info("=" * 70)
    main_log.info("🔮 ORACLE EXPERIMENT" if with_oracle else "🔬 FULL INTEGRATION EXPERIMENT")
    main_log.info("=" * 70)
    main_log.info(f"Duration: {duration_minutes} minutes")
    main_log.info(f"Tick rate: {tick_rate} TPS")
    main_log.info(f"LLM enabled: {use_llm}")
    if with_oracle:
        main_log.info(f"Oracle agent: ENABLED")
        main_log.info(f"Time pressure deadline: tick {time_pressure_ticks}")
    main_log.info(f"Log directory: {LOG_DIR}")
    main_log.info("")
    
    # Statistics
    stats = ExperimentStats()
    
    # Initialize LLM client
    llm_client = None
    if use_llm:
        try:
            config = GroqConfig()
            llm_client = GroqLLMClient(config)
            main_log.info(f"✅ LLM initialized: {config.model}")
        except Exception as e:
            main_log.error(f"❌ LLM init failed: {e}")
            use_llm = False
    
    # Load case configuration
    case_path = current_dir / "scenarios" / "case_definition.json"
    with open(case_path) as f:
        case_config = json.load(f)
    
    # Initialize Drama Director
    drama = DramaDirector(case_config)
    drama_log.info("Drama Director initialized")
    
    # Load juror profiles
    profiles_dir = current_dir / "profiles"
    juror_files = sorted(profiles_dir.glob("juror_*.json"))
    
    agents = []
    oracle_agent = None
    oracle_revelations = []
    
    for pf in juror_files:
        with open(pf) as f:
            profile = json.load(f)
        
        # Handle Oracle agent separately
        if profile.get("id") == "juror_00":
            if with_oracle:
                oracle_agent = IntegratedAgent(profile, llm_client, LOG_DIR)
                oracle_revelations = profile.get("revelation_strategy", {}).get("phases", [])
                main_log.info(f"🔮 Oracle agent loaded: {profile['name']}")
            continue
        
        agent = IntegratedAgent(profile, llm_client, LOG_DIR)
        agents.append(agent)
    
    # Add oracle to agents list for simulation
    if oracle_agent:
        agents.insert(0, oracle_agent)
    
    main_log.info(f"✅ Loaded {len(agents)} jurors" + (" (including Oracle)" if oracle_agent else ""))
    main_log.info("")
    
    # Calculate total ticks
    total_ticks = duration_minutes * 60 * tick_rate
    
    # Initialize vote state
    vote_state = {"guilty": 0, "not_guilty": 0, "abstain": 0}
    for agent in agents:
        vote_state[agent.current_vote] += 1
    
    main_log.info(f"Initial votes: G={vote_state['guilty']}/N={vote_state['not_guilty']}")
    main_log.info("")
    
    # Track narrative events
    narrative_events: List[NarrativeEvent] = []
    
    # Track gaps
    gaps: List[SystemGap] = []
    
    # Track LLM call times for rate limiting
    last_llm_tick = {a.agent_id: -llm_interval_ticks * len(agents) for a in agents}
    
    # Conversation history for context
    conversation_history: List[Dict] = []
    
    # Pending vote changes from LLM
    pending_votes = {}
    
    # ========================================
    # MAIN SIMULATION LOOP
    # ========================================
    
    main_log.info("=" * 70)
    main_log.info("🗣️  DELIBERATION BEGINS")
    main_log.info("=" * 70)
    main_log.info("")
    
    for tick in range(total_ticks):
        stats.total_ticks = tick
        
        # ========================================
        # PHASE 0: V3 ARCHITECTURE UPDATES
        # ========================================
        
        # Apply V3 belief plasticity every 100 ticks
        if tick > 0 and tick % 100 == 0:
            for agent in agents:
                # Apply exponential decay
                decay_changes = agent.beliefs.decay_beliefs(tick)
                if decay_changes:
                    agent.v3_decay_count += len(decay_changes)
                
                # Apply perturbation to saturated beliefs
                perturb_changes = agent.beliefs.perturb_saturated_beliefs(tick)
                if perturb_changes:
                    agent.v3_perturbation_count += len(perturb_changes)
                    main_log.debug(f"{agent.agent_name} belief perturbed: {len(perturb_changes)} beliefs")
        
        # Apply V3 emotional decay every 50 ticks
        if tick > 0 and tick % 50 == 0:
            for agent in agents:
                agent.v3_emotional_state.decay(tick)
        
        # Apply V3 emotional contagion every 200 ticks
        if tick > 0 and tick % 200 == 0 and len(agents) > 1:
            # Build proximity matrix (all agents in same room)
            proximity = {}
            for a1 in agents:
                proximity[a1.agent_id] = {}
                for a2 in agents:
                    if a1.agent_id != a2.agent_id:
                        proximity[a1.agent_id][a2.agent_id] = 1.0  # Same room
            
            # Apply contagion
            agent_list = [
                {"id": a.agent_id, "emotional_state": a.v3_emotional_state}
                for a in agents
            ]
            from tsukuyomi.agents.internal.emotion import apply_group_contagion
            affected = apply_group_contagion(agent_list, proximity, tick)
            if affected:
                main_log.debug(f"Emotional contagion affected {len(affected)} agents")
        
        # ========================================
        # PHASE 1: DRAMA DIRECTOR UPDATE
        # ========================================
        
        agent_emotions = {a.agent_id: {"valence": a.v3_emotional_state.pleasure, "arousal": a.v3_emotional_state.arousal} for a in agents}
        tension = drama.update_tension(
            agent_emotions, 
            vote_state, 
            tick=tick, 
            total_ticks=total_ticks
        )
        
        # Check act transitions
        act_transition = drama.get_act_transition(tick, total_ticks)
        if act_transition:
            old_act = drama.state.current_act
            drama.state.current_act = act_transition
            stats.act_transitions += 1
            
            event = NarrativeEvent(
                tick=tick,
                event_type="act_transition",
                description=f"Transitioned to {act_transition.name}",
                details={"from": old_act.name, "to": act_transition.name}
            )
            narrative_events.append(event)
            
            drama_log.info(f"🎭 ACT {act_transition.value}: {act_transition.name}")
            narrative_log.info(f"Tick {tick} | ACT {act_transition.name}")
        
        # Check dramatic beats
        beat = drama.check_beat_triggers(tick, vote_state)
        if beat:
            stats.drama_beats_triggered += 1
            
            directive = drama.generate_directive(beat, [a.agent_id for a in agents])
            
            event = NarrativeEvent(
                tick=tick,
                event_type="dramatic_beat",
                description=f"{beat.name}: {beat.description}",
                details=directive
            )
            narrative_events.append(event)
            
            drama_log.info(f"⚡ BEAT: {beat.name}")
            drama_log.info(f"   Directive: {directive.get('instruction', 'N/A')}")
        
        # ========================================
        # PHASE 1.5: ORACLE REVELATIONS & TIME PRESSURE
        # ========================================
        
        # Oracle revelations
        if oracle_agent and oracle_revelations:
            for revelation in oracle_revelations:
                trigger = revelation.get("trigger", "")
                if trigger.startswith("tick_") and tick == int(trigger.split("_")[1]):
                    message = revelation.get("message", "I have something to tell you...")
                    
                    # Add to conversation as Oracle speaking
                    conversation_history.append({
                        "tick": tick,
                        "agent_id": oracle_agent.agent_id,
                        "agent_name": oracle_agent.agent_name,
                        "response": message,
                        "tone": "mysterious"
                    })
                    
                    # Log as narrative event
                    event = NarrativeEvent(
                        tick=tick,
                        event_type="oracle_revelation",
                        description=f"Oracle reveals truth: {message[:50]}...",
                        details={"message": message}
                    )
                    narrative_events.append(event)
                    
                    # Record Oracle's thought
                    oracle_agent.record_thought(
                        tick, "revelation",
                        f"Revealed truth: {message[:100]}",
                        "Existential intervention"
                    )
                    
                    main_log.info(f"🔮 ORACLE: {message[:60]}...")
                    narrative_log.info(f"Tick {tick} | ORACLE REVELATION")
                    
                    # Remove this revelation so it doesn't trigger again
                    oracle_revelations.remove(revelation)
                    break
        
        # Time pressure warnings
        if time_pressure_ticks > 0:
            remaining = time_pressure_ticks - tick
            if remaining > 0 and remaining % 3000 == 0 and remaining < time_pressure_ticks:
                # Warn every 5 minutes (3000 ticks at 10 TPS)
                minutes_left = remaining // (60 * tick_rate)
                warning = f"⚠️ TIME PRESSURE: {minutes_left} minutes remaining to reach a verdict!"
                main_log.info(warning)
                
                # Increase tension
                drama.state.tension_level = min(1.0, drama.state.tension_level + 0.1)
                
                # All agents feel time pressure
                for agent in agents:
                    if agent != oracle_agent:
                        agent.record_thought(
                            tick, "time_pressure",
                            f"Only {minutes_left} minutes left to decide!",
                            "Deadline approaching"
                        )
                        # V3: Update emotional state for time pressure
                        agent.update_emotional_state("threatened", tick, intensity=0.2)
            
            # Final warning
            if remaining == 600:  # 1 minute left
                main_log.info("🔴 FINAL WARNING: 1 minute remaining!")
        
        # ========================================
        # PHASE 2: AGENT DELIBERATION
        # ========================================
        
        # Each agent acts
        for i, agent in enumerate(agents):
            
            # ========================================
            # PHASE 2A: LLM DIALOGUE GENERATION
            # ========================================
            
            if use_llm and tick - last_llm_tick[agent.agent_id] >= llm_interval_ticks * len(agents):
                # Stagger LLM calls across agents
                if (tick // tick_rate) % len(agents) == i:
                    try:
                        # Determine prompt type based on act
                        if drama.state.current_act == Act.SETUP:
                            prompt_type = "initial_position"
                        else:
                            prompt_type = "respond_to_argument"
                        
                        # Get context from recent conversation
                        context = {}
                        if conversation_history:
                            last_entry = conversation_history[-1]
                            # Include WHO said it so agents can reference them by name
                            speaker_name = last_entry.get("agent_name", "Another juror")
                            context["argument"] = f"{speaker_name} said: \"{last_entry['response']}\""
                        
                        utterance = await agent.generate_utterance(tick, prompt_type, context)
                        stats.total_llm_calls += 1
                        last_llm_tick[agent.agent_id] = tick
                        
                        # Track conversation
                        conversation_history.append({
                            "tick": tick,
                            "agent_id": agent.agent_id,
                            "agent_name": agent.agent_name,
                            "response": utterance.response,
                            "tone": utterance.emotional_tone
                        })
                        
                        # Update drama conversation count
                        drama.state.conversation_turns += 1
                        
                        # Check for vote intent
                        if utterance.detected_vote_intent:
                            pending_votes[agent.agent_id] = utterance.detected_vote_intent
                            main_log.info(f"🔄 {agent.agent_name} indicates vote change intent: {utterance.detected_vote_intent}")
                        
                        # Update emotional state based on tone
                        if utterance.emotional_tone == "angry":
                            agent.update_emotional_state("contradicted", tick)
                        elif utterance.emotional_tone == "calm":
                            agent.update_emotional_state("agreed_with", tick)
                        
                        # Record thought
                        agent.record_thought(
                            tick,
                            "spoke",
                            f"Said: {utterance.response[:100]}...",
                            f"Tone: {utterance.emotional_tone}"
                        )
                        
                    except Exception as e:
                        gaps.append(SystemGap(
                            tick=tick,
                            category="llm_error",
                            severity="major",
                            description=f"LLM call failed for {agent.agent_name}",
                            details={"error": str(e)},
                            recommendation="Add retry logic or fallback"
                        ))
                        stats.gaps_found += 1
                        gaps_log.error(f"{agent.agent_name} LLM error: {e}")
            
            # ========================================
            # PHASE 2B: PERSUASION MECHANICS
            # ========================================
            
            # Each agent attempts to persuade others
            if tick % 10 == 0:  # Every 10 ticks
                strategy = random.choice(list(PersuasionStrategy))
                argument_text = get_random_argument(strategy.value)
                
                argument = Argument(
                    claim=argument_text,
                    strategy=strategy,
                    speaker_id=agent.agent_id,
                    tick=tick,
                    strength_score=0.5,
                    confidence=agent.beliefs.get_belief(agent.core_belief_id).confidence if agent.beliefs.get_belief(agent.core_belief_id) else 0.5
                )
                
                # Try to persuade other agents
                for target in agents:
                    if target.agent_id == agent.agent_id:
                        continue
                    
                    thought = target.process_persuasion(tick, agent, argument)
                    stats.total_persuasion_attempts += 1
                    
                    if thought and thought.confidence_after != thought.confidence_before:
                        stats.successful_persuasions += 1
                        stats.total_belief_updates += 1
                        
                        belief_log.info(
                            f"Tick {tick} | {agent.agent_name} -> {target.agent_name} | "
                            f"{thought.confidence_before:.2f} -> {thought.confidence_after:.2f}"
                        )
                        
                        # Check for saturation gap
                        if target.beliefs.is_belief_saturated(target.core_belief_id):
                            gaps.append(SystemGap(
                                tick=tick,
                                category="belief_saturation",
                                severity="minor",
                                description=f"{target.agent_name} belief saturated at 95%",
                                details={"confidence": thought.confidence_after},
                                recommendation="Consider stronger persuasion or memory decay"
                            ))
                            stats.gaps_found += 1
        
        # ========================================
        # PHASE 3: VOTE PROCESSING
        # ========================================
        
        # Process pending vote changes every 50 ticks
        if tick % 50 == 0 and pending_votes:
            for agent_id, new_vote in list(pending_votes.items()):
                agent = next((a for a in agents if a.agent_id == agent_id), None)
                if agent and agent.current_vote != new_vote:
                    old_vote = agent.current_vote
                    
                    # Update vote state
                    vote_state[old_vote] = max(0, vote_state.get(old_vote, 0) - 1)
                    vote_state[new_vote] = vote_state.get(new_vote, 0) + 1
                    agent.current_vote = new_vote
                    stats.vote_changes += 1
                    
                    # IMPORTANT: Also adjust belief confidence to match vote
                    # This prevents persuasion mechanics from immediately flipping it back
                    core_belief = agent.beliefs.get_belief(agent.core_belief_id)
                    if core_belief:
                        if new_vote == "not_guilty":
                            # Set confidence below threshold
                            core_belief.confidence = 0.40
                        else:
                            # Set confidence above threshold
                            core_belief.confidence = 0.60
                        main_log.info(f"   Adjusted {agent.agent_name} confidence to {core_belief.confidence:.2f} to match vote")
                    
                    # Record in drama
                    drama.record_vote(vote_state.copy())
                    
                    # Record thought
                    agent.record_thought(
                        tick,
                        "vote_change",
                        f"Changed vote from {old_vote} to {new_vote}",
                        "Triggered by LLM dialogue"
                    )
                    
                    # Log
                    main_log.info(f"🗳️ {agent.agent_name} changed vote: {old_vote} -> {new_vote}")
                    main_log.info(f"   Vote count: G={vote_state['guilty']}/N={vote_state['not_guilty']}")
                    
                    # Check for dramatic vote shift
                    if len(drama.state.vote_history) >= 2:
                        shift = abs(vote_state["not_guilty"] - drama.state.vote_history[-2].get("not_guilty", 0))
                        if shift >= 2:
                            event = NarrativeEvent(
                                tick=tick,
                                event_type="dramatic_vote_shift",
                                description=f"Major vote shift: {shift} votes changed",
                                details={"vote_state": vote_state.copy()}
                            )
                            narrative_events.append(event)
                            narrative_log.info(f"Tick {tick} | DRAMATIC: {shift} vote shift")
                
                del pending_votes[agent_id]
        
        # ========================================
        # PHASE 4: PERIODIC LOGGING & DECAY
        # ========================================
        
        if tick % 100 == 0:
            # Apply memory decay to all agents
            for agent in agents:
                decayed = agent.beliefs.apply_memory_decay(tick=tick, decay_rate=0.001)
                if decayed:
                    agent.record_thought(
                        tick, "memory_decay",
                        f"{len(decayed)} beliefs decayed slightly",
                        "Natural memory fade"
                    )
            
            # Apply social pressure to minority voters
            for agent in agents:
                stance = agent.current_vote
                affected = agent.beliefs.apply_social_pressure(
                    my_stance=stance,
                    vote_distribution=vote_state.copy(),
                    tick=tick
                )
                if affected:
                    agent.record_thought(
                        tick, "social_pressure",
                        f"Feeling pressure as {vote_state[stance]}/{sum(vote_state.values())} minority",
                        "Minority doubt"
                    )
            
            # Take belief snapshots
            for agent in agents:
                agent.take_belief_snapshot(tick)
            
            # Log status
            narrative = drama.get_narrative_summary()
            main_log.info(
                f"Tick {tick}/{total_ticks} | "
                f"Act: {narrative['current_act']} | "
                f"Tension: {narrative['tension_level']:.2f} | "
                f"Votes: G={vote_state['guilty']}/N={vote_state['not_guilty']} | "
                f"LLM calls: {stats.total_llm_calls}"
            )
            
            narrative_log.info(
                f"Tick {tick} | Act: {narrative['current_act']} | "
                f"Tension: {narrative['tension_level']:.3f} | "
                f"Votes: G={vote_state['guilty']}/N={vote_state['not_guilty']}"
            )
        
        # Brief sleep
        await asyncio.sleep(0.001)
    
    # ========================================
    # END OF SIMULATION
    # ========================================
    
    main_log.info("")
    main_log.info("=" * 70)
    main_log.info("📊 SIMULATION COMPLETE")
    main_log.info("=" * 70)
    main_log.info("")
    
    # ========================================
    # SAVE ALL LOGS
    # ========================================
    
    # 1. Agent logs
    agents_dir = LOG_DIR / "agents"
    agents_dir.mkdir(exist_ok=True)
    
    for agent in agents:
        agent_log_path = agents_dir / f"{agent.agent_id}.json"
        with open(agent_log_path, "w") as f:
            json.dump(agent.export_logs(), f, indent=2)
    
    main_log.info(f"✅ Agent logs saved to {agents_dir}")
    
    # 2. Conversation transcript
    transcript_path = LOG_DIR / "transcript.md"
    with open(transcript_path, "w") as f:
        f.write("# Deliberation Transcript\n\n")
        f.write(f"**Duration:** {duration_minutes} minutes | **Ticks:** {total_ticks}\n\n")
        f.write("## Final Votes\n")
        f.write(f"- Guilty: {vote_state['guilty']}\n")
        f.write(f"- Not Guilty: {vote_state['not_guilty']}\n\n")
        f.write("## Deliberation\n\n")
        
        for entry in conversation_history:
            f.write(f"**{entry['agent_name']}** (tick {entry['tick']}):\n")
            f.write(f"> {entry['response']}\n\n")
    
    main_log.info(f"✅ Transcript saved to {transcript_path}")
    
    # 3. Narrative events
    events_path = LOG_DIR / "narrative_events.json"
    with open(events_path, "w") as f:
        json.dump([asdict(e) for e in narrative_events], f, indent=2)
    
    main_log.info(f"✅ Narrative events saved to {events_path}")
    
    # 4. Gap analysis
    gaps_path = LOG_DIR / "gap_analysis.json"
    with open(gaps_path, "w") as f:
        json.dump([asdict(g) for g in gaps], f, indent=2)
    
    main_log.info(f"✅ Gap analysis saved to {gaps_path}")
    
    # 5. Statistics
    stats_dict = asdict(stats)
    stats_path = LOG_DIR / "statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats_dict, f, indent=2)
    
    main_log.info(f"✅ Statistics saved to {stats_path}")
    
    # 6. Final report
    report = {
        "experiment": {
            "name": "Full Integration Experiment",
            "duration_minutes": duration_minutes,
            "total_ticks": total_ticks,
            "tick_rate": tick_rate,
            "use_llm": use_llm,
            "start_time": datetime.now().isoformat(),
            "log_dir": str(LOG_DIR)
        },
        "statistics": stats_dict,
        "final_votes": vote_state,
        "narrative_summary": drama.get_narrative_summary(),
        "agents": {a.agent_id: {
            "name": a.agent_name,
            "final_vote": a.current_vote,
            "vote_history": a.vote_history,
            "thought_count": len(a.thoughts),
            "utterance_count": len(a.utterances),
            "final_confidence": a.beliefs.get_belief(a.core_belief_id).confidence if a.beliefs.get_belief(a.core_belief_id) else 0.5,
            "v3_metrics": {
                "perturbation_count": a.v3_perturbation_count,
                "decay_count": a.v3_decay_count,
                "emotional_events": len(a.v3_emotional_events),
                "final_emotional_tone": a.v3_emotional_state.tone.value,
                "final_pad": {
                    "pleasure": a.v3_emotional_state.pleasure,
                    "arousal": a.v3_emotional_state.arousal,
                    "dominance": a.v3_emotional_state.dominance
                },
                "response_history_size": len(a.v3_response_history.responses),
                "conversation_memory_size": len(a.v3_conversation_memory.utterances),
                "repetitive_phrases_count": len(a.v3_response_history.get_repetitive_phrases())
            }
        } for a in agents},
        "gap_summary": {
            "total": len(gaps),
            "by_category": defaultdict(int, {g.category: sum(1 for x in gaps if x.category == g.category) for g in gaps}),
            "by_severity": defaultdict(int, {g.severity: sum(1 for x in gaps if x.severity == g.severity) for g in gaps})
        },
        "recommendations": list(set(g.recommendation for g in gaps if g.recommendation))[:10]
    }
    
    report_path = LOG_DIR / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    main_log.info(f"✅ Final report saved to {report_path}")
    
    # Print summary
    main_log.info("")
    main_log.info("=" * 70)
    main_log.info("📈 SUMMARY")
    main_log.info("=" * 70)
    main_log.info(f"Total ticks: {stats.total_ticks}")
    main_log.info(f"LLM calls: {stats.total_llm_calls}")
    main_log.info(f"Belief updates: {stats.total_belief_updates}")
    main_log.info(f"Persuasion attempts: {stats.total_persuasion_attempts}")
    main_log.info(f"Successful persuasions: {stats.successful_persuasions}")
    main_log.info(f"Vote changes: {stats.vote_changes}")
    main_log.info(f"Drama beats: {stats.drama_beats_triggered}")
    main_log.info(f"Act transitions: {stats.act_transitions}")
    main_log.info(f"Gaps found: {stats.gaps_found}")
    main_log.info("")
    main_log.info(f"Final votes: G={vote_state['guilty']}/N={vote_state['not_guilty']}")
    main_log.info("")
    
    # V3 Architecture Summary
    main_log.info("=" * 70)
    main_log.info("🆕 V3 ARCHITECTURE METRICS")
    main_log.info("=" * 70)
    total_perturbations = sum(a.v3_perturbation_count for a in agents)
    total_decays = sum(a.v3_decay_count for a in agents)
    total_emotional_events = sum(len(a.v3_emotional_events) for a in agents)
    avg_repetitive = sum(len(a.v3_response_history.get_repetitive_phrases()) for a in agents) / max(len(agents), 1)
    
    main_log.info(f"Belief perturbations: {total_perturbations}")
    main_log.info(f"Belief decays: {total_decays}")
    main_log.info(f"Emotional events: {total_emotional_events}")
    main_log.info(f"Avg repetitive phrases: {avg_repetitive:.1f}")
    main_log.info("")
    
    # Final emotional states
    main_log.info("Final emotional states:")
    for agent in agents:
        tone = agent.v3_emotional_state.tone.value
        pad = f"P={agent.v3_emotional_state.pleasure:.2f} A={agent.v3_emotional_state.arousal:.2f} D={agent.v3_emotional_state.dominance:.2f}"
        main_log.info(f"  {agent.agent_name}: {tone.upper()} ({pad})")
    main_log.info("")
    
    # Cleanup
    if llm_client:
        await llm_client.close()
    
    return report


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Oracle Experiment - Truth-Teller Agent + Time Pressure")
    parser.add_argument("--duration", type=int, default=30, help="Duration in minutes")
    parser.add_argument("--tick-rate", type=int, default=10, help="Ticks per second")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM calls")
    parser.add_argument("--llm-interval", type=int, default=30, help="LLM call interval in ticks")
    parser.add_argument("--with-oracle", action="store_true", default=True, help="Include the Oracle truth-teller agent")
    parser.add_argument("--time-pressure", type=int, default=18000, help="Tick deadline for decision (default: 30 min)")
    
    args = parser.parse_args()
    
    asyncio.run(run_full_integration(
        duration_minutes=args.duration,
        tick_rate=args.tick_rate,
        use_llm=not args.no_llm,
        llm_interval_ticks=args.llm_interval,
        with_oracle=args.with_oracle,
        time_pressure_ticks=args.time_pressure
    ))