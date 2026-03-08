# rclone_ops.py
import json
import os
import subprocess


def _clean_rclone_env() -> dict:
    """Build env dict with RCLONE_CONFIG_* values cleaned for rclone.

    Handles surrounding quotes and escaped quotes that Coolify/Docker
    can introduce when injecting JSON tokens as env vars.
    """
    env = os.environ.copy()
    for key, val in env.items():
        if not key.startswith('RCLONE_CONFIG_'):
            continue
        # Strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        # Unescape backslash-escaped quotes (e.g. {\"access_token\":...})
        if '\\' in val:
            val = val.replace('\\"', '"').replace('\\\\', '\\')
        env[key] = val
    return env


def list_files(remote: str) -> list[dict]:
    """List files in remote, return list of {name, mod_time} dicts."""
    result = subprocess.run(
        ['rclone', 'lsjson', remote],
        capture_output=True, text=True, env=_clean_rclone_env()
    )
    if result.returncode != 0:
        raise RuntimeError(f"rclone lsjson failed: {result.stderr}")
    entries = json.loads(result.stdout or '[]')
    return [
        {'name': e['Name'], 'mod_time': e['ModTime']}
        for e in entries
        if not e.get('IsDir', False)
    ]


def download_file(remote: str, filename: str, local_path: str) -> None:
    """Download a single file from remote to local_path."""
    result = subprocess.run(
        ['rclone', 'copyto', f'{remote}/{filename}', local_path],
        capture_output=True, text=True, env=_clean_rclone_env()
    )
    if result.returncode != 0:
        raise RuntimeError(f"rclone download failed for '{filename}': {result.stderr}")


def upload_file(local_path: str, remote: str, remote_filename: str) -> None:
    """Upload local_path to remote/remote_filename."""
    result = subprocess.run(
        ['rclone', 'copyto', local_path, f'{remote}/{remote_filename}'],
        capture_output=True, text=True, env=_clean_rclone_env()
    )
    if result.returncode != 0:
        raise RuntimeError(f"rclone upload failed for '{remote_filename}': {result.stderr}")
