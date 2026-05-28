from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from xi_embroidery.paths import CONFIG_DIR


@dataclass
class CameraSettings:
    width: int = 1280
    height: int = 720
    preview_width: int = 640
    device: int = 0


@dataclass
class PerceptionSettings:
    reference_max_size: int = 0
    sift_max_features: int = 0
    flann_checks: int = 50
    match_frame_scale: float = 1.0


@dataclass
class DisplaySettings:
    width: int = 1280
    height: int = 720
    overlay_max_width_ratio: float = 0.30
    overlay_max_height_ratio: float = 0.42
    use_static_background: bool = True


@dataclass
class Settings:
    recognition_mode: str = "accurate"
    match_interval_sec: float = 0.5
    similarity_threshold: float = 0.05
    vote_count: int = 3
    verbose_match: bool = False
    sequence_interval_sec: int = 5
    camera: CameraSettings | None = None
    perception: PerceptionSettings | None = None
    display: DisplaySettings | None = None
    output_driver: str = "file"

    @property
    def is_accurate(self) -> bool:
        return self.recognition_mode == "accurate"


def load_settings(mode: str = "accurate") -> Settings:
    config_path = CONFIG_DIR / f"{mode}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    camera = CameraSettings(**raw.get("camera", {}))
    perception = PerceptionSettings(**raw.get("perception", {}))
    display = DisplaySettings(**raw.get("display", {}))

    return Settings(
        recognition_mode=raw.get("recognition_mode", mode),
        match_interval_sec=float(raw.get("match_interval_sec", 0.5)),
        similarity_threshold=float(raw.get("similarity_threshold", 0.05)),
        vote_count=int(raw.get("vote_count", 3)),
        verbose_match=bool(raw.get("verbose_match", False)),
        sequence_interval_sec=int(raw.get("sequence_interval_sec", 5)),
        camera=camera,
        perception=perception,
        display=display,
        output_driver=raw.get("output", {}).get("driver", "file"),
    )
