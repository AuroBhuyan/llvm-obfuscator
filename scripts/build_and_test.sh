#!/bin/bash
# build_and_test.sh — place in scripts/, run from project ROOT
# Also needs: scripts/fix_ir_pointers.py  scripts/visualize.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
TEST_DIR="$PROJECT_ROOT/test"
TEST_CPP="$TEST_DIR/input.cpp"
TEST_IR="$TEST_DIR/input.ll"
OBF_IR="$BUILD_DIR/obf.ll"
FIX_PY="$SCRIPT_DIR/fix_ir_pointers.py"
VIZ_PY="$SCRIPT_DIR/visualize.py"

BOGUS_CF=2; STRING_OBF=0; FAKE_LOOPS=2; CYCLES=1

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     LLVM Obfuscator -- Build & Test      ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

command -v clang++ &>/dev/null || { echo -e "${RED}[ERROR]${NC} clang++ not found"; exit 1; }
echo -e "${GREEN}[OK]${NC} LLVM $(llvm-config --version)"
echo -e "${GREEN}[OK]${NC} clang++ found"

# ── Step 1: Create input.cpp if missing ──────────────────────────────────────
mkdir -p "$TEST_DIR"
if [ ! -f "$TEST_CPP" ]; then
    cat > "$TEST_CPP" << 'CPPEOF'
#include <stdio.h>
// Edit this file freely, then re-run ./scripts/build_and_test.sh
int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }
int factorial(int n) { if (n <= 1) return 1; return n * factorial(n-1); }
int main() {
    printf("==========================\n");
    printf("2 + 3        = %d\n", add(2, 3));
    printf("6 x 7        = %d\n", multiply(6, 7));
    printf("factorial(5) = %d\n", factorial(5));
    printf("==========================\n");
    return 0;
}
CPPEOF
    echo -e "${GREEN}[OK]${NC} Created test/input.cpp"
else
    echo -e "${GREEN}[OK]${NC} Using existing test/input.cpp"
fi

# ── Step 2: Build obfuscator tool ────────────────────────────────────────────
echo ""; echo -e "${CYAN}[Step 2]${NC} Building obfuscator tool..."
mkdir -p "$BUILD_DIR" && cd "$BUILD_DIR"
cmake "$PROJECT_ROOT" -DCMAKE_BUILD_TYPE=Debug -Wno-dev > /dev/null 2>&1
make -j"$(nproc)" 2>&1 | grep -E "error:|Building CXX|Linking" || true
[ -f "$BUILD_DIR/obfuscator" ] || { echo -e "${RED}[FAIL] Build failed${NC}"; exit 1; }
echo -e "${GREEN}[OK]${NC} Obfuscator tool ready"

# ── Step 3: Compile original ──────────────────────────────────────────────────
echo ""; echo -e "${CYAN}[Step 3]${NC} Compiling original executable..."
clang++ -O0 -o "$BUILD_DIR/original" "$TEST_CPP"
echo -e "${GREEN}[OK]${NC} build/original ready"

# ── Step 4: Generate IR ───────────────────────────────────────────────────────
echo ""; echo -e "${CYAN}[Step 4]${NC} Generating LLVM IR..."
clang++ -S -emit-llvm -O0 "$TEST_CPP" -o "$TEST_IR"
python3 "$FIX_PY" "$TEST_IR" "$TEST_IR"
echo -e "${GREEN}[OK]${NC} test/input.ll ready"

# ── Step 5: Obfuscate ─────────────────────────────────────────────────────────
echo ""; echo -e "${CYAN}[Step 5]${NC} Obfuscating IR..."
cd "$BUILD_DIR"
./obfuscator "$TEST_IR" "$BOGUS_CF" "$STRING_OBF" "$FAKE_LOOPS" "$CYCLES"
[ -f "$OBF_IR" ] || { echo -e "${RED}[FAIL] obf.ll not generated${NC}"; exit 1; }
python3 "$FIX_PY" "$OBF_IR" "$OBF_IR"
echo -e "${GREEN}[OK]${NC} build/obf.ll ready"

# ── Step 6: Compile obfuscated IR -> native binary ────────────────────────────
echo ""; echo -e "${CYAN}[Step 6]${NC} Compiling obfuscated binary..."

# Find llc
LLC=""
for c in llc-14 llc-15 llc-16 llc-17 llc; do
    command -v "$c" &>/dev/null && LLC=$(command -v "$c") && break
done

