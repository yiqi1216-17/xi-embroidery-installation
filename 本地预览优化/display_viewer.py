"""本地显示端（预览优化版）。"""

from pathlib import Path

import cv2
import numpy as np

from config import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    OVERLAY_MAX_HEIGHT_RATIO,
    OVERLAY_MAX_WIDTH_RATIO,
    USE_STATIC_BACKGROUND,
)
from image_utils import resize_to_fit
from project_paths import BACKGROUND_VIDEO, OUTPUT_FILE


def parse_output_line(line: str) -> tuple[str, float, float, Path] | None:
    line = line.strip()
    if not line:
        return None
    parts = line.split(",")
    if len(parts) < 4:
        return None
    return parts[0], float(parts[1]), float(parts[2]), Path(",".join(parts[3:]))


def overlay_rgba(background: np.ndarray, foreground: np.ndarray, x: int, y: int) -> np.ndarray:
    fg_h, fg_w = foreground.shape[:2]
    bg_h, bg_w = background.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_w, x + fg_w), min(bg_h, y + fg_h)
    if x1 >= x2 or y1 >= y2:
        return background

    fg_x1, fg_y1 = x1 - x, y1 - y
    fg_crop = foreground[fg_y1 : fg_y1 + (y2 - y1), fg_x1 : fg_x1 + (x2 - x1)]

    if fg_crop.ndim == 3 and fg_crop.shape[2] == 4:
        alpha = fg_crop[:, :, 3:4].astype(np.float32) / 255.0
        rgb = fg_crop[:, :, :3].astype(np.float32)
        region = background[y1:y2, x1:x2].astype(np.float32)
        background[y1:y2, x1:x2] = (rgb * alpha + region * (1.0 - alpha)).astype(np.uint8)
    else:
        background[y1:y2, x1:x2] = fg_crop[:, :, :3]
    return background


def place_overlay(background: np.ndarray, overlay: np.ndarray, x_norm: float, y_norm: float) -> np.ndarray:
    bg_h, bg_w = background.shape[:2]
    overlay_h, overlay_w = overlay.shape[:2]
    center_x = bg_w // 2 + int(x_norm * bg_w)
    center_y = bg_h // 2 + int(-y_norm * bg_h)
    return overlay_rgba(
        background,
        overlay,
        center_x - overlay_w // 2,
        center_y - overlay_h // 2,
    )


def load_background() -> np.ndarray | None:
    if not BACKGROUND_VIDEO.exists():
        print(f"警告：找不到 {BACKGROUND_VIDEO}")
        return None

    cap = cv2.VideoCapture(str(BACKGROUND_VIDEO))
    if not cap.isOpened():
        print(f"警告：无法打开 {BACKGROUND_VIDEO}")
        return None

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None

    frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT), interpolation=cv2.INTER_AREA)
    mode = "静态首帧" if USE_STATIC_BACKGROUND else "逐帧解码"
    print(f"[预览优化] 底图 {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} ({mode})")
    return frame


def load_overlay(image_path: Path) -> np.ndarray | None:
    overlay = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if overlay is None:
        print(f"无法加载: {image_path}")
        return None

    max_w = int(DISPLAY_WIDTH * OVERLAY_MAX_WIDTH_RATIO)
    max_h = int(DISPLAY_HEIGHT * OVERLAY_MAX_HEIGHT_RATIO)
    before = overlay.shape[:2]
    overlay = resize_to_fit(overlay, max_w, max_h)
    after = overlay.shape[:2]
    print(
        f"纹样缩放: {before[1]}x{before[0]} -> {after[1]}x{after[0]} "
        f"(约占底图 {after[1]/DISPLAY_WIDTH:.0%} 宽)"
    )
    return overlay


def main() -> None:
    static_bg = load_background()
    cached_path: Path | None = None
    cached_overlay: np.ndarray | None = None
    cached_x = 0.0
    cached_y = 0.0
    last_mtime = 0.0

    print("显示端已启动，按 q 退出。")

    while True:
        if static_bg is not None:
            frame = static_bg.copy()
        else:
            frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)

        if OUTPUT_FILE.exists():
            mtime = OUTPUT_FILE.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                try:
                    parsed = parse_output_line(OUTPUT_FILE.read_text(encoding="utf-8"))
                except OSError as exc:
                    print(f"读取输出文件失败: {exc}")
                    parsed = None

                if parsed is not None:
                    label, cached_x, cached_y, image_path = parsed
                    if image_path != cached_path or cached_overlay is None:
                        cached_overlay = load_overlay(image_path)
                        if cached_overlay is not None:
                            cached_path = image_path
                            print(f"当前显示: {label} -> {image_path.name}")

        if cached_overlay is not None:
            frame = place_overlay(frame, cached_overlay, cached_x, cached_y)

        cv2.imshow("Display (preview)", frame)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
