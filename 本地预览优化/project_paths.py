from pathlib import Path

# 脚本在 本地预览优化/ 下，资源仍用上级 TD_project 目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_FILE = PROJECT_ROOT / "current_video_path.txt"
BACKGROUND_VIDEO = PROJECT_ROOT / "底图视频4K.mp4"
