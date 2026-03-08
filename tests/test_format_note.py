# tests/test_format_note.py
import pytest
from format_note import parse_place_from_stem, build_note

def test_parse_place_last_word_if_capitalized():
    assert parse_place_from_stem('Meeting Budapest') == 'Budapest'

def test_parse_place_returns_none_if_last_word_lowercase():
    assert parse_place_from_stem('my daily thoughts') is None

def test_parse_place_single_word():
    assert parse_place_from_stem('Budapest') is None  # no context word before it

def test_parse_place_none_for_generic_name():
    assert parse_place_from_stem('Recording') is None

def test_build_note_basic():
    note = build_note(
        stem='My Recording',
        date='2026-03-08',
        duration_str='4:32',
        speakers=2,
        transcript='Hello world.',
        place=None,
    )
    assert note.startswith('---\n')
    assert 'date: 2026-03-08' in note
    assert 'duration: 4:32' in note
    assert 'speakers: 2' in note
    assert 'source_file: My Recording.m4a' in note
    assert 'place:' not in note
    assert 'Hello world.' in note

def test_build_note_with_place():
    note = build_note(
        stem='Meeting Budapest',
        date='2026-03-08',
        duration_str='1:05',
        speakers=1,
        transcript='Test.',
        place='Budapest',
    )
    assert 'place: Budapest' in note

def test_build_note_frontmatter_closed():
    note = build_note('X', '2026-01-01', '0:30', 1, 'Text.', None)
    parts = note.split('---')
    assert len(parts) >= 3  # ---, frontmatter, ---, body
