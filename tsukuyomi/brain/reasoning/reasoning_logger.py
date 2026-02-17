"""
Reasoning Logger - Phase 17: Reasoning Transparency

This module implements structured logging for agent decisions. It produces
human-readable reasoning logs that can be reviewed after simulation.

Core Components:
- ReasoningLogger: Main logging orchestrator
- LogFormatter: Format decisions for different outputs
- DecisionSummary: Condensed decision summary
"""

import json
import logging
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TextIO
from pathlib import Path
from enum import Enum

# Import decision record (with try/except for circular import protection)
try:
    from .decision_record import DecisionRecord, DecisionType
except ImportError:
    from decision_record import DecisionRecord, DecisionType

logger = logging.getLogger(__name__)


class LogFormat(Enum):
    """Output formats for reasoning logs."""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


@dataclass
class LogConfig:
    """Configuration for reasoning logger."""
    output_dir: str = "./simulation_output"
    scenario_name: str = "simulation"
    format: LogFormat = LogFormat.MARKDOWN
    include_reasoning_steps: bool = True
    include_considered_actions: bool = True
    include_context: bool = True
    include_validation: bool = True
    max_entries_per_file: int = 1000
    flush_interval: int = 10  # Flush every N entries


@dataclass
class DecisionSummary:
    """
    Condensed summary of a decision for quick scanning.

    Provides the essential information without full detail.
    """

    agent_name: str
    tick: int
    action: str
    confidence: float
    valid: bool
    personality_drivers: List[str] = field(default_factory=list)

    # One-line summary
    summary: str = ""

    def __str__(self) -> str:
        status = "✓" if self.valid else "✗"
        drivers = ", ".join(self.personality_drivers[:3])  # First 3 only
        return f"[{self.tick:05d}] {self.agent_name}: {self.action} ({self.confidence:.0%}) {status} [{drivers}]"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "tick": self.tick,
            "action": self.action,
            "confidence": self.confidence,
            "valid": self.valid,
            "personality_drivers": self.personality_drivers,
            "summary": self.summary
        }


class LogFormatter:
    """
    Format decision records for different output formats.

    Supports markdown (for human reading), JSON (for programmatic access),
    and plain text (for simple logs).
    """

    @staticmethod
    def format_markdown(record: DecisionRecord, config: LogConfig) -> str:
        """
        Format a decision record as markdown.

        Args:
            record: The decision record to format
            config: Logging configuration

        Returns:
            str: Formatted markdown string
        """
        parts = []

        # Header
        parts.append(f"## {record.agent_name} - Tick {record.tick}\n")

        # Validation status
        status = "✓ VALID" if record.validation_passed else "✗ INVALID"
        parts.append(f"**Status:** {status}\n")

        # Context section
        if config.include_context:
            parts.append("### Context\n")

            # Perception
            if record.context.perception_summary:
                parts.append(f"**Perception:** {record.context.perception_summary}\n")

            # Emotional state
            parts.append(
                f"**Emotional State:** {record.context.emotional_state} "
                f"(valence: {record.context.valence:.1f}, arousal: {record.context.arousal:.1f})\n"
            )

            # Location
            if record.context.location:
                parts.append(f"**Location:** {record.context.location}\n")

            # Memories
            if record.context.relevant_memories:
                parts.append(f"**Relevant Memories:** {len(record.context.relevant_memories)} memories\n")
                for mem in record.context.relevant_memories[:3]:  # First 3
                    parts.append(f"  - {mem}\n")

            # Critical needs
            if record.context.critical_needs:
                parts.append(f"**Critical Needs:** {', '.join(record.context.critical_needs)}\n")

            parts.append("\n")

        # Reasoning section
        if config.include_reasoning_steps and record.reasoning_steps:
            parts.append("### Reasoning\n\n")

            for step in record.reasoning_steps:
                parts.append(f"{step.step_number}. **[{step.step_type.upper()}]** {step.content}\n")

                if step.confidence < 1.0:
                    parts.append(f"   _Confidence: {step.confidence:.0%}_\n")

            parts.append("\n")

        # Considered actions
        if config.include_considered_actions and record.considered_actions:
            parts.append("### Actions Considered\n\n")

            for action in record.considered_actions:
                status = "✓ CHOSEN" if action.accepted else "✗ REJECTED"
                parts.append(f"- **{action.action}** ({status}, score: {action.score:.2f})\n")

                if action.rejection_reason:
                    parts.append(f"  - Reason: {action.rejection_reason}\n")

                if action.risks:
                    parts.append(f"  - Risks: {', '.join(action.risks)}\n")

            parts.append("\n")

        # Decision section
        parts.append("### Decision\n\n")
        parts.append(
            f"**{record.final_action}** (confidence: {record.calibrated_confidence:.0%})\n\n"
        )

        # Personality drivers
        if record.personality_drivers:
            parts.append("_Driven by: " + ", ".join(record.personality_drivers) + "_\n\n")

        # Validation issues
        if config.include_validation and record.validation_violations:
            parts.append("### Validation Issues\n\n")
            for violation in record.validation_violations:
                parts.append(f"- ⚠️ {violation}\n")
            parts.append("\n")

        # Separator
        parts.append("---\n\n")

        return "".join(parts)

    @staticmethod
    def format_json(record: DecisionRecord) -> str:
        """
        Format a decision record as JSON.

        Args:
            record: The decision record to format

        Returns:
            str: JSON string
        """
        return json.dumps(record.to_dict(), indent=2)

    @staticmethod
    def format_text(record: DecisionRecord, config: LogConfig) -> str:
        """
        Format a decision record as plain text.

        Args:
            record: The decision record to format
            config: Logging configuration

        Returns:
            str: Plain text string
        """
        lines = []

        lines.append(f"=== {record.agent_name} @ Tick {record.tick} ===")

        # Quick context
        lines.append(f"State: {record.context.emotional_state}")
        lines.append(f"Location: {record.context.location or 'unknown'}")

        # Reasoning summary
        if record.reasoning_steps:
            lines.append("Reasoning:")
            for step in record.reasoning_steps:
                lines.append(f"  {step.step_number}. [{step.step_type}] {step.content[:80]}")

        # Decision
        lines.append(f"Decision: {record.final_action} ({record.calibrated_confidence:.0%})")

        if record.personality_drivers:
            lines.append(f"Drivers: {', '.join(record.personality_drivers)}")

        lines.append("")

        return "\n".join(lines)


