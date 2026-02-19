# Faster Whisper SRT Converter

一個基於 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 的本地語音辨識工具，將音訊/影片檔案轉換為 SRT 字幕檔。

**特色：**
- 🏠 完全本地執行，不需要 API Key 或雲端服務
- 🎯 支援 12 種 Whisper 模型（tiny → large-v3）
- 📊 即時進度條顯示
- 🎬 支援影片檔案自動擷取音訊
- 📁 輸出檔案自動帶上模型名稱，方便比較
- 🗂️ 支援批次轉換，一次處理多個檔案（模型只載入一次）

---

## 安裝教學（從零開始）

### Step 1：安裝 Python

前往 https://www.python.org/downloads/ 下載 **Python 3.10 ~ 3.12**。

> ⚠️ 安裝時請務必勾選 **「Add Python to PATH」**

驗證：
```bash
python --version
```

### Step 2：安裝 FFmpeg（處理影片用，可選）

如果你只處理 MP3 等音訊檔，可以跳過這一步。

**Windows：**
```powershell
winget install --id "Gyan.FFmpeg" --source winget --accept-package-agreements --accept-source-agreements --silent
```
安裝後**重開終端機**，執行 `ffmpeg -version` 確認。

**macOS：**
```bash
brew install ffmpeg
```

### Step 3：下載本專案

```bash
git clone https://github.com/<YOUR_USERNAME>/faster-whisper-srt.git
cd faster-whisper-srt
```

或直接到 GitHub 頁面點 **Code → Download ZIP** 解壓縮。

### Step 4：安裝 Python 套件

```bash
pip install -r requirements.txt
```

驗證：
```bash
python -c "from faster_whisper import WhisperModel; print('All good!')"
```

---

## 使用方式

```bash
# 基本用法（預設 medium 模型，每行最多 40 字）
python faster_whisper_srt.py your_audio.mp3

# 指定模型
python faster_whisper_srt.py your_audio.mp3 --model large-v3-turbo

# 指定每行最大字數（預設 40，最少 4）
python faster_whisper_srt.py your_audio.mp3 --max-chars 25

# 影片檔案（需要 FFmpeg）
python faster_whisper_srt.py your_video.mp4
```

### 批次轉換（多個檔案）

模型只會載入一次，節省時間和記憶體：

```bash
# 指定多個檔案
python faster_whisper_srt.py a.mp3 b.mp3 c.mp4

# 使用萬用字元（PowerShell / bash 皆支援）
python faster_whisper_srt.py *.mp3 --model large-v3-turbo

# 混合音訊和影片
python faster_whisper_srt.py interview.mp3 presentation.mp4 --model medium
```

執行完成後會顯示摘要：`[+] Done! 3/3 files converted successfully.`

### 輸出

SRT 檔案會產生在**輸入檔案的同一個資料夾**，檔名格式：`原檔名_模型名.srt`

例如：`interview_medium.srt`、`interview_large-v3-turbo.srt`

### 示範

專案附帶一個範例音訊檔 `Colony_Counter_demo.mp3`，你可以直接試跑：

```bash
python faster_whisper_srt.py Colony_Counter_demo.mp3 --model tiny
```

---

## 可用的模型

| 模型 | 大小 | 速度 | 準確度 | 適用場景 |
|------|------|------|--------|----------|
| `tiny` | ~75 MB | ⚡⚡⚡⚡⚡ | ★☆☆☆☆ | 快速測試 |
| `base` | ~145 MB | ⚡⚡⚡⚡ | ★★☆☆☆ | 輕量使用 |
| `small` | ~490 MB | ⚡⚡⚡ | ★★★☆☆ | 日常使用 |
| **`medium`** | **~1.5 GB** | **⚡⚡** | **★★★★☆** | **預設值，平衡首選** |
| `large-v3` | ~3.1 GB | ⚡ | ★★★★★ | 最高精度 |
| `large-v3-turbo` | ~1.6 GB | ⚡⚡⚡ | ★★★★☆ | 速度快且準確 |

> 第一次使用某個模型會自動下載，之後會從快取載入（秒開）。

---

## AI Agent Skill 用法

本專案同時也是一個 AI Agent Skill。如果你使用 Gemini CLI 或其他支援 `.agent/skills/` 的工具，它會自動偵測並在你說「幫我把音訊轉成字幕」時觸發此腳本。

---

## 常見問題

| 問題 | 解法 |
|------|------|
| `python` 找不到 | 確認安裝時有勾「Add Python to PATH」 |
| `pip` 找不到 | 改用 `python -m pip install -r requirements.txt` |
| FFmpeg 找不到 | 重開終端機（或重開電腦）；VS Code 需完全關閉重開 |
| 模型下載卡住 | 大模型需要穩定網路，可先用 `--model tiny` 測試 |
| 字幕不夠準 | 換更大的模型：`medium` → `large-v3-turbo` → `large-v3` |

---

## License

[MIT](LICENSE)
