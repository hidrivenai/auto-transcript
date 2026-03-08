#!/usr/bin/env python3
"""
Interactive setup: authenticates with OneDrive and Google Drive via rclone,
then writes all values to a .env file ready for local use or Coolify deployment.

Usage:
    python setup_env.py
"""

import getpass
import re
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


def authorize_and_get_token(rclone_type):
    """
    Run `rclone authorize <type>` — does ONLY the OAuth browser flow.
    No drive selection, no drive_id issues.
    stderr (progress messages) prints to terminal; stdout is captured for the token.
    """
    result = subprocess.run(
        ['rclone', 'authorize', rclone_type],
        stdout=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: rclone authorize failed for '{rclone_type}'.")
        sys.exit(1)

    stdout = result.stdout

    # rclone prints the token between these markers:
    #   Paste the following into your remote machine --->
    #   {"access_token":"...","refresh_token":"...","expiry":"..."}
    #   <---End paste
    match = re.search(
        r'Paste the following into your remote machine\s*--->\s*(.+?)\s*<---',
        stdout,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Fallback: find any JSON with access_token
    match = re.search(r'\{[^{}]*"access_token"[^{}]*\}', stdout)
    if match:
        return match.group(0).strip()

    return None


def create_remote_with_token(name, rclone_type, token, extra_config=None):
    """Create rclone remote directly with a pre-obtained token (no interactive prompts)."""
    subprocess.run(['rclone', 'config', 'delete', name], capture_output=True)
    cmd = ['rclone', 'config', 'create', name, rclone_type, 'token', token]
    if extra_config:
        for k, v in extra_config.items():
            cmd.extend([k, v])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Failed to create '{name}' remote: {result.stderr}")
        sys.exit(1)


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
    print("Your browser will open to authenticate with Microsoft.")
    print("Sign in and authorize rclone when prompted.")
    input("\nPress Enter to open the browser...")

    od_token = authorize_and_get_token('onedrive')
    if not od_token:
        print("ERROR: Could not capture OneDrive token from rclone output.")
        print("Try running 'rclone authorize onedrive' manually and copy the token.")
        sys.exit(1)
    print("✓ OneDrive token captured")

    # Create the remote with just the token — no drive_id, no drive selection
    create_remote_with_token('onedrive', 'onedrive', od_token)
    print("✓ OneDrive remote configured")

    # ── Google Drive ──────────────────────────────────────────
    banner("Step 2 of 2 — Google Drive authentication")
    print("Your browser will open to authenticate with Google.")
    print("Sign in and authorize rclone when prompted.")
    input("\nPress Enter to open the browser...")

    gd_token = authorize_and_get_token('drive')
    if not gd_token:
        print("ERROR: Could not capture Google Drive token from rclone output.")
        print("Try running 'rclone authorize drive' manually and copy the token.")
        sys.exit(1)
    print("✓ Google Drive token captured")

    create_remote_with_token('gdrive', 'drive', gd_token, extra_config={'scope': 'drive'})
    print("✓ Google Drive remote configured")

    # ── Build .env ────────────────────────────────────────────
    banner("Writing .env")

    env = {
        # Application
        'ELEVENLABS_API_KEY':     elevenlabs_key,
        'ONEDRIVE_REMOTE':        f'onedrive:{onedrive_folder}',
        'GDRIVE_REMOTE':          f'gdrive:{gdrive_folder}',
        'POLL_INTERVAL_SECONDS':  poll_interval,
        # OneDrive rclone config (env vars — no rclone.conf file needed)
        'RCLONE_CONFIG_ONEDRIVE_TYPE':  'onedrive',
        'RCLONE_CONFIG_ONEDRIVE_TOKEN': od_token,
        # Google Drive rclone config
        'RCLONE_CONFIG_GDRIVE_TYPE':  'drive',
        'RCLONE_CONFIG_GDRIVE_SCOPE': 'drive',
        'RCLONE_CONFIG_GDRIVE_TOKEN': gd_token,
    }

    write_env(env)
    print("✓ .env written")

    # ── Verify ────────────────────────────────────────────────
    banner("Verifying connections")
    for name, remote in [('OneDrive', f'onedrive:{onedrive_folder}'), ('Google Drive', f'gdrive:{gdrive_folder}')]:
        result = subprocess.run(
            ['rclone', 'lsjson', remote, '--max-depth', '0'],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"✓ {name} — connected to {remote}")
        else:
            print(f"⚠ {name} — could not list {remote} (folder may not exist yet)")

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
