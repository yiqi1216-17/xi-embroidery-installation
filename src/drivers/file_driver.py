from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from drivers.base import OutputDriver
from manifest import Pattern
from paths import OUTPUT_FILE


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

    def emit(
        self,
        pattern: Pattern,
        frame_index: int,
        confidence: float | None = None,
    ) -> None:
        frame_path = pattern.sequence_frame(frame_index)
        payload = f"{pattern.coordinate_string()},{frame_path}"
        self.output_file.write_text(payload, encoding="utf-8")
        conf = f" conf={confidence:.4f}" if confidence is not None else ""
        print(f"[file] {payload}{conf}")

    def read(self) -> tuple[str, float, float, Path] | None:
        if not self.output_file.exists():
            return None
        return parse_output_line(self.output_file.read_text(encoding="utf-8"))


class HttpOutputDriver:
    def __init__(self, url: str):
        self.url = url

    def emit(
        self,
        pattern: Pattern,
        frame_index: int,
        confidence: float | None = None,
    ) -> None:
        payload = {
            "label": pattern.id,
            "x": pattern.x,
            "y": pattern.y,
            "index": frame_index,
            "asset_path": str(pattern.sequence_frame(frame_index)),
            "confidence": confidence,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                response.read()
            print(f"[http] {pattern.id}-{frame_index}")
        except urllib.error.URLError as exc:
            print(f"[http] 发送失败: {exc}")


class WebSocketOutputDriver:
    def __init__(self, url: str):
        self.url = url

    def emit(
        self,
        pattern: Pattern,
        frame_index: int,
        confidence: float | None = None,
    ) -> None:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            raise RuntimeError("请安装 websocket-client: pip install websocket-client") from exc

        payload = json.dumps(
            {
                "label": pattern.id,
                "x": pattern.x,
                "y": pattern.y,
                "index": frame_index,
                "asset_path": str(pattern.sequence_frame(frame_index)),
                "confidence": confidence,
            }
        )
        ws = websocket.create_connection(self.url, timeout=2)
        try:
            ws.send(payload)
            print(f"[ws] {pattern.id}-{frame_index}")
        finally:
            ws.close()


def create_output_driver(settings) -> OutputDriver:
    output = settings.output
    assert output is not None
    driver = output.driver.lower()
    if driver == "file":
        return FileOutputDriver()
    if driver == "http":
        return HttpOutputDriver(output.http_url)
    if driver == "websocket":
        return WebSocketOutputDriver(output.websocket_url)
    raise ValueError(f"未知 output driver: {driver}")
