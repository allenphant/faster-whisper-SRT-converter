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

| `large-v3-turbo` | ~1.6 GB | ⚡⚡⚡ | ★★★★☆ | 速度快且準確 |

> 第一次使用某個模型會自動下載，之後會從快取載入（秒開）。

---

## 🖥️ 圖形介面 (GUI) 使用方式

本專案提供簡易的圖形介面，方便不習慣使用指令的使用者。

### 啟動 GUI

```bash
python gui.py
```

### 功能
- **檔案選擇**：支援拖放或點擊 Browse 按鈕選擇多個音訊/影片檔
- **模型選擇**：下拉式選單選擇 Whisper 模型
- **參數調整**：調整每行最大字數
- **進度顯示**：顯示當前處理檔案及進度條
- **日誌視窗**：即時查看執行狀況

---

## 📦 打包成執行檔 (Executable)

本專案支援兩種打包方式：**雲端自動打包 (推薦)** 與 **本地手動打包**。

### 雲端自動打包 (推薦，支援 Windows & macOS)
如果你有自己的 GitHub 儲存庫，本專案已內建 GitHub Actions 工作流。
你只需要：
1. 將程式碼推送到你的 GitHub 儲存庫。
2. 建立一個新的 Tag 標籤（例如 `v1.0.0`）並推送：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. 到 GitHub 頁面的 **Actions** 標籤頁，你會看到系統正在自動幫你打包 Windows 與 macOS 版本。
4. 打包完成後，到 **Releases** 頁面即可下載編譯好的 ZIP 壓縮檔。

> **⚠️ macOS 執行注意**：
> GitHub Actions 產出的 macOS 執行檔未經 Apple 簽章。第一次執行時可能會被擋下，請在該應用程式上按「右鍵」→「打開」來繞過限制。

---

### 本地手動打包

如果你想要在自己的電腦上打包：

#### 1. 安裝打包工具
```bash
pip install -r requirements.txt
```
(確保 `pyinstaller` 和 `customtkinter` 已安裝)

### 2. 執行打包腳本

**Windows：**
```bash
python build.py
```
打包完成後，執行檔會位於 `dist/FasterWhisperSRT/FasterWhisperSRT.exe`。

**macOS：**
由於 macOS 的機制不同，請在 Mac 電腦上執行以下指令來進行打包：
```bash
python build.py
```
這會產生一個 Unix 可執行檔或 `.app` 應用程式包（視 PyInstaller 在 Mac 上的預設行為而定）。

> **⚠️ 注意：無法跨平台打包**
> 你不能在 Windows 上打包給 macOS 用，也不能在 macOS 上打包給 Windows 用。請在目標作業系統上執行 `build.py`。

### 3. 如何分享給別人？

由於我們為了啟動速度與穩定性，採用了**目錄模式 (One-Dir)** 打包：

1.  找到 `dist` 資料夾下的 `FasterWhisperSRT` **整個資料夾**。
2.  將這個資料夾壓縮成 ZIP 檔。
3.  傳送給使用者。
4.  使用者解壓縮後，進入資料夾，雙擊執行 `FasterWhisperSRT.exe` (Windows) 或對應的執行檔 (macOS) 即可使用。
    - **不需要**安裝 Python。
    - **不需要**安裝 FFmpeg (如果程式內有打包，或依賴系統，視情況而定；本專案建議使用者電腦最好還是有裝 FFmpeg，但通常 whisper 函式庫會嘗試內建處理)。

> **注意**：
> - 檔案較大（可能超過 1GB），因為包含了 Python 核心與 AI 模型引擎。
> - 第一次執行時，若遇到防毒軟體警示，屬於 PyInstaller 的常見誤報，請加入例外清單。

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
