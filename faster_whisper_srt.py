#!/usr/bin/env python3
"""
Faster-Whisper SRT Converter
=============================
將音訊/影片檔案轉換為 SRT 字幕檔，使用 faster-whisper 語音辨識引擎。
支援模型選擇、進度條顯示、影片自動擷取音訊。

Usage:
    python faster_whisper_srt.py <input_file> [--model MODEL] [--max-chars MAX_CHARS]

Examples:
    python faster_whisper_srt.py demo.mp3
    python faster_whisper_srt.py demo.mp4 --model large-v3-turbo
    python faster_whisper_srt.py demo.wav --max-chars 30

Available Models:
    tiny, tiny.en, base, base.en, small, small.en,
    medium, medium.en, large-v1, large-v2, large-v3, large-v3-turbo
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import warnings
from datetime import timedelta
from pathlib import Path

# Suppress noisy huggingface_hub warnings (symlinks + unauthenticated requests)
# These are harmless for local use and clutter the terminal output.
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*symlinks.*")
warnings.filterwarnings("ignore", message=".*unauthenticated.*")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

VALID_MODELS = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large-v1", "large-v2", "large-v3",
    "large-v3-turbo",
]

# Estimated model sizes in MB (for download progress estimation)
MODEL_SIZES_MB = {
    "tiny": 75, "tiny.en": 75,
    "base": 145, "base.en": 145,
    "small": 490, "small.en": 490,
    "medium": 1500, "medium.en": 1500,
    "large-v1": 3100, "large-v2": 3100, "large-v3": 3100,
    "large-v3-turbo": 1600,
}

# ---------------------------------------------------------------------------
# Environment Checks
# ---------------------------------------------------------------------------


def check_ffmpeg():
    """Check if FFmpeg is available on the system."""
    if shutil.which("ffmpeg") is None:
        print("[!] FFmpeg is not installed.")
        print("    Windows:  winget install --id Gyan.FFmpeg --source winget")
        print("    macOS:    brew install ffmpeg")
        sys.exit(1)


def check_faster_whisper():
    """Check if faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        print("[!] faster-whisper is not installed.")
        print("    Install with: pip install faster-whisper")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Audio Helpers
