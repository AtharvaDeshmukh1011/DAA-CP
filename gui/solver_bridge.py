"""Subprocess bridge to the C++ solver binary.

Starts `solver.exe <algorithm>`, feeds it the instance on stdin, and reads
its line-delimited JSON stdout in a background thread so the Tkinter main
loop is never blocked waiting on the child process. The main loop drains
parsed messages from a thread-safe queue on its own schedule (see
`poll_all` / `poll_one` in app.py).
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOLVER_PATH = PROJECT_ROOT / "cpp" / "bin" / "solver.exe"


@dataclass
class SolverMessage:
    kind: str  # "step" | "done" | "error"
    data: dict


class SolverBridge:
    """Owns one solver.exe run at a time."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._queue: "queue.Queue[SolverMessage]" = queue.Queue()
        self._finished = threading.Event()

    @staticmethod
    def solver_available() -> bool:
        return SOLVER_PATH.exists()

    def start(self, algorithm: str, points: list[tuple[float, float]]) -> None:
        self.stop()  # make sure any previous run is cleaned up
        self._queue = queue.Queue()
        self._finished.clear()

        self._proc = subprocess.Popen(
            [str(SOLVER_PATH), algorithm],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        lines = [str(len(points))]
        lines.extend(f"{x} {y}" for x, y in points)
        assert self._proc.stdin is not None
        self._proc.stdin.write("\n".join(lines) + "\n")
        self._proc.stdin.close()

        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _read_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = obj.get("type", "step")
            self._queue.put(SolverMessage(kind=kind, data=obj))
        self._finished.set()

    def poll_all(self) -> list[SolverMessage]:
        """Non-blocking: drain and return everything currently queued."""
        messages = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return messages

    def is_finished(self) -> bool:
        return self._finished.is_set() and self._queue.empty()

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
