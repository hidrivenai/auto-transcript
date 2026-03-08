# audio.py
import subprocess


def get_duration_seconds(file_path: str) -> float:
    """Return duration in seconds using ffprobe, or 0.0 on failure."""
    result = subprocess.run(
        [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path,
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def format_duration(seconds: float) -> str:
    """272.5 -> '4:32'"""
    total = int(seconds)
    m, s = divmod(total, 60)
    return f'{m}:{s:02d}'
