"""
Real-time alert handling for rule violations.
"""

import sys
from typing import TextIO, Optional
from datetime import datetime

from .models import Violation, Severity


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


SEVERITY_COLORS = {
    Severity.INFO: Colors.BLUE,
    Severity.WARNING: Colors.YELLOW,
    Severity.ERROR: Colors.RED,
    Severity.CRITICAL: Colors.MAGENTA,
}

SEVERITY_ICONS = {
    Severity.INFO: "ℹ",
    Severity.WARNING: "⚠",
    Severity.ERROR: "✖",
    Severity.CRITICAL: "🔥",
}


class AlertHandler:
    """
    Handler for real-time violation alerts.
    Outputs formatted alerts to console.
    """

    def __init__(
        self,
        output: TextIO = sys.stderr,
        use_colors: bool = True,
        verbose: bool = False,
        quiet: bool = False
    ):
        self.output = output
        self.use_colors = use_colors and output.isatty()
        self.verbose = verbose
        self.quiet = quiet
        self._alert_count = 0

    @property
    def alert_count(self) -> int:
        return self._alert_count

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_colors:
            return f"{color}{text}{Colors.RESET}"
        return text

    def alert(self, violation: Violation) -> None:
        """Output an alert for a violation."""
        if self.quiet:
            return

        self._alert_count += 1
        color = SEVERITY_COLORS.get(violation.severity, Colors.RESET)
        icon = SEVERITY_ICONS.get(violation.severity, "•")

        # Format severity tag
        severity_tag = self._colorize(
            f"[{violation.severity.value.upper()}]",
            color
        )

        # Format robot ID
        robot_tag = self._colorize(f"[{violation.robot_id}]", Colors.CYAN)

        # Format rule name
        rule_tag = self._colorize(violation.rule_name, Colors.BOLD)

        # Basic alert format
        alert_line = f"{icon} {severity_tag} {robot_tag} {rule_tag}: {violation.message}"
        
        print(alert_line, file=self.output)

        # Verbose output with details
        if self.verbose:
            detail_color = Colors.DIM if self.use_colors else ""
            reset = Colors.RESET if self.use_colors else ""
            
            print(f"   {detail_color}├─ Field: {violation.field}{reset}", file=self.output)
            print(f"   {detail_color}├─ Actual: {violation.actual_value}{reset}", file=self.output)
            print(f"   {detail_color}├─ Expected: {violation.expected}{reset}", file=self.output)
            print(f"   {detail_color}├─ Timestamp: {violation.timestamp}{reset}", file=self.output)
            print(f"   {detail_color}└─ Log Index: {violation.log_index}{reset}", file=self.output)


class AlertCollector:
    """
    Collector for structured alert output.
    Accumulates alerts for batch processing.
    """

    def __init__(self):
        self.alerts: list[dict] = []

    def alert(self, violation: Violation) -> None:
        """Collect a violation alert."""
        self.alerts.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "violation": violation.to_dict()
        })

    def get_alerts(self) -> list[dict]:
        """Get all collected alerts."""
        return self.alerts

    def clear(self) -> None:
        """Clear all collected alerts."""
        self.alerts = []


def create_console_alerter(verbose: bool = False, quiet: bool = False) -> AlertHandler:
    """Create a console alert handler."""
    return AlertHandler(verbose=verbose, quiet=quiet)
