"""离线识别测试：用 assets/image*.png 作为输入，不依赖摄像头。"""

import argparse

import cv2

from _bootstrap import *  # noqa: F403

from manifest import load_manifest
from orchestrator.controller import PerceptionController
from settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="离线识别测试")
    parser.add_argument("--mode", choices=["exhibition", "dev"], default="exhibition")
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    settings = load_settings(args.mode)
    if args.threshold is not None:
        settings.similarity_threshold = args.threshold

    controller = PerceptionController(settings)
    controller.setup()
    assert controller.matcher is not None

    patterns = load_manifest(use_preview=settings.perception.use_preview_assets)  # type: ignore[union-attr]
    passed = failed = 0

    print(f"离线测试 mode={args.mode}，共 {len(patterns)} 张\n")

    for pattern in patterns:
        frame = cv2.imread(str(pattern.reference_image()))
        if frame is None:
            print(f"SKIP {pattern.id}")
            failed += 1
            continue

        result = controller.match_frame_offline(frame)
        ok = result is not None and result.label == pattern.id
        conf = f"{result.confidence:.4f}" if result else "—"
        got = result.label if result else "None"
        print(f"{'PASS' if ok else 'FAIL'} {pattern.id}: got={got} conf={conf}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1

    print(f"\n结果: {passed} 通过, {failed} 失败")
    raise SystemExit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
