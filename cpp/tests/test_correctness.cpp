#include <cassert>
#include <cmath>
#include <iostream>
#include <sstream>
#include <vector>
#include "../include/tsp_types.hpp"
#include "../include/instance_generator.hpp"
#include "../include/exact/brute_force.hpp"
#include "../include/exact/held_karp.hpp"
#include "../include/approx/nearest_neighbor.hpp"
#include "../include/approx/greedy_edge.hpp"

namespace {

bool is_valid_cycle(const std::vector<int>& order, int n) {
    if (n == 0) return order.empty();
    if (static_cast<int>(order.size()) != n) return false;
    std::vector<bool> seen(n, false);
    for (int city : order) {
        if (city < 0 || city >= n || seen[city]) return false;
        seen[city] = true;
    }
    return true;
}

bool nearly_equal(double a, double b, double eps = 1e-6) {
    return std::fabs(a - b) < eps * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

template <typename Fn>
auto run_quiet(Fn&& fn) {
    std::ostringstream discard;
    std::streambuf* old = std::cout.rdbuf(discard.rdbuf());
    auto result = fn();
    std::cout.rdbuf(old);
    return result;
}

int failures = 0;

void check(bool condition, const std::string& label) {
    if (condition) {
        std::cout << "[PASS] " << label << '\n';
    } else {
        std::cout << "[FAIL] " << label << '\n';
        ++failures;
    }
}

}

int main() {

    for (int n : {1, 2, 3}) {
        auto pts = generate_random_instance(n, 42);
        Instance inst(pts);

        Tour bf = run_quiet([&] { return solve_brute_force(inst); });
        Tour hk = run_quiet([&] { return solve_held_karp(inst); });
        Tour nn = run_quiet([&] { return solve_nearest_neighbor(inst); });
        Tour ge = run_quiet([&] { return solve_greedy_edge(inst); });

        check(is_valid_cycle(bf.order, n), "brute_force valid cycle, n=" + std::to_string(n));
        check(is_valid_cycle(hk.order, n), "held_karp valid cycle, n=" + std::to_string(n));
        check(is_valid_cycle(nn.order, n), "nearest_neighbor valid cycle, n=" + std::to_string(n));
        check(is_valid_cycle(ge.order, n), "greedy_edge valid cycle, n=" + std::to_string(n));

        if (n >= 2) {
            check(nearly_equal(bf.length, hk.length),
                  "brute_force == held_karp length, n=" + std::to_string(n));
        }
    }

    for (unsigned seed = 1; seed <= 8; ++seed) {
        int n = 5 + static_cast<int>(seed % 4);
        auto pts = generate_random_instance(n, seed * 1000);
        Instance inst(pts);

        Tour bf = run_quiet([&] { return solve_brute_force(inst); });
        Tour hk = run_quiet([&] { return solve_held_karp(inst); });

        check(nearly_equal(bf.length, hk.length),
              "brute_force == held_karp length, seed=" + std::to_string(seed) +
              " n=" + std::to_string(n));
        check(is_valid_cycle(bf.order, n) && is_valid_cycle(hk.order, n),
              "valid cycles from exact algorithms, seed=" + std::to_string(seed));
    }

    for (int n : {10, 25, 60}) {
        auto pts = generate_random_instance(n, 7);
        Instance inst(pts);

        Tour nn = run_quiet([&] { return solve_nearest_neighbor(inst); });
        Tour ge = run_quiet([&] { return solve_greedy_edge(inst); });

        check(is_valid_cycle(nn.order, n), "nearest_neighbor valid cycle, n=" + std::to_string(n));
        check(is_valid_cycle(ge.order, n), "greedy_edge valid cycle, n=" + std::to_string(n));
        check(nn.length > 0.0 && ge.length > 0.0,
              "positive tour length, n=" + std::to_string(n));
    }

    std::cout << '\n';
    if (failures == 0) {
        std::cout << "All tests passed.\n";
        return 0;
    }
    std::cout << failures << " test(s) failed.\n";
    return 1;
}
