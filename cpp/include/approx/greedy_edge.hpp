#pragma once

#include <vector>
#include <algorithm>
#include <numeric>
#include <iostream>
#include "../tsp_types.hpp"
#include "../step_emitter.hpp"

namespace greedy_detail {

struct DisjointSet {
    std::vector<int> parent;
    explicit DisjointSet(int n) : parent(n) { std::iota(parent.begin(), parent.end(), 0); }
    int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
    void unite(int a, int b) { parent[find(a)] = find(b); }
};

struct Edge {
    int u, v;
    double dist;
};

} // namespace greedy_detail

// Time complexity: O(n^2 log n) -- generate all C(n,2) candidate edges,
// sort them, then scan once with union-find (near O(alpha(n)) per query).
// Space: O(n^2) for the candidate edge list.
//
// Classic "multi-fragment" greedy-edge heuristic: repeatedly take the
// cheapest remaining edge that doesn't give a vertex degree 3 and doesn't
// close a sub-cycle early (unless it's the final edge completing the full
// Hamiltonian cycle). On metric instances this reliably beats nearest
// neighbor's worst cases.
inline Tour solve_greedy_edge(const Instance& inst) {
    using namespace greedy_detail;
    const int n = inst.size();
    Tour result;
    if (n <= 1) {
        result.order = (n == 1) ? std::vector<int>{0} : std::vector<int>{};
        result.length = 0.0;
        return result;
    }
    std::vector<Edge> edges;
    edges.reserve(static_cast<size_t>(n) * (n - 1) / 2);
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            edges.push_back({i, j, inst.dist(i, j)});
        }
    }
    std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) {
        return a.dist < b.dist;
    });

    std::vector<int> degree(n, 0);
    DisjointSet dsu(n);
    std::vector<std::vector<int>> adj(n);
    int edges_added = 0;

    for (const auto& e : edges) {
        if (edges_added == n) break;

        bool degree_ok = degree[e.u] < 2 && degree[e.v] < 2;
        bool would_close_subcycle = dsu.find(e.u) == dsu.find(e.v);
        bool is_final_edge = (edges_added == n - 1);
        bool accepted = degree_ok && (!would_close_subcycle || is_final_edge);

        if (accepted) {
            dsu.unite(e.u, e.v);
            degree[e.u]++;
            degree[e.v]++;
            adj[e.u].push_back(e.v);
            adj[e.v].push_back(e.u);
            edges_added++;
        }

        std::cout << "{\"type\":\"step\",\"algo\":\"greedy_edge\",\"edge\":[" << e.u << ',' << e.v
                   << "],\"dist\":" << e.dist << ",\"accepted\":" << (accepted ? "true" : "false") << "}";
        end_line(std::cout);
    }

    std::vector<int> path;
    path.reserve(n);
    std::vector<bool> visited(n, false);
    int current = 0, prev = -1;
    for (int step = 0; step < n; ++step) {
        path.push_back(current);
        visited[current] = true;
        int next = -1;
        for (int cand : adj[current]) {
            if (cand != prev && !visited[cand]) { next = cand; break; }
        }
        if (next == -1) {
            for (int cand : adj[current]) {
                if (!visited[cand]) { next = cand; break; }
            }
        }
        prev = current;
        current = next;
    }

    result.order = path;
    result.length = tour_length(inst, path);
    return result;
}
