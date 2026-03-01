#!/usr/bin/env bash
set -euo pipefail

# ── LLVM Obfuscator — build.sh ────────────────────────────────────────────────
# Builds the project using CMake. Run from the repo root.
#
# Usage:
#   ./scripts/build.sh             # Release build
#   ./scripts/build.sh --debug     # Debug build
#   ./scripts/build.sh --clean     # Clean rebuild

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_TYPE="Release"
CLEAN=0

for arg in "$@"; do
    case "$arg" in
        --debug) BUILD_TYPE="Debug"   ;;
        --clean) CLEAN=1              ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

BUILD_DIR="$ROOT/build"

if [[ $CLEAN -eq 1 && -d "$BUILD_DIR" ]]; then
    echo "[build] Cleaning $BUILD_DIR"
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "[build] Configuring ($BUILD_TYPE)..."
cmake "$ROOT" \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

echo "[build] Compiling..."
cmake --build . --parallel "$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"

echo ""
echo "✅  Build complete: $BUILD_DIR/obfuscator"
echo ""
echo "Usage examples:"
echo "  # Compile a sample to IR first:"
echo "  clang -emit-llvm -S -O0 tests/samples/sample_hello.c -o /tmp/hello.ll"
echo ""
echo "  # Run obfuscator:"
echo "  $BUILD_DIR/obfuscator /tmp/hello.ll --bogus-cf 2 --string-obf --fake-loops 2 --cycles 2 --report report.json"
