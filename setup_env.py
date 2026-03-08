#!/usr/bin/env python3
"""
Interactive setup: authenticates with OneDrive and Google Drive via rclone,
then writes all values to a .env file ready for local use or Coolify deployment.

Usage:
    python setup_env.py
"""

import getpass
import subprocess
import sys


def banner(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def ask(prompt, default=None, secret=False):
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    if secret:
        value = getpass.getpass(display)
    else:
        value = input(display).strip()
    return value if value else default


def check_rclone():
    result = subprocess.run(['rclone', 'version'], capture_output=True)
    if result.returncode != 0:
        print("ERROR: rclone is not installed.")
        print("Install it from: https://rclone.org/install/")
        sys.exit(1)
    print("✓ rclone found")


def setup_remote(name, rclone_type, extra_args=None):
    """Create rclone remote via config create — triggers OAuth browser flow."""
    subprocess.run(['rclone', 'config', 'delete', name], capture_output=True)
    cmd = ['rclone', 'config', 'create', name, rclone_type]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"ERROR: Failed to set up '{name}' remote.")
        sys.exit(1)


def read_remote_config(name):
    """Parse `rclone config show <name>` output into a dict."""
    result = subprocess.run(
        ['rclone', 'config', 'show', name],
        capture_output=True, text=True,
    )
    config = {}
    for line in result.stdout.splitlines():
        if ' = ' in line:
            key, _, value = line.partition(' = ')
            config[key.strip()] = value.strip()
    return config


def write_env(values: dict, path: str = '.env'):
    """Write key=value pairs to a .env file, quoting all values."""
    lines = []
    for key, value in values.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    print("╔════════════════════════════════════════════════╗")
    print("║   Voice Memo Auto-Transcriber — Setup         ║")
    print("╚════════════════════════════════════════════════╝")
    print()
    print("This script will:")
    print("  1. Ask for your ElevenLabs API key and folder paths")
    print("  2. Open your browser twice (OneDrive + Google Drive OAuth)")
    print("  3. Write everything to .env")

    # ── Dependencies ──────────────────────────────────────────
    banner("Checking dependencies")
    check_rclone()

    # ── Basic config ──────────────────────────────────────────
    banner("Basic configuration")
    elevenlabs_key = ask("ElevenLabs API key", secret=True)
    if not elevenlabs_key:
        print("ERROR: ElevenLabs API key is required.")
        sys.exit(1)

    print()
    onedrive_folder = ask(
        "OneDrive folder path (e.g. Personal/VoiceNotes)",
        default="Personal/VoiceNotes",
    )
    gdrive_folder = ask(
        "Google Drive folder path (e.g. ObsidianVault/Voice Transcripts)",
        default="ObsidianVault/Voice Transcripts",
    )
    poll_interval = ask("Poll interval in seconds", default="300")

    # ── OneDrive ──────────────────────────────────────────────
    banner("Step 1 of 2 — OneDrive authentication")
    print("rclone will open your browser to authenticate with Microsoft.")
    print("Sign in and authorize rclone when prompted.")
    input("\nPress Enter to open the browser...")

    print("(Any 'Failed to query root for drive' errors below are expected — we fix them automatically.)\n")
    setup_remote('onedrive', 'onedrive')

    # rclone auto-selects a drive_id that can be an invalid SharePoint handle
    # on personal accounts. Clear it so rclone uses the default personal root.
    subprocess.run(
        ['rclone', 'config', 'update', 'onedrive', 'drive_id', ''],
        capture_output=True,
    )

    od_cfg = read_remote_config('onedrive')
    if not od_cfg.get('token'):
        print("ERROR: OneDrive token not found after setup.")
        print("Debug with: rclone config show onedrive")
        sys.exit(1)
    print("✓ OneDrive token captured")

    # ── Google Drive ──────────────────────────────────────────
    banner("Step 2 of 2 — Google Drive authentication")
    print("rclone will open your browser to authenticate with Google.")
    print("Sign in and authorize rclone when prompted.")
    input("\nPress Enter to open the browser...")

    setup_remote('gdrive', 'drive', extra_args=['scope', 'drive'])

    gd_cfg = read_remote_config('gdrive')
    if not gd_cfg.get('token'):
        print("ERROR: Google Drive token not found after setup.")
        print("Debug with: rclone config show gdrive")
        sys.exit(1)
    print("✓ Google Drive token captured")

    # ── Build .env ────────────────────────────────────────────
    banner("Writing .env")

    env = {
        # Application
        'ELEVENLABS_API_KEY':     elevenlabs_key,
        'ONEDRIVE_REMOTE':        f'onedrive:{onedrive_folder}',
        'GDRIVE_REMOTE':          f'gdrive:{gdrive_folder}',
        'POLL_INTERVAL_SECONDS':  poll_interval,
        # OneDrive rclone config (used by rclone via env vars, no config file needed)
        'RCLONE_CONFIG_ONEDRIVE_TYPE':  'onedrive',
        'RCLONE_CONFIG_ONEDRIVE_TOKEN': od_cfg['token'],
    }
    # drive_id is intentionally omitted — it can point to an invalid SharePoint
    # handle for personal accounts. rclone works fine without it.

    # Google Drive rclone config
    env['RCLONE_CONFIG_GDRIVE_TYPE']  = 'drive'
    env['RCLONE_CONFIG_GDRIVE_SCOPE'] = gd_cfg.get('scope', 'drive')
    env['RCLONE_CONFIG_GDRIVE_TOKEN'] = gd_cfg['token']

    write_env(env)
    print("✓ .env written")

    # ── Next steps ────────────────────────────────────────────
    print()
    print("All done! Next steps:")
    print()
    print("  Run locally:")
    print("    python main.py")
    print()
    print("  Deploy to Coolify:")
    print("    Copy each line from .env into Coolify → Environment Variables.")
    print("    The RCLONE_CONFIG_* vars replace the need for an rclone.conf file.")
    print()
    print("  ⚠  .env contains OAuth tokens — keep it secret, never commit it.")


if __name__ == '__main__':
    main()
