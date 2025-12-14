"""
Tests for the core validator.
"""

import pytest
from src.validator import Validator, create_validator
from src.rule_engine import RuleEngine
from src.parser import LogParser
from src.models import LogEntry, ValidationStatus


@pytest.fixture
def rules_dict():
    """Sample rules for testing."""
    return {
        "rules": [
            {
                "id": "battery_min",
                "name": "Battery Minimum",
                "field": "battery_level",
                "operator": ">=",
                "threshold": 20,
                "severity": "warning",
                "message": "Battery below 20%"
            },
            {
                "id": "speed_max",
                "name": "Speed Maximum",
                "field": "speed",
                "operator": "<=",
                "threshold": 100,
                "severity": "error",
                "message": "Speed exceeds limit"
            }
        ]
    }


@pytest.fixture
def validator(rules_dict):
    """Create a validator with sample rules."""
    engine = RuleEngine()
    engine.load_rules_from_dict(rules_dict)
    return Validator(engine)


@pytest.fixture
def sample_logs():
    """Sample log entries for testing."""
    return [
        {"timestamp": "2024-01-15T08:00:00Z", "robot_id": "ROBOT_001", "battery_level": 80, "speed": 50},
        {"timestamp": "2024-01-15T08:00:05Z", "robot_id": "ROBOT_001", "battery_level": 15, "speed": 40},
        {"timestamp": "2024-01-15T08:00:10Z", "robot_id": "ROBOT_002", "battery_level": 60, "speed": 120},
        {"timestamp": "2024-01-15T08:00:15Z", "robot_id": "ROBOT_002", "battery_level": 10, "speed": 110},
    ]


class TestValidator:
    """Test the validator class."""

    def test_validate_passing_entry(self, validator):
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 80,
            "speed": 50
        })
        
        result = validator.validate_entry(entry)
        
        assert result.passed
        assert result.status == ValidationStatus.PASS
        assert len(result.violations) == 0

    def test_validate_failing_entry(self, validator):
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 10,
            "speed": 150
        })
        
        result = validator.validate_entry(entry)
        
        assert not result.passed
        assert result.status == ValidationStatus.FAIL
        assert len(result.violations) == 2

    def test_validate_stream(self, validator, sample_logs):
        parser = LogParser()
        entries = parser.parse_entries(sample_logs)
        
        results = list(validator.validate_stream(entries))
        
        assert len(results) == 4
        assert results[0].passed  # 80% battery, 50 speed
        assert not results[1].passed  # 15% battery (violation)
        assert not results[2].passed  # 120 speed (violation)
        assert not results[3].passed  # 10% battery, 110 speed (2 violations)

    def test_counters(self, validator, sample_logs):
        parser = LogParser()
        entries = parser.parse_entries(sample_logs)
        
        list(validator.validate_stream(entries))
        
        assert validator.total_entries == 4
        assert validator.total_violations == 4  # 1 + 1 + 2

    def test_violation_callbacks(self, rules_dict):
        violations_received = []
        
        engine = RuleEngine()
        engine.load_rules_from_dict(rules_dict)
        validator = Validator(
            engine,
            on_violation=lambda v: violations_received.append(v)
        )
        
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 10,
            "speed": 150
        })
        
        validator.validate_entry(entry)
        
        assert len(violations_received) == 2

    def test_robot_summaries(self, validator, sample_logs):
        parser = LogParser()
        entries = parser.parse_entries(sample_logs)
        
        list(validator.validate_stream(entries))
        report = validator.get_report()
        
        assert "ROBOT_001" in report.robot_summaries
        assert "ROBOT_002" in report.robot_summaries
        
        robot1 = report.robot_summaries["ROBOT_001"]
        assert robot1.total_entries == 2
        assert robot1.violations_count == 1
        
        robot2 = report.robot_summaries["ROBOT_002"]
        assert robot2.total_entries == 2
        assert robot2.violations_count == 3


class TestReport:
    """Test report generation."""

    def test_report_generation(self, validator, sample_logs):
        parser = LogParser()
        entries = parser.parse_entries(sample_logs)
        
        list(validator.validate_stream(entries))
        report = validator.get_report(rules_file="test.json", input_file="logs.json")
        
        assert report.total_entries == 4
        assert report.total_violations == 4
        assert report.pass_rate == 25.0  # 1 out of 4 passed
        
        assert "battery_min" in report.violations_by_rule
        assert "speed_max" in report.violations_by_rule

    def test_report_to_dict(self, validator, sample_logs):
        parser = LogParser()
        entries = parser.parse_entries(sample_logs)
        
        list(validator.validate_stream(entries))
        report = validator.get_report()
        report_dict = report.to_dict()
        
        assert "summary" in report_dict
        assert "violations_by_rule" in report_dict
        assert "robots" in report_dict
        assert "violations" in report_dict
        
        assert report_dict["summary"]["total_entries"] == 4
