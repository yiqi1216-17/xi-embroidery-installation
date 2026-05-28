from image_matcher import ImageRecognitionSystem
import cv2
import time
import threading

from project_paths import ASSETS_DIR, OUTPUT_FILE

# ===================== 输入/输出说明=====================
# 输入（Input）：
# 1) 摄像头画面：使用 `cv2.VideoCapture(0)` 读取实时帧（BGR 图像）。
# 2) 参考图像：程序启动时加载 `assets/image1.png ~ image13.png`，
#    并把它们分别标记为 label = "video1" ~ "video13"（用于 SIFT 特征匹配）。
# 3) 阈值：`similarity_threshold` 决定“匹配到就返回 label”还是返回 None。
#
# 输出（Output）：
# 1) 写文件输出：持续把当前识别到的序列信息写入 `current_video_path.txt`。
# 2) 可视化输出：在窗口 `"Camera"` 显示摄像头画面（可选观察识别效果）。
# =================================================================

recognition_system = ImageRecognitionSystem(similarity_threshold=0.05)
print("图像识别系统已初始化，相似度阈值设置为:", 0.05)

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
print("图像坐标信息已配置")


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


def update_sequence():
    while True:
        time.sleep(1)

        if not current_sequence["active"]:
            continue

        current_time = time.time()
        if current_time - current_sequence["last_update"] >= 5:
            label = current_sequence["label"]
            if label:
                current_sequence["index"] = current_sequence["index"] % 5 + 1
                try:
                    write_output(label, current_sequence["index"])
                except OSError as exc:
                    print(f"写入文件时出错: {exc}")
                current_sequence["last_update"] = current_time


update_thread = threading.Thread(target=update_sequence, daemon=True)
update_thread.start()

print("正在添加参考图像...")
success_list = []
for i in range(1, 14):
    label = f"video{i}"
    success_list.append(
        recognition_system.add_reference_image(str(ASSETS_DIR / f"image{i}.png"), label)
    )

if not all(success_list):
    print("警告：部分参考图像可能未成功加载，请检查 assets 目录")
else:
    print("所有13个参考图像已成功加载")

print("正在打开摄像头...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("错误：无法打开摄像头")
else:
    print("摄像头已成功打开")

frame_count = 0
match_count = 0

print("开始图像识别循环，按 'q' 键退出...")
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头帧")
        continue

    frame_count += 1
    if frame_count % 30 == 0:
        print(f"已处理 {frame_count} 帧图像，匹配成功 {match_count} 次")

    label = recognition_system.match_image(frame)

    if label:
        match_count += 1

        if current_sequence["label"] != label:
            current_sequence["label"] = label
            current_sequence["index"] = 1
            current_sequence["last_update"] = time.time()
            current_sequence["active"] = True

            print(f"匹配成功！标签: {label}")
            try:
                write_output(label, current_sequence["index"])
            except OSError as exc:
                print(f"写入文件时出错: {exc}")

    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("用户按下 'q' 键，程序退出")
        break

print("释放资源...")
cap.release()
cv2.destroyAllWindows()
print(f"程序结束。总共处理 {frame_count} 帧图像，匹配成功 {match_count} 次")
