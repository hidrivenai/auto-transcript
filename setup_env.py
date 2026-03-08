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


def verify_remote(remote, env_vars):
    """Check rclone can list the remote using env-var-based config."""
    import os
    merged = {**os.environ, **env_vars}
    result = subprocess.run(
        ['rclone', 'lsjson', remote, '--max-depth', '0'],
        capture_output=True, text=True, env=merged,
    )
    return result.returncode == 0


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

    # ── Verify (using env vars, no local rclone config needed) ──
    banner("Verifying connections")
    rclone_env = {
        'RCLONE_CONFIG_ONEDRIVE_TYPE': 'onedrive',
        'RCLONE_CONFIG_ONEDRIVE_TOKEN': od_token,
        'RCLONE_CONFIG_GDRIVE_TYPE': 'drive',
        'RCLONE_CONFIG_GDRIVE_SCOPE': 'drive',
        'RCLONE_CONFIG_GDRIVE_TOKEN': gd_token,
    }
    for label, remote in [('OneDrive', f'onedrive:{onedrive_folder}'), ('Google Drive', f'gdrive:{gdrive_folder}')]:
        if verify_remote(remote, rclone_env):
            print(f"✓ {label} — connected to {remote}")
        else:
            print(f"⚠ {label} — could not list {remote} (folder may not exist yet)")

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
