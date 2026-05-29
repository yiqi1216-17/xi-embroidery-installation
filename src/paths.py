from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
PREVIEW_ASSETS_DIR = ASSETS_DIR / "preview"
AUDIO_DIR = ASSETS_DIR / "audio"
CONFIG_DIR = PROJECT_ROOT / "config"
MANIFEST_FILE = ASSETS_DIR / "manifest.json"
OUTPUT_FILE = PROJECT_ROOT / "current_video_path.txt"
BACKGROUND_VIDEO = PROJECT_ROOT / "底图视频4K.mp4"
PREVIEW_BACKGROUND = PREVIEW_ASSETS_DIR / "background.jpg"
OVERLAY_CALIBRATION_FILE = CONFIG_DIR / "overlay_calibration.yaml"
LOG_DIR = PROJECT_ROOT / "logs"
TD_DIR = PROJECT_ROOT / "TD程序"
