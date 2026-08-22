# TSP: Exact & Approximate Algorithms

A DAA course project on the Travelling Salesperson Problem: four algorithms
implemented in C++, driven by an interactive GUI that animates each
algorithm's actual step-by-step execution rather than just showing a final
answer.

- **Exact**: Brute Force (O(n!)), Held-Karp Dynamic Programming (O(n²·2ⁿ))
- **Approximate**: Nearest Neighbor (O(n²)), Greedy Edge (O(n² log n))

## Why it's built this way

The GUI (`gui/`) never reimplements the algorithms — it spawns the real C++
binary and animates the execution trace it streams back. One source of
truth for correctness (C++, covered by `cpp/tests/`), one place for visuals
(Python/CustomTkinter). See `cpp/src/solver.cpp` for the exact streaming
protocol.

Approximate algorithms are also scored against an MST-based lower bound
(`cpp/include/lower_bound.hpp`) — for metric TSP the optimal tour is always
≥ the MST weight, so this gives a rigorous quality bound even for instances
too large for an exact algorithm to solve.

## Build

Requires a C++17 compiler (tested with `g++`). No `cmake`/`vcpkg` needed.

```
cd cpp
./build.sh        # or build.bat on plain cmd
```

This produces `cpp/bin/solver.exe` and `cpp/bin/test_correctness.exe`.

Run the correctness tests:

```
cpp/bin/test_correctness.exe
```

## Run the GUI

```
pip install -r gui/requirements.txt
python gui/app.py
```

Click the canvas to place cities (or use "Generate Random"), pick an
algorithm, and hit Run. Brute Force and Held-Karp are capped at n≤10 and
n≤20 respectively since they're exact/exponential; the GUI shows this and
refuses to run past the cap. Check "Instant result" to skip the animation
for large instances.

## Solver CLI (used internally by the GUI, also runnable standalone)

```
echo "5
0 0
10 0
10 10
0 10
5 5" | cpp/bin/solver.exe nearest_neighbor
```

Prints one JSON line per algorithm step, ending with a `"type":"done"` line
containing the final tour, length, timing, and lower bound.
