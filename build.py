
import PyInstaller.__main__
import customtkinter
import os
import shutil

def build():
    # Clean previous builds
    print("[*] Cleaning up...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"[*] CustomTkinter path: {ctk_path}")

    # Separator for --add-data
    sep = ";" if os.name == 'nt' else ":"

    print("[*] Starting PyInstaller build...")
    
    # Find faster_whisper path
    import faster_whisper
    fw_path = os.path.dirname(faster_whisper.__file__)
    print(f"[*] Faster Whisper path: {fw_path}")

    args = [
        "gui.py",
        "--name=FasterWhisperSRT",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        # Add CustomTkinter data
        "--add-data", f"{ctk_path}{sep}customtkinter",
        # Add Faster Whisper assets (VAD model)
        "--add-data", f"{os.path.join(fw_path, 'assets')}{sep}faster_whisper/assets",
        # Add our core script
        "--add-data", f"faster_whisper_srt.py{sep}.",
        # Hidden imports needed for the engine
        "--hidden-import", "faster_whisper",
        "--hidden-import", "ctranslate2",
        "--hidden-import", "sklearn.utils._typedefs", # Sometimes needed
        "--hidden-import", "sklearn.neighbors._partition_nodes", # Sometimes needed
    ]

    PyInstaller.__main__.run(args)
    
    print("\n[+] Build Complete!")
    print(f"[+] Output: {os.path.abspath('dist/FasterWhisperSRT/FasterWhisperSRT.exe')}")

if __name__ == "__main__":
    build()
