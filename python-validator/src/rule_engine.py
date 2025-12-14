"""
Rule engine for loading and evaluating validation rules.
Supports extensible operators without code changes.
"""

import json
import re
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

from .models import Rule, LogEntry, Violation, Severity


class RuleEngine:
    """
    Engine for loading and evaluating validation rules.
    Supports custom operators for extensibility.
    """

    def __init__(self):
        self.rules: List[Rule] = []
        self._operators: Dict[str, Callable[[Any, Any], bool]] = self._default_operators()

    def _default_operators(self) -> Dict[str, Callable[[Any, Any], bool]]:
        """Define the default set of operators."""
        return {
            ">=": lambda a, b: a is not None and a >= b,
            ">": lambda a, b: a is not None and a > b,
            "<=": lambda a, b: a is not None and a <= b,
            "<": lambda a, b: a is not None and a < b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
            "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
            "regex": lambda a, b: bool(re.match(b, str(a))) if a is not None else False,
            "exists": lambda a, b: (a is not None) == b,
            "contains": lambda a, b: b in str(a) if a is not None else False,
            "starts_with": lambda a, b: str(a).startswith(b) if a is not None else False,
            "ends_with": lambda a, b: str(a).endswith(b) if a is not None else False,
        }

    def register_operator(self, name: str, func: Callable[[Any, Any], bool]) -> None:
        """Register a custom operator."""
        self._operators[name] = func

    def load_rules(self, file_path: str) -> None:
        """Load rules from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rules_data = data.get("rules", [])
        self.rules = [Rule.from_dict(r) for r in rules_data]

    def load_rules_from_dict(self, data: Dict) -> None:
        """Load rules from a dictionary."""
        rules_data = data.get("rules", [])
        self.rules = [Rule.from_dict(r) for r in rules_data]

    def get_field_value(self, entry: LogEntry, field: str) -> Any:
        """
        Get a field value from a log entry.
        Supports nested fields with dot notation (e.g., "location.x").
        """
        data = entry.raw_data
        parts = field.split(".")
        
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return None
        
        return data

    def evaluate_condition(self, entry: LogEntry, field: str, operator: str, value: Any) -> bool:
        """Evaluate a single condition against a log entry."""
        actual_value = self.get_field_value(entry, field)
        
        if operator not in self._operators:
            raise ValueError(f"Unknown operator: {operator}")
        
        return self._operators[operator](actual_value, value)

    def evaluate_rule(self, rule: Rule, entry: LogEntry) -> Optional[Violation]:
        """
        Evaluate a rule against a log entry.
        Returns a Violation if the rule is violated, None otherwise.
        """
        try:
            if rule.type == "conditional":
                return self._evaluate_conditional_rule(rule, entry)
            else:
                return self._evaluate_simple_rule(rule, entry)
        except Exception as e:
            # Log error but don't crash on evaluation errors
            return None

    def _evaluate_simple_rule(self, rule: Rule, entry: LogEntry) -> Optional[Violation]:
        """Evaluate a simple comparison rule."""
        passed = self.evaluate_condition(entry, rule.field, rule.operator, rule.threshold)
        
        if not passed:
            actual_value = self.get_field_value(entry, rule.field)
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=rule.message,
                timestamp=entry.timestamp,
                robot_id=entry.robot_id,
                field=rule.field,
                actual_value=actual_value,
                expected=f"{rule.operator} {rule.threshold}",
                log_index=entry.index
            )
        
        return None

    def _evaluate_conditional_rule(self, rule: Rule, entry: LogEntry) -> Optional[Violation]:
        """
        Evaluate a conditional rule (if condition then check).
        Only validates the 'then' clause if 'condition' is true.
        """
        if not rule.condition or not rule.then:
            return None

        # Check if condition applies
        condition_met = self.evaluate_condition(
            entry,
            rule.condition["field"],
            rule.condition["operator"],
            rule.condition["value"]
        )

        if not condition_met:
            # Condition not met, rule doesn't apply
            return None

        # Condition met, check the 'then' clause
        then_passed = self.evaluate_condition(
            entry,
            rule.then["field"],
            rule.then["operator"],
            rule.then["value"]
        )

        if not then_passed:
            actual_value = self.get_field_value(entry, rule.then["field"])
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=rule.message,
                timestamp=entry.timestamp,
                robot_id=entry.robot_id,
                field=rule.then["field"],
                actual_value=actual_value,
                expected=f"{rule.then['operator']} {rule.then['value']} (when {rule.condition['field']} {rule.condition['operator']} {rule.condition['value']})",
                log_index=entry.index
            )

        return None

    def validate_entry(self, entry: LogEntry) -> List[Violation]:
        """Validate a log entry against all rules."""
        violations = []
        
        for rule in self.rules:
            violation = self.evaluate_rule(rule, entry)
            if violation:
                violations.append(violation)
        
        return violations
