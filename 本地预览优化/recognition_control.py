import threading
import time

import cv2

from config import (
    CAMERA_HEIGHT,
    CAMERA_PREVIEW_WIDTH,
    CAMERA_WIDTH,
    MATCH_INTERVAL_SEC,
    RECOGNITION_MODE,
    SIMILARITY_THRESHOLD,
)
from image_matcher import ImageRecognitionSystem
from project_paths import ASSETS_DIR, OUTPUT_FILE

recognition_system = ImageRecognitionSystem(similarity_threshold=SIMILARITY_THRESHOLD)
print(
    f"[预览优化] 模式 {RECOGNITION_MODE}, 后台识别间隔 {MATCH_INTERVAL_SEC}s, "
    f"摄像头采集 {CAMERA_WIDTH}x{CAMERA_HEIGHT}"
)

image_coordinates = {
    "video1": "video1,0.06,-0.04",
    "video2": "video2,-0.18,0.155",
    "video3": "video3,0.25,-0.2",
    "video4": "video4,-0.42,0.03",
    "video5": "video5,-0.01,0.09",
    "video6": "video6,-0.07,0.185",
    "video7": "video7,-0.26,0.12",
    "video8": "video8,-0.27,-0.02",
    "video9": "video9,0.15,0.14",
    "video10": "video10,-0.03,-0.14",
    "video11": "video11,0.34,-0.02",
    "video12": "video12,0.42,0.11",
    "video13": "video13,-0.25,-0.158",
}


def write_output(label: str, index: int) -> None:
    path = ASSETS_DIR / f"{label}-{index}.png"
    name_with_coordinates = image_coordinates.get(label, label)
    OUTPUT_FILE.write_text(f"{name_with_coordinates},{path}", encoding="utf-8")
    print(f"已写入: {name_with_coordinates},{path}")


current_sequence = {
    "label": None,
    "index": 1,
    "last_update": 0,
    "active": False,
}

latest_frame = None
frame_lock = threading.Lock()
running = True


def update_sequence():
    while running:
        time.sleep(1)
        if not current_sequence["active"]:
            continue
        if time.time() - current_sequence["last_update"] >= 5:
            label = current_sequence["label"]
            if label:
                current_sequence["index"] = current_sequence["index"] % 5 + 1
                try:
                    write_output(label, current_sequence["index"])
                except OSError as exc:
                    print(f"写入文件时出错: {exc}")
                current_sequence["last_update"] = time.time()


def recognition_worker():
    while running:
        time.sleep(MATCH_INTERVAL_SEC)

        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            continue

        label = recognition_system.match_image(frame)
        if label and current_sequence["label"] != label:
            current_sequence.update(
                label=label, index=1, last_update=time.time(), active=True
            )
            try:
                write_output(label, 1)
            except OSError as exc:
                print(f"写入文件时出错: {exc}")


threading.Thread(target=update_sequence, daemon=True).start()
threading.Thread(target=recognition_worker, daemon=True).start()

print("正在添加参考图像...")
success_list = [
    recognition_system.add_reference_image(str(ASSETS_DIR / f"image{i}.png"), f"video{i}")
    for i in range(1, 14)
]
if not all(success_list):
    print("警告：部分参考图像未加载成功")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    raise SystemExit("错误：无法打开摄像头")

print("开始识别（摄像头预览不等待 SIFT，按 q 退出）...")

while running:
    ret, frame = cap.read()
    if not ret:
        continue

    with frame_lock:
        latest_frame = frame

    h, w = frame.shape[:2]
    preview_w = CAMERA_PREVIEW_WIDTH
    preview_h = int(h * (preview_w / w))
    preview = cv2.resize(frame, (preview_w, preview_h), interpolation=cv2.INTER_AREA)
    cv2.imshow("Camera (preview)", preview)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        running = False
        break

cap.release()
cv2.destroyAllWindows()
print("识别端已退出")
