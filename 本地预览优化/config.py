"""本地预览可调参数。"""

# "accurate" = 与原版 Python文件/ 一致的识别精度
# "fast"     = 牺牲精度换流畅（手机/斜角拍摄容易认不出）
RECOGNITION_MODE = "accurate"

# ---------- 识别端（accurate 模式会覆盖 fast 参数）----------
MATCH_INTERVAL_SEC = 0.5          # 后台识别间隔；preview 流畅，accuracy 不受影响
SIMILARITY_THRESHOLD = 0.05
VERBOSE_MATCH = False

# fast 模式专用（accurate 时忽略）
MATCH_FRAME_SCALE = 0.35
REFERENCE_MAX_SIZE = 600
SIFT_MAX_FEATURES = 250
FLANN_CHECKS = 32

# accurate 模式 = 原版参数
ACCURATE_REFERENCE_MAX_SIZE = 0   # 0 表示不缩小参考图（原版 ~1748px）
ACCURATE_SIFT_MAX_FEATURES = 0    # 0 表示不限制特征点（原版无限制）
ACCURATE_FLANN_CHECKS = 50
ACCURATE_MATCH_FRAME_SCALE = 1.0  # 原版：摄像头帧不缩小

CAMERA_WIDTH = 1280               # accurate 模式用更高采集分辨率
CAMERA_HEIGHT = 720
CAMERA_PREVIEW_WIDTH = 640        # 预览窗口仍可缩小，不影响识别用的原始帧

# ---------- 显示端（只影响画布纹样大小，不影响识别）----------
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
OVERLAY_MAX_WIDTH_RATIO = 0.30
OVERLAY_MAX_HEIGHT_RATIO = 0.42
USE_STATIC_BACKGROUND = True
