# System Log Validator

A production-grade Python CLI tool for validating robot/system logs against JSON-defined safety rules.

## Features

- **JSON Rule Engine** - Define validation rules declaratively in JSON
- **Streaming Processing** - Process logs line-by-line for memory efficiency
- **Real-time Alerts** - Console warnings on rule violations
- **Comprehensive Reports** - JSON summary with per-robot status, violation counts, timestamps
- **Modular Architecture** - Clean separation: parser → rule_engine → validator → reporter

## Installation

```bash
cd python-validator
pip install -r requirements.txt
```

## Usage

### Basic validation:
```bash
python -m src.cli --input logs/sample_logs.json --rules rules/safety_rules.json --output report.json
```

### Stream from stdin:
```bash
cat logs/sample_logs.json | python -m src.cli --rules rules/safety_rules.json --stream
```

### CLI Flags:
| Flag | Description |
|------|-------------|
| `--input`, `-i` | Path to log file (JSON or JSONL) |
| `--rules`, `-r` | Path to rules JSON file |
| `--output`, `-o` | Path for JSON report output |
| `--stream` | Enable streaming mode (stdin) |
| `--verbose`, `-v` | Show detailed violation alerts |

## Rule Definition

Rules are defined in JSON with the following structure:

```json
{
  "rules": [
    {
      "id": "battery_minimum",
      "name": "Battery Level Check",
      "field": "battery_level",
      "operator": ">=",
      "threshold": 20,
      "severity": "critical",
      "message": "Battery below minimum safe level"
    }
  ]
}
```

### Supported Operators:
- `>=`, `>`, `<=`, `<`, `==`, `!=` - Numeric comparisons
- `in`, `not_in` - List membership
- `regex` - Pattern matching
- `conditional` - Complex rules with dependencies

## Architecture

```
src/
├── cli.py           # CLI entry point with argparse
├── parser.py        # Log file parsing (JSON, JSONL, streaming)
├── rule_engine.py   # Rule loading and evaluation
├── validator.py     # Core validation orchestration
├── reporter.py      # Report generation
└── alerts.py        # Real-time alert handling
```

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                   VALIDATION REPORT                          ║
╠══════════════════════════════════════════════════════════════╣
║  Total Entries:     1,234                                    ║
║  Passed:            1,180 (95.6%)                            ║
║  Violations:        54                                       ║
╚══════════════════════════════════════════════════════════════╝

Robot Status:
  ROBOT_001: PASS (0 violations)
  ROBOT_002: FAIL (12 violations)
  ROBOT_003: PASS (0 violations)

Top Violations:
  1. speed_limit_exceeded (23)
  2. battery_critical_movement (18)
  3. battery_minimum (13)
```

## License

MIT
