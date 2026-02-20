
import sys
import os
import time

print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
try:
    import customtkinter
    print("customtkinter imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    import PyInstaller
    print("PyInstaller imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")

with open("env_check_log.txt", "w") as f:
    f.write(f"Python: {sys.executable}\n")
