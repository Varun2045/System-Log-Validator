"""
Report generation for validation results.
Produces JSON reports and console summaries.
"""

import json
import sys
from typing import TextIO, Optional
from pathlib import Path

from .models import ValidationReport, ValidationStatus


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class Reporter:
    """
    Report generator for validation results.
    """

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_colors:
            return f"{color}{text}{Colors.RESET}"
        return text

    def write_json_report(self, report: ValidationReport, output_path: str) -> None:
        """Write a JSON report to a file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)

    def print_console_summary(
        self,
        report: ValidationReport,
        output: TextIO = sys.stdout,
        show_violations: bool = True,
        max_violations: int = 10
    ) -> None:
        """Print a formatted console summary."""
        
        # Header
        print("\n" + "═" * 66, file=output)
        print(self._colorize("                    VALIDATION REPORT", Colors.BOLD), file=output)
        print("═" * 66, file=output)

        # Summary statistics
        pass_color = Colors.GREEN if report.pass_rate >= 90 else Colors.YELLOW if report.pass_rate >= 70 else Colors.RED
        
        print(f"\n  Total Entries:     {report.total_entries:,}", file=output)
        print(f"  Passed:            {self._colorize(f'{report.total_passed:,}', Colors.GREEN)} ({report.pass_rate:.1f}%)", file=output)
        print(f"  Violations:        {self._colorize(f'{report.total_violations:,}', Colors.RED if report.total_violations > 0 else Colors.GREEN)}", file=output)
        
        # Robot status
        print("\n" + "─" * 66, file=output)
        print(self._colorize("  Robot Status:", Colors.BOLD), file=output)
        print("─" * 66, file=output)
        
        for robot_id, summary in sorted(report.robot_summaries.items()):
            status_str = "PASS" if summary.status == ValidationStatus.PASS else "FAIL"
            status_color = Colors.GREEN if summary.status == ValidationStatus.PASS else Colors.RED
            
            violation_info = f"({summary.violations_count} violations)" if summary.violations_count > 0 else ""
            print(f"    {robot_id}: {self._colorize(status_str, status_color)} {violation_info}", file=output)

        # Violations by rule
        if report.violations_by_rule:
            print("\n" + "─" * 66, file=output)
            print(self._colorize("  Violations by Rule:", Colors.BOLD), file=output)
            print("─" * 66, file=output)
            
            sorted_rules = sorted(report.violations_by_rule.items(), key=lambda x: x[1], reverse=True)
            for i, (rule_id, count) in enumerate(sorted_rules[:5], 1):
                print(f"    {i}. {rule_id}: {self._colorize(str(count), Colors.YELLOW)}", file=output)

        # Violations by severity
        if report.violations_by_severity:
            print("\n" + "─" * 66, file=output)
            print(self._colorize("  Violations by Severity:", Colors.BOLD), file=output)
            print("─" * 66, file=output)
            
            severity_order = ["critical", "error", "warning", "info"]
            for severity in severity_order:
                if severity in report.violations_by_severity:
                    count = report.violations_by_severity[severity]
                    color = Colors.RED if severity in ["critical", "error"] else Colors.YELLOW if severity == "warning" else Colors.BLUE
                    print(f"    {severity.upper()}: {self._colorize(str(count), color)}", file=output)

        # Recent violations
        if show_violations and report.violations:
            print("\n" + "─" * 66, file=output)
            print(self._colorize(f"  Recent Violations (showing {min(len(report.violations), max_violations)}):", Colors.BOLD), file=output)
            print("─" * 66, file=output)
            
            for violation in report.violations[:max_violations]:
                severity_color = Colors.RED if violation.severity.value in ["critical", "error"] else Colors.YELLOW
                print(
                    f"    [{self._colorize(violation.severity.value.upper(), severity_color)}] "
                    f"{violation.robot_id} - {violation.rule_name}: {violation.message}",
                    file=output
                )

        print("\n" + "═" * 66 + "\n", file=output)


def generate_report(
    report: ValidationReport,
    output_path: Optional[str] = None,
    console: bool = True,
    use_colors: bool = True
) -> None:
    """Convenience function to generate reports."""
    reporter = Reporter(use_colors=use_colors)
    
    if console:
        reporter.print_console_summary(report)
    
    if output_path:
        reporter.write_json_report(report, output_path)
        print(f"Report written to: {output_path}")
