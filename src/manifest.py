from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from paths import ASSETS_DIR, MANIFEST_FILE, PREVIEW_ASSETS_DIR


@dataclass
class PatternDisplay:
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class Pattern:
    id: str
    reference_paths: list[Path]
    x: float
    y: float
    display: PatternDisplay
    use_preview: bool = False

    def reference_image(self) -> Path:
        base = PREVIEW_ASSETS_DIR if self.use_preview else ASSETS_DIR
        return base / self.reference_paths[0].name

    def all_reference_images(self) -> list[Path]:
        base = PREVIEW_ASSETS_DIR if self.use_preview else ASSETS_DIR
        return [base / ref.name for ref in self.reference_paths]

    def sequence_frame(self, index: int) -> Path:
        base = PREVIEW_ASSETS_DIR if self.use_preview else ASSETS_DIR
        return base / f"{self.id}-{index}.png"

    def coordinate_string(self) -> str:
        return f"{self.id},{self.x},{self.y}"


def load_manifest(manifest_path: Path | None = None, use_preview: bool = False) -> list[Pattern]:
    path = manifest_path or MANIFEST_FILE
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    patterns: list[Pattern] = []
    for item in data["patterns"]:
        coords = item["coordinates"]
        refs = item.get("references") or [item["reference"]]
        display_raw = item.get("display", {})
        patterns.append(
            Pattern(
                id=item["id"],
                reference_paths=[Path(r) for r in refs],
                x=float(coords["x"]),
                y=float(coords["y"]),
                display=PatternDisplay(
                    scale=float(display_raw.get("scale", 1.0)),
                    offset_x=float(display_raw.get("offset_x", 0.0)),
                    offset_y=float(display_raw.get("offset_y", 0.0)),
                ),
                use_preview=use_preview,
            )
        )
    return patterns


def pattern_by_id(patterns: list[Pattern], label: str) -> Pattern | None:
    for pattern in patterns:
        if pattern.id == label:
            return pattern
    return None
