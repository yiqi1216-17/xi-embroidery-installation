"""本地显示端：替代 TouchDesigner，在 OpenCV 窗口里播放底图并叠加序列帧。"""

import time
from pathlib import Path

import cv2
import numpy as np

from project_paths import BACKGROUND_VIDEO, OUTPUT_FILE

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720


def parse_output_line(line: str) -> tuple[str, float, float, Path] | None:
    line = line.strip()
    if not line:
        return None
    parts = line.split(",")
    if len(parts) < 4:
        return None
    label = parts[0]
    x = float(parts[1])
    y = float(parts[2])
    image_path = Path(",".join(parts[3:]))
    return label, x, y, image_path


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
        bg_region = background[y1:y2, x1:x2].astype(np.float32)
        background[y1:y2, x1:x2] = (rgb * alpha + bg_region * (1.0 - alpha)).astype(np.uint8)
    else:
        background[y1:y2, x1:x2] = fg_crop[:, :, :3]

    return background


def place_overlay(background: np.ndarray, overlay: np.ndarray, x_norm: float, y_norm: float) -> np.ndarray:
    bg_h, bg_w = background.shape[:2]
    overlay_h, overlay_w = overlay.shape[:2]

    center_x = bg_w // 2 + int(x_norm * bg_w)
    center_y = bg_h // 2 + int(-y_norm * bg_h)
    top_left_x = center_x - overlay_w // 2
    top_left_y = center_y - overlay_h // 2

    return overlay_rgba(background, overlay, top_left_x, top_left_y)


def read_background_frame(cap: cv2.VideoCapture) -> np.ndarray:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
    if not ret:
        frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
    return cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))


def main() -> None:
    if not BACKGROUND_VIDEO.exists():
        print(f"警告：找不到底图视频 {BACKGROUND_VIDEO}，将使用黑底。")
        cap = None
    else:
        cap = cv2.VideoCapture(str(BACKGROUND_VIDEO))
        if not cap.isOpened():
            print(f"警告：无法打开 {BACKGROUND_VIDEO}，将使用黑底。")
            cap = None

    cached_path: Path | None = None
    cached_overlay: np.ndarray | None = None
    cached_x = 0.0
    cached_y = 0.0
    last_mtime = 0.0

    print("显示端已启动。")
    print(f"读取文件: {OUTPUT_FILE}")
    print("按 q 退出。")

    while True:
        frame = read_background_frame(cap) if cap is not None else np.zeros(
            (DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8
        )

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
                        overlay = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
                        if overlay is None:
                            print(f"无法加载叠加图: {image_path}")
                        else:
                            cached_path = image_path
                            cached_overlay = overlay
                            print(f"当前显示: {label} @ ({cached_x}, {cached_y}) -> {image_path.name}")

        if cached_overlay is not None:
            frame = place_overlay(frame, cached_overlay, cached_x, cached_y)

        cv2.imshow("Display", frame)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
