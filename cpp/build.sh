#!/usr/bin/env bash
# Builds bin/solver.exe and bin/test_correctness.exe with plain g++.
# (No `make`/`cmake` assumed to be installed.)
set -e
cd "$(dirname "$0")"
mkdir -p bin

CXXFLAGS="-std=c++17 -O2 -Wall -Iinclude"

echo "Building solver..."
g++ $CXXFLAGS -o bin/solver.exe src/solver.cpp

echo "Building test_correctness..."
g++ $CXXFLAGS -o bin/test_correctness.exe tests/test_correctness.cpp

echo "Done: bin/solver.exe, bin/test_correctness.exe"
