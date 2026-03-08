# stems.py
import re
from typing import Optional

DATE_PREFIX = re.compile(r'^\d{4}-\d{2}-\d{2} (.+)$')


def stem_from_m4a(filename: str) -> str:
    """'My Recording.m4a' -> 'My Recording'"""
    if filename.lower().endswith('.m4a'):
        return filename[:-4]
    return filename


def stem_from_md(filename: str) -> Optional[str]:
    """'2026-03-08 My Recording.md' -> 'My Recording', or None if no date prefix."""
    name = filename[:-3] if filename.lower().endswith('.md') else filename
    m = DATE_PREFIX.match(name)
    return m.group(1) if m else None


def find_unprocessed(m4a_names: list[str], md_names: list[str]) -> list[str]:
    """Return m4a filenames whose stems don't appear in any md filename."""
    processed = {stem_from_md(md) for md in md_names} - {None}
    return [f for f in m4a_names if stem_from_m4a(f) not in processed]
