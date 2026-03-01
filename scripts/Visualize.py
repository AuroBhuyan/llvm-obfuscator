#!/usr/bin/env python3
"""
visualize.py — Generates a stunning side-by-side HTML visualization
of original vs obfuscated LLVM IR, explained for non-experts.

Usage:
    python3 scripts/visualize.py test/input.ll build/obf.ll build/visualization.html
"""

import sys
import re
import html
import json
from collections import defaultdict

# ── IR Parsing ──────────────────────────────────────────────────────────────

def parse_ir(path):
    with open(path, 'r', errors='replace') as f:
        lines = f.readlines()

    functions = []
    current_fn = None
    current_bb = None
    bb_name_counter = [0]

    for line in lines:
        stripped = line.rstrip()

        # New function
        fn_match = re.match(r'^define\s+.*?@([\w\.]+)\s*\(', stripped)
        if fn_match:
            current_fn = {
                'name': fn_match.group(1),
                'raw': stripped,
                'blocks': [],
                'line_count': 0,
            }
            functions.append(current_fn)
            current_bb = None
            continue

        if current_fn is None:
            continue

        # End of function
        if stripped == '}':
            if current_bb:
                current_fn['blocks'].append(current_bb)
                current_bb = None
            current_fn = None
            continue

        # Basic block label
        bb_match = re.match(r'^([\w\.]+):(\s*;.*)?$', stripped)
        if bb_match or re.match(r'^\d+:', stripped):
            if current_bb:
                current_fn['blocks'].append(current_bb)
            label = bb_match.group(1) if bb_match else stripped.split(':')[0]
            bb_name_counter[0] += 1
            current_bb = {
                'label': label,
                'instructions': [],
                'kind': classify_block(label),
            }
            continue

        # Instruction
        if current_bb is not None and stripped.startswith('  '):
            current_fn['line_count'] += 1
            inst = stripped.strip()
            current_bb['instructions'].append({
                'raw': inst,
                'kind': classify_instruction(inst),
                'explanation': explain_instruction(inst),
            })
        elif current_fn is not None and stripped.startswith('  '):
            # First block (entry, no label shown)
            if current_bb is None:
                current_bb = {
                    'label': 'entry',
                    'instructions': [],
                    'kind': 'entry',
                }
            current_fn['line_count'] += 1
            inst = stripped.strip()
            current_bb['instructions'].append({
                'raw': inst,
                'kind': classify_instruction(inst),
                'explanation': explain_instruction(inst),
            })

    return functions


def classify_block(label):
    label = label.lower()
    if 'fake' in label or 'bogus' in label:
        return 'fake'
    if 'real' in label:
        return 'real'
    if 'entry' in label:
        return 'entry'
    if 'junk' in label:
        return 'junk'
    if 'opq' in label:
        return 'opaque'
    return 'normal'


def classify_instruction(inst):
    inst_lower = inst.lower()
    for kw in ['br', 'ret', 'switch', 'indirectbr']:
        if inst_lower.startswith(kw):
            return 'branch'
    for kw in ['call', 'invoke']:
        if kw in inst_lower:
            return 'call'
    for kw in ['alloca', 'load', 'store', 'getelementptr']:
        if kw in inst_lower:
            return 'memory'
    for kw in ['add', 'sub', 'mul', 'div', 'xor', 'and', 'or', 'shl', 'lshr']:
        if kw in inst_lower:
            return 'arithmetic'
    for kw in ['icmp', 'fcmp', 'select']:
        if kw in inst_lower:
            return 'compare'
    for kw in ['phi']:
        if kw in inst_lower:
            return 'phi'
    for kw in ['opq', 'bogus', 'fake', 'junk']:
        if kw in inst_lower:
            return 'obfuscated'
    return 'other'


