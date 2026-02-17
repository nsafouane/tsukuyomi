"""
Tsukuyomi Brain - Reasoning Module

This module implements Phase 17: Reasoning Transparency for Tsukuyomi V2.
It provides structured logging and validation of agent reasoning processes.

Core Components:
- DecisionRecord: Complete record of an agent's decision process
- ConfidenceCalibration: Historical accuracy tracking for confidence scores
- ReasoningValidator: Consistency checks for traits, beliefs, needs
- ReasoningLogger: Structured logging for decisions

Usage:
    from tsukuyomi.brain.reasoning import DecisionRecord, ReasoningLogger

    # Create a decision record
    record = DecisionRecord(agent_name="Arthur", tick=100)
    record.add_reasoning_step("perception", "I see Davis approaching")
    record.add_reasoning_step("emotion", "I feel frustrated")
    record.set_final_decision("SPEAK", {"message": "What do you want?"}, 0.7)

    # Log it
    with ReasoningLogger() as logger:
        logger.log_decision(record)
"""

from .decision_record import (
    DecisionRecord,
    DecisionContext,
    DecisionType,
    ReasoningStep,
    ConsideredAction
)

from .confidence_calibration import (
    ConfidenceCalibration,
    ConfidenceBin,
    BinStatistics,
    CalibrationReport
)

from .reasoning_validator import (
    ReasoningValidator,
    ReasoningViolation,
    ValidationResult,
    ViolationType,
    ViolationSeverity,
    TraitChecker,
    BeliefChecker,
    NeedsChecker,
    PersonalitySnapshot,
    BeliefSnapshot,
    NeedsSnapshot
)

from .reasoning_logger import (
    ReasoningLogger,
    LogFormatter,
    LogConfig,
    LogFormat,
    DecisionSummary,
    QuickLogger
)

__all__ = [
    # Decision Record
    "DecisionRecord",
    "DecisionContext",
    "DecisionType",
    "ReasoningStep",
    "ConsideredAction",

    # Confidence Calibration
    "ConfidenceCalibration",
    "ConfidenceBin",
    "BinStatistics",
    "CalibrationReport",

    # Reasoning Validator
    "ReasoningValidator",
    "ReasoningViolation",
    "ValidationResult",
    "ViolationType",
    "ViolationSeverity",
    "TraitChecker",
    "BeliefChecker",
    "NeedsChecker",
    "PersonalitySnapshot",
    "BeliefSnapshot",
    "NeedsSnapshot",

    # Reasoning Logger
    "ReasoningLogger",
    "LogFormatter",
    "LogConfig",
    "LogFormat",
    "DecisionSummary",
    "QuickLogger"
]

__version__ = "1.0.0"