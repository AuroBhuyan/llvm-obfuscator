#!/usr/bin/env bash
set -euo pipefail

# ── LLVM Obfuscator — run_demo.sh ─────────────────────────────────────────────
# End-to-end demo: compiles sample programs to IR, obfuscates them, and
# runs Phase 10 validation checks.
#
# Prerequisites: clang, llc, the built obfuscator binary, and optionally
# the `strings` utility.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
OBF="$ROOT/build/obfuscator"
SAMPLES="$ROOT/tests/samples"
OUTDIR="$ROOT/demo_output"

if [[ ! -f "$OBF" ]]; then
    echo "[demo] Obfuscator not built. Run: ./scripts/build.sh"
    exit 1
fi

mkdir -p "$OUTDIR"

run_test() {
    local name="$1"
    local src="$SAMPLES/${name}.c"
    local ll="$OUTDIR/${name}.ll"
    local obj="$OUTDIR/${name}_obfuscated.o"
    local report="$OUTDIR/${name}_report.json"
    local bin="$OUTDIR/${name}_original"
    local obin="$OUTDIR/${name}_obfuscated_exec"

    echo "────────────────────────────────────────────────"
    echo "[demo] Testing: $name"
    echo "────────────────────────────────────────────────"

    # Phase 1: Compile to IR
    echo "[Phase 1] Compiling $name.c -> IR"
    clang -emit-llvm -S -O0 "$src" -o "$ll"

    # Also compile original binary for comparison
    clang -O0 "$src" -o "$bin" 2>/dev/null || true

    # Phases 4-9: Obfuscate
    echo "[Phase 4-9] Obfuscating..."
    "$OBF" "$ll" \
        --bogus-cf 3 \
        --string-obf \
        --fake-loops 2 \
        --cycles 2 \
        --seed 12345 \
        --output "$obj" \
        --report "$report" \
        --verbose

    # Phase 10: Validation
    echo ""
    echo "[Phase 10] Validation"

    # Check report was written
    if [[ -f "$report" ]]; then
        echo "  ✅ report.json written"
        # Print basic metrics from report
        python3 -c "
import json, sys
with open('$report') as f:
    r = json.load(f)
d = r.get('delta', {})
print(f'  BasicBlock delta: +{d.get(\"basic_blocks_pct\",0):.1f}%')
print(f'  Instruction delta: +{d.get(\"instructions_pct\",0):.1f}%')
" 2>/dev/null || echo "  (install python3 for delta display)"
    else
        echo "  ❌ report.json NOT written"
    fi

    # Check object file was written
    if [[ -f "$obj" ]]; then
        local orig_size=0
        local obf_size
        obf_size=$(wc -c < "$obj")
        echo "  ✅ Object file written ($obf_size bytes)"
    else
        echo "  ❌ Object file NOT written"
    fi

    # String exposure check
    if command -v strings &>/dev/null && [[ -f "$obj" ]]; then
        local plain_strings
        plain_strings=$(strings "$obj" | grep -c '.\{4\}' || true)
        echo "  Readable strings in obfuscated obj: $plain_strings"
    fi

    echo ""
}

run_test "sample_hello"
run_test "sample_crypto"

echo "════════════════════════════════════════════════"
echo "✅  Demo complete. Outputs in: $OUTDIR"
echo "════════════════════════════════════════════════"
