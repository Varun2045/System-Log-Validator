"""
Core validation orchestrator.
Coordinates parser, rule engine, and collects results.
"""

from typing import Iterator, List, Dict, Optional, Callable
from collections import defaultdict

from .models import (
    LogEntry, 
    Violation, 
    EntryResult, 
    ValidationStatus, 
    RobotSummary,
    ValidationReport,
    Severity
)
from .parser import LogParser
from .rule_engine import RuleEngine


class Validator:
    """
    Core validator that orchestrates log validation.
    Supports streaming processing and real-time callbacks.
    """

    def __init__(
        self,
        rule_engine: RuleEngine,
        on_violation: Optional[Callable[[Violation], None]] = None,
        on_entry: Optional[Callable[[EntryResult], None]] = None
    ):
        self.rule_engine = rule_engine
        self.on_violation = on_violation
        self.on_entry = on_entry
        
        # Counters
        self._total_entries = 0
        self._total_passed = 0
        self._total_violations = 0
        
        # Aggregations
        self._violations_by_rule: Dict[str, int] = defaultdict(int)
        self._violations_by_severity: Dict[str, int] = defaultdict(int)
        self._robot_summaries: Dict[str, RobotSummary] = {}
        self._all_violations: List[Violation] = []

    def reset(self) -> None:
        """Reset all counters and aggregations."""
        self._total_entries = 0
        self._total_passed = 0
        self._total_violations = 0
        self._violations_by_rule = defaultdict(int)
        self._violations_by_severity = defaultdict(int)
        self._robot_summaries = {}
        self._all_violations = []

    @property
    def total_entries(self) -> int:
        return self._total_entries

    @property
    def total_violations(self) -> int:
        return self._total_violations

    @property
    def pass_rate(self) -> float:
        if self._total_entries == 0:
            return 100.0
        return (self._total_passed / self._total_entries) * 100

    def validate_entry(self, entry: LogEntry) -> EntryResult:
        """Validate a single log entry and update statistics."""
        violations = self.rule_engine.validate_entry(entry)
        
        # Determine status
        status = ValidationStatus.PASS if not violations else ValidationStatus.FAIL
        result = EntryResult(log_entry=entry, status=status, violations=violations)
        
        # Update counters
        self._total_entries += 1
        if result.passed:
            self._total_passed += 1
        
        # Update robot summary
        robot_id = entry.robot_id
        if robot_id not in self._robot_summaries:
            self._robot_summaries[robot_id] = RobotSummary(robot_id=robot_id)
        
        robot_summary = self._robot_summaries[robot_id]
        robot_summary.total_entries += 1
        
        # Process violations
        for violation in violations:
            self._total_violations += 1
            self._violations_by_rule[violation.rule_id] += 1
            self._violations_by_severity[violation.severity.value] += 1
            self._all_violations.append(violation)
            
            robot_summary.violations_count += 1
            robot_summary.status = ValidationStatus.FAIL
            robot_summary.violations.append(violation)
            
            # Trigger callback
            if self.on_violation:
                self.on_violation(violation)
        
        # Trigger entry callback
        if self.on_entry:
            self.on_entry(result)
        
        return result

    def validate_stream(self, entries: Iterator[LogEntry]) -> Iterator[EntryResult]:
        """
        Validate a stream of log entries.
        Yields results as they are processed.
        """
        for entry in entries:
            yield self.validate_entry(entry)

    def validate_all(self, entries: Iterator[LogEntry]) -> List[EntryResult]:
        """Validate all entries and return list of results."""
        return list(self.validate_stream(entries))

    def get_report(self, rules_file: str = "", input_file: str = "") -> ValidationReport:
        """Generate a validation report from the accumulated results."""
        return ValidationReport(
            total_entries=self._total_entries,
            total_passed=self._total_passed,
            total_violations=self._total_violations,
            pass_rate=self.pass_rate,
            violations_by_rule=dict(self._violations_by_rule),
            violations_by_severity=dict(self._violations_by_severity),
            robot_summaries=self._robot_summaries,
            violations=self._all_violations,
            rules_file=rules_file,
            input_file=input_file
        )


def create_validator(
    rules_file: str,
    on_violation: Optional[Callable[[Violation], None]] = None,
    on_entry: Optional[Callable[[EntryResult], None]] = None
) -> Validator:
    """Factory function to create a configured validator."""
    engine = RuleEngine()
    engine.load_rules(rules_file)
    return Validator(engine, on_violation=on_violation, on_entry=on_entry)
