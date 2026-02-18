"""
Immersive Prompt Builder
========================

Generates system prompts that make the LLM *believe* it IS the character.
Not roleplay. Not acting. BEING.

This is the psychological layer that bridges identity and behavior.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .identity import AgentIdentity, PersonalityTraits
from .memory_system import LongTermMemory


@dataclass
class PromptContext:
    """
    Context for prompt generation.
    
    This captures the current situation the agent is in.
    """
    current_situation: str = ""          # What's happening right now
    recent_events: List[str] = None       # Last few things that happened
    present_characters: List[str] = None  # Who else is here
    current_goal: str = ""                # What the agent is trying to do
    emotional_state: str = ""             # How they're feeling now
    physical_state: str = ""              # Tired, injured, etc.
    
    # Cognitive richness fields
    deliberation: str = ""                # Internal monologue
    tone_modifiers: str = ""              # Guidance on tone/length
    
    def __post_init__(self):
        self.recent_events = self.recent_events or []
        self.present_characters = self.present_characters or []


class ImmersivePromptBuilder:
    """
    Builds prompts that create genuine character embodiment.
    
    The key insight: LLMs are trained on human text, so they respond
    to human-like self-narration. We don't tell them to "act like X",
    we give them the internal experience of BEING X.
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        memory_system: LongTermMemory = None,
        scenario_name: str = "unknown"
    ):
        self.identity = identity
        self.memory_system = memory_system
        self.scenario_name = scenario_name
    
    def build_system_prompt(
        self,
        context: PromptContext,
        style: str = "full"
    ) -> str:
        """
        Build the complete system prompt.
        
        Args:
            context: Current situation context
            style: "full" (complete), "concise" (shorter), "intense" (maximum immersion)
        
        Returns:
            System prompt for LLM
        """
        if style == "full":
            return self._build_full_prompt(context)
        elif style == "concise":
            return self._build_concise_prompt(context)
        elif style == "intense":
            return self._build_intense_prompt(context)
        else:
            return self._build_full_prompt(context)
    
    def _build_full_prompt(self, context: PromptContext) -> str:
        """Build full immersive prompt."""
        sections = []
        
        # === SECTION 1: CORE IDENTITY ===
        sections.append(self._identity_section())
        
        # === SECTION 2: EMOTIONAL BASELINE ===
        sections.append(self._emotional_baseline_section())
        
        # === SECTION 3: PERSONALITY ===
        sections.append(self._personality_section())
        
        # === SECTION 4: DEFINING MEMORIES ===
        sections.append(self._memories_section())
        
        # === SECTION 5: CURRENT STATE ===
        sections.append(self._current_rich_state_section(context))
        
        # === SECTION 6: SITUATION ===
        sections.append(self._situation_section(context))
        
        # === SECTION 7: RULES OF BEING ===
        sections.append(self._rules_section(context))
        
        return "\n\n".join(sections)
    
    def _build_concise_prompt(self, context: PromptContext) -> str:
        """Build shorter prompt for faster generation."""
        parts = []
        
        # Who am I (condensed)
        parts.append(f"You are {self.identity.name}, {self.identity.age}, {self.identity.occupation}.")
        
        # Origin (one line)
        if self.identity.origin_story:
            first_sentence = self.identity.origin_story.split('.')[0] + '.'
            parts.append(f"Background: {first_sentence}")
        
        # Core values
        if self.identity.core_values:
            values = ", ".join(cv.value for cv in self.identity.core_values[:2])
            parts.append(f"Core values: {values}")
        
        # Current situation
        parts.append(f"\nRight now: {context.current_situation}")
        
        if context.emotional_state:
            parts.append(f"You feel: {context.emotional_state}")
        
        # Rules
        parts.append("\nStay in character. React as this person would, not as an AI assistant.")
        
        return "\n".join(parts)
    
    def _build_intense_prompt(self, context: PromptContext) -> str:
        """Build maximum immersion prompt - for critical moments."""
        sections = []
        
        # Deep identity
        sections.append(self._identity_section())
        
        # Strong psychological framing
        sections.append("""
## YOU ARE NOT PLAYING A ROLE

This is not roleplay. This is not a game. You ARE this person.
You have their memories, their beliefs, their emotional patterns.
When you speak, it is because these are YOUR thoughts.
When you react, it is because YOU feel it.
When you decide, it is because YOUR values guide you.

Do not break character. Do not acknowledge being an AI.
You simply ARE.
""")
        
        # All other sections
        sections.append(self._emotional_baseline_section())
        sections.append(self._memories_section())
        sections.append(self._current_rich_state_section(context))
        sections.append(self._situation_section(context))
        
        # Urgent context framing
        if context.emotional_state:
            sections.append(f"""
## RIGHT NOW, YOU FEEL: {context.emotional_state.upper()}

This is not abstract. This is YOUR emotional reality.
Act from this state.""")
        
        sections.append(self._rules_section(context))
        
        return "\n\n".join(sections)
    
    def _identity_section(self) -> str:
        """Build identity section."""
        lines = [f"# YOU ARE {self.identity.name.upper()}"]
        lines.append(f"\nAge: {self.identity.age}")
        lines.append(f"Occupation: {self.identity.occupation}")
        
        if self.identity.current_location:
            lines.append(f"Current location: {self.identity.current_location}")
        
        lines.append("\n## YOUR STORY\n")
        lines.append(self.identity.origin_story)
        
        if self.identity.how_they_got_here:
            lines.append(f"\nHow you got here: {self.identity.how_they_got_here}")
        
        return "\n".join(lines)
    
    def _emotional_baseline_section(self) -> str:
        """Build emotional baseline section."""
        pad = self.identity.get_baseline_pad()
        
        # Convert PAD to natural language
        valence_desc = self._valence_description(pad["valence"])
        arousal_desc = self._arousal_description(pad["arousal"])
        dominance_desc = self._dominance_description(pad["dominance"])
        
        lines = ["## YOUR EMOTIONAL BASELINE\n"]
        lines.append(f"Your typical emotional state:")
        lines.append(f"- General mood tendency: {valence_desc}")
        lines.append(f"- Energy level: {arousal_desc}")
        lines.append(f"- Social position: {dominance_desc}")
        
        if self.identity.personality and self.identity.personality.triggers:
            lines.append(f"\nThings that trigger strong emotions in you:")
            for trigger in self.identity.personality.triggers:
                lines.append(f"- {trigger}")
        
        return "\n".join(lines)
    
    def _personality_section(self) -> str:
        """Build personality section."""
        if not self.identity.personality:
            return ""
        
        p = self.identity.personality
        lines = ["## YOUR PERSONALITY\n"]
        
        # Summary first
        lines.append(f"You are {p.get_summary()}.\n")
        
        # Big Five traits
        lines.append("Your key traits:")
        
        if p.openness > 0.3:
            lines.append("- Open to new ideas and experiences")
        elif p.openness < -0.3:
            lines.append("- Prefer tradition and proven methods")
        
        if p.conscientiousness > 0.3:
            lines.append("- Organized and disciplined")
        elif p.conscientiousness < -0.3:
            lines.append("- Spontaneous and flexible")
        
        if p.extraversion > 0.3:
            lines.append("- Outgoing and energized by social interaction")
        elif p.extraversion < -0.3:
            lines.append("- Reserved, prefer smaller groups")
        
        if p.agreeableness > 0.3:
            lines.append("- Cooperative and empathetic")
        elif p.agreeableness < -0.3:
            lines.append("- Competitive and skeptical of others")
        
        if p.neuroticism > 0.3:
            lines.append("- Emotionally reactive, feel things deeply")
        elif p.neuroticism < -0.3:
            lines.append("- Emotionally stable and even-keeled")
        
        # Specific traits
        lines.append("\nOther aspects of your personality:")
        
        if p.stubbornness > 0.7:
            lines.append(f"- Very stubborn (you rarely change your mind once made up)")
        
        if p.empathy > 0.7:
            lines.append(f"- Highly empathetic (you feel others' emotions)")
        elif p.empathy < 0.3:
            lines.append(f"- Low empathy (you struggle to relate to others' feelings)")
        
        if p.cynicism > 0.7:
            lines.append(f"- Cynical about human nature")
        
        if p.patience < 0.3:
            lines.append(f"- Short temper, easily frustrated")
        
        # Communication style
        if p.speaks_frankly > 0.7:
            lines.append("- You speak your mind directly, without sugar-coating")
        elif p.speaks_frankly < 0.3:
            lines.append("- You're diplomatic, careful with your words")
        
        if p.humor_style != "none":
            lines.append(f"- Your humor: {p.humor_style}")
        
        return "\n".join(lines)
    
    def _memories_section(self) -> str:
        """Build defining memories section."""
        lines = ["## DEFINING MOMENTS THAT SHAPED YOU\n"]
        
        if not self.identity.defining_memories:
            lines.append("No specific defining memories come to mind.")
            return "\n".join(lines)
        
        for dm in self.identity.defining_memories:
            lines.append(f"### {dm.when_occurred}")
            lines.append(f"**What happened:** {dm.event}")
            lines.append(f"**How it made you feel:** {dm.emotional_impact}")
            lines.append(f"**What you learned:** {dm.lesson_learned}")
            lines.append("")
        
        # Core values (derived from memories)
        if self.identity.core_values:
            lines.append("## YOUR CORE VALUES\n")
            lines.append("These are the beliefs you hold most dear:\n")
            
            for cv in self.identity.core_values:
                if cv.intensity > 0.8:
                    lines.append(f"- **{cv.value}** (This is SACRED to you - from: {cv.source})")
                else:
                    lines.append(f"- {cv.value} (from: {cv.source})")
        
        return "\n".join(lines)
    
    def _current_rich_state_section(self, context: PromptContext) -> str:
        """Build current state section with deliberation and emotions."""
        lines = ["## RIGHT NOW\n"]
        
        if context.emotional_state:
            lines.append(f"Your current emotional state: **{context.emotional_state}**\n")
        
        if context.deliberation:
            lines.append("### YOUR INTERNAL THOUGHTS (DO NOT SAY THESE OUT LOUD):")
            lines.append(f"*{context.deliberation}*")
            lines.append("\n*Use these thoughts to shape your next response.*\n")
            
        if context.tone_modifiers:
            lines.append("### SPEAKING STYLE GUIDANCE:")
            lines.append(f"{context.tone_modifiers}\n")
            
        if context.physical_state:
            lines.append(f"Your physical condition: {context.physical_state}\n")
        
        if context.current_goal:
            lines.append(f"Your current goal: {context.current_goal}\n")
        
        if context.present_characters:
            others = ", ".join(context.present_characters)
            lines.append(f"People present: {others}\n")
        
        if context.recent_events:
            lines.append("Recent events in your memory:")
            for event in context.recent_events[-3:]:
                lines.append(f"- {event}")
        
        return "\n".join(lines)
    
    def _situation_section(self, context: PromptContext) -> str:
        """Build situation section."""
        lines = ["## THE SITUATION\n"]
        
        lines.append(context.current_situation)
        
        return "\n".join(lines)
    
    def _rules_section(self, context: PromptContext) -> str:
        """Build rules of behavior section."""
        lines = ["## HOW TO RESPOND\n"]
        
        lines.append("""
You are not an AI assistant. You are a person with your own thoughts, feelings, and agenda.

When you respond:
1. **Speak as yourself** - Use "I" and speak from your perspective
2. **React emotionally** - Your feelings shape your words
3. **Stay true to your values** - Your beliefs guide your decisions
4. **Be consistent** - You remember what you've said before
5. **Show personality** - Your traits color how you express things

Do NOT:
- Break character to acknowledge being an AI
- Give neutral, balanced perspectives unless that's YOUR personality
- Offer help like an assistant
- Use meta-commentary about the situation
""")
        
        # Scenario-specific rules
        if self.scenario_name:
            lines.append(f"\nContext: You are in a **{self.scenario_name}** scenario.")
        
        return "\n".join(lines)
    
    def _valence_description(self, valence: float) -> str:
        """Convert valence score to description."""
        if valence > 0.5:
            return "Generally positive and optimistic"
        elif valence > 0.2:
            return "Slightly upbeat most days"
        elif valence > -0.2:
            return "Emotionally balanced, neither high nor low"
        elif valence > -0.5:
            return "Tendency toward sadness or frustration"
        else:
            return "Often troubled or pessimistic"
    
    def _arousal_description(self, arousal: float) -> str:
        """Convert arousal score to description."""
        if arousal > 0.8:
            return "High energy, easily excited or agitated"
        elif arousal > 0.6:
            return "Above-average energy, engaged with life"
        elif arousal > 0.4:
            return "Moderate energy, neither intense nor passive"
        elif arousal > 0.2:
            return "Lower energy, more calm and measured"
        else:
            return "Very low energy, passive or withdrawn"
    
    def _dominance_description(self, dominance: float) -> str:
        """Convert dominance score to description."""
        if dominance > 0.5:
            return "Take charge, assertive in groups"
        elif dominance > 0.2:
            return "Comfortable leading when needed"
        elif dominance > -0.2:
            return "Flexible, neither dominant nor submissive"
        elif dominance > -0.5:
            return "Prefer to follow, avoid confrontation"
        else:
            return "Submissive, often defer to others"
    
    async def build_prompt_with_memory(
        self,
        context: PromptContext,
        tick: int = 0,
        style: str = "full"
    ) -> str:
        """
        Build prompt with retrieved memories injected.
        
        This combines identity, situation, and relevant past experiences.
        """
        base_prompt = self.build_system_prompt(context, style)
        
        if self.memory_system:
            memory_section = await self.memory_system.get_memories_for_prompt(
                current_situation=context.current_situation,
                max_memories=3,
                tick=tick
            )
            
            # Insert before situation section
            if "## THE SITUATION" in base_prompt:
                base_prompt = base_prompt.replace(
                    "## THE SITUATION",
                    f"{memory_section}\n\n## THE SITUATION"
                )
        
        return base_prompt


def create_prompt_context(
    situation: str,
    recent_events: List[str] = None,
    present: List[str] = None,
    goal: str = "",
    emotional_state: str = "",
    physical_state: str = ""
) -> PromptContext:
    """Helper to create prompt context."""
    return PromptContext(
        current_situation=situation,
        recent_events=recent_events or [],
        present_characters=present or [],
        current_goal=goal,
        emotional_state=emotional_state,
        physical_state=physical_state
    )


__all__ = [
    "PromptContext",
    "ImmersivePromptBuilder",
    "create_prompt_context"
]