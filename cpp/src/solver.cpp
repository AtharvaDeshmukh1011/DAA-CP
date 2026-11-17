#include <iostream>
#include <streambuf>
#include <string>
#include <vector>
#include "tsp_types.hpp"
#include "instance_generator.hpp"
#include "lower_bound.hpp"
#include "exact/brute_force.hpp"
#include "exact/held_karp.hpp"
#include "approx/nearest_neighbor.hpp"
#include "approx/greedy_edge.hpp"

namespace {
struct NullBuffer : std::streambuf {
    int overflow(int c) override { return c; }
};

constexpr int MAX_BRUTE_FORCE_N = 10;
constexpr int MAX_HELD_KARP_N = 20;

void emit_error(const std::string& message) {
    std::cout << "{\"type\":\"error\",\"message\":\"" << message << "\"}\n";
    std::cout.flush();
}
}

int main(int argc, char** argv) {
    if (argc < 2) {
        emit_error("usage: solver <brute_force|held_karp|nearest_neighbor|greedy_edge>");
        return 1;
    }
    std::string algo = argv[1];

    int n;
    if (!(std::cin >> n) || n < 0) {
        emit_error("invalid input: expected city count on first line");
        return 1;
    }
    std::vector<Point> pts(n);
    for (auto& p : pts) {
        if (!(std::cin >> p.x >> p.y)) {
            emit_error("invalid input: expected n lines of 'x y'");
            return 1;
        }
    }
    Instance inst(pts);

    if (algo == "brute_force" && n > MAX_BRUTE_FORCE_N) {
        emit_error("brute_force is capped at " + std::to_string(MAX_BRUTE_FORCE_N) +
                    " cities (n! blows up fast) -- got " + std::to_string(n));
        return 1;
    }
    if (algo == "held_karp" && n > MAX_HELD_KARP_N) {
        emit_error("held_karp is capped at " + std::to_string(MAX_HELD_KARP_N) +
                    " cities (memory is O(n * 2^n)) -- got " + std::to_string(n));
        return 1;
    }

    bool quiet = argc > 2 && std::string(argv[2]) == "quiet";
    NullBuffer null_buffer;
    std::streambuf* real_out = std::cout.rdbuf();
    if (quiet) std::cout.rdbuf(&null_buffer);

    auto start = Clock::now();
    Tour result;
    if (algo == "brute_force") {
        result = solve_brute_force(inst);
    } else if (algo == "held_karp") {
        result = solve_held_karp(inst);
    } else if (algo == "nearest_neighbor") {
        result = solve_nearest_neighbor(inst);
    } else if (algo == "greedy_edge") {
        result = solve_greedy_edge(inst);
    } else {
        emit_error("unknown algorithm: " + algo);
        return 1;
    }
    auto end = Clock::now();
    std::cout.rdbuf(real_out);

    double lb = mst_lower_bound(inst);

    std::cout << "{\"type\":\"done\",\"tour\":";
    json_int_array(std::cout, result.order);
    std::cout << ",\"length\":" << result.length
               << ",\"time_ms\":" << elapsed_ms(start, end)
               << ",\"lower_bound\":" << lb << "}";
    end_line(std::cout);

    return 0;
}
