# tests/test_rclone_ops.py
import json
import pytest
from unittest.mock import patch, MagicMock
from rclone_ops import list_files, download_file, upload_file

SAMPLE_LSJSON = json.dumps([
    {"Name": "Recording A.m4a", "Size": 1234, "ModTime": "2026-03-08T10:00:00Z"},
    {"Name": "Recording B.m4a", "Size": 5678, "ModTime": "2026-03-07T09:00:00Z"},
])

def test_list_files_returns_name_and_modtime():
    with patch('rclone_ops.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_LSJSON, stderr='')
        files = list_files('onedrive:Notes')
    assert len(files) == 2
    assert files[0]['name'] == 'Recording A.m4a'
    assert files[0]['mod_time'] == '2026-03-08T10:00:00Z'

def test_list_files_raises_on_rclone_error():
    with patch('rclone_ops.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='connection failed')
        with pytest.raises(RuntimeError, match='rclone lsjson failed'):
            list_files('onedrive:Notes')

def test_download_file_calls_correct_command():
    with patch('rclone_ops.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        download_file('onedrive:Notes', 'My Recording.m4a', '/tmp/My Recording.m4a')
    cmd = mock_run.call_args[0][0]
    assert 'rclone' in cmd
    assert 'copyto' in cmd
    assert 'onedrive:Notes/My Recording.m4a' in cmd
    assert '/tmp/My Recording.m4a' in cmd

def test_upload_file_calls_correct_command():
    with patch('rclone_ops.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        upload_file('/tmp/note.md', 'gdrive:Vault', '2026-03-08 My Recording.md')
    cmd = mock_run.call_args[0][0]
    assert 'rclone' in cmd
    assert 'copyto' in cmd
    assert '/tmp/note.md' in cmd
    assert 'gdrive:Vault/2026-03-08 My Recording.md' in cmd
