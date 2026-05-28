"""在本机一键启动：识别端 + 显示端（无需 TouchDesigner）。"""

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
        display = subprocess.run(
            [sys.executable, str(ROOT / "display_viewer.py")],
            cwd=str(ROOT),
        )
        raise SystemExit(display.returncode)
    finally:
        recognition.terminate()
        recognition.wait(timeout=5)


if __name__ == "__main__":
    main()
