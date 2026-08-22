#pragma once

#include <vector>
#include <numeric>
#include <algorithm>
#include <limits>
#include <iostream>
#include "../tsp_types.hpp"
#include "../step_emitter.hpp"

// Time complexity: O(n!) -- tries every permutation of cities 1..n-1 with
// city 0 fixed as the start (fixing the start removes the n-fold rotational
// redundancy of an otherwise O(n * n!) search; direction is still explored
// both ways, which is fine -- it just means we see the reverse tour too).
// Space: O(n) beyond the input.
//
// Only practical up to ~n=10 (10! = 3.6M permutations); callers are expected
// to enforce that cap themselves (see MAX_BRUTE_FORCE_N in solver.cpp) since
// this header has no opinion on what the caller considers "too slow".
inline Tour solve_brute_force(const Instance& inst) {
    const int n = inst.size();
    Tour best;
    if (n <= 1) {
        best.order = (n == 1) ? std::vector<int>{0} : std::vector<int>{};
        best.length = 0.0;
        return best;
    }

    std::vector<int> perm(n - 1);
    std::iota(perm.begin(), perm.end(), 1); // cities 1..n-1

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
