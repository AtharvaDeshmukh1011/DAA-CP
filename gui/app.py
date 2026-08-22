"""TSP Visualizer -- CustomTkinter GUI that drives the C++ solver and
animates its actual step-by-step execution trace (not a canned replay).

Run with: python app.py   (build the C++ solver first: cpp/build.sh or build.bat)
"""

from __future__ import annotations

import random
import tkinter as tk

import customtkinter as ctk

from canvas_view import (
    CanvasView,
    COLOR_ACCEPTED_EDGE,
    COLOR_CURRENT_EDGE,
    COLOR_DP_SUBSET,
    COLOR_PATH_SO_FAR,
    COLOR_REJECTED_EDGE,
)
from solver_bridge import SolverBridge

CANVAS_W, CANVAS_H = 760, 680
MARGIN = 40
TICK_MS = 30

# (display name, solver key, complexity blurb, max n or None)
ALGORITHMS = [
    ("Nearest Neighbor", "nearest_neighbor", "Approximate | O(n²) time, O(n) space", None),
    ("Greedy Edge", "greedy_edge", "Approximate | O(n² log n) time, O(n²) space", None),
    ("Held-Karp (DP)", "held_karp", "Exact | O(n²·2ⁿ) time, O(n·2ⁿ) space", 20),
    ("Brute Force", "brute_force", "Exact | O(n!) time, O(n) space", 10),
]
ALGO_BY_NAME = {a[0]: a for a in ALGORITHMS}


class TSPApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("TSP Visualizer -- Exact & Approximate Algorithms")
        self.geometry(f"{CANVAS_W + 340}x{CANVAS_H + 40}")
        self.resizable(False, False)

        self.points: list[tuple[float, float]] = []
        self.bridge = SolverBridge()
        self.running = False
        self._after_id: str | None = None
        self.run_state: dict = {}
        self.step_count = 0

        self._build_layout()
        self._on_algo_change(ALGORITHMS[0][0])
        self._regenerate_random(int(self.city_slider.get()))

    # -- layout ------------------------------------------------------------

    def _build_layout(self) -> None:
        canvas_frame = ctk.CTkFrame(self, corner_radius=8)
        canvas_frame.pack(side="left", padx=(12, 6), pady=12)

        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_W, height=CANVAS_H, bd=0)
        self.canvas.pack(padx=8, pady=8)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas_view = CanvasView(self.canvas)

        panel = ctk.CTkFrame(self, corner_radius=8)
        panel.pack(side="right", fill="both", expand=True, padx=(6, 12), pady=12)

        ctk.CTkLabel(panel, text="TSP Visualizer", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", padx=14, pady=(14, 4)
        )
        ctk.CTkLabel(
            panel, text="Click the canvas to place cities, or generate random ones.",
            font=("Segoe UI", 11), text_color="#8b93a1", wraplength=290, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Algorithm selection
        ctk.CTkLabel(panel, text="Algorithm", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14)
        self.algo_menu = ctk.CTkOptionMenu(
            panel, values=[a[0] for a in ALGORITHMS], command=self._on_algo_change, width=290,
        )
        self.algo_menu.pack(padx=14, pady=(4, 4))
        self.algo_info_label = ctk.CTkLabel(
            panel, text="", font=("Segoe UI", 10), text_color="#8b93a1", wraplength=290, justify="left",
        )
        self.algo_info_label.pack(anchor="w", padx=14, pady=(0, 10))

        # City count / generation
        ctk.CTkLabel(panel, text="Cities", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14)
        self.city_count_label = ctk.CTkLabel(panel, text="10", font=("Segoe UI", 11))
        self.city_count_label.pack(anchor="w", padx=14)
        self.city_slider = ctk.CTkSlider(
            panel, from_=2, to=100, number_of_steps=98, width=290, command=self._on_city_slider,
        )
        self.city_slider.set(10)
        self.city_slider.pack(padx=14, pady=(0, 6))

        btn_row = ctk.CTkFrame(panel, fg_color="transparent")
        btn_row.pack(padx=14, pady=(0, 10), fill="x")
        ctk.CTkButton(
            btn_row, text="Generate Random", width=140,
            command=lambda: self._regenerate_random(int(self.city_slider.get())),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Clear", width=90, fg_color="#4a4a4a", command=self._clear_points).pack(
            side="left"
        )

        # Animation controls
        ctk.CTkLabel(panel, text="Animation", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(6, 0))
        self.instant_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            panel, text="Instant result (skip animation)", variable=self.instant_var,
        ).pack(anchor="w", padx=14, pady=(4, 4))
        self.speed_label = ctk.CTkLabel(panel, text="Speed: 3 steps/tick", font=("Segoe UI", 11))
        self.speed_label.pack(anchor="w", padx=14)
        self.speed_slider = ctk.CTkSlider(
            panel, from_=1, to=60, number_of_steps=59, width=290, command=self._on_speed_slider,
        )
        self.speed_slider.set(3)
        self.speed_slider.pack(padx=14, pady=(0, 10))

        # Run / stop
        run_row = ctk.CTkFrame(panel, fg_color="transparent")
        run_row.pack(padx=14, pady=(4, 10), fill="x")
        self.run_button = ctk.CTkButton(run_row, text="Run", width=140, command=self._start_run)
        self.run_button.pack(side="left", padx=(0, 6))
        self.stop_button = ctk.CTkButton(
            run_row, text="Stop", width=90, fg_color="#c0392b", hover_color="#922b21",
            command=self._stop_run, state="disabled",
        )
        self.stop_button.pack(side="left")

        self.status_label = ctk.CTkLabel(
            panel, text="", font=("Segoe UI", 11), text_color="#e74c3c", wraplength=290, justify="left",
        )
        self.status_label.pack(anchor="w", padx=14, pady=(0, 6))

        # Stats
        ctk.CTkLabel(panel, text="Stats", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(6, 0))
        self.stats_label = ctk.CTkLabel(
            panel, text="Length: --\nTime: --\nLower bound: --\nSteps: --",
            font=("Consolas", 11), justify="left",
        )
        self.stats_label.pack(anchor="w", padx=14, pady=(4, 10))

        # Run history
        ctk.CTkLabel(panel, text="Run History", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14)
        self.history_box = ctk.CTkTextbox(panel, width=290, height=160, font=("Consolas", 10))
        self.history_box.pack(padx=14, pady=(4, 10))
        self.history_box.configure(state="disabled")

    # -- city management -----------------------------------------------------

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.running:
            return
        self.points.append((float(event.x), float(event.y)))
        self.canvas_view.set_points(self.points)
        self._clear_run_visuals()

    def _regenerate_random(self, n: int) -> None:
        if self.running:
            return
        self.points = [
            (
                random.uniform(MARGIN, CANVAS_W - MARGIN),
                random.uniform(MARGIN, CANVAS_H - MARGIN),
            )
            for _ in range(n)
        ]
        self.canvas_view.set_points(self.points)
        self._clear_run_visuals()

    def _clear_points(self) -> None:
        if self.running:
            return
        self.points = []
        self.canvas_view.clear()
        self._clear_run_visuals()

    def _clear_run_visuals(self) -> None:
        self.canvas.delete("dynamic")
        self.canvas.delete("transient")
        self.canvas.delete("final")
        self.status_label.configure(text="")
        self.stats_label.configure(text="Length: --\nTime: --\nLower bound: --\nSteps: --")

    # -- controls --------------------------------------------------------

    def _on_city_slider(self, value: float) -> None:
        self.city_count_label.configure(text=str(int(value)))
        self._update_algo_info()

    def _on_speed_slider(self, value: float) -> None:
        self.speed_label.configure(text=f"Speed: {int(value)} steps/tick")

    def _on_algo_change(self, name: str) -> None:
        self._update_algo_info()

    def _update_algo_info(self) -> None:
        name = self.algo_menu.get()
        _, _, blurb, cap = ALGO_BY_NAME[name]
        n = int(self.city_slider.get())
        text = blurb
        if cap is not None:
            text += f"\ncapped at n≤{cap}"
            if n > cap:
                text += f"  ⚠ current n={n} exceeds this cap"
        self.algo_info_label.configure(text=text)

    # -- run lifecycle -----------------------------------------------------

    def _start_run(self) -> None:
        if self.running:
            return
        if len(self.points) < 2:
            self.status_label.configure(text="Place or generate at least 2 cities first.")
            return
        if not SolverBridge.solver_available():
            self.status_label.configure(
                text="solver.exe not found. Build it first: cpp/build.sh (or build.bat) then relaunch."
            )
            return

        name = self.algo_menu.get()
        _, algo_key, _, cap = ALGO_BY_NAME[name]
        n = len(self.points)
        if cap is not None and n > cap:
            self.status_label.configure(text=f"{name} is capped at n≤{cap}; you have n={n}.")
            return

        self._clear_run_visuals()
        self.step_count = 0
        self.run_state = {"algo": algo_key}
        self.running = True
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text=f"Running {name} on {n} cities...", text_color="#8b93a1")

        self.bridge.start(algo_key, self.points)
        self._after_id = self.after(TICK_MS, self._tick)

    def _stop_run(self) -> None:
        if not self.running:
            return
        self.bridge.stop()
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.running = False
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Stopped.", text_color="#8b93a1")

    def _tick(self) -> None:
        instant = self.instant_var.get()
        if instant:
            # Drain everything the solver has (or will shortly have) right now.
            import time as _time
            deadline = _time.time() + 5.0
            messages = []
            while _time.time() < deadline:
                batch = self.bridge.poll_all()
                messages.extend(batch)
                if self.bridge.is_finished():
                    break
                if not batch:
                    _time.sleep(0.01)
        else:
            batch_size = max(1, int(self.speed_slider.get()))
            messages = self.bridge.poll_all()[:batch_size]

        finished_msg = None
        for msg in messages:
            self.step_count += 1
            if msg.kind == "step":
                self._apply_step(msg.data)
            elif msg.kind == "done":
                finished_msg = ("done", msg.data)
                break
            elif msg.kind == "error":
                finished_msg = ("error", msg.data)
                break

        self._redraw_dynamic()

        if finished_msg is not None:
            kind, data = finished_msg
            self._finish_run(kind, data)
            return

        if not self.running:
            return
        self._after_id = self.after(TICK_MS, self._tick)

    def _finish_run(self, kind: str, data: dict) -> None:
        self.running = False
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

        if kind == "error":
            self.status_label.configure(text=data.get("message", "Unknown error."), text_color="#e74c3c")
            return

        tour = data["tour"]
        length = data["length"]
        time_ms = data["time_ms"]
        lower_bound = data["lower_bound"]

        self.canvas_view.draw_final_tour(tour)
        self.status_label.configure(text="Done.", text_color="#2ecc71")
        self.stats_label.configure(
            text=(
                f"Length: {length:.2f}\n"
                f"Time: {time_ms:.3f} ms\n"
                f"Lower bound: {lower_bound:.2f}\n"
                f"Steps: {self.step_count}"
            )
        )

        name = self.algo_menu.get()
        n = len(self.points)
        ratio = length / lower_bound if lower_bound > 0 else float("nan")
        entry = f"{name:<18} n={n:<4} len={length:8.2f}  t={time_ms:7.3f}ms  /LB={ratio:.3f}\n"
        self.history_box.configure(state="normal")
        self.history_box.insert("end", entry)
        self.history_box.see("end")
        self.history_box.configure(state="disabled")

    # -- per-algorithm step rendering ---------------------------------------

    def _apply_step(self, step: dict) -> None:
        algo = self.run_state["algo"]
        if algo == "brute_force":
            self.run_state["last_path"] = step["path"]
            self.run_state["best_path"] = step["best_path"]
            self.run_state["best_len"] = step["best_len"]
        elif algo == "held_karp":
            self.run_state["dp_subset"] = step["subset"]
            self.run_state["dp_last"] = step["last"]
            self.run_state["dp_cost"] = step["cost"]
        elif algo == "nearest_neighbor":
            self.run_state["path_so_far"] = step["path_so_far"]
            self.run_state["last_edge"] = (step["from"], step["to"])
        elif algo == "greedy_edge":
            edges = self.run_state.setdefault("accepted_edges", [])
            edge = tuple(step["edge"])
            if step["accepted"]:
                edges.append(edge)
            self.run_state["last_edge"] = edge
            self.run_state["last_accepted"] = step["accepted"]

        live_len = step.get("best_len") or step.get("cost")
        if live_len is not None:
            self.stats_label.configure(
                text=f"Length: {live_len:.2f} (live)\nTime: --\nLower bound: --\nSteps: {self.step_count}"
            )
        else:
            self.stats_label.configure(text=f"Length: --\nTime: --\nLower bound: --\nSteps: {self.step_count}")

    def _redraw_dynamic(self) -> None:
        self.canvas_view.clear_dynamic()
        self.canvas_view.clear_transient()
        algo = self.run_state.get("algo")

        if algo == "brute_force":
            last_path = self.run_state.get("last_path")
            best_path = self.run_state.get("best_path")
            if last_path:
                self.canvas_view.draw_path(last_path, "#4a4a4a", width=1, dash=(3, 3), close_loop=True)
            if best_path:
                self.canvas_view.draw_path(
                    best_path, COLOR_ACCEPTED_EDGE, width=2, close_loop=True,
                    arrow=True, show_distance=True,
                )

        elif algo == "held_karp":
            subset = self.run_state.get("dp_subset") or []
            last = self.run_state.get("dp_last")
            for city in subset:
                self.canvas_view.highlight_city(city, COLOR_DP_SUBSET, tag="dynamic")
            if last is not None:
                self.canvas_view.highlight_city(last, COLOR_CURRENT_EDGE, tag="transient")

        elif algo == "nearest_neighbor":
            path = self.run_state.get("path_so_far") or []
            if path:
                self.canvas_view.draw_path(
                    path, COLOR_PATH_SO_FAR, width=2, arrow=True, show_distance=True,
                )
            last_edge = self.run_state.get("last_edge")
            if last_edge:
                self.canvas_view.draw_edge(*last_edge, COLOR_CURRENT_EDGE, width=3, tag="transient")

        elif algo == "greedy_edge":
            for (i, j) in self.run_state.get("accepted_edges", []):
                self.canvas_view.draw_edge(
                    i, j, COLOR_ACCEPTED_EDGE, width=2, tag="dynamic", show_distance=True,
                )
            last_edge = self.run_state.get("last_edge")
            if last_edge:
                color = COLOR_ACCEPTED_EDGE if self.run_state.get("last_accepted") else COLOR_REJECTED_EDGE
                self.canvas_view.draw_edge(*last_edge, color, width=2, tag="transient")


if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()
