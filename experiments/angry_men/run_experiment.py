"""
Angry Men Experiment - Main Runner
===================================

A sophisticated multi-agent deliberation simulation using the Tsukuyomi engine.
Features:
- 5 jurors with rich personalities, beliefs, and memories
- Drama Director for narrative pacing
- Full memory system integration
- Reasoning and decision logging
- Belief dynamics tracking
- Groq LLM integration with rate limiting (free tier)
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Ensure tsukuyomi is in path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from tsukuyomi.environment.core import FateEngine
from tsukuyomi.brain.agent_brain import AgentBrain
from tsukuyomi.transport.grpc.server import run_server
from tsukuyomi.guest_sdk import GuestAgent
from tsukuyomi.agents.cognitive.memory import MemoryManager
from tsukuyomi.core.belief.unified import BeliefManager, PersonalityBias
from tsukuyomi.agents.internal.emotion import StateManager, PersonalityBaseline, EmotionalState
from tsukuyomi.brain.relationship_manager import RelationshipManager
from tsukuyomi.brain.memory.memory_types import Memory, MemoryType

# Import drama director and Groq LLM
sys.path.insert(0, str(current_dir))
from drama.director import DramaDirector, Act
from groq_llm import GroqLLMClient, GroqConfig, build_juror_prompt

# Configure logging
LOG_DIR = current_dir / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"experiment_{datetime.now():%Y%m%d_%H%M%S}.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AngryMen")

# Force flush after each log
for handler in logging.getLogger().handlers:
    handler.flush = lambda: None  # Will be called explicitly


class JurorAgent:
    """
    Enhanced juror agent with full personality, memory, and belief systems.
    """
    
    def __init__(self, profile_path: str, llm_client: GroqLLMClient = None):
        self.profile = self._load_profile(profile_path)
        self.agent_id = self.profile["id"]
        self.llm_client = llm_client
        
        # Initialize subsystems
        self._init_memory()
        self._init_beliefs()
        self._init_emotional_state()
        self._init_relationships()
        
        # State tracking
        self.current_vote = self.profile.get("beliefs", {}).get("initial_stance", "guilty")
        self.vote_history = []
        
        # Reasoning log
        self.decision_log = []
        
        # Conversation history
        self.conversation_history = []
        
        logger.info(f"Initialized juror: {self.profile['name']} ({self.agent_id})")
    
    def _load_profile(self, path: str) -> dict:
        with open(path) as f:
            return json.load(f)
    
    def _init_memory(self):
        """Initialize 3-tier memory system."""
        self.memory = MemoryManager(self.agent_id)
        
        # Load initial memories
        mem_data = self.profile.get("memories", {})
        
        # Episodic memories
        for mem in mem_data.get("episodic", []):
            self.memory.add_fact(
                subject=mem.get("id", "unknown"),
                predicate="episodic_memory",
                obj=json.dumps(mem),
                confidence=mem.get("importance", 0.5)
            )
        
        # Semantic memories
        for mem in mem_data.get("semantic", []):
            self.memory.add_fact(
                subject="semantic",
                predicate=mem.get("content", "")[:50],
                obj=mem.get("content", ""),
                confidence=mem.get("confidence", 0.5)
            )
    
    def _init_beliefs(self):
        """Initialize belief manager."""
        bias = PersonalityBias(
            confirmation_bias=self.profile.get("personality", {}).get("traits", {}).get("stubbornness", 0.5),
            disconfirmation_resistance=0.5,
            social_pressure_immunity=0.3
        )
        self.beliefs = BeliefManager(self.agent_id, bias)
        
        # Load initial beliefs
        belief_data = self.profile.get("beliefs", {}).get("core_beliefs", {})
        for topic, data in belief_data.items():
            self.beliefs.add_evidence(
                topic=topic,
                position=data.get("position", "neutral"),
                weight=data.get("weight", 0.5),
                source_type="initial",
                description=data.get("description", ""),
                tick_added=0
            )
    
    def _init_emotional_state(self):
        """Initialize emotional state."""
        baseline_data = self.profile.get("personality", {}).get("baseline_emotion", {})
        baseline = PersonalityBaseline(
            valence_baseline=baseline_data.get("valence", 0.0),
            arousal_baseline=baseline_data.get("arousal", 0.5),
            dominance_baseline=baseline_data.get("dominance", 0.5)
        )
        self.emotions = StateManager(baseline)
    
    def _init_relationships(self):
        """Initialize relationship manager."""
        self.relationships = RelationshipManager(self.agent_id)
        
        # Load initial relationships (relationships are established but no events yet)
        # In full implementation, would add history events
        pass
    
    def get_communication_style(self) -> dict:
        """Get agent's communication preferences."""
        return self.profile.get("communication_style", {})
    
    def get_personality_summary(self) -> str:
        """Generate personality summary for LLM context."""
        p = self.profile.get("personality", {}).get("big_five", {})
        traits = self.profile.get("personality", {}).get("traits", {})
        
        summary = f"{self.profile['name']} is a {self.profile['age']}-year-old {self.profile['occupation']}. "
        
        # Big Five summary
        if p.get("openness", 0) < 0:
            summary += "Traditional, practical. "
        else:
            summary += "Open-minded, curious. "
        
        if p.get("agreeableness", 0) < 0:
            summary += "Competitive, challenging. "
        else:
            summary += "Cooperative, considerate. "
        
        if p.get("neuroticism", 0) > 0.5:
            summary += "Emotionally intense. "
        
        # Key traits
        key_traits = [t for t, v in traits.items() if v > 0.7]
        if key_traits:
            summary += f"Key traits: {', '.join(key_traits)}."
        
        return summary
    
    async def generate_response(self, prompt_type: str, context: dict = None) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            prompt_type: Type of prompt (initial_position, respond_to_argument, etc.)
            context: Additional context for the prompt
        
        Returns:
            Generated response
        """
        if not self.llm_client:
            return f"[{self.profile['name']} would respond here - LLM not configured]"
        
        prompt, system_prompt = build_juror_prompt(self, prompt_type, context)
        
        response = await self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Log the interaction
        self.conversation_history.append({
            "prompt_type": prompt_type,
            "context": context,
            "response": response,
            "timestamp": time.time()
        })
        
        return response
    
    def log_decision(self, decision_type: str, details: dict):
        """Log a decision for analysis."""
        self.decision_log.append({
            "timestamp": time.time(),
            "decision_type": decision_type,
            "details": details,
            "current_vote": self.current_vote,
            "emotional_state": self.emotions.get_state_dict()
        })


async def run_simulation(
    tick_rate: int = 10,
    duration_minutes: int = 15,
    use_llm: bool = True,
    llm_interval_ticks: int = 50  # Generate LLM response every N ticks
):
    """
    Run the Angry Men simulation.
    
    Args:
        tick_rate: Ticks per second
        duration_minutes: Duration in minutes
        use_llm: Whether to use LLM for responses
        llm_interval_ticks: How often to generate LLM responses
    """
    logger.info("=" * 60)
    logger.info("ANGRY MEN SIMULATION - STARTING")
    logger.info("=" * 60)
    
    # Initialize Groq LLM client
    llm_client = None
    if use_llm:
        config = GroqConfig()
        llm_client = GroqLLMClient(config)
        logger.info(f"LLM initialized: {config.model} (rate limit: {config.requests_per_minute} RPM)")
    
    # Load case configuration
    case_path = current_dir / "scenarios" / "case_definition.json"
    with open(case_path) as f:
        case_config = json.load(f)
    
    # Initialize Drama Director
    drama_director = DramaDirector(case_config)
    logger.info("Drama Director initialized")
    
    # Load juror profiles
    profiles_dir = current_dir / "profiles"
    juror_files = sorted(profiles_dir.glob("juror_*.json"))
    
    jurors = []
    for pf in juror_files:
        juror = JurorAgent(str(pf), llm_client=llm_client)
        jurors.append(juror)
    
    logger.info(f"Loaded {len(jurors)} jurors: {[j.profile['name'] for j in jurors]}")
    
    # Calculate total ticks
    total_ticks = duration_minutes * 60 * tick_rate
    
    # Track last LLM call per juror to stagger requests
    last_llm_tick = {j.agent_id: -llm_interval_ticks for j in jurors}
    
    # Create initial vote state
    vote_state = {"guilty": 4, "not_guilty": 1, "abstain": 0}
    
    # Track conversation for tension calculation
    conversation_history = []  # List of (speaker, content, tick)
    conflict_keywords = ["disagree", "wrong", "impossible", "ridiculous", "nonsense", "lie", "absurd"]
    agreement_keywords = ["agree", "exactly", "precisely", "correct", "right", "true"]
    
    # Track vote change intents from LLM responses
    pending_vote_changes = {}  # agent_id -> new_vote
    
    # Start gRPC Server
    logger.info("Starting gRPC server...")
    server_task = asyncio.create_task(run_server(tick_rate=tick_rate, host="0.0.0.0", port=50051))
    await asyncio.sleep(2)  # Wait for server startup
    
    # Main simulation loop
    logger.info(f"Starting simulation: {duration_minutes} minutes, {tick_rate} TPS")
    logger.info(f"LLM calls: every {llm_interval_ticks} ticks (staggered across jurors)")
    
    for tick in range(0, total_ticks, tick_rate):
        # Update drama director
        agent_emotions = {j.agent_id: j.emotions.get_state_dict() for j in jurors}
        tension = drama_director.update_tension(agent_emotions)
        
        # Check for act transitions
        act_transition = drama_director.get_act_transition(tick, total_ticks)
        if act_transition:
            drama_director.state.current_act = act_transition
            logger.info(f"=== ACT {act_transition.value}: {act_transition.name} ===")
        
        # Check for dramatic beats
        beat = drama_director.check_beat_triggers(tick, vote_state)
        if beat:
            logger.info(f"⚡ DRAMATIC BEAT: {beat.name}")
            directive = drama_director.generate_directive(beat, [j.agent_id for j in jurors])
            logger.info(f"   Directive: {directive.get('instruction', 'N/A')}")
        
        # Generate LLM responses (staggered)
        if use_llm and llm_client:
            for i, juror in enumerate(jurors):
                # Stagger LLM calls across jurors
                if tick - last_llm_tick[juror.agent_id] >= llm_interval_ticks * len(jurors):
                    if (tick // tick_rate) % (len(jurors)) == i:
                        try:
                            # Determine prompt type based on act
                            if drama_director.state.current_act == Act.SETUP:
                                prompt_type = "initial_position"
                            else:
                                prompt_type = "respond_to_argument"
                            
                            response = await juror.generate_response(prompt_type)
                            last_llm_tick[juror.agent_id] = tick
                            
                            # Track conversation
                            conversation_history.append({
                                "speaker": juror.profile["name"],
                                "content": response,
                                "tick": tick
                            })
                            
                            # Update drama director conversation count
                            drama_director.state.conversation_turns += 1
                            
                            # Detect vote change intent
                            response_lower = response.lower()
                            if any(phrase in response_lower for phrase in ["change my vote", "switch to not guilty", "vote not guilty", "i'm now voting", "change to not"]):
                                pending_vote_changes[juror.agent_id] = "not_guilty"
                                logger.info(f"🔄 {juror.profile['name']} indicates vote change to NOT GUILTY")
                            elif any(phrase in response_lower for phrase in ["change my vote to guilty", "switch to guilty", "vote guilty now"]):
                                pending_vote_changes[juror.agent_id] = "guilty"
                                logger.info(f"🔄 {juror.profile['name']} indicates vote change to GUILTY")
                            
                            # Update emotional state based on response content
                            conflict_count = sum(1 for kw in conflict_keywords if kw in response_lower)
                            agreement_count = sum(1 for kw in agreement_keywords if kw in response_lower)
                            
                            # Apply emotional events
                            if conflict_count > agreement_count:
                                juror.emotions.apply_event("contradicted", tick)
                            elif agreement_count > conflict_count:
                                juror.emotions.apply_event("agreed_with", tick)
                            
                            # High conflict triggers anger
                            if conflict_count >= 2:
                                juror.emotions.apply_event("criticized", tick)
                            
                            logger.info(f"🗣️ {juror.profile['name']}: {response[:100]}...")
                        except Exception as e:
                            logger.error(f"LLM error for {juror.profile['name']}: {e}")
        
        # Log every 50 ticks
        if tick % 50 == 0:
            narrative = drama_director.get_narrative_summary()
            logger.info(
                f"Tick {tick}/{total_ticks} | "
                f"Act: {narrative['current_act']} | "
                f"Tension: {narrative['tension_level']:.2f} | "
                f"Votes: G={vote_state['guilty']}/N={vote_state['not_guilty']}"
            )
            # Flush logs to file
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        
        # Process pending vote changes every 100 ticks
        if tick % 100 == 0 and pending_vote_changes:
            for agent_id, new_vote in list(pending_vote_changes.items()):
                # Find the juror
                juror = next((j for j in jurors if j.agent_id == agent_id), None)
                if juror:
                    old_vote = juror.current_vote
                    
                    # Update vote state
                    if old_vote != new_vote:
                        vote_state[old_vote] = max(0, vote_state.get(old_vote, 0) - 1)
                        vote_state[new_vote] = vote_state.get(new_vote, 0) + 1
                        juror.current_vote = new_vote
                        
                        # Record in drama director
                        drama_director.record_vote(vote_state.copy())
                        
                        # Log decision
                        juror.log_decision("vote_change", {
                            "from": old_vote,
                            "to": new_vote,
                            "tick": tick
                        })
                        
                        logger.info(f"🗳️ {juror.profile['name']} changed vote: {old_vote} -> {new_vote}")
                        logger.info(f"   New vote count: G={vote_state['guilty']}/N={vote_state['not_guilty']}")
                    
                del pending_vote_changes[agent_id]
        
        await asyncio.sleep(0.1)  # Brief pause between ticks
    
    # Simulation complete
    logger.info("=" * 60)
    logger.info("SIMULATION COMPLETE")
    logger.info("=" * 60)
    
    # Save decision logs
    logs_dir = current_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Build comprehensive results
    results = {
        "metadata": {
            "duration_minutes": duration_minutes,
            "total_ticks": total_ticks,
            "tick_rate": tick_rate,
            "use_llm": use_llm,
            "timestamp": datetime.now().isoformat()
        },
        "narrative": drama_director.get_narrative_summary(),
        "final_votes": vote_state,
        "conversation": conversation_history,
        "jurors": {}
    }
    
    for juror in jurors:
        results["jurors"][juror.agent_id] = {
            "name": juror.profile["name"],
            "final_vote": juror.current_vote,
            "vote_history": juror.vote_history,
            "emotional_state": juror.emotions.get_state_dict(),
            "decision_count": len(juror.decision_log),
            "conversation_count": len(juror.conversation_history)
        }
        
        # Save individual decision logs
        log_path = logs_dir / f"decisions_{juror.agent_id}.json"
        with open(log_path, "w") as f:
            json.dump({
                "decisions": juror.decision_log,
                "conversations": juror.conversation_history
            }, f, indent=2)
    
    # Save main results file
    results_path = logs_dir / f"results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save conversation transcript as readable text
    transcript_path = logs_dir / f"transcript_{datetime.now():%Y%m%d_%H%M%S}.md"
    with open(transcript_path, "w") as f:
        f.write("# Angry Men Deliberation Transcript\n\n")
        f.write(f"Duration: {duration_minutes} minutes | Ticks: {total_ticks}\n\n")
        f.write("## Final Votes\n")
        f.write(f"- Guilty: {vote_state['guilty']}\n")
        f.write(f"- Not Guilty: {vote_state['not_guilty']}\n\n")
        f.write("## Deliberation\n\n")
        for entry in conversation_history:
            f.write(f"**{entry['speaker']}** (tick {entry['tick']}):\n")
            f.write(f"> {entry['content']}\n\n")
    
    # Save narrative summary
    narrative_summary = drama_director.get_narrative_summary()
    with open(logs_dir / "narrative_summary.json", "w") as f:
        json.dump(narrative_summary, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    logger.info(f"Transcript saved to {transcript_path}")
    logger.info(f"Final votes: G={vote_state['guilty']}/N={vote_state['not_guilty']}")
    logger.info(f"Conversation turns: {len(conversation_history)}")
    logger.info(f"Final narrative state: {narrative_summary}")
    
    # Cleanup
    if llm_client:
        await llm_client.close()
    
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    
    return narrative_summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Angry Men Simulation")
    parser.add_argument("--ticks", type=int, default=10, help="Ticks per second")
    parser.add_argument("--duration", type=int, default=15, help="Duration in minutes")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM calls")
    parser.add_argument("--llm-interval", type=int, default=50, help="LLM call interval in ticks")
    
    args = parser.parse_args()
    
    asyncio.run(run_simulation(
        tick_rate=args.ticks,
        duration_minutes=args.duration,
        use_llm=not args.no_llm,
        llm_interval_ticks=args.llm_interval
    ))