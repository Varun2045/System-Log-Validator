"""
CLI entry point for the System Log Validator.
"""

import argparse
import sys
from typing import Optional

from .parser import LogParser
from .rule_engine import RuleEngine
from .validator import Validator
from .reporter import Reporter, generate_report
from .alerts import AlertHandler, create_console_alerter


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="log-validator",
        description="Validate robot/system logs against JSON-defined safety rules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a log file with rules
  python -m src.cli -i logs/sample.json -r rules/safety.json -o report.json

  # Stream from stdin
  cat logs/data.jsonl | python -m src.cli -r rules/safety.json --stream

  # Verbose output with all violations
  python -m src.cli -i logs/sample.json -r rules/safety.json -v
        """
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        help="Path to input log file (JSON or JSONL format)"
    )

    parser.add_argument(
        "-r", "--rules",
        type=str,
        required=True,
        help="Path to JSON rules file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path for JSON report output"
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode (read from stdin)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed violation information"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress real-time alerts (only show final report)"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    parser.add_argument(
        "--max-violations",
        type=int,
        default=10,
        help="Maximum violations to show in console summary (default: 10)"
    )

    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments."""
    if not args.input and not args.stream:
        print("Error: Either --input or --stream must be specified", file=sys.stderr)
        return False
    
    if args.input and args.stream:
        print("Error: Cannot use both --input and --stream", file=sys.stderr)
        return False

    return True


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    if not validate_args(args):
        return 1

    use_colors = not args.no_color and sys.stdout.isatty()

    try:
        # Initialize components
        log_parser = LogParser(verbose=args.verbose)
        rule_engine = RuleEngine()
        rule_engine.load_rules(args.rules)

        # Create alert handler
        alerter = create_console_alerter(
            verbose=args.verbose,
            quiet=args.quiet
        )

        # Create validator with alert callback
        validator = Validator(
            rule_engine=rule_engine,
            on_violation=alerter.alert
        )

        # Process logs
        if args.stream:
            entries = log_parser.parse_stream(sys.stdin)
            input_source = "stdin"
        else:
            entries = log_parser.parse_file(args.input)
            input_source = args.input

        # Validate all entries
        print(f"\nValidating logs from: {input_source}")
        print(f"Using rules from: {args.rules}")
        print("-" * 40)

        # Process stream
        for result in validator.validate_stream(entries):
            pass  # Violations are handled by alerter callback

        # Generate report
        report = validator.get_report(
            rules_file=args.rules,
            input_file=input_source
        )

        # Output report
        generate_report(
            report,
            output_path=args.output,
            console=True,
            use_colors=use_colors
        )

        # Return non-zero if there were violations
        return 1 if report.total_violations > 0 else 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
