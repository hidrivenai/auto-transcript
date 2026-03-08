# tests/test_main.py
import pytest
from unittest.mock import patch, MagicMock
from main import process_one, run_once

SAMPLE_CFG = {
    'elevenlabs_api_key': 'key',
    'onedrive_remote': 'onedrive:Notes',
    'gdrive_remote': 'gdrive:Vault',
    'poll_interval': 300,
}

def test_run_once_skips_processed_files():
    with patch('main.list_files') as mock_list, \
         patch('main.find_unprocessed') as mock_find, \
         patch('main.process_one') as mock_proc:

        mock_list.side_effect = [
            [{'name': '2026-03-08 Old.md', 'mod_time': '...'}],  # gdrive
            [{'name': 'Old.m4a', 'mod_time': '...'}],             # onedrive
        ]
        mock_find.return_value = []  # nothing new

        run_once(SAMPLE_CFG)

        mock_proc.assert_not_called()

def test_run_once_processes_new_file():
    with patch('main.list_files') as mock_list, \
         patch('main.find_unprocessed', return_value=['New.m4a']), \
         patch('main.process_one') as mock_proc:

        mock_list.side_effect = [
            [],                                                      # gdrive empty
            [{'name': 'New.m4a', 'mod_time': '2026-03-08T10:00:00Z'}],  # onedrive
        ]

        run_once(SAMPLE_CFG)

        mock_proc.assert_called_once_with(
            'New.m4a', '2026-03-08T10:00:00Z', SAMPLE_CFG
        )

def test_run_once_continues_after_per_file_error():
    with patch('main.list_files') as mock_list, \
         patch('main.find_unprocessed', return_value=['Fail.m4a', 'Success.m4a']), \
         patch('main.process_one') as mock_proc:

        mock_list.side_effect = [
            [],  # gdrive empty
            [
                {'name': 'Fail.m4a', 'mod_time': '2026-03-08T09:00:00Z'},
                {'name': 'Success.m4a', 'mod_time': '2026-03-08T10:00:00Z'},
            ],
        ]
        mock_proc.side_effect = [RuntimeError('transcription failed'), None]

        run_once(SAMPLE_CFG)  # must not raise

        assert mock_proc.call_count == 2
