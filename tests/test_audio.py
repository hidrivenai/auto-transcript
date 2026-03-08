# tests/test_audio.py
import pytest
from unittest.mock import patch, MagicMock
from audio import get_duration_seconds, format_duration

def test_format_duration_minutes_and_seconds():
    assert format_duration(272) == '4:32'

def test_format_duration_zero_pad_seconds():
    assert format_duration(65) == '1:05'

def test_format_duration_under_one_minute():
    assert format_duration(45) == '0:45'

def test_format_duration_exact_minutes():
    assert format_duration(120) == '2:00'

def test_get_duration_parses_ffprobe_output():
    with patch('audio.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='272.5\n', stderr='')
        result = get_duration_seconds('/tmp/file.m4a')
    assert result == 272.5

def test_get_duration_returns_zero_on_failure():
    with patch('audio.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
        result = get_duration_seconds('/tmp/file.m4a')
    assert result == 0.0
