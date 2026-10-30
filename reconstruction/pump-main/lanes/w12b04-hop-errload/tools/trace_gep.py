#!/usr/bin/env python3
"""trace_gep.py build.log : for each print-changed IR dump of swap_hop, report where complete_fill's global arg is defined."""
import sys, re
log = open(sys.argv[1], errors='replace').read()
parts = re.split(r'\n?\*\*\* IR Dump After (.*?) \*\*\*\n', log)
# parts: [pre, name1, body1, name2, body2,...]
for i in range(1, len(parts), 2):
    name, body = parts[i], parts[i+1]
    if 'swap_hop' not in name: continue
    if name.startswith('Finalize') or '(' in name and 'Pass' not in name: break
    lines = body.split('\n')
    blk = 'entry'; defs = {}; callinfo = None
    for ln in lines:
        m = re.match(r'^([\w.$"-]+):', ln)
        if m: blk = m.group(1)
        m = re.match(r'^\s+(%[\w.$"-]+) = (.*)$', ln)
        if m: defs[m.group(1)] = (blk, m.group(2)[:110])
        if 'complete_fill' in ln and ' call ' in ln and 'declare' not in ln:
            args = re.findall(r'(?:ptr|i64|i128|i8)[^,%]*?(%[\w.$"-]+)', ln.split('complete_fill',1)[1])
            callinfo = (blk, args[:3])
    if callinfo:
        cb, args = callinfo
        a1 = args[1] if len(args) > 1 else None
        d = defs.get(a1, ('?', '?'))
        print(f'{name[:60]:60} call@{cb:14} arg1={a1} def@{d[0]:14} {d[1]}')
    else:
        print(f'{name[:60]:60} (no complete_fill call: inlined?)')