# ---------------------------------------------------------------------------


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio from a video file to a temporary WAV file."""
    temp_dir = tempfile.mkdtemp()
    temp_audio = os.path.join(temp_dir, "extracted_audio.wav")

    print(f"[*] Extracting audio from video: {Path(video_path).name}")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",                  # no video
                "-acodec", "pcm_s16le", # WAV format
                "-ar", "16000",         # 16kHz (Whisper optimal)
                "-ac", "1",             # mono
                "-y",                   # overwrite
                temp_audio,
            ],
            capture_output=True,
            check=True,
        )
        print("[+] Audio extraction complete.")
        return temp_audio
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to extract audio: {e.stderr.decode() if e.stderr else e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# SRT Formatting
# ---------------------------------------------------------------------------


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_text_by_chars(text: str, max_chars: int, min_chars: int = 4) -> list:
    """Split text into chunks based on character limit."""
    if len(text) <= max_chars:
        return [text]

    lines = []
    current = ""

    for char in text:
        current += char
        if len(current) >= max_chars:
            lines.append(current)
            current = ""

    if current:
        # Merge short trailing chunk with previous line
        if len(current) < min_chars and lines:
            lines[-1] += current
        else:
            lines.append(current)

    return lines


# ---------------------------------------------------------------------------
# Model Loading with Progress Indicator
# ---------------------------------------------------------------------------


def load_model_with_progress(model_name: str):
    """Load a faster-whisper model with a visual progress indicator."""
    from faster_whisper import WhisperModel

    print(f"[*] Analyzing model: {model_name}")

    stop_flag = False
    LINE_WIDTH = 80

    def loading_indicator():
        spinner = "|/-\\"
        i = 0
        cache_dir = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", ""))) / ".cache" / "huggingface" / "hub"
        expected_mb = MODEL_SIZES_MB.get(model_name, 0)
        start_size = 0

        try:
            if cache_dir.exists():
                start_size = sum(f.stat().st_size for f in cache_dir.glob("**/*") if f.is_file())
        except Exception:
            pass

        while not stop_flag:
            current_size = 0
            try:
                if cache_dir.exists():
                    current_size = sum(f.stat().st_size for f in cache_dir.glob("**/*") if f.is_file())
            except Exception:
                pass

            delta_mb = (current_size - start_size) / (1024 * 1024)

            if delta_mb > 1:
                if expected_mb > 0:
                    pct = min(delta_mb / expected_mb * 100, 99)
                    msg = f"[*] Downloading model... {spinner[i % 4]}  {delta_mb:.0f} / ~{expected_mb} MB ({pct:.0f}%)"
                else:
                    msg = f"[*] Downloading model... {spinner[i % 4]}  {delta_mb:.0f} MB"
            else:
                msg = f"[*] Loading model... {spinner[i % 4]}"

            sys.stdout.write(f"\r{msg:<{LINE_WIDTH}}")
            sys.stdout.flush()
            time.sleep(0.5)
            i += 1

        sys.stdout.write(f"\r{'':<{LINE_WIDTH}}\r")
        sys.stdout.flush()

    t = threading.Thread(target=loading_indicator, daemon=True)
    t.start()

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    finally:
        stop_flag = True
        t.join(timeout=1.0)

    print("[+] Model loaded successfully.")
    return model


# ---------------------------------------------------------------------------
# Core Transcription
# ---------------------------------------------------------------------------


def transcribe_and_build_srt(
    audio_path: str,
    model,
    model_name: str,
    max_chars: int = 40,
) -> str:
    """Transcribe audio using a pre-loaded faster-whisper model and return SRT content."""
    from tqdm import tqdm

    # --- Get duration for progress bar ---
    total_duration = get_audio_duration(audio_path)
    if total_duration <= 0:
        print("[!] Could not determine audio duration. Progress bar will be approximate.")
        total_duration = 1.0

    # --- Transcribe with progress ---
    print(f"[*] Transcribing: {Path(audio_path).name}")
    segments_iter, info = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=False,
        vad_filter=True,
    )

    srt_lines = []
    subtitle_index = 1

    progress_bar = tqdm(
        total=int(total_duration),
        unit="s",
        desc="Transcribing",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}s [{elapsed}<{remaining}, {rate_fmt}]",
        ncols=80,
    )

    last_pos = 0.0

    for segment in segments_iter:
        text = segment.text.strip()
        if not text:
            continue

        progress = int(segment.end) - int(last_pos)
        if progress > 0:
            progress_bar.update(progress)
            last_pos = segment.end

        lines = split_text_by_chars(text, max_chars)
        duration = segment.end - segment.start
        time_per_line = duration / len(lines) if lines else duration

        for i, line in enumerate(lines):
            start_time = segment.start + (i * time_per_line)
            end_time = segment.start + ((i + 1) * time_per_line)

            srt_lines.append(f"{subtitle_index}")
            srt_lines.append(
                f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}"
            )
            srt_lines.append(line)
            srt_lines.append("")

            subtitle_index += 1

    remaining = int(total_duration) - int(last_pos)
    if remaining > 0:
        progress_bar.update(remaining)
    progress_bar.close()

    return "\n".join(srt_lines)


def process_file(input_path: Path, model, model_name: str, max_chars: int) -> bool:
    """Process a single audio/video file. Returns True on success."""
    ext = input_path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        print(f"[!] Skipping {input_path.name}: unsupported format ({ext})")
        return False

    temp_audio = None
    audio_file = str(input_path)

    if ext in VIDEO_EXTENSIONS:
        check_ffmpeg()
        temp_audio = extract_audio_from_video(str(input_path))
        audio_file = temp_audio

    try:
        srt_content = transcribe_and_build_srt(
            audio_path=audio_file,
            model=model,
            model_name=model_name,
            max_chars=max_chars,
        )
    finally:
        if temp_audio and os.path.exists(temp_audio):
            os.remove(temp_audio)
            temp_dir = os.path.dirname(temp_audio)
            if os.path.isdir(temp_dir):
                os.rmdir(temp_dir)

    output_filename = f"{input_path.stem}_{model_name}.srt"
    output_path = input_path.parent / output_filename
    output_path.write_text(srt_content, encoding="utf-8")
    print(f"[+] SRT file created: {output_path}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Convert audio/video files to SRT subtitles using faster-whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python faster_whisper_srt.py demo.mp3
  python faster_whisper_srt.py a.mp3 b.mp3 c.mp4
  python faster_whisper_srt.py *.mp3 --model large-v3-turbo
  python faster_whisper_srt.py demo.wav --model medium --max-chars 30
        """,
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="One or more audio/video files to convert.",
    )
    parser.add_argument(
        "--model",
        default="medium",
        choices=VALID_MODELS,
        help="Whisper model to use (default: medium).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=40,
        help="Maximum characters per subtitle line (default: 40, minimum: 4).",
    )

    args = parser.parse_args()

    # --- Validate ---
    if args.max_chars < 4:
        print("[!] --max-chars must be at least 4.")
        sys.exit(1)

    check_faster_whisper()

    # --- Collect and validate input files ---
    input_paths = []
    for raw in args.input_files:
        p = Path(raw).resolve()
        if not p.exists():
            print(f"[!] File not found, skipping: {p}")
            continue
        input_paths.append(p)

    if not input_paths:
        print("[!] No valid input files found.")
        sys.exit(1)

    total_files = len(input_paths)

    # --- Load model once for all files ---
    model = load_model_with_progress(args.model)

    # --- Process each file ---
    success_count = 0
    for idx, input_path in enumerate(input_paths, 1):
        if total_files > 1:
            print(f"\n[{idx}/{total_files}] Processing: {input_path.name}")
        success = process_file(input_path, model, args.model, args.max_chars)
        if success:
            success_count += 1

    # --- Summary (only shown for batch jobs) ---
    if total_files > 1:
        print(f"\n[+] Done! {success_count}/{total_files} files converted successfully.")


if __name__ == "__main__":
    main()

