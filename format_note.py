# format_note.py
from typing import Optional


def parse_place_from_stem(stem: str) -> Optional[str]:
    """
    Heuristic: if the last word of the stem starts with a capital letter
    and there is more than one word, treat it as a place name.
    e.g. 'Meeting Budapest' -> 'Budapest', 'my thoughts' -> None
    """
    parts = stem.split()
    if len(parts) < 2:
        return None
    last = parts[-1]
    if last and last[0].isupper():
        return last
    return None


def format_diarized_transcript(words: list[dict]) -> str:
    """Build speaker-attributed transcript from ElevenLabs word list.

    Groups consecutive words by speaker_id and formats as:
        **Speaker 1:** Hello, how are you?

        **Speaker 2:** I'm fine, thanks.
    """
    if not words:
        return ''

    segments: list[tuple[str, list[str]]] = []
    current_speaker = None

    for w in words:
        speaker = w.get('speaker_id')
        text = w.get('text', '')
        if not text:
            continue
        if speaker != current_speaker:
            current_speaker = speaker
            label = f'Speaker {speaker}' if speaker is not None else 'Unknown'
            segments.append((label, [text]))
        else:
            segments[-1][1].append(text)

    lines = []
    for label, texts in segments:
        content = ''.join(texts).strip()
        if content:
            lines.append(f'**{label}:** {content}')
    return '\n\n'.join(lines)


def build_note(
    stem: str,
    date: str,
    duration_str: str,
    speakers: int,
    transcript: str,
    place: Optional[str],
) -> str:
    """Build the full Obsidian markdown note string."""
    lines = ['---']
    lines.append(f'date: {date}')
    lines.append(f'duration: {duration_str}')
    lines.append(f'speakers: {speakers}')
    lines.append(f'source_file: {stem}.m4a')
    if place:
        lines.append(f'place: {place}')
    lines.append('---')
    lines.append('')
    lines.append(transcript)
    lines.append('')
    return '\n'.join(lines)
