from __future__ import annotations

from pathlib import Path

from xi_embroidery.manifest import Pattern
from xi_embroidery.paths import OUTPUT_FILE


def parse_output_line(line: str) -> tuple[str, float, float, Path] | None:
    line = line.strip()
    if not line:
        return None
    parts = line.split(",")
    if len(parts) < 4:
        return None
    return parts[0], float(parts[1]), float(parts[2]), Path(",".join(parts[3:]))


class FileOutputDriver:
    def __init__(self, output_file: Path | None = None):
        self.output_file = output_file or OUTPUT_FILE

    def emit(self, pattern: Pattern, frame_index: int) -> None:
        frame_path = pattern.sequence_frame(frame_index)
        payload = f"{pattern.coordinate_string()},{frame_path}"
        self.output_file.write_text(payload, encoding="utf-8")
        print(f"[output] {payload}")

    def read(self) -> tuple[str, float, float, Path] | None:
        if not self.output_file.exists():
            return None
        return parse_output_line(self.output_file.read_text(encoding="utf-8"))
