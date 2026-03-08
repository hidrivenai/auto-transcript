# tests/test_stems.py
import pytest
from stems import stem_from_m4a, stem_from_md, find_unprocessed

def test_stem_from_m4a_basic():
    assert stem_from_m4a('My Recording.m4a') == 'My Recording'

def test_stem_from_m4a_no_path():
    assert stem_from_m4a('Meeting Notes.m4a') == 'Meeting Notes'

def test_stem_from_md_strips_date_prefix():
    assert stem_from_md('2026-03-08 My Recording.md') == 'My Recording'

def test_stem_from_md_no_date_prefix_returns_none():
    assert stem_from_md('My Recording.md') is None

def test_stem_from_md_various_dates():
    assert stem_from_md('2024-12-31 Year End.md') == 'Year End'

def test_find_unprocessed_filters_already_done():
    m4a_names = ['Recording A.m4a', 'Recording B.m4a', 'Recording C.m4a']
    md_names = ['2026-03-07 Recording A.md', '2026-02-01 Recording C.md']
    result = find_unprocessed(m4a_names, md_names)
    assert result == ['Recording B.m4a']

def test_find_unprocessed_all_new():
    result = find_unprocessed(['New.m4a'], [])
    assert result == ['New.m4a']

def test_find_unprocessed_all_processed():
    result = find_unprocessed(['Old.m4a'], ['2026-01-01 Old.md'])
    assert result == []
