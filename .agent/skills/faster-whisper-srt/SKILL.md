---
name: Faster Whisper SRT Converter
description: This skill should be used when the user asks to "convert audio to srt", "generate subtitles from audio/video", "create srt from mp3/wav/m4a/flac/mp4", "transcribe audio to subtitles", "把音訊轉成字幕", "產生 SRT 字幕檔", or needs to generate SRT subtitle files from audio or video files using the faster-whisper engine with model selection and progress display.
---

# Faster Whisper SRT Converter

## Purpose
Convert audio and video files to SRT subtitle files using the faster-whisper speech recognition engine. Supports multiple Whisper model sizes, real-time progress display, and automatic audio extraction from video files.

## When to Use
- User wants to convert audio files (MP3, WAV, M4A, FLAC, OGG, AAC, WMA) to SRT subtitles
- User wants to extract subtitles from video files (MP4, MKV, AVI, MOV, WEBM, FLV)
- User mentions "transcribe", "subtitles", "SRT", "字幕", "逐字稿"

## Prerequisites
- Python 3.10+
- `faster-whisper` and `tqdm` packages (`pip install -r requirements.txt`)
- FFmpeg (only required for video file input)

## Usage

### Step 1: Run the Script
Execute the conversion script with the target audio or video file:

```bash
python faster_whisper_srt.py <input_file> [--model MODEL] [--max-chars MAX_CHARS]
```

### Step 2: Choose a Model (Optional)
Available models, from fastest to most accurate:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~75 MB | Fastest | Low |
| base | ~145 MB | Fast | Fair |
| small | ~490 MB | Medium | Good |
| **medium** | **~1.5 GB** | **Slow** | **High (default)** |
| large-v3 | ~3.1 GB | Slowest | Highest |
| large-v3-turbo | ~1.6 GB | Medium | High |

### Step 3: Check Output
The output SRT file will be saved in the same directory as the input file, named: `<original_name>_<model>.srt`

## Examples

```bash
# Basic usage (default: medium model, 40 chars per line)
python faster_whisper_srt.py interview.mp3

# Use a fast model for testing
python faster_whisper_srt.py interview.mp3 --model tiny

# Use the best model for final output
python faster_whisper_srt.py interview.mp3 --model large-v3-turbo

# Shorter subtitle lines
python faster_whisper_srt.py interview.mp3 --max-chars 25

# Video file input (requires FFmpeg)
python faster_whisper_srt.py presentation.mp4 --model medium
```

## Notes
- First-time use of a model will trigger an automatic download. Subsequent runs use the cached model.
- The script defaults to Chinese (`zh`) language detection. Modify the `language` parameter in the script for other languages.
- Video processing requires FFmpeg to be installed and available in PATH.
- Audio-only files (MP3, WAV, etc.) do NOT require FFmpeg.
