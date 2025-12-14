"""
Log file parser with streaming support.
Handles JSON, JSONL, and structured text formats.
"""

import json
import sys
from typing import Iterator, List, Dict, Any, TextIO, Union
from pathlib import Path

from .models import LogEntry


class LogParser:
    """Parser for log files with streaming support."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._entry_count = 0

    @property
    def entries_parsed(self) -> int:
        """Return the number of entries parsed so far."""
        return self._entry_count

    def parse_file(self, file_path: Union[str, Path]) -> Iterator[LogEntry]:
        """
        Parse a log file and yield LogEntry objects.
        Automatically detects JSON array or JSONL format.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            yield from self._parse_stream(f, str(file_path))

    def parse_stream(self, stream: TextIO) -> Iterator[LogEntry]:
        """Parse from a stream (stdin or file-like object)."""
        yield from self._parse_stream(stream, "stdin")

    def _parse_stream(self, stream: TextIO, source: str) -> Iterator[LogEntry]:
        """
        Internal method to parse a stream.
        Detects format automatically:
        - JSON array: Parse entire array, yield entries
        - JSONL: Parse line by line
        """
        # Peek at first non-whitespace character
        first_char = ""
        while True:
            char = stream.read(1)
            if not char:  # EOF
                return
            if not char.isspace():
                first_char = char
                break

        if first_char == "[":
            # JSON array format - read entire content
            remaining = stream.read()
            content = first_char + remaining
            yield from self._parse_json_array(content)
        else:
            # JSONL format - parse line by line
            first_line = first_char + stream.readline()
            yield from self._parse_jsonl_line(first_line)
            
            for line in stream:
                yield from self._parse_jsonl_line(line)

    def _parse_json_array(self, content: str) -> Iterator[LogEntry]:
        """Parse a JSON array of log entries."""
        try:
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError("Expected JSON array of log entries")
            
            for i, entry in enumerate(data):
                self._entry_count += 1
                yield LogEntry.from_dict(entry, index=i)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    def _parse_jsonl_line(self, line: str) -> Iterator[LogEntry]:
        """Parse a single JSONL line."""
        line = line.strip()
        if not line or line.startswith("#"):
            return

        try:
            data = json.loads(line)
            self._entry_count += 1
            yield LogEntry.from_dict(data, index=self._entry_count - 1)
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"Warning: Skipping invalid JSON line: {e}", file=sys.stderr)

    def parse_entries(self, entries: List[Dict[str, Any]]) -> Iterator[LogEntry]:
        """Parse a list of dictionaries directly."""
        for i, entry in enumerate(entries):
            self._entry_count += 1
            yield LogEntry.from_dict(entry, index=i)


def load_logs_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Convenience function to load all logs from a file."""
    parser = LogParser()
    return [entry.raw_data for entry in parser.parse_file(file_path)]
