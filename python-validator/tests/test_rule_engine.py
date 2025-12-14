"""
Tests for the rule engine.
"""

import pytest
from src.rule_engine import RuleEngine
from src.models import Rule, LogEntry, Severity


@pytest.fixture
def engine():
    """Create a fresh rule engine for each test."""
    return RuleEngine()


@pytest.fixture
def sample_entry():
    """Create a sample log entry."""
    return LogEntry.from_dict({
        "timestamp": "2024-01-15T08:00:00Z",
        "robot_id": "ROBOT_001",
        "battery_level": 45,
        "speed": 50,
        "movement_state": "moving",
        "location": {"x": 100, "y": 200}
    })


class TestOperators:
    """Test operator evaluation."""

    def test_greater_than_or_equal(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "battery_level", ">=", 40)
        assert engine.evaluate_condition(sample_entry, "battery_level", ">=", 45)
        assert not engine.evaluate_condition(sample_entry, "battery_level", ">=", 50)

    def test_less_than_or_equal(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "speed", "<=", 60)
        assert engine.evaluate_condition(sample_entry, "speed", "<=", 50)
        assert not engine.evaluate_condition(sample_entry, "speed", "<=", 40)

    def test_equals(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "robot_id", "==", "ROBOT_001")
        assert not engine.evaluate_condition(sample_entry, "robot_id", "==", "ROBOT_002")

    def test_not_equals(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "robot_id", "!=", "ROBOT_002")
        assert not engine.evaluate_condition(sample_entry, "robot_id", "!=", "ROBOT_001")

    def test_in_list(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "movement_state", "in", ["moving", "stopped"])
        assert not engine.evaluate_condition(sample_entry, "movement_state", "in", ["idle", "charging"])

    def test_not_in_list(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "movement_state", "not_in", ["idle", "error"])
        assert not engine.evaluate_condition(sample_entry, "movement_state", "not_in", ["moving", "idle"])

    def test_regex(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "robot_id", "regex", r"^ROBOT_\d+$")
        assert not engine.evaluate_condition(sample_entry, "robot_id", "regex", r"^BOT_\d+$")

    def test_exists(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "battery_level", "exists", True)
        assert engine.evaluate_condition(sample_entry, "nonexistent_field", "exists", False)

    def test_nested_field(self, engine, sample_entry):
        assert engine.evaluate_condition(sample_entry, "location.x", "==", 100)
        assert engine.evaluate_condition(sample_entry, "location.y", ">=", 150)


class TestRuleEvaluation:
    """Test full rule evaluation."""

    def test_simple_rule_pass(self, engine):
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            field="battery_level",
            operator=">=",
            threshold=20,
            severity=Severity.WARNING,
            message="Battery low"
        )
        engine.rules = [rule]
        
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 50
        })
        
        violations = engine.validate_entry(entry)
        assert len(violations) == 0

    def test_simple_rule_fail(self, engine):
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            field="battery_level",
            operator=">=",
            threshold=20,
            severity=Severity.WARNING,
            message="Battery low"
        )
        engine.rules = [rule]
        
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 15
        })
        
        violations = engine.validate_entry(entry)
        assert len(violations) == 1
        assert violations[0].rule_id == "test_rule"
        assert violations[0].actual_value == 15

    def test_conditional_rule_pass(self, engine):
        rule = Rule(
            id="conditional_test",
            name="No movement when battery critical",
            field="",
            operator="",
            threshold=None,
            severity=Severity.CRITICAL,
            message="Moving with critical battery",
            type="conditional",
            condition={"field": "battery_level", "operator": "<", "value": 10},
            then={"field": "movement_state", "operator": "in", "value": ["idle", "stopped"]}
        )
        engine.rules = [rule]
        
        # Battery OK, moving - should pass
        entry1 = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 50,
            "movement_state": "moving"
        })
        assert len(engine.validate_entry(entry1)) == 0
        
        # Battery critical, stopped - should pass
        entry2 = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 5,
            "movement_state": "stopped"
        })
        assert len(engine.validate_entry(entry2)) == 0

    def test_conditional_rule_fail(self, engine):
        rule = Rule(
            id="conditional_test",
            name="No movement when battery critical",
            field="",
            operator="",
            threshold=None,
            severity=Severity.CRITICAL,
            message="Moving with critical battery",
            type="conditional",
            condition={"field": "battery_level", "operator": "<", "value": 10},
            then={"field": "movement_state", "operator": "in", "value": ["idle", "stopped"]}
        )
        engine.rules = [rule]
        
        # Battery critical, moving - should fail
        entry = LogEntry.from_dict({
            "timestamp": "2024-01-15T08:00:00Z",
            "robot_id": "ROBOT_001",
            "battery_level": 5,
            "movement_state": "moving"
        })
        
        violations = engine.validate_entry(entry)
        assert len(violations) == 1
        assert violations[0].rule_id == "conditional_test"


class TestCustomOperators:
    """Test custom operator registration."""

    def test_register_custom_operator(self, engine, sample_entry):
        # Register a custom "divisible_by" operator
        engine.register_operator(
            "divisible_by",
            lambda a, b: a is not None and a % b == 0
        )
        
        assert engine.evaluate_condition(sample_entry, "battery_level", "divisible_by", 5)
        assert not engine.evaluate_condition(sample_entry, "battery_level", "divisible_by", 7)