class ReasoningLogger:
    """
    Main logging orchestrator for agent reasoning.

    Manages multiple output files and provides a unified interface
    for logging decisions from multiple agents.

    Output Structure:
        {output_dir}/{scenario_name}_{timestamp}/
        ├── reasoning.md       # Full reasoning logs
        ├── decisions.json     # Machine-readable decision records
        ├── summaries.md       # Quick-scan summaries
        └── stats.md           # Aggregate statistics

    Usage:
        logger = ReasoningLogger(config)
        logger.log_decision(decision_record)
        logger.close()
    """

    def __init__(self, config: Optional[LogConfig] = None):
        """
        Initialize the reasoning logger.

        Args:
            config: Logging configuration (uses defaults if not provided)
        """
        self.config = config or LogConfig()

        # Create output directory
        self.session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.output_path = Path(self.config.output_dir) / f"{self.config.scenario_name}_{self.session_timestamp}"
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize file handles
        self._files: Dict[str, TextIO] = {}

        # Open files based on format
        self._init_files()

        # Counters
        self.entry_count = 0
        self.decisions_by_agent: Dict[str, int] = {}

        # In-memory summaries for stats
        self.summaries: List[DecisionSummary] = []

        logger.info(f"ReasoningLogger initialized: {self.output_path}")

    def _init_files(self) -> None:
        """Initialize output files based on format."""
        # Main reasoning log
        if self.config.format == LogFormat.MARKDOWN:
            self._files["reasoning"] = open(self.output_path / "reasoning.md", "w", encoding="utf-8")
            self._write_header("reasoning", f"# Reasoning Log - {self.config.scenario_name}\n\n")

        # JSON output (always available)
        self._files["json"] = open(self.output_path / "decisions.json", "w", encoding="utf-8")
        self._files["json"].write("[\n")

        # Summaries
        self._files["summaries"] = open(self.output_path / "summaries.md", "w", encoding="utf-8")
        self._write_header("summaries", f"# Decision Summaries - {self.config.scenario_name}\n\n")

    def _write_header(self, file_key: str, content: str) -> None:
        """Write header content to a file."""
        if file_key in self._files:
            self._files[file_key].write(content)

    def log_decision(self, record: DecisionRecord) -> None:
        """
        Log a decision record.

        This is the main entry point for logging decisions. The record
        is written to all configured output files.

        Args:
            record: The decision record to log
        """
        # Update counters
        self.entry_count += 1
        agent_name = record.agent_name or "unknown"
        self.decisions_by_agent[agent_name] = self.decisions_by_agent.get(agent_name, 0) + 1

        # Write to main log
        if "reasoning" in self._files:
            formatted = LogFormatter.format_markdown(record, self.config)
            self._files["reasoning"].write(formatted)

        # Write to JSON
        if "json" in self._files:
            if self.entry_count > 1:
                self._files["json"].write(",\n")
            self._files["json"].write(LogFormatter.format_json(record))

        # Write summary
        if "summaries" in self._files:
            summary = self._create_summary(record)
            self.summaries.append(summary)
            self._files["summaries"].write(f"{summary}\n\n")

        # Flush periodically
        if self.entry_count % self.config.flush_interval == 0:
            self._flush()

        logger.debug(f"Logged decision: {record.agent_name} @ tick {record.tick}")

    def _create_summary(self, record: DecisionRecord) -> DecisionSummary:
        """Create a summary from a decision record."""
        summary = DecisionSummary(
            agent_name=record.agent_name,
            tick=record.tick,
            action=record.final_action,
            confidence=record.calibrated_confidence,
            valid=record.validation_passed,
            personality_drivers=record.personality_drivers
        )

        # Generate one-line summary
        parts = [f"{record.agent_name} decided to {record.final_action}"]

        if record.personality_drivers:
            parts.append(f"driven by {', '.join(record.personality_drivers[:2])}")

        if not record.validation_passed:
            parts.append("(has validation issues)")

        summary.summary = " ".join(parts)

        return summary

    def log_summary(self, summary: str) -> None:
        """
        Log a free-text summary comment.

        Useful for adding narrative context or notes between decisions.

        Args:
            summary: The summary text to log
        """
        if "reasoning" in self._files:
            self._files["reasoning"].write(f"\n### Summary\n\n{summary}\n\n---\n\n")

        if "summaries" in self._files:
            self._files["summaries"].write(f"**Note:** {summary}\n\n")

    def log_tick_summary(self, tick: int, events: List[str]) -> None:
        """
        Log a summary of events for a tick.

        Args:
            tick: The tick number
            events: List of events that occurred
        """
        if "reasoning" in self._files:
            self._files["reasoning"].write(
                f"\n## Tick {tick} Summary\n\n" +
                "\n".join(f"- {e}" for e in events) +
                "\n\n---\n\n"
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about logged decisions.

        Returns:
            Dict with statistics
        """
        stats = {
            "total_decisions": self.entry_count,
            "decisions_by_agent": dict(self.decisions_by_agent),
            "output_path": str(self.output_path),
            "format": self.config.format.value
        }

        # Calculate averages
        if self.summaries:
            avg_confidence = sum(s.confidence for s in self.summaries) / len(self.summaries)
            valid_rate = sum(1 for s in self.summaries if s.valid) / len(self.summaries)

            stats["average_confidence"] = avg_confidence
            stats["validity_rate"] = valid_rate

            # Most common actions
            action_counts: Dict[str, int] = {}
            for s in self.summaries:
                action_counts[s.action] = action_counts.get(s.action, 0) + 1

            stats["action_distribution"] = dict(sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])

        return stats

    def write_final_stats(self) -> None:
        """Write final statistics to a stats file."""
        stats = self.get_stats()

        stats_path = self.output_path / "stats.md"
        with open(stats_path, "w", encoding="utf-8") as f:
            f.write(f"# Simulation Statistics - {self.config.scenario_name}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

            f.write("## Overview\n\n")
            f.write(f"- Total Decisions: {stats['total_decisions']}\n")
            f.write(f"- Output Path: {stats['output_path']}\n\n")

            if "average_confidence" in stats:
                f.write("## Decision Metrics\n\n")
                f.write(f"- Average Confidence: {stats['average_confidence']:.1%}\n")
                f.write(f"- Validity Rate: {stats['validity_rate']:.1%}\n\n")

            f.write("## Decisions by Agent\n\n")
            for agent, count in stats["decisions_by_agent"].items():
                f.write(f"- {agent}: {count} decisions\n")

            if "action_distribution" in stats:
                f.write("\n## Action Distribution\n\n")
                for action, count in stats["action_distribution"].items():
                    f.write(f"- {action}: {count}\n")

        logger.info(f"Final stats written to {stats_path}")

    def _flush(self) -> None:
        """Flush all file buffers."""
        for f in self._files.values():
            f.flush()

    def close(self) -> None:
        """Close all files and write final stats."""
        # Close JSON array
        if "json" in self._files:
            self._files["json"].write("\n]\n")

        # Write final stats
        self.write_final_stats()

        # Close all files
        for f in self._files.values():
            f.close()

        self._files.clear()

        logger.info(f"ReasoningLogger closed: {self.entry_count} decisions logged")

    def __enter__(self) -> 'ReasoningLogger':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class QuickLogger:
    """
    Simplified logger for quick prototyping.

    Provides a simpler interface for basic logging without full
    configuration. Outputs to console and a single file.
    """

    def __init__(self, output_file: str = "reasoning.log"):
        """
        Initialize quick logger.

        Args:
            output_file: Path to output file
        """
        self.output_file = output_file
        self.file = open(output_file, "w", encoding="utf-8")

    def log(self, agent_name: str, tick: int, action: str, reasoning: str, confidence: float = 1.0) -> None:
        """
        Log a simple decision.

        Args:
            agent_name: Name of the agent
            tick: Current tick
            action: Action taken
            reasoning: Reasoning text
            confidence: Confidence level
        """
        entry = f"[{tick:05d}] {agent_name}: {action} ({confidence:.0%})\n{reasoning}\n\n"
        self.file.write(entry)
        self.file.flush()
        print(entry.strip())

    def close(self) -> None:
        """Close the logger."""
        self.file.close()

    def __enter__(self) -> 'QuickLogger':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()