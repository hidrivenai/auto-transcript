# Voice Memo Auto-Transcriber

Watches an OneDrive folder for iPhone Voice Memos (`.m4a`), transcribes them with [ElevenLabs Scribe v2](https://elevenlabs.io), and writes Obsidian-ready markdown notes to a Google Drive folder.

## Quick setup

Run the interactive setup script on your local machine (browser required):

```bash
python setup_env.py
```

It will ask for your API key and folder paths, open your browser twice to authenticate with Microsoft and Google, then write a ready-to-use `.env` file.

## How it works

1. Every 5 minutes, lists `.m4a` files in your OneDrive folder
2. Compares against `.md` files already in your Google Drive folder (filename-based deduplication — no database)
3. Downloads new recordings, transcribes with ElevenLabs, writes a markdown note with YAML frontmatter
4. Uploads the note to Google Drive

Each note looks like:

```
---
date: 2026-03-08
duration: 4:32
speakers: 2
source_file: My Recording.m4a
place: Budapest
---

Full transcript text here...
```

## Deploy with Coolify

### Prerequisites

- A [Coolify](https://coolify.io) instance
- This repo pushed to GitHub/GitLab
- An [ElevenLabs](https://elevenlabs.io) account with API key (paid plan for Scribe v2)
- `rclone` installed locally (for generating OAuth tokens)

### Step 1 — Generate your .env with the setup script

Run on your local machine (browser required):

```bash
python setup_env.py
```

The script authenticates with both OneDrive and Google Drive via rclone and writes all required values — including OAuth tokens — to `.env`.

> **Prerequisites:** `rclone` must be installed locally. Install from https://rclone.org/install/

### Step 2 — Deploy in Coolify

1. In Coolify, create a new **Resource → Application**
2. Connect your GitHub/GitLab repo
3. Set build pack to **Dockerfile**
4. Add the following environment variables:

| Variable | Example value | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | `sk_...` | Your ElevenLabs API key |
| `ONEDRIVE_REMOTE` | `onedrive:Personal/VoiceNotes` | OneDrive remote name + folder path |
| `GDRIVE_REMOTE` | `gdrive:ObsidianVault/Voice Transcripts` | GDrive remote name + folder path |
| `POLL_INTERVAL_SECONDS` | `300` | How often to check for new recordings (seconds) |
| `RCLONE_CONFIG_ONEDRIVE_TYPE` | `onedrive` | rclone remote type for OneDrive |
| `RCLONE_CONFIG_ONEDRIVE_TOKEN` | `{"access_token":"...","refresh_token":"...","expiry":"..."}` | OAuth token JSON from rclone.conf |
| `RCLONE_CONFIG_ONEDRIVE_DRIVE_ID` | `b!abc123...` | drive_id from rclone.conf |
| `RCLONE_CONFIG_ONEDRIVE_DRIVE_TYPE` | `personal` | drive_type from rclone.conf |
| `RCLONE_CONFIG_GDRIVE_TYPE` | `drive` | rclone remote type for Google Drive |
| `RCLONE_CONFIG_GDRIVE_SCOPE` | `drive` | OAuth scope |
| `RCLONE_CONFIG_GDRIVE_TOKEN` | `{"access_token":"...","refresh_token":"...","expiry":"..."}` | OAuth token JSON from rclone.conf |

> **Note on remote names:** The remote name in `ONEDRIVE_REMOTE` and `GDRIVE_REMOTE` must match the env var prefix. If `ONEDRIVE_REMOTE=onedrive:...` then the env vars are `RCLONE_CONFIG_ONEDRIVE_*`. If you named your remote `mycloud`, use `RCLONE_CONFIG_MYCLOUD_*`.

5. Deploy. Check logs in Coolify — you should see:
   ```
   Starting. Poll interval: 300s
   No new recordings.
   ```

### Token refresh

rclone automatically refreshes OAuth tokens using the `refresh_token`. As long as you don't revoke access in Microsoft/Google account settings, the token stays valid indefinitely.

If a token expires or is revoked, re-run `rclone config reconnect onedrive:` or `rclone config reconnect gdrive:` locally and update the `RCLONE_CONFIG_*_TOKEN` env var in Coolify.

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your values + run rclone config locally
python main.py
```

Run tests:

```bash
pytest tests/ -v
```

## Environment variables reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `ELEVENLABS_API_KEY` | Yes | — | ElevenLabs API key |
| `ONEDRIVE_REMOTE` | Yes | — | rclone remote path for source folder (e.g. `onedrive:VoiceNotes`) |
| `GDRIVE_REMOTE` | Yes | — | rclone remote path for output folder (e.g. `gdrive:Obsidian/Transcripts`) |
| `POLL_INTERVAL_SECONDS` | No | `300` | Polling interval in seconds |
