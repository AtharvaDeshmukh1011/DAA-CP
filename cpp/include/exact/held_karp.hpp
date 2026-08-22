#pragma once

#include <vector>
#include <limits>
#include <algorithm>
#include <iostream>
#include "../tsp_types.hpp"
#include "../step_emitter.hpp"

// Time complexity: O(n^2 * 2^n), space: O(n * 2^n) for dp/parent tables.
// dp[mask][j] = shortest path that visits exactly the cities in `mask`
// (mask always includes city 0, the fixed start) and ends at city j.
// Transition: dp[mask | {k}][k] = min over j in mask of dp[mask][j] + dist(j,k).
// Answer: min over j != 0 of dp[full][j] + dist(j, 0), closing the cycle.
inline Tour solve_held_karp(const Instance& inst) {
    const int n = inst.size();
    Tour result;
    if (n <= 1) {
        result.order = (n == 1) ? std::vector<int>{0} : std::vector<int>{};
        result.length = 0.0;
        return result;
    }

    const int full = 1 << n;
    const double INF = std::numeric_limits<double>::infinity();
    std::vector<std::vector<double>> dp(full, std::vector<double>(n, INF));
    std::vector<std::vector<int>> parent(full, std::vector<int>(n, -1));

    dp[1][0] = 0.0; // mask = {0}, path ends at 0

    for (int mask = 1; mask < full; ++mask) {
        if (!(mask & 1)) continue; // every reachable mask must contain start city 0
        for (int j = 0; j < n; ++j) {
            if (!(mask & (1 << j))) continue;
            double cur = dp[mask][j];
            if (cur == INF) continue;

            for (int k = 0; k < n; ++k) {
                if (mask & (1 << k)) continue; // k already visited in this subset
                int next_mask = mask | (1 << k);
                double cand = cur + inst.dist(j, k);
                if (cand < dp[next_mask][k]) {
                    dp[next_mask][k] = cand;
                    parent[next_mask][k] = j;

                    std::vector<int> subset;
                    for (int b = 0; b < n; ++b) {
                        if (next_mask & (1 << b)) subset.push_back(b);
                    }

                    std::cout << "{\"type\":\"step\",\"algo\":\"held_karp\",\"subset\":";
                    json_int_array(std::cout, subset);
                    std::cout << ",\"last\":" << k << ",\"cost\":" << cand << "}";
                    end_line(std::cout);
                }
            }
        }
    }

    const int full_mask = full - 1;
    double best_len = INF;
    int best_last = -1;
    for (int j = 1; j < n; ++j) {
        if (dp[full_mask][j] == INF) continue;
        double total = dp[full_mask][j] + inst.dist(j, 0);
        if (total < best_len) {
            best_len = total;
            best_last = j;
        }
    }

    std::vector<int> path;
    int mask = full_mask, cur = best_last;
    while (cur != -1) {
        path.push_back(cur);
        int prev = parent[mask][cur];
        mask ^= (1 << cur);
        cur = prev;
    }
    std::reverse(path.begin(), path.end());

    result.order = path;
    result.length = best_len;
    return result;
}
