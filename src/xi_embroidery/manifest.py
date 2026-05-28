from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from xi_embroidery.paths import ASSETS_DIR, MANIFEST_FILE


@dataclass
class Pattern:
    id: str
    reference_path: Path
    x: float
    y: float

    def reference_image(self) -> Path:
        return self.reference_path

    def sequence_frame(self, index: int) -> Path:
        return ASSETS_DIR / f"{self.id}-{index}.png"

    def coordinate_string(self) -> str:
        return f"{self.id},{self.x},{self.y}"


def load_manifest(manifest_path: Path | None = None) -> list[Pattern]:
    path = manifest_path or MANIFEST_FILE
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    patterns: list[Pattern] = []
    for item in data["patterns"]:
        coords = item["coordinates"]
        patterns.append(
            Pattern(
                id=item["id"],
                reference_path=ASSETS_DIR / item["reference"],
                x=float(coords["x"]),
                y=float(coords["y"]),
            )
        )
    return patterns


def pattern_by_id(patterns: list[Pattern], label: str) -> Pattern | None:
    for pattern in patterns:
        if pattern.id == label:
            return pattern
    return None
