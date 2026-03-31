#!/usr/bin/env python3
"""
fix_ir_pointers.py — Complete LLVM 14 opaque->typed pointer fixer.
Usage: python3 fix_ir_pointers.py input.ll output.ll
"""
import sys, re

def fix_module_flags(content):
    """
    LLVM 14 only accepts module flag behavior values 1-6.
    Values >= 7 (e.g. i32 8 = Min, added in LLVM 15+) cause llc-14 to reject the module.
    Strip any metadata lines that use an unsupported behavior value.
    """
    # Remove metadata definition lines with behavior >= 7
    content = re.sub(r'^(!\d+ = !\{i32 [7-9]\d*,.*\})\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^(!\d+ = !\{i32 \d{2,},.*\})\s*$', '', content, flags=re.MULTILINE)
    # Remove references to those stripped entries from !llvm.module.flags
    # (dangling !N refs in the flags list will also fail verification)
    # Simplest: remove the whole !llvm.module.flags named metadata and let llc proceed without it
    content = re.sub(r'^!llvm\.module\.flags\s*=.*$', '', content, flags=re.MULTILINE)
    # Clean up any blank lines left behind
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

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

    def gep_or_i8_typed(name):
        """Like gep_or_i8 but always includes i8* type prefix (needed inside call args)."""
        gtype = gmap.get(name, '')
        arr = re.match(r'\[(\d+) x i8\]', gtype)
        if arr:
            n = arr.group(1)
            return f'i8* getelementptr inbounds ([{n} x i8], [{n} x i8]* {name}, i32 0, i32 0)'
        return f'i8* {name}'

    lines = []
    for line in content.splitlines(keepends=True):
        is_call = bool(re.search(r'\bcall\b', line))

        # 1. store iN X, ptr %y / ptr @y
        line = re.sub(r'\bstore\s+(i\d+|float|double)\s+(.*?),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'store {m.group(1)} {m.group(2)}, {m.group(1)}* {m.group(3)}', line)
        # 2. load iN, ptr %y / ptr @y
        line = re.sub(r'\bload\s+(i\d+|float|double),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'load {m.group(1)}, {m.group(1)}* {m.group(2)}', line)
        # 3. getelementptr [inbounds] iN, ptr %y
        line = re.sub(r'\bgetelementptr(\s+inbounds)?\s+(i\d+|float|double),\s*ptr\s+([%@][\w.]+)',
            lambda m: f'getelementptr{m.group(1) or ""} {m.group(2)}, {m.group(2)}* {m.group(3)}', line)
        # 4. function type sig: (ptr, ...) / (ptr) / ptr noundef anywhere
        line = re.sub(r'\(ptr,', '(i8*,', line)
        line = re.sub(r'\(ptr\)', '(i8*)', line)
        line = re.sub(r'\bptr noundef\b', 'i8* noundef', line)
        # 5. i8* noundef @name — use typed variant on call lines
        if is_call:
            line = re.sub(r'\bi8\*\s+noundef\s+(@[\w.]+)', lambda m: gep_or_i8_typed(m.group(1)), line)
        else:
            line = re.sub(r'\bi8\*\s+noundef\s+(@[\w.]+)', lambda m: gep_or_i8(m.group(1)), line)
        # 6. i8* @name — use typed variant on call lines
        if is_call:
            line = re.sub(r'\bi8\*\s+(@[\w.]+)', lambda m: gep_or_i8_typed(m.group(1)), line)
        else:
            line = re.sub(r'\bi8\*\s+(@[\w.]+)', lambda m: gep_or_i8(m.group(1)), line)
        # 7. catch-all: remaining ptr %x or ptr @x
        line = re.sub(r'\bptr\s+([%@][\w.]+)', r'i8* \1', line)
        lines.append(line)

    result = ''.join(lines)
    result = fix_module_flags(result)
    return result

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <input.ll> <output.ll>'); sys.exit(1)
    with open(sys.argv[1], 'r', errors='replace') as f:
        content = f.read()
    fixed = fix_ir(content)
    with open(sys.argv[2], 'w') as f:
        f.write(fixed)
    print(f'[fix_ir] Done: {sys.argv[2]}')