def explain_instruction(inst):
    inst_lower = inst.lower()
    if inst_lower.startswith('alloca'):
        return "📦 Allocates stack memory for a variable"
    if inst_lower.startswith('store'):
        return "💾 Writes a value into memory"
    if inst_lower.startswith('load'):
        return "📖 Reads a value from memory"
    if inst_lower.startswith('call'):
        return "📞 Calls a function"
    if inst_lower.startswith('ret'):
        return "🔙 Returns from this function"
    if inst_lower.startswith('br'):
        if 'true' in inst_lower or 'false' in inst_lower or 'i1' in inst_lower:
            return "🔀 Conditional branch — takes different paths based on a condition"
        return "➡️  Unconditional jump to another block"
    if inst_lower.startswith('icmp'):
        return "⚖️  Integer comparison (checks ==, !=, <, > etc.)"
    if 'opq' in inst_lower or 'bogus' in inst_lower:
        return "🎭 OBFUSCATION: Fake condition that always evaluates the same way"
    if 'junk' in inst_lower or 'fake' in inst_lower:
        return "🗑️  OBFUSCATION: Dead junk code inserted to confuse analysis"
    if inst_lower.startswith('add'):
        return "➕ Addition"
    if inst_lower.startswith('sub'):
        return "➖ Subtraction"
    if inst_lower.startswith('mul'):
        return "✖️  Multiplication"
    if inst_lower.startswith('xor'):
        return "🔢 XOR — used here for string encryption"
    if inst_lower.startswith('phi'):
        return "φ  PHI node — merges values from multiple predecessor blocks"
    if inst_lower.startswith('getelementptr'):
        return "📍 Computes address of array/struct element"
    return ""


def count_stats(functions):
    fns   = len(functions)
    bbs   = sum(len(f['blocks']) for f in functions)
    insts = sum(f['line_count'] for f in functions)
    fake  = sum(1 for f in functions for b in f['blocks'] if b['kind'] == 'fake')
    return {'functions': fns, 'blocks': bbs, 'instructions': insts, 'fake_blocks': fake}


# ── HTML Generation ──────────────────────────────────────────────────────────

INST_COLORS = {
    'branch':     ('#ffd93d', '#1a1a2e'),   # yellow
    'call':       ('#6bcb77', '#0d1f0d'),   # green
    'memory':     ('#4d96ff', '#0a0f1e'),   # blue
    'arithmetic': ('#c77dff', '#1a0a2e'),   # purple
    'compare':    ('#ff6b6b', '#2e0a0a'),   # red
    'phi':        ('#ff9f1c', '#2e1a00'),   # orange
    'obfuscated': ('#ff4d6d', '#2e0010'),   # hot pink
    'other':      ('#aaaaaa', '#1a1a1a'),   # grey
}

BLOCK_BORDER = {
    'fake':    '#ff4d6d',
    'junk':    '#ff9f1c',
    'opaque':  '#c77dff',
    'entry':   '#6bcb77',
    'real':    '#4d96ff',
    'normal':  '#333355',
}


def render_instruction(inst):
    raw = html.escape(inst['raw'])
    kind = inst['kind']
    bg, fg = INST_COLORS.get(kind, INST_COLORS['other'])
    expl = inst['explanation']

    badge_map = {
        'branch':     ('BRANCH',  '#ffd93d'),
        'call':       ('CALL',    '#6bcb77'),
        'memory':     ('MEM',     '#4d96ff'),
        'arithmetic': ('MATH',    '#c77dff'),
        'compare':    ('CMP',     '#ff6b6b'),
        'phi':        ('PHI',     '#ff9f1c'),
        'obfuscated': ('OBF 🎭',  '#ff4d6d'),
        'other':      ('',        ''),
    }
    badge_text, badge_color = badge_map.get(kind, ('', ''))
    badge = f'<span class="badge" style="background:{badge_color};color:#000">{badge_text}</span>' if badge_text else ''

    tooltip = f'<span class="tooltip">{html.escape(expl)}</span>' if expl else ''

    return f'''
<div class="inst inst-{kind}" style="border-left:3px solid {bg}">
  <code>{raw}</code>{badge}
  {tooltip}
</div>'''


def render_block(block):
    label = html.escape(block['label'])
    kind  = block['kind']
    border = BLOCK_BORDER.get(kind, BLOCK_BORDER['normal'])

    kind_label = {
        'fake':   '🎭 FAKE DEAD BLOCK',
        'junk':   '🗑️ JUNK BLOCK',
        'opaque': '🔮 OPAQUE PREDICATE',
        'entry':  '🚪 ENTRY',
        'real':   '✅ REAL PATH',
        'normal': '',
    }.get(kind, '')

    kind_badge = f'<span class="block-kind-badge">{kind_label}</span>' if kind_label else ''

    insts_html = ''.join(render_instruction(i) for i in block['instructions'])
    if not insts_html:
        insts_html = '<div class="inst inst-other"><code><em>(empty)</em></code></div>'

    return f'''
<div class="block block-{kind}" style="border:1.5px solid {border}">
  <div class="block-header" style="border-bottom:1px solid {border}40">
    <span class="block-label">{label}:</span>
    {kind_badge}
    <span class="block-count">{len(block["instructions"])} insts</span>
  </div>
  <div class="block-body">{insts_html}</div>
</div>'''


