"""交互式叠加标定：调整纹样位置/比例并写入 config/overlay_calibration.yaml"""

import argparse

from _bootstrap import *  # noqa: F403

from display.viewer import DisplayViewer, place_overlay, resolve_display_transform
from manifest import load_manifest, pattern_by_id
from settings import load_overlay_calibration, load_settings, save_overlay_calibration


def main() -> None:
    parser = argparse.ArgumentParser(description="纹样叠加标定")
    parser.add_argument("--mode", choices=["exhibition", "dev"], default="exhibition")
    parser.add_argument("--pattern", default="video1")
    parser.add_argument("--frame", type=int, default=1)
    args = parser.parse_args()

    settings = load_settings(args.mode)
    viewer = DisplayViewer(settings)
    pattern = pattern_by_id(viewer.patterns, args.pattern)
    if pattern is None:
        raise SystemExit(f"未知 pattern: {args.pattern}")

    bg = viewer.load_background()
    if bg is None:
        import numpy as np

        bg = np.zeros((viewer.display.height, viewer.display.width, 3), dtype=np.uint8)

    overlay_path = pattern.sequence_frame(args.frame)
    overlay = viewer.load_overlay(overlay_path, pattern.id, pattern)
    if overlay is None:
        raise SystemExit(f"无法加载 {overlay_path}")

    calibration = load_overlay_calibration()
    cal = calibration.setdefault("patterns", {}).setdefault(
        pattern.id, {"scale": 1.0, "offset_x": 0.0, "offset_y": 0.0}
    )

    print("方向键=移动 | +/-=缩放 | s=保存 | q=退出")
    step = 0.01

    while True:
        ox, oy, scale = resolve_display_transform(
            pattern.id, pattern, viewer.display, calibration
        )
        frame = place_overlay(bg.copy(), overlay.copy(), ox, oy, scale)
        import cv2

        cv2.imshow("Calibrate", frame)
        key = cv2.waitKey(30) & 0xFF

        if key == ord("q"):
            break
        if key == ord("s"):
            save_overlay_calibration(calibration)
            print(f"已保存 {pattern.id}")
        elif key in (ord("+"), ord("=")):
            cal["scale"] = float(cal.get("scale", 1.0)) + 0.05
        elif key == ord("-"):
            cal["scale"] = max(0.1, float(cal.get("scale", 1.0)) - 0.05)
        elif key == 81:
            cal["offset_x"] = float(cal.get("offset_x", 0.0)) - step
        elif key == 83:
            cal["offset_x"] = float(cal.get("offset_x", 0.0)) + step
        elif key == 82:
            cal["offset_y"] = float(cal.get("offset_y", 0.0)) + step
        elif key == 84:
            cal["offset_y"] = float(cal.get("offset_y", 0.0)) - step

    import cv2

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
