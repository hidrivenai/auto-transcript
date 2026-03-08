# tests/test_transcribe.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
from transcribe import transcribe_file, count_speakers

SAMPLE_RESPONSE = {
    'text': 'Hello world. This is a test.',
    'words': [
        {'text': 'Hello', 'start': 0.0, 'end': 0.5, 'confidence': 0.99, 'speaker_id': 'speaker_0'},
        {'text': 'world.', 'start': 0.6, 'end': 1.0, 'confidence': 0.98, 'speaker_id': 'speaker_0'},
        {'text': 'This', 'start': 1.5, 'end': 1.8, 'confidence': 0.97, 'speaker_id': 'speaker_1'},
    ],
    'language_code': 'en',
}

def test_count_speakers_unique():
    assert count_speakers(SAMPLE_RESPONSE['words']) == 2

def test_count_speakers_single():
    words = [{'speaker_id': 'speaker_0'}, {'speaker_id': 'speaker_0'}]
    assert count_speakers(words) == 1

def test_count_speakers_no_words():
    assert count_speakers([]) == 0

def test_transcribe_file_sends_correct_request():
    m = mock_open(read_data=b'fake audio bytes')
    with patch('builtins.open', m), \
         patch('transcribe.requests.post') as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: SAMPLE_RESPONSE
        )
        result = transcribe_file('/tmp/test.m4a', api_key='test_key')

    assert result['text'] == 'Hello world. This is a test.'
    assert result['speakers'] == 2
    assert result['language'] == 'en'

    call_kwargs = mock_post.call_args
    assert call_kwargs[1]['headers']['xi-api-key'] == 'test_key'

def test_transcribe_file_raises_on_api_error():
    m = mock_open(read_data=b'fake audio bytes')
    with patch('builtins.open', m), \
         patch('transcribe.requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=401, text='Unauthorized')
        with pytest.raises(RuntimeError, match='ElevenLabs API error 401'):
            transcribe_file('/tmp/test.m4a', api_key='bad_key')
