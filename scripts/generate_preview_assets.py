"""生成 assets/preview/ 轻量资源（720p），供 dev 模式本地开发。"""

from _bootstrap import *  # noqa: F403

from pathlib import Path

import cv2

from paths import ASSETS_DIR, BACKGROUND_VIDEO, PREVIEW_ASSETS_DIR

MAX_SIDE = 1280


def resize_file(src: Path, dst: Path) -> None:
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"跳过: {src}")
        return
    h, w = img.shape[:2]
    scale = min(1.0, MAX_SIDE / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst), img)
    print(f"  {src.name} -> {dst.name}")


def main() -> None:
    PREVIEW_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"生成 preview 到 {PREVIEW_ASSETS_DIR}")

    for src in sorted(ASSETS_DIR.glob("image*.png")):
        resize_file(src, PREVIEW_ASSETS_DIR / src.name)
    for src in sorted(ASSETS_DIR.glob("video*-*.png")):
        resize_file(src, PREVIEW_ASSETS_DIR / src.name)

    if BACKGROUND_VIDEO.exists():
        cap = cv2.VideoCapture(str(BACKGROUND_VIDEO))
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(PREVIEW_ASSETS_DIR / "background.jpg"), frame)
            print("  底图视频首帧 -> background.jpg")

    print("完成。")


if __name__ == "__main__":
    main()
