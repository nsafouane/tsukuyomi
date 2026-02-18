"""
Full Integration Experiment - V2 + LLM + Drama
================================================

Comprehensive experiment combining:
- V2 belief/persuasion mechanics
- LLM-generated character dialogue (Groq)
- Drama director for narrative pacing
- Complete logging of EVERYTHING

Tracks:
- Agent thoughts (internal reasoning)
- Agent talk (LLM dialogue)
- Agent behavior (vote changes, belief updates)
- Narrative flow (acts, beats, tension)
- System gaps and weaknesses

Run: python3 experiments/angry_men/run_full_integration.py --duration 15
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
from tsukuyomi.agent import (
    BeliefSystem, Belief, BeliefType, EvidenceStrength,
    PersuasionEngine, PersuasionStrategy, PersuasionAttempt, Argument,
    ContextManager,
    ProposalHandler, Proposal, ProposalStatus, ProposalType,
    AgentIdentity, PersonalityTraits,
    apply_personality_to_persuasion_engine
)

from tsukuyomi.brain.deliberation import DeliberationEngine
from tsukuyomi.proto.emotional_expression import EmotionalExpression
from tsukuyomi.proto.conversation_manager import ConversationManager, TurnContext, TurnDecision

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
        self._init_cognitive_richness()
        
        # V1 subsystems
        self.emotional_state = profile.get("personality", {}).get("baseline_emotion", {
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.5
        })
        
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
        
    def _init_cognitive_richness(self):
        """Initialize new cognitive richness modules (Phase 1 & 2)."""
        # Phase 1: Deliberation Engine
        self.deliberation_engine = DeliberationEngine(
            agent_id=self.agent_id,
            belief_system=self.beliefs,
            emotional_state=self.emotional_state,
            personality=asdict(self.identity.personality) if self.identity.personality else {},
            llm_call=None # Will use template or we could hook up Groq
        )
        
        # Phase 2: Emotional Expression
        self.expression_layer = EmotionalExpression(
            pad_state=self.emotional_state,
            personality=asdict(self.identity.personality) if self.identity.personality else {}
        )
    
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
        
        # Phase 1: Internal Deliberation
        deliberation_result = await self.deliberation_engine.deliberate(
            context={
                "stimulus": context.get("argument", ""),
                "others_votes": context.get("vote_distribution", {}),
                "my_vote": self.current_vote
            },
            tick=tick
        )
        self.record_thought(
            tick, "deliberation",
            f"Internal thoughts: {deliberation_result.content}",
            f"Emotional reaction: {deliberation_result.emotional_reaction}"
        )
        
        # Phase 2: Emotional Tone Modifiers
        modifiers = self.expression_layer.get_tone_modifiers()
        tone_guidance = modifiers.get_prompt_additions()
        
        # Build prompt
        prompt_template = DELIBERATION_PROMPTS.get(prompt_type, "")
        
        # Get current belief state
        core_belief = self.beliefs.get_belief(self.core_belief_id)
        confidence = core_belief.confidence if core_belief else 0.5
        
        # Phase 5: Memory Injection (Retrieving relevant context)
        relevant_memories = ""
        if hasattr(self, 'context') and self.context:
            # Retrieve last 3 relevant events
            memories = self.context.get_recent_events(limit=3)
            if memories:
                relevant_memories = "\nRELEVANT MEMORIES:\n" + "\n".join([f"- {m}" for m in memories])
        
        prompt = prompt_template.format(
            name=self.agent_name,
            personality=self._get_personality_summary(),
            stance=self.current_vote,
            confidence=int(confidence * 10),
            other_juror_argument=context.get("argument", ""),
            evidence=context.get("evidence", ""),
            triggers=self._get_emotional_triggers()
        )
        
        # Inject Cognitive Richness into system prompt
        system_prompt = (
            f"You are roleplaying as {self.agent_name}, a {self.profile['age']}-year-old {self.profile['occupation']} on a jury. "
            f"Stay completely in character. Be authentic.\n\n"
            f"{relevant_memories}\n\n"
            f"INTERNAL MONOLOGUE (NOT FOR PUBLIC): {deliberation_result.content}\n\n"
            f"TONE GUIDANCE: {tone_guidance}\n\n"
            f"Remember: Your responses should be shaped by your internal thoughts and emotional state."
        )
        
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
        persuasion = PersuasionEngine(
            agent_id=self.agent_id,
            personality=asdict(self.identity.personality) if self.identity.personality else {}
        )
        
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
    
    def update_emotional_state(self, event: str, tick: int):
        """Update emotional state based on event."""
        # Simplified emotional model
        if event == "persuaded":
            self.emotional_state["valence"] += 0.1
            self.emotional_state["arousal"] += 0.05
        elif event == "contradicted":
            self.emotional_state["valence"] -= 0.1
            self.emotional_state["arousal"] += 0.15
        elif event == "agreed_with":
            self.emotional_state["valence"] += 0.15
            self.emotional_state["arousal"] -= 0.05
        
        # Clamp values
        self.emotional_state["valence"] = max(-1, min(1, self.emotional_state["valence"]))
        self.emotional_state["arousal"] = max(0, min(1, self.emotional_state["arousal"]))
        self.emotional_state["dominance"] = max(0, min(1, self.emotional_state["dominance"]))
    
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
            "emotional_state": self.emotional_state.copy(),
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
            "final_emotional_state": self.emotional_state
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
    llm_interval_ticks: int = 30
):
    """
    Run the full integration experiment.
    
    Args:
        duration_minutes: Duration in minutes
        tick_rate: Ticks per second (simulated)
        llm_interval_ticks: How often to call LLM per agent
    """
    main_log.info("=" * 70)
    main_log.info("🔬 FULL INTEGRATION EXPERIMENT")
    main_log.info("=" * 70)
    main_log.info(f"Duration: {duration_minutes} minutes")
    main_log.info(f"Tick rate: {tick_rate} TPS")
    main_log.info(f"LLM enabled: {use_llm}")
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
    for pf in juror_files:
        with open(pf) as f:
            profile = json.load(f)
        agent = IntegratedAgent(profile, llm_client, LOG_DIR)
        agents.append(agent)
    
    main_log.info(f"✅ Loaded {len(agents)} jurors")
    
    # Phase 3: Initialize Conversation Manager
    conversation_manager = ConversationManager(agents=agents)
    main_log.info("✅ Conversation Manager initialized")
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
        # PHASE 1: DRAMA DIRECTOR UPDATE
        # ========================================
        
        agent_emotions = {a.agent_id: a.emotional_state for a in agents}
        tension = drama.update_tension(agent_emotions, vote_state)
        
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
        # PHASE 2: AGENT DELIBERATION
        # ========================================
        
        # Each agent acts
        for i, agent in enumerate(agents):
            
            # ========================================
            # PHASE 2A: LLM DIALOGUE GENERATION (Phase 3: Turn-Taking)
            # ========================================
            
            # Check if agent wants to speak using Conversation Manager
            turn_context = TurnContext(
                tick=tick,
                agent_id=agent.agent_id,
                last_speaker_id=conversation_manager.last_speaker_id,
                tension_level=tension,
                vote_distribution=vote_state
            )
            
            turn_result = conversation_manager.should_agent_speak(agent, turn_context)
            
            if use_llm and turn_result.decision in [TurnDecision.SPEAK, TurnDecision.INTERRUPT]:
                # Stagger LLM calls slightly to avoid overwhelming
                if (tick // 5) % len(agents) == i:
                    try:
                        if turn_result.decision == TurnDecision.INTERRUPT:
                            main_log.info(f"⚡ {agent.agent_name} INTERRUPTS {conversation_manager.last_speaker_id}!")
                        
                        # Determine prompt type based on act
                        if drama.state.current_act == Act.SETUP:
                            prompt_type = "initial_position"
                        else:
                            prompt_type = "respond_to_argument"
                        
                        # Get context from recent conversation
                        context = {"vote_distribution": vote_state}
                        if conversation_history:
                            last_entry = conversation_history[-1]
                            context["argument"] = last_entry["response"]
                        
                        utterance = await agent.generate_utterance(tick, prompt_type, context)
                        stats.total_llm_calls += 1
                        last_llm_tick[agent.agent_id] = tick
                        
                        # Record speech start in manager
                        conversation_manager.record_speech_start(agent.agent_id, tick)
                        
                        # Track conversation
                        conversation_history.append({
                            "tick": tick,
                            "agent_id": agent.agent_id,
                            "agent_name": agent.agent_name,
                            "response": utterance.response,
                            "tone": utterance.emotional_tone,
                            "is_interruption": turn_result.decision == TurnDecision.INTERRUPT
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
                            f"Decision: {turn_result.decision.value}, Reason: {turn_result.reason}"
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
            elif turn_result.decision == TurnDecision.WAIT:
                # Manager track silence
                conversation_manager.increment_silence()
            
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
                    
                    # FIXED: Also append to vote_history (Phase 6 Bug Fix)
                    agent.vote_history.append({
                        "tick": tick,
                        "vote": new_vote,
                        "trigger": "llm_dialogue",
                        "confidence": agent.beliefs.get_belief(agent.core_belief_id).confidence if agent.beliefs.get_belief(agent.core_belief_id) else 0.5
                    })
                    
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
            "final_confidence": a.beliefs.get_belief(a.core_belief_id).confidence if a.beliefs.get_belief(a.core_belief_id) else 0.5
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
    
    # Cleanup
    if llm_client:
        await llm_client.close()
    
    return report


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Full Integration Experiment")
    parser.add_argument("--duration", type=int, default=15, help="Duration in minutes")
    parser.add_argument("--tick-rate", type=int, default=10, help="Ticks per second")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM calls")
    parser.add_argument("--llm-interval", type=int, default=30, help="LLM call interval in ticks")
    
    args = parser.parse_args()
    
    asyncio.run(run_full_integration(
        duration_minutes=args.duration,
        tick_rate=args.tick_rate,
        use_llm=not args.no_llm,
        llm_interval_ticks=args.llm_interval
    ))