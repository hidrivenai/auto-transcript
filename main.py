# main.py
import logging
import os
import tempfile
import time

from audio import get_duration_seconds, format_duration
from config import load_config
from format_note import build_note, format_diarized_transcript, parse_place_from_stem
from rclone_ops import list_files, download_file, upload_file
from stems import find_unprocessed, stem_from_m4a

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


def process_one(filename: str, mod_time: str, cfg: dict) -> None:
    """Download, transcribe, format, and upload a single recording."""
    from transcribe import transcribe_file

    stem = stem_from_m4a(filename)
    date = mod_time[:10]  # '2026-03-08T10:00:00Z' -> '2026-03-08'
    out_filename = f'{date} {stem}.md'

    log.info(f'Processing: {filename}')

    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(cfg['onedrive_remote'], filename, tmp_path)
        log.info(f'Downloaded to {tmp_path}')

        duration_secs = get_duration_seconds(tmp_path)
        duration_str = format_duration(duration_secs)

        result = transcribe_file(tmp_path, api_key=cfg['elevenlabs_api_key'])
        log.info(f'Transcribed: {len(result["text"])} chars, {result["speakers"]} speaker(s)')

        place = parse_place_from_stem(stem)
        if result['speakers'] > 1:
            transcript = format_diarized_transcript(result['words'])
        else:
            transcript = result['text']
        note = build_note(
            stem=stem,
            date=date,
            duration_str=duration_str,
            speakers=result['speakers'],
            transcript=transcript,
            place=place,
        )

        with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w', encoding='utf-8') as md_tmp:
            md_tmp.write(note)
            md_tmp_path = md_tmp.name

        try:
            upload_file(md_tmp_path, cfg['gdrive_remote'], out_filename)
            log.info(f'Uploaded: {out_filename}')
        finally:
            os.unlink(md_tmp_path)

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_once(cfg: dict) -> None:
    """One poll cycle: list, diff, process new files."""
    gdrive_files = list_files(cfg['gdrive_remote'])
    onedrive_files = list_files(cfg['onedrive_remote'])

    md_names = [f['name'] for f in gdrive_files if f['name'].endswith('.md')]
    m4a_files = [f for f in onedrive_files if f['name'].endswith('.m4a')]
    m4a_names = [f['name'] for f in m4a_files]

    new_names = find_unprocessed(m4a_names, md_names)

    if not new_names:
        log.info('No new recordings.')
        return

    mod_time_map = {f['name']: f['mod_time'] for f in m4a_files}
    for filename in new_names:
        try:
            process_one(filename, mod_time_map[filename], cfg)
        except Exception as e:
            log.error(f'Failed to process {filename}: {e}')


def main() -> None:
    cfg = load_config()
    log.info(f'Starting. Poll interval: {cfg["poll_interval"]}s')
    while True:
        try:
            run_once(cfg)
        except Exception as e:
            log.error(f'Poll cycle error: {e}')
        time.sleep(cfg['poll_interval'])


if __name__ == '__main__':
    main()
