
@echo off
echo [*] Cleaning up previous builds...
rmdir /s /q dist
rmdir /s /q build
del /q *.spec

echo [*] Building EXE...
pyinstaller --noconfirm --onedir --windowed --name "FasterWhisperSRT" --icon "NONE" --add-data "faster_whisper_srt.py;." --hidden-import "faster_whisper" --hidden-import "ctranslate2" gui.py

echo.
echo [*] Build Complete!
echo    Output: dist\FasterWhisperSRT\FasterWhisperSRT.exe
pause
