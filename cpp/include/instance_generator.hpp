#pragma once

#include <random>
#include <vector>
#include "tsp_types.hpp"

inline std::vector<Point> generate_random_instance(int n, unsigned seed, double box = 1000.0) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(0.0, box);
    std::vector<Point> pts(n);
    for (auto& p : pts) {
        p.x = dist(rng);
        p.y = dist(rng);
    }
    return pts;
}
