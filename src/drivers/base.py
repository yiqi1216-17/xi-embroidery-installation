from __future__ import annotations

from typing import Protocol

from manifest import Pattern


class OutputDriver(Protocol):
    def emit(
        self,
        pattern: Pattern,
        frame_index: int,
        confidence: float | None = None,
    ) -> None: ...
