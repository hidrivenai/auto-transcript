# transcribe.py
import requests

ELEVENLABS_STT_URL = 'https://api.elevenlabs.io/v1/speech-to-text'


def count_speakers(words: list[dict]) -> int:
    """Count unique speaker_ids in word list."""
    return len({w['speaker_id'] for w in words if w.get('speaker_id') is not None})


def transcribe_file(file_path: str, api_key: str) -> dict:
    """
    Transcribe an audio file with ElevenLabs Scribe v2.
    Returns dict with 'text', 'speakers', 'language', 'words'.
    """
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()

    response = requests.post(
        ELEVENLABS_STT_URL,
        headers={'xi-api-key': api_key},
        files={'file': ('audio.m4a', audio_bytes, 'audio/mp4')},
        data={
            'model_id': 'scribe_v2',
            'timestamps_granularity': 'word',
            'diarize': 'true',
            'tag_audio_events': 'false',
        },
    )

    if response.status_code != 200:
        raise RuntimeError(f'ElevenLabs API error {response.status_code}: {response.text}')

    data = response.json()
    words = data.get('words', [])

    return {
        'text': data.get('text', ''),
        'speakers': count_speakers(words),
        'language': data.get('language_code', ''),
        'words': words,
    }
