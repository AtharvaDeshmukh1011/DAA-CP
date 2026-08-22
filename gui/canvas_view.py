"""Drawing primitives for the TSP canvas.

City coordinates are used directly as canvas pixel coordinates (both random
generation and click-placement keep points inside the visible canvas area),
so no world<->screen transform is needed here -- it's kept intentionally
simple since the point of this view is the algorithm animation, not a
scrollable/zoomable map.
"""

from __future__ import annotations

import tkinter as tk

CITY_RADIUS = 6

COLOR_BG = "#12161c"
COLOR_CITY = "#e8ecf1"
COLOR_CITY_START = "#f5a623"
COLOR_LABEL = "#8b93a1"
COLOR_PATH_SO_FAR = "#3498db"
COLOR_CURRENT_EDGE = "#f5a623"
COLOR_ACCEPTED_EDGE = "#2ecc71"
COLOR_REJECTED_EDGE = "#e74c3c"
COLOR_DP_SUBSET = "#9b59b6"
COLOR_FINAL_TOUR = "#2ecc71"


class CanvasView:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self.canvas.configure(bg=COLOR_BG, highlightthickness=0)
        self.points: list[tuple[float, float]] = []

    # -- city management -------------------------------------------------

    def set_points(self, points: list[tuple[float, float]]) -> None:
        self.points = points
        self.redraw_cities()

    def redraw_cities(self) -> None:
        self.canvas.delete("city")
        for idx, (x, y) in enumerate(self.points):
            color = COLOR_CITY_START if idx == 0 else COLOR_CITY
            self.canvas.create_oval(
                x - CITY_RADIUS, y - CITY_RADIUS, x + CITY_RADIUS, y + CITY_RADIUS,
                fill=color, outline="", tags="city",
            )
            self.canvas.create_text(
                x, y - CITY_RADIUS - 10, text=str(idx), fill=COLOR_LABEL,
                font=("Segoe UI", 9), tags="city",
            )

    def clear(self) -> None:
        self.canvas.delete("all")
        self.points = []

    # -- dynamic (per-step) layer ------------------------------------------

    def clear_dynamic(self) -> None:
        self.canvas.delete("dynamic")

    def clear_transient(self) -> None:
        self.canvas.delete("transient")

    def _edge_coords(self, i: int, j: int) -> tuple[float, float, float, float]:
        x1, y1 = self.points[i]
        x2, y2 = self.points[j]
        return x1, y1, x2, y2

    def draw_path(self, order: list[int], color: str, width: int = 2,
                   dash: tuple[int, int] | None = None, tag: str = "dynamic",
                   close_loop: bool = False) -> None:
        if len(order) < 2:
            return
        pairs = list(zip(order, order[1:]))
        if close_loop:
            pairs.append((order[-1], order[0]))
        for i, j in pairs:
            x1, y1, x2, y2 = self._edge_coords(i, j)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash, tags=tag)
        self.canvas.tag_raise("city")

    def draw_edge(self, i: int, j: int, color: str, width: int = 3, tag: str = "dynamic") -> None:
        x1, y1, x2, y2 = self._edge_coords(i, j)
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, tags=tag)
        self.canvas.tag_raise("city")

    def highlight_city(self, idx: int, color: str, tag: str = "transient") -> None:
        x, y = self.points[idx]
        r = CITY_RADIUS + 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, width=2, tags=tag)

    def draw_final_tour(self, order: list[int]) -> None:
        self.canvas.delete("dynamic")
        self.canvas.delete("transient")
        self.draw_path(order, COLOR_FINAL_TOUR, width=3, tag="final", close_loop=True)
