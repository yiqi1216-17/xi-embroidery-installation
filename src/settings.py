from __future__ import annotations

from dataclasses import dataclass

import yaml

from paths import CONFIG_DIR

VALID_MODES = ("exhibition", "dev")


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
    use_preview_assets: bool = False


@dataclass
class DisplaySettings:
    width: int = 1280
    height: int = 720
    overlay_max_width_ratio: float = 0.30
    overlay_max_height_ratio: float = 0.42
    use_static_background: bool = True
    use_preview_assets: bool = False
    global_scale: float = 1.0
    global_offset_x: float = 0.0
    global_offset_y: float = 0.0


@dataclass
class OutputSettings:
    driver: str = "file"
    http_url: str = "http://127.0.0.1:8765/state"
    websocket_url: str = "ws://127.0.0.1:8766"


@dataclass
class Settings:
    recognition_mode: str = "exhibition"
    match_interval_sec: float = 0.5
    similarity_threshold: float = 0.05
    similarity_threshold_hold: float = 0.03
    vote_count: int = 3
    verbose_match: bool = False
    sequence_interval_sec: int = 5
    camera: CameraSettings | None = None
    perception: PerceptionSettings | None = None
    display: DisplaySettings | None = None
    output: OutputSettings | None = None


def load_settings(mode: str = "exhibition") -> Settings:
    if mode not in VALID_MODES:
        raise ValueError(f"未知模式 '{mode}'，请使用: {', '.join(VALID_MODES)}")

    config_path = CONFIG_DIR / f"{mode}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    camera = CameraSettings(**raw.get("camera", {}))
    perception = PerceptionSettings(**raw.get("perception", {}))
    display_raw = raw.get("display", {})
    display = DisplaySettings(
        width=display_raw.get("width", 1280),
        height=display_raw.get("height", 720),
        overlay_max_width_ratio=display_raw.get("overlay_max_width_ratio", 0.30),
        overlay_max_height_ratio=display_raw.get("overlay_max_height_ratio", 0.42),
        use_static_background=display_raw.get("use_static_background", True),
        use_preview_assets=display_raw.get("use_preview_assets", False),
        global_scale=display_raw.get("global_scale", 1.0),
        global_offset_x=display_raw.get("global_offset_x", 0.0),
        global_offset_y=display_raw.get("global_offset_y", 0.0),
    )
    output_raw = raw.get("output", {})
    output = OutputSettings(
        driver=output_raw.get("driver", "file"),
        http_url=output_raw.get("http_url", "http://127.0.0.1:8765/state"),
        websocket_url=output_raw.get("websocket_url", "ws://127.0.0.1:8766"),
    )

    return Settings(
        recognition_mode=raw.get("recognition_mode", mode),
        match_interval_sec=float(raw.get("match_interval_sec", 0.5)),
        similarity_threshold=float(raw.get("similarity_threshold", 0.05)),
        similarity_threshold_hold=float(raw.get("similarity_threshold_hold", 0.03)),
        vote_count=int(raw.get("vote_count", 3)),
        verbose_match=bool(raw.get("verbose_match", False)),
        sequence_interval_sec=int(raw.get("sequence_interval_sec", 5)),
        camera=camera,
        perception=perception,
        display=display,
        output=output,
    )


def load_overlay_calibration() -> dict:
    path = CONFIG_DIR / "overlay_calibration.yaml"
    if not path.exists():
        return {"patterns": {}}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {"patterns": {}}


def save_overlay_calibration(data: dict) -> None:
    path = CONFIG_DIR / "overlay_calibration.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
