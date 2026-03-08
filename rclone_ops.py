# rclone_ops.py
import json
import logging
import os
import subprocess

import requests as _requests

log = logging.getLogger(__name__)

_env_cache: dict | None = None


def _strip_quotes(val: str) -> str:
    """Strip surrounding quotes and unescape backslash-escaped quotes."""
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
        val = val[1:-1]
    if '\\' in val:
        val = val.replace('\\"', '"').replace('\\\\', '\\')
    return val


RCLONE_ONEDRIVE_CLIENT_ID = 'b15665d9-eda6-4092-8539-0eec376afd59'
MS_TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'


def _refresh_onedrive_access_token(token_data: dict, client_id: str) -> str | None:
    """Use refresh_token to get a new access_token from Microsoft."""
    refresh_token = token_data.get('refresh_token')
    if not refresh_token:
        return None
    try:
        r = _requests.post(MS_TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
        }, timeout=10)
        r.raise_for_status()
        return r.json().get('access_token')
    except Exception as e:
        log.warning(f'Could not refresh OneDrive access_token: {e}')
        return None


def _resolve_onedrive_drive_id(env: dict) -> None:
    """Auto-detect OneDrive drive_id and drive_type via MS Graph API.

    Tries the existing access_token first; if expired (401), refreshes it
    using the refresh_token.
    """
    token_raw = env.get('RCLONE_CONFIG_ONEDRIVE_TOKEN', '')
    if not token_raw:
        return
    try:
        token_data = json.loads(token_raw)
    except json.JSONDecodeError:
        log.warning('Could not parse OneDrive token JSON')
        return

    client_id = env.get('RCLONE_CONFIG_ONEDRIVE_CLIENT_ID', RCLONE_ONEDRIVE_CLIENT_ID)
    access_token = token_data.get('access_token', '')

    for attempt in range(2):
        try:
            r = _requests.get(
                'https://graph.microsoft.com/v1.0/me/drive',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if r.status_code == 401 and attempt == 0:
                log.info('OneDrive access_token expired, refreshing...')
                new_token = _refresh_onedrive_access_token(token_data, client_id)
                if new_token:
                    access_token = new_token
                    continue
            r.raise_for_status()
            data = r.json()
            env['RCLONE_CONFIG_ONEDRIVE_DRIVE_ID'] = data['id']
            env['RCLONE_CONFIG_ONEDRIVE_DRIVE_TYPE'] = data.get('driveType', 'personal')
            log.info(f'OneDrive drive_id={data["id"]}, type={data.get("driveType")}')
            return
        except Exception as e:
            if attempt == 1:
                log.warning(f'Could not auto-detect OneDrive drive_id: {e}')


def _clean_rclone_env() -> dict:
    """Build env dict with RCLONE_CONFIG_* values cleaned for rclone.

    Handles surrounding quotes and escaped quotes that Coolify/Docker
    can introduce when injecting JSON tokens as env vars.
    Also auto-detects OneDrive drive_id on first call.
    """
    global _env_cache
    if _env_cache is not None:
        return _env_cache

    env = os.environ.copy()
    for key, val in env.items():
        if key.startswith('RCLONE_CONFIG_'):
            env[key] = _strip_quotes(val)

    if not env.get('RCLONE_CONFIG_ONEDRIVE_DRIVE_ID'):
        _resolve_onedrive_drive_id(env)

    _env_cache = env
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