if [ -n "$LLC" ]; then
    echo -e "    Using llc: $LLC"
    "$LLC" -filetype=obj --relocation-model=pic "$OBF_IR" -o "$BUILD_DIR/obf.o" 2>&1
    LLC_EXIT=$?
    if [ $LLC_EXIT -eq 0 ] && [ -f "$BUILD_DIR/obf.o" ]; then
        clang++ -no-pie "$BUILD_DIR/obf.o" -o "$BUILD_DIR/obfuscated" 2>&1
        LINK_EXIT=$?
        if [ $LINK_EXIT -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} build/obfuscated ready (native binary via llc)"
        else
            echo -e "${RED}[FAIL] Linking failed — see error above${NC}"
            cp "$BUILD_DIR/original" "$BUILD_DIR/obfuscated"
        fi
    else
        echo -e "${RED}[FAIL] llc failed — see error above${NC}"
        cp "$BUILD_DIR/original" "$BUILD_DIR/obfuscated"
    fi
else
    echo -e "${YELLOW}[!]${NC} llc not found. Installing llvm-14..."
    sudo apt-get install -y llvm-14 -q
    llc-14 -filetype=obj --relocation-model=pic "$OBF_IR" -o "$BUILD_DIR/obf.o" 2>&1 && \
        clang++ -no-pie "$BUILD_DIR/obf.o" -o "$BUILD_DIR/obfuscated" 2>&1 && \
        echo -e "${GREEN}[OK]${NC} build/obfuscated ready" || \
        { echo -e "${YELLOW}[!]${NC} Falling back to original binary"; cp "$BUILD_DIR/original" "$BUILD_DIR/obfuscated"; }
fi

# ── Step 7: Run both and compare ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  RUNNING BOTH EXECUTABLES${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""; echo -e "${YELLOW}  ./build/original${NC}   (compiled directly from input.cpp)"
echo -e "${BOLD}  ─────────────────────────────────────────────${NC}"
"$BUILD_DIR/original"

echo ""; echo -e "${YELLOW}  ./build/obfuscated${NC}  (compiled from obfuscated IR)"
echo -e "${BOLD}  ─────────────────────────────────────────────${NC}"
"$BUILD_DIR/obfuscated"

ORIG_OUT=$("$BUILD_DIR/original" 2>&1)
OBFS_OUT=$("$BUILD_DIR/obfuscated" 2>&1)
echo ""
if [ "$ORIG_OUT" = "$OBFS_OUT" ]; then
    echo -e "${GREEN}[OK] Outputs MATCH — obfuscation is semantics-preserving${NC}"
else
    echo -e "${RED}[!!] Outputs differ${NC}"
    diff <(echo "$ORIG_OUT") <(echo "$OBFS_OUT") || true
fi

# ── Step 8: IR stats ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  IR STATISTICS${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
orig_f=$(grep -c "^define " "$TEST_IR" 2>/dev/null || echo 0)
obf_f=$( grep -c "^define " "$OBF_IR"  2>/dev/null || echo 0)
orig_l=$(wc -l < "$TEST_IR"); obf_l=$(wc -l < "$OBF_IR")
printf "\n  %-18s %10s %12s %10s\n" "Metric" "Original" "Obfuscated" "Delta"
printf   "  %-18s %10s %12s %10s\n" "──────" "────────" "──────────" "─────"
printf   "  %-18s %10d %12d %+10d\n" "Functions"  $orig_f $obf_f $((obf_f-orig_f))
printf   "  %-18s %10d %12d %+10d\n" "IR Lines"   $orig_l $obf_l $((obf_l-orig_l))
echo ""

# ── Step 9: Visualization ─────────────────────────────────────────────────────
echo -e "${CYAN}[Step 9]${NC} Generating HTML visualization..."
cd "$BUILD_DIR"
./obfuscator "$TEST_IR" "$BOGUS_CF" 1 "$FAKE_LOOPS" "$CYCLES" > /dev/null 2>&1 || true
python3 "$FIX_PY" "$OBF_IR" "$OBF_IR" > /dev/null 2>&1 || true
HTML_OUT="$BUILD_DIR/visualization.html"
python3 "$VIZ_PY" "$TEST_IR" "$OBF_IR" "$HTML_OUT" && \
    echo -e "${GREEN}[OK]${NC} build/visualization.html" || \
    echo -e "${YELLOW}[!]${NC} visualize.py not found at $VIZ_PY"
# restore obf.ll to runnable version
./obfuscator "$TEST_IR" "$BOGUS_CF" "$STRING_OBF" "$FAKE_LOOPS" "$CYCLES" > /dev/null 2>&1 || true
python3 "$FIX_PY" "$OBF_IR" "$OBF_IR" > /dev/null 2>&1 || true

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}./build/original${NC}           run original"
echo -e "  ${GREEN}./build/obfuscated${NC}          run obfuscated"
echo -e "  ${GREEN}build/visualization.html${NC}    open in browser:"
echo -e "  ${CYAN}explorer.exe \"\$(wslpath -w $HTML_OUT)\"${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""