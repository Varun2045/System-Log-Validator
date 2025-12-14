"""
Data models for the log validator.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class Severity(Enum):
    """Severity levels for rule violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationStatus(Enum):
    """Validation result status."""
    PASS = "pass"
    FAIL = "fail"


@dataclass
class Rule:
    """Represents a validation rule."""
    id: str
    name: str
    field: str
    operator: str
    threshold: Any
    severity: Severity
    message: str
    description: str = ""
    type: str = "simple"
    condition: Optional[Dict] = None
    then: Optional[Dict] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "Rule":
        """Create a Rule from a dictionary."""
        severity = Severity(data.get("severity", "warning"))
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            field=data.get("field", ""),
            operator=data.get("operator", ""),
            threshold=data.get("threshold"),
            severity=severity,
            message=data.get("message", ""),
            description=data.get("description", ""),
            type=data.get("type", "simple"),
            condition=data.get("condition"),
            then=data.get("then")
        )


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: str
    robot_id: str
    raw_data: Dict[str, Any]
    index: int = 0

    @classmethod
    def from_dict(cls, data: Dict, index: int = 0) -> "LogEntry":
        """Create a LogEntry from a dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            robot_id=data.get("robot_id", "unknown"),
            raw_data=data,
            index=index
        )


@dataclass
class Violation:
    """Represents a rule violation."""
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    timestamp: str
    robot_id: str
    field: str
    actual_value: Any
    expected: str
    log_index: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "robot_id": self.robot_id,
            "field": self.field,
            "actual_value": self.actual_value,
            "expected": self.expected,
            "log_index": self.log_index
        }


@dataclass
class EntryResult:
    """Result of validating a single log entry."""
    log_entry: LogEntry
    status: ValidationStatus
    violations: List[Violation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASS


@dataclass
class RobotSummary:
    """Summary of validation results for a single robot."""
    robot_id: str
    total_entries: int = 0
    violations_count: int = 0
    status: ValidationStatus = ValidationStatus.PASS
    violations: List[Violation] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "robot_id": self.robot_id,
            "total_entries": self.total_entries,
            "violations_count": self.violations_count,
            "status": self.status.value,
            "pass_rate": round((self.total_entries - self.violations_count) / max(self.total_entries, 1) * 100, 2)
        }


@dataclass
class ValidationReport:
    """Complete validation report."""
    total_entries: int
    total_passed: int
    total_violations: int
    pass_rate: float
    violations_by_rule: Dict[str, int]
    violations_by_severity: Dict[str, int]
    robot_summaries: Dict[str, RobotSummary]
    violations: List[Violation]
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    rules_file: str = ""
    input_file: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_entries": self.total_entries,
                "total_passed": self.total_passed,
                "total_violations": self.total_violations,
                "pass_rate": round(self.pass_rate, 2),
                "generated_at": self.generated_at,
                "rules_file": self.rules_file,
                "input_file": self.input_file
            },
            "violations_by_rule": self.violations_by_rule,
            "violations_by_severity": self.violations_by_severity,
            "robots": {rid: rs.to_dict() for rid, rs in self.robot_summaries.items()},
            "violations": [v.to_dict() for v in self.violations]
        }
