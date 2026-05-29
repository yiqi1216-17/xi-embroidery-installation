import argparse

from _bootstrap import *  # noqa: F403

from display.viewer import DisplayViewer
from settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="锡绣装置 — 本地显示端")
    parser.add_argument("--mode", choices=["exhibition", "dev"], default="exhibition")
    args = parser.parse_args()

    DisplayViewer(load_settings(args.mode)).run()


if __name__ == "__main__":
    main()
