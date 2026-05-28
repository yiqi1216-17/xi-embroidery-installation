import cv2

from xi_embroidery.perception.utils import resize_max_side
from xi_embroidery.settings import Settings


def _sift_create(max_features: int):
    if max_features and max_features > 0:
        return cv2.SIFT_create(nfeatures=max_features)
    return cv2.SIFT_create()


class ImageRecognitionSystem:
    def __init__(self, settings: Settings):
        self.settings = settings
        perception = settings.perception
        assert perception is not None

        self.reference_features: dict = {}
        self.similarity_threshold = settings.similarity_threshold
        self.verbose = settings.verbose_match
        self.reference_max_size = perception.reference_max_size
        self.default_frame_scale = perception.match_frame_scale

        self.sift = _sift_create(perception.sift_max_features)
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=perception.flann_checks)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        print(f"[perception] 模式: {settings.recognition_mode}")

    def add_reference_image(self, image_path: str, label: str) -> bool:
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法加载图像: {image_path}")
            return False

        if self.reference_max_size and self.reference_max_size > 0:
            img = resize_max_side(img, self.reference_max_size)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.sift.detectAndCompute(gray, None)
        if descriptors is None:
            print(f"无法提取特征: {image_path}")
            return False

        self.reference_features[label] = (keypoints, descriptors)
        print(f"已加载参考图 {label}: {len(keypoints)} 特征点, {gray.shape[1]}x{gray.shape[0]}")
        return True

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
            return None

        best_match = None
        best_match_ratio = 0.0

        for label, (_, ref_descriptors) in self.reference_features.items():
            try:
                matches = self.flann.knnMatch(frame_descriptors, ref_descriptors, k=2)
                good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
                match_ratio = len(good_matches) / max(len(frame_keypoints), 1)

                if self.verbose:
                    print(f"  {label}: {match_ratio:.4f} ({len(good_matches)} 点)")

                if match_ratio > best_match_ratio:
                    best_match_ratio = match_ratio
                    best_match = label
            except Exception as exc:
                if self.verbose:
                    print(f"  {label} 匹配出错: {exc}")

        if best_match_ratio > self.similarity_threshold:
            print(f"匹配: {best_match} ({best_match_ratio:.4f})")
            return best_match
        return None
