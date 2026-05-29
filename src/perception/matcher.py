from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from perception.utils import resize_max_side
from settings import Settings


@dataclass
class MatchResult:
    label: str
    confidence: float


def _sift_create(max_features: int):
    if max_features and max_features > 0:
        return cv2.SIFT_create(nfeatures=max_features)
    return cv2.SIFT_create()


class ImageRecognitionSystem:
    def __init__(self, settings: Settings):
        self.settings = settings
        perception = settings.perception
        assert perception is not None

        self.reference_features: dict[str, list[tuple]] = {}
        self.trigger_threshold = settings.similarity_threshold
        self.hold_threshold = settings.similarity_threshold_hold
        self.verbose = settings.verbose_match
        self.reference_max_size = perception.reference_max_size
        self.default_frame_scale = perception.match_frame_scale

        self.sift = _sift_create(perception.sift_max_features)
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=perception.flann_checks)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        print(f"[perception] 模式: {settings.recognition_mode}")

    def effective_threshold(self, active_label: str | None) -> float:
        if active_label and active_label in self.reference_features:
            return self.hold_threshold
        return self.trigger_threshold

    def add_reference_image(self, image_path: str, pattern_id: str) -> bool:
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

        self.reference_features.setdefault(pattern_id, []).append((keypoints, descriptors))
        print(
            f"已加载参考图 {pattern_id}: {len(keypoints)} 特征点 "
            f"({Path(image_path).name})"
        )
        return True

    def _best_ratio_for_pattern(
        self, frame_keypoints, frame_descriptors, ref_list: list[tuple]
    ) -> float:
        best = 0.0
        for _, ref_descriptors in ref_list:
            try:
                matches = self.flann.knnMatch(frame_descriptors, ref_descriptors, k=2)
                good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
                ratio = len(good_matches) / max(len(frame_keypoints), 1)
                best = max(best, ratio)
            except Exception:
                continue
        return best

    def match_image(
        self,
        frame,
        frame_scale: float | None = None,
        active_label: str | None = None,
    ) -> MatchResult | None:
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

        threshold = self.effective_threshold(active_label)
        best_match = None
        best_match_ratio = 0.0

        for pattern_id, ref_list in self.reference_features.items():
            match_ratio = self._best_ratio_for_pattern(
                frame_keypoints, frame_descriptors, ref_list
            )
            if self.verbose:
                print(f"  {pattern_id}: {match_ratio:.4f}")

            if match_ratio > best_match_ratio:
                best_match_ratio = match_ratio
                best_match = pattern_id

        if best_match and best_match_ratio > threshold:
            if self.verbose or best_match_ratio >= self.trigger_threshold:
                print(f"匹配: {best_match} ({best_match_ratio:.4f}, 阈值 {threshold:.2f})")
            return MatchResult(label=best_match, confidence=best_match_ratio)
        return None
