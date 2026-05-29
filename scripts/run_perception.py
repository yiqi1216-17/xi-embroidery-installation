import argparse

from _bootstrap import *  # noqa: F403

from orchestrator.controller import PerceptionController
from settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="锡绣装置 — 感知识别端")
    parser.add_argument("--mode", choices=["exhibition", "dev"], default="exhibition")
    args = parser.parse_args()

    controller = PerceptionController(load_settings(args.mode))
    controller.setup()
    controller.run()


if __name__ == "__main__":
    main()
