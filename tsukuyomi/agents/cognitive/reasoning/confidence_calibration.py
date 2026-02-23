"""
Confidence Calibration - Phase 17: Reasoning Transparency

This module implements historical accuracy tracking for confidence scores.
LLM self-reported confidence is often miscalibrated (overconfident on uncertain
decisions, underconfident on clear ones). This system combines LLM self-assessment
with historical accuracy tracking to produce calibrated confidence scores.

Core Components:
- ConfidenceCalibration: Track and calibrate confidence scores
- CalibrationReport: Summary of calibration metrics
- ConfidenceBin: Binned confidence tracking
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import math

logger = logging.getLogger(__name__)


class ConfidenceBin(Enum):
    """Bins for confidence levels."""
    VERY_HIGH = "very_high"    # 0.9 - 1.0
    HIGH = "high"              # 0.7 - 0.9
    MEDIUM = "medium"          # 0.5 - 0.7
    LOW = "low"                # 0.3 - 0.5
    VERY_LOW = "very_low"      # 0.0 - 0.3


@dataclass
class BinStatistics:
    """Statistics for a single confidence bin."""
    reported_confidence: float  # Expected confidence for this bin
    outcomes: List[bool] = field(default_factory=list)  # True = correct, False = incorrect
    total_decisions: int = 0
    correct_decisions: int = 0

    @property
    def actual_accuracy(self) -> float:
        """Calculate actual accuracy for this bin."""
        if self.total_decisions == 0:
            return self.reported_confidence  # Default to expected
        return self.correct_decisions / self.total_decisions

    @property
    def calibration_gap(self) -> float:
        """Calculate gap between reported and actual confidence."""
        return abs(self.reported_confidence - self.actual_accuracy)

    @property
    def is_overconfident(self) -> bool:
        """Check if this bin is overconfident (reported > actual)."""
        return self.reported_confidence > self.actual_accuracy

    @property
    def is_underconfident(self) -> bool:
        """Check if this bin is underconfident (reported < actual)."""
        return self.reported_confidence < self.actual_accuracy

    def add_outcome(self, was_correct: bool) -> None:
        """Add an outcome to this bin."""
        self.outcomes.append(was_correct)
        self.total_decisions += 1
        if was_correct:
            self.correct_decisions += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "reported_confidence": self.reported_confidence,
            "total_decisions": self.total_decisions,
            "correct_decisions": self.correct_decisions,
            "actual_accuracy": self.actual_accuracy,
            "calibration_gap": self.calibration_gap,
            "is_overconfident": self.is_overconfident,
            "is_underconfident": self.is_underconfident
        }


@dataclass
class CalibrationReport:
    """
    Summary of calibration metrics for debugging and monitoring.

    Provides insights into how well the agent's confidence matches
    actual decision accuracy.
    """

    agent_id: str
    total_decisions: int
    overall_accuracy: float
    bin_statistics: Dict[str, BinStatistics]

    # Aggregate metrics
    average_calibration_gap: float
    worst_bin_gap: Tuple[str, float]  # (bin_name, gap)
    best_bin_gap: Tuple[str, float]   # (bin_name, gap)

    # Trends
    overconfidence_trend: float  # Positive = getting more overconfident
    recent_accuracy_trend: float  # Positive = improving

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        lines = [
            f"Calibration Report for {self.agent_id}",
            f"=" * 40,
            f"Total Decisions: {self.total_decisions}",
            f"Overall Accuracy: {self.overall_accuracy:.1%}",
            f"Average Calibration Gap: {self.average_calibration_gap:.2f}",
            "",
            "Bin Statistics:"
        ]

        for bin_name, stats in self.bin_statistics.items():
            status = "overconfident" if stats.is_overconfident else (
                "underconfident" if stats.is_underconfident else "calibrated"
            )
            lines.append(
                f"  {bin_name}: reported={stats.reported_confidence:.0%}, "
                f"actual={stats.actual_accuracy:.0%}, "
                f"gap={stats.calibration_gap:.2f} ({status})"
            )

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "total_decisions": self.total_decisions,
            "overall_accuracy": self.overall_accuracy,
            "bin_statistics": {k: v.to_dict() for k, v in self.bin_statistics.items()},
            "average_calibration_gap": self.average_calibration_gap,
            "worst_bin_gap": self.worst_bin_gap,
            "best_bin_gap": self.best_bin_gap,
            "overconfidence_trend": self.overconfidence_trend,
            "recent_accuracy_trend": self.recent_accuracy_trend
        }


class ConfidenceCalibration:
    """
    Track and calibrate confidence scores based on historical accuracy.

    This system addresses the common problem of LLM overconfidence by
    learning from past decisions and adjusting confidence scores to
    better reflect actual accuracy.

    Usage:
        calibrator = ConfidenceCalibration(agent_id="agent_1")

        # Record a decision outcome
        calibrator.record_outcome(confidence=0.8, was_correct=True)

        # Calibrate a new confidence score
        calibrated = calibrator.calibrate_confidence(raw_confidence=0.9)

        # Get calibration report for monitoring
        report = calibrator.get_calibration_report()
    """

    # Expected confidence for each bin
    BIN_EXPECTED_CONFIDENCE = {
        ConfidenceBin.VERY_HIGH: 0.95,
        ConfidenceBin.HIGH: 0.80,
        ConfidenceBin.MEDIUM: 0.60,
        ConfidenceBin.LOW: 0.40,
        ConfidenceBin.VERY_LOW: 0.20
    }

    # Minimum samples needed before calibration is applied
    MIN_SAMPLES_FOR_CALIBRATION = 5

    # Maximum history to keep (for trend calculation)
    MAX_HISTORY_SIZE = 100

    def __init__(self, agent_id: str):
        """
        Initialize calibration tracker.

        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id

        # Initialize bins with expected confidence values
        self.bins: Dict[ConfidenceBin, BinStatistics] = {
            ConfidenceBin.VERY_HIGH: BinStatistics(reported_confidence=0.95),
            ConfidenceBin.HIGH: BinStatistics(reported_confidence=0.80),
            ConfidenceBin.MEDIUM: BinStatistics(reported_confidence=0.60),
            ConfidenceBin.LOW: BinStatistics(reported_confidence=0.40),
            ConfidenceBin.VERY_LOW: BinStatistics(reported_confidence=0.20)
        }

        # Full history for trend calculation
        self.confidence_history: List[Tuple[float, bool]] = []

        # EMA tracking for smoothed metrics
        self.ema_accuracy: float = 0.5
        self.ema_alpha: float = 0.1  # Weight for new samples in EMA

        logger.info(f"ConfidenceCalibration initialized for {agent_id}")

    def record_outcome(self, confidence: float, was_correct: bool) -> None:
        """
        Record whether a decision at given confidence was correct.

        This is the primary feedback mechanism - after a decision's outcome
        is known, record it to improve future calibration.

        Args:
            confidence: The confidence score that was reported
            was_correct: Whether the decision was correct
        """
        # Add to history
        self.confidence_history.append((confidence, was_correct))

        # Trim history if needed
        if len(self.confidence_history) > self.MAX_HISTORY_SIZE:
            self.confidence_history.pop(0)

        # Add to appropriate bin
        bin_type = self._confidence_to_bin(confidence)
        self.bins[bin_type].add_outcome(was_correct)

        # Update EMA accuracy
        outcome_value = 1.0 if was_correct else 0.0
        self.ema_accuracy = (
            self.ema_alpha * outcome_value +
            (1 - self.ema_alpha) * self.ema_accuracy
        )

        logger.debug(
            f"Recorded outcome for {self.agent_id}: "
            f"confidence={confidence:.2f}, correct={was_correct}, "
            f"bin={bin_type.value}"
        )

    def calibrate_confidence(self, raw_confidence: float) -> float:
        """
        Adjust raw confidence based on historical calibration.

        If the agent is historically overconfident at this confidence level,
        the score is adjusted down. If underconfident, adjusted up.

        The calibration uses a damping factor to avoid extreme adjustments.

        Args:
            raw_confidence: The raw self-reported confidence (0.0 to 1.0)

        Returns:
            float: Calibrated confidence score (0.0 to 1.0)
        """
        bin_type = self._confidence_to_bin(raw_confidence)
        bin_stats = self.bins[bin_type]

        # If not enough data, return raw confidence
        if bin_stats.total_decisions < self.MIN_SAMPLES_FOR_CALIBRATION:
            return raw_confidence

        # Calculate calibration factor
        # If confidence 0.8 but accuracy is 0.6, calibrate down
        actual = bin_stats.actual_accuracy
        expected = bin_stats.reported_confidence

        if expected > 0:
            calibration_factor = actual / expected
        else:
            calibration_factor = 1.0

        # Apply calibration with damping (70% raw + 30% calibration adjustment)
        # This prevents extreme swings while still learning from history
        calibrated = raw_confidence * (0.7 + 0.3 * calibration_factor)

        # Clamp to valid range
        calibrated = max(0.1, min(1.0, calibrated))

        logger.debug(
            f"Calibrated confidence: raw={raw_confidence:.2f}, "
            f"calibrated={calibrated:.2f}, factor={calibration_factor:.2f}"
        )

        return calibrated

    def get_current_accuracy(self) -> float:
        """
        Get the current smoothed accuracy estimate.

        Returns:
            float: EMA accuracy (0.0 to 1.0)
        """
        return self.ema_accuracy

    def get_bin_for_confidence(self, confidence: float) -> str:
        """
        Get the bin name for a confidence score.

        Args:
            confidence: Confidence score

        Returns:
            str: Bin name
        """
        return self._confidence_to_bin(confidence).value

    def get_calibration_report(self) -> CalibrationReport:
        """
        Get comprehensive calibration metrics for debugging.

        Returns:
            CalibrationReport with all calibration statistics
        """
        # Calculate overall accuracy
        total_decisions = sum(b.total_decisions for b in self.bins.values())
        total_correct = sum(b.correct_decisions for b in self.bins.values())

        overall_accuracy = total_correct / total_decisions if total_decisions > 0 else 0.5

        # Calculate average calibration gap
        gaps = []
        for bin_stats in self.bins.values():
            if bin_stats.total_decisions >= self.MIN_SAMPLES_FOR_CALIBRATION:
                gaps.append(bin_stats.calibration_gap)

        average_gap = sum(gaps) / len(gaps) if gaps else 0.0

        # Find worst and best bins
        worst_bin = ("", 0.0)
        best_bin = ("", 1.0)

        for bin_name, bin_stats in self.bins.items():
            if bin_stats.total_decisions >= self.MIN_SAMPLES_FOR_CALIBRATION:
                if bin_stats.calibration_gap > worst_bin[1]:
                    worst_bin = (bin_name.value, bin_stats.calibration_gap)
                if bin_stats.calibration_gap < best_bin[1]:
                    best_bin = (bin_name.value, bin_stats.calibration_gap)

        # Calculate trends
        overconfidence_trend = self._calculate_overconfidence_trend()
        accuracy_trend = self._calculate_accuracy_trend()

        return CalibrationReport(
            agent_id=self.agent_id,
            total_decisions=total_decisions,
            overall_accuracy=overall_accuracy,
            bin_statistics={b.value: s for b, s in self.bins.items()},
            average_calibration_gap=average_gap,
            worst_bin_gap=worst_bin,
            best_bin_gap=best_bin,
            overconfidence_trend=overconfidence_trend,
            recent_accuracy_trend=accuracy_trend
        )

    def _confidence_to_bin(self, confidence: float) -> ConfidenceBin:
        """
        Map confidence score to appropriate bin.

        Args:
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            ConfidenceBin enum value
        """
        if confidence >= 0.9:
            return ConfidenceBin.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceBin.HIGH
        elif confidence >= 0.5:
            return ConfidenceBin.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceBin.LOW
        else:
            return ConfidenceBin.VERY_LOW

    def _calculate_overconfidence_trend(self) -> float:
        """
        Calculate trend in overconfidence.

        Positive = getting more overconfident over time
        Negative = getting better calibrated over time

        Returns:
            float: Trend value (-1.0 to 1.0)
        """
        if len(self.confidence_history) < 20:
            return 0.0

        # Split history into first half and second half
        mid = len(self.confidence_history) // 2
        first_half = self.confidence_history[:mid]
        second_half = self.confidence_history[mid:]

        # Calculate average confidence vs accuracy for each half
        first_conf = sum(c for c, _ in first_half) / len(first_half)
        first_acc = sum(1 for _, correct in first_half if correct) / len(first_half)
        first_gap = first_conf - first_acc

        second_conf = sum(c for c, _ in second_half) / len(second_half)
        second_acc = sum(1 for _, correct in second_half if correct) / len(second_half)
        second_gap = second_conf - second_acc

        # Trend is the change in gap
        return second_gap - first_gap

    def _calculate_accuracy_trend(self) -> float:
        """
        Calculate trend in accuracy.

        Positive = accuracy improving over time
        Negative = accuracy declining over time

        Returns:
            float: Trend value (-1.0 to 1.0)
        """
        if len(self.confidence_history) < 20:
            return 0.0

        # Split history into quarters
        q = len(self.confidence_history) // 4
        quarters = [
            self.confidence_history[:q],
            self.confidence_history[q:2*q],
            self.confidence_history[2*q:3*q],
            self.confidence_history[3*q:]
        ]

        # Calculate accuracy for each quarter
        accuracies = []
        for quarter in quarters:
            if quarter:
                acc = sum(1 for _, correct in quarter if correct) / len(quarter)
                accuracies.append(acc)

        # Linear regression slope (simplified)
        if len(accuracies) < 2:
            return 0.0

        x_mean = sum(range(len(accuracies))) / len(accuracies)
        y_mean = sum(accuracies) / len(accuracies)

        numerator = sum((i - x_mean) * (a - y_mean) for i, a in enumerate(accuracies))
        denominator = sum((i - x_mean) ** 2 for i in range(len(accuracies)))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def reset(self) -> None:
        """Reset all calibration data."""
        self.bins = {
            ConfidenceBin.VERY_HIGH: BinStatistics(reported_confidence=0.95),
            ConfidenceBin.HIGH: BinStatistics(reported_confidence=0.80),
            ConfidenceBin.MEDIUM: BinStatistics(reported_confidence=0.60),
            ConfidenceBin.LOW: BinStatistics(reported_confidence=0.40),
            ConfidenceBin.VERY_LOW: BinStatistics(reported_confidence=0.20)
        }
        self.confidence_history = []
        self.ema_accuracy = 0.5

        logger.info(f"Calibration data reset for {self.agent_id}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "bins": {k.value: v.to_dict() for k, v in self.bins.items()},
            "ema_accuracy": self.ema_accuracy,
            "history_size": len(self.confidence_history)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConfidenceCalibration':
        """Create from dictionary."""
        calibrator = cls(agent_id=data["agent_id"])

        # Restore bins
        for bin_name, bin_data in data.get("bins", {}).items():
            bin_type = ConfidenceBin(bin_name)
            stats = calibrator.bins[bin_type]
            stats.total_decisions = bin_data.get("total_decisions", 0)
            stats.correct_decisions = bin_data.get("correct_decisions", 0)
            stats.outcomes = [True] * stats.correct_decisions + [False] * (stats.total_decisions - stats.correct_decisions)

        calibrator.ema_accuracy = data.get("ema_accuracy", 0.5)

        return calibrator