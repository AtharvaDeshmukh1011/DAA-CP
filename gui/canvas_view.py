"""Drawing primitives for the TSP canvas.

City coordinates are used directly as canvas pixel coordinates (both random
generation and click-placement keep points inside the visible canvas area),
so no world<->screen transform is needed here -- it's kept intentionally
simple since the point of this view is the algorithm animation, not a
scrollable/zoomable map.

There's no real geography behind these coordinates, so "km" is a demo scale
(PIXELS_PER_KM below) rather than a real-world distance -- it exists so
edge lengths read as a familiar unit instead of raw pixel counts.
"""

from __future__ import annotations

import math
import tkinter as tk

CITY_RADIUS = 6
PIXELS_PER_KM = 20  # arbitrary demo scale: 20px of canvas == 1 km
LINE_END_GAP = 9    # shrink lines by this much at each end so arrowheads/dots don't overlap

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
COLOR_DISTANCE_LABEL = "#aab2bd"


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
        """Endpoints for the line i->j, shrunk at both ends so it doesn't
        run underneath the city dots (which matters most once we're
        drawing arrowheads -- an arrow tip buried in a dot is invisible)."""
        x1, y1 = self.points[i]
        x2, y2 = self.points[j]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length <= 2 * LINE_END_GAP:
            return x1, y1, x2, y2
        ux, uy = dx / length, dy / length
        return (x1 + ux * LINE_END_GAP, y1 + uy * LINE_END_GAP,
                x2 - ux * LINE_END_GAP, y2 - uy * LINE_END_GAP)

    def _distance_km(self, i: int, j: int) -> float:
        x1, y1 = self.points[i]
        x2, y2 = self.points[j]
        return math.hypot(x2 - x1, y2 - y1) / PIXELS_PER_KM

    def _draw_distance_label(self, i: int, j: int, tag: str) -> None:
        x1, y1 = self.points[i]
        x2, y2 = self.points[j]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1.0
        perp_x, perp_y = -dy / length, dx / length
        offset = 10
        lx, ly = mx + perp_x * offset, my + perp_y * offset
        km = length / PIXELS_PER_KM
        self.canvas.create_text(
            lx, ly, text=f"{km:.1f} km", fill=COLOR_DISTANCE_LABEL,
            font=("Segoe UI", 8), tags=tag,
        )

    def draw_path(self, order: list[int], color: str, width: int = 2,
                   dash: tuple[int, int] | None = None, tag: str = "dynamic",
                   close_loop: bool = False, arrow: bool = False,
                   show_distance: bool = False) -> None:
        if len(order) < 2:
            return
        pairs = list(zip(order, order[1:]))
        if close_loop:
            pairs.append((order[-1], order[0]))
        for i, j in pairs:
            x1, y1, x2, y2 = self._edge_coords(i, j)
            kwargs = dict(fill=color, width=width, dash=dash, tags=tag)
            if arrow:
                kwargs["arrow"] = tk.LAST
                kwargs["arrowshape"] = (10, 12, 4)
            self.canvas.create_line(x1, y1, x2, y2, **kwargs)
            if show_distance:
                self._draw_distance_label(i, j, tag)
        self.canvas.tag_raise("city")

    def draw_edge(self, i: int, j: int, color: str, width: int = 3, tag: str = "dynamic",
                   arrow: bool = False, show_distance: bool = False) -> None:
        x1, y1, x2, y2 = self._edge_coords(i, j)
        kwargs = dict(fill=color, width=width, tags=tag)
        if arrow:
            kwargs["arrow"] = tk.LAST
            kwargs["arrowshape"] = (10, 12, 4)
        self.canvas.create_line(x1, y1, x2, y2, **kwargs)
        if show_distance:
            self._draw_distance_label(i, j, tag)
        self.canvas.tag_raise("city")

    def highlight_city(self, idx: int, color: str, tag: str = "transient") -> None:
        x, y = self.points[idx]
        r = CITY_RADIUS + 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, width=2, tags=tag)

    def draw_final_tour(self, order: list[int]) -> None:
        self.canvas.delete("dynamic")
        self.canvas.delete("transient")
        self.draw_path(order, COLOR_FINAL_TOUR, width=3, tag="final", close_loop=True,
                        arrow=True, show_distance=True)
