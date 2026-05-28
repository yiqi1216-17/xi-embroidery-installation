import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xi_embroidery.orchestrator.controller import PerceptionController
from xi_embroidery.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="锡绣装置 — 感知识别端")
    parser.add_argument("--mode", choices=["accurate", "fast"], default="accurate")
    args = parser.parse_args()

    settings = load_settings(args.mode)
    controller = PerceptionController(settings)
    controller.setup()
    controller.run()


if __name__ == "__main__":
    main()
