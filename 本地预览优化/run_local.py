"""一键启动本地预览优化版（识别 + 显示）。"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    recognition = subprocess.Popen(
        [sys.executable, str(ROOT / "recognition_control.py")],
        cwd=str(ROOT),
    )
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "display_viewer.py")],
            cwd=str(ROOT),
        )
        raise SystemExit(result.returncode)
    finally:
        recognition.terminate()
        recognition.wait(timeout=5)


if __name__ == "__main__":
    main()
