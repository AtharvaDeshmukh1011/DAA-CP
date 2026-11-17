#pragma once

#include <vector>
#include <limits>
#include "tsp_types.hpp"

inline double mst_lower_bound(const Instance& inst) {
    const int n = inst.size();
    if (n <= 1) return 0.0;

    std::vector<double> min_edge(n, std::numeric_limits<double>::infinity());
    std::vector<bool> in_mst(n, false);
    min_edge[0] = 0.0;
    double total = 0.0;

    for (int iter = 0; iter < n; ++iter) {
        int u = -1;
        double best = std::numeric_limits<double>::infinity();
        for (int i = 0; i < n; ++i) {
            if (!in_mst[i] && min_edge[i] < best) {
                best = min_edge[i];
                u = i;
            }
        }
        in_mst[u] = true;
        total += best;
        for (int v = 0; v < n; ++v) {
            if (!in_mst[v] && inst.dist(u, v) < min_edge[v]) {
                min_edge[v] = inst.dist(u, v);
            }
        }
    }
    return total;
}
