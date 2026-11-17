#pragma once

#include <vector>
#include <numeric>
#include <algorithm>
#include <limits>
#include <iostream>
#include "../tsp_types.hpp"
#include "../step_emitter.hpp"

inline Tour solve_brute_force(const Instance& inst) {
    const int n = inst.size();
    Tour best;
    if (n <= 1) {
        best.order = (n == 1) ? std::vector<int>{0} : std::vector<int>{};
        best.length = 0.0;
        return best;
    }

    std::vector<int> perm(n - 1);
    std::iota(perm.begin(), perm.end(), 1);

    std::vector<int> best_path;
    double best_len = std::numeric_limits<double>::infinity();

    do {
        std::vector<int> path;
        path.reserve(n);
        path.push_back(0);
        path.insert(path.end(), perm.begin(), perm.end());

        double len = tour_length(inst, path);
        bool improved = len < best_len;
        if (improved) {
            best_len = len;
            best_path = path;
        }

        std::cout << "{\"type\":\"step\",\"algo\":\"brute_force\",\"path\":";
        json_int_array(std::cout, path);
        std::cout << ",\"best_len\":" << best_len << ",\"best_path\":";
        json_int_array(std::cout, best_path);
        std::cout << ",\"improved\":" << (improved ? "true" : "false") << "}";
        end_line(std::cout);
    } while (std::next_permutation(perm.begin(), perm.end()));

    best.order = best_path;
    best.length = best_len;
    return best;
}
