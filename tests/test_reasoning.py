"""
Tests for Tsukuyomi Brain Reasoning Module (Phase 17)

Run with: python -m pytest tests/test_reasoning.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.reasoning import (
    DecisionRecord, DecisionContext, DecisionType, ReasoningStep, ConsideredAction,
    ConfidenceCalibration, ReasoningValidator, ValidationResult,
    PersonalitySnapshot, BeliefSnapshot, NeedsSnapshot, ReasoningLogger, LogConfig, LogFormat
)


class TestDecisionRecord:
    def test_create(self):
        record = DecisionRecord(agent_name="TestAgent", tick=100)
        assert record.agent_name == "TestAgent"
        assert record.tick == 100

    def test_add_reasoning_step(self):
        record = DecisionRecord(agent_name="Test", tick=1)
        record.add_reasoning_step("perception", "Test content")
        assert len(record.reasoning_steps) == 1

    def test_set_final_decision(self):
        record = DecisionRecord(agent_name="Test", tick=1)
        record.set_final_decision("TAKE", {"target": "apple"}, 0.85)
        assert record.final_action == "TAKE"

    def test_serialization(self):
        record = DecisionRecord(agent_name="Test", tick=1)
        record.set_final_decision("IDLE", {}, 0.5)
        data = record.to_dict()
        assert isinstance(data, dict)


class TestConfidenceCalibration:
    def test_create(self):
        cal = ConfidenceCalibration(agent_id="TestAgent")
        assert cal is not None

    def test_record_outcome(self):
        cal = ConfidenceCalibration(agent_id="TestAgent")
        cal.record_outcome(0.9, True)
        assert cal is not None

    def test_calibration_report(self):
        cal = ConfidenceCalibration(agent_id="TestAgent")
        for _ in range(10):
            cal.record_outcome(0.8, True)
        report = cal.get_calibration_report()
        assert report.total_decisions == 10


class TestReasoningValidator:
    def test_create(self):
        validator = ReasoningValidator()
        assert validator is not None

    def test_validate_decision_record(self):
        validator = ReasoningValidator()
        record = DecisionRecord(agent_name="Test", tick=1)
        record.set_final_decision("IDLE", {}, 0.5)
        result = validator.validate_decision_record(record)
        assert result is not None


class TestReasoningLogger:
    def test_create_logger(self):
        config = LogConfig(format=LogFormat.JSON)
        logger = ReasoningLogger(config=config)
        assert logger is not None
        logger.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
