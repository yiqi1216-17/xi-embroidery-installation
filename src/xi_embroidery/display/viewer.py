from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from xi_embroidery.drivers.file_driver import FileOutputDriver, parse_output_line
from xi_embroidery.paths import BACKGROUND_VIDEO
from xi_embroidery.perception.utils import resize_to_fit
from xi_embroidery.settings import DisplaySettings, Settings


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


def place_overlay(
    background: np.ndarray,
    overlay: np.ndarray,
    x_norm: float,
    y_norm: float,
) -> np.ndarray:
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


class DisplayViewer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.display: DisplaySettings = settings.display  # type: ignore[assignment]
        self.output = FileOutputDriver()

    def load_background(self) -> np.ndarray | None:
        if not BACKGROUND_VIDEO.exists():
            print(f"警告: 找不到 {BACKGROUND_VIDEO}")
            return None

        cap = cv2.VideoCapture(str(BACKGROUND_VIDEO))
        if not cap.isOpened():
            return None

        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None

        return cv2.resize(
            frame,
            (self.display.width, self.display.height),
            interpolation=cv2.INTER_AREA,
        )

    def load_overlay(self, image_path: Path) -> np.ndarray | None:
        overlay = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if overlay is None:
            return None

        max_w = int(self.display.width * self.display.overlay_max_width_ratio)
        max_h = int(self.display.height * self.display.overlay_max_height_ratio)
        return resize_to_fit(overlay, max_w, max_h)

    def run(self) -> None:
        static_bg = self.load_background()
        cached_path: Path | None = None
        cached_overlay: np.ndarray | None = None
        cached_x = 0.0
        cached_y = 0.0
        last_mtime = 0.0

        print("[display] 已启动，按 q 退出")

        while True:
            if static_bg is not None:
                frame = static_bg.copy()
            else:
                frame = np.zeros((self.display.height, self.display.width, 3), dtype=np.uint8)

            output_file = self.output.output_file
            if output_file.exists():
                mtime = output_file.stat().st_mtime
                if mtime != last_mtime:
                    last_mtime = mtime
                    parsed = parse_output_line(output_file.read_text(encoding="utf-8"))
                    if parsed is not None:
                        label, cached_x, cached_y, image_path = parsed
                        if image_path != cached_path or cached_overlay is None:
                            cached_overlay = self.load_overlay(image_path)
                            if cached_overlay is not None:
                                cached_path = image_path
                                print(f"[display] {label} -> {image_path.name}")

            if cached_overlay is not None:
                frame = place_overlay(frame, cached_overlay, cached_x, cached_y)

            cv2.imshow("Display", frame)
            if cv2.waitKey(30) & 0xFF == ord("q"):
                break

        cv2.destroyAllWindows()
