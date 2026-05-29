from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import cv2

from drivers.file_driver import create_output_driver
from manifest import Pattern, load_manifest, pattern_by_id
from paths import LOG_DIR
from perception.matcher import ImageRecognitionSystem, MatchResult
from settings import Settings


@dataclass
class SequenceState:
    label: str | None = None
    index: int = 1
    last_update: float = 0.0
    active: bool = False
    matched_at: float = 0.0


@dataclass
class PerceptionController:
    settings: Settings
    patterns: list[Pattern] = field(default_factory=list)
    matcher: ImageRecognitionSystem | None = None
    output: object | None = None
    sequence: SequenceState = field(default_factory=SequenceState)
    vote_buffer: deque[tuple[str, float]] = field(default_factory=deque)
    running: bool = True

    def setup(self) -> None:
        use_preview = bool(
            self.settings.perception and self.settings.perception.use_preview_assets
        )
        self.patterns = load_manifest(use_preview=use_preview)
        self.matcher = ImageRecognitionSystem(self.settings)
        self.output = create_output_driver(self.settings)
        self.vote_buffer = deque(maxlen=self.settings.vote_count)

        for pattern in self.patterns:
            for ref_path in pattern.all_reference_images():
                if not ref_path.exists():
                    print(f"警告: 参考图不存在 {ref_path}")
                    continue
                ok = self.matcher.add_reference_image(str(ref_path), pattern.id)
                if not ok:
                    print(f"警告: 参考图加载失败 {pattern.id} <- {ref_path}")

    def _log_event(self, event: str, **payload) -> None:
        LOG_DIR.mkdir(exist_ok=True)
        record = {"ts": time.time(), "event": event, **payload}
        with (LOG_DIR / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _confirm_label(self, result: MatchResult) -> bool:
        self.vote_buffer.append((result.label, result.confidence))
        if len(self.vote_buffer) < self.settings.vote_count:
            return False
        return all(item[0] == result.label for item in self.vote_buffer)

    def on_match(self, result: MatchResult) -> None:
        if self.sequence.label == result.label:
            return
        if not self._confirm_label(result):
            return

        pattern = pattern_by_id(self.patterns, result.label)
        if pattern is None or self.output is None:
            return

        now = time.time()
        if self.sequence.label and self.sequence.matched_at:
            self._log_event(
                "pattern_released",
                label=self.sequence.label,
                dwell_sec=round(now - self.sequence.matched_at, 2),
            )

        self.sequence.label = result.label
        self.sequence.index = 1
        self.sequence.last_update = now
        self.sequence.matched_at = now
        self.sequence.active = True
        self.output.emit(pattern, 1, confidence=result.confidence)
        self._log_event(
            "pattern_matched",
            label=result.label,
            index=1,
            confidence=round(result.confidence, 4),
        )

    def tick_sequence(self) -> None:
        if not self.sequence.active or self.sequence.label is None or self.output is None:
            return
        if time.time() - self.sequence.last_update < self.settings.sequence_interval_sec:
            return

        pattern = pattern_by_id(self.patterns, self.sequence.label)
        if pattern is None:
            return

        self.sequence.index = self.sequence.index % 5 + 1
        self.output.emit(pattern, self.sequence.index)
        self.sequence.last_update = time.time()
        self._log_event(
            "sequence_advanced",
            label=pattern.id,
            index=self.sequence.index,
            dwell_sec=round(time.time() - self.sequence.matched_at, 2),
        )

    def run(self) -> None:
        assert self.matcher is not None
        camera = self.settings.camera
        assert camera is not None

        cap = cv2.VideoCapture(camera.device)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            raise SystemExit("无法打开摄像头")

        latest_frame = None
        frame_lock = threading.Lock()

        def recognition_worker():
            while self.running:
                time.sleep(self.settings.match_interval_sec)
                with frame_lock:
                    frame = None if latest_frame is None else latest_frame.copy()
                if frame is None:
                    continue
                result = self.matcher.match_image(frame, active_label=self.sequence.label)
                if result:
                    self.on_match(result)

        def sequence_worker():
            while self.running:
                time.sleep(1)
                self.tick_sequence()

        threading.Thread(target=recognition_worker, daemon=True).start()
        threading.Thread(target=sequence_worker, daemon=True).start()

        print(f"[orchestrator] 模式 {self.settings.recognition_mode}，按 q 退出")
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            with frame_lock:
                latest_frame = frame

            h, w = frame.shape[:2]
            preview_w = camera.preview_width
            preview_h = int(h * (preview_w / w))
            preview = cv2.resize(frame, (preview_w, preview_h), interpolation=cv2.INTER_AREA)
            cv2.imshow("Camera", preview)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.running = False

        cap.release()
        cv2.destroyAllWindows()

    def match_frame_offline(self, frame) -> MatchResult | None:
        assert self.matcher is not None
        return self.matcher.match_image(frame, active_label=self.sequence.label)