def render_function(fn, side):
    name = html.escape(fn['name'])
    blocks_html = ''.join(render_block(b) for b in fn['blocks'])
    if not blocks_html:
        blocks_html = '<div class="block"><div class="block-body"><em>(no blocks parsed)</em></div></div>'

    return f'''
<div class="function" id="{side}-{name}">
  <div class="fn-header">
    <span class="fn-icon">ƒ</span>
    <span class="fn-name">{name}</span>
    <span class="fn-meta">{len(fn["blocks"])} blocks · {fn["line_count"]} insts</span>
  </div>
  <div class="fn-body">{blocks_html}</div>
</div>'''


def generate_html(orig_fns, obf_fns, orig_path, obf_path):
    orig_stats = count_stats(orig_fns)
    obf_stats  = count_stats(obf_fns)

    def delta(a, b):
        d = b - a
        sign = '+' if d >= 0 else ''
        color = '#ff4d6d' if d > 0 else '#6bcb77'
        return f'<span style="color:{color};font-weight:700">{sign}{d}</span>'

    orig_html = ''.join(render_function(f, 'orig') for f in orig_fns) or '<p>No functions found</p>'
    obf_html  = ''.join(render_function(f, 'obf')  for f in obf_fns)  or '<p>No functions found</p>'

    fn_names_orig = [f['name'] for f in orig_fns]
    fn_nav = ''.join(
        f'<button class="nav-btn" onclick="jumpTo(\'{n}\')">{n}</button>'
        for n in fn_names_orig
    )

    # Build legend
    legend_items = ''.join(
        f'<span class="legend-item"><span class="legend-dot" style="background:{c[0]}"></span>{k}</span>'
        for k, c in INST_COLORS.items() if k != 'other'
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLVM Obfuscator — IR Visualizer</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:        #0a0a10;
    --bg2:       #10101a;
    --bg3:       #16162a;
    --border:    #1e1e3a;
    --text:      #d0d0e8;
    --text2:     #7070a0;
    --accent:    #6bcb77;
    --accent2:   #4d96ff;
    --danger:    #ff4d6d;
    --warn:      #ff9f1c;
    --purple:    #c77dff;
    --glow:      0 0 20px rgba(107, 203, 119, 0.15);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }}

  /* ── Background ── */
  body::before {{
    content: '';
    position: fixed; inset: 0;
    background:
      radial-gradient(ellipse 60% 40% at 20% 20%, rgba(77,150,255,0.06) 0%, transparent 60%),
      radial-gradient(ellipse 50% 50% at 80% 80%, rgba(199,125,255,0.06) 0%, transparent 60%);
    pointer-events: none; z-index: 0;
  }}

  /* ── Header ── */
  .header {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(10,10,16,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
  }}
  .header-top {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 0.5rem;
  }}
  .header-title {{
    font-size: 1.3rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .header-sub {{ font-size: 0.75rem; color: var(--text2); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }}

  /* ── Stats bar ── */
  .stats-bar {{
    display: flex; gap: 1rem; padding: 0.75rem 0;
    border-top: 1px solid var(--border);
    overflow-x: auto;
  }}
  .stat-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    min-width: 130px;
    flex-shrink: 0;
  }}
  .stat-label {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text2); }}
  .stat-row {{ display: flex; gap: 0.5rem; align-items: baseline; margin-top: 4px; }}
  .stat-orig {{ font-size: 1rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: var(--accent2); }}
  .stat-arrow {{ color: var(--text2); font-size: 0.8rem; }}
  .stat-obf {{ font-size: 1rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: var(--danger); }}
  .stat-delta {{ font-size: 0.75rem; margin-left: 4px; }}

  /* ── Nav ── */
  .nav-bar {{
    display: flex; gap: 0.5rem; padding: 0.6rem 2rem;
    border-bottom: 1px solid var(--border);
    background: rgba(10,10,16,0.85);
    overflow-x: auto;
  }}
  .nav-btn {{
    background: var(--bg2); border: 1px solid var(--border);
    color: var(--text2); font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; padding: 4px 10px; border-radius: 20px; cursor: pointer;
    transition: all 0.2s; white-space: nowrap;
  }}
  .nav-btn:hover {{ border-color: var(--accent); color: var(--accent); background: rgba(107,203,119,0.08); }}

  /* ── Explainer banner ── */
  .explainer {{
    margin: 1.5rem 2rem;
    background: linear-gradient(135deg, rgba(77,150,255,0.08), rgba(199,125,255,0.08));
    border: 1px solid rgba(77,150,255,0.2);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
  }}
  .explainer h2 {{ font-size: 1rem; font-weight: 800; color: var(--accent2); margin-bottom: 0.5rem; }}
  .explainer p {{ font-size: 0.85rem; color: var(--text); line-height: 1.7; }}
  .explainer .highlight {{ color: var(--danger); font-weight: 700; }}
  .explainer .good {{ color: var(--accent); font-weight: 700; }}

  /* ── Legend ── */
  .legend {{
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    padding: 0.75rem 2rem;
    border-bottom: 1px solid var(--border);
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 5px;
    font-size: 0.7rem; color: var(--text2);
    font-family: 'JetBrains Mono', monospace;
  }}
  .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}

  /* ── Main columns ── */
  .columns {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    position: relative; z-index: 1;
  }}
  .column {{
    border-right: 1px solid var(--border);
    min-height: 100vh;
    padding: 1rem 1.5rem 3rem;
    overflow-y: auto;
  }}
  .column:last-child {{ border-right: none; }}

  .col-header {{
    position: sticky; top: 0;
    background: rgba(10,10,16,0.9);
    backdrop-filter: blur(6px);
    padding: 0.75rem 0;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--border);
    display: flex; align-items: center; gap: 0.75rem;
    z-index: 10;
  }}
  .col-title {{
    font-size: 0.9rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  }}
  .col-orig .col-title {{ color: var(--accent2); }}
  .col-obf  .col-title {{ color: var(--danger); }}
  .col-path {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text2); }}

  /* ── Functions ── */
  .function {{
    margin-bottom: 1.5rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    scroll-margin-top: 120px;
  }}
  .fn-header {{
    display: flex; align-items: center; gap: 0.6rem;
    background: var(--bg2); padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--border);
  }}
  .fn-icon {{ font-size: 1.1rem; color: var(--purple); font-weight: 700; }}
  .fn-name {{ font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 700; color: var(--text); }}
  .fn-meta {{ margin-left: auto; font-size: 0.65rem; color: var(--text2); font-family: 'JetBrains Mono', monospace; }}
  .fn-body {{ padding: 0.75rem; background: var(--bg); display: flex; flex-direction: column; gap: 0.6rem; }}

  /* ── Blocks ── */
  .block {{
    border-radius: 8px;
    overflow: hidden;
    background: var(--bg2);
    transition: transform 0.15s;
  }}
  .block:hover {{ transform: translateX(2px); }}
  .block-header {{
    display: flex; align-items: center; gap: 0.5rem;
    padding: 4px 10px; background: rgba(0,0,0,0.3);
  }}
  .block-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: var(--text2); }}
  .block-kind-badge {{
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    background: rgba(255,77,109,0.15); color: var(--danger);
    padding: 1px 6px; border-radius: 3px; letter-spacing: 0.05em;
  }}
  .block-fake .block-kind-badge {{ background: rgba(255,77,109,0.15); color: var(--danger); }}
  .block-junk .block-kind-badge {{ background: rgba(255,159,28,0.15); color: var(--warn); }}
  .block-count {{ margin-left: auto; font-size: 0.6rem; color: var(--text2); font-family: 'JetBrains Mono', monospace; }}
  .block-body {{ padding: 6px 8px; display: flex; flex-direction: column; gap: 2px; }}

  /* ── Instructions ── */
  .inst {{
    display: flex; align-items: center; gap: 0.5rem;
    padding: 3px 8px; border-radius: 4px;
    position: relative; cursor: default;
    background: rgba(255,255,255,0.02);
    transition: background 0.15s;
    flex-wrap: wrap;
  }}
  .inst:hover {{ background: rgba(255,255,255,0.05); }}
  .inst code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: var(--text);
    flex: 1; min-width: 0; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
  }}
  .inst-obfuscated {{ background: rgba(255,77,109,0.06) !important; }}
  .inst-obfuscated code {{ color: var(--danger) !important; }}

  .badge {{
    font-size: 0.55rem; font-weight: 700;
    padding: 1px 5px; border-radius: 3px;
    flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.05em;
  }}
  .tooltip {{
    display: none;
    position: absolute; left: 0; top: calc(100% + 4px);
    background: #1e1e3a; border: 1px solid var(--border);
    padding: 6px 10px; border-radius: 6px;
    font-size: 0.7rem; color: var(--text);
    z-index: 50; white-space: nowrap;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    pointer-events: none;
  }}
  .inst:hover .tooltip {{ display: block; }}

  /* ── Highlight pulse ── */
  @keyframes highlight-pulse {{
    0%   {{ box-shadow: 0 0 0 0 rgba(107,203,119,0.5); }}
    70%  {{ box-shadow: 0 0 0 10px rgba(107,203,119,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(107,203,119,0); }}
  }}
  .highlight-pulse {{ animation: highlight-pulse 1s ease; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text2); }}

  /* ── Responsive ── */
  @media (max-width: 900px) {{
    .columns {{ grid-template-columns: 1fr; }}
    .column {{ border-right: none; border-bottom: 1px solid var(--border); }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div>
      <div class="header-title">LLVM IR Obfuscation Visualizer</div>
      <div class="header-sub">original vs obfuscated — hover instructions for explanations</div>
    </div>
  </div>

  <div class="stats-bar">
    <div class="stat-card">
      <div class="stat-label">Functions</div>
      <div class="stat-row">
        <span class="stat-orig">{orig_stats['functions']}</span>
        <span class="stat-arrow">→</span>
        <span class="stat-obf">{obf_stats['functions']}</span>
        <span class="stat-delta">{delta(orig_stats['functions'], obf_stats['functions'])}</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Basic Blocks</div>
      <div class="stat-row">
        <span class="stat-orig">{orig_stats['blocks']}</span>
        <span class="stat-arrow">→</span>
        <span class="stat-obf">{obf_stats['blocks']}</span>
        <span class="stat-delta">{delta(orig_stats['blocks'], obf_stats['blocks'])}</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Instructions</div>
      <div class="stat-row">
        <span class="stat-orig">{orig_stats['instructions']}</span>
        <span class="stat-arrow">→</span>
        <span class="stat-obf">{obf_stats['instructions']}</span>
        <span class="stat-delta">{delta(orig_stats['instructions'], obf_stats['instructions'])}</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Fake Blocks</div>
      <div class="stat-row">
        <span class="stat-orig">0</span>
        <span class="stat-arrow">→</span>
        <span class="stat-obf" style="color:var(--danger)">{obf_stats['fake_blocks']}</span>
        <span class="stat-delta">{delta(0, obf_stats['fake_blocks'])}</span>
      </div>
    </div>
  </div>
</div>

<div class="nav-bar">{fn_nav}</div>

<div class="explainer">
  <h2>🔍 What am I looking at?</h2>
  <p>
    The left panel shows your <span class="good">original program</span> compiled to LLVM Intermediate Representation (IR) —
    think of IR as a universal, low-level version of your code that's still somewhat readable.<br><br>
    The right panel shows the <span class="highlight">obfuscated version</span> of the same program.
    The obfuscator has inserted <span class="highlight">fake dead branches</span> (code paths that look real but are never taken),
    <span class="highlight">junk arithmetic</span> (meaningless calculations to inflate code size),
    and <span class="highlight">encrypted strings</span> (so a reverse engineer can't just grep for passwords or messages).
    The program still produces <strong>exactly the same output</strong> — it just looks completely different to any analysis tool.
  </p>
</div>

<div class="legend">{legend_items}</div>

<div class="columns">
  <div class="column col-orig">
    <div class="col-header">
      <span class="col-title">Original IR</span>
      <span class="col-path">{html.escape(orig_path)}</span>
    </div>
    {orig_html}
  </div>
  <div class="column col-obf">
    <div class="col-header">
      <span class="col-title">Obfuscated IR</span>
      <span class="col-path">{html.escape(obf_path)}</span>
    </div>
    {obf_html}
  </div>
</div>

<script>
function jumpTo(name) {{
  const origEl = document.getElementById('orig-' + name);
  const obfEl  = document.getElementById('obf-'  + name);
  if (origEl) {{
    origEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    origEl.classList.add('highlight-pulse');
    setTimeout(() => origEl.classList.remove('highlight-pulse'), 1100);
  }}
  if (obfEl) {{
    obfEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    obfEl.classList.add('highlight-pulse');
    setTimeout(() => obfEl.classList.remove('highlight-pulse'), 1100);
  }}
}}
</script>
</body>
</html>'''


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <input.ll> <obf.ll> <output.html>')
        sys.exit(1)

    orig_path = sys.argv[1]
    obf_path  = sys.argv[2]
    out_path  = sys.argv[3]

    print(f'[Viz] Parsing {orig_path}...')
    orig_fns = parse_ir(orig_path)
    print(f'[Viz] Parsing {obf_path}...')
    obf_fns  = parse_ir(obf_path)

    print(f'[Viz] Generating HTML...')
    page = generate_html(orig_fns, obf_fns, orig_path, obf_path)

    with open(out_path, 'w') as f:
        f.write(page)

    print(f'[Viz] Written to: {out_path}')
    print(f'[Viz] Open in browser: file://{out_path}')