"""
Tests for the log parser.
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.parser import LogParser


@pytest.fixture
def parser():
    """Create a fresh parser for each test."""
    return LogParser()


class TestJSONArrayParsing:
    """Test parsing JSON arrays."""

    def test_parse_json_array(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"timestamp": "2024-01-15T08:00:00Z", "robot_id": "ROBOT_001", "battery_level": 80},
                {"timestamp": "2024-01-15T08:00:05Z", "robot_id": "ROBOT_002", "battery_level": 60}
            ], f)
            f.flush()
            
            entries = list(parser.parse_file(f.name))
            
            assert len(entries) == 2
            assert entries[0].robot_id == "ROBOT_001"
            assert entries[1].robot_id == "ROBOT_002"
            
            Path(f.name).unlink()

    def test_entries_have_correct_indices(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"timestamp": "t1", "robot_id": "R1"},
                {"timestamp": "t2", "robot_id": "R2"},
                {"timestamp": "t3", "robot_id": "R3"}
            ], f)
            f.flush()
            
            entries = list(parser.parse_file(f.name))
            
            assert entries[0].index == 0
            assert entries[1].index == 1
            assert entries[2].index == 2
            
            Path(f.name).unlink()


class TestJSONLParsing:
    """Test parsing JSONL (line-delimited JSON)."""

    def test_parse_jsonl(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"timestamp": "t1", "robot_id": "R1"}\n')
            f.write('{"timestamp": "t2", "robot_id": "R2"}\n')
            f.write('{"timestamp": "t3", "robot_id": "R3"}\n')
            f.flush()
            
            entries = list(parser.parse_file(f.name))
            
            assert len(entries) == 3
            assert entries[0].robot_id == "R1"
            assert entries[1].robot_id == "R2"
            assert entries[2].robot_id == "R3"
            
            Path(f.name).unlink()

    def test_skip_empty_lines(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"timestamp": "t1", "robot_id": "R1"}\n')
            f.write('\n')
            f.write('{"timestamp": "t2", "robot_id": "R2"}\n')
            f.write('   \n')
            f.write('{"timestamp": "t3", "robot_id": "R3"}\n')
            f.flush()
            
            entries = list(parser.parse_file(f.name))
            
            assert len(entries) == 3
            
            Path(f.name).unlink()

    def test_skip_comments(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('# This is a comment\n')
            f.write('{"timestamp": "t1", "robot_id": "R1"}\n')
            f.write('# Another comment\n')
            f.write('{"timestamp": "t2", "robot_id": "R2"}\n')
            f.flush()
            
            entries = list(parser.parse_file(f.name))
            
            assert len(entries) == 2
            
            Path(f.name).unlink()


class TestEntryParsing:
    """Test parsing entry data."""

    def test_parse_entry_dict(self, parser):
        entries = list(parser.parse_entries([
            {"timestamp": "2024-01-15T08:00:00Z", "robot_id": "ROBOT_001", "battery_level": 80},
        ]))
        
        assert len(entries) == 1
        assert entries[0].timestamp == "2024-01-15T08:00:00Z"
        assert entries[0].robot_id == "ROBOT_001"
        assert entries[0].raw_data["battery_level"] == 80

    def test_missing_robot_id(self, parser):
        entries = list(parser.parse_entries([
            {"timestamp": "2024-01-15T08:00:00Z", "battery_level": 80},
        ]))
        
        assert len(entries) == 1
        assert entries[0].robot_id == "unknown"


class TestErrorHandling:
    """Test error handling."""

    def test_file_not_found(self, parser):
        with pytest.raises(FileNotFoundError):
            list(parser.parse_file("nonexistent_file.json"))

    def test_invalid_json(self, parser):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[{"invalid json}')
            f.flush()
            
            with pytest.raises(ValueError):
                list(parser.parse_file(f.name))
            
            Path(f.name).unlink()

    def test_counter_updates(self, parser):
        assert parser.entries_parsed == 0
        
        list(parser.parse_entries([
            {"timestamp": "t1", "robot_id": "R1"},
            {"timestamp": "t2", "robot_id": "R2"},
        ]))
        
        assert parser.entries_parsed == 2
