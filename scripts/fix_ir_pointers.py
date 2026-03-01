#!/usr/bin/env python3
"""
fix_ir_pointers.py — Complete LLVM 14 opaque->typed pointer fixer.
Usage: python3 fix_ir_pointers.py input.ll output.ll
"""
import sys, re

def fix_ir(content):
    # Build global type map: @name -> type string
    gmap = {}
    for m in re.finditer(
        r'^(@[\w.]+)\s*=.*?(?:constant|global)\s+(\[[0-9]+ x \w+\]|i\d+|float|double)',
        content, re.MULTILINE):
        gmap[m.group(1)] = m.group(2).strip()

    def gep_or_i8(name):
        """Return proper typed ref for a global: GEP for arrays, i8* otherwise."""
        gtype = gmap.get(name, '')
        arr = re.match(r'\[(\d+) x i8\]', gtype)
        if arr:
            n = arr.group(1)
            return f'getelementptr inbounds ([{n} x i8], [{n} x i8]* {name}, i32 0, i32 0)'
        return f'i8* {name}'

    lines = []
    for line in content.splitlines(keepends=True):
        # 1. store iN X, ptr %y / ptr @y
        line = re.sub(r'\bstore\s+(i\d+|float|double)\s+(.*?),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'store {m.group(1)} {m.group(2)}, {m.group(1)}* {m.group(3)}', line)
        # 2. load iN, ptr %y / ptr @y
        line = re.sub(r'\bload\s+(i\d+|float|double),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'load {m.group(1)}, {m.group(1)}* {m.group(2)}', line)
        # 3. getelementptr [inbounds] iN, ptr %y
        line = re.sub(r'\bgetelementptr(\s+inbounds)?\s+(i\d+|float|double),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'getelementptr{m.group(1) or ""} {m.group(2)}, {m.group(2)}* {m.group(3)}', line)
        # 4. function type sig: (ptr, ...) / (ptr)
        line = re.sub(r'\(ptr,', '(i8*,', line)
        line = re.sub(r'\(ptr\)', '(i8*)', line)
        # 5. ptr noundef @name (call args with noundef)
        line = re.sub(r'\bptr\s+noundef\s+(@[\w.]+)', lambda m: gep_or_i8(m.group(1)), line)
        # 6. i8* @name -> proper GEP if it's an array global (fixes type mismatch)
        line = re.sub(r'\bi8\*\s+(@[\w.]+)', lambda m: gep_or_i8(m.group(1)), line)
        # 7. catch-all: remaining ptr %x or ptr @x
        line = re.sub(r'\bptr\s+([%@][\w.]+)', r'i8* \1', line)
        lines.append(line)
    return ''.join(lines)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <input.ll> <output.ll>'); sys.exit(1)
    with open(sys.argv[1], 'r', errors='replace') as f:
        content = f.read()
    fixed = fix_ir(content)
    with open(sys.argv[2], 'w') as f:
        f.write(fixed)
    print(f'[fix_ir] Done: {sys.argv[2]}')