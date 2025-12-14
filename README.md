# System Log Validator

A Python CLI-first tool for validating robot/system logs against configurable safety rules defined in JSON.

## Features

- **Streaming validation** — process logs line-by-line without loading everything into memory
- **JSON-based rule engine** — extensible rules with 12+ operators including conditional rules
- **Real-time alerts** — console warnings when rules are violated
- **JSON reports** — detailed output with per-robot PASS/FAIL status and violation summaries
- **Demo UI** — minimal web interface for quick validation demos

## Quick Start

### CLI Usage

```sh
cd python-validator
pip install -r requirements.txt

# Run validation
python -m src.cli -i ../samples/sample_logs.json -r ../samples/sample_rules.json -o report.json

# Stream mode with verbose output
python -m src.cli -i logs.json -r rules.json --stream -v
```

### Web UI (Demo)

```sh
npm install
npm run dev
```

Open the browser and use the "Use Sample Files" button to run a demo validation.

## Project Structure

```
├── python-validator/
│   ├── src/
│   │   ├── cli.py          # CLI entry point
│   │   ├── parser.py       # Log file parser (JSON/JSONL)
│   │   ├── rule_engine.py  # Extensible rule engine
│   │   ├── validator.py    # Streaming validator
│   │   ├── alerts.py       # Real-time console alerts
│   │   └── reporter.py     # JSON report generator
│   ├── rules/
│   │   └── safety_rules.json
│   └── tests/
├── samples/
│   ├── sample_logs.json
│   └── sample_rules.json
├── output/
│   └── report.json         # Example output
└── src/                    # Web UI (React/TypeScript)
```

## Rule Engine

Rules are defined in JSON with support for:

- Comparison operators: `>=`, `<=`, `>`, `<`, `==`, `!=`
- Collection operators: `in`, `not_in`
- Pattern matching: `regex`
- Existence checks: `exists`
- Conditional rules: `if condition then check`

Example rule:

```json
{
  "id": "battery_minimum",
  "field": "battery_level",
  "operator": ">=",
  "threshold": 20,
  "severity": "warning",
  "message": "Battery level below minimum safe threshold (20%)"
}
```

## Technologies

- **Backend**: Python 3.x (CLI-first)
- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui (demo UI only)

## License

MIT