
import faster_whisper
import os

print(f"Faster Whisper path: {os.path.dirname(faster_whisper.__file__)}")
assets_path = os.path.join(os.path.dirname(faster_whisper.__file__), "assets")
if os.path.exists(assets_path):
    print(f"Assets found at: {assets_path}")
    print("Files:", os.listdir(assets_path))
else:
    print("Assets directory NOT found.")
