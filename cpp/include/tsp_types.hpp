#pragma once

#include <vector>
#include <cmath>
#include <chrono>

struct Point {
    double x = 0.0;
    double y = 0.0;
};

// Symmetric Euclidean TSP instance. Precomputes the full distance matrix
// once so every algorithm queries dist(i, j) in O(1).
class Instance {
public:
    explicit Instance(std::vector<Point> pts) : points_(std::move(pts)) {
        const int n = size();
        dist_.assign(n, std::vector<double>(n, 0.0));
        for (int i = 0; i < n; ++i) {
            for (int j = i + 1; j < n; ++j) {
                double dx = points_[i].x - points_[j].x;
                double dy = points_[i].y - points_[j].y;
                double d = std::sqrt(dx * dx + dy * dy);
                dist_[i][j] = d;
                dist_[j][i] = d;
            }
        }
    }

    int size() const { return static_cast<int>(points_.size()); }
    const Point& point(int i) const { return points_[i]; }
    double dist(int i, int j) const { return dist_[i][j]; }

private:
    std::vector<Point> points_;
    std::vector<std::vector<double>> dist_;
};

struct Tour {
    std::vector<int> order; // permutation of [0, n)
    double length = 0.0;
};

inline double tour_length(const Instance& inst, const std::vector<int>& order) {
    double total = 0.0;
    const int n = static_cast<int>(order.size());
    for (int i = 0; i < n; ++i) {
        total += inst.dist(order[i], order[(i + 1) % n]);
    }
    return total;
}

using Clock = std::chrono::steady_clock;

inline double elapsed_ms(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double, std::milli>(end - start).count();
}
