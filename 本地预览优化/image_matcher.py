import cv2

from config import (
    ACCURATE_FLANN_CHECKS,
    ACCURATE_MATCH_FRAME_SCALE,
    ACCURATE_REFERENCE_MAX_SIZE,
    ACCURATE_SIFT_MAX_FEATURES,
    FLANN_CHECKS,
    MATCH_FRAME_SCALE,
    RECOGNITION_MODE,
    REFERENCE_MAX_SIZE,
    SIFT_MAX_FEATURES,
    SIMILARITY_THRESHOLD,
    VERBOSE_MATCH,
)
from image_utils import resize_max_side


def _sift_create(max_features: int):
    if max_features and max_features > 0:
        return cv2.SIFT_create(nfeatures=max_features)
    return cv2.SIFT_create()


class ImageRecognitionSystem:
    def __init__(self, similarity_threshold=0.7, verbose: bool | None = None):
        self.reference_features = {}
        self.similarity_threshold = similarity_threshold
        self.verbose = VERBOSE_MATCH if verbose is None else verbose
        self.accurate = RECOGNITION_MODE == "accurate"

        if self.accurate:
            self.reference_max_size = ACCURATE_REFERENCE_MAX_SIZE
            self.sift_max_features = ACCURATE_SIFT_MAX_FEATURES
            self.flann_checks = ACCURATE_FLANN_CHECKS
            self.default_frame_scale = ACCURATE_MATCH_FRAME_SCALE
        else:
            self.reference_max_size = REFERENCE_MAX_SIZE
            self.sift_max_features = SIFT_MAX_FEATURES
            self.flann_checks = FLANN_CHECKS
            self.default_frame_scale = MATCH_FRAME_SCALE

        self.sift = _sift_create(self.sift_max_features)
        flann_index_kdtree = 1
        index_params = dict(algorithm=flann_index_kdtree, trees=5)
        search_params = dict(checks=self.flann_checks)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        mode_label = "accurate（原版参数）" if self.accurate else "fast（预览优化）"
        print(f"[识别] 模式: {mode_label}")

    def add_reference_image(self, image_path, label):
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"无法加载图像: {image_path}")
                return False

            if self.reference_max_size and self.reference_max_size > 0:
                img = resize_max_side(img, self.reference_max_size)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)
            if descriptors is None:
                print(f"无法从图像中提取特征: {image_path}")
                return False

            self.reference_features[label] = (keypoints, descriptors)
            print(f"已添加参考图像: {label}，特征点 {len(keypoints)}，尺寸 {gray.shape[1]}x{gray.shape[0]}")
            return True
        except Exception as exc:
            print(f"添加参考图像时出错: {exc}")
            return False

    def match_image(self, frame, frame_scale: float | None = None):
        scale = self.default_frame_scale if frame_scale is None else frame_scale
        if scale < 1.0:
            height, width = frame.shape[:2]
            frame = cv2.resize(
                frame,
                (max(1, int(width * scale)), max(1, int(height * scale))),
                interpolation=cv2.INTER_AREA,
            )

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_keypoints, frame_descriptors = self.sift.detectAndCompute(gray_frame, None)
        if frame_descriptors is None:
            if self.verbose:
                print("当前帧无法提取特征")
            return None

        best_match = None
        best_match_ratio = 0.0

        for label, (ref_keypoints, ref_descriptors) in self.reference_features.items():
            try:
                matches = self.flann.knnMatch(frame_descriptors, ref_descriptors, k=2)
                good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
                match_ratio = len(good_matches) / max(len(frame_keypoints), 1)

                if self.verbose:
                    print(f"与 {label} 的匹配比率: {match_ratio:.4f}，好的匹配点: {len(good_matches)}")

                if match_ratio > best_match_ratio:
                    best_match_ratio = match_ratio
                    best_match = label
            except Exception as exc:
                if self.verbose:
                    print(f"匹配图像 {label} 时出错: {exc}")

        if best_match_ratio > self.similarity_threshold:
            print(f"匹配到: {best_match} ({best_match_ratio:.4f})")
            return best_match

        return None
