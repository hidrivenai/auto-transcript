# tests/test_config.py
import os
import sys
import importlib
import pytest
from unittest.mock import patch


def _reload_config():
    """Force a fresh import of config module to avoid module caching issues."""
    if 'config' in sys.modules:
        del sys.modules['config']
    import config
    return config


def test_config_loads_required_vars():
    env = {
        'ELEVENLABS_API_KEY': 'test_key',
        'ONEDRIVE_REMOTE': 'onedrive:Notes',
        'GDRIVE_REMOTE': 'gdrive:Vault/Transcripts',
        'POLL_INTERVAL_SECONDS': '300',
    }
    with patch.dict(os.environ, env, clear=True):
        config = _reload_config()
        cfg = config.load_config()
    assert cfg['elevenlabs_api_key'] == 'test_key'
    assert cfg['onedrive_remote'] == 'onedrive:Notes'
    assert cfg['gdrive_remote'] == 'gdrive:Vault/Transcripts'
    assert cfg['poll_interval'] == 300


def test_config_raises_on_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        config = _reload_config()
        with patch.object(config, 'load_dotenv'):
            with pytest.raises(ValueError, match='ELEVENLABS_API_KEY'):
                config.load_config()


def test_config_default_poll_interval():
    env = {
        'ELEVENLABS_API_KEY': 'k',
        'ONEDRIVE_REMOTE': 'onedrive:X',
        'GDRIVE_REMOTE': 'gdrive:Y',
    }
    with patch.dict(os.environ, env, clear=True):
        config = _reload_config()
        cfg = config.load_config()
    assert cfg['poll_interval'] == 300
