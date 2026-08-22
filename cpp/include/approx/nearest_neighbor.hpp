#pragma once

#include <vector>
#include <limits>
#include <iostream>
#include "../tsp_types.hpp"
#include "../step_emitter.hpp"

// Time complexity: O(n^2) -- at each of n steps, scan all unvisited cities
// for the nearest one. Space: O(n).
// Heuristic quality: can be arbitrarily bad in the worst case, but on
// random Euclidean instances typically lands within ~25% of optimal.
inline Tour solve_nearest_neighbor(const Instance& inst, int start = 0) {
    const int n = inst.size();
    Tour result;
    if (n <= 1) {
        result.order = (n == 1) ? std::vector<int>{0} : std::vector<int>{};
        result.length = 0.0;
        return result;
    }

    std::vector<bool> visited(n, false);
    std::vector<int> path;
    path.reserve(n);

    int current = start;
    visited[current] = true;
    path.push_back(current);

    for (int step = 1; step < n; ++step) {
        int best = -1;
        double best_dist = std::numeric_limits<double>::infinity();
        for (int j = 0; j < n; ++j) {
            if (!visited[j] && inst.dist(current, j) < best_dist) {
                best_dist = inst.dist(current, j);
                best = j;
            }
        }

        visited[best] = true;
        path.push_back(best);

        std::cout << "{\"type\":\"step\",\"algo\":\"nearest_neighbor\",\"from\":" << current
                   << ",\"to\":" << best << ",\"dist\":" << best_dist << ",\"path_so_far\":";
        json_int_array(std::cout, path);
        std::cout << "}";
        end_line(std::cout);

        current = best;
    }

    result.order = path;
    result.length = tour_length(inst, path);
    return result;
}
