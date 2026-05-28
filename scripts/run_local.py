import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="锡绣装置 — 一键启动识别 + 显示")
    parser.add_argument("--mode", choices=["accurate", "fast"], default="accurate")
    args = parser.parse_args()

    perception = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "run_perception.py"), "--mode", args.mode],
        cwd=str(ROOT),
    )
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_display.py"), "--mode", args.mode],
            cwd=str(ROOT),
        )
        raise SystemExit(result.returncode)
    finally:
        perception.terminate()
        perception.wait(timeout=5)


if __name__ == "__main__":
    main()
