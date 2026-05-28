from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
CONFIG_DIR = PROJECT_ROOT / "config"
MANIFEST_FILE = ASSETS_DIR / "manifest.json"
OUTPUT_FILE = PROJECT_ROOT / "current_video_path.txt"
BACKGROUND_VIDEO = PROJECT_ROOT / "底图视频4K.mp4"
LOG_DIR = PROJECT_ROOT / "logs"
