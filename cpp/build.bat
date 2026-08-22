@echo off
REM Builds bin\solver.exe and bin\test_correctness.exe with plain g++.
REM (No make/cmake assumed to be installed.)
cd /d "%~dp0"
if not exist bin mkdir bin

echo Building solver...
g++ -std=c++17 -O2 -Wall -Iinclude -o bin\solver.exe src\solver.cpp
if errorlevel 1 exit /b 1

echo Building test_correctness...
g++ -std=c++17 -O2 -Wall -Iinclude -o bin\test_correctness.exe tests\test_correctness.cpp
if errorlevel 1 exit /b 1

echo Done: bin\solver.exe, bin\test_correctness.exe
