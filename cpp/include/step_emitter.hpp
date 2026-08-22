#pragma once

#include <vector>
#include <iostream>

// Minimal hand-rolled JSON writing -- we only ever emit, never parse, on the
// C++ side, so a full JSON library would be overkill (and unavailable
// without a package manager here). One line per step keeps this a simple,
// greppable streaming protocol that the GUI reads line-by-line.

inline void json_int_array(std::ostream& os, const std::vector<int>& v) {
    os << '[';
    for (size_t i = 0; i < v.size(); ++i) {
        if (i) os << ',';
        os << v[i];
    }
    os << ']';
}

inline void end_line(std::ostream& os) {
    os << '\n';
    os.flush();
}
